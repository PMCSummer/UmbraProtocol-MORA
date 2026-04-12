from __future__ import annotations

from typing import Any, Mapping

from substrate.observability.utils import to_jsonable


SECTION_KIND_NORMALIZED = "normalized"
SECTION_KIND_RAW = "raw"
SECTION_KIND_NOT_AVAILABLE = "not_available"
SECTION_KIND_ALLOWED = {
    SECTION_KIND_NORMALIZED,
    SECTION_KIND_RAW,
    SECTION_KIND_NOT_AVAILABLE,
}


def is_json_compatible(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(is_json_compatible(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and is_json_compatible(item) for key, item in value.items())
    return False


def section_normalized(
    payload: Mapping[str, Any] | None,
    *,
    missing_keys: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "_section_kind": SECTION_KIND_NORMALIZED,
        "payload": to_jsonable(dict(payload or {})),
        "missing_keys": list(missing_keys),
    }


def section_raw(raw_payload: Any, *, reason: str) -> dict[str, Any]:
    return {
        "_section_kind": SECTION_KIND_RAW,
        "raw_payload": to_jsonable(raw_payload),
        "reason": reason,
    }


def section_not_available(reason: str) -> dict[str, Any]:
    return {
        "_section_kind": SECTION_KIND_NOT_AVAILABLE,
        "reason": reason,
    }


def coerce_section_contract(
    value: Any,
    *,
    default_reason: str = "not_provided",
) -> dict[str, Any]:
    if isinstance(value, Mapping) and "_section_kind" in value:
        return to_jsonable(value)
    if value is None:
        return section_not_available(default_reason)
    if isinstance(value, Mapping):
        payload = dict(value)
        if not payload:
            return section_not_available(default_reason)
        return section_normalized(payload)
    return section_raw(value, reason="non_mapping_payload")


def section_kind(section: Mapping[str, Any]) -> str:
    value = section.get("_section_kind")
    return value if isinstance(value, str) else ""


def normalized_payload(section: Mapping[str, Any]) -> dict[str, Any]:
    if section_kind(section) != SECTION_KIND_NORMALIZED:
        return {}
    payload = section.get("payload")
    if isinstance(payload, Mapping):
        return dict(payload)
    return {}
