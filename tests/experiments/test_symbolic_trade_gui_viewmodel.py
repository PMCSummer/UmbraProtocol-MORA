from __future__ import annotations

import copy
from dataclasses import asdict
import json
import subprocess
from pathlib import Path

from experiments.symbolic_trade.gui import (
    REQUIRED_RUSSIAN_LABELS,
    RUSSIAN_UI_STRINGS,
    build_stage5_gui_view_model,
    list_stage5_gui_scenarios,
    run_stage5_gui_payload,
)


def test_gui_localization_contains_required_russian_labels() -> None:
    required_keys = {
        "window_title",
        "scenario_selector",
        "run_mode_observe",
        "run_mode_execute",
        "scene_panel",
        "causal_spine_panel",
        "timeline_panel",
        "anti_shortcut_panel",
        "result_panel",
        "trace_inspector_panel",
        "first_step_button",
        "prev_step_button",
        "next_step_button",
        "last_step_button",
        "play_button",
        "pause_button",
        "speed_selector",
    }
    assert required_keys.issubset(set(RUSSIAN_UI_STRINGS))
    for label in REQUIRED_RUSSIAN_LABELS:
        assert label
        assert any(ord(ch) > 127 for ch in label)


def test_gui_scenario_selector_lists_all_stage_scenarios() -> None:
    scenarios = list_stage5_gui_scenarios()
    assert "successful_scripted_exchange_cycle" in scenarios
    assert "blocked_aperture" in scenarios
    assert "mirrored_resource_asymmetry" in scenarios
    assert "transfer_affordance_failure" in scenarios


def test_gui_viewmodel_default_excludes_eval_only_from_public_sections() -> None:
    payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=True)
    assert "eval_only" not in payload
    view_model = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
    public_flat = json.dumps(
        {
            "scene_items": view_model.scene_items,
            "result_items": view_model.result_items,
            "causal_spine_items": view_model.causal_spine_items,
            "anti_shortcut_items": view_model.anti_shortcut_items,
            "timeline": [asdict(step) for step in view_model.timeline_state.steps],
            "playback_trace": asdict(view_model.playback_trace),
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    assert "\"eval_only\":" not in public_flat
    assert "harness_truth" not in public_flat
    assert view_model.developer_payload == {"mode": RUSSIAN_UI_STRINGS["dev_mode_disabled"]}


def test_gui_viewmodel_dev_mode_can_include_eval_only_only_when_explicit() -> None:
    payload_without_eval = run_stage5_gui_payload(
        "successful_scripted_exchange_cycle",
        execute_world_actuator=True,
        include_eval_only=False,
    )
    vm_without_eval = build_stage5_gui_view_model(
        payload_without_eval,
        dev_mode=True,
        include_eval_only=False,
    )
    assert "eval_only" not in vm_without_eval.developer_payload

    payload_with_eval = run_stage5_gui_payload(
        "successful_scripted_exchange_cycle",
        execute_world_actuator=True,
        include_eval_only=True,
    )
    vm_with_eval = build_stage5_gui_view_model(
        payload_with_eval,
        dev_mode=True,
        include_eval_only=True,
    )
    assert "eval_only" in vm_with_eval.developer_payload
    assert "harness_truth" in vm_with_eval.developer_payload["eval_only"]


def test_gui_timeline_navigation_and_bounds() -> None:
    payload = run_stage5_gui_payload("mirrored_resource_asymmetry", execute_world_actuator=False)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)

    assert vm.step_count >= 10
    assert vm.current_step_index == 0
    assert vm.can_go_previous is False
    assert vm.can_go_next is True

    vm.go_next()
    assert vm.current_step_index == 1

    vm.go_last()
    assert vm.current_step_index == vm.step_count - 1
    assert vm.can_go_next is False

    vm.go_previous()
    assert vm.current_step_index == vm.step_count - 2

    vm.go_first()
    assert vm.current_step_index == 0

    vm.set_step(999)
    assert vm.current_step_index == vm.step_count - 1

    vm.reset_timeline()
    assert vm.current_step_index == 0
    assert vm.play_state == "paused"


def test_gui_presentation_trace_has_frame_driven_chamber_state() -> None:
    payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=True)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)

    assert vm.playback_trace.frame_count == vm.step_count
    assert vm.playback_trace.frame_count > 10

    initial = asdict(vm.playback_trace.frames[0].chamber_state)
    offer_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "offer_candidate")
    invocation_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "world_actuator")
    result_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "transfer_result")

    assert initial != asdict(offer_frame.chamber_state)
    assert offer_frame.chamber_state.offer_visible is True
    assert offer_frame.chamber_state.actuator_invoked_visible is False
    assert invocation_frame.chamber_state.actuator_invoked_visible is True
    assert asdict(offer_frame.chamber_state) != asdict(invocation_frame.chamber_state)
    assert result_frame.chamber_state.transfer_result_visible is True
    assert result_frame.chamber_state.transfer_result == "succeeded"


def test_gui_current_frame_tracks_navigation() -> None:
    payload = run_stage5_gui_payload("mirrored_resource_asymmetry", execute_world_actuator=False)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)

    first_frame = vm.current_frame
    vm.go_next()
    assert vm.current_frame.step_index == 2
    assert vm.current_frame != first_frame
    vm.go_last()
    assert vm.current_frame.step_id == "final_claim_boundary"
    vm.reset_timeline()
    assert vm.current_frame == first_frame


def test_gui_noexec_and_exec_frames_visibly_differ_for_successful_cycle() -> None:
    noexec = build_stage5_gui_view_model(
        run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=False),
        dev_mode=False,
        include_eval_only=False,
    )
    exec_vm = build_stage5_gui_view_model(
        run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=True),
        dev_mode=False,
        include_eval_only=False,
    )

    noexec_invocation = next(frame for frame in noexec.playback_trace.frames if frame.event_kind == "world_actuator")
    exec_invocation = next(frame for frame in exec_vm.playback_trace.frames if frame.event_kind == "world_actuator")
    noexec_completion = next(frame for frame in noexec.playback_trace.frames if frame.event_kind == "completion")
    exec_completion = next(frame for frame in exec_vm.playback_trace.frames if frame.event_kind == "completion")

    assert noexec_invocation.chamber_state.actuator_invoked_visible is False
    assert exec_invocation.chamber_state.actuator_invoked_visible is True
    assert noexec_completion.chamber_state.completion_claim is False
    assert exec_completion.chamber_state.completion_claim is True
    assert asdict(noexec_completion.chamber_state) != asdict(exec_completion.chamber_state)


def test_gui_timeline_step_fields_are_present() -> None:
    payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=True)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
    step = vm.current_step
    assert step.step_index >= 1
    assert step.step_id
    assert step.title_ru
    assert step.short_explanation_ru
    assert step.status
    assert isinstance(step.evidence_refs, tuple)
    assert isinstance(step.hidden_or_eval_excluded, bool)
    assert isinstance(step.is_decision_bearing, bool)
    assert step.claim_boundary_note_ru


def test_gui_stage5_successful_cycle_maps_execution_boundary() -> None:
    noexec_payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=False)
    noexec_vm = build_stage5_gui_view_model(noexec_payload, dev_mode=False, include_eval_only=False)
    assert noexec_vm.offer_candidate_emitted is True
    assert noexec_vm.invocation_request_created is True
    assert noexec_vm.world_actuator_invoked is False
    assert noexec_vm.completion_claim is False

    exec_payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=True)
    exec_vm = build_stage5_gui_view_model(exec_payload, dev_mode=False, include_eval_only=False)
    assert exec_vm.offer_candidate_emitted is True
    assert exec_vm.affordance_selection_status == "selected_for_invocation_request"
    assert exec_vm.invocation_request_created is True
    assert exec_vm.world_actuator_invoked is True
    assert exec_vm.completion_claim is True
    assert exec_vm.verification_status == "verified"


def test_gui_stage5_blocked_aperture_maps_blocked_and_no_completion() -> None:
    payload = run_stage5_gui_payload("blocked_aperture", execute_world_actuator=True)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
    assert vm.world_actuator_invoked is False
    assert vm.completion_claim is False
    assert vm.readiness_status in {
        "blocked",
        "revalidation_required",
        "observe_only",
        "abstain",
    }
    invocation_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "world_actuator")
    assert invocation_frame.chamber_state.actuator_invoked_visible is False
    assert invocation_frame.chamber_state.aperture_open is False


def test_gui_transfer_affordance_failure_has_failed_result_without_completion() -> None:
    payload = run_stage5_gui_payload("transfer_affordance_failure", execute_world_actuator=True)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
    assert vm.world_actuator_invoked is True
    assert vm.transfer_result.startswith("failed")
    assert vm.completion_claim is False
    result_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "transfer_result")
    completion_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "completion")
    assert result_frame.chamber_state.actuator_invoked_visible is True
    assert result_frame.chamber_state.transfer_result.startswith("failed")
    assert completion_frame.chamber_state.completion_claim is False
    assert completion_frame.chamber_state.residue_visible is True


def test_gui_noexec_mode_keeps_world_actuator_off_for_all_scenarios() -> None:
    for scenario_id in list_stage5_gui_scenarios():
        payload = run_stage5_gui_payload(scenario_id, execute_world_actuator=False)
        vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
        assert vm.world_actuator_invoked is False
        assert vm.transfer_result == "not_attempted"
        assert vm.causal_post_invocation_ref_count == 0


def test_gui_phase_statuses_not_hardcoded_passed() -> None:
    payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=False)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
    phases = {item["phase"]: item for item in vm.causal_spine_items}
    for phase in ("W01", "W02", "W03", "W05"):
        assert phases[phase]["status"] in {"trace_derived", "missing", "not_exposed", "inferred_from_stage5_summary"}
        assert phases[phase]["status_ru"] != "пройдено"


def test_gui_public_passive_vs_causal_counts_present() -> None:
    payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=False)
    vm = build_stage5_gui_view_model(payload, dev_mode=False, include_eval_only=False)
    labels = {item["label_ru"] for item in vm.result_items}
    assert RUSSIAN_UI_STRINGS["passive_packets"] in labels
    assert RUSSIAN_UI_STRINGS["causal_packets"] in labels
    result_frame = next(frame for frame in vm.playback_trace.frames if frame.event_kind == "transfer_result")
    assert result_frame.chamber_state.passive_packet_ref_count > 0
    assert result_frame.chamber_state.causal_post_invocation_ref_count == 0


def test_gui_russian_labels_exist_for_major_event_kinds() -> None:
    for key in (
        "event_claim",
        "event_offer",
        "event_affordance",
        "event_invocation",
        "event_result",
        "event_verification",
        "chamber_symbolic_boundary",
    ):
        value = RUSSIAN_UI_STRINGS[key]
        assert value
        assert any(ord(ch) > 127 for ch in value)


def test_gui_anti_shortcut_statuses_are_derived_from_falsifier_results() -> None:
    payload = run_stage5_gui_payload("successful_scripted_exchange_cycle", execute_world_actuator=True)
    mutated = copy.deepcopy(payload)
    falsifiers = list(mutated.get("falsifier_summary", []))
    for item in falsifiers:
        if item.get("name") == "stage5_b_claim_as_fact":
            item["passed"] = False
            break
    else:
        raise AssertionError("stage5_b_claim_as_fact falsifier not found")
    mutated["falsifier_summary"] = falsifiers
    vm = build_stage5_gui_view_model(mutated, dev_mode=False, include_eval_only=False)
    target = next(item for item in vm.anti_shortcut_items if item["falsifier_name"] == "stage5_b_claim_as_fact")
    assert target["passed"] is False


def test_gui_forbidden_core_status_remains_clean() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            "git",
            "status",
            "--short",
            "--",
            "src/substrate/w01*",
            "src/substrate/w02*",
            "src/substrate/w03*",
            "src/substrate/w04*",
            "src/substrate/w05*",
            "src/substrate/w06*",
            "src/substrate/subject_tick",
            "src/substrate/runtime_topology/policy.py",
            "src/substrate/runtime_tap_trace.py",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""
