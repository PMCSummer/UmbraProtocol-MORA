from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKER_DIR = REPO_ROOT / "tracker"
if str(TRACKER_DIR) not in sys.path:
    sys.path.insert(0, str(TRACKER_DIR))

from roadmap_tracker.ideas import (
    create_idea,
    duplicate_idea,
    export_ready_ideas_to_bulk,
    load_store,
    ready_candidate,
    save_store,
)


def test_load_store_missing_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "ideas.json"
    store = load_store(path)
    assert store["schema_version"] == 1
    assert store["ideas"] == []


def test_save_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "ideas.json"
    store = {"schema_version": 1, "ideas": [create_idea("A", "B")]}
    save_store(path, store)
    loaded = load_store(path)
    assert loaded["schema_version"] == 1
    assert len(loaded["ideas"]) == 1
    assert loaded["ideas"][0]["title"] == "A"


def test_duplicate_idea_new_id() -> None:
    idea = create_idea("alpha", "beta")
    clone = duplicate_idea(idea)
    assert clone["id"] != idea["id"]
    assert clone["title"] == idea["title"]


def test_export_ready_ideas_to_bulk_only_ready() -> None:
    ready = create_idea("Ready Idea", "summary")
    ready["status"] = "ready_for_phase"
    ready["implementation_clarity"] = "clear"
    raw = create_idea("Raw Idea", "summary")
    exported = export_ready_ideas_to_bulk([ready, raw])
    assert len(exported) == 1
    assert exported[0]["title"] == "Ready Idea"
    assert ready_candidate(ready) is True
    assert ready_candidate(raw) is False


def test_exported_bulk_is_json_serializable() -> None:
    ready = create_idea("Ready", "text")
    ready["status"] = "ready_for_phase"
    ready["implementation_clarity"] = "clear"
    payload = export_ready_ideas_to_bulk([ready])
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    assert text.startswith("[")
