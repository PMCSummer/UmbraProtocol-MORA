from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKER_DIR = REPO_ROOT / "tracker"
ROADMAP_PATH = TRACKER_DIR / "UmbraProtocol_MORA_language_refactor.json"


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _existing_phase_code() -> str:
    raw = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    for item in raw.get("phases", []):
        code = str(item.get("code", "")).strip()
        if code:
            return code
    raise AssertionError("No phase codes found in roadmap")


def test_validate_smoke() -> None:
    cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "validate",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
    ]
    result = _run(cmd, cwd=REPO_ROOT)
    assert "schema_version:" in result.stdout
    assert "result:" in result.stdout
    assert result.returncode == 0


def test_show_and_todo_smoke() -> None:
    code = _existing_phase_code()
    show_cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "show",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--code",
        code,
    ]
    todo_cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "todo",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--code",
        code,
    ]
    show_result = _run(show_cmd, cwd=REPO_ROOT)
    todo_result = _run(todo_cmd, cwd=REPO_ROOT)
    assert show_result.returncode == 0
    assert todo_result.returncode == 0
    show_payload = json.loads(show_result.stdout)
    todo_payload = json.loads(todo_result.stdout)
    assert show_payload.get("code") == code
    assert todo_payload.get("code") == code


def test_add_phase_dry_run_does_not_modify_real_roadmap() -> None:
    before = _sha256(ROADMAP_PATH)
    cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "add-phase",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--code",
        "CLI_SMOKE_PHASE",
        "--title",
        "CLI Smoke Phase",
        "--desc",
        "Temporary dry-run phase for CLI smoke validation.",
        "--track",
        "build",
        "--line",
        "tooling",
        "--status",
        "later",
    ]
    result = _run(cmd, cwd=REPO_ROOT)
    after = _sha256(ROADMAP_PATH)
    assert result.returncode == 0
    assert before == after
    assert "dry_run:" in result.stdout


def test_duplicate_code_is_rejected() -> None:
    code = _existing_phase_code()
    cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "add-phase",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--code",
        code,
        "--title",
        "Duplicate",
        "--desc",
        "Duplicate code check.",
    ]
    result = _run(cmd, cwd=REPO_ROOT)
    assert result.returncode != 0
    assert "Duplicate phase code" in result.stderr


def test_add_phase_write_modifies_temp_copy_and_creates_backup(tmp_path: Path) -> None:
    roadmap_tmp = tmp_path / "roadmap.json"
    roadmap_tmp.write_bytes(ROADMAP_PATH.read_bytes())
    before = _sha256(roadmap_tmp)
    cmd = [
        sys.executable,
        str(TRACKER_DIR / "roadmap_cli.py"),
        "add-phase",
        "--roadmap",
        str(roadmap_tmp),
        "--code",
        "CLI_SMOKE_PHASE_WRITE",
        "--title",
        "CLI Smoke Write",
        "--desc",
        "Temporary write phase for CLI smoke validation.",
        "--write",
    ]
    result = _run(cmd, cwd=REPO_ROOT)
    after = _sha256(roadmap_tmp)
    backups = list(tmp_path.glob("roadmap.json.bak.*"))
    assert result.returncode == 0
    assert before != after
    assert backups


def test_bulk_add_dry_run_and_duplicate_input_rejection(tmp_path: Path) -> None:
    valid_input = tmp_path / "bulk_valid.json"
    valid_input.write_text(
        json.dumps(
            [
                {
                    "code": "CLI_BULK_1",
                    "title": "CLI Bulk 1",
                    "desc": "Bulk dry-run entry 1.",
                },
                {
                    "code": "CLI_BULK_2",
                    "title": "CLI Bulk 2",
                    "desc": "Bulk dry-run entry 2.",
                    "conceptually_after": ["P18"],
                },
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    dry_cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "bulk-add",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--input",
        str(valid_input),
    ]
    dry_result = _run(dry_cmd, cwd=REPO_ROOT)
    assert dry_result.returncode == 0
    assert "dry_run:" in dry_result.stdout

    dup_input = tmp_path / "bulk_dup.json"
    dup_input.write_text(
        json.dumps(
            [
                {"code": "CLI_DUP", "title": "Dup 1", "desc": "x"},
                {"code": "CLI_DUP", "title": "Dup 2", "desc": "y"},
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    dup_cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "bulk-add",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--input",
        str(dup_input),
    ]
    dup_result = _run(dup_cmd, cwd=REPO_ROOT)
    assert dup_result.returncode != 0
    assert "Duplicate code in input" in dup_result.stderr
