from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.body_action_falsifiers import (
    acp01_executes_body_action,
    action_space_alone_body_action,
    body_action_bypasses_ap01,
    body_delta_without_effect,
    drive_alone_pickup,
    effect_as_completion_oracle,
    internal_drop_without_inventory_basis,
    internal_move_without_body_basis,
    internal_pickup_without_basis,
    internal_turn_without_body_basis,
    inventory_delta_without_effect,
    manual_provider_used_in_internal_body_action,
    movement_through_wall_as_success,
    p10_report_overclaims,
    pickup_hidden_eval_object,
    pickup_without_capacity_basis,
    pickup_without_proximity_basis,
    request_as_body_effect,
    scenario_label_body_action_selection,
    visible_object_alone_pickup,
    world_object_delta_without_effect,
)
from experiments.embodied_playground.body_action_proof import run_body_action_proof_case


def _run_pickup():
    return run_body_action_proof_case(scenario_id="internal_pickup_visible_reachable_item", strict_internal_mode=True)


def _run_move():
    return run_body_action_proof_case(scenario_id="internal_move_forward_open", strict_internal_mode=True)


def test_manual_provider_used_in_internal_body_action_negative_control() -> None:
    run = _run_move()
    bad = replace(run, manual_provider_used=True)
    assert manual_provider_used_in_internal_body_action(bad)


def test_internal_pickup_without_basis_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    bad_step = replace(step, envelope_payload={"action_kind": "pickup", "evidence_refs": ()})
    bad_run = replace(run, bridge_run=replace(run.bridge_run, steps=(bad_step,) + run.bridge_run.steps[1:]))
    assert internal_pickup_without_basis(bad_run)


def test_internal_move_without_body_basis_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    payload = dict(step.subject_tick_surface_payload)
    payload["body"] = {"body_ref": "", "location_ref": ""}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, subject_tick_surface_payload=payload),) + run.bridge_run.steps[1:]))
    assert internal_move_without_body_basis(bad)


def test_internal_turn_without_body_basis_negative_control() -> None:
    run = run_body_action_proof_case(scenario_id="internal_turn_left_orientation_change", strict_internal_mode=True)
    step = run.bridge_run.steps[0]
    payload = dict(step.subject_tick_surface_payload)
    payload["body"] = {"body_ref": "", "orientation": ""}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, subject_tick_surface_payload=payload),) + run.bridge_run.steps[1:]))
    assert internal_turn_without_body_basis(bad)


def test_internal_drop_without_inventory_basis_negative_control() -> None:
    run = run_body_action_proof_case(scenario_id="internal_drop_inventory_item", strict_internal_mode=True)
    step = run.bridge_run.steps[0]
    payload = dict(step.subject_tick_surface_payload)
    payload["inventory"] = {"item_counts": {}}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, subject_tick_surface_payload=payload),) + run.bridge_run.steps[1:]))
    assert internal_drop_without_inventory_basis(bad)


def test_body_delta_without_effect_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    payload = dict(step.world_effect_payload or {})
    payload["body_delta"] = {"location_to": "grid:9:9"}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, world_effect_id=None, world_effect_payload=payload),) + run.bridge_run.steps[1:]))
    assert body_delta_without_effect(bad)


def test_inventory_delta_without_effect_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    payload = dict(step.world_effect_payload or {})
    payload["inventory_delta"] = {"added": {"item:x": 1}}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, world_effect_id=None, world_effect_payload=payload),) + run.bridge_run.steps[1:]))
    assert inventory_delta_without_effect(bad)


def test_world_object_delta_without_effect_negative_control() -> None:
    run = run_body_action_proof_case(scenario_id="internal_drop_inventory_item", strict_internal_mode=True)
    step = run.bridge_run.steps[0]
    payload = dict(step.world_effect_payload or {})
    payload["world_delta_public"] = {"dropped_items": ["item:x"]}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, world_effect_id=None, world_effect_payload=payload),) + run.bridge_run.steps[1:]))
    assert world_object_delta_without_effect(bad)


def test_movement_through_wall_as_success_negative_control() -> None:
    run = run_body_action_proof_case(scenario_id="internal_move_forward_blocked_wall", strict_internal_mode=True)
    step = run.bridge_run.steps[0]
    payload = dict(step.world_effect_payload or {})
    payload["body_delta"] = {"location_to": "grid:3:3"}
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, world_effect_status="blocked", world_effect_payload=payload),) + run.bridge_run.steps[1:]))
    assert movement_through_wall_as_success(bad)


def test_pickup_without_proximity_basis_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["evidence_refs"] = tuple(ref for ref in env.get("evidence_refs", ()) if "capability:proximity:" not in str(ref))
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:]))
    assert pickup_without_proximity_basis(bad)


