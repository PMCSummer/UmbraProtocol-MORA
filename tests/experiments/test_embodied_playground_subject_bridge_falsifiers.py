from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path

from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig
from experiments.embodied_playground.candidate_provider import ManualCandidateProvider, ManualCandidateSpec
from experiments.embodied_playground.falsifiers import (
    action_space_as_action_request,
    ap01_policy_called_directly_by_bridge,
    bridge_calls_w_modules_directly,
    bridge_chooses_action_from_scenario_id,
    bridge_directly_mutates_world,
    candidate_provider_uses_hidden_or_eval,
    effect_not_correlated_to_request,
    effect_not_fed_to_next_observation,
    eval_truth_fed_to_subject_tick,
    hidden_map_fed_to_subject_tick,
    invalid_ap01_decision_submitted,
    multiple_requests_auto_selected,
    no_candidate_executes_action,
    observation_mutates_world,
    public_trace_contains_eval_only,
    raw_action_submitted_to_world,
    request_as_success_or_completion_bridge,
    subject_tick_not_used,
    world_effect_as_competence_oracle,
    world_executes_without_subject_request,
)
from experiments.embodied_playground.grid_world import GridWorldBackend, make_published_action_envelope
from experiments.embodied_playground.models import CorrelationStatus, EffectStatus
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


def test_p3_falsifier_function_presence() -> None:
    required = [
        bridge_calls_w_modules_directly,
        world_executes_without_subject_request,
        bridge_chooses_action_from_scenario_id,
        action_space_as_action_request,
        eval_truth_fed_to_subject_tick,
        hidden_map_fed_to_subject_tick,
        ap01_policy_called_directly_by_bridge,
        raw_action_submitted_to_world,
        invalid_ap01_decision_submitted,
        multiple_requests_auto_selected,
        effect_not_correlated_to_request,
        effect_not_fed_to_next_observation,
        observation_mutates_world,
        no_candidate_executes_action,
        request_as_success_or_completion_bridge,
        world_effect_as_competence_oracle,
        subject_tick_not_used,
        candidate_provider_uses_hidden_or_eval,
        public_trace_contains_eval_only,
        bridge_directly_mutates_world,
    ]
    assert len(required) == 20


def test_negative_control_bridge_direct_w_call_detection() -> None:
    source = Path("experiments/embodied_playground/subject_bridge.py").read_text(encoding="utf-8")
    assert bridge_calls_w_modules_directly(source) is False
    assert ap01_policy_called_directly_by_bridge(source) is False
    assert bridge_calls_w_modules_directly("from substrate.w01_world_modeling import build_w01") is True


def test_negative_control_world_executes_without_request() -> None:
    assert world_executes_without_subject_request(world_submission_attempted=False, ap01_published_request_count=0) is False
    assert world_executes_without_subject_request(world_submission_attempted=True, ap01_published_request_count=0) is True


def test_negative_control_scenario_id_action_selection() -> None:
    assert bridge_chooses_action_from_scenario_id({"mode": "manual"}) is False
    assert bridge_chooses_action_from_scenario_id({"scenario_to_action": "move_forward"}) is True


def test_negative_control_action_space_as_request() -> None:
    assert action_space_as_action_request(
        action_space_available=True,
        ap01_published_request_count=0,
        world_submission_attempted=False,
    ) is False
    assert action_space_as_action_request(
        action_space_available=True,
        ap01_published_request_count=0,
        world_submission_attempted=True,
    ) is True


def test_negative_control_eval_truth_and_hidden_map_fed_to_tick() -> None:
    assert eval_truth_fed_to_subject_tick({"visible_objects": ["item:1"]}) is False
    assert eval_truth_fed_to_subject_tick({"hidden_objects": ["object:hidden:1"]}) is True
    assert hidden_map_fed_to_subject_tick({"objects": ["item:visible"]}, "object:hidden:1") is False
    assert hidden_map_fed_to_subject_tick({"objects": ["object:hidden:1"]}, "object:hidden:1") is True


def test_negative_control_raw_action_and_invalid_decision_submission() -> None:
    envelope = make_published_action_envelope(subject_id="subject_a", action_kind="wait", request_ref="ap01_request:x")
    assert raw_action_submitted_to_world(envelope) is False
    assert raw_action_submitted_to_world("move_forward") is True
    assert invalid_ap01_decision_submitted(decision_statuses=("published",), world_submission_attempted=True) is False
    assert invalid_ap01_decision_submitted(decision_statuses=("blocked",), world_submission_attempted=True) is True


def test_negative_control_effect_not_fed_and_subject_tick_not_used() -> None:
    assert effect_not_fed_to_next_observation(effect_id="effect:1", next_previous_effect_refs=("effect:1",)) is False
    assert effect_not_fed_to_next_observation(effect_id="effect:1", next_previous_effect_refs=()) is True
    assert subject_tick_not_used(True) is False
    assert subject_tick_not_used(False) is True


def test_negative_control_no_candidate_executes_and_multiple_requests_auto_selected() -> None:
    assert no_candidate_executes_action(ap01_candidate_count=0, world_submission_attempted=False) is False
    assert no_candidate_executes_action(ap01_candidate_count=0, world_submission_attempted=True) is True
    assert multiple_requests_auto_selected(
        published_request_count=2,
        world_submission_attempted=False,
        reject_multiple_published_requests=True,
    ) is False
    assert multiple_requests_auto_selected(
        published_request_count=2,
        world_submission_attempted=True,
        reject_multiple_published_requests=True,
    ) is True


