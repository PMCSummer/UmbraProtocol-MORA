from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


REVIEW_OVERALL_ALLOWED = {
    "coherent",
    "mostly_coherent_with_questions",
    "suspicious_but_inconclusive",
    "likely_problematic",
    "insufficient_evidence",
}
PRIORITY_ALLOWED = {"low", "medium", "high"}
SEVERITY_ALLOWED = {"low", "medium", "high"}


class ReviewerSchemaError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GeneratedCase:
    case_id: str
    seed: int
    theme: str
    scenario_family: str
    scenario_intent: str
    paired_with: str | None
    key_tension_axis: tuple[str, ...]
    what_to_inspect_in_trace: tuple[str, ...]
    why_this_case_exists: str
    trace_path: str
    generation_params: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ReviewCallResult:
    tier: str
    model: str
    raw_text: str
    parsed_json: dict[str, Any]


def _as_string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ReviewerSchemaError(f"{field_name} must be list")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ReviewerSchemaError(f"{field_name} must contain strings")
        out.append(item)
    return out


def _ensure_priority(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or value not in PRIORITY_ALLOWED:
        raise ReviewerSchemaError(f"{field_name} must be one of {sorted(PRIORITY_ALLOWED)}")
    return value


def validate_reviewer_output(payload: dict[str, Any], *, expected_case_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ReviewerSchemaError("reviewer payload must be object")

    case_id = str(payload.get("case_id", ""))
    if case_id != expected_case_id:
        raise ReviewerSchemaError("case_id mismatch")

    overall = payload.get("overall_reading")
    if not isinstance(overall, str) or overall not in REVIEW_OVERALL_ALLOWED:
        raise ReviewerSchemaError(
            f"overall_reading must be one of {sorted(REVIEW_OVERALL_ALLOWED)}"
        )

    confidence = payload.get("confidence")
    if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0):
        raise ReviewerSchemaError("confidence must be float in [0, 1]")

    _as_string_list(payload.get("behavior_summary", []), field_name="behavior_summary")

    for field_name in ("coherent_segments", "suspicious_segments", "likely_observability_gaps", "code_focus_candidates"):
        if not isinstance(payload.get(field_name, []), list):
            raise ReviewerSchemaError(f"{field_name} must be list")

    comparison = payload.get("paired_case_comparison", {})
    if not isinstance(comparison, dict):
        raise ReviewerSchemaError("paired_case_comparison must be object")
    if "used" in comparison and not isinstance(comparison["used"], bool):
        raise ReviewerSchemaError("paired_case_comparison.used must be bool")

    _ensure_priority(payload.get("human_review_priority"), field_name="human_review_priority")

    final_note = payload.get("final_note")
    if not isinstance(final_note, str):
        raise ReviewerSchemaError("final_note must be string")

    for item in payload.get("suspicious_segments", []):
        if not isinstance(item, dict):
            raise ReviewerSchemaError("suspicious_segments items must be objects")
        severity = item.get("severity", "low")
        if not isinstance(severity, str) or severity not in SEVERITY_ALLOWED:
            raise ReviewerSchemaError("suspicious_segments[].severity invalid")

    return payload


def extract_first_json_object(raw_text: str) -> dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        raise ReviewerSchemaError("empty reviewer output")

    # Fast path: whole response is valid JSON object.
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ReviewerSchemaError("no JSON object found in reviewer output")
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ReviewerSchemaError(f"invalid JSON from reviewer: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReviewerSchemaError("reviewer output JSON must be object")
    return payload

