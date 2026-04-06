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
from substrate.regulation.models import RegulationResult, RegulationState
from substrate.regulatory_preferences.models import (
    PreferenceState,
    PreferenceUpdateResult,
)
from substrate.stream_kernel.models import (
    CarryoverClass,
    StreamKernelResult,
    StreamKernelState,
)
from substrate.tension_scheduler.models import (
    TensionDecayState,
    TensionKind,
    TensionLedgerEvent,
    TensionLedgerEventKind,
    TensionLifecycleStatus,
    TensionScheduleEntry,
    TensionSignalOrigin,
    TensionSchedulerContext,
    TensionSchedulerResult,
    TensionWakeCause,
    TensionSchedulingMode,
    TensionSchedulerState,
)
from substrate.tension_scheduler.policy import evaluate_tension_scheduler_downstream_gate
from substrate.tension_scheduler.telemetry import (
    build_tension_scheduler_telemetry,
    tension_scheduler_result_snapshot,
)
from substrate.transition import execute_transition
from substrate.viability_control.models import (
    ViabilityControlDirective,
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityDirectiveType,
    ViabilityEscalationStage,
)


ATTEMPTED_TENSION_SCHEDULER_PATHS: tuple[str, ...] = (
    "tension_scheduler.validate_typed_inputs",
    "tension_scheduler.extract_candidates_from_c01",
    "tension_scheduler.normalize_lifecycle_entries",
    "tension_scheduler.scheduling_decision",
    "tension_scheduler.suppression_bookkeeping",
    "tension_scheduler.wake_trigger_reactivation",
    "tension_scheduler.closure_reopen_logic",
    "tension_scheduler.decay_stale_release",
    "tension_scheduler.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class _TensionCandidate:
    tension_kind: TensionKind
    causal_anchor: str
    source_ref: str
    priority_seed: float
    wake_conditions: tuple[str, ...]
    closure_criteria: tuple[str, ...]
    reopen_criteria: tuple[str, ...]
    confidence: float
    priority_basis_present: bool
    trigger_unknown: bool
    reason: str


_TRUSTED_SIGNAL_ORIGINS: frozenset[TensionSignalOrigin] = frozenset(
    {
        TensionSignalOrigin.C02_INTERNAL,
        TensionSignalOrigin.C01_PHASE_NATIVE,
        TensionSignalOrigin.R_PHASE_NATIVE,
    }
)


def build_tension_scheduler(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
    regulation_state_or_result: RegulationState | RegulationResult,
    affordance_result: AffordanceResult,
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
    context: TensionSchedulerContext | None = None,
) -> TensionSchedulerResult:
    context = context or TensionSchedulerContext()
    if not isinstance(context, TensionSchedulerContext):
        raise TypeError("context must be TensionSchedulerContext")
    if context.step_delta < 1:
        raise ValueError("context.step_delta must be >= 1")
    if not isinstance(affordance_result, AffordanceResult):
        raise TypeError("build_tension_scheduler requires typed AffordanceResult")

    stream_state = _extract_stream_input(stream_state_or_result)
    regulation_state, regulation_ref = _extract_regulation_input(regulation_state_or_result)
    preference_state, preference_ref = _extract_preference_input(preference_state_or_result)
    viability_state, viability_directives, viability_ref = _extract_viability_input(
        viability_state_or_result
    )
    prior = context.prior_scheduler_state
    if prior is not None and not isinstance(prior, TensionSchedulerState):
        raise TypeError("context.prior_scheduler_state must be TensionSchedulerState")

    candidates = _extract_candidates(
        stream_state=stream_state,
        regulation_state=regulation_state,
        preference_state=preference_state,
        viability_state=viability_state,
        viability_directives=viability_directives,
    )
    prior_map = (
        {(entry.tension_kind, entry.causal_anchor): entry for entry in prior.tensions}
        if prior is not None
        else {}
    )
    candidate_keys = {(candidate.tension_kind, candidate.causal_anchor) for candidate in candidates}

    entries: list[TensionScheduleEntry] = []
    ledger_events: list[TensionLedgerEvent] = []
    for candidate in candidates:
        prior_entry = prior_map.get((candidate.tension_kind, candidate.causal_anchor))
        entry = _schedule_entry(
            candidate=candidate,
            prior_entry=prior_entry,
            stream_state=stream_state,
            context=context,
        )
        entries.append(entry)
        ledger_events.append(
            _ledger_event_for_entry(
                entry=entry,
                prior_entry=prior_entry,
                stream_id=stream_state.stream_id,
            )
        )

    for key, prior_entry in prior_map.items():
        if key in candidate_keys:
            continue
        decayed = _decay_unseen_entry(
            prior_entry=prior_entry,
            stream_state=stream_state,
            context=context,
        )
        entries.append(decayed)
        ledger_events.append(
            _ledger_event_for_entry(
                entry=decayed,
                prior_entry=prior_entry,
                stream_id=stream_state.stream_id,
            )
        )

    entries = sorted(entries, key=lambda item: item.tension_id)
    active_ids = tuple(
        entry.tension_id
        for entry in entries
        if entry.current_status in {TensionLifecycleStatus.ACTIVE, TensionLifecycleStatus.REACTIVATED}
    )
    deferred_ids = tuple(
        entry.tension_id
        for entry in entries
        if entry.current_status == TensionLifecycleStatus.DEFERRED
    )
    dormant_ids = tuple(
        entry.tension_id
        for entry in entries
        if entry.current_status == TensionLifecycleStatus.DORMANT
    )
    stale_ids = tuple(
        entry.tension_id
        for entry in entries
        if entry.current_status == TensionLifecycleStatus.STALE
    )
    closed_ids = tuple(
        entry.tension_id
        for entry in entries
        if entry.current_status == TensionLifecycleStatus.CLOSED
    )
    wake_queue = tuple(
        entry.tension_id
        for entry in entries
        if entry.scheduling_mode
        in {
            TensionSchedulingMode.REVISIT_NOW,
            TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
            TensionSchedulingMode.NO_SAFE_DEFER_CLAIM,
        }
    )
    confidence = (
        round(sum(entry.confidence for entry in entries) / max(1, len(entries)), 4)
        if entries
        else 0.0
    )
    state = TensionSchedulerState(
        scheduler_id=f"tension-scheduler-{stream_state.stream_id}",
        source_stream_id=stream_state.stream_id,
        source_stream_sequence_index=stream_state.sequence_index,
        tensions=tuple(entries),
        active_tension_ids=active_ids,
        deferred_tension_ids=deferred_ids,
        dormant_tension_ids=dormant_ids,
        stale_tension_ids=stale_ids,
        closed_tension_ids=closed_ids,
        wake_queue_tension_ids=wake_queue,
        suppression_active=any(
            entry.scheduling_mode == TensionSchedulingMode.SUPPRESS_TEMPORARILY
            for entry in entries
        ),
        confidence=confidence,
        source_c01_state_ref=f"{stream_state.stream_id}@{stream_state.sequence_index}",
        source_regulation_ref=regulation_ref,
        source_affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
        source_preference_ref=preference_ref,
        source_viability_ref=viability_ref,
        source_lineage=tuple(dict.fromkeys((*context.source_lineage, *stream_state.source_lineage))),
        last_update_provenance="c02.tension_scheduler_from_c01_r01_r02_r03_r04",
    )
    gate = evaluate_tension_scheduler_downstream_gate(state)
    telemetry = build_tension_scheduler_telemetry(
        state=state,
        ledger_events=tuple(ledger_events),
        attempted_paths=ATTEMPTED_TENSION_SCHEDULER_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "C01 carry-over anchors normalized into unresolved tension lifecycle with explicit revisit/defer/suppress/closure/reopen transitions"
        ),
    )
    abstain = bool(not entries and bool(stream_state.unresolved_anchors))
    abstain_reason = "no_schedulable_tension_candidates" if abstain else None
    return TensionSchedulerResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_planner_backlog_dependency=True,
        no_retrieval_scheduler_dependency=True,
    )


