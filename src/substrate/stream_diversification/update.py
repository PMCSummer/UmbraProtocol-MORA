from __future__ import annotations

from dataclasses import dataclass
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
from substrate.stream_diversification.models import (
    AlternativePathClass,
    DiversificationDecisionStatus,
    DiversificationLedgerEvent,
    DiversificationLedgerEventKind,
    DiversificationPathAssessment,
    DiversificationPathCount,
    ProgressEvidenceClass,
    DiversificationRedundancyScore,
    DiversificationTransitionClass,
    StagnationSignature,
    StreamDiversificationContext,
    StreamDiversificationResult,
    StreamDiversificationState,
)
from substrate.stream_diversification.policy import (
    evaluate_stream_diversification_downstream_gate,
)
from substrate.stream_diversification.telemetry import (
    build_stream_diversification_telemetry,
    stream_diversification_result_snapshot,
)
from substrate.stream_kernel.models import StreamKernelResult, StreamKernelState
from substrate.tension_scheduler.models import (
    TensionKind,
    TensionLifecycleStatus,
    TensionSchedulingMode,
    TensionSchedulerResult,
    TensionSchedulerState,
    TensionWakeCause,
)
from substrate.transition import execute_transition
from substrate.viability_control.models import (
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityEscalationStage,
)


