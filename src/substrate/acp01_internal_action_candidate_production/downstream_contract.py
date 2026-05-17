from __future__ import annotations

from dataclasses import dataclass

from substrate.acp01_internal_action_candidate_production.models import (
    ACP01CandidateProductionResult,
)


@dataclass(frozen=True, slots=True)
class ACP01CandidateProductionContractView:
    decision_count: int
    proposal_count: int
    proposed_count: int
    blocked_count: int
    revalidation_required_count: int
    unsafe_basis_count: int
    insufficient_basis_count: int
    no_candidate_count: int
    has_candidate_set_for_ap01: bool
    candidate_production_only: bool
    must_not_publish_request: bool
    must_not_execute_world_action: bool
    must_not_submit_world_action: bool
    private_eval_excluded: bool
    scenario_label_excluded: bool
    scope: str
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class ACP01CandidateProductionConsumerView:
    proposed_count: int
    blocked_count: int
    revalidation_required_count: int
    unsafe_basis_count: int
    has_candidate_set_for_ap01: bool
    must_not_publish_request: bool
    must_not_execute_world_action: bool
    must_not_submit_world_action: bool
    reason: str


def derive_acp01_candidate_production_contract_view(
    result: ACP01CandidateProductionResult,
) -> ACP01CandidateProductionContractView:
    if not isinstance(result, ACP01CandidateProductionResult):
        raise TypeError(
            "derive_acp01_candidate_production_contract_view requires ACP01CandidateProductionResult"
        )
    telemetry = result.telemetry
    scope = result.scope_marker
    return ACP01CandidateProductionContractView(
        decision_count=telemetry.decision_count,
        proposal_count=telemetry.proposal_count,
        proposed_count=telemetry.proposed_count,
        blocked_count=telemetry.blocked_count,
        revalidation_required_count=telemetry.revalidation_required_count,
        unsafe_basis_count=telemetry.unsafe_basis_count,
        insufficient_basis_count=telemetry.insufficient_basis_count,
        no_candidate_count=telemetry.no_candidate_count,
        has_candidate_set_for_ap01=result.candidate_set_for_ap01 is not None,
        candidate_production_only=scope.candidate_production_only,
        must_not_publish_request=True,
        must_not_execute_world_action=True,
        must_not_submit_world_action=True,
        private_eval_excluded=telemetry.private_eval_excluded,
        scenario_label_excluded=telemetry.scenario_label_excluded,
        scope=scope.scope,
        scope_reason=scope.reason,
        reason=result.reason,
    )


def derive_acp01_candidate_production_consumer_view(
    result_or_view: ACP01CandidateProductionResult | ACP01CandidateProductionContractView,
) -> ACP01CandidateProductionConsumerView:
    view = (
        derive_acp01_candidate_production_contract_view(result_or_view)
        if isinstance(result_or_view, ACP01CandidateProductionResult)
        else result_or_view
    )
    if not isinstance(view, ACP01CandidateProductionContractView):
        raise TypeError(
            "derive_acp01_candidate_production_consumer_view requires ACP01 result/contract view"
        )
    return ACP01CandidateProductionConsumerView(
        proposed_count=view.proposed_count,
        blocked_count=view.blocked_count,
        revalidation_required_count=view.revalidation_required_count,
        unsafe_basis_count=view.unsafe_basis_count,
        has_candidate_set_for_ap01=view.has_candidate_set_for_ap01,
        must_not_publish_request=view.must_not_publish_request,
        must_not_execute_world_action=view.must_not_execute_world_action,
        must_not_submit_world_action=view.must_not_submit_world_action,
        reason="acp01 candidate production consumer view",
    )
