from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_scenario(scenario: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools" / "w02_regularity_extraction_demo.py"),
            "--scenario",
            scenario,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_w02_demo_smoke_scenarios() -> None:
    for scenario in (
        "single_trace_blocked",
        "recurrent_scaffold",
        "persistent_instance_candidate",
        "same_kind_not_same_instance",
        "duplicate_vs_continuity",
        "replacement_vs_continuity",
        "scaffold_only_blocks_promotion",
        "contradiction_downgrades",
        "affordance_requires_action_effect_linkage",
        "provider_bias_blocked",
    ):
        result = _run_scenario(scenario)
        assert result.returncode == 0, result.stderr
        assert "W02 REGULARITY EXTRACTION DEMO" in result.stdout
        assert f"scenario={scenario}" in result.stdout
        assert "consumer_flags=" in result.stdout
