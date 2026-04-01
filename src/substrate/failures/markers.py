from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping

from substrate.contracts import FailureCode, FailureMarker


def build_failure_marker(
    *,
    code: FailureCode,
    stage: str,
    message: str,
    transition_id: str,
    details: Mapping[str, str] | None = None,
    created_at: str | None = None,
) -> FailureMarker:
    return FailureMarker(
        code=code,
        stage=stage,
        message=message,
        transition_id=transition_id,
        created_at=created_at or datetime.now(tz=timezone.utc).isoformat(),
        details=MappingProxyType(dict(details or {})),
    )
