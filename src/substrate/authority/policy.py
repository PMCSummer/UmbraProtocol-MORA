from __future__ import annotations

from substrate.contracts import AuthorityDecision, TransitionKind, WriterIdentity


WRITER_ALLOWED_PATHS: dict[WriterIdentity, frozenset[str]] = {
    WriterIdentity.BOOTSTRAPPER: frozenset(
        {
            "meta.schema_version",
            "meta.initialized_at",
            "runtime.lifecycle",
            "runtime.revision",
        }
    ),
    WriterIdentity.TRANSITION_ENGINE: frozenset(
        {
            "runtime.revision",
            "runtime.last_transition_id",
            "runtime.last_event_id",
            "turn.current_turn_id",
            "turn.last_event_ref",
            "failures.current",
            "trace.transitions",
            "trace.events",
        }
    ),
    WriterIdentity.OBSERVER: frozenset(),
    WriterIdentity.UNKNOWN: frozenset(),
}


ENGINE_INTERNAL_WRITES: frozenset[str] = frozenset(
    {
        "runtime.revision",
        "runtime.last_transition_id",
        "runtime.last_event_id",
        "failures.current",
        "trace.transitions",
        "trace.events",
    }
)


def writer_transition_paths(transition_kind: TransitionKind) -> frozenset[str]:
    if transition_kind == TransitionKind.BOOTSTRAP_INIT:
        return frozenset({"meta.schema_version", "meta.initialized_at", "runtime.lifecycle"})
    if transition_kind in {
        TransitionKind.INGEST_EXTERNAL_EVENT,
        TransitionKind.APPLY_INTERNAL_EVENT,
    }:
        return frozenset({"turn.current_turn_id", "turn.last_event_ref"})
    return frozenset()


def check_authority(
    writer: WriterIdentity, requested_paths: frozenset[str]
) -> AuthorityDecision:
    allowed_paths = WRITER_ALLOWED_PATHS.get(writer, frozenset())
    denied_paths = tuple(sorted(requested_paths - allowed_paths))
    if denied_paths:
        return AuthorityDecision(
            allowed=False,
            denied_paths=denied_paths,
            reason="writer attempted forbidden field writes",
        )
    return AuthorityDecision(allowed=True, denied_paths=(), reason="writer authorized")


def allowed_changed_paths(
    *,
    transition_kind: TransitionKind,
    writer: WriterIdentity,
    accepted: bool,
) -> frozenset[str]:
    base = set(ENGINE_INTERNAL_WRITES)
    if accepted:
        base |= WRITER_ALLOWED_PATHS.get(writer, frozenset())
        base |= writer_transition_paths(transition_kind)
    return frozenset(base)
