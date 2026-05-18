from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_mini_factory_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "full_chain_verified" in proc.stdout
    assert "evaluator_only_chain_rule_rejected" in proc.stdout


def test_demo_full_chain_case() -> None:
    proc = _run_demo("--scenario", "full_chain_verified", "--report")
    assert "MINI-FACTORY CHAIN REPORT (P17)" in proc.stdout
    assert "scenario_id=full_chain_verified" in proc.stdout


def test_demo_missing_first_input_case() -> None:
    proc = _run_demo("--scenario", "missing_first_input_blocks_chain", "--json")
    payload = json.loads(proc.stdout)
    assert payload["completion_assessment"]["chain_complete"] is False


def test_demo_failed_plate_step_case() -> None:
    proc = _run_demo("--scenario", "failed_plate_step_blocks_filter", "--report")
    lowered = proc.stdout.lower()
    assert "completion_status" in lowered


def test_demo_partial_chain_case() -> None:
    proc = _run_demo("--scenario", "partial_chain_no_completion", "--json")
    payload = json.loads(proc.stdout)
    assert payload["completion_assessment"]["chain_complete"] is False


def test_demo_evaluator_only_rule_case() -> None:
    proc = _run_demo("--scenario", "evaluator_only_chain_rule_rejected", "--json")
    payload = json.loads(proc.stdout)
    assert payload["completion_assessment"]["chain_complete"] is False
    assert payload["hidden_eval_used"] is False


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "full_chain_verified", "--json")
    payload = json.loads(proc.stdout)
    assert "chain_step_traces" in payload
    assert "falsifier_results" in payload
    assert "ablation_summary" in payload


def test_demo_report_does_not_overclaim_factory_automation_or_general_intelligence() -> None:
    proc = _run_demo("--scenario", "full_chain_verified", "--report")
    lowered = proc.stdout.lower()
    assert "general automation proven" not in lowered
    assert "mature factory skill achieved" not in lowered
    assert "consciousness proven" not in lowered
