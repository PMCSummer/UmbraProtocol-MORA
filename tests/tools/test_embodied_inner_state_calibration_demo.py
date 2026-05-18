from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_inner_state_calibration_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "clear_self_caused_effect" in proc.stdout
    assert "hidden_eval_only_cause" in proc.stdout


def test_demo_clear_self_case() -> None:
    proc = _run_demo("--scenario", "clear_self_caused_effect", "--report")
    assert "INNER-STATE CALIBRATION REPORT (P12)" in proc.stdout
    assert "scenario_id=clear_self_caused_effect" in proc.stdout


def test_demo_world_only_case() -> None:
    proc = _run_demo("--scenario", "world_only_change", "--json")
    payload = json.loads(proc.stdout)
    assert payload["scenario_id"] == "world_only_change"
    assert payload["public_report"]["fact_claimed"] is False


def test_demo_mixed_case() -> None:
    proc = _run_demo("--scenario", "mixed_cause", "--report")
    lowered = proc.stdout.lower()
    assert "conflict_reported=true" in lowered


def test_demo_conflict_case() -> None:
    proc = _run_demo("--scenario", "conflicting_evidence", "--json")
    payload = json.loads(proc.stdout)
    assert payload["public_report"]["conflict_reported"] is True
    assert payload["public_report"]["closure_status"] == "open"


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--scenario", "hidden_eval_only_cause", "--json")
    payload = json.loads(proc.stdout)
    assert payload["hidden_leak_detected"] is False
    assert payload["public_report"]["hidden_eval_used"] is False


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "clear_self_caused_effect", "--json")
    payload = json.loads(proc.stdout)
    assert "calibration_metrics" in payload
    assert "falsifier_results" in payload
    assert "sealed_condition_id" in payload


def test_demo_report_does_not_overclaim_consciousness_full_causality_general_reasoning() -> None:
    proc = _run_demo("--scenario", "clear_self_caused_effect", "--report")
    lowered = proc.stdout.lower()
    assert "consciousness proven" not in lowered
    assert "full causality proven" not in lowered
    assert "general reasoning proven" not in lowered
