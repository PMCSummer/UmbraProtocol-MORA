from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from experiments.embodied_playground.candidate_provider import ManualCandidateProvider, ManualCandidateSpec
from experiments.embodied_playground.falsifiers import (
    ap01_policy_called_directly_by_bridge,
    bridge_calls_w_modules_directly,
    public_trace_contains_eval_only,
)
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge
from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig


def test_bridge_config_and_no_candidate_observe_only() -> None:
    run = run_subject_world_bridge(
        scenario_id="empty_room_presence",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
        ),
        candidate_provider=None,
    )
    assert run.subject_tick_used_any is True
    assert run.world_submissions_count == 0
    assert run.world_effect_count == 0
    assert run.autonomous_action_selection is False
    assert run.eval_only is None

    step = run.steps[0]
    assert step.subject_tick_used is True
    assert step.ap01_candidate_count == 0
    assert step.ap01_published_request_count == 0
    assert step.world_submission_attempted is False
    assert step.bridge_chose_action is False


def test_manual_candidate_provider_is_explicit_non_autonomous_input() -> None:
    provider = ManualCandidateProvider(
        plans_by_tick={
            1: (
                ManualCandidateSpec(action_kind="move_forward", intended_effect="move_forward"),
            ),
        }
    )
    run = run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=True,
            allow_manual_candidate_provider=True,
        ),
        candidate_provider=provider,
    )
    step = run.steps[0]
    assert step.manual_candidate_input is True
    assert step.bridge_chose_action is False
    assert step.autonomous_action_selection is False


def test_bridge_runtime_uses_subject_tick_and_no_direct_phase_policy_calls() -> None:
    source_text = Path("experiments/embodied_playground/subject_bridge.py").read_text(encoding="utf-8")
    assert bridge_calls_w_modules_directly(source_text) is False
    assert ap01_policy_called_directly_by_bridge(source_text) is False


def test_public_trace_excludes_eval_only_by_default() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=False,
            include_eval_only=False,
        ),
    )
    assert public_trace_contains_eval_only(run) is False


def test_public_trace_may_include_eval_only_in_separate_scope_when_enabled() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=1,
            execute_world_actions=False,
            include_eval_only=True,
        ),
    )
    assert run.eval_only is not None
    # Public per-step trace remains hidden/eval-excluded even when eval scope is requested.
    for step in run.steps:
        assert step.hidden_eval_excluded is True


def test_bridge_tick_subject_tick_used_is_runtime_derived(monkeypatch) -> None:
    from experiments.embodied_playground import subject_bridge as sb

    called = {"value": False}

    def _fake_tick(*_args, **_kwargs):
        called["value"] = True
        telemetry = SimpleNamespace(
            candidate_count=0,
            published_request_count=0,
            blocked_count=0,
            revalidation_required_count=0,
            unsafe_basis_count=0,
        )
        ap01_result = SimpleNamespace(telemetry=telemetry, published_requests=(), decisions=())
        state = SimpleNamespace(tick_id="subject-tick-runtime-derived")
        return SimpleNamespace(ap01_result=ap01_result, state=state)

    monkeypatch.setattr(sb, "execute_subject_tick", _fake_tick)
    run = sb.run_subject_world_bridge(
        scenario_id="empty_room_presence",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
    )
    step = run.steps[0]
    assert called["value"] is True
    assert step.subject_tick_used is True
    assert step.subject_tick_result_ref == "subject-tick-runtime-derived"


def test_bridge_does_not_report_subject_tick_used_when_tick_call_fails(monkeypatch) -> None:
    from experiments.embodied_playground import subject_bridge as sb

    def _boom(*_args, **_kwargs):
        raise RuntimeError("tick_failure")

    monkeypatch.setattr(sb, "execute_subject_tick", _boom)
    run = sb.run_subject_world_bridge(
        scenario_id="empty_room_presence",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
    )
    step = run.steps[0]
    assert run.subject_tick_used_any is False
    assert step.subject_tick_used is False
    assert step.subject_tick_result_ref is None
    assert step.subject_tick_error is not None
    assert "tick_failure" in step.subject_tick_error


def test_bridge_does_not_submit_world_action_when_subject_tick_fails(monkeypatch) -> None:
    from experiments.embodied_playground import subject_bridge as sb

    def _boom(*_args, **_kwargs):
        raise RuntimeError("tick_failure")

    monkeypatch.setattr(sb, "execute_subject_tick", _boom)
    run = sb.run_subject_world_bridge(
        scenario_id="open_movement_forward",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=True),
    )
    step = run.steps[0]
    assert run.world_submissions_count == 0
    assert step.world_submission_attempted is False
    assert step.world_effect_id is None


def test_subject_tick_surface_payload_includes_public_body_inventory_objects_and_action_space() -> None:
    run = run_subject_world_bridge(
        scenario_id="visible_item_pickup_available",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=False),
    )
    payload = run.steps[0].subject_tick_surface_payload
    assert "body" in payload
    assert "inventory" in payload
    assert "visible_objects" in payload
    assert "action_space" in payload
    assert "previous_effect_refs" in payload
    assert "location_ref" in payload["body"]
    assert "orientation" in payload["body"]
    assert "item_counts" in payload["inventory"]
    assert "available_surfaces" in payload["action_space"]


def test_subject_tick_surface_payload_excludes_eval_only_and_private_world_data() -> None:
    run = run_subject_world_bridge(
        scenario_id="hidden_map_not_visible",
        config=SubjectWorldBridgeConfig(subject_id="subject_a", max_ticks=1, execute_world_actions=False),
    )
    payload = run.steps[0].subject_tick_surface_payload
    text = str(payload).lower()
    for forbidden in ("hidden_objects", "hidden_inventory", "true_recipe_table", "expected_outcome", "scenario_labels", "eval_only"):
        assert forbidden not in text


def test_effect_feedback_ref_is_preserved_in_enriched_subject_tick_payload() -> None:
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
    assert first.world_effect_id in second.subject_tick_surface_payload["previous_effect_refs"]
