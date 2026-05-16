from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REQUIRED_SCENARIOS = (
    "presence_only",
    "resource_claim_contact",
    "mirrored_resource_asymmetry",
    "false_counterpart_claim",
    "blocked_aperture",
    "noisy_signal",
    "transfer_seen_without_trade_token",
    "eval_label_leak_attack",
)
STAGE3_SCENARIOS = REQUIRED_SCENARIOS + (
    "a_deficit_only",
    "b_surplus_claim_only",
    "claim_then_confirmed_transfer",
    "claim_then_failed_transfer",
)
STAGE4_SCENARIOS = STAGE3_SCENARIOS + (
    "b_surplus_only",
    "b_need_only",
    "clarification_resolves_missing_need",
    "clarification_loop_guard",
    "transfer_affordance_failure",
    "successful_scripted_exchange_cycle",
)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "symbolic_trade_experiment.py"), *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_symbolic_trade_cli_list_scenarios() -> None:
    result = _run("--list-scenarios")
    assert result.returncode == 0, result.stderr
    for scenario in STAGE4_SCENARIOS:
        assert scenario in result.stdout


def test_symbolic_trade_cli_smoke_scenarios() -> None:
    for scenario in REQUIRED_SCENARIOS:
        result = _run("--scenario", scenario, "--run-falsifiers")
        assert result.returncode == 0, result.stderr
        assert "SYMBOLIC TRADE HARNESS" in result.stdout
        assert f"scenario_id={scenario}" in result.stdout
        assert "packet_count=" in result.stdout
        assert "falsifier_summary=" in result.stdout
        assert "claim_discipline_markers=" in result.stdout


def test_symbolic_trade_cli_json_output_contains_required_fields() -> None:
    result = _run("--scenario", "mirrored_resource_asymmetry", "--json", "--run-falsifiers")
    assert result.returncode == 0, result.stderr
    assert '"scenario_id": "mirrored_resource_asymmetry"' in result.stdout
    assert '"packet_count"' in result.stdout
    assert '"falsifier_results"' in result.stdout
    assert '"claim_discipline_markers"' in result.stdout


def test_symbolic_trade_cli_default_json_excludes_eval_only() -> None:
    result = _run("--scenario", "mirrored_resource_asymmetry", "--json", "--run-falsifiers")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "eval_only" not in payload


def test_symbolic_trade_cli_include_eval_only_is_scoped() -> None:
    result = _run("--scenario", "mirrored_resource_asymmetry", "--json", "--run-falsifiers", "--include-eval-only")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "eval_only" in payload
    for step in payload["steps"]:
        for packet in step["subject_visible_packets"]:
            flat = json.dumps(packet, sort_keys=True)
            assert "harness_truth" not in flat
            assert "mutually_beneficial_trade_possible_eval_only" not in flat


def test_repo_root_imports_work_without_manual_pythonpath() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-c", "import experiments.symbolic_trade as st; import experiments.symbolic_trade.runner as r; print('ok')"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_symbolic_trade_cli_stage2_trace_text_and_json_smoke() -> None:
    text_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage2-trace")
    assert text_result.returncode == 0, text_result.stderr
    assert "SYMBOLIC TRADE HARNESS STAGE2 TRACE" in text_result.stdout
    assert "stage2_trace_verdict=" in text_result.stdout

    json_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage2-trace", "--json")
    assert json_result.returncode == 0, json_result.stderr
    payload = json.loads(json_result.stdout)
    assert payload["stage"] == "stage_2_subject_adapter_trace_through"
    assert {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(payload["phase_coverage"]))
    assert "eval_only" not in payload


def test_symbolic_trade_cli_stage2_trace_with_falsifiers_exits_zero() -> None:
    for scenario in REQUIRED_SCENARIOS:
        result = _run("--scenario", scenario, "--stage2-trace", "--run-falsifiers")
        assert result.returncode == 0, result.stderr


def test_symbolic_trade_cli_stage2_include_eval_only_scoped() -> None:
    result = _run(
        "--scenario",
        "mirrored_resource_asymmetry",
        "--stage2-trace",
        "--json",
        "--run-falsifiers",
        "--include-eval-only",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "eval_only" in payload
    for step in payload["steps"]:
        for packet in step["packet_refs"]:
            flat = json.dumps(packet, sort_keys=True)
            assert "harness_truth" not in flat
            assert "mutually_beneficial_trade_possible_eval_only" not in flat


def test_symbolic_trade_cli_stage25_reaction_text_and_json_smoke() -> None:
    text_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage25-reaction")
    assert text_result.returncode == 0, text_result.stderr
    assert "SYMBOLIC TRADE HARNESS STAGE2.5 REAL-A REACTION PROBE" in text_result.stdout
    assert "execution_level=" in text_result.stdout
    assert "subject_tick_used=" in text_result.stdout

    json_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage25-reaction", "--json")
    assert json_result.returncode == 0, json_result.stderr
    payload = json.loads(json_result.stdout)
    assert payload["stage"] == "stage25_reaction_probe"
    assert "execution_surface" in payload
    assert "eval_only" not in payload


def test_symbolic_trade_cli_stage25_reaction_with_falsifiers_all_scenarios() -> None:
    for scenario in REQUIRED_SCENARIOS:
        result = _run("--scenario", scenario, "--stage25-reaction", "--run-falsifiers")
        assert result.returncode == 0, result.stderr
        assert "falsifier_summary=" in result.stdout


def test_symbolic_trade_cli_stage25_include_eval_only_scoped() -> None:
    result = _run(
        "--scenario",
        "mirrored_resource_asymmetry",
        "--stage25-reaction",
        "--json",
        "--run-falsifiers",
        "--include-eval-only",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "eval_only" in payload
    assert "harness_truth" in payload["eval_only"]
    for step in payload["steps"]:
        flat = json.dumps(step, sort_keys=True)
        assert "harness_truth" not in flat
        assert "mutually_beneficial_trade_possible_eval_only" not in flat
        assert "success_labels" not in flat
        phase_flat = json.dumps(step["phase_trace_summary"], sort_keys=True)
        assert "harness_truth" not in phase_flat
        assert "mutually_beneficial_trade_possible_eval_only" not in phase_flat


def test_symbolic_trade_cli_stage3_response_text_and_json_smoke() -> None:
    text_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage3-response")
    assert text_result.returncode == 0, text_result.stderr
    assert "SYMBOLIC TRADE HARNESS STAGE3 RESPONSE-CANDIDATE PROBE" in text_result.stdout
    assert "selected_response_kind=" in text_result.stdout

    json_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage3-response", "--json")
    assert json_result.returncode == 0, json_result.stderr
    payload = json.loads(json_result.stdout)
    assert payload["stage"] == "stage3_response_candidate_probe"
    assert "execution_level" in payload
    assert "response_verdict" in payload
    assert "eval_only" not in payload


def test_symbolic_trade_cli_stage3_all_scenarios_with_falsifiers_exit_zero() -> None:
    for scenario in STAGE3_SCENARIOS:
        result = _run("--scenario", scenario, "--stage3-response", "--run-falsifiers")
        assert result.returncode == 0, result.stderr
        assert "falsifier_summary=" in result.stdout


def test_symbolic_trade_cli_stage3_json_eval_scope_and_candidates_flag() -> None:
    summary_result = _run(
        "--scenario",
        "mirrored_resource_asymmetry",
        "--stage3-response",
        "--json",
        "--stage3-summary",
        "--run-falsifiers",
    )
    assert summary_result.returncode == 0, summary_result.stderr
    summary_payload = json.loads(summary_result.stdout)
    assert "response_candidates" not in summary_payload

    result = _run(
        "--scenario",
        "mirrored_resource_asymmetry",
        "--stage3-response",
        "--json",
        "--include-response-candidates",
        "--include-eval-only",
        "--run-falsifiers",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "eval_only" in payload
    assert "response_candidates" in payload
    for candidate in payload["response_candidates"]:
        flat = json.dumps(candidate, sort_keys=True)
        assert "harness_truth" not in flat
        assert "mutually_beneficial_trade_possible_eval_only" not in flat


def test_symbolic_trade_cli_stage4_text_and_json_smoke() -> None:
    text_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage4-cycle")
    assert text_result.returncode == 0, text_result.stderr
    assert "SYMBOLIC TRADE HARNESS STAGE4 CLARIFICATION-TRANSFER CYCLE" in text_result.stdout
    assert "readiness_status=" in text_result.stdout
    assert "transfer_affordance_status=" in text_result.stdout

    json_result = _run("--scenario", "mirrored_resource_asymmetry", "--stage4-cycle", "--json")
    assert json_result.returncode == 0, json_result.stderr
    payload = json.loads(json_result.stdout)
    assert payload["stage"] == "stage4_clarification_to_transfer_affordance_cycle"
    assert "eval_only" not in payload


def test_symbolic_trade_cli_stage4_with_flags_and_eval_scope() -> None:
    result = _run(
        "--scenario",
        "mirrored_resource_asymmetry",
        "--stage4-cycle",
        "--execute-transfer-affordance",
        "--json",
        "--include-eval-only",
        "--run-falsifiers",
        "--show-clarification-state",
        "--include-transfer-episode",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "eval_only" in payload
    assert payload["transfer_invocation_candidate"]["execution_requested"] is True
    visible_flat = json.dumps(
        {
            "visible_packets": payload.get("visible_packets", []),
            "transfer_invocation_candidate": payload.get("transfer_invocation_candidate", {}),
            "transfer_result_record": payload.get("transfer_result_record", {}),
        },
        sort_keys=True,
    )
    assert "harness_truth" not in visible_flat
    assert "mutual_benefit_oracle" not in visible_flat


def test_symbolic_trade_cli_stage4_noexec_keeps_passive_transfer_packets_non_causal() -> None:
    result = _run(
        "--scenario",
        "successful_scripted_exchange_cycle",
        "--stage4-cycle",
        "--json",
        "--run-falsifiers",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["transfer_attempt_record"]["attempted"] is False
    assert payload["transfer_result_record"]["outcome"] == "not_attempted"
    assert payload["post_invocation_response_count"] == 0
    assert payload["exchange_completion_claim"] is False
    for item in payload["scripted_b_response_details"]:
        assert item["caused_by_transfer_invocation"] is False
        assert item["causing_invocation_id"] is None
        assert item["attempt_id"] is None


def test_symbolic_trade_cli_stage4_exec_links_causal_response_to_invocation() -> None:
    result = _run(
        "--scenario",
        "successful_scripted_exchange_cycle",
        "--stage4-cycle",
        "--execute-transfer-affordance",
        "--json",
        "--run-falsifiers",
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["transfer_attempt_record"]["attempted"] is True
    assert payload["post_invocation_response_count"] > 0
    invocation_id = payload["transfer_invocation_candidate"]["invocation_id"]
    attempt_id = payload["transfer_attempt_record"]["attempt_id"]
    for item in payload["scripted_b_response_details"]:
        assert item["caused_by_transfer_invocation"] is True
        assert item["causing_invocation_id"] == invocation_id
        assert item["attempt_id"] == attempt_id


def test_symbolic_trade_cli_stage4_all_scenarios_with_falsifiers_exit_zero() -> None:
    for scenario in STAGE4_SCENARIOS:
        result = _run("--scenario", scenario, "--stage4-cycle", "--run-falsifiers")
        assert result.returncode == 0, result.stderr
        assert "falsifier_summary=" in result.stdout


def test_symbolic_trade_cli_stage4_all_scenarios_execute_transfer_mode_exit_zero() -> None:
    for scenario in STAGE4_SCENARIOS:
        result = _run(
            "--scenario",
            scenario,
            "--stage4-cycle",
            "--execute-transfer-affordance",
            "--run-falsifiers",
        )
        assert result.returncode == 0, result.stderr
        assert "falsifier_summary=" in result.stdout
