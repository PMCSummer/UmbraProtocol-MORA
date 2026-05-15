from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "w04_applicability_gating_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_w04_demo_smoke_scenarios() -> None:
    for scenario in (
        "clean_allowed_bounded_prior",
        "w03_must_revalidate_blocks_clean_deploy",
        "stale_prior_revalidation",
        "hard_world_constraint_blocks",
        "soft_constraint_relaxes_with_ledger",
        "hard_constraint_cannot_relax",
        "empty_intersection_blocks",
        "authority_scope_mismatch",
        "perspective_transfer_blocked",
        "malformed_desired_state_rejected",
        "unknown_hard_feasibility_revalidates",
        "applicability_not_action_authorization",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "W04 APPLICABILITY GATING DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout
