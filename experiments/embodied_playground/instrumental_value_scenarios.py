from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstrumentalValueScenarioSpec:
    scenario_id: str
    description: str
    p15_case_id: str
    ab7_case_id: str
    need_refs: tuple[str, ...]
    resource_refs: tuple[str, ...]
    station_linked: bool
    protected_eval_only: bool = False
    name_only_resource: bool = False


_SCENARIOS: tuple[InstrumentalValueScenarioSpec, ...] = (
    InstrumentalValueScenarioSpec(
        scenario_id="resource_with_need_and_recipe_chain",
        description="Need + recipe candidate + effect chain allows bounded instrumental value.",
        p15_case_id="repeated_consistent_traces_candidate_strengthens",
        ab7_case_id="repeated_trace_candidate_with_ab_support",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="resource_without_need_no_value",
        description="Resource without need should not gain instrumental value.",
        p15_case_id="one_success_trace_provisional_only",
        ab7_case_id="one_success_trace_not_automation",
        need_refs=(),
        resource_refs=("resource:item_a",),
        station_linked=False,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="iron_magic_value_guard",
        description="Name-only useful-sounding resource must not gain value without chain.",
        p15_case_id="visible_station_no_trace_no_recipe",
        ab7_case_id="one_success_trace_not_automation",
        need_refs=(),
        resource_refs=("resource:iron",),
        station_linked=False,
        name_only_resource=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="filter_without_water_problem",
        description="Tool-like resource without linked problem/need/effect chain must stay no-value.",
        p15_case_id="visible_station_no_trace_no_recipe",
        ab7_case_id="one_success_trace_not_automation",
        need_refs=(),
        resource_refs=("resource:filter",),
        station_linked=False,
        name_only_resource=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="resource_with_recipe_candidate_but_missing_effect_chain",
        description="Recipe candidate without effect chain is blocked.",
        p15_case_id="station_success_without_effect_refs_blocked",
        ab7_case_id="p15_candidate_bound_to_ab_frontier",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="resource_with_station_affordance_missing",
        description="Station-linked value requires station affordance refs.",
        p15_case_id="one_success_trace_provisional_only",
        ab7_case_id="station_affordance_missing_blocks_integration",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="confounded_resource_value",
        description="Active confounder weakens or blocks value assignment.",
        p15_case_id="confounded_station_effect",
        ab7_case_id="active_confounder_blocks_recipe_maturity",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="disconfirmed_resource_value",
        description="Disconfirming evidence blocks instrumental value.",
        p15_case_id="disconfirming_trace_blocks_maturity",
        ab7_case_id="disconfirming_effect_blocks_recipe_integration",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="repeated_trace_strengthens_instrumental_value",
        description="Repeated traces strengthen value status but do not imply automation.",
        p15_case_id="repeated_consistent_traces_candidate_strengthens",
        ab7_case_id="repeated_trace_candidate_with_ab_support",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="AB7_blocks_automation_readiness",
        description="AB7 blocked readiness keeps automation blocked while value remains bounded.",
        p15_case_id="one_success_trace_provisional_only",
        ab7_case_id="one_success_trace_not_automation",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="hidden_eval_value_rule_rejected",
        description="Protected evaluator-only value rule does not produce subject value.",
        p15_case_id="hidden_recipe_only_no_candidate",
        ab7_case_id="protected_eval_only_rule_rejected",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
        protected_eval_only=True,
    ),
    InstrumentalValueScenarioSpec(
        scenario_id="value_candidate_does_not_emit_action",
        description="Value candidate generation never emits AP01/ACP01/world actions.",
        p15_case_id="recipe_candidate_does_not_emit_action",
        ab7_case_id="recipe_candidate_does_not_emit_action",
        need_refs=("need:need_x",),
        resource_refs=("resource:item_a",),
        station_linked=True,
    ),
)


def list_instrumental_value_scenarios() -> tuple[InstrumentalValueScenarioSpec, ...]:
    return _SCENARIOS


def instrumental_value_scenario_for_id(scenario_id: str) -> InstrumentalValueScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown instrumental-value scenario: {scenario_id}")
