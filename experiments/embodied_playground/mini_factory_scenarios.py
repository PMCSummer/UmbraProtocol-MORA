from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MiniFactoryScenarioSpec:
    scenario_id: str
    description: str
    p16_case_id: str
    p15_case_id: str
    ab7_case_id: str
    has_first_input: bool = True
    plate_step_mode: str = "succeed"  # succeed|failed|blocked|missing_effect
    filter_step_mode: str = "succeed"  # succeed|failed|blocked|missing_effect|attempt_without_input
    water_step_mode: str = "succeed"  # succeed|failed|blocked|missing_effect|external_effect
    partial_after_plate: bool = False
    protected_eval_only_rule: bool = False
    active_confounder: bool = False
    disconfirming_intermediate: bool = False


_SCENARIOS: tuple[MiniFactoryScenarioSpec, ...] = (
    MiniFactoryScenarioSpec(
        scenario_id="full_chain_verified",
        description="ore->plate->filter->clean_water with full verified intermediate chain.",
        p16_case_id="resource_with_need_and_recipe_chain",
        p15_case_id="repeated_consistent_traces_candidate_strengthens",
        ab7_case_id="repeated_trace_candidate_with_ab_support",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="missing_first_input_blocks_chain",
        description="Missing first input blocks chain and propagates residue downstream.",
        p16_case_id="resource_without_need_no_value",
        p15_case_id="visible_station_no_trace_no_recipe",
        ab7_case_id="one_success_trace_not_automation",
        has_first_input=False,
        plate_step_mode="blocked",
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="failed_plate_step_blocks_filter",
        description="Plate step fails and blocks downstream filter/water.",
        p16_case_id="resource_with_recipe_candidate_but_missing_effect_chain",
        p15_case_id="station_success_without_effect_refs_blocked",
        ab7_case_id="disconfirming_effect_blocks_recipe_integration",
        plate_step_mode="failed",
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="filter_step_without_plate_rejected",
        description="Filter step attempted without verified plate input must be blocked.",
        p16_case_id="resource_with_recipe_candidate_but_missing_effect_chain",
        p15_case_id="station_success_without_effect_refs_blocked",
        ab7_case_id="p15_candidate_bound_to_ab_frontier",
        plate_step_mode="missing_effect",
        filter_step_mode="attempt_without_input",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="clean_water_without_filter_chain_rejected",
        description="Clean-water-like effect without verified filter chain is rejected for completion.",
        p16_case_id="resource_with_recipe_candidate_but_missing_effect_chain",
        p15_case_id="station_success_without_effect_refs_blocked",
        ab7_case_id="p15_candidate_bound_to_ab_frontier",
        plate_step_mode="succeed",
        filter_step_mode="missing_effect",
        water_step_mode="external_effect",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="partial_chain_no_completion",
        description="Partial chain (ore->plate) without downstream verification stays incomplete.",
        p16_case_id="repeated_trace_strengthens_instrumental_value",
        p15_case_id="one_success_trace_provisional_only",
        ab7_case_id="one_success_trace_not_automation",
        partial_after_plate=True,
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="blocked_station_preserves_residue",
        description="Blocked station creates residue and downstream blocked steps.",
        p16_case_id="resource_with_station_affordance_missing",
        p15_case_id="one_success_trace_provisional_only",
        ab7_case_id="station_affordance_missing_blocks_integration",
        plate_step_mode="blocked",
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="confounded_intermediate_blocks_completion",
        description="Confounded intermediate verification blocks clean completion.",
        p16_case_id="confounded_resource_value",
        p15_case_id="confounded_station_effect",
        ab7_case_id="active_confounder_blocks_recipe_maturity",
        active_confounder=True,
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="disconfirming_intermediate_blocks_completion",
        description="Disconfirming intermediate blocks completion.",
        p16_case_id="disconfirmed_resource_value",
        p15_case_id="disconfirming_trace_blocks_maturity",
        ab7_case_id="disconfirming_effect_blocks_recipe_integration",
        disconfirming_intermediate=True,
        plate_step_mode="failed",
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="evaluator_only_chain_rule_rejected",
        description="Protected evaluator-only rule cannot produce chain completion.",
        p16_case_id="hidden_eval_value_rule_rejected",
        p15_case_id="hidden_recipe_only_no_candidate",
        ab7_case_id="protected_eval_only_rule_rejected",
        protected_eval_only_rule=True,
        plate_step_mode="blocked",
        filter_step_mode="blocked",
        water_step_mode="blocked",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="chain_candidate_does_not_become_mature_automation",
        description="Even valid chain candidate never becomes mature automation in P17.",
        p16_case_id="AB7_blocks_automation_readiness",
        p15_case_id="one_success_trace_provisional_only",
        ab7_case_id="one_success_trace_not_automation",
        plate_step_mode="succeed",
        filter_step_mode="succeed",
        water_step_mode="succeed",
    ),
    MiniFactoryScenarioSpec(
        scenario_id="chain_effect_feedback_preserved",
        description="Per-step effect refs are preserved as next-step verified inputs.",
        p16_case_id="resource_with_need_and_recipe_chain",
        p15_case_id="repeated_consistent_traces_candidate_strengthens",
        ab7_case_id="repeated_trace_candidate_with_ab_support",
        plate_step_mode="succeed",
        filter_step_mode="succeed",
        water_step_mode="succeed",
    ),
)


def list_mini_factory_scenarios() -> tuple[MiniFactoryScenarioSpec, ...]:
    return _SCENARIOS


def mini_factory_scenario_for_id(scenario_id: str) -> MiniFactoryScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown mini-factory scenario: {scenario_id}")