ATTEMPTED_STREAM_DIVERSIFICATION_PATHS: tuple[str, ...] = (
    "stream_diversification.validate_typed_inputs",
    "stream_diversification.classify_transition_routes",
    "stream_diversification.estimate_progress_sensitive_redundancy",
    "stream_diversification.detect_structural_stagnation",
    "stream_diversification.repeat_justification_gating",
    "stream_diversification.safe_alternative_openings",
    "stream_diversification.protected_recurrence_boundary",
    "stream_diversification.pressure_decay_reset",
    "stream_diversification.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class _AssessmentBuild:
    assessment: DiversificationPathAssessment
    redundancy_score: DiversificationRedundancyScore
    path_count: DiversificationPathCount
    ledger_event: DiversificationLedgerEvent


def build_stream_diversification(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
    tension_scheduler_state_or_result: TensionSchedulerState | TensionSchedulerResult,
    regulation_state_or_result: RegulationState | RegulationResult,
    affordance_result: AffordanceResult,
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
    context: StreamDiversificationContext | None = None,
) -> StreamDiversificationResult:
    context = context or StreamDiversificationContext()
    if not isinstance(context, StreamDiversificationContext):
        raise TypeError("context must be StreamDiversificationContext")
    if context.step_delta < 1:
        raise ValueError("context.step_delta must be >= 1")
    if not isinstance(affordance_result, AffordanceResult):
        raise TypeError("build_stream_diversification requires typed AffordanceResult")

    stream_state = _extract_stream_input(stream_state_or_result)
    scheduler_state = _extract_scheduler_input(tension_scheduler_state_or_result)
    _, regulation_ref = _extract_regulation_input(regulation_state_or_result)
    _, preference_ref = _extract_preference_input(preference_state_or_result)
    viability_state, viability_ref = _extract_viability_input(viability_state_or_result)

    prior = context.prior_diversification_state
    if prior is not None and not isinstance(prior, StreamDiversificationState):
        raise TypeError(
            "context.prior_diversification_state must be StreamDiversificationState"
        )

    strong_survival_pressure = bool(
        viability_state.escalation_stage
        in {ViabilityEscalationStage.THREAT, ViabilityEscalationStage.CRITICAL}
        or viability_state.pressure_level >= 0.72
    )
    prior_assessment_map = (
        {
            (assessment.tension_id, assessment.causal_anchor): assessment
            for assessment in prior.path_assessments
        }
        if prior is not None
        else {}
    )
    prior_path_counts = (
        {count.path_key: count.count for count in prior.recent_path_counts}
        if prior is not None
        else {}
    )

    builds = [
        _build_assessment(
            entry=entry,
            prior_assessment=prior_assessment_map.get((entry.tension_id, entry.causal_anchor)),
            prior_count=prior_path_counts.get(_path_key_from_entry(entry), 0),
            strong_survival_pressure=strong_survival_pressure,
            context=context,
        )
        for entry in scheduler_state.tensions
    ]
    path_assessments = tuple(build.assessment for build in builds)
    redundancy_scores = tuple(build.redundancy_score for build in builds)
    path_counts = tuple(
        sorted((build.path_count for build in builds), key=lambda item: item.path_key)
    )
    ledger_events: list[DiversificationLedgerEvent] = [build.ledger_event for build in builds]

    stagnation_signatures = tuple(
        dict.fromkeys(
            signature
            for assessment in path_assessments
            for signature in assessment.stagnation_signatures
        )
    )
    repeat_requires_justification_for = tuple(
        assessment.path_id
        for assessment in path_assessments
        if assessment.repeat_requires_justification
    )
    protected_recurrence_classes = tuple(
        dict.fromkeys(
            assessment.transition_class
            for assessment in path_assessments
            if assessment.protected_recurrence
        )
    )
    allowed_alternative_classes = tuple(
        dict.fromkeys(
            candidate
            for assessment in path_assessments
            if not assessment.no_safe_diversification
            for candidate in assessment.alternative_classes
        )
    )
    actionable_alternative_classes = tuple(
        dict.fromkeys(
            candidate
            for assessment in path_assessments
            if not assessment.no_safe_diversification
            for candidate in assessment.actionable_alternative_classes
        )
    )
    no_safe_diversification = any(
        assessment.no_safe_diversification for assessment in path_assessments
    )
    has_protected_survival_route = any(
        assessment.transition_class
        == DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE
        and assessment.protected_recurrence
        for assessment in path_assessments
    )
    has_non_survival_actionable_candidates = any(
        assessment.transition_class
        != DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE
        and bool(assessment.actionable_alternative_classes)
        for assessment in path_assessments
    )
    diversification_conflict_with_survival = bool(
        strong_survival_pressure
        and has_protected_survival_route
        and has_non_survival_actionable_candidates
    )
    if diversification_conflict_with_survival:
        actionable_alternative_classes = ()

    confidence = _aggregate_confidence(path_assessments)
    low_confidence_stagnation = bool(stagnation_signatures and confidence < 0.55)
    diversification_pressure = _update_diversification_pressure(
        prior_pressure=(prior.diversification_pressure if prior is not None else 0.0),
        path_assessments=path_assessments,
        context=context,
    )
    if diversification_pressure < 0.55 - context.pressure_edge_band:
        actionable_alternative_classes = ()
    decision_status = _derive_decision_status(
        path_assessments=path_assessments,
        pressure=diversification_pressure,
        allowed_alternative_classes=allowed_alternative_classes,
        actionable_alternative_classes=actionable_alternative_classes,
        no_safe_diversification=no_safe_diversification,
        diversification_conflict_with_survival=diversification_conflict_with_survival,
        low_confidence_stagnation=low_confidence_stagnation,
        has_stagnation_signatures=bool(stagnation_signatures),
        pressure_edge_band=context.pressure_edge_band,
    )

    if prior is not None:
        pressure_delta = diversification_pressure - prior.diversification_pressure
        if pressure_delta > 0.05:
            ledger_events.append(
                _ledger_event(
                    event_kind=DiversificationLedgerEventKind.PRESSURE_RAISED,
                    path_id="pressure",
                    tension_id="*",
                    stream_id=stream_state.stream_id,
                    reason="diversification pressure increased after repeated low-progress routes",
                    reason_code="pressure_raised",
                )
            )
        elif pressure_delta < -0.05:
            ledger_events.append(
                _ledger_event(
                    event_kind=DiversificationLedgerEventKind.PRESSURE_DECAYED,
                    path_id="pressure",
                    tension_id="*",
                    stream_id=stream_state.stream_id,
                    reason="diversification pressure decayed after progress/route shift",
                    reason_code="pressure_decayed",
                )
            )
        if diversification_pressure == 0.0 and prior.diversification_pressure > 0.01:
            ledger_events.append(
                _ledger_event(
                    event_kind=DiversificationLedgerEventKind.PRESSURE_RESET,
                    path_id="pressure",
                    tension_id="*",
                    stream_id=stream_state.stream_id,
                    reason="pressure reset after closure/route shift removed stagnation claim",
                    reason_code="pressure_reset",
                )
            )

    state = StreamDiversificationState(
        diversification_id=f"stream-diversification-{stream_state.stream_id}",
        stream_id=stream_state.stream_id,
        source_stream_sequence_index=stream_state.sequence_index,
        source_scheduler_id=scheduler_state.scheduler_id,
        path_assessments=path_assessments,
        recent_path_counts=path_counts,
        stagnation_signatures=stagnation_signatures,
        redundancy_scores=redundancy_scores,
        diversification_pressure=diversification_pressure,
        allowed_alternative_classes=allowed_alternative_classes,
        actionable_alternative_classes=actionable_alternative_classes,
        repeat_requires_justification_for=repeat_requires_justification_for,
        protected_recurrence_classes=protected_recurrence_classes,
        decision_status=decision_status,
        no_safe_diversification=no_safe_diversification,
        diversification_conflict_with_survival=diversification_conflict_with_survival,
        low_confidence_stagnation=low_confidence_stagnation,
        confidence=confidence,
        source_c01_state_ref=f"{stream_state.stream_id}@{stream_state.sequence_index}",
        source_c02_state_ref=(
            f"{scheduler_state.scheduler_id}@{scheduler_state.source_stream_sequence_index}"
        ),
        source_regulation_ref=regulation_ref,
        source_affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
        source_preference_ref=preference_ref,
        source_viability_ref=viability_ref,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *context.source_lineage,
                    *stream_state.source_lineage,
                    *scheduler_state.source_lineage,
                )
            )
        ),
        last_update_provenance="c03.stream_diversification_from_c01_c02_r04",
    )
    gate = evaluate_stream_diversification_downstream_gate(state)
    telemetry = build_stream_diversification_telemetry(
        state=state,
        ledger_events=tuple(ledger_events),
        attempted_paths=ATTEMPTED_STREAM_DIVERSIFICATION_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "structural stagnation signatures from c02 lifecycle topology and c01 continuity state, with progress-sensitive repeat-justification gating"
        ),
    )
    abstain = bool(
        decision_status == DiversificationDecisionStatus.AMBIGUOUS_STAGNATION
        and diversification_pressure < 0.45
    )
    abstain_reason = "insufficient_basis_for_stagnation_claim" if abstain else None
    return StreamDiversificationResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_text_antirepeat_dependency=True,
        no_randomness_dependency=True,
        no_planner_arbitration_dependency=True,
    )


def stream_diversification_result_to_payload(
    result: StreamDiversificationResult,
) -> dict[str, object]:
    return stream_diversification_result_snapshot(result)


def persist_stream_diversification_result_via_f01(
    *,
    result: StreamDiversificationResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("c03-stream-diversification-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": (
                f"stream-diversification-step-{result.state.source_stream_sequence_index}"
            ),
            "stream_diversification_snapshot": stream_diversification_result_to_payload(
                result
            ),
        },
    )
    return execute_transition(request, runtime_state)


def _build_assessment(
    *,
    entry,
    prior_assessment: DiversificationPathAssessment | None,
    prior_count: int,
    strong_survival_pressure: bool,
    context: StreamDiversificationContext,
) -> _AssessmentBuild:
    transition_class = _classify_transition(entry)
    path_key = _path_key_from_entry(entry)
    repetition_count = prior_count + 1
    new_causal_input = bool(
        entry.reactivation_cause != TensionWakeCause.NONE
        or bool(entry.matched_wake_triggers)
    )
    progress_delta = _estimate_progress_delta(
        entry=entry,
        prior_assessment=prior_assessment,
        repetition_count=repetition_count,
        new_causal_input=new_causal_input,
    )
    progress_evidence_axes = _count_progress_evidence_axes(
        entry=entry,
        prior_assessment=prior_assessment,
        new_causal_input=new_causal_input,
    )
    progress_evidence_class, edge_band_applied = _derive_progress_evidence_class(
        progress_delta=progress_delta,
        progress_evidence_axes=progress_evidence_axes,
        context=context,
    )
    signatures = _collect_stagnation_signatures(
        entry=entry,
        transition_class=transition_class,
        repetition_count=repetition_count,
        progress_delta=progress_delta,
        new_causal_input=new_causal_input,
        strong_survival_pressure=strong_survival_pressure,
        disabled=context.disable_structural_stagnation_detection,
        low_progress_threshold=context.low_progress_threshold,
        progress_evidence_class=progress_evidence_class,
    )
    protected_recurrence = _is_protected_recurrence(
        transition_class=transition_class,
        progress_delta=progress_delta,
        new_causal_input=new_causal_input,
        strong_survival_pressure=strong_survival_pressure,
        strong_progress_threshold=context.strong_progress_threshold,
        progress_evidence_class=progress_evidence_class,
    )
    repeat_requires_justification = bool(
        not context.disable_repeat_justification_gating
        and repetition_count >= 2
        and entry.current_status != TensionLifecycleStatus.CLOSED
        and not protected_recurrence
        and (
            progress_evidence_class == ProgressEvidenceClass.WEAK
            or repetition_count >= 3
        )
    )
    redundancy_score = _estimate_redundancy_score(
        entry=entry,
        repetition_count=repetition_count,
        progress_delta=progress_delta,
        protected_recurrence=protected_recurrence,
        new_causal_input=new_causal_input,
        disabled=context.disable_structural_stagnation_detection,
        progress_evidence_class=progress_evidence_class,
    )
    alternative_classes = _derive_alternative_classes(
        entry=entry,
        transition_class=transition_class,
        redundancy_score=redundancy_score,
        repeat_requires_justification=repeat_requires_justification,
        protected_recurrence=protected_recurrence,
        strong_survival_pressure=strong_survival_pressure,
    )
    (
        alternative_classes,
        survival_filtered_alternatives,
    ) = _apply_survival_candidate_filter(
        transition_class=transition_class,
        alternative_classes=alternative_classes,
        strong_survival_pressure=strong_survival_pressure,
        protected_recurrence=protected_recurrence,
    )
    actionable_alternative_classes = _derive_actionable_alternatives(
        alternatives=alternative_classes,
        redundancy_score=redundancy_score,
        repeat_requires_justification=repeat_requires_justification,
        progress_evidence_class=progress_evidence_class,
    )
    no_safe_diversification = bool(
        repeat_requires_justification and len(actionable_alternative_classes) == 0
    )
    confidence = round(
        max(
            0.15,
            min(
                1.0,
                entry.confidence
                - (0.12 if no_safe_diversification else 0.0)
                - (0.1 if signatures else 0.0)
                - (0.08 if edge_band_applied else 0.0)
                + (0.1 if protected_recurrence else 0.0),
            ),
        ),
        4,
    )
    path_id = f"{entry.tension_id}:{transition_class.value}"
    reason = (
        "route repeats without enough progress and now requires diversification basis"
        if repeat_requires_justification
        else (
            "recurrence remains protected by survival/progress/new causal input"
            if protected_recurrence
            else "route remains bounded without strong stagnation claim"
        )
    )
    assessment = DiversificationPathAssessment(
        assessment_id=f"c03-assessment-{uuid4().hex[:10]}",
        path_id=path_id,
        tension_id=entry.tension_id,
        causal_anchor=entry.causal_anchor,
        transition_class=transition_class,
        current_status=entry.current_status.value,
        current_mode=entry.scheduling_mode.value,
        revisit_priority=entry.revisit_priority,
        repetition_count=repetition_count,
        progress_delta=progress_delta,
        progress_evidence_axes=progress_evidence_axes,
        progress_evidence_class=progress_evidence_class,
        new_causal_input=new_causal_input,
        edge_band_applied=edge_band_applied,
        stagnation_signatures=signatures,
        redundancy_score=redundancy_score,
        repeat_requires_justification=repeat_requires_justification,
        protected_recurrence=protected_recurrence,
        alternative_classes=alternative_classes,
        actionable_alternative_classes=actionable_alternative_classes,
        survival_filtered_alternatives=survival_filtered_alternatives,
        no_safe_diversification=no_safe_diversification,
        confidence=confidence,
        reason=reason,
        provenance="c03.path_assessment",
    )
    redundancy = DiversificationRedundancyScore(
        path_id=path_id,
        transition_class=transition_class,
        repetition_count=repetition_count,
        progress_delta=progress_delta,
        redundancy_score=redundancy_score,
        repeat_requires_justification=repeat_requires_justification,
        protected_recurrence=protected_recurrence,
    )
    path_count = DiversificationPathCount(path_key=path_key, count=repetition_count)
    ledger_event = _assessment_ledger_event(
        assessment=assessment,
        stream_id=entry.source_stream_id,
    )
    return _AssessmentBuild(
        assessment=assessment,
        redundancy_score=redundancy,
        path_count=path_count,
        ledger_event=ledger_event,
    )


