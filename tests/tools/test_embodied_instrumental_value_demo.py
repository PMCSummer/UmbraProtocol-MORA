from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_instrumental_value_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "resource_with_need_and_recipe_chain" in proc.stdout
    assert "hidden_eval_value_rule_rejected" in proc.stdout


def test_demo_resource_with_need_chain_case() -> None:
    proc = _run_demo("--scenario", "resource_with_need_and_recipe_chain", "--report")
    assert "INSTRUMENTAL VALUE REPORT (P16)" in proc.stdout
    assert "scenario_id=resource_with_need_and_recipe_chain" in proc.stdout


def test_demo_no_need_case() -> None:
    proc = _run_demo("--scenario", "resource_without_need_no_value", "--json")
    payload = json.loads(proc.stdout)
    assert payload["instrumental_value_frames"]
    assert payload["instrumental_value_frames"][0]["value_status"] in {"no_value", "blocked"}


def test_demo_iron_magic_guard_case() -> None:
    proc = _run_demo("--scenario", "iron_magic_value_guard", "--json")
    payload = json.loads(proc.stdout)
    assert payload["falsifier_results"]["iron_magic_value"] is False


def test_demo_filter_without_water_problem_case() -> None:
    proc = _run_demo("--scenario", "filter_without_water_problem", "--report")
    lowered = proc.stdout.lower()
    assert "resource_refs" in lowered
    assert "intrinsic_value_claimed=false" in lowered


def test_demo_confounded_case() -> None:
    proc = _run_demo("--scenario", "confounded_resource_value", "--json")
    payload = json.loads(proc.stdout)
    assert payload["confounder_refs"]
    assert payload["instrumental_value_frames"][0]["value_status"] in {"weak_instrumental", "blocked"}


def test_demo_hidden_eval_rule_case() -> None:
    proc = _run_demo("--scenario", "hidden_eval_value_rule_rejected", "--json")
    payload = json.loads(proc.stdout)
    assert payload["hidden_eval_used"] is False
    assert payload["instrumental_value_frames"][0]["value_status"] == "blocked"


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "resource_with_need_and_recipe_chain", "--json")
    payload = json.loads(proc.stdout)
    assert "value_chains" in payload
    assert "means_candidates" in payload
    assert "ablation_summary" in payload


def test_demo_report_does_not_overclaim_automation_value_learning_consciousness() -> None:
    proc = _run_demo("--scenario", "resource_with_need_and_recipe_chain", "--report")
    lowered = proc.stdout.lower()
    assert "intrinsic value learning achieved" not in lowered
    assert "automation achieved" not in lowered
    assert "consciousness proven" not in lowered
