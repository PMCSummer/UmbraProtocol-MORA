from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "n01_narrative_commitment_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_n01_demo_smoke_scenarios() -> None:
    for scenario in (
        "statement_only",
        "grounded_state_commitment",
        "ungrounded_capability",
        "grounded_limitation",
        "contradiction",
        "invalidated_basis",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "N01 NARRATIVE COMMITMENT DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "record=" in result.stdout
        assert "gate=" in result.stdout
