from __future__ import annotations

from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig
from experiments.embodied_playground.candidate_provider import ManualCandidateProvider, ManualCandidateSpec
from experiments.embodied_playground.grid_world import GridWorldBackend
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


def test_internal_no_drive_visible_item_no_candidate() -> None:
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=(),
        ),
    )
    step = run.steps[0]
    assert step.subject_tick_used is True
    assert step.acp01_proposed_count == 0
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_internal_drive_without_visible_object_no_candidate() -> None:
    run = run_subject_world_bridge(
        scenario_id="empty_room_presence",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.acp01_proposed_count == 0
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_internal_pickup_visible_reachable_item() -> None:
    backend = GridWorldBackend("visible_item_pickup_available")
    before = backend.observe("subject_a").inventory_state.item_counts.get("item:water_flask", 0)
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=2,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
        backend=backend,
    )
    after_obs = backend.observe("subject_a")
    after = after_obs.inventory_state.item_counts.get("item:water_flask", 0)
    first = run.steps[0]
    assert first.acp01_proposed_count >= 1
    assert first.ap01_published_request_count == 1
    assert first.world_submission_attempted is True
    assert first.world_effect_status == "succeeded"
    assert after == before + 1
    assert first.world_effect_id in run.steps[1].observation_previous_effect_refs


def test_internal_pickup_blocked_by_capacity() -> None:
    run = run_subject_world_bridge(
        scenario_id="inventory_capacity_block",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.acp01_proposed_count == 0
    assert step.acp01_blocked_count >= 1
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_internal_object_too_far_no_pickup() -> None:
    run = run_subject_world_bridge(
        scenario_id="pickup_without_proximity",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_internal_uncertain_object_inspect_candidate() -> None:
    backend = GridWorldBackend("pickup_without_proximity")
    backend._state.items["item:water_flask"].observable_properties["confidence"] = 0.2  # type: ignore[attr-defined]
    run = run_subject_world_bridge(
        scenario_id="pickup_without_proximity",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("resolve_uncertainty",),
        ),
        backend=backend,
    )
    step = run.steps[0]
    assert step.ap01_published_request_count == 1
    assert step.world_submission_attempted is True
    assert step.world_effect_status == "succeeded"


def test_internal_action_space_only_no_candidate() -> None:
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=(),
        ),
    )
    step = run.steps[0]
    assert step.ap01_candidate_count == 0
    assert step.world_submission_attempted is False


def test_internal_previous_blocked_effect_revalidation() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
    )
    run = run_subject_world_bridge(
        scenario_id="blocked_movement_wall",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=2,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            allow_manual_override_in_internal_mode=True,
            internal_drive_kinds=("water_need",),
        ),
        candidate_provider=provider,
    )
    first, second = run.steps
    assert first.world_effect_status == "blocked"
    assert second.acp01_revalidation_required_count >= 1
    assert second.world_submission_attempted is False


def test_internal_private_eval_object_no_candidate() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    payload = str(step.subject_tick_surface_payload).lower()
    assert "object:hidden:1" not in payload


def test_internal_scenario_label_no_candidate() -> None:
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("scenario_id:pickup_bias",),
        ),
    )
    step = run.steps[0]
    assert step.acp01_unsafe_basis_count >= 1
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_manual_provider_not_used_in_internal_mode() -> None:
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
        candidate_provider=None,
    )
    step = run.steps[0]
    assert step.internal_candidate_producer_used is True
    assert step.manual_candidate_input is False
    assert step.candidate_source == "acp01_internal"


def test_internal_mode_rejects_manual_provider_by_default() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
    )
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=(),
        ),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.manual_candidate_input is False
    assert step.manual_override_used is False
    assert step.internal_candidate_mode_boundary_relaxed is False
    assert step.ap01_candidate_count == 0
    assert step.world_submission_attempted is False


def test_internal_mode_candidate_source_remains_acp01_internal() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
    )
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.manual_candidate_input is False
    assert step.candidate_source == "acp01_internal"
    assert step.ap01_published_request_count == 1


def test_internal_mode_manual_candidate_input_false_when_acp01_used() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="pickup", target_ref="item:water_flask"),)}
    )
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.manual_candidate_input is False
    assert step.manual_override_used is False
    assert step.internal_candidate_mode_boundary_relaxed is False
    assert step.candidate_source == "acp01_internal"


def test_internal_mode_does_not_submit_manual_candidate_when_internal_enabled() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
    )
    run = run_subject_world_bridge(
        scenario_id="blocked_movement_wall",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=(),
        ),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.manual_candidate_input is False
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False


def test_internal_private_eval_object_no_candidate_has_zero_acp01_proposals() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.acp01_proposed_count == 0
    assert step.acp01_unsafe_basis_count >= 0


def test_internal_private_eval_object_no_candidate_has_zero_ap01_publications() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.ap01_published_request_count == 0


def test_internal_private_eval_object_no_candidate_does_not_submit_world_action() -> None:
    backend = GridWorldBackend("hidden_map_not_visible")
    before = backend.observe("subject_a")
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
        backend=backend,
    )
    after = backend.observe("subject_a")
    step = run.steps[0]
    assert step.world_submission_attempted is False
    assert step.world_effect_id is None
    assert before.body_state.location_ref == after.body_state.location_ref
    assert before.inventory_state.item_counts == after.inventory_state.item_counts
    assert before.tick_index == after.tick_index


def test_internal_private_eval_object_no_candidate_never_targets_private_object() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=("water_need",),
        ),
    )
    step = run.steps[0]
    assert step.envelope_payload is None
    if step.subject_tick_surface_payload:
        payload = str(step.subject_tick_surface_payload).lower()
        assert "object:hidden:1" not in payload
