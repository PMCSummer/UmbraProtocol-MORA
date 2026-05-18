from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/embodied_body_action_demo.py", *args],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )


def test_demo_lists_scenarios() -> None:
    proc = _run_demo("--list-scenarios")
    assert "internal_move_forward_open" in proc.stdout
    assert "internal_drop_inventory_item" in proc.stdout


def test_demo_turn_report() -> None:
    proc = _run_demo("--scenario", "internal_turn_left_orientation_change", "--ticks", "2", "--report")
    assert "BODY ACTION PROOF REPORT (P10)" in proc.stdout
    assert "manual_provider_used=False" in proc.stdout


def test_demo_move_open_report() -> None:
    proc = _run_demo("--scenario", "internal_move_forward_open", "--ticks", "2", "--report")
    assert "effect_status=succeeded" in proc.stdout
    assert "policy=basis_persistent_repeat_allowed" in proc.stdout
    assert "stale_candidate_detected=False" in proc.stdout


def test_demo_move_blocked_json() -> None:
    proc = _run_demo("--scenario", "internal_move_forward_blocked_wall", "--ticks", "2", "--json")
    payload = json.loads(proc.stdout)
    assert payload["scenario_id"] == "internal_move_forward_blocked_wall"
    statuses = [item["effect_status"] for item in payload["step_summaries"] if item["effect_status"]]
    assert "blocked" in statuses


def test_demo_pickup_full_basis_report() -> None:
    proc = _run_demo("--scenario", "internal_pickup_visible_reachable_item", "--ticks", "2", "--report")
    assert "ap01_published=" in proc.stdout
    assert "world_submissions=" in proc.stdout


def test_demo_pickup_no_drive_json() -> None:
    proc = _run_demo("--scenario", "internal_pickup_no_drive_no_publish", "--ticks", "1", "--json")
    payload = json.loads(proc.stdout)
    assert payload["ap01_published_count"] == 0
    assert payload["world_submission_count"] == 0


def test_demo_repeated_move_json_has_fresh_refs() -> None:
    proc = _run_demo("--scenario", "internal_move_forward_open", "--ticks", "2", "--json")
    payload = json.loads(proc.stdout)
    submitted = [step for step in payload["step_summaries"] if step["world_submission_count"] > 0]
    assert len(submitted) == 2
    refs = [step["ap01_request_ref"] for step in submitted]
    assert all(refs)
    assert len(set(refs)) == len(refs)
    assert payload["stale_candidate_detected"] is False


def test_demo_drop_report() -> None:
    proc = _run_demo("--scenario", "internal_drop_inventory_item", "--ticks", "2", "--report")
    assert "inventory_delta" in proc.stdout
    assert "world_delta_public" in proc.stdout


def test_demo_report_does_not_overclaim() -> None:
    proc = _run_demo("--scenario", "internal_move_forward_open", "--ticks", "2", "--report")
    lowered = proc.stdout.lower()
    assert "proves consciousness" not in lowered
    assert "general autonomy proven" not in lowered
    assert "planning intelligence" not in lowered
