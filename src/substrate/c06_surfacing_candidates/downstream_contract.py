from __future__ import annotations

from dataclasses import dataclass

from substrate.c06_surfacing_candidates.models import C06SurfacingResult


@dataclass(frozen=True, slots=True)
class C06SurfacingContractView:
    candidate_set_id: str
    status: str
    candidate_count: int
    commitment_carryover_count: int
    repair_obligation_count: int
    protective_monitor_count: int
    closure_candidate_count: int
    ambiguous_candidate_count: int
    suppressed_item_count: int
    duplicate_merge_count: int
    false_merge_detected: bool
    no_continuity_candidates: bool
    published_frontier_requirement: bool
    published_frontier_requirement_satisfied: bool
    unresolved_ambiguity_preserved: bool
    confidence_residue_preserved: bool
    candidate_set_consumer_ready: bool
    suppression_report_consumer_ready: bool
    identity_merge_consumer_ready: bool
    restrictions: tuple[str, ...]
    surfaced_candidate_ids: tuple[str, ...]
    surfaced_candidate_classes: tuple[str, ...]
    suppression_reasons: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_c06_first_slice_only: bool
    scope_c06_1_workspace_handoff_contract: bool
    scope_no_retention_write_layer: bool
    scope_no_project_reformation_layer: bool
    scope_no_map_wide_rollout_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class C06SurfacingConsumerView:
    status: str
    candidate_count: int
    commitment_carryover_count: int
    repair_obligation_count: int
    protective_monitor_count: int
    closure_candidate_count: int
    ambiguous_candidate_count: int
    suppressed_item_count: int
    duplicate_merge_count: int
    false_merge_detected: bool
    no_continuity_candidates: bool
    published_frontier_requirement_satisfied: bool
    unresolved_ambiguity_preserved: bool
    confidence_residue_preserved: bool
    candidate_set_consumer_ready: bool
    suppression_report_consumer_ready: bool
    identity_merge_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_c06_surfacing_contract_view(result: C06SurfacingResult) -> C06SurfacingContractView:
    if not isinstance(result, C06SurfacingResult):
        raise TypeError("derive_c06_surfacing_contract_view requires C06SurfacingResult")
    return C06SurfacingContractView(
        candidate_set_id=result.candidate_set.candidate_set_id,
        status=result.candidate_set.status.value,
        candidate_count=result.candidate_set.metadata.candidate_count,
        commitment_carryover_count=result.candidate_set.metadata.commitment_carryover_count,
        repair_obligation_count=result.candidate_set.metadata.repair_obligation_count,
        protective_monitor_count=result.candidate_set.metadata.protective_monitor_count,
        closure_candidate_count=result.candidate_set.metadata.closure_candidate_count,
        ambiguous_candidate_count=result.candidate_set.metadata.ambiguous_candidate_count,
        suppressed_item_count=result.candidate_set.suppression_report.suppressed_item_count,
        duplicate_merge_count=result.candidate_set.metadata.duplicate_merge_count,
        false_merge_detected=result.candidate_set.metadata.false_merge_detected,
        no_continuity_candidates=result.candidate_set.metadata.no_continuity_candidates,
        published_frontier_requirement=result.candidate_set.metadata.published_frontier_requirement,
        published_frontier_requirement_satisfied=result.candidate_set.metadata.published_frontier_requirement_satisfied,
        unresolved_ambiguity_preserved=result.candidate_set.metadata.unresolved_ambiguity_preserved,
        confidence_residue_preserved=result.candidate_set.metadata.confidence_residue_preserved,
        candidate_set_consumer_ready=result.gate.candidate_set_consumer_ready,
        suppression_report_consumer_ready=result.gate.suppression_report_consumer_ready,
        identity_merge_consumer_ready=result.gate.identity_merge_consumer_ready,
        restrictions=result.gate.restrictions,
        surfaced_candidate_ids=tuple(item.candidate_id for item in result.candidate_set.surfaced_candidates),
        surfaced_candidate_classes=tuple(
            item.candidate_class.value for item in result.candidate_set.surfaced_candidates
        ),
        suppression_reasons=tuple(
            item.suppression_reason.value for item in result.candidate_set.suppression_report.suppressed_items
        ),
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_c06_first_slice_only=result.scope_marker.c06_first_slice_only,
        scope_c06_1_workspace_handoff_contract=result.scope_marker.c06_1_workspace_handoff_contract,
        scope_no_retention_write_layer=result.scope_marker.no_retention_write_layer,
        scope_no_project_reformation_layer=result.scope_marker.no_project_reformation_layer,
        scope_no_map_wide_rollout_claim=result.scope_marker.no_map_wide_rollout_claim,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_c06_surfacing_consumer_view(
    result_or_view: C06SurfacingResult | C06SurfacingContractView,
) -> C06SurfacingConsumerView:
    view = (
        derive_c06_surfacing_contract_view(result_or_view)
        if isinstance(result_or_view, C06SurfacingResult)
        else result_or_view
    )
    if not isinstance(view, C06SurfacingContractView):
        raise TypeError(
            "derive_c06_surfacing_consumer_view requires C06SurfacingResult/C06SurfacingContractView"
        )
    return C06SurfacingConsumerView(
        status=view.status,
        candidate_count=view.candidate_count,
        commitment_carryover_count=view.commitment_carryover_count,
        repair_obligation_count=view.repair_obligation_count,
        protective_monitor_count=view.protective_monitor_count,
        closure_candidate_count=view.closure_candidate_count,
        ambiguous_candidate_count=view.ambiguous_candidate_count,
        suppressed_item_count=view.suppressed_item_count,
        duplicate_merge_count=view.duplicate_merge_count,
        false_merge_detected=view.false_merge_detected,
        no_continuity_candidates=view.no_continuity_candidates,
        published_frontier_requirement_satisfied=view.published_frontier_requirement_satisfied,
        unresolved_ambiguity_preserved=view.unresolved_ambiguity_preserved,
        confidence_residue_preserved=view.confidence_residue_preserved,
        candidate_set_consumer_ready=view.candidate_set_consumer_ready,
        suppression_report_consumer_ready=view.suppression_report_consumer_ready,
        identity_merge_consumer_ready=view.identity_merge_consumer_ready,
        restrictions=view.restrictions,
        reason="c06 surfacing consumer view",
    )


def require_c06_candidate_set_consumer_ready(
    result_or_view: C06SurfacingResult | C06SurfacingContractView,
) -> C06SurfacingConsumerView:
    view = derive_c06_surfacing_consumer_view(result_or_view)
    if not view.candidate_set_consumer_ready:
        raise PermissionError("c06 candidate-set consumer requires surfaced candidate-set readiness")
    return view


def require_c06_suppression_report_consumer_ready(
    result_or_view: C06SurfacingResult | C06SurfacingContractView,
) -> C06SurfacingConsumerView:
    view = derive_c06_surfacing_consumer_view(result_or_view)
    if not view.suppression_report_consumer_ready:
        raise PermissionError("c06 suppression-report consumer requires explicit suppression report readiness")
    return view


def require_c06_identity_merge_consumer_ready(
    result_or_view: C06SurfacingResult | C06SurfacingContractView,
) -> C06SurfacingConsumerView:
    view = derive_c06_surfacing_consumer_view(result_or_view)
    if not view.identity_merge_consumer_ready:
        raise PermissionError("c06 identity-merge consumer requires false-merge-free surfacing state")
    return view

