from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BodyActionScenarioSpec:
    scenario_id: str
    world_scenario_id: str
    ticks: int
    drive_kinds: tuple[str, ...]
    expected_behavior: str


def list_body_action_scenarios() -> tuple[BodyActionScenarioSpec, ...]:
    return (
        BodyActionScenarioSpec(
            scenario_id="internal_turn_left_orientation_change",
            world_scenario_id="empty_room_presence",
            ticks=2,
            drive_kinds=("turn_left_intent",),
            expected_behavior="orientation changes via AP01-gated world effect",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_turn_right_orientation_change",
            world_scenario_id="empty_room_presence",
            ticks=2,
            drive_kinds=("turn_right_intent",),
            expected_behavior="orientation changes via AP01-gated world effect",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_move_forward_open",
            world_scenario_id="open_movement_forward",
            ticks=2,
            drive_kinds=("move_forward_intent",),
            expected_behavior="body location delta after AP01-gated movement effect",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_move_forward_blocked_wall",
            world_scenario_id="blocked_movement_wall",
            ticks=2,
            drive_kinds=("move_forward_intent",),
            expected_behavior="blocked movement effect, no location delta",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_pickup_visible_reachable_item",
            world_scenario_id="visible_item_pickup_available",
            ticks=2,
            drive_kinds=("water_need",),
            expected_behavior="pickup through full basis path with inventory delta",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_pickup_no_drive_no_publish",
            world_scenario_id="visible_item_pickup_available",
            ticks=1,
            drive_kinds=(),
            expected_behavior="no pickup candidate/publication without drive basis",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_pickup_no_visible_object_no_publish",
            world_scenario_id="empty_room_presence",
            ticks=1,
            drive_kinds=("water_need",),
            expected_behavior="no pickup candidate/publication without visible object basis",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_pickup_no_proximity_no_publish",
            world_scenario_id="pickup_without_proximity",
            ticks=1,
            drive_kinds=("water_need",),
            expected_behavior="no pickup publication without proximity basis",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_pickup_no_capacity_no_publish",
            world_scenario_id="inventory_capacity_block",
            ticks=1,
            drive_kinds=("water_need",),
            expected_behavior="no pickup publication when inventory capacity is blocked",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_drop_inventory_item",
            world_scenario_id="drop_item_available",
            ticks=2,
            drive_kinds=("drop_water_flask",),
            expected_behavior="drop candidate leads to inventory and world deltas",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_drop_without_inventory_no_publish",
            world_scenario_id="empty_room_presence",
            ticks=1,
            drive_kinds=("drop_water_flask",),
            expected_behavior="no drop candidate/publication without inventory item",
        ),
        BodyActionScenarioSpec(
            scenario_id="internal_body_action_effect_feedback_next_tick",
            world_scenario_id="open_movement_forward",
            ticks=2,
            drive_kinds=("move_forward_intent",),
            expected_behavior="effect ref appears in next observation payload",
        ),
    )


def body_action_scenario_for_id(scenario_id: str) -> BodyActionScenarioSpec:
    for spec in list_body_action_scenarios():
        if spec.scenario_id == scenario_id:
            return spec
    raise ValueError(f"Unknown P10 body-action scenario id: {scenario_id}")

