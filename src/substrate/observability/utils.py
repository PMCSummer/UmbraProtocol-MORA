from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, Enum):
        enum_value = getattr(value, "value", None)
        if isinstance(enum_value, (str, int, float, bool)) or enum_value is None:
            return enum_value
        return str(enum_value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [to_jsonable(item) for item in sorted(value, key=lambda item: str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def short_ref(*tokens: str) -> str:
    clean: list[str] = []
    for token in tokens:
        if not token or not token.strip():
            continue
        normalized = []
        for ch in token.strip():
            if ch.isalnum() or ch in {"_", "-"}:
                normalized.append(ch)
            else:
                normalized.append("_")
        clean.append("".join(normalized))
    return "_".join(clean)
