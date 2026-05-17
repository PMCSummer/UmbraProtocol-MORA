from __future__ import annotations

from experiments.embodied_playground.grid_world import GridWorldBackend, make_published_action_envelope
from experiments.embodied_playground.models import CorrelationStatus, EffectStatus


def _run(backend: GridWorldBackend, action_kind: str, target_ref: str | None = None):
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind=action_kind,
        target_ref=target_ref,
        request_ref=f"ap01_request:{action_kind}",
    )
    return backend.submit_action(envelope)


def test_blocked_movement_wall() -> None:
    backend = GridWorldBackend("blocked_movement_wall")
    before = backend.observe("subject_a").body_state.location_ref
    effect = _run(backend, "move_forward")
    after = backend.observe("subject_a").body_state.location_ref
    assert effect.effect_status == EffectStatus.BLOCKED
    assert before == after


def test_open_movement_forward() -> None:
    backend = GridWorldBackend("open_movement_forward")
    before = backend.observe("subject_a").body_state.location_ref
    effect = _run(backend, "move_forward")
    after = backend.observe("subject_a").body_state.location_ref
    assert effect.effect_status == EffectStatus.SUCCEEDED
    assert before != after


def test_turn_left_and_turn_right_update_orientation() -> None:
    backend = GridWorldBackend("empty_room_presence")
    start_orientation = str(backend.observe("subject_a").body_state.orientation.value)
    left_effect = _run(backend, "turn_left")
    after_left = str(backend.observe("subject_a").body_state.orientation.value)
    right_effect = _run(backend, "turn_right")
    after_right = str(backend.observe("subject_a").body_state.orientation.value)

    assert left_effect.effect_status == EffectStatus.SUCCEEDED
    assert right_effect.effect_status == EffectStatus.SUCCEEDED
    assert start_orientation != after_left
    assert after_right == start_orientation


def test_pickup_visible_item() -> None:
    backend = GridWorldBackend("visible_item_pickup_available")
    effect = _run(backend, "pickup", target_ref="item:water_flask")
    observation = backend.observe("subject_a")
    assert effect.effect_status == EffectStatus.SUCCEEDED
    assert observation.inventory_state.item_counts.get("item:water_flask", 0) == 1


def test_pickup_without_proximity() -> None:
    backend = GridWorldBackend("pickup_without_proximity")
    effect = _run(backend, "pickup", target_ref="item:water_flask")
    assert effect.effect_status == EffectStatus.BLOCKED
    assert effect.blocked_reason == "target_not_reachable"


def test_inventory_capacity_block() -> None:
    backend = GridWorldBackend("inventory_capacity_block")
    effect = _run(backend, "pickup", target_ref="item:water_flask")
    assert effect.effect_status == EffectStatus.BLOCKED
    assert effect.blocked_reason == "inventory_full"


def test_drop_item_available() -> None:
    backend = GridWorldBackend("drop_item_available")
    effect = _run(backend, "drop", target_ref="item:water_flask")
    observation = backend.observe("subject_a")
    assert effect.effect_status == EffectStatus.SUCCEEDED
    assert observation.inventory_state.item_counts.get("item:water_flask", 0) == 0


def test_station_visible_no_input() -> None:
    backend = GridWorldBackend("station_visible_no_input")
    effect = _run(backend, "use_station", target_ref="station:alpha")
    assert effect.effect_status == EffectStatus.BLOCKED
    assert effect.blocked_reason == "station_input_missing"


def test_station_input_available_no_recipe_execution() -> None:
    backend = GridWorldBackend("station_input_available_no_recipe_execution")
    effect = _run(backend, "use_station", target_ref="station:alpha")
    assert effect.effect_status in {EffectStatus.PARTIAL, EffectStatus.NO_EFFECT, EffectStatus.SUCCEEDED}
    assert "recipe_execution_not_available_in_p2" in str(effect.observed_result_refs)


def test_water_source_visible_interact_and_inspect() -> None:
    backend = GridWorldBackend("water_source_visible")
    inspect = _run(backend, "inspect", target_ref="water:source:1")
    interact = _run(backend, "interact", target_ref="water:source:1")
    assert inspect.effect_status == EffectStatus.SUCCEEDED
    assert interact.effect_status == EffectStatus.NO_EFFECT


def test_invalid_envelope_rejected() -> None:
    backend = GridWorldBackend("invalid_envelope_rejected")
    effect = backend.submit_action({"action_kind": "move_forward"})  # type: ignore[arg-type]
    assert effect.effect_status == EffectStatus.BLOCKED
    assert effect.correlation_status == CorrelationStatus.INVALID
