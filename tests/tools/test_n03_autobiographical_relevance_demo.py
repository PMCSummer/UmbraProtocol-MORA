from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "n03_autobiographical_relevance_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_n03_demo_smoke_scenarios() -> None:
    for scenario in (
        "semantic_similarity_only",
        "recovery_pattern",
        "single_episode_overgeneralization",
        "identity_drift_blocks_transfer",
        "affordance_change_blocks_transfer",
        "conflicting_traces",
        "commitment_anchor",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "N03 AUTOBIOGRAPHICAL RELEVANCE DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout
