from __future__ import annotations

from dataclasses import replace
from itertools import combinations

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.transition import execute_transition
from substrate.regulation.models import (
    AbstentionMarker,
    DeviationDirection,
    DeviationRecord,
    NeedAxis,
    NeedSignal,
    NeedState,
    PartialKnownMarker,
    PreferredRange,
    PressureState,
    RegulationConfidence,
    RegulationContext,
    RegulationResult,
    RegulationState,
    TradeoffPair,
    TradeoffState,
)
from substrate.regulation.policy import derive_regulation_bias
from substrate.regulation.telemetry import build_regulation_telemetry


ATTEMPTED_REGULATION_PATHS: tuple[str, ...] = (
    "regulation.tracked_needs",
    "regulation.preferred_ranges",
    "regulation.deviations",
    "regulation.pressure_load",
    "regulation.tradeoff_state",
    "regulation.downstream_bias",
    "regulation.confidence_markers",
)


DEFAULT_RANGES: dict[NeedAxis, PreferredRange] = {
    NeedAxis.ENERGY: PreferredRange(min_value=45.0, max_value=65.0),
    NeedAxis.COGNITIVE_LOAD: PreferredRange(min_value=30.0, max_value=60.0),
    NeedAxis.SAFETY: PreferredRange(min_value=55.0, max_value=85.0),
    NeedAxis.SOCIAL_CONTACT: PreferredRange(min_value=35.0, max_value=65.0),
    NeedAxis.NOVELTY: PreferredRange(min_value=30.0, max_value=70.0),
}


def create_default_regulation_state() -> RegulationState:
    needs: list[NeedState] = []
    for axis, preferred in DEFAULT_RANGES.items():
        baseline = (preferred.min_value + preferred.max_value) / 2.0
        needs.append(
            NeedState(
                axis=axis,
                current_value=baseline,
                preferred_range=preferred,
                deviation=0.0,
                deviation_direction=DeviationDirection.IN_RANGE,
                pressure=0.0,
                load_accumulated=0.0,
                unresolved_steps=0,
            )
        )
    return RegulationState(needs=tuple(needs), confidence=RegulationConfidence.MEDIUM)


def update_regulation_state(
    signals: tuple[NeedSignal, ...] | list[NeedSignal],
    prior_state: RegulationState | None,
    context: RegulationContext | None = None,
) -> RegulationResult:
    context = context or RegulationContext()
    is_valid_input, input_errors = validate_input_shape(signals, context)
    is_valid_prior, prior_error, normalized_prior = validate_prior_regulation_state(prior_state)
    relevant_signals = classify_relevant_regulatory_signals(
        tuple(signals) if is_valid_input else ()
    )
    needs = update_tracked_needs(relevant_signals, normalized_prior)
    deviations = compute_preferred_range_deviations(needs)
    needs = accumulate_load_and_pressure_over_time(needs, normalized_prior, context)
    tradeoff = compute_competing_needs_tradeoff_state(needs)
    state = RegulationState(needs=needs, confidence=normalized_prior.confidence)
    state = emit_degraded_confidence_or_abstain_markers(
        state=state,
        relevant_signals=relevant_signals,
        input_errors=input_errors,
        prior_error=prior_error if not is_valid_prior else None,
        context=context,
    )
    state = enforce_regulation_invariants(state)
    bias = derive_downstream_regulation_bias_urgency_surface(state, tradeoff, context)
    telemetry = build_regulation_telemetry(
        state=state,
        deviations=deviations,
        pressures=tuple(
            PressureState(
                axis=need.axis,
                pressure=need.pressure,
                load_accumulated=need.load_accumulated,
                unresolved_steps=need.unresolved_steps,
            )
            for need in state.needs
        ),
        tradeoff=tradeoff,
        bias=bias,
        signals=tuple(relevant_signals.values()),
        source_lineage=context.source_lineage,
        confidence=state.confidence,
        causal_basis=(
            "validated regulation signals + prior pressure/load accumulation dynamics"
        ),
        attempted_paths=ATTEMPTED_REGULATION_PATHS,
    )
    return return_typed_regulation_result(state=state, tradeoff=tradeoff, bias=bias, telemetry=telemetry)


