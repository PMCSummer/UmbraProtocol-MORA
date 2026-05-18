from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InnerStateCalibrationScenarioSpec:
    scenario_id: str
    description: str
    hidden_condition_id: str
    true_cause_class: str
    true_ambiguity_class: str
    true_confounder_presence: bool
    true_delay_presence: bool
    true_mixed_cause_presence: bool
    ab6_case_id: str


_SCENARIOS: tuple[InnerStateCalibrationScenarioSpec, ...] = (
    InnerStateCalibrationScenarioSpec(
        scenario_id="clear_self_caused_effect",
        description="Self-caused public effect with AP01 request and correlated effect.",
        hidden_condition_id="p12:hidden:self_clear",
        true_cause_class="self_action",
        true_ambiguity_class="low",
        true_confounder_presence=False,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="self_action_correlated_effect",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="world_only_change",
        description="World process causes public change; no AP01 request present.",
        hidden_condition_id="p12:hidden:world_only",
        true_cause_class="world_process",
        true_ambiguity_class="low",
        true_confounder_presence=False,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="world_only_change",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="other_actor_change",
        description="Other actor causes public change.",
        hidden_condition_id="p12:hidden:other_actor",
        true_cause_class="other_actor",
        true_ambiguity_class="low",
        true_confounder_presence=False,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="other_actor_change",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="mixed_cause",
        description="Self and external world contribution jointly affect outcome.",
        hidden_condition_id="p12:hidden:mixed",
        true_cause_class="mixed_cause",
        true_ambiguity_class="high",
        true_confounder_presence=True,
        true_delay_presence=False,
        true_mixed_cause_presence=True,
        ab6_case_id="mixed_self_world_effect",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="delayed_effect",
        description="Effect appears with delay after prior self request.",
        hidden_condition_id="p12:hidden:delayed",
        true_cause_class="delayed_self_effect",
        true_ambiguity_class="high",
        true_confounder_presence=False,
        true_delay_presence=True,
        true_mixed_cause_presence=False,
        ab6_case_id="delayed_self_effect",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="sensor_projection_mismatch",
        description="Public mismatch-like evidence without world-fact confirmation.",
        hidden_condition_id="p12:hidden:mismatch",
        true_cause_class="sensor_or_projection_error",
        true_ambiguity_class="high",
        true_confounder_presence=True,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="sensor_projection_mismatch",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="unknown_cause",
        description="Public evidence insufficient for cause closure.",
        hidden_condition_id="p12:hidden:unknown",
        true_cause_class="unknown_cause",
        true_ambiguity_class="high",
        true_confounder_presence=True,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="unknown_unexplained_effect",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="conflicting_evidence",
        description="Competing evidence supports multiple interpretations.",
        hidden_condition_id="p12:hidden:conflict",
        true_cause_class="mixed_cause",
        true_ambiguity_class="high",
        true_confounder_presence=True,
        true_delay_presence=False,
        true_mixed_cause_presence=True,
        ab6_case_id="mixed_self_world_effect",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="residue_present",
        description="Residual unresolved evidence remains after update/attribution.",
        hidden_condition_id="p12:hidden:residue",
        true_cause_class="unknown_cause",
        true_ambiguity_class="high",
        true_confounder_presence=True,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="unknown_unexplained_effect",
    ),
    InnerStateCalibrationScenarioSpec(
        scenario_id="hidden_eval_only_cause",
        description="True hidden cause unavailable to public subject pipeline.",
        hidden_condition_id="p12:hidden:hidden_eval_only",
        true_cause_class="hidden_eval_only",
        true_ambiguity_class="high",
        true_confounder_presence=False,
        true_delay_presence=False,
        true_mixed_cause_presence=False,
        ab6_case_id="hidden_eval_only_cause",
    ),
)


def list_inner_state_calibration_scenarios() -> tuple[InnerStateCalibrationScenarioSpec, ...]:
    return _SCENARIOS


def inner_state_calibration_scenario_for_id(scenario_id: str) -> InnerStateCalibrationScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown inner-state calibration scenario: {scenario_id}")
