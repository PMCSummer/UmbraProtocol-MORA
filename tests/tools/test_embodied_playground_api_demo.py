from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "embodied_playground_api_demo.py"), *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_demo_runs_and_prints_boundaries() -> None:
    result = _run()
    assert result.returncode == 0, result.stderr
    assert "EMBODIED PLAYGROUND API DEMO" in result.stdout
    assert "boundary_claims=request!=execution;request!=success;request!=completion" in result.stdout
    assert "effect_status=" in result.stdout
    assert "correlation_status=" in result.stdout
    assert "success achieved" not in result.stdout.lower()


def test_demo_json_contains_observation_action_space_envelope_effect() -> None:
    result = _run("--json")
    assert result.returncode == 0, result.stderr
    assert "\"observation\"" in result.stdout
    assert "\"action_space\"" in result.stdout
    assert "\"published_envelope\"" in result.stdout
    assert "\"effect\"" in result.stdout
    assert "\"public_snapshot\"" in result.stdout
