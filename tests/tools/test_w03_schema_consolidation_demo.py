from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "w03_schema_consolidation_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_w03_demo_smoke_scenarios() -> None:
    for scenario in (
        "clean_kind_prior",
        "contested_regularities_block_prior",
        "scaffold_only_deferred",
        "authority_scope_narrow",
        "revoked_authority_revalidate",
        "context_transfer_failure",
        "contradiction_downgrades",
        "contradictory_affordance_worlds_split",
        "stale_schema_revalidation",
        "language_prior_rejected",
        "operational_default_clean_path",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "W03 SCHEMA CONSOLIDATION DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout
