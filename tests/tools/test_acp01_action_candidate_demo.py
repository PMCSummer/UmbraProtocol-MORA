from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(case_id: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "acp01_action_candidate_demo.py"), "--case", case_id, *extra],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_no_drive_visible_item_no_candidate() -> None:
    result = _run("visible-item-no-drive")
    assert result.returncode == 0, result.stderr
    assert "candidate_count=0" in result.stdout
    assert "world_execution=False" in result.stdout


def test_full_basis_pickup_candidate_proposed() -> None:
    result = _run("water-drive-visible-flask")
    assert result.returncode == 0, result.stderr
    assert "action_kind=pickup" in result.stdout
    assert "execution_boundary=candidate_only" in result.stdout


def test_capacity_blocked_no_pickup_publication() -> None:
    result = _run("capacity-blocked")
    assert result.returncode == 0, result.stderr
    assert "action_kind=pickup" not in result.stdout
    assert "ap01_candidate_set_ready=False" in result.stdout


def test_private_eval_object_no_candidate() -> None:
    result = _run("hidden-eval-object")
    assert result.returncode == 0, result.stderr
    assert "unsafe_basis" in result.stdout
    assert "candidate_count=0" in result.stdout


def test_action_space_only_case_json() -> None:
    result = _run("action-space-only", "--json")
    assert result.returncode == 0, result.stderr
    assert '"proposal": null' in result.stdout
    assert '"world_execution=False"' not in result.stdout  # plain marker only in text section
