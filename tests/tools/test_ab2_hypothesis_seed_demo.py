from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab2_hypothesis_seed_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "blocked_movement_effect" in proc.stdout
    assert "hidden_eval_only" in proc.stdout
    assert "no_event_digest" in proc.stdout


def test_demo_blocked_movement_case() -> None:
    proc = _run_demo("--case", "blocked_movement_effect", "--report", "--show-hypotheses")
    assert "AB2 HYPOTHESIS SEED REPORT" in proc.stdout
    assert "hypothesis_count=" in proc.stdout


def test_demo_effect_mismatch_case() -> None:
    proc = _run_demo("--case", "effect_mismatch", "--json")
    payload = json.loads(proc.stdout)
    assert payload["seed_set"]["seed_set_id"].startswith("ab2:")
    assert payload["seed_set"]["fact_claimed"] is False


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--case", "hidden_eval_only", "--json")
    payload = json.loads(proc.stdout)
    assert payload["seed_set"] is None
    assert payload["telemetry"]["unsafe_basis_count"] >= 1


def test_demo_no_digest_case() -> None:
    proc = _run_demo("--case", "no_event_digest", "--report")
    assert "seed_set=None" in proc.stdout


def test_demo_json_output() -> None:
    proc = _run_demo("--case", "blocked_movement_effect", "--json")
    payload = json.loads(proc.stdout)
    assert "seed_set" in payload
    assert "telemetry" in payload


def test_demo_report_does_not_claim_fact_cause_consciousness_general_abduction() -> None:
    proc = _run_demo("--case", "effect_mismatch", "--report")
    lowered = proc.stdout.lower()
    assert "cause confirmed" not in lowered
    assert "proves consciousness" not in lowered
    assert "consciousness proven" not in lowered
    assert "general reasoning proven" not in lowered
    assert "full abduction proven" not in lowered
    assert "final explanation" not in lowered
