from __future__ import annotations

from experiments.embodied_playground.grid_world import GridWorldBackend
from experiments.embodied_playground.scenarios import list_grid_world_scenarios


def test_grid_world_constructs_and_observes_all_required_scenarios() -> None:
    for scenario_id in list_grid_world_scenarios():
        backend = GridWorldBackend(scenario_id=scenario_id)
        observation = backend.observe("subject_a")
        action_space = backend.action_space("subject_a")
        snapshot = backend.public_snapshot("subject_a")
        eval_snapshot = backend.eval_snapshot()

        assert observation.__class__.__name__ == "ObservationFrame"
        assert action_space.__class__.__name__ == "ActionSpaceFrame"
        assert snapshot.__class__.__name__ == "PublicWorldSnapshot"
        assert eval_snapshot.__class__.__name__ == "EvalOnlyWorldTruth"
        assert observation.hidden_truth_excluded is True
        assert observation.eval_only_excluded is True
        assert snapshot.hidden_truth_excluded is True
        assert eval_snapshot.must_never_enter_subject_visible is True


def test_public_snapshot_excludes_eval_fields() -> None:
    backend = GridWorldBackend(scenario_id="hidden_map_not_visible")
    snapshot = backend.public_snapshot("subject_a")
    text = str(snapshot).lower()
    assert "hidden_objects" not in text
    assert "expected_outcome" not in text
    assert "scenario_labels" not in text


def test_grid_world_backend_exposes_no_action_selection_methods() -> None:
    backend = GridWorldBackend(scenario_id="empty_room_presence")
    method_names = {name.lower() for name in dir(backend)}
    forbidden = {"choose_action", "select_action", "decide_action", "plan_action", "scenario_to_action"}
    assert not (method_names & forbidden)
