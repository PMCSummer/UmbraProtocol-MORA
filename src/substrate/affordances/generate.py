from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.transition import execute_transition
from substrate.affordances.models import (
    AffordanceAbstentionMarker,
    AffordanceApplicability,
    AffordanceContext,
    AffordanceCost,
    AffordanceOptionClass,
    AffordanceResult,
    AffordanceRisk,
    AffordanceSetSummary,
    AffordanceStatus,
    AffordanceTradeoffProfile,
    BlockedMarker,
    CapabilitySpec,
    CapabilityState,
    EffectClass,
    EffectDirection,
    ExpectedEffect,
    RegulationAffordance,
    RegulationConfidence,
    UnavailableMarker,
    UnknownEffectMarker,
    UnsafeMarker,
)
from substrate.affordances.policy import evaluate_affordance_landscape_for_downstream
from substrate.affordances.telemetry import affordance_result_snapshot, build_affordance_telemetry
from substrate.regulation.models import NeedAxis, RegulationState


ATTEMPTED_AFFORDANCE_PATHS: tuple[str, ...] = (
    "affordance.targets",
    "affordance.candidate_set",
    "affordance.expected_effect",
    "affordance.cost_latency_duration_risk",
    "affordance.applicability_blockers",
    "affordance.tradeoff_profile",
    "affordance.downstream_gate",
    "affordance.uncertainty_markers",
)


BASE_EFFECT_CLASS: dict[AffordanceOptionClass, EffectClass] = {
    AffordanceOptionClass.ATTENTIONAL_NARROWING: EffectClass.IMMEDIATE_RELIEF,
    AffordanceOptionClass.LOAD_SHEDDING: EffectClass.IMMEDIATE_RELIEF,
    AffordanceOptionClass.RECOVERY_PAUSE: EffectClass.DELAYED_RECOVERY,
    AffordanceOptionClass.NOVELTY_SUPPRESSION: EffectClass.PREVENTIVE_REGULATION,
    AffordanceOptionClass.SAFETY_RECHECK: EffectClass.PROTECTIVE_SUPPRESSION,
    AffordanceOptionClass.SOCIAL_REGULATION_BIAS: EffectClass.PREVENTIVE_REGULATION,
    AffordanceOptionClass.RESOURCE_CONSERVATION: EffectClass.DELAYED_RECOVERY,
}


BASE_EFFECT_DIRECTION: dict[AffordanceOptionClass, EffectDirection] = {
    AffordanceOptionClass.ATTENTIONAL_NARROWING: EffectDirection.SHIFT_SALIENCE,
    AffordanceOptionClass.LOAD_SHEDDING: EffectDirection.REDUCE_PRESSURE,
    AffordanceOptionClass.RECOVERY_PAUSE: EffectDirection.INCREASE_STABILITY,
    AffordanceOptionClass.NOVELTY_SUPPRESSION: EffectDirection.REDUCE_EXPOSURE,
    AffordanceOptionClass.SAFETY_RECHECK: EffectDirection.REDUCE_EXPOSURE,
    AffordanceOptionClass.SOCIAL_REGULATION_BIAS: EffectDirection.SHIFT_SALIENCE,
    AffordanceOptionClass.RESOURCE_CONSERVATION: EffectDirection.INCREASE_STABILITY,
}


def create_default_capability_state() -> CapabilityState:
    return CapabilityState(
        capabilities=tuple(
            CapabilitySpec(option_class=option, enabled=True, source_ref="default-capability")
            for option in AffordanceOptionClass
        ),
        confidence=RegulationConfidence.MEDIUM,
    )


