from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab7_recipe_automation_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "p15_candidate_bound_to_ab_frontier" in proc.stdout
    assert "one_success_trace_not_automation" in proc.stdout


def test_demo_p15_candidate_binding_case() -> None:
    proc = _run_demo("--case", "p15_candidate_bound_to_ab_frontier", "--report")
    assert "AB7 RECIPE-AUTOMATION INTEGRATION REPORT" in proc.stdout
    assert "frame_id=" in proc.stdout


def test_demo_repeated_trace_case() -> None:
    proc = _run_demo("--case", "repeated_trace_candidate_with_ab_support", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frame"] is not None
    assert payload["frame"]["mature_recipe_claimed"] is False


def test_demo_confounder_case() -> None:
    proc = _run_demo("--case", "active_confounder_blocks_recipe_maturity", "--report")
    assert "active_confounder_requires_resolution" in proc.stdout


def test_demo_disconfirming_case() -> None:
    proc = _run_demo("--case", "disconfirming_effect_blocks_recipe_integration", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frame"] is not None
    assert "disconfirming_trace_present" in payload["frame"]["blocked_reasons"]


def test_demo_protected_eval_case() -> None:
    proc = _run_demo("--case", "protected_eval_only_rule_rejected", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frame"] is None
    assert "protected_evaluator_only_rule_forbidden" in payload["reason_codes"]


def test_demo_one_trace_case() -> None:
    proc = _run_demo("--case", "one_success_trace_not_automation", "--report")
    assert "automation_claimed=False" in proc.stdout


def test_demo_json_output() -> None:
    proc = _run_demo("--case", "p15_candidate_bound_to_ab_frontier", "--json")
    payload = json.loads(proc.stdout)
    assert "telemetry" in payload
    assert "scope_marker" in payload


def test_demo_report_does_not_overclaim_automation_mature_recipes_tool_use_consciousness() -> None:
    proc = _run_demo("--case", "p15_candidate_bound_to_ab_frontier", "--report")
    lowered = proc.stdout.lower()
    assert "mature recipe learned" not in lowered
    assert "automation achieved" not in lowered
    assert "general tool use proven" not in lowered
    assert "consciousness proven" not in lowered