def validate_input_shape(
    signals: tuple[NeedSignal, ...] | list[NeedSignal], context: RegulationContext
) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if not isinstance(context, RegulationContext):
        errors.append("context must be RegulationContext")
    if isinstance(context, RegulationContext) and context.step_delta < 1:
        errors.append("context.step_delta must be >= 1")
    if not isinstance(signals, (tuple, list)):
        errors.append("signals must be tuple/list of NeedSignal")
        return False, tuple(errors)
    for signal in signals:
        if not isinstance(signal, NeedSignal):
            errors.append("all signals must be NeedSignal")
            continue
        if signal.value < 0.0 or signal.value > 100.0:
            errors.append(f"signal value out of range for axis {signal.axis.value}")
    return len(errors) == 0, tuple(errors)


def validate_prior_regulation_state(
    prior_state: RegulationState | None,
) -> tuple[bool, str | None, RegulationState]:
    if prior_state is None:
        return True, None, create_default_regulation_state()
    if not isinstance(prior_state, RegulationState):
        return False, "prior state must be RegulationState", create_default_regulation_state()

    axis_to_need = {need.axis: need for need in prior_state.needs}
    if set(axis_to_need.keys()) != set(DEFAULT_RANGES.keys()):
        return (
            False,
            "prior state missing required regulation axes",
            create_default_regulation_state(),
        )
    for need in prior_state.needs:
        if need.preferred_range.min_value >= need.preferred_range.max_value:
            return (
                False,
                f"invalid preferred range for axis {need.axis.value}",
                create_default_regulation_state(),
            )
    return True, None, prior_state


def classify_relevant_regulatory_signals(
    signals: tuple[NeedSignal, ...],
) -> dict[NeedAxis, NeedSignal]:
    by_axis: dict[NeedAxis, NeedSignal] = {}
    for signal in signals:
        by_axis[signal.axis] = signal
    return by_axis


def update_tracked_needs(
    relevant_signals: dict[NeedAxis, NeedSignal],
    prior_state: RegulationState,
) -> tuple[NeedState, ...]:
    updated: list[NeedState] = []
    prior_map = {need.axis: need for need in prior_state.needs}
    for axis in DEFAULT_RANGES:
        prior = prior_map[axis]
        signal = relevant_signals.get(axis)
        next_value = signal.value if signal is not None else prior.current_value
        updated.append(
            replace(
                prior,
                current_value=next_value,
                preferred_range=DEFAULT_RANGES[axis],
                last_signal_ref=signal.source_ref if signal else prior.last_signal_ref,
            )
        )
    return tuple(updated)


def compute_preferred_range_deviations(needs: tuple[NeedState, ...]) -> tuple[DeviationRecord, ...]:
    records: list[DeviationRecord] = []
    for need in needs:
        deviation, direction = _deviation_from_range(need.current_value, need.preferred_range)
        records.append(
            DeviationRecord(
                axis=need.axis,
                preferred_range=need.preferred_range,
                current_value=need.current_value,
                deviation=deviation,
                direction=direction,
            )
        )
    return tuple(records)


def accumulate_load_and_pressure_over_time(
    needs: tuple[NeedState, ...],
    prior_state: RegulationState,
    context: RegulationContext,
) -> tuple[NeedState, ...]:
    prior_map = {need.axis: need for need in prior_state.needs}
    updated: list[NeedState] = []
    for need in needs:
        prior = prior_map[need.axis]
        deviation, direction = _deviation_from_range(need.current_value, need.preferred_range)
        if deviation > 0.0:
            unresolved_steps = prior.unresolved_steps + context.step_delta
            load_accumulated = min(
                300.0, prior.load_accumulated + (deviation * context.step_delta)
            )
            pressure = min(
                100.0,
                prior.pressure + (deviation * 0.35 * context.step_delta) + (0.8 * context.step_delta),
            )
        else:
            unresolved_steps = max(0, prior.unresolved_steps - context.step_delta)
            load_accumulated = max(
                0.0, prior.load_accumulated - (4.0 * context.step_delta)
            )
            pressure = max(0.0, prior.pressure - (3.0 * context.step_delta))
        updated.append(
            replace(
                need,
                deviation=round(deviation, 4),
                deviation_direction=direction,
                pressure=round(pressure, 4),
                load_accumulated=round(load_accumulated, 4),
                unresolved_steps=unresolved_steps,
            )
        )
    return tuple(updated)


def compute_competing_needs_tradeoff_state(needs: tuple[NeedState, ...]) -> TradeoffState:
    urgent = tuple(
        need.axis
        for need in sorted(
            needs,
            key=lambda item: item.pressure + (item.deviation * 0.4),
            reverse=True,
        )
        if need.pressure >= 12.0 or need.deviation >= 8.0
    )
    dominant_axis = urgent[0] if urgent else None
    competing_pairs: list[TradeoffPair] = []
    for first, second in combinations(urgent[:3], 2):
        competing_pairs.append(
            TradeoffPair(
                first_axis=first,
                second_axis=second,
                reason=_tradeoff_reason(first, second),
            )
        )
    suppressed_axes = tuple(axis for axis in urgent[1:] if axis != dominant_axis)
    if not urgent:
        reason = "no strong unresolved pressure"
    elif len(urgent) == 1:
        reason = "single dominant pressure axis"
    else:
        reason = "multiple competing pressure axes"
    return TradeoffState(
        active_axes=urgent,
        dominant_axis=dominant_axis,
        suppressed_axes=suppressed_axes,
        competing_pairs=tuple(competing_pairs),
        reason=reason,
    )


def derive_downstream_regulation_bias_urgency_surface(
    state: RegulationState,
    tradeoff: TradeoffState,
    context: RegulationContext,
):
    return derive_regulation_bias(state, tradeoff, context)


def emit_degraded_confidence_or_abstain_markers(
    *,
    state: RegulationState,
    relevant_signals: dict[NeedAxis, NeedSignal],
    input_errors: tuple[str, ...],
    prior_error: str | None,
    context: RegulationContext,
) -> RegulationState:
    provided_axes = set(relevant_signals.keys())
    missing_axes = tuple(axis for axis in DEFAULT_RANGES if axis not in provided_axes)
    confidence = _confidence_from_signals(tuple(relevant_signals.values()))
    partial_known = (
        PartialKnownMarker(
            missing_axes=missing_axes,
            reason="missing regulation signals for part of tracked axes",
        )
        if missing_axes
        else None
    )

    error_reasons = list(input_errors)
    if prior_error:
        error_reasons.append(prior_error)
    abstention: AbstentionMarker | None = None

    if not relevant_signals:
        confidence = RegulationConfidence.LOW
        abstention = AbstentionMarker(reason="no regulation signals provided")
    if error_reasons:
        confidence = RegulationConfidence.LOW
        abstention = AbstentionMarker(reason="; ".join(error_reasons))
    if context.require_strong_claim and confidence != RegulationConfidence.HIGH:
        abstention = abstention or AbstentionMarker(
            reason="strong regulation claim requested but confidence is not high"
        )
    return replace(
        state,
        confidence=confidence,
        partial_known=partial_known,
        abstention=abstention,
        last_updated_step=state.last_updated_step + context.step_delta,
    )


def enforce_regulation_invariants(state: RegulationState) -> RegulationState:
    axis_set = {need.axis for need in state.needs}
    if axis_set != set(DEFAULT_RANGES):
        raise ValueError("regulation state must include all required axes")
    for need in state.needs:
        if need.preferred_range.min_value >= need.preferred_range.max_value:
            raise ValueError(f"invalid preferred range for {need.axis.value}")
        if need.deviation < 0.0:
            raise ValueError(f"deviation must be >= 0 for {need.axis.value}")
        if need.pressure < 0.0 or need.pressure > 100.0:
            raise ValueError(f"pressure out of bounds for {need.axis.value}")
    if state.confidence == RegulationConfidence.HIGH and state.partial_known is not None:
        return replace(state, confidence=RegulationConfidence.MEDIUM)
    return state


