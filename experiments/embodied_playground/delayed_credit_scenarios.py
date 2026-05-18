from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DelayedCreditScenarioSpec:
    scenario_id: str
    description: str
    ab5_case_id: str
    ab6_case_id: str
    p12_case_id: str
    delayed_expected: bool
    confounder_expected: bool
    disconfirming_expected: bool
    repeated_expected: bool
    hidden_eval_expected: bool


_SCENARIOS: tuple[DelayedCreditScenarioSpec, ...] = (
    DelayedCreditScenarioSpec(
        scenario_id="immediate_clear_effect",
        description="Immediate correlated effect after precursor/action.",
        ab5_case_id="correlated_effect_support_increase",
        ab6_case_id="self_action_correlated_effect",
        p12_case_id="clear_self_caused_effect",
        delayed_expected=False,
        confounder_expected=False,
        disconfirming_expected=False,
        repeated_expected=False,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="delayed_effect_correct_window",
        description="Delayed effect appears in plausible delay window.",
        ab5_case_id="ambiguous_effect_no_closure",
        ab6_case_id="delayed_self_effect",
        p12_case_id="delayed_effect",
        delayed_expected=True,
        confounder_expected=False,
        disconfirming_expected=False,
        repeated_expected=False,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="delayed_effect_wrong_window",
        description="Effect appears outside admissible delay window.",
        ab5_case_id="uncorrelated_effect_weak_or_blocked_update",
        ab6_case_id="unknown_unexplained_effect",
        p12_case_id="delayed_effect",
        delayed_expected=True,
        confounder_expected=False,
        disconfirming_expected=True,
        repeated_expected=False,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="confounded_effect_two_precursors",
        description="Two precursor candidates overlap before effect.",
        ab5_case_id="ambiguous_effect_no_closure",
        ab6_case_id="mixed_self_world_effect",
        p12_case_id="mixed_cause",
        delayed_expected=False,
        confounder_expected=True,
        disconfirming_expected=False,
        repeated_expected=False,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="confounder_disconfirmed_by_repetition",
        description="Repeated traces weaken confounder without maturing schema.",
        ab5_case_id="correlated_effect_support_increase",
        ab6_case_id="mixed_self_world_effect",
        p12_case_id="mixed_cause",
        delayed_expected=False,
        confounder_expected=True,
        disconfirming_expected=True,
        repeated_expected=True,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="spurious_one_shot_correlation",
        description="Single coincidence remains weak and provisional.",
        ab5_case_id="uncorrelated_effect_weak_or_blocked_update",
        ab6_case_id="unknown_unexplained_effect",
        p12_case_id="unknown_cause",
        delayed_expected=False,
        confounder_expected=True,
        disconfirming_expected=False,
        repeated_expected=False,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="disconfirming_episode",
        description="Previously supported precursor occurs without effect.",
        ab5_case_id="disconfirming_effect_support_decrease",
        ab6_case_id="blocked_action_no_success",
        p12_case_id="residue_present",
        delayed_expected=False,
        confounder_expected=False,
        disconfirming_expected=True,
        repeated_expected=True,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="hidden_recipe_only",
        description="Evaluator hidden recipe unavailable to subject learning.",
        ab5_case_id="hidden_eval_effect_rejected",
        ab6_case_id="hidden_eval_only_cause",
        p12_case_id="hidden_eval_only_cause",
        delayed_expected=False,
        confounder_expected=False,
        disconfirming_expected=False,
        repeated_expected=False,
        hidden_eval_expected=True,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="ambiguous_public_evidence",
        description="Public evidence supports multiple competing links.",
        ab5_case_id="ambiguous_effect_no_closure",
        ab6_case_id="sensor_projection_mismatch",
        p12_case_id="conflicting_evidence",
        delayed_expected=False,
        confounder_expected=True,
        disconfirming_expected=False,
        repeated_expected=False,
        hidden_eval_expected=False,
    ),
    DelayedCreditScenarioSpec(
        scenario_id="delayed_and_confounded_mixed",
        description="Delayed effect and confounder overlap remain unresolved/provisional.",
        ab5_case_id="ambiguous_effect_no_closure",
        ab6_case_id="mixed_self_world_effect",
        p12_case_id="conflicting_evidence",
        delayed_expected=True,
        confounder_expected=True,
        disconfirming_expected=False,
        repeated_expected=True,
        hidden_eval_expected=False,
    ),
)


def list_delayed_credit_scenarios() -> tuple[DelayedCreditScenarioSpec, ...]:
    return _SCENARIOS


def delayed_credit_scenario_for_id(scenario_id: str) -> DelayedCreditScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown delayed-credit scenario: {scenario_id}")
