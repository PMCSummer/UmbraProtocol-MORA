from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecipePrecursorScenarioSpec:
    scenario_id: str
    description: str
    p14_case_id: str
    p13_case_id: str
    repeated_traces: int
    no_lived_trace: bool = False
    remove_input_refs: bool = False
    remove_effect_refs: bool = False
    ambiguous_output: bool = False
    expect_disconfirming: bool = False
    expect_delay: bool = False
    expect_active_confounder: bool = False
    protected_eval_only_recipe: bool = False


_SCENARIOS: tuple[RecipePrecursorScenarioSpec, ...] = (
    RecipePrecursorScenarioSpec(
        scenario_id="one_success_trace_provisional_only",
        description="Single lived station effect trace should stay weak/provisional.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="immediate_clear_effect",
        repeated_traces=1,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="repeated_consistent_traces_candidate_strengthens",
        description="Repeated consistent public traces can strengthen candidate without final truth closure.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="confounder_disconfirmed_by_repetition",
        repeated_traces=3,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="hidden_recipe_only_no_candidate",
        description="Protected evaluator-only recipe does not create public candidate without lived basis.",
        p14_case_id="station_protected_eval_only_rule",
        p13_case_id="hidden_recipe_only",
        repeated_traces=0,
        no_lived_trace=True,
        protected_eval_only_recipe=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="visible_station_no_trace_no_recipe",
        description="Visible station without use/effect trace does not create recipe candidate.",
        p14_case_id="station_visible_not_usable",
        p13_case_id="spurious_one_shot_correlation",
        repeated_traces=0,
        no_lived_trace=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="station_success_without_input_refs_blocked",
        description="Effect trace with removed input refs remains blocked for recipe candidate.",
        p14_case_id="station_proximate_with_input",
        p13_case_id="immediate_clear_effect",
        repeated_traces=1,
        remove_input_refs=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="station_success_without_effect_refs_blocked",
        description="Station/input basis without public effect refs remains blocked.",
        p14_case_id="station_proximate_with_input",
        p13_case_id="immediate_clear_effect",
        repeated_traces=1,
        remove_effect_refs=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="confounded_station_effect",
        description="Confounded precursors keep maturity blocked.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="confounded_effect_two_precursors",
        repeated_traces=2,
        expect_active_confounder=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="confounder_disconfirmed_by_repetition",
        description="Confounder weakens under repetition but candidate stays non-mature.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="confounder_disconfirmed_by_repetition",
        repeated_traces=3,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="disconfirming_trace_blocks_maturity",
        description="Disconfirming traces reduce support and block maturity.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="disconfirming_episode",
        repeated_traces=2,
        expect_disconfirming=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="delayed_station_effect",
        description="Delayed station effect keeps timing uncertainty explicit.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="delayed_effect_correct_window",
        repeated_traces=2,
        expect_delay=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="ambiguous_output_effect",
        description="Ambiguous output explanation remains open and non-mature.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="ambiguous_public_evidence",
        repeated_traces=2,
        ambiguous_output=True,
        expect_active_confounder=True,
    ),
    RecipePrecursorScenarioSpec(
        scenario_id="recipe_candidate_does_not_emit_action",
        description="Recipe candidate production must not emit action/publication/world submission.",
        p14_case_id="station_use_effect_feedback",
        p13_case_id="immediate_clear_effect",
        repeated_traces=2,
    ),
)


def list_recipe_precursor_scenarios() -> tuple[RecipePrecursorScenarioSpec, ...]:
    return _SCENARIOS


def recipe_precursor_scenario_for_id(scenario_id: str) -> RecipePrecursorScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown recipe/precursor scenario: {scenario_id}")