def return_typed_regulation_result(
    *,
    state: RegulationState,
    tradeoff: TradeoffState,
    bias,
    telemetry,
) -> RegulationResult:
    return RegulationResult(state=state, tradeoff=tradeoff, bias=bias, telemetry=telemetry)


def regulation_result_to_payload(result: RegulationResult) -> dict[str, object]:
    urgency = {axis.value: value for axis, value in result.bias.urgency_by_axis}
    needs = {
        need.axis.value: {
            "current_value": need.current_value,
            "deviation": need.deviation,
            "pressure": need.pressure,
            "load_accumulated": need.load_accumulated,
            "unresolved_steps": need.unresolved_steps,
        }
        for need in result.state.needs
    }
    return {
        "confidence": result.state.confidence.value,
        "abstain": result.state.abstention.reason if result.state.abstention else None,
        "partial_known": (
            {
                "missing_axes": tuple(axis.value for axis in result.state.partial_known.missing_axes),
                "reason": result.state.partial_known.reason,
            }
            if result.state.partial_known
            else None
        ),
        "tradeoff": {
            "active_axes": tuple(axis.value for axis in result.tradeoff.active_axes),
            "dominant_axis": (
                result.tradeoff.dominant_axis.value if result.tradeoff.dominant_axis else None
            ),
            "suppressed_axes": tuple(axis.value for axis in result.tradeoff.suppressed_axes),
            "reason": result.tradeoff.reason,
        },
        "bias": {
            "urgency_by_axis": urgency,
            "salience_order": tuple(axis.value for axis in result.bias.salience_order),
            "coping_mode": result.bias.coping_mode,
            "claim_strength": result.bias.claim_strength,
            "restrictions": result.bias.restrictions,
        },
        "needs": needs,
    }


def persist_regulation_result_via_f01(
    *,
    result: RegulationResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("r01-regulation-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"regulation-step-{result.state.last_updated_step}",
            "regulation_snapshot": regulation_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _deviation_from_range(
    value: float, preferred_range: PreferredRange
) -> tuple[float, DeviationDirection]:
    if value < preferred_range.min_value:
        return preferred_range.min_value - value, DeviationDirection.BELOW_RANGE
    if value > preferred_range.max_value:
        return value - preferred_range.max_value, DeviationDirection.ABOVE_RANGE
    return 0.0, DeviationDirection.IN_RANGE


def _confidence_from_signals(signals: tuple[NeedSignal, ...]) -> RegulationConfidence:
    if not signals:
        return RegulationConfidence.LOW
    explicit_conf = tuple(signal.confidence for signal in signals if signal.confidence is not None)
    if not explicit_conf:
        return RegulationConfidence.MEDIUM
    if all(level == RegulationConfidence.HIGH for level in explicit_conf) and len(signals) >= 3:
        return RegulationConfidence.HIGH
    if any(level == RegulationConfidence.LOW for level in explicit_conf):
        return RegulationConfidence.LOW
    return RegulationConfidence.MEDIUM


def _tradeoff_reason(first: NeedAxis, second: NeedAxis) -> str:
    pair = {first, second}
    if pair == {NeedAxis.ENERGY, NeedAxis.NOVELTY}:
        return "resource conservation competes with exploration demand"
    if pair == {NeedAxis.SAFETY, NeedAxis.SOCIAL_CONTACT}:
        return "protective caution competes with social engagement"
    if pair == {NeedAxis.COGNITIVE_LOAD, NeedAxis.NOVELTY}:
        return "overload pressure competes with additional stimulation"
    return "simultaneous unresolved pressures require trade-off"