def tension_scheduler_result_to_payload(result: TensionSchedulerResult) -> dict[str, object]:
    return tension_scheduler_result_snapshot(result)


def persist_tension_scheduler_result_via_f01(
    *,
    result: TensionSchedulerResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("c02-tension-scheduler-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"tension-scheduler-step-{result.state.source_stream_sequence_index}",
            "tension_scheduler_snapshot": tension_scheduler_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_stream_input(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
) -> StreamKernelState:
    if isinstance(stream_state_or_result, StreamKernelResult):
        return stream_state_or_result.state
    if isinstance(stream_state_or_result, StreamKernelState):
        return stream_state_or_result
    raise TypeError("build_tension_scheduler requires StreamKernelState or StreamKernelResult")


def _extract_regulation_input(
    regulation_state_or_result: RegulationState | RegulationResult,
) -> tuple[RegulationState, str]:
    if isinstance(regulation_state_or_result, RegulationResult):
        state = regulation_state_or_result.state
        return state, f"regulation-step-{state.last_updated_step}"
    if isinstance(regulation_state_or_result, RegulationState):
        return (
            regulation_state_or_result,
            f"regulation-step-{regulation_state_or_result.last_updated_step}",
        )
    raise TypeError("build_tension_scheduler requires RegulationState or RegulationResult")


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
    raise TypeError("build_tension_scheduler requires PreferenceState or PreferenceUpdateResult")


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
    raise TypeError("build_tension_scheduler requires ViabilityControlState or ViabilityControlResult")


def _extract_candidates(
    *,
    stream_state: StreamKernelState,
    regulation_state: RegulationState,
    preference_state: PreferenceState,
    viability_state: ViabilityControlState,
    viability_directives: tuple[ViabilityControlDirective, ...],
) -> tuple[_TensionCandidate, ...]:
    _ = regulation_state
    candidates: list[_TensionCandidate] = []
    for item in stream_state.carryover_items:
        kind, wake_conditions, reason = _kind_from_carryover(item.carryover_class)
        priority_seed = _priority_from_item(
            kind=kind,
            item_strength=item.strength,
            viability_state=viability_state,
            viability_directives=viability_directives,
            preference_state=preference_state,
        )
        confidence = round(
            max(0.15, min(1.0, (item.strength * 0.6) + (stream_state.continuity_confidence * 0.4))),
            4,
        )
        priority_basis_present = not (
            kind == TensionKind.FOCUS_DRIFT and len(stream_state.unresolved_anchors) == 0
        )
        closure = (f"closure_evidence:{item.anchor_key}",)
        reopen = (f"reopen_anchor:{item.anchor_key}", f"wake_trigger:{item.anchor_key}")
        candidates.append(
            _TensionCandidate(
                tension_kind=kind,
                causal_anchor=item.anchor_key,
                source_ref=item.source_ref,
                priority_seed=priority_seed,
                wake_conditions=wake_conditions,
                closure_criteria=closure,
                reopen_criteria=reopen,
                confidence=confidence,
                priority_basis_present=priority_basis_present,
                trigger_unknown=len(wake_conditions) == 0,
                reason=reason,
            )
        )

    for anchor in stream_state.unresolved_anchors:
        if any(candidate.causal_anchor == anchor for candidate in candidates):
            continue
        candidates.append(
            _TensionCandidate(
                tension_kind=TensionKind.UNRESOLVED_OPERATIONAL_PROCESS,
                causal_anchor=anchor,
                source_ref=f"{stream_state.stream_id}@{stream_state.sequence_index}",
                priority_seed=0.58,
                wake_conditions=("defer_window_expiry", "failed_adjacent_step"),
                closure_criteria=(f"closure_evidence:{anchor}",),
                reopen_criteria=(f"reopen_anchor:{anchor}",),
                confidence=max(0.25, stream_state.continuity_confidence),
                priority_basis_present=True,
                trigger_unknown=False,
                reason="c01 unresolved anchor normalized into schedule-able tension",
            )
        )
    return tuple(candidates)


def _kind_from_carryover(carryover_class: CarryoverClass) -> tuple[TensionKind, tuple[str, ...], str]:
    if carryover_class == CarryoverClass.SURVIVAL_VIABILITY_ANCHOR:
        return (
            TensionKind.VIABILITY_PRESSURE,
            ("worsening_pressure", "defer_window_expiry", "repeated_conflict"),
            "viability anchor requires temporal revisit discipline",
        )
    if carryover_class == CarryoverClass.UNRESOLVED_OPERATIONAL_PROCESS:
        return (
            TensionKind.UNRESOLVED_OPERATIONAL_PROCESS,
            ("failed_adjacent_step", "defer_window_expiry"),
            "unresolved operational process requires scheduled revisit",
        )
    if carryover_class == CarryoverClass.PENDING_OUTPUT_OR_RECOVERY:
        return (
            TensionKind.PENDING_RECOVERY,
            ("recovery_failure", "worsening_pressure", "defer_window_expiry"),
            "pending recovery cannot be treated as silent backlog",
        )
    if carryover_class == CarryoverClass.INTERRUPTION_MARKER:
        return (
            TensionKind.INTERRUPTION_CONTINUITY,
            ("explicit_resume", "defer_window_expiry"),
            "interruption continuity requires explicit wake/resume contract",
        )
    return (
        TensionKind.FOCUS_DRIFT,
        ("defer_window_expiry",),
        "focus drift requires bounded monitoring, not forced immediate revisit",
    )


def _priority_from_item(
    *,
    kind: TensionKind,
    item_strength: float,
    viability_state: ViabilityControlState,
    viability_directives: tuple[ViabilityControlDirective, ...],
    preference_state: PreferenceState,
) -> float:
    base = item_strength
    if kind == TensionKind.VIABILITY_PRESSURE:
        if viability_state.escalation_stage in {
            ViabilityEscalationStage.THREAT,
            ViabilityEscalationStage.CRITICAL,
        }:
            base += 0.28
        if viability_state.no_strong_override_claim:
            base -= 0.08
    elif kind == TensionKind.UNRESOLVED_OPERATIONAL_PROCESS:
        base += min(0.25, 0.05 * len(preference_state.unresolved_updates))
    elif kind == TensionKind.PENDING_RECOVERY:
        if any(
            directive.directive_type
            in {
                ViabilityDirectiveType.INTERRUPT_RECOMMENDATION,
                ViabilityDirectiveType.PROTECTIVE_MODE_REQUEST,
            }
            for directive in viability_directives
        ):
            base += 0.22
    elif kind == TensionKind.FOCUS_DRIFT:
        base -= 0.15
    return round(max(0.0, min(1.0, base)), 4)


def _schedule_entry(
    *,
    candidate: _TensionCandidate,
    prior_entry: TensionScheduleEntry | None,
    stream_state: StreamKernelState,
    context: TensionSchedulerContext,
) -> TensionScheduleEntry:
    sequence = stream_state.sequence_index
    explicit_wakes = set(context.explicit_wake_triggers)
    wake_scope = set(context.wake_anchor_scope)
    closure_refs = set(context.closure_evidence_anchor_keys)
    reopen_refs = set(context.reopen_anchor_keys)
    retrieval_refs = set(context.retrieved_episode_refs)
    wake_origin_trusted = context.wake_signal_origin in _TRUSTED_SIGNAL_ORIGINS
    closure_origin_trusted = context.closure_signal_origin in _TRUSTED_SIGNAL_ORIGINS
    reopen_origin_trusted = context.reopen_signal_origin in _TRUSTED_SIGNAL_ORIGINS
    weak_wake_signal_ignored = bool(explicit_wakes) and not wake_origin_trusted
    weak_closure_signal_ignored = bool(closure_refs) and not closure_origin_trusted
    weak_reopen_signal_ignored = bool(reopen_refs) and not reopen_origin_trusted
    wake_scope_matched = candidate.causal_anchor in wake_scope
    matched_wakes = tuple(
        sorted(
            trigger
            for trigger in candidate.wake_conditions
            if trigger in explicit_wakes and wake_scope_matched and wake_origin_trusted
        )
    )
    matched_reopen_signals = tuple(
        sorted(
            marker
            for marker in candidate.reopen_criteria
            if marker in explicit_wakes and wake_scope_matched and reopen_origin_trusted
        )
    )
    closure_evidence_present = (
        candidate.causal_anchor in closure_refs and closure_origin_trusted
    )
    explicit_reopen = (
        candidate.causal_anchor in reopen_refs and reopen_origin_trusted
    )
    retrieval_only = candidate.causal_anchor in retrieval_refs
    closure_uncertain = bool(
        (retrieval_only and not closure_evidence_present) or weak_closure_signal_ignored
    )
    scheduler_conflict = bool(closure_evidence_present and explicit_reopen)
    wake_cause = TensionWakeCause.NONE
    if explicit_reopen or matched_reopen_signals:
        wake_cause = TensionWakeCause.REOPEN_CONDITION
    elif matched_wakes:
        wake_cause = TensionWakeCause.EXPLICIT_SIGNAL

    shared_tension_id = (
        prior_entry.tension_id if prior_entry is not None else f"tension-{uuid4().hex[:10]}"
    )
    shared_created_index = (
        prior_entry.created_sequence_index if prior_entry is not None else sequence
    )
    shared_suppression_budget = (
        prior_entry.suppression_budget
        if prior_entry is not None
        else context.default_suppression_budget
    )
    shared_suppression_remaining = (
        prior_entry.suppression_remaining
        if prior_entry is not None
        else context.default_suppression_budget
    )

    if prior_entry is not None and prior_entry.current_status == TensionLifecycleStatus.CLOSED:
        if wake_cause == TensionWakeCause.REOPEN_CONDITION:
            return TensionScheduleEntry(
                tension_id=prior_entry.tension_id,
                source_stream_id=stream_state.stream_id,
                source_stream_sequence_index=sequence,
                tension_kind=candidate.tension_kind,
                causal_anchor=candidate.causal_anchor,
                current_status=TensionLifecycleStatus.REACTIVATED,
                revisit_priority=max(candidate.priority_seed, 0.7),
                scheduling_mode=TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
                earliest_revisit_step=sequence,
                wake_conditions=candidate.wake_conditions,
                matched_wake_triggers=tuple(
                    dict.fromkeys((*matched_reopen_signals, *matched_wakes))
                ),
                reactivation_cause=wake_cause,
                wake_scope_matched=wake_scope_matched,
                suppression_budget=prior_entry.suppression_budget,
                suppression_remaining=prior_entry.suppression_budget,
                decay_state=TensionDecayState.NONE,
                stale=False,
                closure_criteria=candidate.closure_criteria,
                reopen_criteria=candidate.reopen_criteria,
                confidence=max(candidate.confidence, 0.6),
                trigger_unknown=candidate.trigger_unknown,
                closure_uncertain=closure_uncertain,
                scheduler_conflict=scheduler_conflict,
                weak_wake_signal_ignored=weak_wake_signal_ignored,
                weak_closure_signal_ignored=weak_closure_signal_ignored,
                weak_reopen_signal_ignored=weak_reopen_signal_ignored,
                threshold_edge_downgrade_applied=False,
                kind_policy_applied=False,
                unschedulable=False,
                created_sequence_index=prior_entry.created_sequence_index,
                last_touched_sequence_index=sequence,
                inactive_steps=0,
                reason="closed tension reopened by explicit trigger",
                provenance="c02.reopen_due_to_trigger",
            )
        return TensionScheduleEntry(
            tension_id=prior_entry.tension_id,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=sequence,
            tension_kind=candidate.tension_kind,
            causal_anchor=candidate.causal_anchor,
            current_status=TensionLifecycleStatus.CLOSED,
            revisit_priority=0.0,
            scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
            earliest_revisit_step=None,
            wake_conditions=candidate.wake_conditions,
            matched_wake_triggers=(),
            reactivation_cause=TensionWakeCause.NONE,
            wake_scope_matched=wake_scope_matched,
            suppression_budget=prior_entry.suppression_budget,
            suppression_remaining=prior_entry.suppression_remaining,
            decay_state=TensionDecayState.NONE,
            stale=False,
            closure_criteria=candidate.closure_criteria,
            reopen_criteria=candidate.reopen_criteria,
            confidence=max(0.35, candidate.confidence),
            trigger_unknown=candidate.trigger_unknown,
            closure_uncertain=closure_uncertain,
            scheduler_conflict=scheduler_conflict,
            weak_wake_signal_ignored=weak_wake_signal_ignored,
            weak_closure_signal_ignored=weak_closure_signal_ignored,
            weak_reopen_signal_ignored=weak_reopen_signal_ignored,
            threshold_edge_downgrade_applied=False,
            kind_policy_applied=False,
            unschedulable=False,
            created_sequence_index=prior_entry.created_sequence_index,
            last_touched_sequence_index=sequence,
            inactive_steps=prior_entry.inactive_steps + context.step_delta,
            reason="closed tension remains closed without reopen trigger",
            provenance="c02.closed_monitor",
        )

    if closure_evidence_present and not scheduler_conflict:
        return TensionScheduleEntry(
            tension_id=prior_entry.tension_id if prior_entry is not None else f"tension-{uuid4().hex[:10]}",
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=sequence,
            tension_kind=candidate.tension_kind,
            causal_anchor=candidate.causal_anchor,
            current_status=TensionLifecycleStatus.CLOSED,
            revisit_priority=0.0,
            scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
            earliest_revisit_step=None,
            wake_conditions=candidate.wake_conditions,
            matched_wake_triggers=(),
            reactivation_cause=TensionWakeCause.NONE,
            wake_scope_matched=wake_scope_matched,
            suppression_budget=(prior_entry.suppression_budget if prior_entry is not None else context.default_suppression_budget),
            suppression_remaining=(prior_entry.suppression_remaining if prior_entry is not None else context.default_suppression_budget),
            decay_state=TensionDecayState.NONE,
            stale=False,
            closure_criteria=candidate.closure_criteria,
            reopen_criteria=candidate.reopen_criteria,
            confidence=max(0.45, candidate.confidence),
            trigger_unknown=candidate.trigger_unknown,
            closure_uncertain=False,
            scheduler_conflict=False,
            weak_wake_signal_ignored=weak_wake_signal_ignored,
            weak_closure_signal_ignored=weak_closure_signal_ignored,
            weak_reopen_signal_ignored=weak_reopen_signal_ignored,
            threshold_edge_downgrade_applied=False,
            kind_policy_applied=False,
            unschedulable=False,
            created_sequence_index=(prior_entry.created_sequence_index if prior_entry is not None else sequence),
            last_touched_sequence_index=sequence,
            inactive_steps=0,
            reason="closure evidence present; revisit suspended until explicit reopen",
            provenance="c02.closed_with_evidence",
            )

    if context.require_strong_priority_basis and not candidate.priority_basis_present:
        mode = (
            TensionSchedulingMode.NO_SAFE_DEFER_CLAIM
            if candidate.priority_seed >= 0.45
            else TensionSchedulingMode.UNSCHEDULABLE_TENSION
        )
        return TensionScheduleEntry(
            tension_id=shared_tension_id,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=sequence,
            tension_kind=candidate.tension_kind,
            causal_anchor=candidate.causal_anchor,
            current_status=TensionLifecycleStatus.ACTIVE,
            revisit_priority=max(candidate.priority_seed, 0.35),
            scheduling_mode=mode,
            earliest_revisit_step=sequence,
            wake_conditions=candidate.wake_conditions,
            matched_wake_triggers=(),
            reactivation_cause=TensionWakeCause.NONE,
            wake_scope_matched=wake_scope_matched,
            suppression_budget=shared_suppression_budget,
            suppression_remaining=shared_suppression_remaining,
            decay_state=TensionDecayState.NONE,
            stale=False,
            closure_criteria=candidate.closure_criteria,
            reopen_criteria=candidate.reopen_criteria,
            confidence=max(0.25, candidate.confidence - 0.2),
            trigger_unknown=candidate.trigger_unknown,
            closure_uncertain=closure_uncertain,
            scheduler_conflict=scheduler_conflict,
            weak_wake_signal_ignored=weak_wake_signal_ignored,
            weak_closure_signal_ignored=weak_closure_signal_ignored,
            weak_reopen_signal_ignored=weak_reopen_signal_ignored,
            threshold_edge_downgrade_applied=False,
            kind_policy_applied=False,
            unschedulable=True,
            created_sequence_index=shared_created_index,
            last_touched_sequence_index=sequence,
            inactive_steps=0,
            reason="insufficient_basis_for_priority; cannot claim safe defer",
            provenance="c02.unschedulable_or_no_safe_defer",
        )

    if wake_cause != TensionWakeCause.NONE:
        return TensionScheduleEntry(
            tension_id=shared_tension_id,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=sequence,
            tension_kind=candidate.tension_kind,
            causal_anchor=candidate.causal_anchor,
            current_status=TensionLifecycleStatus.REACTIVATED,
            revisit_priority=max(candidate.priority_seed, 0.72),
            scheduling_mode=TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
            earliest_revisit_step=sequence,
            wake_conditions=candidate.wake_conditions,
            matched_wake_triggers=tuple(
                dict.fromkeys((*matched_reopen_signals, *matched_wakes))
            ),
            reactivation_cause=wake_cause,
            wake_scope_matched=wake_scope_matched,
            suppression_budget=shared_suppression_budget,
            suppression_remaining=shared_suppression_budget,
            decay_state=TensionDecayState.NONE,
            stale=False,
            closure_criteria=candidate.closure_criteria,
            reopen_criteria=candidate.reopen_criteria,
            confidence=max(candidate.confidence, 0.6),
            trigger_unknown=candidate.trigger_unknown,
            closure_uncertain=closure_uncertain,
            scheduler_conflict=scheduler_conflict,
            weak_wake_signal_ignored=weak_wake_signal_ignored,
            weak_closure_signal_ignored=weak_closure_signal_ignored,
            weak_reopen_signal_ignored=weak_reopen_signal_ignored,
            threshold_edge_downgrade_applied=False,
            kind_policy_applied=False,
            unschedulable=False,
            created_sequence_index=shared_created_index,
            last_touched_sequence_index=sequence,
            inactive_steps=0,
            reason=f"lawful wake cause ({wake_cause.value}) reactivated tension",
            provenance="c02.reactivated_by_wake",
        )

    if (
        retrieval_only
        and prior_entry is not None
        and prior_entry.current_status
        in {
            TensionLifecycleStatus.DORMANT,
            TensionLifecycleStatus.STALE,
            TensionLifecycleStatus.CLOSED,
        }
        and not closure_evidence_present
        and not explicit_reopen
        and not matched_wakes
    ):
        return TensionScheduleEntry(
            tension_id=shared_tension_id,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=sequence,
            tension_kind=candidate.tension_kind,
            causal_anchor=candidate.causal_anchor,
            current_status=TensionLifecycleStatus.DORMANT,
            revisit_priority=min(candidate.priority_seed, 0.35),
            scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
            earliest_revisit_step=None,
            wake_conditions=candidate.wake_conditions,
            matched_wake_triggers=(),
            reactivation_cause=TensionWakeCause.NONE,
            wake_scope_matched=wake_scope_matched,
            suppression_budget=shared_suppression_budget,
            suppression_remaining=shared_suppression_remaining,
            decay_state=TensionDecayState.DECAYING,
            stale=prior_entry.stale,
            closure_criteria=candidate.closure_criteria,
            reopen_criteria=candidate.reopen_criteria,
            confidence=max(0.2, candidate.confidence - 0.25),
            trigger_unknown=candidate.trigger_unknown,
            closure_uncertain=True,
            scheduler_conflict=scheduler_conflict,
            weak_wake_signal_ignored=weak_wake_signal_ignored,
            weak_closure_signal_ignored=weak_closure_signal_ignored,
            weak_reopen_signal_ignored=weak_reopen_signal_ignored,
            threshold_edge_downgrade_applied=True,
            kind_policy_applied=False,
            unschedulable=False,
            created_sequence_index=shared_created_index,
            last_touched_sequence_index=sequence,
            inactive_steps=prior_entry.inactive_steps + context.step_delta,
            reason="retrieval signal alone cannot reopen tension without explicit reopen basis",
            provenance="c02.retrieval_without_reopen",
        )

    suppression_remaining = shared_suppression_remaining
    threshold_edge_downgrade_applied = False
    kind_policy_applied = False
    if candidate.priority_seed >= 0.83:
        status = TensionLifecycleStatus.ACTIVE
        mode = TensionSchedulingMode.REVISIT_NOW
        earliest = sequence
    elif candidate.priority_seed >= 0.58:
        status = TensionLifecycleStatus.DEFERRED
        mode = TensionSchedulingMode.DEFER_UNTIL_CONDITION
        earliest = sequence + 1
    elif candidate.priority_seed >= 0.52:
        status = TensionLifecycleStatus.DEFERRED
        mode = TensionSchedulingMode.DEFER_UNTIL_CONDITION
        earliest = sequence + 1
        threshold_edge_downgrade_applied = True
    elif context.allow_suppression and suppression_remaining > 0:
        status = TensionLifecycleStatus.DORMANT
        mode = TensionSchedulingMode.SUPPRESS_TEMPORARILY
        earliest = sequence + 1
        suppression_remaining = max(0, suppression_remaining - 1)
    else:
        status = TensionLifecycleStatus.DORMANT
        mode = TensionSchedulingMode.HOLD_IN_BACKGROUND
        earliest = None

    if (
        prior_entry is not None
        and prior_entry.current_status
        in {
            TensionLifecycleStatus.DORMANT,
            TensionLifecycleStatus.STALE,
            TensionLifecycleStatus.DEFERRED,
        }
        and mode == TensionSchedulingMode.REVISIT_NOW
    ):
        status = TensionLifecycleStatus.DEFERRED
        mode = TensionSchedulingMode.DEFER_UNTIL_CONDITION
        earliest = sequence + 1
        threshold_edge_downgrade_applied = True

    if candidate.tension_kind in {
        TensionKind.VIABILITY_PRESSURE,
        TensionKind.PENDING_RECOVERY,
        TensionKind.INTERRUPTION_CONTINUITY,
    } and mode == TensionSchedulingMode.SUPPRESS_TEMPORARILY:
        status = TensionLifecycleStatus.DEFERRED
        mode = TensionSchedulingMode.DEFER_UNTIL_CONDITION
        earliest = sequence + 1
        suppression_remaining = max(suppression_remaining, 0)
        kind_policy_applied = True

    if (
        candidate.tension_kind == TensionKind.FOCUS_DRIFT
        and mode == TensionSchedulingMode.REVISIT_NOW
    ):
        status = TensionLifecycleStatus.DEFERRED
        mode = TensionSchedulingMode.DEFER_UNTIL_CONDITION
        earliest = sequence + 1
        threshold_edge_downgrade_applied = True
        kind_policy_applied = True

    if scheduler_conflict:
        status = TensionLifecycleStatus.ACTIVE
        mode = TensionSchedulingMode.NO_SAFE_DEFER_CLAIM
        earliest = sequence

    return TensionScheduleEntry(
        tension_id=shared_tension_id,
        source_stream_id=stream_state.stream_id,
        source_stream_sequence_index=sequence,
        tension_kind=candidate.tension_kind,
        causal_anchor=candidate.causal_anchor,
        current_status=status,
        revisit_priority=candidate.priority_seed,
        scheduling_mode=mode,
        earliest_revisit_step=earliest,
        wake_conditions=candidate.wake_conditions,
        matched_wake_triggers=(),
        reactivation_cause=TensionWakeCause.NONE,
        wake_scope_matched=wake_scope_matched,
        suppression_budget=shared_suppression_budget,
        suppression_remaining=suppression_remaining,
        decay_state=TensionDecayState.NONE,
        stale=False,
        closure_criteria=candidate.closure_criteria,
        reopen_criteria=candidate.reopen_criteria,
        confidence=candidate.confidence,
        trigger_unknown=candidate.trigger_unknown,
        closure_uncertain=closure_uncertain,
        scheduler_conflict=scheduler_conflict,
        weak_wake_signal_ignored=weak_wake_signal_ignored,
        weak_closure_signal_ignored=weak_closure_signal_ignored,
        weak_reopen_signal_ignored=weak_reopen_signal_ignored,
        threshold_edge_downgrade_applied=threshold_edge_downgrade_applied,
        kind_policy_applied=kind_policy_applied,
        unschedulable=(mode == TensionSchedulingMode.UNSCHEDULABLE_TENSION),
        created_sequence_index=shared_created_index,
        last_touched_sequence_index=sequence,
        inactive_steps=0,
        reason=candidate.reason,
        provenance="c02.scheduling_decision",
    )


def _decay_unseen_entry(
    *,
    prior_entry: TensionScheduleEntry,
    stream_state: StreamKernelState,
    context: TensionSchedulerContext,
) -> TensionScheduleEntry:
    inactive = prior_entry.inactive_steps + context.step_delta
    if prior_entry.current_status == TensionLifecycleStatus.CLOSED:
        return replace(
            prior_entry,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=stream_state.sequence_index,
            current_status=TensionLifecycleStatus.CLOSED,
            scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
            last_touched_sequence_index=stream_state.sequence_index,
            inactive_steps=inactive,
            decay_state=TensionDecayState.NONE,
            reactivation_cause=TensionWakeCause.NONE,
            reason="closed tension remains monitored without reopen trigger",
            provenance="c02.closed_persist",
        )
    if inactive >= context.release_after_steps:
        return replace(
            prior_entry,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=stream_state.sequence_index,
            current_status=TensionLifecycleStatus.STALE,
            scheduling_mode=TensionSchedulingMode.RELEASE_AS_STALE,
            last_touched_sequence_index=stream_state.sequence_index,
            inactive_steps=inactive,
            decay_state=TensionDecayState.RELEASED,
            reactivation_cause=TensionWakeCause.NONE,
            stale=True,
            revisit_priority=0.0,
            reason="tension released as stale after prolonged inactivity",
            provenance="c02.release_as_stale",
        )
    if inactive >= context.stale_after_steps:
        return replace(
            prior_entry,
            source_stream_id=stream_state.stream_id,
            source_stream_sequence_index=stream_state.sequence_index,
            current_status=TensionLifecycleStatus.STALE,
            scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
            last_touched_sequence_index=stream_state.sequence_index,
            inactive_steps=inactive,
            decay_state=TensionDecayState.STALE,
            reactivation_cause=TensionWakeCause.NONE,
            stale=True,
            revisit_priority=min(prior_entry.revisit_priority, 0.3),
            reason="tension became stale but remains inspectable",
            provenance="c02.stale_decay",
        )
    return replace(
        prior_entry,
        source_stream_id=stream_state.stream_id,
        source_stream_sequence_index=stream_state.sequence_index,
        current_status=TensionLifecycleStatus.DORMANT,
        scheduling_mode=TensionSchedulingMode.HOLD_IN_BACKGROUND,
        last_touched_sequence_index=stream_state.sequence_index,
        inactive_steps=inactive,
        decay_state=TensionDecayState.DECAYING,
        reactivation_cause=TensionWakeCause.NONE,
        stale=False,
        revisit_priority=max(0.1, prior_entry.revisit_priority - 0.1),
        reason="unseen tension decays in background",
        provenance="c02.decay_unseen",
    )


def _ledger_event_for_entry(
    *,
    entry: TensionScheduleEntry,
    prior_entry: TensionScheduleEntry | None,
    stream_id: str,
) -> TensionLedgerEvent:
    event_kind = TensionLedgerEventKind.MONITORED
    reason_code = "monitored"
    if prior_entry is None:
        event_kind = TensionLedgerEventKind.REGISTERED
        reason_code = "registered_new_tension"
    elif (
        prior_entry.current_status != TensionLifecycleStatus.CLOSED
        and entry.current_status == TensionLifecycleStatus.CLOSED
    ):
        event_kind = TensionLedgerEventKind.CLOSED
        reason_code = "closure_evidence_met"
    elif (
        prior_entry.current_status == TensionLifecycleStatus.CLOSED
        and entry.current_status == TensionLifecycleStatus.REACTIVATED
    ):
        event_kind = TensionLedgerEventKind.REOPENED
        reason_code = "reopen_due_to_trigger"
    elif entry.current_status == TensionLifecycleStatus.REACTIVATED:
        event_kind = TensionLedgerEventKind.REACTIVATED
        reason_code = "wake_trigger_reactivation"
    elif entry.weak_wake_signal_ignored:
        event_kind = TensionLedgerEventKind.MONITORED
        reason_code = "weak_wake_signal_ignored"
    elif entry.weak_closure_signal_ignored:
        event_kind = TensionLedgerEventKind.MONITORED
        reason_code = "weak_closure_signal_ignored"
    elif entry.weak_reopen_signal_ignored:
        event_kind = TensionLedgerEventKind.MONITORED
        reason_code = "weak_reopen_signal_ignored"
    elif entry.scheduling_mode == TensionSchedulingMode.DEFER_UNTIL_CONDITION:
        event_kind = TensionLedgerEventKind.DEFERRED
        reason_code = "defer_until_condition"
    elif entry.scheduling_mode == TensionSchedulingMode.SUPPRESS_TEMPORARILY:
        event_kind = TensionLedgerEventKind.SUPPRESSED
        reason_code = "suppression_active"
    elif entry.decay_state == TensionDecayState.RELEASED:
        event_kind = TensionLedgerEventKind.RELEASED
        reason_code = "released_as_stale"
    elif entry.current_status == TensionLifecycleStatus.STALE:
        event_kind = TensionLedgerEventKind.STALE
        reason_code = "stale_decay"

    return _ledger_event(
        event_kind=event_kind,
        tension_id=entry.tension_id,
        stream_id=stream_id,
        reason=entry.reason,
        reason_code=reason_code,
    )


def _ledger_event(
    *,
    event_kind: TensionLedgerEventKind,
    tension_id: str,
    stream_id: str,
    reason: str,
    reason_code: str,
) -> TensionLedgerEvent:
    return TensionLedgerEvent(
        event_id=f"tension-ledger-{uuid4().hex[:10]}",
        event_kind=event_kind,
        tension_id=tension_id,
        stream_id=stream_id,
        reason=reason,
        reason_code=reason_code,
        provenance="c02.tension_scheduler_ledger",
    )
