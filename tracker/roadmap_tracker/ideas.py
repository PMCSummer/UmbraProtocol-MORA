from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4


IDEA_SCHEMA_VERSION = 1
DEFAULT_IDEA_FILE = "idea_incubator.json"
IDEA_CATEGORIES = {
    "raw_sensor",
    "language",
    "agi_frontier",
    "gui_tooling",
    "roadmap_candidate",
    "other",
}
IDEA_STATUSES = {"raw", "incubating", "ready_for_phase", "deferred", "rejected"}
IDEA_CLARITY = {"unclear", "partial", "clear"}
IDEA_PRIORITIES = {"low", "medium", "high", "critical"}
IDEA_TARGET_LAYERS = {"subject", "contact", "runner", "adapter", "sensorium", "language", "tooling", "unknown"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def empty_store() -> Dict[str, Any]:
    return {
        "schema_version": IDEA_SCHEMA_VERSION,
        "ideas": [],
    }


def _normalize_idea(item: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_iso()
    category = str(item.get("category", "other")).strip() or "other"
    status = str(item.get("status", "raw")).strip() or "raw"
    clarity = str(item.get("implementation_clarity", "unclear")).strip() or "unclear"
    priority = str(item.get("priority", "medium")).strip() or "medium"
    target_layer = str(item.get("target_layer", "unknown")).strip() or "unknown"
    normalized = {
        "id": str(item.get("id", "")).strip() or f"idea_{uuid4().hex[:12]}",
        "title": str(item.get("title", "")).strip(),
        "summary": str(item.get("summary", "")).strip(),
        "category": category if category in IDEA_CATEGORIES else "other",
        "status": status if status in IDEA_STATUSES else "raw",
        "implementation_clarity": clarity if clarity in IDEA_CLARITY else "unclear",
        "priority": priority if priority in IDEA_PRIORITIES else "medium",
        "target_layer": target_layer if target_layer in IDEA_TARGET_LAYERS else "unknown",
        "linked_phase_codes": _listify(item.get("linked_phase_codes", [])),
        "blockers": _listify(item.get("blockers", [])),
        "falsifiers_to_resolve": _listify(item.get("falsifiers_to_resolve", [])),
        "notes": str(item.get("notes", "")).strip(),
        "created_at": str(item.get("created_at", "")).strip() or now,
        "updated_at": str(item.get("updated_at", "")).strip() or now,
    }
    return normalized


def normalize_store(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = raw or {}
    ideas_raw = payload.get("ideas", [])
    if not isinstance(ideas_raw, list):
        ideas_raw = []
    normalized_ideas = [_normalize_idea(item if isinstance(item, dict) else {}) for item in ideas_raw]
    return {
        "schema_version": IDEA_SCHEMA_VERSION,
        "ideas": normalized_ideas,
    }


def load_store(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return empty_store()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return empty_store()
    return normalize_store(raw)


def save_store(path: Path, store: Dict[str, Any]) -> None:
    normalized = normalize_store(store)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def create_idea(title: str = "", summary: str = "") -> Dict[str, Any]:
    return _normalize_idea({"title": title, "summary": summary})


def duplicate_idea(idea: Dict[str, Any]) -> Dict[str, Any]:
    clone = deepcopy(_normalize_idea(idea))
    clone["id"] = f"idea_{uuid4().hex[:12]}"
    clone["created_at"] = _now_iso()
    clone["updated_at"] = clone["created_at"]
    return clone


def update_idea_timestamp(idea: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _normalize_idea(idea)
    normalized["updated_at"] = _now_iso()
    return normalized


def ready_candidate(idea: Dict[str, Any]) -> bool:
    return (
        str(idea.get("implementation_clarity", "")).strip() == "clear"
        and str(idea.get("status", "")).strip() == "ready_for_phase"
    )


def idea_to_markdown(idea: Dict[str, Any]) -> str:
    idea_n = _normalize_idea(idea)
    lines = [
        f"# {idea_n['title'] or idea_n['id']}",
        "",
        f"- id: {idea_n['id']}",
        f"- category: {idea_n['category']}",
        f"- status: {idea_n['status']}",
        f"- implementation_clarity: {idea_n['implementation_clarity']}",
        f"- priority: {idea_n['priority']}",
        f"- target_layer: {idea_n['target_layer']}",
        f"- linked_phase_codes: {', '.join(idea_n['linked_phase_codes']) or 'none'}",
        "",
        "## Summary",
        idea_n["summary"] or "",
        "",
        "## Blockers",
    ]
    lines.extend(f"- {item}" for item in idea_n["blockers"])
    if not idea_n["blockers"]:
        lines.append("- none")
    lines.extend(["", "## Falsifiers To Resolve"])
    lines.extend(f"- {item}" for item in idea_n["falsifiers_to_resolve"])
    if not idea_n["falsifiers_to_resolve"]:
        lines.append("- none")
    lines.extend(["", "## Notes", idea_n["notes"] or ""])
    return "\n".join(lines).strip()


def idea_to_phase_skeleton(idea: Dict[str, Any]) -> Dict[str, Any]:
    idea_n = _normalize_idea(idea)
    title = idea_n["title"] or "Untitled Idea Candidate"
    summary = idea_n["summary"] or "TODO: define objective from incubated idea."
    risk_tags = [f"idea:{idea_n['category']}", f"priority:{idea_n['priority']}"]
    return {
        "code": "",
        "title": title,
        "desc": summary,
        "track": "build",
        "line": idea_n["target_layer"] if idea_n["target_layer"] != "unknown" else "tooling",
        "status": "later",
        "priority_bucket": "",
        "claim_role": "",
        "claim_state": "hypothesis",
        "maturity": "L1_theoretical_only",
        "risk_tag": risk_tags,
        "conceptually_after": idea_n["linked_phase_codes"],
        "implemented_after": "",
    }


def export_ready_ideas_to_bulk(ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    exported: List[Dict[str, Any]] = []
    for idea in ideas:
        if ready_candidate(idea):
            exported.append(idea_to_phase_skeleton(idea))
    return exported
