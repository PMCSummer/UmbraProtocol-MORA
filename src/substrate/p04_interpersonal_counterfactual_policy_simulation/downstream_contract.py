from dataclasses import dataclass

from substrate.p04_interpersonal_counterfactual_policy_simulation.models import (
    P04SimulationResult,
)


@dataclass(frozen=True, slots=True)
class P04SimulationContractView:
    branch_count: int
    selectable_branch_count: int
    excluded_policy_count: int
    unstable_region_count: int
    no_clear_dominance_count: int
    belief_conditioned_rollout: bool
    incomplete_information_support: bool
    false_belief_case_support: bool
    misread_case_support: bool
    knowledge_uncertainty_support: bool
    guardrail_exclusion_count: int
    branch_record_consumer_ready: bool
    comparison_consumer_ready: bool
    excluded_policy_consumer_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    dominance_state: str
    comparison_readiness: str
    scope: str
    scope_rt01_hosted_only: bool
    scope_p04_frontier_slice_only: bool
    scope_simulation_not_selector: bool
    scope_no_hidden_policy_selection_authority: bool
    scope_no_policy_mutation_authority: bool
    scope_no_map_wide_prediction_claim: bool
    scope_no_full_social_world_prediction_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class P04SimulationConsumerView:
    branch_count: int
    selectable_branch_count: int
    excluded_policy_count: int
    unstable_region_count: int
    no_clear_dominance_count: int
    belief_conditioned_rollout: bool
    incomplete_information_support: bool
    false_belief_case_support: bool
    misread_case_support: bool
    knowledge_uncertainty_support: bool
    guardrail_exclusion_count: int
    branch_record_consumer_ready: bool
    comparison_consumer_ready: bool
    excluded_policy_consumer_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    dominance_state: str
    comparison_readiness: str
    reason: str


def derive_p04_simulation_contract_view(
    result: P04SimulationResult,
) -> P04SimulationContractView:
    if not isinstance(result, P04SimulationResult):
        raise TypeError("derive_p04_simulation_contract_view requires P04SimulationResult")
    telemetry = result.telemetry
    matrix = result.simulation_set.comparison_matrix
    return P04SimulationContractView(
        branch_count=telemetry.branch_count,
        selectable_branch_count=telemetry.selectable_branch_count,
        excluded_policy_count=telemetry.excluded_policy_count,
        unstable_region_count=telemetry.unstable_region_count,
        no_clear_dominance_count=telemetry.no_clear_dominance_count,
        belief_conditioned_rollout=telemetry.belief_conditioned_rollout,
        incomplete_information_support=telemetry.incomplete_information_support,
        false_belief_case_support=telemetry.false_belief_case_support,
        misread_case_support=telemetry.misread_case_support,
        knowledge_uncertainty_support=telemetry.knowledge_uncertainty_support,
        guardrail_exclusion_count=telemetry.guardrail_exclusion_count,
        branch_record_consumer_ready=result.gate.branch_record_consumer_ready,
        comparison_consumer_ready=result.gate.comparison_consumer_ready,
        excluded_policy_consumer_ready=result.gate.excluded_policy_consumer_ready,
        downstream_consumer_ready=telemetry.downstream_consumer_ready,
        restrictions=result.gate.restrictions,
        dominance_state=matrix.dominance_state.value,
        comparison_readiness=matrix.comparison_readiness.value,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_p04_frontier_slice_only=result.scope_marker.p04_frontier_slice_only,
        scope_simulation_not_selector=result.scope_marker.simulation_not_selector,
        scope_no_hidden_policy_selection_authority=(
            result.scope_marker.no_hidden_policy_selection_authority
        ),
        scope_no_policy_mutation_authority=result.scope_marker.no_policy_mutation_authority,
        scope_no_map_wide_prediction_claim=result.scope_marker.no_map_wide_prediction_claim,
        scope_no_full_social_world_prediction_claim=(
            result.scope_marker.no_full_social_world_prediction_claim
        ),
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_p04_simulation_consumer_view(
    result_or_view: P04SimulationResult | P04SimulationContractView,
) -> P04SimulationConsumerView:
    view = (
        derive_p04_simulation_contract_view(result_or_view)
        if isinstance(result_or_view, P04SimulationResult)
        else result_or_view
    )
    if not isinstance(view, P04SimulationContractView):
        raise TypeError(
            "derive_p04_simulation_consumer_view requires P04SimulationResult/P04SimulationContractView"
        )
    return P04SimulationConsumerView(
        branch_count=view.branch_count,
        selectable_branch_count=view.selectable_branch_count,
        excluded_policy_count=view.excluded_policy_count,
        unstable_region_count=view.unstable_region_count,
        no_clear_dominance_count=view.no_clear_dominance_count,
        belief_conditioned_rollout=view.belief_conditioned_rollout,
        incomplete_information_support=view.incomplete_information_support,
        false_belief_case_support=view.false_belief_case_support,
        misread_case_support=view.misread_case_support,
        knowledge_uncertainty_support=view.knowledge_uncertainty_support,
        guardrail_exclusion_count=view.guardrail_exclusion_count,
        branch_record_consumer_ready=view.branch_record_consumer_ready,
        comparison_consumer_ready=view.comparison_consumer_ready,
        excluded_policy_consumer_ready=view.excluded_policy_consumer_ready,
        downstream_consumer_ready=view.downstream_consumer_ready,
        restrictions=view.restrictions,
        dominance_state=view.dominance_state,
        comparison_readiness=view.comparison_readiness,
        reason="p04 simulation consumer view",
    )


def require_p04_branch_record_consumer(
    result_or_view: P04SimulationResult | P04SimulationContractView,
) -> P04SimulationConsumerView:
    view = derive_p04_simulation_consumer_view(result_or_view)
    if not view.branch_record_consumer_ready:
        raise PermissionError("p04 branch-record consumer requires explicit branch records")
    return view


def require_p04_comparison_consumer(
    result_or_view: P04SimulationResult | P04SimulationContractView,
) -> P04SimulationConsumerView:
    view = derive_p04_simulation_consumer_view(result_or_view)
    if not view.comparison_consumer_ready:
        raise PermissionError("p04 comparison consumer requires explicit comparison matrix")
    return view


def require_p04_excluded_policy_consumer(
    result_or_view: P04SimulationResult | P04SimulationContractView,
) -> P04SimulationConsumerView:
    view = derive_p04_simulation_consumer_view(result_or_view)
    if not view.excluded_policy_consumer_ready:
        raise PermissionError("p04 excluded-policy consumer requires explicit exclusion records")
    return view
