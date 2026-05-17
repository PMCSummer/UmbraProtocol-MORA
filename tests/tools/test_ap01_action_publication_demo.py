from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "ap01_action_publication_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_ap01_demo_smoke_scenarios() -> None:
    scenarios = (
        "valid_move",
        "valid_inspect",
        "valid_use_station",
        "desired_only_rejected",
        "affordance_only_rejected",
        "scenario_hidden_eval_rejected",
    )
    for scenario in scenarios:
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "AP01 ACTION PUBLICATION DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "telemetry=" in result.stdout
        assert "decision=" in result.stdout


def test_ap01_demo_published_request_is_not_execution() -> None:
    result = _run_scenario("valid_use_station")
    assert result.returncode == 0, result.stderr
    assert "execution_boundary=external_world_only" in result.stdout
    assert "executed_by_subject=False" in result.stdout
    assert "world_execution_status=not_executed_by_subject" in result.stdout
    assert "must_wait_for_world_effect=True" in result.stdout