def _assessment_ledger_event(
    *,
    assessment: DiversificationPathAssessment,
    stream_id: str,
) -> DiversificationLedgerEvent:
    event_kind = DiversificationLedgerEventKind.ASSESSED
    reason_code = "assessed"
    if assessment.no_safe_diversification:
        event_kind = DiversificationLedgerEventKind.NO_SAFE_DIVERSIFICATION
        reason_code = "no_safe_diversification"
    elif assessment.alternative_classes:
        event_kind = DiversificationLedgerEventKind.ALTERNATIVE_OPENED
        reason_code = "alternative_opened"
    elif assessment.repeat_requires_justification:
        event_kind = DiversificationLedgerEventKind.REPEAT_GATED
        reason_code = "repeat_gated"
    elif assessment.stagnation_signatures:
        event_kind = DiversificationLedgerEventKind.STAGNATION_SIGNATURE
        reason_code = "stagnation_signature"
    elif assessment.protected_recurrence:
        event_kind = DiversificationLedgerEventKind.PROTECTED_RECURRENCE
        reason_code = "protected_recurrence"
    return _ledger_event(
        event_kind=event_kind,
        path_id=assessment.path_id,
        tension_id=assessment.tension_id,
        stream_id=stream_id,
        reason=assessment.reason,
        reason_code=reason_code,
    )


def _path_key_from_entry(entry) -> str:
    transition_class = _classify_transition(entry)
    return f"{transition_class.value}:{entry.causal_anchor}"


def _classify_transition(entry) -> DiversificationTransitionClass:
    if entry.tension_kind == TensionKind.VIABILITY_PRESSURE:
        return DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE
    if entry.tension_kind in {
        TensionKind.PENDING_RECOVERY,
        TensionKind.INTERRUPTION_CONTINUITY,
    }:
        return DiversificationTransitionClass.RECOVERY_REVISIT_ROUTE
    if entry.tension_kind == TensionKind.FOCUS_DRIFT:
        return DiversificationTransitionClass.FOCUS_RECURRENCE_ROUTE
    if entry.current_status in {
        TensionLifecycleStatus.DORMANT,
        TensionLifecycleStatus.STALE,
    }:
        return DiversificationTransitionClass.BACKGROUND_MONITOR_ROUTE
    return DiversificationTransitionClass.ACTIVE_REVISIT_ROUTE


def _estimate_progress_delta(
    *,
    entry,
    prior_assessment: DiversificationPathAssessment | None,
    repetition_count: int,
    new_causal_input: bool,
) -> float:
    if entry.current_status == TensionLifecycleStatus.CLOSED:
        return 0.95

    progress = 0.0
    if prior_assessment is None:
        progress += 0.3
    else:
        if entry.current_status.value != prior_assessment.current_status:
            if entry.current_status == TensionLifecycleStatus.CLOSED:
                progress += 0.45
            elif entry.current_status in {
                TensionLifecycleStatus.DEFERRED,
                TensionLifecycleStatus.DORMANT,
                TensionLifecycleStatus.STALE,
            } and prior_assessment.current_status in {"active", "reactivated"}:
                progress += 0.18
            else:
                progress += 0.05
        if entry.scheduling_mode.value != prior_assessment.current_mode:
            if entry.scheduling_mode in {
                TensionSchedulingMode.DEFER_UNTIL_CONDITION,
                TensionSchedulingMode.MONITOR_PASSIVELY,
                TensionSchedulingMode.HOLD_IN_BACKGROUND,
                TensionSchedulingMode.RELEASE_AS_STALE,
            } and prior_assessment.current_mode in {
                TensionSchedulingMode.REVISIT_NOW.value,
                TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER.value,
            }:
                progress += 0.12
            else:
                progress += 0.04
        priority_delta = prior_assessment.revisit_priority - entry.revisit_priority
        if priority_delta >= 0.12:
            progress += 0.18
        elif priority_delta <= -0.12:
            progress += 0.05
    if new_causal_input:
        progress += 0.25
    if repetition_count >= 2 and not new_causal_input:
        progress -= 0.1
    if entry.current_status in {TensionLifecycleStatus.DORMANT, TensionLifecycleStatus.STALE}:
        progress -= 0.08
    return round(max(0.0, min(1.0, progress)), 4)


def _count_progress_evidence_axes(
    *,
    entry,
    prior_assessment: DiversificationPathAssessment | None,
    new_causal_input: bool,
) -> int:
    axes = 0
    if new_causal_input:
        axes += 1
    if prior_assessment is None:
        return axes + 1
    if entry.current_status.value != prior_assessment.current_status:
        axes += 1
    if entry.scheduling_mode.value != prior_assessment.current_mode:
        axes += 1
    if abs(prior_assessment.revisit_priority - entry.revisit_priority) >= 0.12:
        axes += 1
    return axes


def _derive_progress_evidence_class(
    *,
    progress_delta: float,
    progress_evidence_axes: int,
    context: StreamDiversificationContext,
) -> tuple[ProgressEvidenceClass, bool]:
    low_edge = context.low_progress_threshold + context.progress_edge_band
    strong_low = max(
        context.low_progress_threshold,
        context.strong_progress_threshold - context.progress_edge_band,
    )
    edge_band_applied = bool(
        (context.low_progress_threshold <= progress_delta < low_edge)
        or (strong_low <= progress_delta <= context.strong_progress_threshold)
    )
    if (
        progress_delta >= context.strong_progress_threshold
        and progress_evidence_axes >= context.minimum_progress_axes_for_meaningful
    ):
        return ProgressEvidenceClass.STRONG, edge_band_applied
    if (
        progress_delta >= low_edge
        and progress_evidence_axes >= context.minimum_progress_axes_for_meaningful
    ):
        return ProgressEvidenceClass.MODERATE, edge_band_applied
    return ProgressEvidenceClass.WEAK, edge_band_applied


def _collect_stagnation_signatures(
    *,
    entry,
    transition_class: DiversificationTransitionClass,
    repetition_count: int,
    progress_delta: float,
    new_causal_input: bool,
    strong_survival_pressure: bool,
    disabled: bool,
    low_progress_threshold: float,
    progress_evidence_class: ProgressEvidenceClass,
) -> tuple[StagnationSignature, ...]:
    if disabled:
        return ()
    signatures: list[StagnationSignature] = []
    if (
        repetition_count >= 2
        and progress_delta <= low_progress_threshold
        and entry.current_status != TensionLifecycleStatus.CLOSED
        and progress_evidence_class == ProgressEvidenceClass.WEAK
    ):
        signatures.append(StagnationSignature.REPEATED_ROUTE_LOW_PROGRESS)
    if (
        repetition_count >= 3
        and transition_class
        in {
            DiversificationTransitionClass.ACTIVE_REVISIT_ROUTE,
            DiversificationTransitionClass.RECOVERY_REVISIT_ROUTE,
            DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE,
        }
        and progress_delta <= max(0.05, low_progress_threshold + 0.02)
        and progress_evidence_class != ProgressEvidenceClass.STRONG
    ):
        signatures.append(StagnationSignature.LOOPING_REVISIT_WITHOUT_DELTA)
    if (
        entry.current_status == TensionLifecycleStatus.REACTIVATED
        and not new_causal_input
    ):
        signatures.append(StagnationSignature.REPEATED_REOPEN_WITHOUT_NEW_INPUT)
    if (
        transition_class == DiversificationTransitionClass.BACKGROUND_MONITOR_ROUTE
        and repetition_count >= 2
        and progress_delta <= low_progress_threshold
        and progress_evidence_class == ProgressEvidenceClass.WEAK
    ):
        signatures.append(StagnationSignature.STAGNANT_BACKGROUND_CYCLE)
    if (
        repetition_count >= 2
        and progress_delta <= low_progress_threshold
        and not strong_survival_pressure
        and progress_evidence_class == ProgressEvidenceClass.WEAK
    ):
        signatures.append(
            StagnationSignature.DOMINANT_ROUTE_WHILE_ALTERNATIVES_AVAILABLE
        )
    return tuple(dict.fromkeys(signatures))


def _is_protected_recurrence(
    *,
    transition_class: DiversificationTransitionClass,
    progress_delta: float,
    new_causal_input: bool,
    strong_survival_pressure: bool,
    strong_progress_threshold: float,
    progress_evidence_class: ProgressEvidenceClass,
) -> bool:
    if (
        transition_class == DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE
        and strong_survival_pressure
    ):
        return True
    if new_causal_input:
        return True
    return (
        progress_delta >= strong_progress_threshold
        and progress_evidence_class == ProgressEvidenceClass.STRONG
    )


def _estimate_redundancy_score(
    *,
    entry,
    repetition_count: int,
    progress_delta: float,
    protected_recurrence: bool,
    new_causal_input: bool,
    disabled: bool,
    progress_evidence_class: ProgressEvidenceClass,
) -> float:
    if disabled:
        return 0.0
    score = ((max(0, repetition_count - 1) * 0.22) + ((1.0 - progress_delta) * 0.55))
    if entry.current_status in {TensionLifecycleStatus.DORMANT, TensionLifecycleStatus.STALE}:
        score += 0.1
    if new_causal_input:
        score -= 0.18
    if protected_recurrence:
        score *= 0.45
    elif progress_evidence_class == ProgressEvidenceClass.MODERATE:
        score *= 0.72
    return round(max(0.0, min(1.0, score)), 4)


def _derive_alternative_classes(
    *,
    entry,
    transition_class: DiversificationTransitionClass,
    redundancy_score: float,
    repeat_requires_justification: bool,
    protected_recurrence: bool,
    strong_survival_pressure: bool,
) -> tuple[AlternativePathClass, ...]:
    if (
        not repeat_requires_justification
        or redundancy_score < 0.6
        or (
            protected_recurrence
            and transition_class == DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE
            and strong_survival_pressure
        )
    ):
        return ()

    alternatives: list[AlternativePathClass] = [
        AlternativePathClass.REQUEST_NEW_INPUT_CANDIDATE
    ]
    if transition_class in {
        DiversificationTransitionClass.ACTIVE_REVISIT_ROUTE,
        DiversificationTransitionClass.RECOVERY_REVISIT_ROUTE,
    }:
        alternatives.extend(
            (
                AlternativePathClass.RAISE_BRANCH_CANDIDATE,
                AlternativePathClass.REFRAME_TENSION_ACCESS,
            )
        )
    if transition_class == DiversificationTransitionClass.FOCUS_RECURRENCE_ROUTE:
        alternatives.extend(
            (
                AlternativePathClass.SWITCH_PROCESSING_MODE_CANDIDATE,
                AlternativePathClass.SAFE_PAUSE_CANDIDATE,
            )
        )
    if entry.current_status in {TensionLifecycleStatus.DORMANT, TensionLifecycleStatus.STALE}:
        alternatives.append(AlternativePathClass.REVIVE_DORMANT_BRANCH_CANDIDATE)
    if (
        entry.tension_kind == TensionKind.VIABILITY_PRESSURE
        and not strong_survival_pressure
    ):
        alternatives.append(
            AlternativePathClass.SHIFT_REGULATION_OPTION_CLASS_CANDIDATE
        )
    return tuple(dict.fromkeys(alternatives))


def _apply_survival_candidate_filter(
    *,
    transition_class: DiversificationTransitionClass,
    alternative_classes: tuple[AlternativePathClass, ...],
    strong_survival_pressure: bool,
    protected_recurrence: bool,
) -> tuple[tuple[AlternativePathClass, ...], bool]:
    if not alternative_classes:
        return alternative_classes, False
    if not (
        strong_survival_pressure
        and protected_recurrence
        and transition_class == DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE
    ):
        return alternative_classes, False
    safe_classes = {
        AlternativePathClass.REQUEST_NEW_INPUT_CANDIDATE,
        AlternativePathClass.SAFE_PAUSE_CANDIDATE,
    }
    filtered = tuple(path_class for path_class in alternative_classes if path_class in safe_classes)
    return filtered, len(filtered) != len(alternative_classes)


def _derive_actionable_alternatives(
    *,
    alternatives: tuple[AlternativePathClass, ...],
    redundancy_score: float,
    repeat_requires_justification: bool,
    progress_evidence_class: ProgressEvidenceClass,
) -> tuple[AlternativePathClass, ...]:
    if not alternatives:
        return ()
    if not repeat_requires_justification:
        return ()
    if progress_evidence_class == ProgressEvidenceClass.WEAK and redundancy_score < 0.72:
        return (AlternativePathClass.REQUEST_NEW_INPUT_CANDIDATE,)
    if redundancy_score < 0.62:
        return ()
    return alternatives


def _aggregate_confidence(
    path_assessments: tuple[DiversificationPathAssessment, ...],
) -> float:
    if not path_assessments:
        return 0.0
    return round(
        sum(assessment.confidence for assessment in path_assessments)
        / len(path_assessments),
        4,
    )


def _update_diversification_pressure(
    *,
    prior_pressure: float,
    path_assessments: tuple[DiversificationPathAssessment, ...],
    context: StreamDiversificationContext,
) -> float:
    if not path_assessments:
        return 0.0

    pressure = prior_pressure
    has_stagnation = any(assessment.stagnation_signatures for assessment in path_assessments)
    avg_redundancy = sum(assessment.redundancy_score for assessment in path_assessments) / len(
        path_assessments
    )
    has_strong_progress = any(
        assessment.progress_delta >= context.strong_progress_threshold
        for assessment in path_assessments
    )
    has_closed = any(
        assessment.current_status == TensionLifecycleStatus.CLOSED.value
        for assessment in path_assessments
    )
    has_path_shift = any(
        assessment.progress_delta >= 0.45 and not assessment.stagnation_signatures
        for assessment in path_assessments
    )
    has_edge_band = any(
        assessment.edge_band_applied for assessment in path_assessments
    )

    if has_stagnation:
        pressure += context.stagnation_pressure_gain + (avg_redundancy * 0.15)
        if has_edge_band:
            pressure -= min(0.05, context.stagnation_pressure_gain * 0.4)
    if has_strong_progress or has_closed or has_path_shift:
        pressure -= context.pressure_decay_on_shift
        if has_edge_band:
            pressure -= min(0.04, context.pressure_decay_on_shift * 0.25)
    if all(
        assessment.current_status in {TensionLifecycleStatus.CLOSED.value, TensionLifecycleStatus.STALE.value}
        for assessment in path_assessments
    ):
        pressure -= context.pressure_decay_on_shift * 0.8
    if all(
        assessment.protected_recurrence and not assessment.stagnation_signatures
        for assessment in path_assessments
    ):
        pressure -= context.pressure_decay_on_shift * 0.5

    return round(max(0.0, min(1.0, pressure)), 4)


def _derive_decision_status(
    *,
    path_assessments: tuple[DiversificationPathAssessment, ...],
    pressure: float,
    allowed_alternative_classes: tuple[AlternativePathClass, ...],
    actionable_alternative_classes: tuple[AlternativePathClass, ...],
    no_safe_diversification: bool,
    diversification_conflict_with_survival: bool,
    low_confidence_stagnation: bool,
    has_stagnation_signatures: bool,
    pressure_edge_band: float,
) -> DiversificationDecisionStatus:
    if not path_assessments:
        return DiversificationDecisionStatus.AMBIGUOUS_STAGNATION
    if no_safe_diversification:
        return DiversificationDecisionStatus.NO_SAFE_DIVERSIFICATION
    if diversification_conflict_with_survival:
        return DiversificationDecisionStatus.AMBIGUOUS_STAGNATION
    pressure_open_threshold = 0.55
    if (
        pressure >= pressure_open_threshold + pressure_edge_band
        and has_stagnation_signatures
        and bool(actionable_alternative_classes)
    ):
        return DiversificationDecisionStatus.ALTERNATIVE_PATH_OPENING
    if (
        pressure >= pressure_open_threshold - pressure_edge_band
        and has_stagnation_signatures
        and bool(allowed_alternative_classes)
    ):
        return DiversificationDecisionStatus.AMBIGUOUS_STAGNATION
    if has_stagnation_signatures and not low_confidence_stagnation:
        return DiversificationDecisionStatus.STAGNATION_DETECTED
    if low_confidence_stagnation:
        return DiversificationDecisionStatus.AMBIGUOUS_STAGNATION
    return DiversificationDecisionStatus.JUSTIFIED_RECURRENCE


def _ledger_event(
    *,
    event_kind: DiversificationLedgerEventKind,
    path_id: str,
    tension_id: str,
    stream_id: str,
    reason: str,
    reason_code: str,
) -> DiversificationLedgerEvent:
    return DiversificationLedgerEvent(
        event_id=f"c03-ledger-{uuid4().hex[:10]}",
        event_kind=event_kind,
        path_id=path_id,
        tension_id=tension_id,
        stream_id=stream_id,
        reason=reason,
        reason_code=reason_code,
        provenance="c03.stream_diversification_ledger",
    )


def _extract_stream_input(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
) -> StreamKernelState:
    if isinstance(stream_state_or_result, StreamKernelResult):
        return stream_state_or_result.state
    if isinstance(stream_state_or_result, StreamKernelState):
        return stream_state_or_result
    raise TypeError(
        "build_stream_diversification requires StreamKernelState or StreamKernelResult"
    )


def _extract_scheduler_input(
    tension_scheduler_state_or_result: TensionSchedulerState | TensionSchedulerResult,
) -> TensionSchedulerState:
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerResult):
        return tension_scheduler_state_or_result.state
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerState):
        return tension_scheduler_state_or_result
    raise TypeError(
        "build_stream_diversification requires TensionSchedulerState or TensionSchedulerResult"
    )


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
    raise TypeError(
        "build_stream_diversification requires RegulationState or RegulationResult"
    )


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
    raise TypeError(
        "build_stream_diversification requires PreferenceState or PreferenceUpdateResult"
    )


def _extract_viability_input(
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
) -> tuple[ViabilityControlState, str]:
    if isinstance(viability_state_or_result, ViabilityControlResult):
        state = viability_state_or_result.state
        return (
            state,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    if isinstance(viability_state_or_result, ViabilityControlState):
        state = viability_state_or_result
        return (
            state,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    raise TypeError(
        "build_stream_diversification requires ViabilityControlState or ViabilityControlResult"
    )
