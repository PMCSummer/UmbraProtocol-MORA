from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab_live_subject_tick_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "public_effect_mismatch_creates_digest_seed_frontier" in proc.stdout
    assert "disabled_ab_live_preserves_subject_tick_behavior" in proc.stdout


def test_demo_digest_frontier_case() -> None:
    proc = _run_demo("--case", "public_effect_mismatch_creates_digest_seed_frontier", "--report")
    assert "AB LIVE SUBJECT_TICK CONTOUR REPORT" in proc.stdout
    assert "ab1=" in proc.stdout
    assert "ab3=" in proc.stdout


def test_demo_update_case_json() -> None:
    proc = _run_demo("--case", "prior_frontier_correlated_effect_updates_support", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ab5_update_refs"]


def test_demo_attribution_case_json() -> None:
    proc = _run_demo("--case", "ap01_effect_creates_bounded_attribution", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ab6_attribution_refs"]


def test_demo_epistemic_basis_case_report() -> None:
    proc = _run_demo("--case", "open_frontier_creates_epistemic_basis_before_acp01", "--report", "--show-epistemic-basis")
    assert "epistemic_basis_refs=" in proc.stdout


def test_demo_recipe_constraint_case_json() -> None:
    proc = _run_demo("--case", "recipe_candidate_creates_ab7_constraints", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ab7_constraint_refs"]
    assert payload["automation_claimed"] is False


def test_demo_protected_evaluator_only_case_json() -> None:
    proc = _run_demo("--case", "protected_eval_input_blocked", "--json")
    payload = json.loads(proc.stdout)
    assert "protected_eval_present" in payload["blocked_reasons"]
    assert payload["hidden_eval_used"] is False


def test_demo_disabled_mode_case_report() -> None:
    proc = _run_demo("--case", "disabled_ab_live_preserves_subject_tick_behavior", "--report")
    assert "ab1=0" in proc.stdout


def test_demo_repeated_ticks_case_json() -> None:
    proc = _run_demo("--case", "repeated_ticks_without_new_evidence", "--ticks", "5", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ab_live_counters"]["performance_guard_triggered_count"] == 0


def test_demo_json_output_contains_authority_flags_and_no_overclaim() -> None:
    proc = _run_demo("--case", "public_effect_mismatch_creates_digest_seed_frontier", "--json")
    payload = json.loads(proc.stdout)
    assert payload["fact_claimed"] is False
    assert payload["cause_confirmed"] is False
    assert payload["action_request_emitted"] is False
    assert payload["world_submission_emitted"] is False
    assert payload["automation_claimed"] is False
    assert payload["mature_recipe_claimed"] is False


def test_demo_report_does_not_overclaim() -> None:
    proc = _run_demo("--case", "public_effect_mismatch_creates_digest_seed_frontier", "--report")
    lowered = proc.stdout.lower()
    assert "consciousness proven" not in lowered
    assert "full autonomous reasoning" not in lowered
    assert "mature automation achieved" not in lowered
