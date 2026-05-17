from __future__ import annotations

from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig
from experiments.embodied_playground.candidate_provider import ManualCandidateProvider, ManualCandidateSpec
from experiments.embodied_playground.grid_world import GridWorldBackend
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


def test_manual_move_forward_open() -> None:
    backend = GridWorldBackend("open_movement_forward")
    before = backend.observe("subject_a").body_state.location_ref
    provider = ManualCandidateProvider(plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)})

    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=provider,
        backend=backend,
    )

    after = backend.observe("subject_a").body_state.location_ref
    step = run.steps[0]
    assert step.subject_tick_used is True
    assert step.ap01_published_request_count == 1
    assert step.world_submission_attempted is True
    assert step.world_effect_status == "succeeded"
    assert before != after


def test_manual_move_forward_blocked_wall() -> None:
    backend = GridWorldBackend("blocked_movement_wall")
    before = backend.observe("subject_a").body_state.location_ref
    provider = ManualCandidateProvider(plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)})

    run = run_subject_world_bridge(
        scenario_id="blocked_movement_wall",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=provider,
        backend=backend,
    )

    after = backend.observe("subject_a").body_state.location_ref
    step = run.steps[0]
    assert step.ap01_published_request_count == 1
    assert step.world_submission_attempted is True
    assert step.world_effect_status == "blocked"
    assert before == after


def test_manual_pickup_visible_item() -> None:
    backend = GridWorldBackend("visible_item_pickup_available")
    before_inventory = backend.observe("subject_a").inventory_state.item_counts.get("item:water_flask", 0)
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="pickup", target_ref="item:water_flask"),)}
    )

    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=provider,
        backend=backend,
    )

    after_observation = backend.observe("subject_a")
    after_inventory = after_observation.inventory_state.item_counts.get("item:water_flask", 0)
    visible_refs = {obj.object_ref for obj in after_observation.visible_objects}
    step = run.steps[0]
    assert step.world_submission_attempted is True
    assert step.world_effect_status == "succeeded"
    assert after_inventory == before_inventory + 1
    assert "item:water_flask" not in visible_refs


def test_action_space_only_no_execution_without_candidate() -> None:
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=None,
    )
    step = run.steps[0]
    assert step.ap01_candidate_count == 0
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_unsafe_hidden_eval_candidate_rejected() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={
            1: (
                ManualCandidateSpec(
                    action_kind="move_forward",
                    no_hidden_truth_used=False,
                    forbidden_basis_markers=("eval_only:hidden_truth",),
                ),
            )
        }
    )
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.ap01_published_request_count == 0
    assert step.ap01_unsafe_basis_count >= 1
    assert step.world_submission_attempted is False


def test_multiple_requests_rejected() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={
            1: (
                ManualCandidateSpec(action_kind="move_forward"),
                ManualCandidateSpec(action_kind="turn_left"),
            )
        }
    )
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            reject_multiple_published_requests=True,
        ),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.ap01_published_request_count >= 2
    assert step.world_submission_attempted is False
    assert run.rejected_multiple_requests_count >= 1


def test_effect_feedback_next_tick() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
    )
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=2, execute_world_actions=True),
        candidate_provider=provider,
    )

    first = run.steps[0]
    second = run.steps[1]
    assert first.world_effect_id is not None
    assert first.world_submission_attempted is True
    assert second.world_submission_attempted is False
    assert first.world_effect_id in second.observation_previous_effect_refs
