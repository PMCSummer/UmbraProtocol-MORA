from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKER_DIR = REPO_ROOT / "tracker"
if str(TRACKER_DIR) not in sys.path:
    sys.path.insert(0, str(TRACKER_DIR))

from roadmap_tracker.model import Phase, RoadmapModel


ROADMAP_PATH = TRACKER_DIR / "UmbraProtocol_MORA_language_refactor.json"


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def test_todo_preserves_existing_current_values() -> None:
    raw = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    model = RoadmapModel.from_json(raw)
    phase = model.get_phase("UMWELT0")
    assert phase is not None
    todo = phase.to_todo_dict()

    assert todo["spec"]["objective"]["current"] == (phase.spec or {}).get("objective", "")
    assert todo["risk_tags"]["current"] == phase.risk_tags
    assert todo["knowledge_card"]["functional_role"]["current"] == phase.knowledge_card.functional_role
    assert "todo" in todo["spec"]["objective"]
    assert "todo" in todo["risk_tags"]
    assert "todo" in todo["knowledge_card"]["functional_role"]


def test_todo_wraps_empty_fields_without_filling() -> None:
    phase = Phase.from_dict(
        {
            "code": "T_WRAP",
            "title": "Wrap Test",
            "spec": {},
            "notes": "",
            "risk_tags": [],
            "claim_blocked_by": [],
            "knowledge_card": {},
        }
    )
    todo = phase.to_todo_dict()
    assert todo["spec"]["objective"]["current"] == ""
    assert todo["spec"]["includes"]["current"] == []
    assert todo["notes"]["current"] == ""
    assert todo["risk_tags"]["current"] == []
    assert todo["knowledge_card"]["inputs"]["current"] == []
    assert todo["knowledge_card"]["authority"]["current"] == ""
    assert isinstance(todo["spec"]["objective"]["todo"], str) and todo["spec"]["objective"]["todo"]


def test_todo_metadata_fields_remain_direct_values() -> None:
    raw = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    model = RoadmapModel.from_json(raw)
    phase = model.get_phase("UMWELT0")
    assert phase is not None
    todo = phase.to_todo_dict()
    for key in [
        "code",
        "title",
        "track",
        "line",
        "after",
        "status",
        "status_source",
        "implemented_after",
        "conceptually_after",
        "validation_state",
        "claim_role",
        "priority_bucket",
        "claim_state",
        "maturity",
        "authority_role",
        "computational_role",
        "related_node_ids",
    ]:
        assert key in todo
        assert not (isinstance(todo[key], dict) and "current" in todo[key] and "todo" in todo[key])


def test_cli_todo_outputs_valid_json_with_wrapped_fields() -> None:
    cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "todo",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--code",
        "UMWELT0",
    ]
    result = _run(cmd, cwd=REPO_ROOT)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "spec" in payload
    assert "objective" in payload["spec"]
    assert "current" in payload["spec"]["objective"]
    assert "todo" in payload["spec"]["objective"]


def test_todo_template_no_question_mark_encoding_corruption() -> None:
    raw = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    model = RoadmapModel.from_json(raw)
    phase = model.get_phase("UMWELT0")
    assert phase is not None
    todo = phase.to_todo_dict()
    todo_json = json.dumps(todo, ensure_ascii=False, indent=2)
    assert "????" not in todo_json
    assert "mechanism/state-transition" in todo_json


def test_json_write_read_utf8_roundtrip() -> None:
    sample = {
        "todo": "Проверка UTF-8 roundtrip",
        "todo_en": "Unicode stability check",
    }
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "utf8_roundtrip.json"
        path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
        loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == sample
    assert loaded["todo"] == "Проверка UTF-8 roundtrip"


def test_todo_cli_output_has_no_corrupted_guidance() -> None:
    cmd = [
        sys.executable,
        "tracker/roadmap_cli.py",
        "todo",
        "--roadmap",
        "tracker/UmbraProtocol_MORA_language_refactor.json",
        "--code",
        "UMWELT0",
    ]
    result = _run(cmd, cwd=REPO_ROOT)
    assert result.returncode == 0
    assert "????" not in result.stdout
