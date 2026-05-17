from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "embodied_baseline_competition_demo.py"), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_demo_lists_baselines() -> None:
    result = _run("--list-baselines")
    assert result.returncode == 0, result.stderr
    assert "baseline:random_action" in result.stdout
    assert "baseline:hidden_oracle" in result.stdout


def test_demo_lists_scenarios() -> None:
    result = _run("--list-scenarios")
    assert result.returncode == 0, result.stderr
    assert "visible_flask_no_drive" in result.stdout
    assert "hidden_map_not_visible" in result.stdout


def test_demo_normal_run() -> None:
    result = _run(
        "--scenario",
        "visible_item_pickup_available",
        "--drive",
        "water_need",
        "--ticks",
        "2",
    )
    assert result.returncode == 0, result.stderr
    assert "mora: subject_tick=True" in result.stdout
    assert "does not prove consciousness or general autonomy" in result.stdout.lower()


def test_demo_json_run() -> None:
    result = _run(
        "--scenario",
        "action_space_only_no_candidate",
        "--ticks",
        "1",
        "--json",
    )
    assert result.returncode == 0, result.stderr
    assert '"metric_summary"' in result.stdout


def test_demo_hidden_oracle_and_direct_bridge_marked() -> None:
    result = _run(
        "--scenario",
        "hidden_map_not_visible",
        "--drive",
        "water_need",
        "--include-hidden-oracle",
        "--include-direct-bridge",
        "--json",
    )
    assert result.returncode == 0, result.stderr
    assert '"hidden_oracle_marked_unfair": true' in result.stdout.lower()
    assert '"direct_bridge_marked_bypass": true' in result.stdout.lower()


def test_demo_visible_no_drive_shows_mora_restraint() -> None:
    result = _run("--scenario", "visible_flask_no_drive", "--ticks", "1", "--report")
    assert result.returncode == 0, result.stderr
    assert "ap01_published_count: 0" in result.stdout
    assert "world_submission_count: 0" in result.stdout


def test_matrix_json_output_contains_required_sections() -> None:
    result = _run("--matrix", "--json")
    assert result.returncode == 0, result.stderr
    assert '"scenario_runs"' in result.stdout
    assert '"scenario_id": "visible_flask_no_drive"' in result.stdout


def test_matrix_report_output_mentions_fairness_and_boundary() -> None:
    result = _run("--matrix", "--report")
    assert result.returncode == 0, result.stderr
    assert "fairness matched=" in result.stdout.lower()
    assert "boundary ap01_bypass=" in result.stdout.lower()


def test_hidden_oracle_is_reported_unfair_in_matrix() -> None:
    result = _run("--matrix", "--include-hidden-oracle", "--json")
    assert result.returncode == 0, result.stderr
    assert '"hidden_oracle_marked_unfair": true' in result.stdout.lower()


def test_direct_bridge_is_reported_ap01_bypass_in_matrix() -> None:
    result = _run("--matrix", "--include-direct-bridge", "--json")
    assert result.returncode == 0, result.stderr
    assert '"direct_bridge_marked_bypass": true' in result.stdout.lower()


def test_report_does_not_claim_consciousness_or_general_autonomy() -> None:
    result = _run("--matrix", "--report")
    assert result.returncode == 0, result.stderr
    lowered = result.stdout.lower()
    assert "proves consciousness" not in lowered
    assert "general autonomy proven" not in lowered
