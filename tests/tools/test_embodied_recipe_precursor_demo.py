from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_recipe_precursor_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "one_success_trace_provisional_only" in proc.stdout
    assert "hidden_recipe_only_no_candidate" in proc.stdout


def test_demo_one_success_case() -> None:
    proc = _run_demo("--scenario", "one_success_trace_provisional_only", "--report")
    assert "RECIPE/PRECURSOR LEARNING REPORT (P15)" in proc.stdout
    assert "scenario_id=one_success_trace_provisional_only" in proc.stdout


def test_demo_repeated_trace_case() -> None:
    proc = _run_demo("--scenario", "repeated_consistent_traces_candidate_strengthens", "--json")
    payload = json.loads(proc.stdout)
    assert payload["recipe_candidates"]
    assert payload["maturity_assessment"]["mature_recipe_count"] == 0


def test_demo_hidden_recipe_case() -> None:
    proc = _run_demo("--scenario", "hidden_recipe_only_no_candidate", "--json")
    payload = json.loads(proc.stdout)
    assert payload["maturity_assessment"]["hidden_recipe_detected"] is False


def test_demo_confounded_case() -> None:
    proc = _run_demo("--scenario", "confounded_station_effect", "--report")
    lowered = proc.stdout.lower()
    assert "confounders=" in lowered
    assert "mature_recipe_count=0" in lowered


def test_demo_disconfirming_case() -> None:
    proc = _run_demo("--scenario", "disconfirming_trace_blocks_maturity", "--json")
    payload = json.loads(proc.stdout)
    assert payload["disconfirming_records"]


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "one_success_trace_provisional_only", "--json")
    payload = json.loads(proc.stdout)
    assert "falsifier_results" in payload
    assert "ablation_summary" in payload


def test_demo_report_does_not_overclaim_mature_recipe_automation_tool_use_consciousness() -> None:
    proc = _run_demo("--scenario", "one_success_trace_provisional_only", "--report")
    lowered = proc.stdout.lower()
    assert "mature recipe learned" not in lowered
    assert "automation achieved" not in lowered
    assert "general tool use proven" not in lowered
    assert "consciousness proven" not in lowered
