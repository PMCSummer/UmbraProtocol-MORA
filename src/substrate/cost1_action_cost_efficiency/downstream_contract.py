from __future__ import annotations

from dataclasses import dataclass

from .models import CostValidationResult


@dataclass(frozen=True, slots=True)
class COST1DownstreamContract:
    comparison_ref: str | None
    allowed_downstream_uses: tuple[str, ...]
    forbidden_downstream_uses: tuple[str, ...]
    compatible_with_micro1: bool
    compatible_with_ksurf1_hints: bool
    compatible_with_p16_p17_inputs: bool
    no_action_authority: bool
    no_publication_authority: bool
    no_execution_authority: bool


def derive_cost1_downstream_contract(result: CostValidationResult) -> COST1DownstreamContract:
    return COST1DownstreamContract(
        comparison_ref=result.comparison.comparison_id if result.comparison is not None else None,
        allowed_downstream_uses=(
            "dimension_explicit_candidate_comparison_support",
            "micro1_candidate_economy_annotation_without_permission",
            "provider_declared_vs_observed_cost_mismatch_residue_tracking",
            "throughput_support_status_passthrough_for_later_phases",
        ),
        forbidden_downstream_uses=(
            "action_or_candidate_or_goal_selection_from_cost1",
            "ap01_request_emission_or_world_submission_from_cost1",
            "provider_declared_cost_as_observed_truth",
            "single_scalar_hidden_cost_optimization",
            "recipe_or_skill_or_automation_maturity_claim_from_efficiency",
            "planner_optimizer_pathfinder_factory_scheduler_substitution",
        ),
        compatible_with_micro1=True,
        compatible_with_ksurf1_hints=True,
        compatible_with_p16_p17_inputs=True,
        no_action_authority=True,
        no_publication_authority=True,
        no_execution_authority=True,
    )
