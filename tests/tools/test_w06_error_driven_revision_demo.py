from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "w06_error_driven_revision_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_w06_demo_smoke_scenarios() -> None:
    for scenario in (
        "clean_local_downgrade_from_world_model_mismatch",
        "contradiction_blocks_claim",
        "repeated_revalidation_triggers_anti_paralysis",
        "identity_split_candidate",
        "correction_candidate_not_executed",
        "local_error_not_global_invalidation",
        "confidence_drop_precision_sensitive",
        "protected_target_escalates",
        "residual_uncertainty_preserved_after_downgrade",
        "ambiguous_mismatch_retains_competing_routes",
        "claim_block_propagates_to_downstream",
        "decorative_contradiction_forbidden",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "W06 ERROR-DRIVEN REVISION DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout
