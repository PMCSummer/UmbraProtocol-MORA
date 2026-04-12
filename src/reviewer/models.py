from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


REVIEW_OVERALL_ALLOWED = {
    "coherent_bounded_caution",
    "coherent_abstention_or_revalidation",
    "plausible_but_needs_review",
    "likely_behavioral_problem",
    "insufficient_evidence",
}
PRIORITY_ALLOWED = {"low", "medium", "high"}
SEVERITY_ALLOWED = {"low", "medium", "high"}
SIGNAL_CODE_ALLOWED = {
    "t03_honest_nonconvergence",
    "t04_not_reportable",
    "bounded_revalidation_required",
    "subject_idle_continuation",
    "world_basis_missing",
    "ownership_confidence_low",
    "memory_claim_denied",
    "narrative_claim_denied",
    "mode_safe_idle_selected",
    "validity_reuse_only",
    "bounded_repair_required",
    "subject_abstention_revalidation",
    "causal_transition_mismatch",
    "unexpected_mode_shift",
    "unknown_or_unmapped_signal",
}
GAP_CODE_ALLOWED = {
    "hidden_transition",
    "insufficient_local_state",
    "ambiguous_world_basis",
    "unclear_resolution_step",
}
REVIEW_CALL_STATUS_ALLOWED = {
    "transport_error",
    "timeout",
    "empty_response",
    "thinking_only_no_answer",
    "parse_error",
    "schema_warning",
    "semantic_review_completed",
}


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
class ReviewNormalizationResult:
    normalized_payload: dict[str, Any]
    schema_warnings: tuple[str, ...]
    nonfatal_warnings: tuple[str, ...]
    model_case_id: str | None


@dataclass(frozen=True, slots=True)
class ReviewCallResult:
    tier: str
    model: str
    case_id: str
    status: str
    endpoint: str
    request_payload: dict[str, Any]
    raw_http_response_body: str
    extracted_text: str
    response_field_used: str
    thinking_present: bool
    prompt_eval_count: int | None
    eval_count: int | None
    latency_ms: float
    timeout: bool
    retry_count: int
    parsed_json: dict[str, Any] | None
    schema_warnings: tuple[str, ...]
    nonfatal_warnings: tuple[str, ...]
    error_message: str | None
    model_case_id: str | None = None


def _as_str(value: Any, *, field_name: str, default: str, warnings: list[str]) -> str:
    if isinstance(value, str):
        return value
    warnings.append(f"{field_name}_invalid")
    return default


def _as_float(
    value: Any,
    *,
    field_name: str,
    default: float,
    lo: float,
    hi: float,
    warnings: list[str],
) -> float:
    try:
        cast = float(value)
        if cast < lo or cast > hi:
            raise ValueError("out_of_range")
        return cast
    except (TypeError, ValueError):
        warnings.append(f"{field_name}_invalid")
        return default


def _normalize_suspicious_segments(
    value: Any,
    *,
    warnings: list[str],
    nonfatal_warnings: list[str],
) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        warnings.append("suspicious_segments_invalid_type")
        return []
    out: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            warnings.append("suspicious_segment_non_object")
            continue
        module = _as_str(
            item.get("module"),
            field_name="suspicious_segment_module",
            default="unknown",
            warnings=warnings,
        )
        signal_code = _as_str(
            item.get("signal_code"),
            field_name="suspicious_segment_signal_code",
            default="unknown_or_unmapped_signal",
            warnings=warnings,
        )
        if signal_code not in SIGNAL_CODE_ALLOWED:
            warnings.append("suspicious_segment_signal_code_invalid")
            signal_code = "unknown_or_unmapped_signal"
        severity = _as_str(
            item.get("severity"),
            field_name="suspicious_segment_severity",
            default="low",
            warnings=warnings,
        )
        if severity not in SEVERITY_ALLOWED:
            warnings.append("suspicious_segment_severity_invalid")
            severity = "low"
        out.append({"module": module, "signal_code": signal_code, "severity": severity})
    if len(out) > 3:
        nonfatal_warnings.append("suspicious_segments_truncated")
        return out[:3]
    return out


