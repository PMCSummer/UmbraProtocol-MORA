from __future__ import annotations

from experiments.embodied_playground.body_action_proof import run_body_action_proof_case


def _single_effect_status(run) -> str | None:
    for step in run.step_summaries:
        if step.world_submission_count > 0:
            return step.effect_status
    return None


def test_turn_left_through_internal_path() -> None:
    run = run_body_action_proof_case(scenario_id="internal_turn_left_orientation_change", strict_internal_mode=True)
    assert run.subject_tick_used and run.acp01_used
    assert not run.manual_provider_used
    assert run.ap01_published_count >= 1
    assert run.world_submission_count >= 1
    body_deltas = [step.body_delta for step in run.step_summaries if step.body_delta]
    assert any("orientation_to" in delta for delta in body_deltas)


def test_turn_right_through_internal_path() -> None:
    run = run_body_action_proof_case(scenario_id="internal_turn_right_orientation_change", strict_internal_mode=True)
    assert run.ap01_published_count >= 1
    assert run.world_submission_count >= 1
    body_deltas = [step.body_delta for step in run.step_summaries if step.body_delta]
    assert any("orientation_to" in delta for delta in body_deltas)


def test_move_forward_open_through_internal_path() -> None:
    run = run_body_action_proof_case(scenario_id="internal_move_forward_open", strict_internal_mode=True)
    assert run.ap01_published_count >= 1
    assert run.world_submission_count >= 1
    body_deltas = [step.body_delta for step in run.step_summaries if step.body_delta]
    assert any("location_to" in delta for delta in body_deltas)


def test_move_forward_blocked_wall_returns_blocked_effect() -> None:
    run = run_body_action_proof_case(scenario_id="internal_move_forward_blocked_wall", strict_internal_mode=True)
    assert run.ap01_published_count >= 1
    assert run.world_submission_count >= 1
    assert _single_effect_status(run) == "blocked"
    submitted_steps = [step for step in run.step_summaries if step.world_submission_count > 0]
    assert submitted_steps
    assert all(not step.body_delta for step in submitted_steps)


def test_pickup_visible_reachable_item_through_internal_path() -> None:
    run = run_body_action_proof_case(scenario_id="internal_pickup_visible_reachable_item", strict_internal_mode=True)
    assert run.ap01_published_count >= 1
    assert run.world_submission_count >= 1
    inventory_deltas = [step.inventory_delta for step in run.step_summaries if step.inventory_delta]
    assert any("added" in delta for delta in inventory_deltas)


def test_pickup_no_drive_no_publication() -> None:
    run = run_body_action_proof_case(scenario_id="internal_pickup_no_drive_no_publish", strict_internal_mode=True)
    assert run.ap01_published_count == 0
    assert run.world_submission_count == 0


def test_pickup_no_visible_object_no_publication() -> None:
    run = run_body_action_proof_case(scenario_id="internal_pickup_no_visible_object_no_publish", strict_internal_mode=True)
    assert run.ap01_published_count == 0
    assert run.world_submission_count == 0


def test_pickup_no_proximity_no_publication() -> None:
    run = run_body_action_proof_case(scenario_id="internal_pickup_no_proximity_no_publish", strict_internal_mode=True)
    assert run.ap01_published_count == 0
    assert run.world_submission_count == 0


def test_pickup_no_capacity_no_publication() -> None:
    run = run_body_action_proof_case(scenario_id="internal_pickup_no_capacity_no_publish", strict_internal_mode=True)
    assert run.ap01_published_count == 0
    assert run.world_submission_count == 0


def test_drop_inventory_item_through_internal_path() -> None:
    run = run_body_action_proof_case(scenario_id="internal_drop_inventory_item", strict_internal_mode=True)
    assert run.ap01_published_count >= 1
    assert run.world_submission_count >= 1
    inventory_deltas = [step.inventory_delta for step in run.step_summaries if step.inventory_delta]
    world_deltas = [step.world_delta_public for step in run.step_summaries if step.world_delta_public]
    assert any("removed" in delta for delta in inventory_deltas)
    assert any("dropped_items" in delta for delta in world_deltas)


def test_drop_without_inventory_no_publication() -> None:
    run = run_body_action_proof_case(scenario_id="internal_drop_without_inventory_no_publish", strict_internal_mode=True)
    assert run.ap01_published_count == 0
    assert run.world_submission_count == 0


def test_effect_feedback_appears_in_next_observation() -> None:
    run = run_body_action_proof_case(scenario_id="internal_body_action_effect_feedback_next_tick", strict_internal_mode=True)
    assert run.world_submission_count >= 1
    assert any(step.previous_effect_refs_in_next_tick for step in run.step_summaries)


def test_no_manual_provider_used_in_internal_mode_body_action_scenarios() -> None:
    scenario_ids = (
        "internal_move_forward_open",
        "internal_pickup_visible_reachable_item",
        "internal_drop_inventory_item",
    )
    for scenario_id in scenario_ids:
        run = run_body_action_proof_case(scenario_id=scenario_id, strict_internal_mode=True)
        assert not run.manual_provider_used
        assert all(not step.manual_provider_used for step in run.step_summaries)


def test_p10_repeated_move_publish_has_fresh_request_refs() -> None:
    run = run_body_action_proof_case(scenario_id="internal_move_forward_open", ticks=2, strict_internal_mode=True)
    submitted = [step for step in run.step_summaries if step.world_submission_count > 0]
    assert len(submitted) == 2
    refs = [step.ap01_request_ref for step in submitted]
    assert all(refs)
    assert len(set(refs)) == len(refs)


def test_p10_repeated_turn_publish_has_fresh_request_refs() -> None:
    run = run_body_action_proof_case(scenario_id="internal_turn_left_orientation_change", ticks=2, strict_internal_mode=True)
    submitted = [step for step in run.step_summaries if step.world_submission_count > 0]
    assert len(submitted) == 2
    refs = [step.ap01_request_ref for step in submitted]
    assert all(refs)
    assert len(set(refs)) == len(refs)


def test_p10_repeated_body_action_is_reported_as_basis_persistent_not_stale() -> None:
    run = run_body_action_proof_case(scenario_id="internal_move_forward_open", ticks=2, strict_internal_mode=True)
    assert run.repeated_body_action_policy == "basis_persistent_repeat_allowed"
    assert run.repeated_publish_expected is True
    assert run.stale_candidate_detected is False


def test_p10_repeated_body_action_effects_are_individually_correlated() -> None:
    run = run_body_action_proof_case(scenario_id="internal_turn_right_orientation_change", ticks=2, strict_internal_mode=True)
    submitted = [step for step in run.step_summaries if step.world_submission_count > 0]
    assert submitted
    assert all(step.effect_correlated_to_request for step in submitted)
    assert all(step.envelope_ref for step in submitted)
    assert all(step.world_effect_id for step in submitted)


def test_p10_single_tick_move_has_single_publish() -> None:
    run = run_body_action_proof_case(scenario_id="internal_move_forward_open", ticks=1, strict_internal_mode=True)
    assert run.ap01_published_count == 1
    assert run.world_submission_count == 1


def test_p10_no_lexical_water_collect_shortcut_for_pickup() -> None:
    run = run_body_action_proof_case(
        scenario_id="internal_pickup_visible_reachable_item",
        ticks=1,
        drive_kinds=("water_collect_phrase_only",),
        strict_internal_mode=True,
    )
    assert run.ap01_published_count == 0
    assert run.world_submission_count == 0
