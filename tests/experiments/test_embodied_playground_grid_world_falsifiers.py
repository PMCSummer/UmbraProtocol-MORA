from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.falsifiers import (
    action_space_as_permission,
    action_without_ap01_envelope,
    ap01_request_boundary_lost,
    backend_selects_action,
    effect_success_without_correlation,
    eval_truth_leak,
    hidden_map_leak,
    inventory_delta_without_effect,
    movement_through_wall,
    movement_without_effect,
    observation_as_effect,
    pickup_without_proximity,
    pickup_without_capacity,
    public_snapshot_contains_eval_truth,
    recipe_result_in_p2,
    scenario_id_action_selection,
    station_result_without_input,
    station_use_without_visibility_or_proximity,
    station_visible_as_usable,
    drop_without_inventory_item,
    backend_chooses_action,
    invalid_envelope_effect_invariant,
)
from experiments.embodied_playground.grid_world import GridWorldBackend, make_published_action_envelope
from experiments.embodied_playground.models import ActionSpaceFrame, CorrelationStatus, EffectStatus, ObservationFrame, PublicWorldSnapshot


def test_falsifier_movement_through_wall_negative_control() -> None:
    backend = GridWorldBackend("blocked_movement_wall")
    before = backend.observe("subject_a").body_state.location_ref
    envelope = make_published_action_envelope(subject_id="subject_a", action_kind="move_forward", request_ref="ap01_request:move")
    effect = backend.submit_action(envelope)
    after = backend.observe("subject_a").body_state.location_ref

    assert movement_through_wall(
        was_blocked_by_wall=True,
        previous_location_ref=before,
        current_location_ref=after,
        effect=effect,
    ) is False

    bad_effect = replace(effect, effect_status=EffectStatus.SUCCEEDED)
    assert movement_through_wall(
        was_blocked_by_wall=True,
        previous_location_ref=before,
        current_location_ref=after,
        effect=bad_effect,
    ) is True


def test_falsifier_pickup_without_proximity_negative_control() -> None:
    backend = GridWorldBackend("pickup_without_proximity")
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind="pickup",
        target_ref="item:water_flask",
        request_ref="ap01_request:pickup",
    )
    effect = backend.submit_action(envelope)
    assert pickup_without_proximity(pickup_succeeded=(effect.effect_status == EffectStatus.SUCCEEDED), target_reachable=False) is False
    assert pickup_without_proximity(pickup_succeeded=True, target_reachable=False) is True
    assert pickup_without_capacity(pickup_succeeded=False, capacity_available=False) is False
    assert pickup_without_capacity(pickup_succeeded=True, capacity_available=False) is True


def test_falsifier_inventory_delta_without_effect_negative_control() -> None:
    assert inventory_delta_without_effect({"item:water": 0}, {"item:water": 1}, None) is True
    assert inventory_delta_without_effect({"item:water": 0}, {"item:water": 0}, None) is False


def test_falsifier_hidden_map_leak_negative_control() -> None:
    backend = GridWorldBackend("hidden_map_not_visible")
    observation = backend.observe("subject_a")
    snapshot = backend.public_snapshot("subject_a")
    eval_snapshot = backend.eval_snapshot()

    hidden_ref = eval_snapshot.hidden_objects[0]["object_ref"]
    assert hidden_map_leak(observation, snapshot, hidden_ref) is False


def test_falsifier_action_without_ap01_envelope_negative_control() -> None:
    backend = GridWorldBackend("invalid_envelope_rejected")
    effect = backend.submit_action({"action": "move_forward"})  # type: ignore[arg-type]
    assert action_without_ap01_envelope(effect) is False
    bad = replace(effect, effect_status=EffectStatus.SUCCEEDED, correlation_status=CorrelationStatus.CORRELATED_TO_REQUEST)
    assert action_without_ap01_envelope(bad) is True


def test_falsifier_station_result_without_input_negative_control() -> None:
    backend = GridWorldBackend("station_visible_no_input")
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind="use_station",
        target_ref="station:alpha",
        request_ref="ap01_request:station",
    )
    effect = backend.submit_action(envelope)
    assert station_result_without_input(station_output_produced=(effect.effect_status == EffectStatus.SUCCEEDED), station_input_available=False) is False
    assert station_result_without_input(station_output_produced=True, station_input_available=False) is True


def test_falsifier_recipe_result_in_p2_negative_control() -> None:
    backend = GridWorldBackend("station_input_available_no_recipe_execution")
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind="use_station",
        target_ref="station:alpha",
        request_ref="ap01_request:station2",
    )
    effect = backend.submit_action(envelope)
    assert recipe_result_in_p2(effect) is False
    bad = replace(effect, world_delta_public={"crafted": ["item:new"]})
    assert recipe_result_in_p2(bad) is True


def test_falsifier_scenario_id_action_selection_negative_control() -> None:
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind="inspect",
        request_ref="ap01_request:inspect",
    )
    assert scenario_id_action_selection(envelope) is False
    bad = replace(envelope, args={"scenario_id_action_basis": "scenario_id:blocked_movement_wall"})
    assert scenario_id_action_selection(bad) is True


def test_remaining_p2_falsifiers_structural_checks() -> None:
    backend = GridWorldBackend("empty_room_presence")
    observation = backend.observe("subject_a")
    snapshot = backend.public_snapshot("subject_a")
    envelope = make_published_action_envelope(subject_id="subject_a", action_kind="wait", request_ref="ap01_request:wait")
    effect = backend.submit_action(envelope)

    assert action_space_as_permission(observation.action_space) is False
    assert movement_without_effect("grid:1,1", "grid:1,2", None) is True
    assert effect_success_without_correlation(replace(effect, effect_status=EffectStatus.SUCCEEDED, request_ref=None, envelope_ref=None)) is True
    assert observation_as_effect(observation) is False
    assert public_snapshot_contains_eval_truth(snapshot) is False
    assert ap01_request_boundary_lost(envelope) is False
    assert station_visible_as_usable(station_visible=True, use_station_succeeded=True, station_reachable=False, input_available=False) is True
    assert station_use_without_visibility_or_proximity(use_station_succeeded=False, station_visible=False, station_reachable=False) is False
    assert station_use_without_visibility_or_proximity(use_station_succeeded=True, station_visible=False, station_reachable=True) is True
    assert drop_without_inventory_item(drop_succeeded=False, had_item_before=False) is False
    assert drop_without_inventory_item(drop_succeeded=True, had_item_before=False) is True
    assert eval_truth_leak(observation, snapshot) is False
    assert backend_selects_action(backend) is False
    assert backend_chooses_action(backend) is False


def test_p2_falsifier_backend_chooses_action_detects_choose_method() -> None:
    class BadBackend:
        def reset(self, seed: int | None, scenario_config: object | None = None) -> object:
            return {}

        def choose_action(self) -> str:
            return "move_forward"

        def observe(self, subject_id: str) -> ObservationFrame:
            return GridWorldBackend("empty_room_presence").observe(subject_id)

        def action_space(self, subject_id: str) -> ActionSpaceFrame:
            return GridWorldBackend("empty_room_presence").action_space(subject_id)

        def submit_action(self, envelope) -> object:
            return GridWorldBackend("empty_room_presence").submit_action(envelope)

        def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot:
            return GridWorldBackend("empty_room_presence").public_snapshot(subject_id)

    assert backend_chooses_action(BadBackend()) is True


def test_p2_falsifier_backend_chooses_action_detects_action_return_from_observe() -> None:
    class BadBackend:
        def reset(self, seed: int | None, scenario_config: object | None = None) -> object:
            return {}

        def observe(self, subject_id: str):
            return make_published_action_envelope(subject_id=subject_id, action_kind="wait", request_ref="ap01_request:bad")

        def action_space(self, subject_id: str) -> ActionSpaceFrame:
            return GridWorldBackend("empty_room_presence").action_space(subject_id)

        def submit_action(self, envelope) -> object:
            return GridWorldBackend("empty_room_presence").submit_action(envelope)

        def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot:
            return GridWorldBackend("empty_room_presence").public_snapshot(subject_id)

    assert backend_chooses_action(BadBackend()) is True


def test_p2_falsifier_backend_chooses_action_detects_raw_action_submit_signature() -> None:
    class BadBackend:
        def reset(self, seed: int | None, scenario_config: object | None = None) -> object:
            return {}

        def observe(self, subject_id: str) -> ObservationFrame:
            return GridWorldBackend("empty_room_presence").observe(subject_id)

        def action_space(self, subject_id: str) -> ActionSpaceFrame:
            return GridWorldBackend("empty_room_presence").action_space(subject_id)

        def submit_action(self, action_kind: str):
            return action_kind

        def public_snapshot(self, subject_id: str) -> PublicWorldSnapshot:
            return GridWorldBackend("empty_room_presence").public_snapshot(subject_id)

    assert backend_chooses_action(BadBackend()) is True


def test_invalid_envelope_returns_invalid_correlation_and_zero_deltas() -> None:
    backend = GridWorldBackend("invalid_envelope_rejected")
    invalid_inputs = [
        "move_forward",
        {"action_kind": "move_forward"},
        None,
        object(),
    ]
    for invalid in invalid_inputs:
        effect = backend.submit_action(invalid)  # type: ignore[arg-type]
        assert invalid_envelope_effect_invariant(effect) is False


def test_invalid_envelope_does_not_mutate_body_inventory_or_world() -> None:
    backend = GridWorldBackend("visible_item_pickup_available")
    before = backend.observe("subject_a")
    before_refs = tuple(sorted(obj.object_ref for obj in before.visible_objects))

    _ = backend.submit_action("pickup")  # type: ignore[arg-type]

    after = backend.observe("subject_a")
    after_refs = tuple(sorted(obj.object_ref for obj in after.visible_objects))

    assert before.body_state.location_ref == after.body_state.location_ref
    assert before.body_state.orientation == after.body_state.orientation
    assert before.inventory_state.item_counts == after.inventory_state.item_counts
    assert before_refs == after_refs


def test_p2_falsifier_invalid_envelope_with_delta_fails() -> None:
    backend = GridWorldBackend("invalid_envelope_rejected")
    effect = backend.submit_action({"bad": "input"})  # type: ignore[arg-type]
    bad_effect = replace(effect, body_delta={"location_to": "grid:9,9"})
    assert invalid_envelope_effect_invariant(effect) is False
    assert invalid_envelope_effect_invariant(bad_effect) is True
