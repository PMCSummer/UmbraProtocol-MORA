from __future__ import annotations

from experiments.embodied_playground.baselines import (
    ActionSpaceGreedyBaseline,
    BaselineFairnessClass,
    DirectBridgeBypassBaseline,
    DriveOnlyBaseline,
    HiddenOracleBaseline,
    RandomActionBaseline,
    VisibleObjectHeuristicBaseline,
)
from experiments.embodied_playground.grid_world import GridWorldBackend


def _frames(scenario_id: str):
    backend = GridWorldBackend(scenario_id)
    return backend.observe("subject_a"), backend.action_space("subject_a")


def test_baseline_protocol_objects() -> None:
    assert RandomActionBaseline().controller_kind == "random_action_baseline"
    assert ActionSpaceGreedyBaseline().controller_kind == "action_space_greedy_baseline"
    assert VisibleObjectHeuristicBaseline().controller_kind == "visible_object_heuristic_baseline"
    assert DriveOnlyBaseline().controller_kind == "drive_only_baseline"


def test_random_baseline_deterministic_seed() -> None:
    obs, action_space = _frames("open_movement_forward")
    b1 = RandomActionBaseline(seed=13)
    b2 = RandomActionBaseline(seed=13)
    d1 = b1.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=(),
        previous_effects=(),
        scenario_id="open_movement_forward",
    )
    d2 = b2.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=(),
        previous_effects=(),
        scenario_id="open_movement_forward",
    )
    assert d1.action_kind == d2.action_kind
    assert d1.target_ref == d2.target_ref


def test_action_space_greedy_acts_from_action_surfaces() -> None:
    obs, action_space = _frames("open_movement_forward")
    baseline = ActionSpaceGreedyBaseline()
    decision = baseline.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=(),
        previous_effects=(),
        scenario_id="action_space_only_no_candidate",
    )
    assert decision.used_action_space is True
    assert decision.action_kind is not None


def test_visible_object_heuristic_acts_from_visible_object() -> None:
    obs, action_space = _frames("visible_item_pickup_available")
    baseline = VisibleObjectHeuristicBaseline()
    decision = baseline.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=(),
        previous_effects=(),
        scenario_id="visible_flask_no_drive",
    )
    assert decision.action_kind in {"pickup", "inspect"}
    assert decision.used_public_observation is True
    assert "visible_object_shortcut" in decision.reason_codes


def test_drive_only_acts_from_drive_without_object() -> None:
    obs, action_space = _frames("empty_room_presence")
    baseline = DriveOnlyBaseline()
    decision = baseline.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=("water_need",),
        previous_effects=(),
        scenario_id="water_need_no_visible_water",
    )
    assert decision.action_kind == "pickup"
    assert decision.used_drive_basis is True
    assert decision.used_public_observation is False


def test_hidden_oracle_marked_diagnostic_unfair() -> None:
    baseline = HiddenOracleBaseline()
    assert baseline.fairness_class == BaselineFairnessClass.DIAGNOSTIC_UNFAIR
    obs, action_space = _frames("hidden_map_not_visible")
    decision = baseline.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=("water_need",),
        previous_effects=(),
        scenario_id="hidden_map_not_visible",
        eval_only={"hidden_objects": [{"object_ref": "object:hidden:1"}]},
    )
    assert decision.used_hidden_or_eval is True


def test_direct_bridge_marked_boundary_violation_baseline() -> None:
    baseline = DirectBridgeBypassBaseline()
    assert baseline.fairness_class == BaselineFairnessClass.BOUNDARY_VIOLATION_BASELINE
    obs, action_space = _frames("open_movement_forward")
    decision = baseline.choose_action(
        tick_index=1,
        observation=obs,
        action_space=action_space,
        drive_basis=(),
        previous_effects=(),
        scenario_id="open_movement_forward",
    )
    assert decision.expected_boundary_violation is True
    assert "ap01_bypassed" in decision.boundary_notes


def test_fair_baselines_do_not_get_eval_private_data() -> None:
    obs, action_space = _frames("hidden_map_not_visible")
    for baseline in (RandomActionBaseline(), ActionSpaceGreedyBaseline(), VisibleObjectHeuristicBaseline(), DriveOnlyBaseline()):
        decision = baseline.choose_action(
            tick_index=1,
            observation=obs,
            action_space=action_space,
            drive_basis=("water_need",),
            previous_effects=(),
            scenario_id="hidden_map_not_visible",
            eval_only=None,
        )
        assert decision.used_hidden_or_eval is False

