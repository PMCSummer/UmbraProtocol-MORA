from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REQUIRED_SCENARIOS = (
    "presence_only",
    "resource_claim_contact",
    "mirrored_resource_asymmetry",
    "false_counterpart_claim",
    "blocked_aperture",
    "noisy_signal",
    "transfer_seen_without_trade_token",
    "eval_label_leak_attack",
)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "symbolic_trade_experiment.py"), *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_symbolic_trade_cli_list_scenarios() -> None:
    result = _run("--list-scenarios")
    assert result.returncode == 0, result.stderr
    for scenario in REQUIRED_SCENARIOS:
        assert scenario in result.stdout


def test_symbolic_trade_cli_smoke_scenarios() -> None:
    for scenario in REQUIRED_SCENARIOS:
        result = _run("--scenario", scenario, "--run-falsifiers")
        assert result.returncode == 0, result.stderr
        assert "SYMBOLIC TRADE HARNESS" in result.stdout
        assert f"scenario_id={scenario}" in result.stdout
        assert "packet_count=" in result.stdout
        assert "falsifier_summary=" in result.stdout
        assert "claim_discipline_markers=" in result.stdout


def test_symbolic_trade_cli_json_output_contains_required_fields() -> None:
    result = _run("--scenario", "mirrored_resource_asymmetry", "--json", "--run-falsifiers")
    assert result.returncode == 0, result.stderr
    assert '"scenario_id": "mirrored_resource_asymmetry"' in result.stdout
    assert '"packet_count"' in result.stdout
    assert '"falsifier_results"' in result.stdout
    assert '"claim_discipline_markers"' in result.stdout