def generate_regulation_affordances(
    regulation_state: RegulationState,
    capability_state: CapabilityState | None,
    context: AffordanceContext | None = None,
) -> AffordanceResult:
    context = context or AffordanceContext()
    cap_state = capability_state or create_default_capability_state()
    valid_regulation, regulation_error, normalized_regulation = validate_regulation_input(
        regulation_state
    )
    valid_capabilities, capability_error, normalized_capability = validate_capability_contract(
        cap_state
    )
    if not valid_regulation or not valid_capabilities:
        reason = "; ".join(
            x for x in (regulation_error, capability_error) if x is not None
        ) or "invalid affordance inputs"
        return _abstain_result(
            regulation_state=normalized_regulation,
            capability_state=normalized_capability,
            context=context,
            reason=reason,
        )

    targets = derive_candidate_need_targets(normalized_regulation)
    candidates = derive_candidate_affordance_set(
        regulation_state=normalized_regulation,
        capability_state=normalized_capability,
        targets=targets,
        context=context,
    )
    candidates = estimate_expected_effect(candidates, normalized_regulation, normalized_capability)
    candidates = estimate_cost_latency_duration_risk(candidates, normalized_capability)
    candidates = evaluate_applicability_and_blockers(
        candidates=candidates,
        regulation_state=normalized_regulation,
        capability_state=normalized_capability,
        context=context,
    )
    candidates = compute_tradeoff_profile(candidates)
    gate = derive_downstream_affordance_surface(candidates, context)
    candidates, abstention = emit_unknown_effect_blocked_unavailable_unsafe_abstain(
        candidates=candidates,
        gate=gate,
        regulation_state=normalized_regulation,
        context=context,
    )
    candidates = enforce_affordance_invariants(candidates)
    summary = _build_summary(candidates)
    telemetry = build_affordance_telemetry(
        regulation_snapshot=_regulation_snapshot(normalized_regulation),
        capability_state=normalized_capability,
        candidates=candidates,
        gate=gate,
        confidence=normalized_regulation.confidence,
        abstain_reason=abstention.reason if abstention else None,
        source_lineage=context.source_lineage,
        attempted_paths=ATTEMPTED_AFFORDANCE_PATHS,
        causal_basis=(
            "regulation pressure/tradeoff + capability constraints -> affordance landscape"
        ),
    )
    return return_typed_affordance_result(
        regulation_state=normalized_regulation,
        candidates=candidates,
        summary=summary,
        gate=gate,
        telemetry=telemetry,
        abstention=abstention,
    )


def validate_regulation_input(
    regulation_state: RegulationState,
) -> tuple[bool, str | None, RegulationState]:
    if not isinstance(regulation_state, RegulationState):
        return False, "regulation_state must be RegulationState", _empty_regulation_state()
    if not regulation_state.needs:
        return False, "regulation_state.needs must be non-empty", _empty_regulation_state()
    return True, None, regulation_state


def validate_capability_contract(
    capability_state: CapabilityState,
) -> tuple[bool, str | None, CapabilityState]:
    if not isinstance(capability_state, CapabilityState):
        return False, "capability_state must be CapabilityState", create_default_capability_state()
    capability_map = {spec.option_class: spec for spec in capability_state.capabilities}
    missing = tuple(option for option in AffordanceOptionClass if option not in capability_map)
    if missing:
        merged = capability_state.capabilities + tuple(
            CapabilitySpec(
                option_class=option,
                enabled=False,
                source_ref="autofill-missing-capability",
            )
            for option in missing
        )
        return False, "capability contract missing option classes", replace(
            capability_state, capabilities=merged
        )
    return True, None, capability_state


