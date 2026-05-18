from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_station_affordance_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "station_visible_not_usable" in proc.stdout
    assert "station_protected_eval_only_rule" in proc.stdout


def test_demo_visible_not_usable_case() -> None:
    proc = _run_demo("--scenario", "station_visible_not_usable", "--report")
    assert "STATION AFFORDANCE REPORT (P14)" in proc.stdout
    assert "scenario_id=station_visible_not_usable" in proc.stdout


def test_demo_proximate_no_input_case() -> None:
    proc = _run_demo("--scenario", "station_proximate_no_input", "--json")
    payload = json.loads(proc.stdout)
    assert payload["input_status"] == "missing_input"
    assert payload["effect_status"] == "blocked"


def test_demo_proximate_with_input_case() -> None:
    proc = _run_demo("--scenario", "station_proximate_with_input", "--report")
    lowered = proc.stdout.lower()
    assert "ap01_publication_status=published" in lowered
    assert "world_submission_status=submitted" in lowered


def test_demo_blocked_station_case() -> None:
    proc = _run_demo("--scenario", "station_blocked", "--json")
    payload = json.loads(proc.stdout)
    assert payload["blocked_status"] == "blocked"
    assert payload["effect_status"] == "blocked"


def test_demo_protected_eval_only_case() -> None:
    proc = _run_demo("--scenario", "station_protected_eval_only_rule", "--json")
    payload = json.loads(proc.stdout)
    assert payload["protected_evaluator_only_rule_present"] is True
    assert payload["ap01_publication_status"] != "published"


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "station_proximate_with_input", "--json")
    payload = json.loads(proc.stdout)
    assert "falsifier_results" in payload
    assert "ablation_summary" in payload


def test_demo_report_does_not_overclaim_recipe_tool_use_automation_consciousness() -> None:
    proc = _run_demo("--scenario", "station_proximate_with_input", "--report")
    lowered = proc.stdout.lower()
    assert "learned recipe" not in lowered
    assert "general tool use proven" not in lowered
    assert "automation achieved" not in lowered
    assert "consciousness proven" not in lowered
