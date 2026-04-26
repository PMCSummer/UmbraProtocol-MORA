from substrate.p04_interpersonal_counterfactual_policy_simulation.models import (
    P04SimulationResult,
)


def p04_interpersonal_counterfactual_policy_simulation_snapshot(
    result: P04SimulationResult,
) -> dict[str, object]:
    if not isinstance(result, P04SimulationResult):
        raise TypeError(
            "p04_interpersonal_counterfactual_policy_simulation_snapshot requires P04SimulationResult"
        )
    matrix = result.simulation_set.comparison_matrix
    metadata = result.simulation_set.metadata
    return {
        "simulation_set": {
            "simulation_id": result.simulation_set.simulation_id,
            "branch_count": len(result.simulation_set.branch_records),
            "excluded_policy_count": len(result.simulation_set.excluded_policies),
            "unstable_region_count": len(result.simulation_set.unstable_regions),
            "contrast_count": len(matrix.contrasts),
            "dominance_state": matrix.dominance_state.value,
            "comparison_readiness": matrix.comparison_readiness.value,
            "no_clear_dominance": matrix.no_clear_dominance,
            "reason": result.simulation_set.reason,
        },
        "metadata": {
            "evaluated_candidate_count": metadata.evaluated_candidate_count,
            "selectable_candidate_count": metadata.selectable_candidate_count,
            "excluded_policy_count": metadata.excluded_policy_count,
            "belief_conditioned_rollout": metadata.belief_conditioned_rollout,
            "incomplete_information_support": metadata.incomplete_information_support,
            "false_belief_case_support": metadata.false_belief_case_support,
            "misread_case_support": metadata.misread_case_support,
            "knowledge_uncertainty_support": metadata.knowledge_uncertainty_support,
            "source_lineage": metadata.source_lineage,
            "reason": metadata.reason,
        },
        "gate": {
            "branch_record_consumer_ready": result.gate.branch_record_consumer_ready,
            "comparison_consumer_ready": result.gate.comparison_consumer_ready,
            "excluded_policy_consumer_ready": result.gate.excluded_policy_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "p04_frontier_slice_only": result.scope_marker.p04_frontier_slice_only,
            "simulation_not_selector": result.scope_marker.simulation_not_selector,
            "no_hidden_policy_selection_authority": (
                result.scope_marker.no_hidden_policy_selection_authority
            ),
            "no_policy_mutation_authority": result.scope_marker.no_policy_mutation_authority,
            "no_map_wide_prediction_claim": result.scope_marker.no_map_wide_prediction_claim,
            "no_full_social_world_prediction_claim": (
                result.scope_marker.no_full_social_world_prediction_claim
            ),
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "branch_count": result.telemetry.branch_count,
            "selectable_branch_count": result.telemetry.selectable_branch_count,
            "excluded_policy_count": result.telemetry.excluded_policy_count,
            "unstable_region_count": result.telemetry.unstable_region_count,
            "no_clear_dominance_count": result.telemetry.no_clear_dominance_count,
            "belief_conditioned_rollout": result.telemetry.belief_conditioned_rollout,
            "incomplete_information_support": result.telemetry.incomplete_information_support,
            "false_belief_case_support": result.telemetry.false_belief_case_support,
            "misread_case_support": result.telemetry.misread_case_support,
            "knowledge_uncertainty_support": result.telemetry.knowledge_uncertainty_support,
            "guardrail_exclusion_count": result.telemetry.guardrail_exclusion_count,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
