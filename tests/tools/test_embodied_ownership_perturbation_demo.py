from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_ownership_perturbation_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "self_caused_move_effect" in proc.stdout
    assert "hidden_eval_only_cause" in proc.stdout


def test_demo_self_move_case() -> None:
    proc = _run_demo("--scenario", "self_caused_move_effect", "--report")
    assert "OWNERSHIP PERTURBATION REPORT (P11)" in proc.stdout
    assert "self=supported" in proc.stdout


def test_demo_world_only_case() -> None:
    proc = _run_demo("--scenario", "world_only_object_change", "--json")
    payload = json.loads(proc.stdout)
    assert payload["scenario_id"] == "world_only_object_change"
    assert payload["ownership_assessment"]["self_cause_status"] in {"blocked", "not_supported"}


def test_demo_other_actor_case() -> None:
    proc = _run_demo("--scenario", "other_actor_object_change", "--report")
    assert "other=supported" in proc.stdout


def test_demo_mixed_case() -> None:
    proc = _run_demo("--scenario", "mixed_self_and_world_effect", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ownership_assessment"]["mixed_cause_status"] in {"supported", "weak"}
    assert payload["ownership_assessment"]["mixed_cause_preserved"] is True


def test_demo_unknown_case() -> None:
    proc = _run_demo("--scenario", "unknown_unexplained_effect", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ownership_assessment"]["unknown_cause_status"] in {"supported", "weak"}
    assert payload["ownership_assessment"]["unknown_preserved"] is True


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--scenario", "hidden_eval_only_cause", "--json")
    payload = json.loads(proc.stdout)
    assert payload["hidden_eval_used"] is False
    assert payload["ownership_assessment"]["fact_claimed"] is False


def test_demo_json_output() -> None:
    proc = _run_demo("--scenario", "self_caused_pickup_effect", "--json")
    payload = json.loads(proc.stdout)
    assert "falsifier_results" in payload
    assert "ablation_summary" in payload


def test_demo_report_does_not_overclaim_consciousness_full_self_model_complete_causality() -> None:
    proc = _run_demo("--scenario", "self_caused_move_effect", "--report")
    lowered = proc.stdout.lower()
    assert "consciousness proven" not in lowered
    assert "full self-model proven" not in lowered
    assert "complete causal attribution proven" not in lowered