def _normalize_observability_gaps(
    value: Any,
    *,
    warnings: list[str],
    nonfatal_warnings: list[str],
) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        warnings.append("likely_observability_gaps_invalid_type")
        return []
    out: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            warnings.append("likely_observability_gap_non_object")
            continue
        module_or_transition = _as_str(
            item.get("module_or_transition"),
            field_name="likely_observability_gap_module_or_transition",
            default="unknown",
            warnings=warnings,
        )
        gap_code = _as_str(
            item.get("gap_code"),
            field_name="likely_observability_gap_gap_code",
            default="insufficient_local_state",
            warnings=warnings,
        )
        if gap_code not in GAP_CODE_ALLOWED:
            warnings.append("likely_observability_gap_gap_code_invalid")
            gap_code = "insufficient_local_state"
        out.append({"module_or_transition": module_or_transition, "gap_code": gap_code})
    if len(out) > 3:
        nonfatal_warnings.append("likely_observability_gaps_truncated")
        return out[:3]
    return out


def normalize_reviewer_output(
    payload: dict[str, Any],
    *,
    expected_case_id: str,
) -> ReviewNormalizationResult:
    if not isinstance(payload, dict):
        raise ReviewerSchemaError("reviewer payload must be object")

    schema_warnings: list[str] = []
    nonfatal_warnings: list[str] = []

    model_case_id_raw = payload.get("case_id")
    model_case_id: str | None
    if model_case_id_raw is None:
        model_case_id = None
        nonfatal_warnings.append("model_case_id_missing")
    elif isinstance(model_case_id_raw, str):
        model_case_id = model_case_id_raw
    else:
        model_case_id = str(model_case_id_raw)
        nonfatal_warnings.append("model_case_id_non_string")
    if model_case_id != expected_case_id:
        nonfatal_warnings.append("case_id_mismatch")

    overall_reading = payload.get("overall_reading")
    if not isinstance(overall_reading, str) or overall_reading not in REVIEW_OVERALL_ALLOWED:
        schema_warnings.append("overall_reading_invalid")
        overall_reading = "insufficient_evidence"

    confidence = _as_float(
        payload.get("confidence"),
        field_name="confidence",
        default=0.0,
        lo=0.0,
        hi=1.0,
        warnings=schema_warnings,
    )

    priority = payload.get("human_review_priority")
    if not isinstance(priority, str) or priority not in PRIORITY_ALLOWED:
        schema_warnings.append("human_review_priority_invalid")
        priority = "high"

    final_note = payload.get("final_note")
    if not isinstance(final_note, str):
        schema_warnings.append("final_note_invalid")
        final_note = ""
    if len(final_note) > 220:
        nonfatal_warnings.append("final_note_truncated")
        final_note = final_note[:220]

    suspicious_segments = _normalize_suspicious_segments(
        payload.get("suspicious_segments"),
        warnings=schema_warnings,
        nonfatal_warnings=nonfatal_warnings,
    )
    likely_observability_gaps = _normalize_observability_gaps(
        payload.get("likely_observability_gaps"),
        warnings=schema_warnings,
        nonfatal_warnings=nonfatal_warnings,
    )

    normalized = {
        "case_id": expected_case_id,
        "overall_reading": overall_reading,
        "confidence": confidence,
        "suspicious_segments": suspicious_segments,
        "likely_observability_gaps": likely_observability_gaps,
        "human_review_priority": priority,
        "final_note": final_note,
    }
    return ReviewNormalizationResult(
        normalized_payload=normalized,
        schema_warnings=tuple(schema_warnings),
        nonfatal_warnings=tuple(nonfatal_warnings),
        model_case_id=model_case_id,
    )


def validate_reviewer_output(payload: dict[str, Any], *, expected_case_id: str) -> dict[str, Any]:
    normalized = normalize_reviewer_output(payload, expected_case_id=expected_case_id)
    if normalized.schema_warnings:
        raise ReviewerSchemaError(
            "schema warnings present: " + ",".join(normalized.schema_warnings)
        )
    return normalized.normalized_payload


def extract_first_json_object(raw_text: str) -> dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        raise ReviewerSchemaError("empty reviewer output")

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