def derive_candidate_need_targets(
    regulation_state: RegulationState,
) -> dict[AffordanceOptionClass, tuple[NeedAxis, ...]]:
    needs = {need.axis: need for need in regulation_state.needs}
    targets: dict[AffordanceOptionClass, tuple[NeedAxis, ...]] = {}
    if needs[NeedAxis.COGNITIVE_LOAD].pressure >= 10.0:
        targets[AffordanceOptionClass.LOAD_SHEDDING] = (NeedAxis.COGNITIVE_LOAD,)
        targets[AffordanceOptionClass.ATTENTIONAL_NARROWING] = (NeedAxis.COGNITIVE_LOAD,)
    if needs[NeedAxis.ENERGY].pressure >= 8.0 or needs[NeedAxis.ENERGY].deviation >= 6.0:
        targets[AffordanceOptionClass.RECOVERY_PAUSE] = (NeedAxis.ENERGY,)
        targets[AffordanceOptionClass.RESOURCE_CONSERVATION] = (
            NeedAxis.ENERGY,
            NeedAxis.COGNITIVE_LOAD,
        )
    if needs[NeedAxis.SAFETY].pressure >= 8.0:
        targets[AffordanceOptionClass.SAFETY_RECHECK] = (NeedAxis.SAFETY,)
    if needs[NeedAxis.NOVELTY].pressure >= 8.0:
        targets[AffordanceOptionClass.NOVELTY_SUPPRESSION] = (NeedAxis.NOVELTY,)
    if needs[NeedAxis.SOCIAL_CONTACT].pressure >= 8.0:
        targets[AffordanceOptionClass.SOCIAL_REGULATION_BIAS] = (NeedAxis.SOCIAL_CONTACT,)

    if not targets:
        targets[AffordanceOptionClass.RESOURCE_CONSERVATION] = (
            NeedAxis.ENERGY,
            NeedAxis.COGNITIVE_LOAD,
        )
        targets[AffordanceOptionClass.RECOVERY_PAUSE] = (NeedAxis.ENERGY,)
    return targets


def derive_candidate_affordance_set(
    *,
    regulation_state: RegulationState,
    capability_state: CapabilityState,
    targets: dict[AffordanceOptionClass, tuple[NeedAxis, ...]],
    context: AffordanceContext,
) -> tuple[RegulationAffordance, ...]:
    needs = {need.axis: need for need in regulation_state.needs}
    cap_map = {spec.option_class: spec for spec in capability_state.capabilities}
    candidates: list[RegulationAffordance] = []
    for option, target_axes in targets.items():
        spec = cap_map.get(
            option,
            CapabilitySpec(option_class=option, enabled=False, source_ref="missing-capability"),
        )
        mean_pressure = sum(needs[axis].pressure for axis in target_axes) / len(target_axes)
        base_strength = min(1.0, round((mean_pressure / 100.0) * spec.max_intensity + 0.2, 4))
        effect = ExpectedEffect(
            effect_class=BASE_EFFECT_CLASS[option],
            effect_direction=BASE_EFFECT_DIRECTION[option],
            target_axes=target_axes,
            effect_strength_estimate=base_strength,
            confidence=regulation_state.confidence,
            basis="derived from target-axis pressure and capability intensity",
        )
        candidates.append(
            RegulationAffordance(
                affordance_id=f"aff-{option.value}-{uuid4().hex[:8]}",
                option_class=option,
                target_axes=target_axes,
                status=AffordanceStatus.PROVISIONAL,
                expected_effect=effect,
                cost=AffordanceCost(
                    energy_cost=0.0, cognitive_cost=0.0, social_cost=0.0, basis="pending-estimate"
                ),
                risk=AffordanceRisk(level=0.0, risk_note="pending-estimate"),
                latency_steps=1,
                duration_steps=2,
                applicability=AffordanceApplicability(
                    conditions=("regulation-target-active",),
                    blockers=(),
                    context_bounds=context.source_lineage,
                ),
                blockers=(),
                tradeoff=AffordanceTradeoffProfile(
                    immediate_relief_score=0.0,
                    delayed_recovery_score=0.0,
                    preventive_score=0.0,
                    side_effect_axes=(),
                    notes="pending-tradeoff",
                ),
                confidence=regulation_state.confidence,
                provenance_basis=f"targeted-by:{','.join(axis.value for axis in target_axes)}",
            )
        )
    return tuple(candidates)


def estimate_expected_effect(
    candidates: tuple[RegulationAffordance, ...],
    regulation_state: RegulationState,
    capability_state: CapabilityState,
) -> tuple[RegulationAffordance, ...]:
    cap_map = {spec.option_class: spec for spec in capability_state.capabilities}
    confidence = min(regulation_state.confidence, capability_state.confidence, key=_conf_rank)
    updated: list[RegulationAffordance] = []
    for candidate in candidates:
        spec = cap_map[candidate.option_class]
        adjusted_strength = min(
            1.0, round(candidate.expected_effect.effect_strength_estimate * spec.max_intensity, 4)
        )
        updated.append(
            replace(
                candidate,
                expected_effect=replace(
                    candidate.expected_effect,
                    effect_strength_estimate=adjusted_strength,
                    confidence=confidence,
                    basis=(
                        candidate.expected_effect.basis
                        + "; adjusted by capability intensity and confidence"
                    ),
                ),
                confidence=confidence,
            )
        )
    return tuple(updated)


def estimate_cost_latency_duration_risk(
    candidates: tuple[RegulationAffordance, ...],
    capability_state: CapabilityState,
) -> tuple[RegulationAffordance, ...]:
    cap_map = {spec.option_class: spec for spec in capability_state.capabilities}
    updated: list[RegulationAffordance] = []
    for candidate in candidates:
        spec = cap_map[candidate.option_class]
        cost, risk, latency, duration = _estimate_profile(candidate.option_class, spec)
        updated.append(
            replace(
                candidate,
                cost=cost,
                risk=risk,
                latency_steps=latency,
                duration_steps=duration,
            )
        )
    return tuple(updated)


def evaluate_applicability_and_blockers(
    *,
    candidates: tuple[RegulationAffordance, ...],
    regulation_state: RegulationState,
    capability_state: CapabilityState,
    context: AffordanceContext,
) -> tuple[RegulationAffordance, ...]:
    cap_map = {spec.option_class: spec for spec in capability_state.capabilities}
    updated: list[RegulationAffordance] = []
    for candidate in candidates:
        spec = cap_map.get(candidate.option_class)
        blockers: list[str] = list(candidate.blockers)
        status = AffordanceStatus.AVAILABLE
        blocked_marker = None
        unavailable_marker = None
        unsafe_marker = None
        unknown_effect = None

        if spec is None or not spec.enabled:
            status = AffordanceStatus.UNAVAILABLE
            reason = "capability missing or disabled"
            blockers.append(reason)
            unavailable_marker = UnavailableMarker(reason=reason)
        elif spec.cooldown_steps_remaining > 0:
            status = AffordanceStatus.BLOCKED
            reason = f"capability cooling down ({spec.cooldown_steps_remaining} steps)"
            blockers.append(reason)
            blocked_marker = BlockedMarker(reason=reason)
        elif (
            candidate.option_class == AffordanceOptionClass.SAFETY_RECHECK
            and not context.allow_protective_suppression
        ):
            status = AffordanceStatus.BLOCKED
            reason = "protective suppression disabled by context"
            blockers.append(reason)
            blocked_marker = BlockedMarker(reason=reason)
        elif candidate.risk.level > context.max_risk_tolerance:
            status = AffordanceStatus.UNSAFE
            reason = "estimated risk exceeds context tolerance"
            blockers.append(reason)
            unsafe_marker = UnsafeMarker(reason=reason)
        elif (
            candidate.expected_effect.effect_strength_estimate < 0.25
            or candidate.confidence == RegulationConfidence.LOW
        ):
            status = AffordanceStatus.PROVISIONAL
            unknown_effect = UnknownEffectMarker(
                reason="expected effect too weak or low-confidence"
            )

        updated.append(
            replace(
                candidate,
                status=status,
                blockers=tuple(dict.fromkeys(blockers)),
                applicability=replace(
                    candidate.applicability,
                    blockers=tuple(dict.fromkeys(blockers)),
                ),
                blocked_marker=blocked_marker,
                unavailable_marker=unavailable_marker,
                unsafe_marker=unsafe_marker,
                unknown_effect=unknown_effect,
            )
        )
    return tuple(updated)


def compute_tradeoff_profile(
    candidates: tuple[RegulationAffordance, ...],
) -> tuple[RegulationAffordance, ...]:
    updated: list[RegulationAffordance] = []
    for candidate in candidates:
        immediate, delayed, preventive, side_axes, note = _tradeoff_profile_for_option(
            candidate.option_class
        )
        updated.append(
            replace(
                candidate,
                tradeoff=AffordanceTradeoffProfile(
                    immediate_relief_score=immediate,
                    delayed_recovery_score=delayed,
                    preventive_score=preventive,
                    side_effect_axes=side_axes,
                    notes=note,
                ),
            )
        )
    return tuple(updated)


def derive_downstream_affordance_surface(
    candidates: tuple[RegulationAffordance, ...],
    context: AffordanceContext,
):
    return evaluate_affordance_landscape_for_downstream(
        candidates, require_available=context.require_available_candidates
    )


def emit_unknown_effect_blocked_unavailable_unsafe_abstain(
    *,
    candidates: tuple[RegulationAffordance, ...],
    gate,
    regulation_state: RegulationState,
    context: AffordanceContext,
) -> tuple[tuple[RegulationAffordance, ...], AffordanceAbstentionMarker | None]:
    if gate.accepted_candidate_ids:
        return candidates, None
    if not candidates:
        return candidates, AffordanceAbstentionMarker(
            reason="no candidates generated from current regulation state"
        )
    if context.require_available_candidates:
        return candidates, AffordanceAbstentionMarker(
            reason="no available affordance candidates under required constraints"
        )
    if regulation_state.abstention is not None:
        return candidates, AffordanceAbstentionMarker(
            reason=f"upstream regulation abstention propagated: {regulation_state.abstention.reason}"
        )
    return candidates, AffordanceAbstentionMarker(
        reason="affordance landscape produced but no candidate passed downstream gate"
    )


def enforce_affordance_invariants(
    candidates: tuple[RegulationAffordance, ...],
) -> tuple[RegulationAffordance, ...]:
    if not candidates:
        return candidates
    for candidate in candidates:
        if not candidate.target_axes:
            raise ValueError("affordance candidate must have target axes")
        if candidate.latency_steps < 0 or candidate.duration_steps <= 0:
            raise ValueError("affordance candidate must have bounded latency/duration")
        if candidate.expected_effect.effect_strength_estimate < 0.0:
            raise ValueError("effect_strength_estimate must be >= 0")
        if candidate.status == AffordanceStatus.BLOCKED and candidate.blocked_marker is None:
            raise ValueError("blocked candidate must include BlockedMarker")
        if (
            candidate.status == AffordanceStatus.UNAVAILABLE
            and candidate.unavailable_marker is None
        ):
            raise ValueError("unavailable candidate must include UnavailableMarker")
        if candidate.status == AffordanceStatus.UNSAFE and candidate.unsafe_marker is None:
            raise ValueError("unsafe candidate must include UnsafeMarker")
    return candidates


def return_typed_affordance_result(
    *,
    regulation_state: RegulationState,
    candidates: tuple[RegulationAffordance, ...],
    summary: AffordanceSetSummary,
    gate,
    telemetry,
    abstention: AffordanceAbstentionMarker | None,
) -> AffordanceResult:
    return AffordanceResult(
        regulation_state=regulation_state,
        candidates=candidates,
        summary=summary,
        gate=gate,
        telemetry=telemetry,
        abstention=abstention,
    )


def affordance_result_to_payload(result: AffordanceResult) -> dict[str, object]:
    candidates = {
        candidate.affordance_id: {
            "option_class": candidate.option_class.value,
            "status": candidate.status.value,
            "target_axes": tuple(axis.value for axis in candidate.target_axes),
            "effect_class": candidate.expected_effect.effect_class.value,
            "effect_direction": candidate.expected_effect.effect_direction.value,
            "effect_strength_estimate": candidate.expected_effect.effect_strength_estimate,
            "cost": {
                "energy_cost": candidate.cost.energy_cost,
                "cognitive_cost": candidate.cost.cognitive_cost,
                "social_cost": candidate.cost.social_cost,
            },
            "risk": candidate.risk.level,
            "latency_steps": candidate.latency_steps,
            "duration_steps": candidate.duration_steps,
            "blockers": candidate.blockers,
            "tradeoff": {
                "immediate_relief_score": candidate.tradeoff.immediate_relief_score,
                "delayed_recovery_score": candidate.tradeoff.delayed_recovery_score,
                "preventive_score": candidate.tradeoff.preventive_score,
            },
        }
        for candidate in result.candidates
    }
    payload = affordance_result_snapshot(result)
    payload["candidates"] = candidates
    payload["abstention"] = result.abstention.reason if result.abstention else None
    return payload


def persist_affordance_result_via_f01(
    *,
    result: AffordanceResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("r02-affordance-generation",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"affordance-step-{result.regulation_state.last_updated_step}",
            "affordance_snapshot": affordance_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _build_summary(candidates: tuple[RegulationAffordance, ...]) -> AffordanceSetSummary:
    statuses = [candidate.status for candidate in candidates]
    return AffordanceSetSummary(
        total_candidates=len(candidates),
        available_count=statuses.count(AffordanceStatus.AVAILABLE),
        blocked_count=statuses.count(AffordanceStatus.BLOCKED),
        unavailable_count=statuses.count(AffordanceStatus.UNAVAILABLE),
        unsafe_count=statuses.count(AffordanceStatus.UNSAFE),
        provisional_count=statuses.count(AffordanceStatus.PROVISIONAL),
        no_selection_performed=True,
        reason="affordance layer returns candidate landscape without final selection",
    )


def _estimate_profile(option: AffordanceOptionClass, spec: CapabilitySpec):
    if option == AffordanceOptionClass.ATTENTIONAL_NARROWING:
        return (
            AffordanceCost(energy_cost=0.15, cognitive_cost=0.2, social_cost=0.05, basis="base"),
            AffordanceRisk(level=0.35 * spec.risk_multiplier, risk_note="narrowing may suppress exploration"),
            1,
            2,
        )
    if option == AffordanceOptionClass.LOAD_SHEDDING:
        return (
            AffordanceCost(energy_cost=0.1, cognitive_cost=0.15, social_cost=0.1, basis="base"),
            AffordanceRisk(level=0.28 * spec.risk_multiplier, risk_note="scope reduction may defer obligations"),
            1,
            3,
        )
    if option == AffordanceOptionClass.RECOVERY_PAUSE:
        return (
            AffordanceCost(energy_cost=0.05, cognitive_cost=0.08, social_cost=0.12, basis="base"),
            AffordanceRisk(level=0.22 * spec.risk_multiplier, risk_note="pause may delay throughput"),
            2,
            5,
        )
    if option == AffordanceOptionClass.NOVELTY_SUPPRESSION:
        return (
            AffordanceCost(energy_cost=0.04, cognitive_cost=0.1, social_cost=0.02, basis="base"),
            AffordanceRisk(level=0.31 * spec.risk_multiplier, risk_note="suppression may reduce adaptive exploration"),
            1,
            4,
        )
    if option == AffordanceOptionClass.SAFETY_RECHECK:
        return (
            AffordanceCost(energy_cost=0.12, cognitive_cost=0.2, social_cost=0.05, basis="base"),
            AffordanceRisk(level=0.55 * spec.risk_multiplier, risk_note="protective mode can overconstrain behavior"),
            1,
            3,
        )
    if option == AffordanceOptionClass.SOCIAL_REGULATION_BIAS:
        return (
            AffordanceCost(energy_cost=0.09, cognitive_cost=0.12, social_cost=0.18, basis="base"),
            AffordanceRisk(level=0.33 * spec.risk_multiplier, risk_note="social rebias can misfit context"),
            2,
            4,
        )
    return (
        AffordanceCost(energy_cost=0.08, cognitive_cost=0.1, social_cost=0.08, basis="base"),
        AffordanceRisk(level=0.27 * spec.risk_multiplier, risk_note="conservation may reduce responsiveness"),
        1,
        4,
    )


def _tradeoff_profile_for_option(option: AffordanceOptionClass):
    if option == AffordanceOptionClass.LOAD_SHEDDING:
        return (
            0.85,
            0.45,
            0.55,
            (NeedAxis.NOVELTY,),
            "fast overload relief with moderate exploration cost",
        )
    if option == AffordanceOptionClass.RECOVERY_PAUSE:
        return (
            0.5,
            0.82,
            0.58,
            (NeedAxis.SOCIAL_CONTACT,),
            "slower recovery with stronger energy restoration",
        )
    if option == AffordanceOptionClass.SAFETY_RECHECK:
        return (
            0.74,
            0.4,
            0.8,
            (NeedAxis.NOVELTY, NeedAxis.SOCIAL_CONTACT),
            "protective suppression reduces exposure but narrows engagement",
        )
    if option == AffordanceOptionClass.NOVELTY_SUPPRESSION:
        return (
            0.52,
            0.5,
            0.88,
            (NeedAxis.NOVELTY,),
            "prevents overstimulation while reducing exploratory intake",
        )
    if option == AffordanceOptionClass.SOCIAL_REGULATION_BIAS:
        return (
            0.55,
            0.62,
            0.63,
            (NeedAxis.SAFETY,),
            "social rebias can help isolation pressure but may raise safety caution",
        )
    if option == AffordanceOptionClass.ATTENTIONAL_NARROWING:
        return (
            0.76,
            0.35,
            0.57,
            (NeedAxis.NOVELTY,),
            "strong immediate focus with reduced context breadth",
        )
    return (
        0.6,
        0.75,
        0.5,
        (NeedAxis.NOVELTY, NeedAxis.SOCIAL_CONTACT),
        "resource conservation helps long-tail recovery with responsiveness trade-off",
    )


def _regulation_snapshot(state: RegulationState) -> dict[str, object]:
    return {
        "confidence": state.confidence.value,
        "abstention": state.abstention.reason if state.abstention else None,
        "partial_known": state.partial_known.reason if state.partial_known else None,
        "needs": {
            need.axis.value: {
                "pressure": need.pressure,
                "deviation": need.deviation,
                "unresolved_steps": need.unresolved_steps,
            }
            for need in state.needs
        },
    }


def _conf_rank(level: RegulationConfidence) -> int:
    if level == RegulationConfidence.HIGH:
        return 3
    if level == RegulationConfidence.MEDIUM:
        return 2
    return 1


def _empty_regulation_state() -> RegulationState:
    return RegulationState(needs=(), confidence=RegulationConfidence.LOW)


def _abstain_result(
    *,
    regulation_state: RegulationState,
    capability_state: CapabilityState,
    context: AffordanceContext,
    reason: str,
) -> AffordanceResult:
    gate = evaluate_affordance_landscape_for_downstream(
        (), require_available=context.require_available_candidates
    )
    abstention = AffordanceAbstentionMarker(reason=reason)
    summary = AffordanceSetSummary(
        total_candidates=0,
        available_count=0,
        blocked_count=0,
        unavailable_count=0,
        unsafe_count=0,
        provisional_count=0,
        no_selection_performed=True,
        reason="abstained due to invalid contracts",
    )
    telemetry = build_affordance_telemetry(
        regulation_snapshot={"error": "invalid-regulation-input"},
        capability_state=capability_state,
        candidates=(),
        gate=gate,
        confidence=RegulationConfidence.LOW,
        abstain_reason=reason,
        source_lineage=context.source_lineage,
        attempted_paths=ATTEMPTED_AFFORDANCE_PATHS,
        causal_basis="invalid regulation/capability input -> abstain",
    )
    return AffordanceResult(
        regulation_state=regulation_state,
        candidates=(),
        summary=summary,
        gate=gate,
        telemetry=telemetry,
        abstention=abstention,
    )
