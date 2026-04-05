from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import uuid4

from substrate.affordances.models import AffordanceResult
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.regulation.models import (
    NeedAxis,
    RegulationResult,
    RegulationState,
    TradeoffState,
)
from substrate.regulatory_preferences.models import (
    PreferenceState,
    PreferenceUpdateResult,
)
from substrate.stream_kernel.models import (
    CarryoverClass,
    StreamBranchStatus,
    StreamCarryoverItem,
    StreamDecayState,
    StreamInterruptionStatus,
    StreamKernelContext,
    StreamKernelResult,
    StreamLedgerEvent,
    StreamLedgerEventKind,
    StreamLinkDecision,
    StreamKernelState,
)
from substrate.stream_kernel.policy import evaluate_stream_kernel_downstream_gate
from substrate.stream_kernel.telemetry import (
    build_stream_kernel_telemetry,
    stream_kernel_result_snapshot,
)
from substrate.transition import execute_transition
from substrate.viability_control.models import (
    ViabilityControlDirective,
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityDirectiveType,
    ViabilityEscalationStage,
)


ATTEMPTED_STREAM_KERNEL_PATHS: tuple[str, ...] = (
    "stream_kernel.validate_typed_inputs",
    "stream_kernel.collect_phase_native_anchors",
    "stream_kernel.merge_prior_carryover",
    "stream_kernel.interruption_resume_handling",
    "stream_kernel.link_decision",
    "stream_kernel.branch_decision",
    "stream_kernel.decay_and_release",
    "stream_kernel.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class _CarryoverSeed:
    carryover_class: CarryoverClass
    anchor_key: str
    source_ref: str
    strength: float
    provisional: bool
    reason: str


def build_stream_kernel(
    regulation_state_or_result: RegulationState | RegulationResult,
    affordance_result: AffordanceResult,
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
    context: StreamKernelContext | None = None,
) -> StreamKernelResult:
    context = context or StreamKernelContext()
    if not isinstance(context, StreamKernelContext):
        raise TypeError("context must be StreamKernelContext")
    if context.step_delta < 1:
        raise ValueError("context.step_delta must be >= 1")

    regulation_state, tradeoff_state, regulation_ref = _extract_regulation_input(
        regulation_state_or_result
    )
    preference_state, preference_ref = _extract_preference_input(
        preference_state_or_result
    )
    viability_state, viability_directives, viability_ref = _extract_viability_input(
        viability_state_or_result
    )
    if not isinstance(affordance_result, AffordanceResult):
        raise TypeError("build_stream_kernel requires typed AffordanceResult")

    prior = context.prior_stream_state
    if prior is not None and not isinstance(prior, StreamKernelState):
        raise TypeError("context.prior_stream_state must be StreamKernelState")

    seeds, unresolved_anchors, pending_operations = _collect_carryover_seeds(
        regulation_state=regulation_state,
        tradeoff_state=tradeoff_state,
        affordance_result=affordance_result,
        preference_state=preference_state,
        viability_state=viability_state,
        viability_directives=viability_directives,
        context=context,
        regulation_ref=regulation_ref,
        preference_ref=preference_ref,
        viability_ref=viability_ref,
    )

    seed_map = {
        (seed.carryover_class, seed.anchor_key): seed
        for seed in seeds
    }
    seed_classes = {seed.carryover_class for seed in seeds}
    held_focus_only = seed_classes == {CarryoverClass.HELD_FOCUS_ANCHOR}
    survival_only = seed_classes == {CarryoverClass.SURVIVAL_VIABILITY_ANCHOR}
    stale_pressure = bool(
        prior is not None
        and (
            prior.decay_state in {StreamDecayState.DECAYING, StreamDecayState.STALE}
            or bool(prior.stale_markers)
        )
    )
    interruption_seed_present = CarryoverClass.INTERRUPTION_MARKER in seed_classes
    prior_map = (
        {(item.carryover_class, item.anchor_key): item for item in prior.carryover_items}
        if prior is not None
        else {}
    )
    matched_seed_keys = tuple(
        key for key in seed_map if key in prior_map and not context.disable_anchor_linking
    )
    matched_ratio = (
        len(matched_seed_keys) / max(1, len(seed_map))
        if seed_map and not context.disable_anchor_linking
        else 0.0
    )

    (
        link_decision,
        continuity_confidence,
        interruption_status,
        branch_status,
    ) = _decide_stream_topology(
        prior=prior,
        context=context,
        seed_count=len(seed_map),
        matched_seed_count=len(matched_seed_keys),
        matched_ratio=matched_ratio,
        held_focus_only=held_focus_only,
        survival_only=survival_only,
        interruption_seed_present=interruption_seed_present,
        stale_pressure=stale_pressure,
    )

    stream_id = _derive_stream_id(
        prior=prior,
        decision=link_decision,
    )
    sequence_index = _derive_sequence_index(prior=prior, stream_id=stream_id)
    carryover_items, stale_markers, decay_state, ledger_events = _merge_and_decay_items(
        prior=prior,
        stream_id=stream_id,
        sequence_index=sequence_index,
        seed_map=seed_map,
        matched_seed_keys=matched_seed_keys,
        link_decision=link_decision,
        interruption_status=interruption_status,
        context=context,
    )

    if link_decision == StreamLinkDecision.FORCED_RELEASE:
        unresolved_anchors = ()
        pending_operations = ()

    state = StreamKernelState(
        stream_id=stream_id,
        sequence_index=sequence_index,
        link_decision=link_decision,
        carryover_items=carryover_items,
        unresolved_anchors=unresolved_anchors,
        pending_operations=pending_operations,
        interruption_status=interruption_status,
        branch_status=branch_status,
        decay_state=decay_state,
        stale_markers=stale_markers,
        continuity_confidence=continuity_confidence,
        source_regulation_ref=regulation_ref,
        source_affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
        source_preference_ref=preference_ref,
        source_viability_ref=viability_ref,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *context.source_lineage,
                    *affordance_result.telemetry.source_lineage,
                )
            )
        ),
        last_update_provenance="c01.stream_kernel_from_r01_r02_r03_r04",
    )
    gate = evaluate_stream_kernel_downstream_gate(state)
    telemetry = build_stream_kernel_telemetry(
        state=state,
        ledger_events=ledger_events,
        attempted_paths=ATTEMPTED_STREAM_KERNEL_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "typed carry-over linkage from R04 viability pressure, R03 unresolved preference traces, and R01/R02 process context"
        ),
    )
    abstain = bool(
        link_decision
        in {
            StreamLinkDecision.AMBIGUOUS_LINK,
            StreamLinkDecision.FORCED_NEW_STREAM,
        }
        and continuity_confidence < 0.45
    )
    abstain_reason = (
        "insufficient_delta_for_claim"
        if abstain
        else None
    )
    return StreamKernelResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_downstream_scheduler_selection_performed=True,
        no_transcript_replay_dependency=True,
        no_memory_retrieval_dependency=True,
        no_planner_hidden_flag_dependency=True,
    )


