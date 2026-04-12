from __future__ import annotations

from typing import Any, Mapping

from substrate.observability.contracts import (
    SECTION_KIND_ALLOWED,
    SECTION_KIND_NORMALIZED,
    SECTION_KIND_NOT_AVAILABLE,
    SECTION_KIND_RAW,
    is_json_compatible,
    section_kind,
)


EVENT_CLASS_ALLOWED = {
    "lifecycle",
    "decision",
    "constraint",
    "failure_degradation",
    "snapshot",
    "handoff_contract_dispatch",
    "diff_state_change",
    "topology_routing",
    "provenance_evidence",
}

SECTION_FIELDS: tuple[str, ...] = (
    "inputs",
    "outputs",
    "state_before",
    "state_after",
    "decision",
    "constraints",
    "failures",
    "degradations",
    "markers",
    "provenance",
    "ownership",
)

SECTION_REQUIRED_NORMALIZED_KEYS: dict[str, tuple[str, ...]] = {
    "state_before": ("local_state",),
    "state_after": ("local_state",),
}

REQUIRED_EVENT_FIELDS: tuple[str, ...] = (
    "tick_id",
    "trace_id",
    "span_id",
    "parent_span_id",
    "module",
    "stage",
    "event_type",
    "event_class",
    "timestamp",
    "order_index",
    "causal_depth",
    "inputs",
    "outputs",
    "state_before",
    "state_after",
    "decision",
    "constraints",
    "failures",
    "degradations",
    "markers",
    "provenance",
    "ownership",
    "upstream_refs",
    "downstream_refs",
    "module_run_id",
    "transition_id",
    "contract_id",
    "decision_id",
    "artifact_refs",
    "derived_from",
    "canonical",
    "derived",
    "inferred",
    "summarized",
)


def _validate_section_contract(field_name: str, value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, Mapping):
        return [f"{field_name} must be section contract object"]
    kind = section_kind(value)
    if kind not in SECTION_KIND_ALLOWED:
        return [f"{field_name} section has invalid _section_kind: {kind!r}"]

    if kind == SECTION_KIND_NORMALIZED:
        payload = value.get("payload")
        if not isinstance(payload, Mapping):
            errors.append(f"{field_name} normalized section must include payload object")
        elif not is_json_compatible(payload):
            errors.append(f"{field_name} normalized payload must be JSON-compatible")
        missing_keys = value.get("missing_keys", [])
        if not isinstance(missing_keys, list) or not all(isinstance(item, str) for item in missing_keys):
            errors.append(f"{field_name} normalized missing_keys must be list[str]")
        required_keys = SECTION_REQUIRED_NORMALIZED_KEYS.get(field_name, ())
        for required_key in required_keys:
            if not isinstance(payload, Mapping) or required_key not in payload:
                errors.append(
                    f"{field_name} normalized payload missing required key: {required_key}"
                )
        return errors

    if kind == SECTION_KIND_RAW:
        if "raw_payload" not in value:
            errors.append(f"{field_name} raw section must include raw_payload")
        elif not is_json_compatible(value["raw_payload"]):
            errors.append(f"{field_name} raw_payload must be JSON-compatible")
        reason = value.get("reason")
        if not isinstance(reason, str) or not reason:
            errors.append(f"{field_name} raw section must include non-empty reason")
        return errors

    if kind == SECTION_KIND_NOT_AVAILABLE:
        reason = value.get("reason")
        if not isinstance(reason, str) or not reason:
            errors.append(f"{field_name} not_available section must include non-empty reason")
        return errors

    return [f"{field_name} section has unsupported _section_kind: {kind!r}"]


def validate_event_schema(event: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_EVENT_FIELDS:
        if field not in event:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    if not isinstance(event["tick_id"], str) or not event["tick_id"]:
        errors.append("tick_id must be non-empty string")
    if not isinstance(event["trace_id"], str) or not event["trace_id"]:
        errors.append("trace_id must be non-empty string")
    if not isinstance(event["span_id"], str) or not event["span_id"]:
        errors.append("span_id must be non-empty string")
    if event["parent_span_id"] is not None and not isinstance(event["parent_span_id"], str):
        errors.append("parent_span_id must be string or null")
    if not isinstance(event["module"], str) or not event["module"]:
        errors.append("module must be non-empty string")
    if not isinstance(event["stage"], str) or not event["stage"]:
        errors.append("stage must be non-empty string")
    if not isinstance(event["event_type"], str) or not event["event_type"]:
        errors.append("event_type must be non-empty string")
    if event["event_class"] not in EVENT_CLASS_ALLOWED:
        errors.append(f"invalid event_class: {event['event_class']}")
    if not isinstance(event["timestamp"], str) or not event["timestamp"]:
        errors.append("timestamp must be non-empty string")
    if not isinstance(event["order_index"], int) or event["order_index"] < 0:
        errors.append("order_index must be int >= 0")
    if not isinstance(event["causal_depth"], int) or event["causal_depth"] < 0:
        errors.append("causal_depth must be int >= 0")

    for section_field in SECTION_FIELDS:
        errors.extend(_validate_section_contract(section_field, event[section_field]))

    for list_field in ("upstream_refs", "downstream_refs", "artifact_refs", "derived_from"):
        if not isinstance(event[list_field], list):
            errors.append(f"{list_field} must be list")
        elif not all(isinstance(item, str) and item for item in event[list_field]):
            errors.append(f"{list_field} must contain non-empty strings only")

    for id_field in ("module_run_id",):
        if not isinstance(event[id_field], str) or not event[id_field]:
            errors.append(f"{id_field} must be non-empty string")

    for optional_id in ("transition_id", "contract_id", "decision_id"):
        value = event[optional_id]
        if value is not None and not isinstance(value, str):
            errors.append(f"{optional_id} must be string or null")

    for bool_field in ("canonical", "derived", "inferred", "summarized"):
        if not isinstance(event[bool_field], bool):
            errors.append(f"{bool_field} must be bool")

    return errors
