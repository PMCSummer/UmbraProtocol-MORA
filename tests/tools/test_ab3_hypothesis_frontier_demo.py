from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab3_hypothesis_frontier_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "blocked_movement_effect" in proc.stdout
    assert "ambiguous_evidence" in proc.stdout
    assert "single_hypothesis_ambiguous" in proc.stdout


def test_demo_blocked_movement_case() -> None:
    proc = _run_demo("--case", "blocked_movement_effect", "--report")
    assert "AB3 HYPOTHESIS FRONTIER REPORT" in proc.stdout
    assert "frontier_id=" in proc.stdout


def test_demo_effect_mismatch_case() -> None:
    proc = _run_demo("--case", "effect_mismatch", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frontier"]["fact_claimed"] is False


def test_demo_ambiguous_evidence_case() -> None:
    proc = _run_demo("--case", "ambiguous_evidence", "--report")
    assert "closure_status=AB3ClosureStatus.OPEN" in proc.stdout


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--case", "hidden_eval_only", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frontier"] is None
    assert payload["telemetry"]["unsafe_basis_count"] >= 1


def test_demo_single_hypothesis_blocked_case() -> None:
    proc = _run_demo("--case", "single_hypothesis_ambiguous", "--report")
    assert "closure_status=AB3ClosureStatus.BLOCKED" in proc.stdout


def test_demo_json_output() -> None:
    proc = _run_demo("--case", "blocked_movement_effect", "--json")
    payload = json.loads(proc.stdout)
    assert "frontier" in payload
    assert "telemetry" in payload


def test_demo_report_does_not_claim_fact_cause_consciousness_full_abduction() -> None:
    proc = _run_demo("--case", "effect_mismatch", "--report")
    lowered = proc.stdout.lower()
    assert "cause confirmed" not in lowered
    assert "consciousness proven" not in lowered
    assert "full abduction proven" not in lowered
    assert "final explanation" not in lowered