def stream_kernel_result_to_payload(result: StreamKernelResult) -> dict[str, object]:
    return stream_kernel_result_snapshot(result)


def persist_stream_kernel_result_via_f01(
    *,
    result: StreamKernelResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("c01-stream-kernel-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"stream-kernel-step-{result.state.sequence_index}",
            "stream_kernel_snapshot": stream_kernel_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_regulation_input(
    regulation_state_or_result: RegulationState | RegulationResult,
) -> tuple[RegulationState, TradeoffState | None, str]:
    if isinstance(regulation_state_or_result, RegulationResult):
        state = regulation_state_or_result.state
        return (
            state,
            regulation_state_or_result.tradeoff,
            f"regulation-step-{state.last_updated_step}",
        )
    if isinstance(regulation_state_or_result, RegulationState):
        return (
            regulation_state_or_result,
            None,
            f"regulation-step-{regulation_state_or_result.last_updated_step}",
        )
    raise TypeError("build_stream_kernel requires RegulationState or RegulationResult")


def _extract_preference_input(
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
) -> tuple[PreferenceState, str]:
    if isinstance(preference_state_or_result, PreferenceUpdateResult):
        state = preference_state_or_result.updated_preference_state
        return state, f"preference-step-{state.last_updated_step}:{state.schema_version}"
    if isinstance(preference_state_or_result, PreferenceState):
        return (
            preference_state_or_result,
            f"preference-step-{preference_state_or_result.last_updated_step}:{preference_state_or_result.schema_version}",
        )
    raise TypeError("build_stream_kernel requires PreferenceState or PreferenceUpdateResult")


def _extract_viability_input(
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
) -> tuple[ViabilityControlState, tuple[ViabilityControlDirective, ...], str]:
    if isinstance(viability_state_or_result, ViabilityControlResult):
        state = viability_state_or_result.state
        return (
            state,
            viability_state_or_result.directives,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    if isinstance(viability_state_or_result, ViabilityControlState):
        state = viability_state_or_result
        return (
            state,
            (),
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    raise TypeError("build_stream_kernel requires ViabilityControlState or ViabilityControlResult")


def _collect_carryover_seeds(
    *,
    regulation_state: RegulationState,
    tradeoff_state: TradeoffState | None,
    affordance_result: AffordanceResult,
    preference_state: PreferenceState,
    viability_state: ViabilityControlState,
    viability_directives: tuple[ViabilityControlDirective, ...],
    context: StreamKernelContext,
    regulation_ref: str,
    preference_ref: str,
    viability_ref: str,
) -> tuple[tuple[_CarryoverSeed, ...], tuple[str, ...], tuple[str, ...]]:
    seeds: list[_CarryoverSeed] = []
    unresolved_anchors: list[str] = []
    pending_operations: list[str] = []

    if (
        viability_state.escalation_stage != ViabilityEscalationStage.BASELINE
        or viability_state.pressure_level >= 0.35
    ):
        affected = "-".join(axis.value for axis in viability_state.affected_need_ids) or "none"
        anchor_key = f"viability:{affected}:{viability_state.escalation_stage.value}"
        unresolved_anchors.append(anchor_key)
        pending_operations.append("resolve_viability_pressure")
        seeds.append(
            _CarryoverSeed(
                carryover_class=CarryoverClass.SURVIVAL_VIABILITY_ANCHOR,
                anchor_key=anchor_key,
                source_ref=viability_ref,
                strength=max(0.3, min(1.0, viability_state.pressure_level)),
                provisional=viability_state.no_strong_override_claim,
                reason="r04 survival pressure remains unresolved across cycle boundary",
            )
        )

    if preference_state.unresolved_updates:
        anchor_key = f"preference-unresolved:{len(preference_state.unresolved_updates)}"
        unresolved_anchors.append(anchor_key)
        pending_operations.append("resolve_preference_attribution")
        seeds.append(
            _CarryoverSeed(
                carryover_class=CarryoverClass.UNRESOLVED_OPERATIONAL_PROCESS,
                anchor_key=anchor_key,
                source_ref=preference_ref,
                strength=min(1.0, 0.3 + (0.15 * len(preference_state.unresolved_updates))),
                provisional=True,
                reason="r03 unresolved updates remain open and must carry over",
            )
        )

    dominant_axis = None
    if tradeoff_state is not None:
        dominant_axis = tradeoff_state.dominant_axis
    if dominant_axis is None:
        dominant_axis = _dominant_regulation_axis(regulation_state)
    if dominant_axis is not None:
        anchor_key = f"focus:{dominant_axis.value}"
        seeds.append(
            _CarryoverSeed(
                carryover_class=CarryoverClass.HELD_FOCUS_ANCHOR,
                anchor_key=anchor_key,
                source_ref=regulation_ref,
                strength=0.45,
                provisional=regulation_state.confidence.value != "high",
                reason="r01 dominant unresolved axis keeps focus continuity",
            )
        )

    viability_pressure_active = (
        viability_state.escalation_stage != ViabilityEscalationStage.BASELINE
        or viability_state.pressure_level >= 0.35
    )
    if any(
        directive.directive_type
        in {
            ViabilityDirectiveType.INTERRUPT_RECOMMENDATION,
            ViabilityDirectiveType.PROTECTIVE_MODE_REQUEST,
        }
        for directive in viability_directives
    ) or (affordance_result.summary.available_count == 0 and viability_pressure_active):
        anchor_key = "pending-output-or-recovery"
        pending_operations.append("pending_output_or_recovery")
        seeds.append(
            _CarryoverSeed(
                carryover_class=CarryoverClass.PENDING_OUTPUT_OR_RECOVERY,
                anchor_key=anchor_key,
                source_ref=viability_ref,
                strength=0.55,
                provisional=True,
                reason="pending output/recovery remains unresolved at cycle boundary",
            )
        )

    if context.interruption_signal:
        anchor_key = "interruption:signal"
        pending_operations.append("resume_interrupted_process")
        seeds.append(
            _CarryoverSeed(
                carryover_class=CarryoverClass.INTERRUPTION_MARKER,
                anchor_key=anchor_key,
                source_ref=viability_ref,
                strength=0.6,
                provisional=False,
                reason="explicit interruption marker requires resumability handling",
            )
        )

    return (
        tuple(seeds),
        tuple(dict.fromkeys(unresolved_anchors)),
        tuple(dict.fromkeys(pending_operations)),
    )


def _dominant_regulation_axis(regulation_state: RegulationState) -> NeedAxis | None:
    if not regulation_state.needs:
        return None
    top = max(
        regulation_state.needs,
        key=lambda item: item.pressure + (item.deviation * 0.45),
    )
    if top.pressure <= 0.0 and top.deviation <= 0.0:
        return None
    return top.axis


def _decide_stream_topology(
    *,
    prior: StreamKernelState | None,
    context: StreamKernelContext,
    seed_count: int,
    matched_seed_count: int,
    matched_ratio: float,
    held_focus_only: bool,
    survival_only: bool,
    interruption_seed_present: bool,
    stale_pressure: bool,
) -> tuple[
    StreamLinkDecision,
    float,
    StreamInterruptionStatus,
    StreamBranchStatus,
]:
    interruption = StreamInterruptionStatus.NONE
    branch = StreamBranchStatus.NONE
    confidence = 0.65

    if prior is None:
        decision = StreamLinkDecision.STARTED_NEW_STREAM
        confidence = 0.92 if seed_count > 0 else 0.78
    elif context.force_new_stream:
        decision = StreamLinkDecision.FORCED_NEW_STREAM
        confidence = 0.25
    elif context.interruption_signal:
        decision = StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION
        interruption = StreamInterruptionStatus.INTERRUPTED
        confidence = 0.42
    elif (
        prior.interruption_status == StreamInterruptionStatus.INTERRUPTED
        and not context.resume_signal
    ):
        interruption = StreamInterruptionStatus.INTERRUPTED
        if context.require_strong_link:
            decision = StreamLinkDecision.AMBIGUOUS_LINK
            confidence = 0.34
        else:
            decision = StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION
            confidence = 0.46
    elif context.resume_signal and prior.interruption_status == StreamInterruptionStatus.INTERRUPTED:
        if matched_seed_count > 0:
            decision = StreamLinkDecision.RESUMED_INTERRUPTED_STREAM
            interruption = StreamInterruptionStatus.RESUMED
            confidence = 0.82
        else:
            decision = StreamLinkDecision.AMBIGUOUS_LINK
            confidence = 0.34
    elif seed_count == 0 and prior.carryover_items:
        decision = StreamLinkDecision.FORCED_RELEASE
        confidence = 0.44
    elif seed_count > 0 and matched_seed_count == 0 and context.require_strong_link:
        decision = StreamLinkDecision.AMBIGUOUS_LINK
        confidence = 0.35
    elif (
        seed_count > 0
        and context.require_strong_link
        and matched_ratio < 0.75
    ):
        decision = StreamLinkDecision.AMBIGUOUS_LINK
        confidence = 0.38
    elif seed_count > 0 and matched_seed_count == 0:
        decision = StreamLinkDecision.FORCED_NEW_STREAM
        confidence = 0.4
    elif seed_count > matched_seed_count and context.allow_branch_opening:
        decision = StreamLinkDecision.OPENED_BRANCH
        branch = StreamBranchStatus.BRANCH_OPENED
        confidence = max(0.5, min(0.72, 0.42 + (0.3 * matched_ratio)))
    elif matched_ratio >= 0.75:
        decision = StreamLinkDecision.CONTINUED_EXISTING_STREAM
        confidence = 0.88
    elif matched_ratio >= 0.45:
        decision = StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION
        confidence = 0.58
    else:
        decision = StreamLinkDecision.AMBIGUOUS_LINK
        confidence = 0.36

    if (
        prior is not None
        and prior.branch_status == StreamBranchStatus.BRANCH_OPENED
        and decision == StreamLinkDecision.OPENED_BRANCH
    ):
        branch = StreamBranchStatus.BRANCH_CONFLICT
        confidence = min(confidence, 0.28)

    if context.disable_anchor_linking and prior is not None:
        if decision in {
            StreamLinkDecision.CONTINUED_EXISTING_STREAM,
            StreamLinkDecision.RESUMED_INTERRUPTED_STREAM,
            StreamLinkDecision.OPENED_BRANCH,
            StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
        }:
            decision = StreamLinkDecision.FORCED_NEW_STREAM
            confidence = min(confidence, 0.22)

    if held_focus_only:
        if decision == StreamLinkDecision.CONTINUED_EXISTING_STREAM:
            decision = StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION
        if decision in {
            StreamLinkDecision.CONTINUED_EXISTING_STREAM,
            StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
            StreamLinkDecision.OPENED_BRANCH,
        }:
            confidence = min(confidence, 0.52)

    if survival_only and stale_pressure:
        if decision == StreamLinkDecision.CONTINUED_EXISTING_STREAM:
            decision = StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION
        if decision == StreamLinkDecision.OPENED_BRANCH and context.require_strong_link:
            decision = StreamLinkDecision.AMBIGUOUS_LINK
        confidence = min(confidence, 0.5)

    if interruption_seed_present and decision == StreamLinkDecision.CONTINUED_EXISTING_STREAM:
        decision = StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION
        interruption = StreamInterruptionStatus.INTERRUPTED
        confidence = min(confidence, 0.48)

    return decision, round(confidence, 4), interruption, branch


def _derive_stream_id(
    *,
    prior: StreamKernelState | None,
    decision: StreamLinkDecision,
) -> str:
    if prior is None:
        return f"stream-{uuid4().hex[:10]}"
    if decision in {
        StreamLinkDecision.CONTINUED_EXISTING_STREAM,
        StreamLinkDecision.RESUMED_INTERRUPTED_STREAM,
        StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
        StreamLinkDecision.OPENED_BRANCH,
    }:
        return prior.stream_id
    return f"stream-{uuid4().hex[:10]}"


def _derive_sequence_index(
    *,
    prior: StreamKernelState | None,
    stream_id: str,
) -> int:
    if prior is None or prior.stream_id != stream_id:
        return 0
    return prior.sequence_index + 1


def _merge_and_decay_items(
    *,
    prior: StreamKernelState | None,
    stream_id: str,
    sequence_index: int,
    seed_map: dict[tuple[CarryoverClass, str], _CarryoverSeed],
    matched_seed_keys: tuple[tuple[CarryoverClass, str], ...],
    link_decision: StreamLinkDecision,
    interruption_status: StreamInterruptionStatus,
    context: StreamKernelContext,
) -> tuple[
    tuple[StreamCarryoverItem, ...],
    tuple[str, ...],
    StreamDecayState,
    tuple[StreamLedgerEvent, ...],
]:
    carryover: list[StreamCarryoverItem] = []
    stale_markers: list[str] = []
    ledger: list[StreamLedgerEvent] = []
    released_count = 0
    stale_count = 0

    prior_map = (
        {(item.carryover_class, item.anchor_key): item for item in prior.carryover_items}
        if prior is not None
        else {}
    )
    for key, seed in seed_map.items():
        if key in prior_map and key in matched_seed_keys:
            prev = prior_map[key]
            item = replace(
                prev,
                source_ref=seed.source_ref,
                strength=max(prev.strength, seed.strength),
                last_seen_sequence_index=sequence_index,
                decay_steps=0,
                stale=False,
                released=False,
                provisional=seed.provisional,
                reason=seed.reason,
            )
            event_kind = StreamLedgerEventKind.RETAIN
            if interruption_status == StreamInterruptionStatus.RESUMED:
                event_kind = StreamLedgerEventKind.RESUME
            ledger.append(
                _ledger_event(
                    event_kind=event_kind,
                    stream_id=stream_id,
                    item_id=item.item_id,
                    anchor_key=item.anchor_key,
                    reason=item.reason,
                    reason_code=f"carryover_{event_kind.value}",
                )
            )
            carryover.append(item)
        else:
            item = StreamCarryoverItem(
                item_id=f"carryover-{uuid4().hex[:10]}",
                carryover_class=seed.carryover_class,
                anchor_key=seed.anchor_key,
                source_ref=seed.source_ref,
                strength=seed.strength,
                created_sequence_index=sequence_index,
                last_seen_sequence_index=sequence_index,
                decay_steps=0,
                stale=False,
                provisional=seed.provisional,
                released=False,
                reason=seed.reason,
            )
            ledger.append(
                _ledger_event(
                    event_kind=(
                        StreamLedgerEventKind.INTERRUPT
                        if seed.carryover_class == CarryoverClass.INTERRUPTION_MARKER
                        else StreamLedgerEventKind.NEW_STREAM
                    ),
                    stream_id=stream_id,
                    item_id=item.item_id,
                    anchor_key=item.anchor_key,
                    reason=item.reason,
                    reason_code="carryover_new",
                )
            )
            carryover.append(item)

    for key, prior_item in prior_map.items():
        if key in seed_map:
            continue
        next_decay = prior_item.decay_steps + context.step_delta
        if next_decay >= context.release_after_steps:
            released_count += 1
            stale_markers.append(f"released:{prior_item.anchor_key}")
            ledger.append(
                _ledger_event(
                    event_kind=StreamLedgerEventKind.RELEASE,
                    stream_id=stream_id,
                    item_id=prior_item.item_id,
                    anchor_key=prior_item.anchor_key,
                    reason="carryover released after closure/decay threshold",
                    reason_code="release_after_decay",
                )
            )
            continue
        stale = next_decay >= context.stale_after_steps
        if stale:
            stale_count += 1
            stale_markers.append(f"stale:{prior_item.anchor_key}")
        decayed_item = replace(
            prior_item,
            decay_steps=next_decay,
            stale=stale,
            released=False,
            reason=(
                "carryover stale due to unresolved refresh gap"
                if stale
                else "carryover decaying awaiting refresh"
            ),
        )
        carryover.append(decayed_item)
        ledger.append(
            _ledger_event(
                event_kind=(
                    StreamLedgerEventKind.STALE if stale else StreamLedgerEventKind.DECAY
                ),
                stream_id=stream_id,
                item_id=prior_item.item_id,
                anchor_key=prior_item.anchor_key,
                reason=decayed_item.reason,
                reason_code=(
                    "stale_carryover" if stale else "decaying_carryover"
                ),
            )
        )

    if link_decision == StreamLinkDecision.OPENED_BRANCH:
        ledger.append(
            _ledger_event(
                event_kind=StreamLedgerEventKind.BRANCH,
                stream_id=stream_id,
                item_id=None,
                anchor_key=None,
                reason="new branch opened because carry-over partially diverged",
                reason_code="branch_opened",
            )
        )

    if link_decision == StreamLinkDecision.FORCED_RELEASE:
        carryover = tuple()
        stale_markers = tuple(dict.fromkeys((*stale_markers, "forced_release")))
        return (
            (),
            stale_markers,
            StreamDecayState.RELEASED,
            tuple(ledger),
        )

    if released_count > 0 and not carryover:
        decay_state = StreamDecayState.RELEASED
    elif stale_count > 0:
        decay_state = StreamDecayState.STALE
    elif prior is not None and len(carryover) < len(prior.carryover_items):
        decay_state = StreamDecayState.DECAYING
    else:
        decay_state = StreamDecayState.NONE

    return (
        tuple(carryover),
        tuple(dict.fromkeys(stale_markers)),
        decay_state,
        tuple(ledger),
    )


def _ledger_event(
    *,
    event_kind: StreamLedgerEventKind,
    stream_id: str,
    item_id: str | None,
    anchor_key: str | None,
    reason: str,
    reason_code: str,
) -> StreamLedgerEvent:
    return StreamLedgerEvent(
        event_id=f"stream-ledger-{uuid4().hex[:10]}",
        event_kind=event_kind,
        stream_id=stream_id,
        item_id=item_id,
        anchor_key=anchor_key,
        reason=reason,
        reason_code=reason_code,
        provenance="c01.stream_kernel_ledger",
    )
