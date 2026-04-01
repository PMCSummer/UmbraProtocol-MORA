from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Lifecycle(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"


class TransitionKind(str, Enum):
    BOOTSTRAP_INIT = "BOOTSTRAP_INIT"
    INGEST_EXTERNAL_EVENT = "INGEST_EXTERNAL_EVENT"
    APPLY_INTERNAL_EVENT = "APPLY_INTERNAL_EVENT"
    REJECTED_TRANSITION = "REJECTED_TRANSITION"


class WriterIdentity(str, Enum):
    BOOTSTRAPPER = "bootstrapper"
    TRANSITION_ENGINE = "transition_engine"
    OBSERVER = "observer"
    UNKNOWN = "unknown"


class ProvenanceStatus(str, Enum):
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"


class FailureCode(str, Enum):
    INVALID_REQUEST_SHAPE = "INVALID_REQUEST_SHAPE"
    INVALID_STATE_SHAPE = "INVALID_STATE_SHAPE"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
    REQUESTED_REJECTION = "REQUESTED_REJECTION"


@dataclass(frozen=True, slots=True)
class FailureMarker:
    code: FailureCode
    stage: str
    message: str
    transition_id: str
    created_at: str
    details: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuthorityDecision:
    allowed: bool
    denied_paths: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class EventRecord:
    event_id: str
    transition_id: str
    transition_kind: TransitionKind
    payload: Mapping[str, Any]
    created_at: str


@dataclass(frozen=True, slots=True)
class StateDelta:
    changed_fields: tuple[str, ...]
    before_revision: int
    after_revision: int
    transition_id: str
    event_id: str


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    transition_id: str
    writer: WriterIdentity
    transition_kind: TransitionKind
    event_id: str
    cause_chain: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    actual_delta: StateDelta
    authority: AuthorityDecision
    status: ProvenanceStatus
    recorded_at: str
    failure_code: FailureCode | None = None


@dataclass(frozen=True, slots=True)
class RuntimeMeta:
    schema_version: str | None = None
    initialized_at: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeCore:
    lifecycle: Lifecycle = Lifecycle.UNINITIALIZED
    revision: int = 0
    last_transition_id: str | None = None
    last_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class TurnState:
    current_turn_id: str | None = None
    last_event_ref: str | None = None


@dataclass(frozen=True, slots=True)
class FailureState:
    current: FailureMarker | None = None


@dataclass(frozen=True, slots=True)
class TraceState:
    transitions: tuple[ProvenanceRecord, ...] = ()
    events: tuple[EventRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class RuntimeState:
    meta: RuntimeMeta = field(default_factory=RuntimeMeta)
    runtime: RuntimeCore = field(default_factory=RuntimeCore)
    turn: TurnState = field(default_factory=TurnState)
    failures: FailureState = field(default_factory=FailureState)
    trace: TraceState = field(default_factory=TraceState)


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    transition_id: str
    transition_kind: TransitionKind
    writer: WriterIdentity
    cause_chain: tuple[str, ...]
    requested_at: str
    event_id: str | None = None
    event_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class TransitionResult:
    accepted: bool
    state: RuntimeState
    delta: StateDelta
    provenance: ProvenanceRecord
    authority: AuthorityDecision
    emitted_event: EventRecord
    failure: FailureMarker | None = None
