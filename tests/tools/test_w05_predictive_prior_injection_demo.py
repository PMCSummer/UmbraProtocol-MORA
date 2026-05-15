from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "w05_predictive_prior_injection_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_w05_demo_smoke_scenarios() -> None:
    for scenario in (
        "clean_prior_injection",
        "w04_block_prevents_injection",
        "w04_revalidate_routes_revalidation",
        "permitted_false_blocks_predicted_utility",
        "desired_not_evidence",
        "high_precision_observation_suppresses_prior",
        "low_precision_noise_contested",
        "weak_source_reduces_gain",
        "ambiguous_mismatch_revalidates",
        "constitutional_guard_blocks_update",
        "protected_target_escalates",
        "routing_not_execution",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "W05 PREDICTIVE PRIOR INJECTION DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout
