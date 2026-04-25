from __future__ import annotations

from substrate.o04_rupture_hostility_coercion import O04DynamicResult
from substrate.p01_project_formation import P01ProjectFormationResult
from substrate.r05_appraisal_sovereign_protective_regulation import (
    R05ProtectiveMode,
    R05ProtectiveResult,
)
from substrate.v01_normative_permission_commitment_licensing import V01LicenseResult
from substrate.v02_communicative_intent_utterance_plan_bridge import V02UtterancePlanResult
from substrate.v03_surface_verbalization_causality_constrained_realization import (
    V03ConstrainedRealizationResult,
)
from substrate.c06_surfacing_candidates.models import (
    C06CandidateClass,
    C06CandidateSetMetadata,
    C06ContinuityHorizon,
    C06ScopeMarker,
    C06StrengthGrade,
    C06SuppressedItem,
    C06SuppressionReason,
    C06SuppressionReport,
    C06SurfacedCandidate,
    C06SurfacedCandidateSet,
    C06SurfacingGateDecision,
    C06SurfacingInput,
    C06SurfacingResult,
    C06SurfacingStatus,
    C06Telemetry,
    C06UncertaintyState,
)


def build_c06_surfacing_candidates(
    *,
    tick_id: str,
    tick_index: int,
    v03_result: V03ConstrainedRealizationResult,
    v02_result: V02UtterancePlanResult,
    v01_result: V01LicenseResult,
    p01_result: P01ProjectFormationResult | None,
    o04_result: O04DynamicResult | None,
    r05_result: R05ProtectiveResult | None,
    surfacing_input: C06SurfacingInput | None,
    source_lineage: tuple[str, ...],
    surfacing_enabled: bool = True,
) -> C06SurfacingResult:
    if not surfacing_enabled:
        return _build_minimal_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
            reason="c06 surfacing disabled in ablation context",
            restrictions=("c06_disabled", "insufficient_surfacing_basis"),
        )
    if not isinstance(v03_result, V03ConstrainedRealizationResult):
        raise TypeError("build_c06_surfacing_candidates requires V03ConstrainedRealizationResult")
    if not isinstance(v02_result, V02UtterancePlanResult):
        raise TypeError("build_c06_surfacing_candidates requires V02UtterancePlanResult")
    if not isinstance(v01_result, V01LicenseResult):
        raise TypeError("build_c06_surfacing_candidates requires V01LicenseResult")

    surfacing_input = surfacing_input or C06SurfacingInput(input_id=f"{tick_id}:c06:default")
    has_surface_basis = bool(v03_result.artifact.surface_text.strip())
    if not has_surface_basis:
        return _build_minimal_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
            reason="c06 has no realized-surface basis to extract continuity candidates",
            restrictions=("insufficient_surfacing_basis", "no_continuity_candidates"),
        )

    raw_candidates: list[C06SurfacedCandidate] = []
    suppressed: list[C06SuppressedItem] = []
    false_merge_detected = False

    def _candidate(
        *,
        candidate_class: C06CandidateClass,
        identity_hint: str,
        identity_stabilizer: str,
        source_refs: tuple[str, ...],
        horizon: C06ContinuityHorizon,
        strength: C06StrengthGrade,
        uncertainty: C06UncertaintyState,
        project_relation: str,
        discourse_relation: str,
        consumers: tuple[str, ...],
        dismissal_risk: str,
        rationale: tuple[str, ...],
    ) -> C06SurfacedCandidate:
        return C06SurfacedCandidate(
            candidate_id=f"c06:{tick_id}:{len(raw_candidates) + 1}",
            candidate_class=candidate_class,
            source_refs=source_refs,
            identity_hint=identity_hint,
            identity_stabilizer=identity_stabilizer,
            continuity_horizon=horizon,
            strength_grade=strength,
            uncertainty_state=uncertainty,
            relation_to_current_project=project_relation,
            relation_to_discourse=discourse_relation,
            suggested_next_layer_consumers=consumers,
            dismissal_risk=dismissal_risk,
            rationale_codes=rationale,
            provenance="c06.surfacing_candidates.policy",
        )

    project_active = bool(_p01_active_project_count(p01_result) > 0)
    project_blocked = bool(
        isinstance(p01_result, P01ProjectFormationResult)
        and (
            p01_result.state.blocked_pending_grounding
            or p01_result.state.candidate_only_without_activation_basis
            or p01_result.state.no_safe_project_formation
        )
    )
    commitment_basis = bool(
        v01_result.state.commitment_delta_count > 0 or surfacing_input.prior_commitment_carry_present
    )
    threatened_commitment_basis = bool(
        v01_result.state.promise_like_act_denied and commitment_basis
    )
    repair_basis = bool(
        surfacing_input.prior_repair_open
        or v03_result.failure_state.replan_required
        or v03_result.constraint_report.hard_constraint_violation_count > 0
    )
    clarification_basis = bool(
        surfacing_input.prior_unresolved_question_present
        or v02_result.state.clarification_first_required
    )
    protective_basis = _protective_monitor_basis(o04_result=o04_result, r05_result=r05_result)
    boundary_basis = bool(v02_result.state.protective_boundary_first)
    closure_basis = bool(surfacing_input.closure_resolved)
    alignment_source_anchors = _aligned_source_act_refs(v03_result=v03_result)
    alignment_primary_anchor = (
        alignment_source_anchors[0] if alignment_source_anchors else "none"
    )
    alignment_violation_refs = _alignment_violation_refs(v03_result=v03_result)

    if clarification_basis and not closure_basis:
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.OPEN_QUESTION,
                identity_hint="open_question:clarification_loop",
                identity_stabilizer="clarification:loop",
                source_refs=("v02:clarification_first_required",),
                horizon=C06ContinuityHorizon.NEXT_TURN,
                strength=C06StrengthGrade.MODERATE,
                uncertainty=C06UncertaintyState.UNRESOLVED,
                project_relation="project_context_pending",
                discourse_relation="unresolved_clarification_loop",
                consumers=("P02", "P03"),
                dismissal_risk="high_if_dropped",
                rationale=("clarification_first_required",),
            )
        )
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.PENDING_CLARIFICATION,
                identity_hint="pending_clarification:current_turn",
                identity_stabilizer="clarification:pending",
                source_refs=("v01:clarification_before_commitment",),
                horizon=C06ContinuityHorizon.IMMEDIATE,
                strength=C06StrengthGrade.MODERATE,
                uncertainty=C06UncertaintyState.CANDIDATE_NEEDS_CONFIRMATION,
                project_relation="project_context_pending",
                discourse_relation="clarification_pending",
                consumers=("P02",),
                dismissal_risk="high_if_dropped",
                rationale=("pending_clarification",),
            )
        )
    elif clarification_basis and closure_basis:
        suppressed.append(
            _suppressed_item(
                tick_id=tick_id,
                item_id="open_question:clarification_loop",
                reason=C06SuppressionReason.ALREADY_CLOSED,
                source_refs=("v02:clarification_first_required",),
                rationale=("closure_resolved",),
            )
        )

    if commitment_basis:
        commitment_source_refs = (
            "v01:commitment_delta",
            f"v03:aligned_source_act:{alignment_primary_anchor}",
        )
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.COMMITMENT_CARRYOVER,
                identity_hint="commitment:carryover_scope",
                identity_stabilizer="commitment:carryover_scope",
                source_refs=commitment_source_refs,
                horizon=C06ContinuityHorizon.SHORT_CHAIN,
                strength=C06StrengthGrade.STRONG,
                uncertainty=C06UncertaintyState.PROVISIONAL,
                project_relation="active_project" if project_active else "project_pending",
                discourse_relation="continuity_commitment_thread",
                consumers=("P02", "P03", "N04"),
                dismissal_risk="high_if_dropped",
                rationale=("commitment_delta_present", "confidence_residue_required"),
            )
        )
        if (
            surfacing_input.prior_commitment_carry_present
            and v01_result.state.commitment_delta_count > 0
        ):
            raw_candidates.append(
                _candidate(
                    candidate_class=C06CandidateClass.COMMITMENT_CARRYOVER,
                    identity_hint="commitment:carryover_scope",
                    identity_stabilizer="commitment:carryover_scope",
                    source_refs=(
                        "history:prior_commitment_carry",
                        f"v03:aligned_source_act:{alignment_primary_anchor}",
                    ),
                    horizon=C06ContinuityHorizon.SHORT_CHAIN,
                    strength=C06StrengthGrade.MODERATE,
                    uncertainty=C06UncertaintyState.PROVISIONAL,
                    project_relation="active_project" if project_active else "project_pending",
                    discourse_relation="continuity_commitment_thread",
                    consumers=("P02", "P03"),
                    dismissal_risk="high_if_dropped",
                    rationale=("prior_commitment_carry_present",),
                )
            )
    if threatened_commitment_basis:
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.THREATENED_COMMITMENT,
                identity_hint="commitment:threatened_by_denial",
                identity_stabilizer="commitment:threatened",
                source_refs=("v01:promise_like_denied",),
                horizon=C06ContinuityHorizon.NEXT_TURN,
                strength=C06StrengthGrade.MODERATE,
                uncertainty=C06UncertaintyState.PROVISIONAL,
                project_relation="active_project" if project_active else "project_pending",
                discourse_relation="commitment_threat_surface",
                consumers=("P02", "P03"),
                dismissal_risk="high_if_dropped",
                rationale=("promise_like_act_denied",),
            )
        )

    if repair_basis:
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.REPAIR_OBLIGATION,
                identity_hint="repair:constrained_realization_violation",
                identity_stabilizer=(
                    f"repair_alignment:{alignment_violation_refs[0]}"
                    if alignment_violation_refs
                    else "repair_alignment:none"
                ),
                source_refs=(
                    "v03:constraint_report",
                    *alignment_violation_refs,
                ),
                horizon=C06ContinuityHorizon.IMMEDIATE,
                strength=C06StrengthGrade.STRONG,
                uncertainty=C06UncertaintyState.KNOWN,
                project_relation="repair_before_project_continuation",
                discourse_relation="repair_required",
                consumers=("P02",),
                dismissal_risk="high_if_dropped",
                rationale=("v03_replan_required_or_violation",),
            )
        )

    if boundary_basis:
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.BOUNDARY_TO_PRESERVE,
                identity_hint="boundary:protective_continuation",
                identity_stabilizer="boundary:protective_continuation",
                source_refs=("v02:protective_boundary_first",),
                horizon=C06ContinuityHorizon.NEXT_TURN,
                strength=C06StrengthGrade.MODERATE,
                uncertainty=C06UncertaintyState.KNOWN,
                project_relation="project_guardrail",
                discourse_relation="boundary_carryover",
                consumers=("P02", "P04"),
                dismissal_risk="moderate_if_dropped",
                rationale=("protective_boundary_first",),
            )
        )

    if project_active and not project_blocked:
        if alignment_source_anchors:
            for anchor in alignment_source_anchors:
                raw_candidates.append(
                    _candidate(
                        candidate_class=C06CandidateClass.PROJECT_CONTINUATION_CUE,
                        identity_hint="project:active_continuation",
                        identity_stabilizer=f"project_anchor:{anchor}",
                        source_refs=(
                            "p01:active_project",
                            f"v03:aligned_source_act:{anchor}",
                        ),
                        horizon=C06ContinuityHorizon.NEXT_TURN,
                        strength=C06StrengthGrade.MODERATE,
                        uncertainty=C06UncertaintyState.PROVISIONAL,
                        project_relation="active_project",
                        discourse_relation="project_continuation",
                        consumers=("P02", "P03"),
                        dismissal_risk="moderate_if_dropped",
                        rationale=("active_project_present", "alignment_anchor_selected"),
                    )
                )
        elif v03_result.alignment_map.alignments:
            raw_candidates.append(
                _candidate(
                    candidate_class=C06CandidateClass.WEAK_CANDIDATE,
                    identity_hint="project:active_continuation",
                    identity_stabilizer="project_alignment_underconstrained",
                    source_refs=("p01:active_project", "v03:alignment_underconstrained"),
                    horizon=C06ContinuityHorizon.NEXT_TURN,
                    strength=C06StrengthGrade.PROVISIONAL,
                    uncertainty=C06UncertaintyState.INSUFFICIENT_DELTA_BASIS,
                    project_relation="active_project_alignment_underconstrained",
                    discourse_relation="project_continuation_underconstrained",
                    consumers=("P02",),
                    dismissal_risk="high_if_dropped",
                    rationale=(
                        "active_project_present",
                        "alignment_anchor_missing",
                    ),
                )
            )
        else:
            raw_candidates.append(
                _candidate(
                    candidate_class=C06CandidateClass.PROJECT_CONTINUATION_CUE,
                    identity_hint="project:active_continuation",
                    identity_stabilizer="project_anchor:none",
                    source_refs=("p01:active_project",),
                    horizon=C06ContinuityHorizon.NEXT_TURN,
                    strength=C06StrengthGrade.MODERATE,
                    uncertainty=C06UncertaintyState.PROVISIONAL,
                    project_relation="active_project",
                    discourse_relation="project_continuation",
                    consumers=("P02", "P03"),
                    dismissal_risk="moderate_if_dropped",
                    rationale=("active_project_present",),
                )
            )

    if protective_basis:
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.PROTECTIVE_MONITOR,
                identity_hint="protective:monitor_state",
                identity_stabilizer="protective:monitor_state",
                source_refs=("r05:protective_mode", "o04:rupture_risk"),
                horizon=C06ContinuityHorizon.SHORT_CHAIN,
                strength=C06StrengthGrade.MODERATE,
                uncertainty=C06UncertaintyState.PROVISIONAL,
                project_relation="project_requires_protective_monitor",
                discourse_relation="protective_monitor_carry",
                consumers=("P02", "P04"),
                dismissal_risk="high_if_dropped",
                rationale=("protective_mode_or_rupture_risk_present",),
            )
        )

    if closure_basis and not commitment_basis and not repair_basis and not clarification_basis:
        raw_candidates.append(
            _candidate(
                candidate_class=C06CandidateClass.CLOSURE_CANDIDATE,
                identity_hint="closure:resolved_exchange",
                identity_stabilizer="closure:resolved_exchange",
                source_refs=("c06:closure_resolved",),
                horizon=C06ContinuityHorizon.IMMEDIATE,
                strength=C06StrengthGrade.MODERATE,
                uncertainty=C06UncertaintyState.KNOWN,
                project_relation="no_project_relation",
                discourse_relation="closure_state",
                consumers=("N04",),
                dismissal_risk="low_if_dropped",
                rationale=("closure_resolved",),
            )
        )

    for fragment in surfacing_input.salient_but_resolved_fragments:
        suppressed.append(
            _suppressed_item(
                tick_id=tick_id,
                item_id=f"salient:{fragment}",
                reason=C06SuppressionReason.STYLISTICALLY_SALIENT_ONLY,
                source_refs=("v03:surface_text",),
                rationale=("salience_without_continuity_relevance",),
            )
        )

    published_refs = set(surfacing_input.published_frontier_item_ids)
    for workspace_ref in surfacing_input.workspace_item_ids:
        if workspace_ref in published_refs:
            continue
        suppression_reason = (
            C06SuppressionReason.FRONTIER_NOT_PUBLISHED
            if surfacing_input.published_frontier_requirement
            else C06SuppressionReason.HIDDEN_WORKSPACE_ONLY
        )
        suppression_rationale = (
            ("c06_1_frontier_not_published",)
            if suppression_reason is C06SuppressionReason.FRONTIER_NOT_PUBLISHED
            else ("c06_1_hidden_workspace_only",)
        )
        suppressed.append(
            _suppressed_item(
                tick_id=tick_id,
                item_id=f"workspace:{workspace_ref}",
                reason=suppression_reason,
                source_refs=(workspace_ref,),
                rationale=suppression_rationale,
            )
        )

    deduped_candidates, duplicate_merge_count, false_merge_detected = _deduplicate_candidates(
        tick_id=tick_id,
        candidates=raw_candidates,
        already_false_merge=false_merge_detected,
        suppressed=suppressed,
    )

    unresolved_ambiguity_preserved = _resolve_ambiguity_preservation(
        required=surfacing_input.unresolved_ambiguity_preservation_required,
        tokens=surfacing_input.unresolved_ambiguity_tokens,
        candidates=deduped_candidates,
    )
    confidence_residue_preserved = _resolve_confidence_residue_preservation(
        required=surfacing_input.confidence_residue_preservation_required,
        tokens=surfacing_input.confidence_residue_tokens,
        candidates=deduped_candidates,
    )
    published_frontier_requirement_satisfied = _resolve_frontier_publication(
        required=surfacing_input.published_frontier_requirement,
        candidates=deduped_candidates,
        published_frontier_refs=published_refs,
        workspace_refs=set(surfacing_input.workspace_item_ids),
    )

    ambiguous_candidate_count = sum(
        1
        for item in deduped_candidates
        if item.candidate_class in {C06CandidateClass.CLASS_AMBIGUOUS, C06CandidateClass.WEAK_CANDIDATE}
        or item.uncertainty_state in {
            C06UncertaintyState.UNRESOLVED,
            C06UncertaintyState.INSUFFICIENT_DELTA_BASIS,
        }
    )
    commitment_carryover_count = sum(
        1 for item in deduped_candidates if item.candidate_class is C06CandidateClass.COMMITMENT_CARRYOVER
    )
    repair_obligation_count = sum(
        1 for item in deduped_candidates if item.candidate_class is C06CandidateClass.REPAIR_OBLIGATION
    )
    protective_monitor_count = sum(
        1 for item in deduped_candidates if item.candidate_class is C06CandidateClass.PROTECTIVE_MONITOR
    )
    closure_candidate_count = sum(
        1 for item in deduped_candidates if item.candidate_class is C06CandidateClass.CLOSURE_CANDIDATE
    )
    no_continuity_candidates = len(deduped_candidates) <= 0

    status = (
        C06SurfacingStatus.NO_CONTINUITY_CANDIDATES
        if no_continuity_candidates
        else C06SurfacingStatus.SURFACED
    )
    metadata = C06CandidateSetMetadata(
        candidate_count=len(deduped_candidates),
        ambiguous_candidate_count=ambiguous_candidate_count,
        commitment_carryover_count=commitment_carryover_count,
        repair_obligation_count=repair_obligation_count,
        protective_monitor_count=protective_monitor_count,
        closure_candidate_count=closure_candidate_count,
        duplicate_merge_count=duplicate_merge_count,
        false_merge_detected=false_merge_detected,
        no_continuity_candidates=no_continuity_candidates,
        published_frontier_requirement=surfacing_input.published_frontier_requirement,
        published_frontier_requirement_satisfied=published_frontier_requirement_satisfied,
        unresolved_ambiguity_preserved=unresolved_ambiguity_preserved,
        confidence_residue_preserved=confidence_residue_preserved,
        source_lineage=tuple(dict.fromkeys((*source_lineage, *v03_result.alignment_map.unaligned_segment_ids))),
    )
    suppression_report = C06SuppressionReport(
        examined_item_count=len(raw_candidates) + len(surfacing_input.workspace_item_ids),
        suppressed_item_count=len(suppressed),
        suppressed_items=tuple(suppressed),
        reason="c06 suppression report keeps examined-but-not-surfaced items explicit",
    )
    candidate_set = C06SurfacedCandidateSet(
        candidate_set_id=f"c06-candidates:{tick_id}",
        status=status,
        surfaced_candidates=tuple(deduped_candidates),
        suppression_report=suppression_report,
        metadata=metadata,
        reason=(
            "c06 surfaced typed continuity candidates from realized utterance and upstream deltas "
            "with explicit suppression and identity-merge accounting"
        ),
    )
    gate = _build_gate(candidate_set=candidate_set)
    scope = C06ScopeMarker(
        scope="rt01_hosted_c06_first_slice",
        rt01_hosted_only=True,
        c06_first_slice_only=True,
        c06_1_workspace_handoff_contract=True,
        no_retention_write_layer=True,
        no_project_reformation_layer=True,
        no_map_wide_rollout_claim=True,
        reason="c06 first slice surfaces typed continuity candidates without retention/planner authority",
    )
    telemetry = C06Telemetry(
        candidate_set_id=candidate_set.candidate_set_id,
        tick_index=tick_index,
        status=status,
        surfaced_candidate_count=metadata.candidate_count,
        suppressed_item_count=suppression_report.suppressed_item_count,
        commitment_carryover_count=metadata.commitment_carryover_count,
        repair_obligation_count=metadata.repair_obligation_count,
        protective_monitor_count=metadata.protective_monitor_count,
        closure_candidate_count=metadata.closure_candidate_count,
        ambiguous_candidate_count=metadata.ambiguous_candidate_count,
        duplicate_merge_count=metadata.duplicate_merge_count,
        false_merge_detected=metadata.false_merge_detected,
        published_frontier_requirement=metadata.published_frontier_requirement,
        unresolved_ambiguity_preserved=metadata.unresolved_ambiguity_preserved,
        confidence_residue_preserved=metadata.confidence_residue_preserved,
        downstream_consumer_ready=(
            gate.candidate_set_consumer_ready
            and gate.suppression_report_consumer_ready
            and gate.identity_merge_consumer_ready
        ),
    )
    return C06SurfacingResult(
        candidate_set=candidate_set,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=(
            "c06 built explicit typed surfacing candidate set with suppression report, "
            "identity merge discipline and c06.1 workspace-to-frontier publication constraints"
        ),
    )


def _build_gate(*, candidate_set: C06SurfacedCandidateSet) -> C06SurfacingGateDecision:
    metadata = candidate_set.metadata
    candidate_set_consumer_ready = bool(
        metadata.candidate_count > 0 or metadata.no_continuity_candidates
    )
    suppression_report_consumer_ready = bool(
        candidate_set.suppression_report.examined_item_count > 0
        or metadata.candidate_count > 0
    )
    identity_merge_consumer_ready = not metadata.false_merge_detected
    restrictions: list[str] = []
    if not candidate_set_consumer_ready:
        restrictions.append("candidate_set_not_ready")
    if not suppression_report_consumer_ready:
        restrictions.append("suppression_report_not_ready")
    if not identity_merge_consumer_ready:
        restrictions.append("identity_merge_review_required")
    if metadata.ambiguous_candidate_count > 0:
        restrictions.append("candidate_ambiguity")
    if metadata.commitment_carryover_count > 0:
        restrictions.append("commitment_carryover_present")
    if metadata.protective_monitor_count > 0:
        restrictions.append("protective_monitor_present")
    if not metadata.published_frontier_requirement_satisfied:
        restrictions.append("frontier_publication_violation")
    if not metadata.unresolved_ambiguity_preserved:
        restrictions.append("unresolved_ambiguity_not_preserved")
    if not metadata.confidence_residue_preserved:
        restrictions.append("confidence_residue_not_preserved")
    return C06SurfacingGateDecision(
        candidate_set_consumer_ready=candidate_set_consumer_ready,
        suppression_report_consumer_ready=suppression_report_consumer_ready,
        identity_merge_consumer_ready=identity_merge_consumer_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="c06 gate exposes candidate-set readiness, suppression visibility and identity-merge readiness",
    )


def _suppressed_item(
    *,
    tick_id: str,
    item_id: str,
    reason: C06SuppressionReason,
    source_refs: tuple[str, ...],
    rationale: tuple[str, ...],
) -> C06SuppressedItem:
    return C06SuppressedItem(
        item_id=f"{tick_id}:{item_id}",
        suppression_reason=reason,
        source_refs=source_refs,
        rationale_codes=rationale,
        provenance="c06.surfacing_candidates.suppression",
    )


def _deduplicate_candidates(
    *,
    tick_id: str,
    candidates: list[C06SurfacedCandidate],
    already_false_merge: bool,
    suppressed: list[C06SuppressedItem],
) -> tuple[list[C06SurfacedCandidate], int, bool]:
    dedup_map: dict[str, C06SurfacedCandidate] = {}
    class_by_identity: dict[str, C06CandidateClass] = {}
    duplicate_merge_count = 0
    false_merge_detected = already_false_merge
    for item in candidates:
        key = f"{item.candidate_class.value}|{item.identity_hint}|{item.identity_stabilizer}"
        class_key = f"{item.identity_hint}|{item.identity_stabilizer}"
        if class_key in class_by_identity and class_by_identity[class_key] != item.candidate_class:
            false_merge_detected = True
        class_by_identity[class_key] = item.candidate_class
        if key not in dedup_map:
            dedup_map[key] = item
            continue
        duplicate_merge_count += 1
        prior = dedup_map[key]
        dedup_map[key] = C06SurfacedCandidate(
            candidate_id=prior.candidate_id,
            candidate_class=prior.candidate_class,
            source_refs=tuple(dict.fromkeys((*prior.source_refs, *item.source_refs))),
            identity_hint=prior.identity_hint,
            identity_stabilizer=prior.identity_stabilizer,
            continuity_horizon=prior.continuity_horizon,
            strength_grade=prior.strength_grade,
            uncertainty_state=prior.uncertainty_state,
            relation_to_current_project=prior.relation_to_current_project,
            relation_to_discourse=prior.relation_to_discourse,
            suggested_next_layer_consumers=tuple(
                dict.fromkeys(
                    (*prior.suggested_next_layer_consumers, *item.suggested_next_layer_consumers)
                )
            ),
            dismissal_risk=prior.dismissal_risk,
            rationale_codes=tuple(dict.fromkeys((*prior.rationale_codes, *item.rationale_codes, "identity_merged"))),
            provenance=prior.provenance,
        )
        suppressed.append(
            _suppressed_item(
                tick_id=tick_id,
                item_id=item.candidate_id,
                reason=C06SuppressionReason.DUPLICATE_OF_STRONGER_CANDIDATE,
                source_refs=item.source_refs,
                rationale=("identity_merge",),
            )
        )
    return list(dedup_map.values()), duplicate_merge_count, false_merge_detected


def _resolve_ambiguity_preservation(
    *,
    required: bool,
    tokens: tuple[str, ...],
    candidates: list[C06SurfacedCandidate],
) -> bool:
    if not required:
        return True
    if not tokens:
        return True
    unresolved_present = any(
        item.uncertainty_state in {C06UncertaintyState.UNRESOLVED, C06UncertaintyState.PROVISIONAL}
        for item in candidates
    )
    return unresolved_present


def _resolve_confidence_residue_preservation(
    *,
    required: bool,
    tokens: tuple[str, ...],
    candidates: list[C06SurfacedCandidate],
) -> bool:
    if not required:
        return True
    if not tokens:
        return True
    return any(
        item.candidate_class in {C06CandidateClass.COMMITMENT_CARRYOVER, C06CandidateClass.THREATENED_COMMITMENT}
        and item.uncertainty_state in {C06UncertaintyState.PROVISIONAL, C06UncertaintyState.CANDIDATE_NEEDS_CONFIRMATION}
        for item in candidates
    )


def _resolve_frontier_publication(
    *,
    required: bool,
    candidates: list[C06SurfacedCandidate],
    published_frontier_refs: set[str],
    workspace_refs: set[str],
) -> bool:
    if not required:
        return True
    if not workspace_refs:
        return True
    return all(item in published_frontier_refs for item in workspace_refs)


