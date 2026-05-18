from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/ab6_causal_attribution_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_list_cases() -> None:
    proc = _run_demo("--list-cases")
    assert "self_action_correlated_effect" in proc.stdout
    assert "hidden_eval_only_cause" in proc.stdout


def test_demo_self_action_case() -> None:
    proc = _run_demo("--case", "self_action_correlated_effect", "--report")
    assert "AB6 CAUSAL ATTRIBUTION REPORT" in proc.stdout
    assert "attribution_frame_id=" in proc.stdout


def test_demo_world_only_case() -> None:
    proc = _run_demo("--case", "world_only_change", "--json")
    payload = json.loads(proc.stdout)
    assert "self_action" in payload["frame"]["blocked_attribution_kinds"]


def test_demo_other_actor_case() -> None:
    proc = _run_demo("--case", "other_actor_change", "--report")
    assert "other_actor" in proc.stdout


def test_demo_mixed_case() -> None:
    proc = _run_demo("--case", "mixed_self_world_effect", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frame"]["mixed_cause_preserved"] is True


def test_demo_unknown_case() -> None:
    proc = _run_demo("--case", "unknown_unexplained_effect", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frame"]["unknown_preserved"] is True


def test_demo_hidden_eval_case() -> None:
    proc = _run_demo("--case", "hidden_eval_only_cause", "--json")
    payload = json.loads(proc.stdout)
    assert payload["frame"] is None
    assert "hidden_eval_exclusion_required" in payload["reason_codes"]


def test_demo_report_does_not_claim_full_self_model_consciousness_final_cause() -> None:
    proc = _run_demo("--case", "self_action_correlated_effect", "--report")
    lowered = proc.stdout.lower()
    assert "full self-model proven" not in lowered
    assert "consciousness proven" not in lowered
    assert "final cause confirmed" not in lowered
