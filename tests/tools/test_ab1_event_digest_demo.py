from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab1_event_digest_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "blocked_movement_effect" in proc.stdout
    assert "hidden_eval_only" in proc.stdout


def test_demo_blocked_movement_case_report() -> None:
    proc = _run_demo("--case", "blocked_movement_effect", "--report")
    assert "AB1 EVENT DIGEST REPORT" in proc.stdout
    assert "kind=unexpected_block" in proc.stdout


def test_demo_effect_mismatch_case_json() -> None:
    proc = _run_demo("--case", "effect_mismatch", "--json")
    payload = json.loads(proc.stdout)
    assert payload["digests"][0]["event_kind"] == "effect_mismatch"


def test_demo_hidden_eval_case_json() -> None:
    proc = _run_demo("--case", "hidden_eval_only", "--json")
    payload = json.loads(proc.stdout)
    assert payload["digests"] == []
    assert payload["telemetry"]["unsafe_basis_count"] >= 1


def test_demo_report_does_not_claim_cause_explanation_consciousness() -> None:
    proc = _run_demo("--case", "blocked_movement_effect", "--report")
    lowered = proc.stdout.lower()
    assert "cause confirmed" not in lowered
    assert "consciousness" not in lowered
    assert "explanation frontier" not in lowered
