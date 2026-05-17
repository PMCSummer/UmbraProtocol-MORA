from __future__ import annotations

from dataclasses import dataclass

from substrate.ap01_subject_action_publication.models import AP01SubjectActionPublicationResult


@dataclass(frozen=True, slots=True)
class AP01ActionPublicationContractView:
    candidate_count: int
    published_request_count: int
    blocked_count: int
    revalidation_required_count: int
    unsafe_basis_count: int
    execution_boundary_preserved: bool
    must_wait_for_effect: bool
    no_hidden_truth_used: bool
    no_eval_only_used: bool
    no_scenario_label_used: bool
    may_submit_to_world_bridge: bool
    must_not_execute_inside_subject: bool
    must_wait_for_effect_feedback: bool
    must_preserve_request_boundary: bool
    must_preserve_permission_refs: bool
    must_preserve_residue_refs: bool
    must_not_treat_request_as_success: bool
    must_not_treat_request_as_world_change: bool
    must_not_infer_completion_from_request: bool
    scope: str
    scope_rt01_hosted_only: bool
    scope_publication_not_planner: bool
    scope_publication_not_execution: bool
    scope_no_world_mutation_inside_subject: bool
    scope_no_phase_override_authority: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class AP01ActionPublicationConsumerView:
    candidate_count: int
    published_request_count: int
    blocked_count: int
    revalidation_required_count: int
    unsafe_basis_count: int
    may_submit_to_world_bridge: bool
    must_not_execute_inside_subject: bool
    must_wait_for_effect_feedback: bool
    must_preserve_request_boundary: bool
    must_preserve_permission_refs: bool
    must_preserve_residue_refs: bool
    must_not_treat_request_as_success: bool
    must_not_treat_request_as_world_change: bool
    must_not_infer_completion_from_request: bool
    reason: str


def derive_ap01_action_publication_contract_view(
    result: AP01SubjectActionPublicationResult,
) -> AP01ActionPublicationContractView:
    if not isinstance(result, AP01SubjectActionPublicationResult):
        raise TypeError(
            "derive_ap01_action_publication_contract_view requires AP01SubjectActionPublicationResult"
        )
    telemetry = result.telemetry
    scope = result.scope_marker
    may_submit = telemetry.published_request_count > 0 and telemetry.execution_boundary_preserved
    return AP01ActionPublicationContractView(
        candidate_count=telemetry.candidate_count,
        published_request_count=telemetry.published_request_count,
        blocked_count=telemetry.blocked_count,
        revalidation_required_count=telemetry.revalidation_required_count,
        unsafe_basis_count=telemetry.unsafe_basis_count,
        execution_boundary_preserved=telemetry.execution_boundary_preserved,
        must_wait_for_effect=telemetry.must_wait_for_effect,
        no_hidden_truth_used=telemetry.no_hidden_truth_used,
        no_eval_only_used=telemetry.no_eval_only_used,
        no_scenario_label_used=telemetry.no_scenario_label_used,
        may_submit_to_world_bridge=may_submit,
        must_not_execute_inside_subject=True,
        must_wait_for_effect_feedback=True,
        must_preserve_request_boundary=True,
        must_preserve_permission_refs=True,
        must_preserve_residue_refs=True,
        must_not_treat_request_as_success=True,
        must_not_treat_request_as_world_change=True,
        must_not_infer_completion_from_request=True,
        scope=scope.scope,
        scope_rt01_hosted_only=scope.rt01_hosted_only,
        scope_publication_not_planner=scope.publication_not_planner,
        scope_publication_not_execution=scope.publication_not_execution,
        scope_no_world_mutation_inside_subject=scope.no_world_mutation_inside_subject,
        scope_no_phase_override_authority=scope.no_phase_override_authority,
        scope_reason=scope.reason,
        reason=result.reason,
    )


def derive_ap01_action_publication_consumer_view(
    result_or_view: AP01SubjectActionPublicationResult | AP01ActionPublicationContractView,
) -> AP01ActionPublicationConsumerView:
    view = (
        derive_ap01_action_publication_contract_view(result_or_view)
        if isinstance(result_or_view, AP01SubjectActionPublicationResult)
        else result_or_view
    )
    if not isinstance(view, AP01ActionPublicationContractView):
        raise TypeError(
            "derive_ap01_action_publication_consumer_view requires AP01SubjectActionPublicationResult/AP01ActionPublicationContractView"
        )
    return AP01ActionPublicationConsumerView(
        candidate_count=view.candidate_count,
        published_request_count=view.published_request_count,
        blocked_count=view.blocked_count,
        revalidation_required_count=view.revalidation_required_count,
        unsafe_basis_count=view.unsafe_basis_count,
        may_submit_to_world_bridge=view.may_submit_to_world_bridge,
        must_not_execute_inside_subject=view.must_not_execute_inside_subject,
        must_wait_for_effect_feedback=view.must_wait_for_effect_feedback,
        must_preserve_request_boundary=view.must_preserve_request_boundary,
        must_preserve_permission_refs=view.must_preserve_permission_refs,
        must_preserve_residue_refs=view.must_preserve_residue_refs,
        must_not_treat_request_as_success=view.must_not_treat_request_as_success,
        must_not_treat_request_as_world_change=view.must_not_treat_request_as_world_change,
        must_not_infer_completion_from_request=view.must_not_infer_completion_from_request,
        reason="ap01 action publication consumer view",
    )
