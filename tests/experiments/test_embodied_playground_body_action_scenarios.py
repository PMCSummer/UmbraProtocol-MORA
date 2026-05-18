from __future__ import annotations

from experiments.embodied_playground.body_action_scenarios import (
    body_action_scenario_for_id,
    list_body_action_scenarios,
)


def test_p10_required_scenarios_exist() -> None:
    ids = {item.scenario_id for item in list_body_action_scenarios()}
    required = {
        "internal_turn_left_orientation_change",
        "internal_turn_right_orientation_change",
        "internal_move_forward_open",
        "internal_move_forward_blocked_wall",
        "internal_pickup_visible_reachable_item",
        "internal_pickup_no_drive_no_publish",
        "internal_pickup_no_visible_object_no_publish",
        "internal_pickup_no_proximity_no_publish",
        "internal_pickup_no_capacity_no_publish",
        "internal_drop_inventory_item",
        "internal_drop_without_inventory_no_publish",
        "internal_body_action_effect_feedback_next_tick",
    }
    assert required.issubset(ids)


def test_p10_scenario_ids_not_used_as_action_basis() -> None:
    for spec in list_body_action_scenarios():
        lowered = " ".join(spec.drive_kinds).lower()
        assert "scenario_id" not in lowered
        assert "scenario:" not in lowered
        assert "test_case" not in lowered


def test_p10_hidden_eval_scenario_maps_to_public_world_surface() -> None:
    spec = body_action_scenario_for_id("internal_pickup_no_visible_object_no_publish")
    assert spec.world_scenario_id == "empty_room_presence"


def test_p10_drop_and_movement_scenarios_have_public_drive_basis_only() -> None:
    move = body_action_scenario_for_id("internal_move_forward_open")
    drop = body_action_scenario_for_id("internal_drop_inventory_item")
    assert move.drive_kinds == ("move_forward_intent",)
    assert drop.drive_kinds == ("drop_water_flask",)

