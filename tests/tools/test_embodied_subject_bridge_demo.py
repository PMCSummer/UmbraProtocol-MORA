from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "embodied_subject_bridge_demo.py"), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_demo_lists_scenarios() -> None:
    result = _run("--list-scenarios")
    assert result.returncode == 0, result.stderr
    assert "empty_room_presence" in result.stdout
    assert "blocked_movement_wall" in result.stdout


def test_no_candidate_run_shows_no_execution() -> None:
    result = _run("--scenario", "empty_room_presence", "--ticks", "1")
    assert result.returncode == 0, result.stderr
    assert "subject_tick_used_any=True" in result.stdout
    assert "world_submissions=0" in result.stdout
    assert "autonomous_action_selection=False" in result.stdout


def test_manual_move_open_shows_succeeded_effect() -> None:
    result = _run(
        "--scenario",
        "open_movement_forward",
        "--manual-action",
        "move_forward",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert "effect=succeeded" in result.stdout


def test_blocked_wall_shows_blocked_effect() -> None:
    result = _run(
        "--scenario",
        "blocked_movement_wall",
        "--manual-action",
        "move_forward",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert "effect=blocked" in result.stdout


def test_pickup_shows_inventory_effect_and_feedback() -> None:
    result = _run(
        "--scenario",
        "visible_item_pickup_available",
        "--manual-action",
        "pickup",
        "--target",
        "item:water_flask",
        "--ticks",
        "2",
        "--json",
    )
    assert result.returncode == 0, result.stderr
    assert '"inventory_delta"' in result.stdout
    assert '"observation_previous_effect_refs"' in result.stdout


def test_json_eval_scope_is_opt_in() -> None:
    default_json = _run(
        "--scenario",
        "hidden_map_not_visible",
        "--ticks",
        "1",
        "--json",
    )
    assert default_json.returncode == 0, default_json.stderr
    assert '"eval_only"' not in default_json.stdout

    eval_json = _run(
        "--scenario",
        "hidden_map_not_visible",
        "--ticks",
        "1",
        "--json",
        "--include-eval-only",
    )
    assert eval_json.returncode == 0, eval_json.stderr
    assert '"eval_only"' in eval_json.stdout


def test_demo_does_not_claim_autonomous_action_selection() -> None:
    result = _run(
        "--scenario",
        "open_movement_forward",
        "--manual-action",
        "move_forward",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert "autonomous_action_selection=False" in result.stdout


def test_internal_candidate_mode_runs_without_manual_provider() -> None:
    result = _run(
        "--scenario",
        "visible_item_pickup_available",
        "--internal-candidate",
        "--drive",
        "water_need",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert "internal_candidate_mode=True" in result.stdout
    assert "manual_candidate_input=False" in result.stdout
