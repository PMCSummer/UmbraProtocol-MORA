from __future__ import annotations

from substrate.c06_surfacing_candidates import C06SurfacingResult
from substrate.v01_normative_permission_commitment_licensing import V01LicenseResult
from substrate.v02_communicative_intent_utterance_plan_bridge import V02UtterancePlanResult
from substrate.v03_surface_verbalization_causality_constrained_realization import (
    V03ConstrainedRealizationResult,
)
from substrate.p02_intervention_episode_layer_licensed_action_trace.models import (
    P02CompletionAndVerificationState,
    P02EpisodeBoundaryReport,
    P02EpisodeGateDecision,
    P02EpisodeMetadata,
    P02EpisodeStatus,
    P02ExecutionEvent,
    P02ExecutionStatus,
    P02InterventionEpisodeInput,
    P02InterventionEpisodeRecord,
    P02InterventionEpisodeResult,
    P02LicensedActionSnapshot,
    P02OutcomeEvidence,
    P02OutcomeVerificationStatus,
    P02ResidueItem,
    P02ResidueKind,
    P02ScopeMarker,
    P02Telemetry,
)


def build_p02_intervention_episode_layer_licensed_action_trace(
    *,
    tick_id: str,
    tick_index: int,
    c06_result: C06SurfacingResult,
    v03_result: V03ConstrainedRealizationResult,
    v02_result: V02UtterancePlanResult,
    v01_result: V01LicenseResult,
    episode_input: P02InterventionEpisodeInput | None,
    source_lineage: tuple[str, ...],
    episode_enabled: bool = True,
) -> P02InterventionEpisodeResult:
    if not episode_enabled:
        return _build_minimal_result(
            reason="p02 intervention episode construction disabled in ablation context",
            source_lineage=source_lineage,
            restrictions=("p02_disabled", "candidate_episode_only"),
        )
    if not isinstance(c06_result, C06SurfacingResult):
        raise TypeError("p02 requires C06SurfacingResult")
    if not isinstance(v03_result, V03ConstrainedRealizationResult):
        raise TypeError("p02 requires V03ConstrainedRealizationResult")
    if not isinstance(v02_result, V02UtterancePlanResult):
        raise TypeError("p02 requires V02UtterancePlanResult")
    if not isinstance(v01_result, V01LicenseResult):
        raise TypeError("p02 requires V01LicenseResult")

    explicit_input = episode_input if isinstance(episode_input, P02InterventionEpisodeInput) else None
    if explicit_input is None:
        return _build_minimal_result(
            reason=(
                "p02 frontier slice requires explicit intervention episode input; "
                "auto-construction from generic surfacing state is intentionally deferred"
            ),
            source_lineage=source_lineage,
            restrictions=("candidate_episode_only", "insufficient_episode_basis"),
        )

    licensed_actions = (
        explicit_input.licensed_actions
        if explicit_input is not None and explicit_input.licensed_actions
        else _derive_licensed_actions(v01_result=v01_result)
    )
    execution_events = (
        explicit_input.execution_events
        if explicit_input is not None and explicit_input.execution_events
        else _derive_execution_events(v03_result=v03_result, licensed_actions=licensed_actions)
    )
    outcome_evidence = (
        explicit_input.outcome_evidence
        if explicit_input is not None and explicit_input.outcome_evidence
        else ()
    )
    side_effect_refs = (
        explicit_input.side_effect_refs
        if explicit_input is not None and explicit_input.side_effect_refs
        else ()
    )

    if not execution_events and not outcome_evidence and not licensed_actions:
        return _build_minimal_result(
            reason="p02 could not determine execution boundary/license basis from available inputs",
            source_lineage=source_lineage,
            restrictions=(
                "boundary_ambiguous",
                "license_link_missing",
                "cannot_determine_episode_closure",
            ),
        )

    boundary = _construct_boundary(execution_events=execution_events)
    completion = _build_completion_state(
        included_events=boundary.included_event_refs,
        execution_events=execution_events,
        outcome_evidence=outcome_evidence,
        licensed_actions=licensed_actions,
    )
    side_effects = tuple(dict.fromkeys(side_effect_refs))

    residue = _build_residue(
        tick_id=tick_id,
        completion=completion,
        side_effects=side_effects,
        commitment_carryover_count=c06_result.candidate_set.metadata.commitment_carryover_count,
    )

    project_refs = tuple(
        dict.fromkeys(
            (
                *(
                    explicit_input.project_refs
                    if explicit_input is not None
                    else ()
                ),
                *tuple(
                    item.project_ref
                    for item in execution_events
                    if isinstance(item.project_ref, str) and item.project_ref.strip()
                ),
            )
        )
    )
    license_refs = tuple(
        dict.fromkeys(
            (
                *(item.source_license_ref for item in licensed_actions),
                *tuple(
                    item.source_license_ref
                    for item in execution_events
                    if isinstance(item.source_license_ref, str)
                    and item.source_license_ref.strip()
                ),
            )
        )
    )

    included_set = set(boundary.included_event_refs)
    included_trace_refs = tuple(
        item.event_id for item in execution_events if item.event_id in included_set
    )
    license_link_missing = _license_link_missing(
        included_events=included_trace_refs,
        execution_events=execution_events,
        licensed_actions=licensed_actions,
    )
    overrun_detected = _overrun_detected(
        included_events=included_trace_refs,
        execution_events=execution_events,
        licensed_actions=licensed_actions,
    )
    possible_overrun = bool(overrun_detected or license_link_missing)

    status = _resolve_episode_status(
        completion=completion,
        overrun_detected=overrun_detected,
        license_link_missing=license_link_missing,
    )
    uncertainty_markers = _uncertainty_markers(
        boundary=boundary,
        completion=completion,
        license_link_missing=license_link_missing,
        possible_overrun=possible_overrun,
    )

    record = P02InterventionEpisodeRecord(
        episode_id=f"p02:{tick_id}:episode:1",
        source_license_refs=license_refs,
        project_refs=project_refs,
        action_trace_refs=included_trace_refs,
        excluded_event_refs=boundary.excluded_event_refs,
        boundary_window_start=boundary.boundary_window_start,
        boundary_window_end=boundary.boundary_window_end,
        boundary_report=boundary,
        status=status,
        completion_and_verification=completion,
        execution_status=completion.execution_status,
        outcome_verification_status=completion.outcome_verification_status,
        license_link_missing=license_link_missing,
        overrun_detected=overrun_detected,
        possible_overrun=possible_overrun,
        side_effects=side_effects,
        residue=residue,
        uncertainty_markers=uncertainty_markers,
        rationale_codes=(
            "licensed_action_trace_built",
            "execution_vs_verification_separated",
            "residue_preserved",
        ),
        provenance="p02.intervention_episode.policy",
    )
    episodes = (record,)
    metadata = P02EpisodeMetadata(
        episode_count=1,
        completed_as_licensed_count=int(status is P02EpisodeStatus.COMPLETED_AS_LICENSED),
        partial_episode_count=int(status is P02EpisodeStatus.PARTIAL),
        blocked_episode_count=int(status is P02EpisodeStatus.BLOCKED),
        awaiting_verification_count=int(status is P02EpisodeStatus.AWAITING_VERIFICATION),
        completion_verified_count=int(completion.completion_verified),
        overrun_detected_count=int(overrun_detected),
        boundary_ambiguous_count=int(boundary.boundary_ambiguous),
        license_link_missing_count=int(license_link_missing),
        residue_count=len(residue),
        side_effect_count=len(side_effects),
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *c06_result.candidate_set.metadata.source_lineage,
                    *v01_result.state.source_lineage,
                    v02_result.state.provenance,
                    v03_result.artifact.provenance,
                )
            )
        ),
    )
    gate = _build_gate(metadata=metadata, record=record)
    telemetry = P02Telemetry(
        episode_count=metadata.episode_count,
        completed_as_licensed_count=metadata.completed_as_licensed_count,
        partial_episode_count=metadata.partial_episode_count,
        blocked_episode_count=metadata.blocked_episode_count,
        awaiting_verification_count=metadata.awaiting_verification_count,
        overrun_detected_count=metadata.overrun_detected_count,
        boundary_ambiguous_count=metadata.boundary_ambiguous_count,
        residue_count=metadata.residue_count,
        side_effect_count=metadata.side_effect_count,
        downstream_consumer_ready=(
            gate.episode_consumer_ready
            and gate.boundary_consumer_ready
            and gate.verification_consumer_ready
        ),
    )
    scope = P02ScopeMarker(
        scope="rt01_hosted_p02_first_slice",
        rt01_hosted_only=True,
        p02_first_slice_only=True,
        no_project_formation_authority=True,
        no_action_licensing_authority=True,
        no_external_success_claim_without_evidence=True,
        no_memory_retention_authority=True,
        no_map_wide_rollout_claim=True,
        reason="p02 builds typed intervention episodes without licensing/formation/retention authority",
    )
    return P02InterventionEpisodeResult(
        episodes=episodes,
        metadata=metadata,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=(
            "p02 constructed typed intervention episode with boundary/license/verification split "
            "and explicit residue handoff"
        ),
    )


def _derive_licensed_actions(*, v01_result: V01LicenseResult) -> tuple[P02LicensedActionSnapshot, ...]:
    snapshots: list[P02LicensedActionSnapshot] = []
    for entry in v01_result.state.licensed_acts:
        snapshots.append(
            P02LicensedActionSnapshot(
                action_id=entry.act_id,
                source_license_ref=f"v01:licensed:{entry.act_id}",
                license_scope_ref=entry.act_type.value,
                project_ref=None,
                allowed=True,
                provenance="p02.derived_from_v01",
            )
        )
    return tuple(snapshots)


def _derive_execution_events(
    *,
    v03_result: V03ConstrainedRealizationResult,
    licensed_actions: tuple[P02LicensedActionSnapshot, ...],
) -> tuple[P02ExecutionEvent, ...]:
    if not v03_result.artifact.surface_text.strip():
        return ()
    license_refs = {item.action_id: item.source_license_ref for item in licensed_actions}
    events: list[P02ExecutionEvent] = []
    order = 1
    for item in v03_result.alignment_map.alignments:
        if not item.realized:
            continue
        action_ref = str(item.source_act_ref or "").strip()
        if not action_ref:
            action_ref = f"segment:{item.segment_id}"
        events.append(
            P02ExecutionEvent(
                event_id=f"v03:{item.segment_id}:{order}",
                action_ref=action_ref,
                event_kind="executed",
                order_index=order,
                source_license_ref=license_refs.get(action_ref),
                continuation_hint=True,
                new_episode_hint=False,
                provenance="p02.derived_from_v03_alignment",
            )
        )
        order += 1
    return tuple(events)


def _construct_boundary(
    *,
    execution_events: tuple[P02ExecutionEvent, ...],
) -> P02EpisodeBoundaryReport:
    if not execution_events:
        return P02EpisodeBoundaryReport(
            boundary_window_start=None,
            boundary_window_end=None,
            action_trace_refs=(),
            included_event_refs=(),
            excluded_event_refs=(),
            boundary_ambiguous=True,
            reason_codes=("no_execution_events", "cannot_determine_episode_closure"),
            reason="p02 could not construct episode boundary from empty execution trace",
        )
    events = sorted(execution_events, key=lambda item: item.order_index)
    anchor = events[0]
    included = [anchor.event_id]
    excluded: list[str] = []
    reason_codes: list[str] = []
    boundary_ambiguous = False
    for item in events[1:]:
        same_action = item.action_ref == anchor.action_ref
        same_project = (
            (anchor.project_ref or "").strip() == (item.project_ref or "").strip()
        )
        same_license = (
            (anchor.source_license_ref or "").strip()
            == (item.source_license_ref or "").strip()
        )
        continuation_kind = item.event_kind in {"pause", "clarification", "retry", "resume"}
        if item.new_episode_hint:
            excluded.append(item.event_id)
            reason_codes.append("new_episode_hint")
            if same_action:
                boundary_ambiguous = True
            continue
        if item.continuation_hint and (same_action or continuation_kind or (same_project and same_license)):
            included.append(item.event_id)
            continue
        excluded.append(item.event_id)
        reason_codes.append("boundary_split")
        if continuation_kind and not item.new_episode_hint:
            boundary_ambiguous = True
    included_orders = [
        item.order_index for item in events if item.event_id in set(included)
    ]
    return P02EpisodeBoundaryReport(
        boundary_window_start=min(included_orders) if included_orders else None,
        boundary_window_end=max(included_orders) if included_orders else None,
        action_trace_refs=tuple(item.event_id for item in events),
        included_event_refs=tuple(included),
        excluded_event_refs=tuple(excluded),
        boundary_ambiguous=boundary_ambiguous,
        reason_codes=tuple(dict.fromkeys(reason_codes)) if reason_codes else ("single_episode",),
        reason="p02 boundary construction grouped continuation events and excluded out-of-boundary events",
    )


def _build_completion_state(
    *,
    included_events: tuple[str, ...],
    execution_events: tuple[P02ExecutionEvent, ...],
    outcome_evidence: tuple[P02OutcomeEvidence, ...],
    licensed_actions: tuple[P02LicensedActionSnapshot, ...],
) -> P02CompletionAndVerificationState:
    included_set = set(included_events)
    events = [item for item in execution_events if item.event_id in included_set]
    if not events:
        return P02CompletionAndVerificationState(
            execution_status=P02ExecutionStatus.CANDIDATE_ONLY,
            outcome_verification_status=P02OutcomeVerificationStatus.OUTCOME_UNKNOWN,
            status=P02EpisodeStatus.CANDIDATE_EPISODE_ONLY,
            completion_verified=False,
            awaiting_verification=False,
            verification_conflicted=False,
            outcome_unknown=True,
            reason="p02 has no included execution events; keeping candidate_episode_only status",
        )

    kinds = {item.event_kind for item in events}
    aborted_seen = "aborted" in kinds
    deferred_seen = "deferred" in kinds
    partial_seen = "partial" in kinds
    blocked_seen = "blocked" in kinds
    executed_seen = bool(kinds.intersection({"executed", "partial", "blocked", "aborted", "deferred"}))
    emitted_seen = "emitted" in kinds

    if aborted_seen:
        execution_status = P02ExecutionStatus.ABORTED
    elif deferred_seen:
        execution_status = P02ExecutionStatus.DEFERRED
    elif partial_seen:
        execution_status = P02ExecutionStatus.PARTIAL
    elif blocked_seen:
        execution_status = P02ExecutionStatus.BLOCKED
    elif executed_seen or emitted_seen:
        execution_status = P02ExecutionStatus.EXECUTED
    else:
        execution_status = P02ExecutionStatus.CANDIDATE_ONLY

    action_refs = {item.action_ref for item in events}
    evidence = [item for item in outcome_evidence if item.action_ref in action_refs]
    verified_success = any(item.evidence_kind == "verified_success" and item.verified for item in evidence)
    verified_failure = any(item.evidence_kind in {"verified_failure", "verification_failed"} for item in evidence)
    observed = any(item.evidence_kind in {"observed_success", "observed_failure"} for item in evidence)
    conflicting = any(item.conflicting for item in evidence) or (verified_success and verified_failure)

    if conflicting:
        verification_status = P02OutcomeVerificationStatus.VERIFICATION_CONFLICTED
    elif verified_success or verified_failure:
        verification_status = P02OutcomeVerificationStatus.VERIFIED
    elif observed:
        verification_status = P02OutcomeVerificationStatus.OBSERVED_UNVERIFIED
    elif executed_seen or emitted_seen:
        verification_status = P02OutcomeVerificationStatus.AWAITING_VERIFICATION
    else:
        verification_status = P02OutcomeVerificationStatus.OUTCOME_UNKNOWN

    licensed_ids = {item.action_id for item in licensed_actions if item.allowed}
    all_linked = all(
        item.action_ref in licensed_ids or bool((item.source_license_ref or "").strip())
        for item in events
    )

    if execution_status is P02ExecutionStatus.ABORTED:
        status = P02EpisodeStatus.ABORTED
    elif execution_status is P02ExecutionStatus.DEFERRED:
        status = P02EpisodeStatus.DEFERRED
    elif execution_status is P02ExecutionStatus.PARTIAL:
        status = P02EpisodeStatus.PARTIAL
    elif execution_status is P02ExecutionStatus.BLOCKED:
        status = P02EpisodeStatus.BLOCKED
    elif verification_status is P02OutcomeVerificationStatus.VERIFICATION_CONFLICTED:
        status = P02EpisodeStatus.VERIFICATION_CONFLICTED
    elif verified_success and all_linked:
        status = P02EpisodeStatus.COMPLETED_AS_LICENSED
    elif verification_status in {
        P02OutcomeVerificationStatus.AWAITING_VERIFICATION,
        P02OutcomeVerificationStatus.OBSERVED_UNVERIFIED,
    }:
        status = P02EpisodeStatus.AWAITING_VERIFICATION
    elif execution_status is P02ExecutionStatus.EXECUTED:
        status = P02EpisodeStatus.EXECUTED
    else:
        status = P02EpisodeStatus.OUTCOME_UNKNOWN

    if verified_failure and status is not P02EpisodeStatus.VERIFICATION_CONFLICTED:
        status = P02EpisodeStatus.BLOCKED

    return P02CompletionAndVerificationState(
        execution_status=execution_status,
        outcome_verification_status=verification_status,
        status=status,
        completion_verified=bool(verified_success and all_linked and status is P02EpisodeStatus.COMPLETED_AS_LICENSED),
        awaiting_verification=status in {P02EpisodeStatus.AWAITING_VERIFICATION, P02EpisodeStatus.EXECUTED},
        verification_conflicted=status is P02EpisodeStatus.VERIFICATION_CONFLICTED,
        outcome_unknown=status in {P02EpisodeStatus.OUTCOME_UNKNOWN, P02EpisodeStatus.EXECUTED},
        reason="p02 separates execution trace from outcome verification before assigning closure status",
    )


def _license_link_missing(
    *,
    included_events: tuple[str, ...],
    execution_events: tuple[P02ExecutionEvent, ...],
    licensed_actions: tuple[P02LicensedActionSnapshot, ...],
) -> bool:
    included_set = set(included_events)
    events = [item for item in execution_events if item.event_id in included_set]
    if not events:
        return True
    licensed_ids = {item.action_id for item in licensed_actions if item.allowed}
    licensed_refs = {item.source_license_ref for item in licensed_actions if item.allowed}
    for item in events:
        if item.action_ref in licensed_ids:
            continue
        if (item.source_license_ref or "").strip() in licensed_refs:
            continue
        return True
    return False


def _overrun_detected(
    *,
    included_events: tuple[str, ...],
    execution_events: tuple[P02ExecutionEvent, ...],
    licensed_actions: tuple[P02LicensedActionSnapshot, ...],
) -> bool:
    included_set = set(included_events)
    events = [
        item for item in execution_events if item.event_id in included_set and item.event_kind in {"executed", "partial"}
    ]
    if not events:
        return False
    licensed_ids = {item.action_id for item in licensed_actions if item.allowed}
    licensed_refs = {item.source_license_ref for item in licensed_actions if item.allowed}
    for item in events:
        if item.action_ref in licensed_ids:
            continue
        if (item.source_license_ref or "").strip() in licensed_refs:
            continue
        return True
    return False


def _resolve_episode_status(
    *,
    completion: P02CompletionAndVerificationState,
    overrun_detected: bool,
    license_link_missing: bool,
) -> P02EpisodeStatus:
    if overrun_detected:
        return P02EpisodeStatus.OVERRAN_SCOPE
    if license_link_missing and completion.status is P02EpisodeStatus.COMPLETED_AS_LICENSED:
        return P02EpisodeStatus.AWAITING_VERIFICATION
    return completion.status


def _build_residue(
    *,
    tick_id: str,
    completion: P02CompletionAndVerificationState,
    side_effects: tuple[str, ...],
    commitment_carryover_count: int,
) -> tuple[P02ResidueItem, ...]:
    residue: list[P02ResidueItem] = []
    if completion.awaiting_verification:
        residue.append(
            P02ResidueItem(
                residue_id=f"{tick_id}:residue:pending_verification",
                residue_kind=P02ResidueKind.PENDING_VERIFICATION,
                ref_id="verification:pending",
                unresolved=True,
                reason="execution trace exists but completion is not externally verified",
                provenance="p02.residue",
            )
        )
    for item in side_effects:
        residue.append(
            P02ResidueItem(
                residue_id=f"{tick_id}:residue:side_effect:{item}",
                residue_kind=P02ResidueKind.UNRESOLVED_SIDE_EFFECT,
                ref_id=item,
                unresolved=True,
                reason="side effect observed in intervention episode and must remain visible",
                provenance="p02.residue",
            )
        )
    if commitment_carryover_count > 0 and completion.status is not P02EpisodeStatus.COMPLETED_AS_LICENSED:
        residue.append(
            P02ResidueItem(
                residue_id=f"{tick_id}:residue:followup",
                residue_kind=P02ResidueKind.FOLLOW_UP_OBLIGATION,
                ref_id="c06:commitment_carryover",
                unresolved=True,
                reason="upstream surfaced commitment carryover requires follow-up handoff from p02",
                provenance="p02.residue",
            )
        )
    return tuple(residue)