def _aligned_source_act_refs(
    *,
    v03_result: V03ConstrainedRealizationResult,
) -> tuple[str, ...]:
    anchors: list[str] = []
    for item in v03_result.alignment_map.alignments:
        if not item.realized:
            continue
        if not item.ordering_pass:
            continue
        if not item.qualifier_locality_pass:
            continue
        source = str(item.source_act_ref or "").strip()
        if source and source not in anchors:
            anchors.append(source)
    return tuple(anchors)


def _alignment_violation_refs(
    *,
    v03_result: V03ConstrainedRealizationResult,
) -> tuple[str, ...]:
    refs: list[str] = []
    for item in v03_result.alignment_map.alignments:
        if item.ordering_pass and item.qualifier_locality_pass:
            continue
        token = f"v03:alignment_violation:{item.segment_id}"
        if token not in refs:
            refs.append(token)
    return tuple(refs)


def _protective_monitor_basis(
    *,
    o04_result: O04DynamicResult | None,
    r05_result: R05ProtectiveResult | None,
) -> bool:
    if isinstance(r05_result, R05ProtectiveResult) and r05_result.state.protective_mode in {
        R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE,
        R05ProtectiveMode.DEGRADED_OPERATION_ONLY,
        R05ProtectiveMode.RECOVERY_IN_PROGRESS,
    }:
        return True
    if isinstance(o04_result, O04DynamicResult) and o04_result.state.rupture_status.value in {
        "rupture_risk_only",
        "rupture_active_candidate",
    }:
        return True
    return False


def _p01_active_project_count(p01_result: P01ProjectFormationResult | None) -> int:
    if not isinstance(p01_result, P01ProjectFormationResult):
        return 0
    return int(getattr(p01_result.state, "active_project_count", 0))


def _build_minimal_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
    reason: str,
    restrictions: tuple[str, ...],
) -> C06SurfacingResult:
    metadata = C06CandidateSetMetadata(
        candidate_count=0,
        ambiguous_candidate_count=0,
        commitment_carryover_count=0,
        repair_obligation_count=0,
        protective_monitor_count=0,
        closure_candidate_count=0,
        duplicate_merge_count=0,
        false_merge_detected=False,
        no_continuity_candidates=True,
        published_frontier_requirement=True,
        published_frontier_requirement_satisfied=True,
        unresolved_ambiguity_preserved=True,
        confidence_residue_preserved=True,
        source_lineage=source_lineage,
    )
    suppression_report = C06SuppressionReport(
        examined_item_count=0,
        suppressed_item_count=0,
        suppressed_items=(),
        reason=reason,
    )
    candidate_set = C06SurfacedCandidateSet(
        candidate_set_id=f"c06-candidates:{tick_id}",
        status=C06SurfacingStatus.INSUFFICIENT_SURFACING_BASIS,
        surfaced_candidates=(),
        suppression_report=suppression_report,
        metadata=metadata,
        reason=reason,
    )
    gate = C06SurfacingGateDecision(
        candidate_set_consumer_ready=False,
        suppression_report_consumer_ready=False,
        identity_merge_consumer_ready=False,
        restrictions=restrictions,
        reason=reason,
    )
    scope = C06ScopeMarker(
        scope="rt01_hosted_c06_first_slice",
        rt01_hosted_only=True,
        c06_first_slice_only=True,
        c06_1_workspace_handoff_contract=True,
        no_retention_write_layer=True,
        no_project_reformation_layer=True,
        no_map_wide_rollout_claim=True,
        reason="c06 minimal fallback scope",
    )
    telemetry = C06Telemetry(
        candidate_set_id=candidate_set.candidate_set_id,
        tick_index=tick_index,
        status=C06SurfacingStatus.INSUFFICIENT_SURFACING_BASIS,
        surfaced_candidate_count=0,
        suppressed_item_count=0,
        commitment_carryover_count=0,
        repair_obligation_count=0,
        protective_monitor_count=0,
        closure_candidate_count=0,
        ambiguous_candidate_count=0,
        duplicate_merge_count=0,
        false_merge_detected=False,
        published_frontier_requirement=True,
        unresolved_ambiguity_preserved=True,
        confidence_residue_preserved=True,
        downstream_consumer_ready=False,
    )
    return C06SurfacingResult(
        candidate_set=candidate_set,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )
