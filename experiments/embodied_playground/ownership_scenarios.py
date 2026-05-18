from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OwnershipScenarioSpec:
    scenario_id: str
    perturbation_kind: str
    description: str
    expected_attribution: str
    world_scenario_id: str | None = None
    ticks: int = 2


_SCENARIOS: tuple[OwnershipScenarioSpec, ...] = (
    OwnershipScenarioSpec(
        scenario_id="self_caused_move_effect",
        perturbation_kind="self_action_effect",
        description="self move request with correlated body delta effect",
        expected_attribution="self_action_supported",
        world_scenario_id="internal_move_forward_open",
        ticks=2,
    ),
    OwnershipScenarioSpec(
        scenario_id="self_caused_pickup_effect",
        perturbation_kind="self_action_effect",
        description="self pickup request with correlated inventory/world delta effect",
        expected_attribution="self_action_supported",
        world_scenario_id="internal_pickup_visible_reachable_item",
        ticks=2,
    ),
    OwnershipScenarioSpec(
        scenario_id="world_only_object_change",
        perturbation_kind="external_world_change",
        description="public object change with no AP01 request",
        expected_attribution="world_or_unknown_not_self",
    ),
    OwnershipScenarioSpec(
        scenario_id="other_actor_object_change",
        perturbation_kind="other_actor_change",
        description="public other-actor perturbation changes object state",
        expected_attribution="other_actor_not_self",
    ),
    OwnershipScenarioSpec(
        scenario_id="mixed_self_and_world_effect",
        perturbation_kind="mixed_effect",
        description="self request and external perturbation jointly shape outcome",
        expected_attribution="mixed_preserved",
        world_scenario_id="internal_move_forward_open",
        ticks=2,
    ),
    OwnershipScenarioSpec(
        scenario_id="delayed_self_effect",
        perturbation_kind="delayed_effect",
        description="effect appears later and maps to prior self request chain",
        expected_attribution="delayed_self_not_immediate_overclaim",
        world_scenario_id="internal_move_forward_open",
        ticks=2,
    ),
    OwnershipScenarioSpec(
        scenario_id="unknown_unexplained_effect",
        perturbation_kind="unknown_effect",
        description="unexpected public effect without sufficient self/world/other basis",
        expected_attribution="unknown_preserved",
    ),
    OwnershipScenarioSpec(
        scenario_id="sensor_or_projection_mismatch",
        perturbation_kind="projection_mismatch",
        description="mismatch-like signal without lawful world-change confirmation",
        expected_attribution="projection_mismatch_not_world_fact",
    ),
    OwnershipScenarioSpec(
        scenario_id="blocked_self_action_no_world_delta",
        perturbation_kind="blocked_self_action",
        description="self request blocked; no successful body/world delta",
        expected_attribution="self_attempt_blocked_not_success",
        world_scenario_id="internal_move_forward_blocked_wall",
        ticks=2,
    ),
    OwnershipScenarioSpec(
        scenario_id="hidden_eval_only_cause",
        perturbation_kind="hidden_eval_only",
        description="cause only in hidden/eval channel",
        expected_attribution="blocked_or_unknown_no_hidden_truth_use",
    ),
)


def list_ownership_scenarios() -> tuple[OwnershipScenarioSpec, ...]:
    return _SCENARIOS


def ownership_scenario_for_id(scenario_id: str) -> OwnershipScenarioSpec:
    for item in _SCENARIOS:
        if item.scenario_id == scenario_id:
            return item
    raise ValueError(f"Unknown ownership scenario: {scenario_id}")
