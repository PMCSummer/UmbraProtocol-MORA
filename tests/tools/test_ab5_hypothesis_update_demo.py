from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab5_hypothesis_update_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "correlated_effect_support_increase" in proc.stdout
    assert "hidden_eval_effect_rejected" in proc.stdout


def test_demo_correlated_effect_case() -> None:
    proc = _run_demo("--case", "correlated_effect_support_increase", "--report")
    assert "AB5 HYPOTHESIS UPDATE REPORT" in proc.stdout
    assert "update_id=" in proc.stdout


def test_demo_disconfirming_effect_case() -> None:
    proc = _run_demo("--case", "disconfirming_effect_support_decrease", "--json")
    payload = json.loads(proc.stdout)
    assert payload["update"]["disconfirmed_hypothesis_refs"] or payload["update"]["weakened_hypothesis_refs"]


def test_demo_ambiguous_effect_case() -> None:
    proc = _run_demo("--case", "ambiguous_effect_no_closure", "--report")
    assert "closure_allowed=False" in proc.stdout


def test_demo_request_only_case() -> None:
    proc = _run_demo("--case", "request_alone_no_confirmation", "--json")
    payload = json.loads(proc.stdout)
    assert payload["update"]["support_deltas"] == []
    assert payload["update"]["closure_blocked_reason"] == "request_without_effect_not_confirmation"


def test_demo_uncorrelated_effect_case() -> None:
    proc = _run_demo("--case", "uncorrelated_effect_weak_or_blocked_update", "--json")
    payload = json.loads(proc.stdout)
    assert all(item["delta_kind"] != "increase" for item in payload["update"]["support_deltas"])


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--case", "hidden_eval_effect_rejected", "--json")
    payload = json.loads(proc.stdout)
    assert payload["update"] is None
    assert "hidden_eval_exclusion_required" in payload["reason_codes"]


def test_demo_report_does_not_claim_cause_fact_consciousness_full_abduction() -> None:
    proc = _run_demo("--case", "correlated_effect_support_increase", "--report")
    lowered = proc.stdout.lower()
    assert "cause confirmed" not in lowered
    assert "fact selected" not in lowered
    assert "consciousness proven" not in lowered
    assert "full abduction proven" not in lowered
