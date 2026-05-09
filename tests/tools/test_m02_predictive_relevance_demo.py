from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "m02_predictive_relevance_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_m02_demo_smoke_scenarios() -> None:
    for scenario in (
        "boring_predictive",
        "repetition_only",
        "vivid_non_predictive",
        "context_locked",
        "spurious",
        "m01_separation",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "M02 PREDICTIVE RELEVANCE DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout

