from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_delayed_credit_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "immediate_clear_effect" in proc.stdout
    assert "hidden_recipe_only" in proc.stdout


def test_demo_immediate_clear_case() -> None:
    proc = _run_demo("--scenario", "immediate_clear_effect", "--report")
    assert "DELAYED CREDIT LEARNING REPORT (P13)" in proc.stdout
    assert "scenario_id=immediate_clear_effect" in proc.stdout


def test_demo_delayed_case() -> None:
    proc = _run_demo("--scenario", "delayed_effect_correct_window", "--json")
    payload = json.loads(proc.stdout)
    assert payload["scenario_id"] == "delayed_effect_correct_window"
    assert payload["delayed_effect_records"]


def test_demo_confounded_case() -> None:
    proc = _run_demo("--scenario", "confounded_effect_two_precursors", "--report")
    lowered = proc.stdout.lower()
    assert "confounder_records=" in lowered


def test_demo_disconfirming_case() -> None:
    proc = _run_demo("--scenario", "disconfirming_episode", "--json")
    payload = json.loads(proc.stdout)
    statuses = [item["correlation_status"] for item in payload["candidate_credit_links"]]
    assert "disconfirmed" in statuses or "insufficient_evidence" in statuses


def test_demo_hidden_recipe_case() -> None:
    proc = _run_demo("--scenario", "hidden_recipe_only", "--json")
    payload = json.loads(proc.stdout)
    assert payload["candidate_credit_links"] == []
    assert payload["falsifier_results"]["hidden_recipe_leak"] is False


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "immediate_clear_effect", "--json")
    payload = json.loads(proc.stdout)
    assert "maturity_assessment" in payload
    assert "falsifier_results" in payload
    assert "calibration_summary" in payload


def test_demo_report_does_not_overclaim_mature_learning_recipe_consciousness() -> None:
    proc = _run_demo("--scenario", "immediate_clear_effect", "--report")
    lowered = proc.stdout.lower()
    assert "mature recipe learned" not in lowered
    assert "consciousness proven" not in lowered
