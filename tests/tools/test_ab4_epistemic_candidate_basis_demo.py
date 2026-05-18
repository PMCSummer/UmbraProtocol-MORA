from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab4_epistemic_candidate_basis_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "open_frontier_inspect" in proc.stdout
    assert "no_discriminating_test" in proc.stdout


def test_demo_open_frontier_case() -> None:
    proc = _run_demo("--case", "open_frontier_inspect", "--report")
    assert "AB4 EPISTEMIC CANDIDATE BASIS REPORT" in proc.stdout
    assert "basis_id=" in proc.stdout


def test_demo_ambiguous_frontier_case() -> None:
    proc = _run_demo("--case", "ambiguous_frontier_wait", "--json")
    payload = json.loads(proc.stdout)
    assert payload["result"]["bases"]


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--case", "hidden_eval_only", "--json")
    payload = json.loads(proc.stdout)
    assert payload["result"]["bases"] == []
    assert "hidden_eval_exclusion_required" in payload["result"]["reason_codes"]


def test_demo_no_frontier_case() -> None:
    proc = _run_demo("--case", "no_frontier", "--report")
    assert "reason_codes=('frontier_required'" in proc.stdout or "frontier_required" in proc.stdout


def test_demo_no_discriminating_test_case() -> None:
    proc = _run_demo("--case", "no_discriminating_test", "--report")
    assert "basis_count=0" in proc.stdout


def test_demo_json_output() -> None:
    proc = _run_demo("--case", "open_frontier_inspect", "--json")
    payload = json.loads(proc.stdout)
    assert "result" in payload
    assert "telemetry" in payload["result"]


def test_demo_report_does_not_claim_active_inference_fact_cause_consciousness() -> None:
    proc = _run_demo("--case", "open_frontier_inspect", "--report")
    lowered = proc.stdout.lower()
    assert "full active inference proven" not in lowered
    assert "cause confirmed" not in lowered
    assert "consciousness proven" not in lowered