def test_pickup_without_capacity_basis_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["evidence_refs"] = tuple(ref for ref in env.get("evidence_refs", ()) if "capability:inventory_capacity" not in str(ref))
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:]))
    assert pickup_without_capacity_basis(bad)


def test_pickup_hidden_eval_object_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["target_ref"] = "object:hidden:1"
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:]))
    assert pickup_hidden_eval_object(bad)


def test_visible_object_alone_pickup_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["evidence_refs"] = tuple(ref for ref in env.get("evidence_refs", ()) if not str(ref).startswith("drive:"))
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:]))
    assert visible_object_alone_pickup(bad)


def test_drive_alone_pickup_negative_control() -> None:
    run = _run_pickup()
    step = run.bridge_run.steps[0]
    payload = dict(step.subject_tick_surface_payload)
    payload["visible_objects"] = ()
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, subject_tick_surface_payload=payload),) + run.bridge_run.steps[1:]))
    assert drive_alone_pickup(bad)


def test_action_space_alone_body_action_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    payload = dict(step.subject_tick_surface_payload)
    payload["visible_objects"] = ()
    env = dict(step.envelope_payload or {})
    env["evidence_refs"] = tuple(ref for ref in env.get("evidence_refs", ()) if not str(ref).startswith("drive:"))
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, subject_tick_surface_payload=payload, envelope_payload=env),) + run.bridge_run.steps[1:]))
    assert action_space_alone_body_action(bad)


def test_request_as_body_effect_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["inventory_delta"] = {"added": {"item:x": 1}}
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(replace(step, world_submission_attempted=False, envelope_payload=env),) + run.bridge_run.steps[1:],
        ),
    )
    assert request_as_body_effect(bad)


def test_effect_as_completion_oracle_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["completion_claim"] = True
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:]))
    assert effect_as_completion_oracle(bad)


def test_scenario_label_body_action_selection_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["target_ref"] = "scenario:force_action"
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:],
        ),
    )
    assert scenario_label_body_action_selection(bad)


def test_body_action_bypasses_ap01_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, world_submission_attempted=True, ap01_published_request_count=0),) + run.bridge_run.steps[1:]))
    assert body_action_bypasses_ap01(bad)


def test_acp01_executes_body_action_negative_control() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    bad = replace(run, bridge_run=replace(run.bridge_run, steps=(replace(step, world_submission_attempted=True, candidate_source="none"),) + run.bridge_run.steps[1:]))
    assert acp01_executes_body_action(bad)


def test_p10_report_overclaims_negative_control() -> None:
    assert p10_report_overclaims("This proves planning and consciousness.")


def test_p10_falsifier_scenario_label_body_action_selection_structural() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["args"] = {"selector": "select_action_by_scenario"}
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:],
        ),
    )
    assert scenario_label_body_action_selection(bad)


def test_p10_falsifier_ignores_scenario_id_metadata() -> None:
    run = _run_move()
    bad = replace(run, scenario_id="scenario_to_action:metadata_only")
    assert not scenario_label_body_action_selection(bad)


def test_p10_falsifier_report_overclaim_structural() -> None:
    assert p10_report_overclaims("MORA demonstrates planning and motor intelligence.")
    assert not p10_report_overclaims("No planning and no consciousness are claimed.")


def test_p10_falsifier_request_as_body_effect_structural() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["body_delta"] = {"location_to": "grid:2:3"}
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:],
        ),
    )
    assert request_as_body_effect(bad)


def test_p10_falsifier_effect_as_completion_oracle_structural() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["autonomy_claim"] = "general autonomy"
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(replace(step, envelope_payload=env),) + run.bridge_run.steps[1:],
        ),
    )
    assert effect_as_completion_oracle(bad)


def test_p10_falsifier_body_action_bypasses_ap01_structural() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(
                replace(
                    step,
                    world_submission_attempted=True,
                    ap01_published_request_count=1,
                    ap01_request_ref=None,
                    envelope_ref=None,
                ),
            )
            + run.bridge_run.steps[1:],
        ),
    )
    assert body_action_bypasses_ap01(bad)


def test_p10_falsifier_acp01_executes_body_action_structural() -> None:
    run = _run_move()
    step = run.bridge_run.steps[0]
    env = dict(step.envelope_payload or {})
    env["executed"] = True
    bad = replace(
        run,
        bridge_run=replace(
            run.bridge_run,
            steps=(replace(step, envelope_payload=env, candidate_source="acp01_internal"),) + run.bridge_run.steps[1:],
        ),
    )
    assert acp01_executes_body_action(bad)
