from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "embodied_causal_necessity_demo.py"), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_demo_lists_ablations() -> None:
    result = _run("--list-ablations")
    assert result.returncode == 0, result.stderr
    assert "no_acp01" in result.stdout
    assert "hidden_eval_substitution_attempt" in result.stdout


def test_demo_no_acp01_report() -> None:
    result = _run(
        "--scenario",
        "visible_item_pickup_available",
        "--ablation",
        "no_acp01",
        "--strict",
        "--report",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert "id=no_acp01" in result.stdout
    assert "degradation_observed=True" in result.stdout


def test_demo_no_ap01_json() -> None:
    result = _run(
        "--scenario",
        "visible_item_pickup_available",
        "--ablation",
        "no_ap01",
        "--strict",
        "--json",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert '"ablation_id": "no_ap01"' in result.stdout


def test_demo_hidden_eval_substitution_attempt_json() -> None:
    result = _run(
        "--scenario",
        "hidden_map_not_visible",
        "--ablation",
        "hidden_eval_substitution_attempt",
        "--strict",
        "--json",
        "--ticks",
        "1",
    )
    assert result.returncode == 0, result.stderr
    assert '"ablation_id": "hidden_eval_substitution_attempt"' in result.stdout


def test_demo_matrix_json() -> None:
    result = _run("--matrix", "--json", "--strict", "--ticks", "1")
    assert result.returncode == 0, result.stderr
    assert '"ablation_id": "no_acp01"' in result.stdout
    assert '"ablation_id": "no_ap01"' in result.stdout


def test_demo_report_does_not_overclaim() -> None:
    result = _run("--matrix", "--strict", "--report", "--ticks", "1")
    assert result.returncode == 0, result.stderr
    lowered = result.stdout.lower()
    assert "consciousness proven" not in lowered
    assert "general autonomy proven" not in lowered
