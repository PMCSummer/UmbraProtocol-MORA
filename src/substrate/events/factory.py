from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from substrate.contracts import EventRecord, TransitionKind


def build_event_record(
    *,
    event_id: str,
    transition_id: str,
    transition_kind: TransitionKind,
    payload: Mapping[str, Any],
    created_at: str,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        transition_id=transition_id,
        transition_kind=transition_kind,
        payload=MappingProxyType(dict(payload)),
        created_at=created_at,
    )
