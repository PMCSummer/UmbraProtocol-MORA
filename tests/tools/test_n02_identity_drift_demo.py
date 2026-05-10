from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "n02_identity_drift_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_n02_demo_smoke_scenarios() -> None:
    for scenario in (
        "stable_continuation",
        "bounded_revision",
        "gradual_shift",
        "abrupt_reorientation",
        "context_split",
        "text_diff_only",
        "silent_rewrite",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "N02 IDENTITY DRIFT REFLECTION DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "gate=" in result.stdout
