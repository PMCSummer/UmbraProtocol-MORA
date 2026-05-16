from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "symbolic_trade_gui.py"), *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_symbolic_trade_gui_help() -> None:
    result = _run("--help")
    assert result.returncode == 0, result.stderr
    assert "--scenario" in result.stdout
    assert "--execute-world-actuator" in result.stdout
    assert "--dev-mode" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--timeline-dry-run" in result.stdout


def test_symbolic_trade_gui_dry_run_successful_noexec() -> None:
    result = _run("--scenario", "successful_scripted_exchange_cycle", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "SYMBOLIC TRADE GUI DRY RUN" in result.stdout
    assert "world_actuator_invoked=False" in result.stdout
    assert "transfer_result=not_attempted" in result.stdout
    assert "completion_claim=False" in result.stdout


def test_symbolic_trade_gui_dry_run_successful_exec() -> None:
    result = _run(
        "--scenario",
        "successful_scripted_exchange_cycle",
        "--execute-world-actuator",
        "--dry-run",
    )
    assert result.returncode == 0, result.stderr
    assert "world_actuator_invoked=True" in result.stdout
    assert "transfer_result=succeeded" in result.stdout
    assert "completion_claim=True" in result.stdout


def test_symbolic_trade_gui_dry_run_blocked_aperture_stays_noninvoked() -> None:
    result = _run(
        "--scenario",
        "blocked_aperture",
        "--execute-world-actuator",
        "--dry-run",
    )
    assert result.returncode == 0, result.stderr
    assert "world_actuator_invoked=False" in result.stdout
    assert "completion_claim=False" in result.stdout


def test_symbolic_trade_gui_dev_mode_eval_only_exposed_only_with_flag() -> None:
    no_eval = _run(
        "--scenario",
        "successful_scripted_exchange_cycle",
        "--execute-world-actuator",
        "--dev-mode",
        "--dry-run",
    )
    assert no_eval.returncode == 0, no_eval.stderr
    assert "developer_payload_json=" in no_eval.stdout
    assert "\"eval_only\"" not in no_eval.stdout

    with_eval = _run(
        "--scenario",
        "successful_scripted_exchange_cycle",
        "--execute-world-actuator",
        "--dev-mode",
        "--include-eval-only",
        "--dry-run",
    )
    assert with_eval.returncode == 0, with_eval.stderr
    assert "developer_payload_json=" in with_eval.stdout
    assert "\"eval_only\"" in with_eval.stdout


def test_symbolic_trade_gui_timeline_dry_run_prints_steps() -> None:
    result = _run(
        "--scenario",
        "successful_scripted_exchange_cycle",
        "--timeline-dry-run",
    )
    assert result.returncode == 0, result.stderr
    assert "timeline_steps=" in result.stdout
    assert "scenario_loaded" in result.stdout
    assert "completion_verified_or_rejected" in result.stdout


def test_symbolic_trade_gui_launch_path_handles_missing_pyside6_gracefully() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    code = (
        "import experiments.symbolic_trade.gui_app as a; "
        "a._load_qt=lambda:None; "
        "rc=a.run_symbolic_trade_gui(scenario='successful_scripted_exchange_cycle', execute_world_actuator=False, dev_mode=False); "
        "print('rc='+str(rc))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "PySide6 is required for this GUI" in result.stdout
    assert "rc=2" in result.stdout