def _uncertainty_markers(
    *,
    boundary: P02EpisodeBoundaryReport,
    completion: P02CompletionAndVerificationState,
    license_link_missing: bool,
    possible_overrun: bool,
) -> tuple[str, ...]:
    markers: list[str] = []
    if boundary.boundary_ambiguous:
        markers.append("boundary_ambiguous")
    if license_link_missing:
        markers.append("license_link_missing")
    if possible_overrun:
        markers.append("possible_overrun")
    if completion.awaiting_verification:
        markers.append("execution_seen_outcome_unverified")
    if completion.outcome_unknown:
        markers.append("outcome_unknown")
    if completion.verification_conflicted:
        markers.append("verification_conflicted")
    if not markers:
        markers.append("none")
    return tuple(dict.fromkeys(markers))


def _build_gate(
    *,
    metadata: P02EpisodeMetadata,
    record: P02InterventionEpisodeRecord,
) -> P02EpisodeGateDecision:
    episode_consumer_ready = metadata.episode_count > 0
    boundary_consumer_ready = not record.boundary_report.boundary_ambiguous
    verification_consumer_ready = (
        metadata.completion_verified_count > 0
        or metadata.awaiting_verification_count > 0
    )
    restrictions: list[str] = []
    if not episode_consumer_ready:
        restrictions.append("episode_consumer_not_ready")
    if not boundary_consumer_ready:
        restrictions.append("boundary_ambiguous")
    if not verification_consumer_ready:
        restrictions.append("verification_consumer_not_ready")
    if metadata.awaiting_verification_count > 0:
        restrictions.append("awaiting_verification")
    if metadata.overrun_detected_count > 0:
        restrictions.append("possible_overrun")
    if metadata.residue_count > 0:
        restrictions.append("residue_followup_required")
    if metadata.license_link_missing_count > 0:
        restrictions.append("license_link_missing")
    return P02EpisodeGateDecision(
        episode_consumer_ready=episode_consumer_ready,
        boundary_consumer_ready=boundary_consumer_ready,
        verification_consumer_ready=verification_consumer_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="p02 gate exposes episode/boundary/verification readiness and bounded restrictions",
    )


def _build_minimal_result(
    *,
    reason: str,
    source_lineage: tuple[str, ...],
    restrictions: tuple[str, ...],
) -> P02InterventionEpisodeResult:
    metadata = P02EpisodeMetadata(
        episode_count=0,
        completed_as_licensed_count=0,
        partial_episode_count=0,
        blocked_episode_count=0,
        awaiting_verification_count=0,
        completion_verified_count=0,
        overrun_detected_count=0,
        boundary_ambiguous_count=0,
        license_link_missing_count=0,
        residue_count=0,
        side_effect_count=0,
        source_lineage=source_lineage,
    )
    gate = P02EpisodeGateDecision(
        episode_consumer_ready=False,
        boundary_consumer_ready=False,
        verification_consumer_ready=False,
        restrictions=restrictions,
        reason=reason,
    )
    scope = P02ScopeMarker(
        scope="rt01_hosted_p02_first_slice",
        rt01_hosted_only=True,
        p02_first_slice_only=True,
        no_project_formation_authority=True,
        no_action_licensing_authority=True,
        no_external_success_claim_without_evidence=True,
        no_memory_retention_authority=True,
        no_map_wide_rollout_claim=True,
        reason="p02 minimal fallback scope",
    )
    telemetry = P02Telemetry(
        episode_count=0,
        completed_as_licensed_count=0,
        partial_episode_count=0,
        blocked_episode_count=0,
        awaiting_verification_count=0,
        overrun_detected_count=0,
        boundary_ambiguous_count=0,
        residue_count=0,
        side_effect_count=0,
        downstream_consumer_ready=False,
    )
    return P02InterventionEpisodeResult(
        episodes=(),
        metadata=metadata,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )
