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
    for scenario in REQUIRED_SCENARIOS:
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