def test_negative_control_effect_correlation_and_completion_claim() -> None:
    backend = GridWorldBackend("open_movement_forward")
    envelope = make_published_action_envelope(subject_id="subject_a", action_kind="move_forward", request_ref="ap01_request:ok")
    effect = backend.submit_action(envelope)
    assert effect_not_correlated_to_request(effect) is False

    bad = replace(effect, correlation_status=CorrelationStatus.AMBIGUOUS)
    assert effect_not_correlated_to_request(bad) is True

    assert request_as_success_or_completion_bridge(
        envelope_created=True,
        world_effect_status="succeeded",
        bridge_claims_completion=False,
    ) is False
    assert request_as_success_or_completion_bridge(
        envelope_created=True,
        world_effect_status=None,
        bridge_claims_completion=True,
    ) is True


def test_negative_control_no_candidate_and_subject_tick_used_in_bridge_run() -> None:
    run = run_subject_world_bridge(
        scenario_id="empty_room_presence",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=None,
    )
    step = run.steps[0]
    assert step.subject_tick_used is True
    assert step.world_submission_attempted is False
    assert no_candidate_executes_action(ap01_candidate_count=step.ap01_candidate_count, world_submission_attempted=step.world_submission_attempted) is False
    assert public_trace_contains_eval_only(run) is False


def test_negative_control_manual_provider_hidden_eval_use_and_world_mutation_surface() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={1: (ManualCandidateSpec(action_kind="wait"),)}
    )
    assert candidate_provider_uses_hidden_or_eval(provider) is False
    assert candidate_provider_uses_hidden_or_eval({"strategy": "scenario_to_action"}) is True
    assert bridge_directly_mutates_world(world_mutation_surface="submit_action") is False
    assert bridge_directly_mutates_world(world_mutation_surface="observe") is True


def test_negative_control_world_effect_as_competence_oracle() -> None:
    assert world_effect_as_competence_oracle(world_effect_status="succeeded", bridge_claims_autonomy=False) is False
    assert world_effect_as_competence_oracle(world_effect_status="succeeded", bridge_claims_autonomy=True) is True


def test_negative_control_observation_mutates_world() -> None:
    assert observation_mutates_world(world_tick_before=1, world_tick_after_observe_only=1) is False
    assert observation_mutates_world(world_tick_before=1, world_tick_after_observe_only=2) is True


def test_negative_control_action_without_ap01_request_path_not_used() -> None:
    backend = GridWorldBackend("invalid_envelope_rejected")
    effect = backend.submit_action({"action_kind": "move_forward"})  # type: ignore[arg-type]
    assert effect.effect_status == EffectStatus.BLOCKED
    assert str(getattr(effect.correlation_status, "value", effect.correlation_status)) == CorrelationStatus.INVALID.value


def test_p3_check_scenario_id_action_basis_detects_structured_candidate_marker() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={
            1: (
                ManualCandidateSpec(
                    action_kind="move_forward",
                    args={"action_basis": "scenario_id:open_movement_forward"},
                ),
            )
        }
    )
    assert bridge_chooses_action_from_scenario_id(provider) is True


def test_p3_check_scenario_id_identity_field_is_not_action_basis() -> None:
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=False),
        candidate_provider=None,
    )
    assert bridge_chooses_action_from_scenario_id(run) is False


def test_p3_check_eval_private_data_detects_structured_subject_tick_payload_violation() -> None:
    payload = {
        "surface_schema_version": "p3_public_observation_v1",
        "body": {"location_ref": "grid:1,1"},
        "inventory": {"used_slots": 0},
        "visible_objects": (),
        "action_space": {"frame_id": "as:1"},
        "previous_effect_refs": (),
        "expected_outcome": "leak",
    }
    assert eval_truth_fed_to_subject_tick(payload) is True


def test_p3_public_payload_allows_no_eval_section_by_default() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=False, include_eval_only=False),
        candidate_provider=None,
    )
    payload = run.steps[0].subject_tick_surface_payload
    assert eval_truth_fed_to_subject_tick(payload) is False


def test_p3_check_public_trace_eval_scope_is_structural() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=False, include_eval_only=True),
        candidate_provider=None,
    )
    assert public_trace_contains_eval_only(run) is False
    leaked = replace(
        run.steps[0],
        subject_tick_surface_payload={
            **run.steps[0].subject_tick_surface_payload,
            "hidden_objects": [{"object_ref": "object:hidden:1"}],
        },
    )
    assert public_trace_contains_eval_only({"run": {"steps": [asdict(leaked)], "eval_only": run.eval_only}}) is True


def test_p3_check_subject_tick_not_used_detects_effect_without_tick_result_marker() -> None:
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
        candidate_provider=ManualCandidateProvider(
            plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
        ),
    )
    step = run.steps[0]
    assert step.world_effect_id is not None
    assert subject_tick_not_used(record=step) is False
    broken_step = replace(step, subject_tick_used=False)
    assert subject_tick_not_used(record=broken_step) is True
