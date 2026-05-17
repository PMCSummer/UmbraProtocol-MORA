from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "embodied_grid_world_demo.py"), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_demo_lists_scenarios() -> None:
    result = _run("--list-scenarios")
    assert result.returncode == 0, result.stderr
    assert "blocked_movement_wall" in result.stdout
    assert "visible_item_pickup_available" in result.stdout


def test_blocked_wall_demo_shows_blocked_effect() -> None:
    result = _run("--scenario", "blocked_movement_wall", "--action", "move_forward")
    assert result.returncode == 0, result.stderr
    assert "effect_status=blocked" in result.stdout.lower()


def test_pickup_demo_shows_inventory_delta_via_effect() -> None:
    result = _run(
        "--scenario",
        "visible_item_pickup_available",
        "--action",
        "pickup",
        "--target",
        "item:water_flask",
    )
    assert result.returncode == 0, result.stderr
    assert "inventory_before" in result.stdout
    assert "inventory_after" in result.stdout


def test_hidden_map_demo_excludes_eval_by_default_and_shows_with_flag() -> None:
    default_json = _run("--scenario", "hidden_map_not_visible", "--json")
    assert default_json.returncode == 0, default_json.stderr
    assert '"eval_only"' not in default_json.stdout

    eval_json = _run("--scenario", "hidden_map_not_visible", "--json", "--show-eval-only")
    assert eval_json.returncode == 0, eval_json.stderr
    assert '"eval_only"' in eval_json.stdout
