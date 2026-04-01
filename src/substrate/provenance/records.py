from __future__ import annotations

from datetime import datetime, timezone

from substrate.contracts import (
    AuthorityDecision,
    FailureMarker,
    ProvenanceRecord,
    ProvenanceStatus,
    StateDelta,
    TransitionKind,
    WriterIdentity,
)


def build_provenance_record(
    *,
    transition_id: str,
    writer: WriterIdentity,
    transition_kind: TransitionKind,
    event_id: str,
    cause_chain: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    actual_delta: StateDelta,
    authority: AuthorityDecision,
    status: ProvenanceStatus,
    failure: FailureMarker | None = None,
    recorded_at: str | None = None,
) -> ProvenanceRecord:
    return ProvenanceRecord(
        transition_id=transition_id,
        writer=writer,
        transition_kind=transition_kind,
        event_id=event_id,
        cause_chain=cause_chain,
        attempted_paths=attempted_paths,
        actual_delta=actual_delta,
        authority=authority,
        status=status,
        recorded_at=recorded_at or datetime.now(tz=timezone.utc).isoformat(),
        failure_code=failure.code if failure else None,
    )
