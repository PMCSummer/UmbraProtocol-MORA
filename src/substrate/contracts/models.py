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


class DomainWriterPhase(str, Enum):
    R04 = "R04"
    C04 = "C04"
    C05 = "C05"
    RT01 = "RT01"
    F01 = "F01"
    UNKNOWN = "UNKNOWN"


class DomainWriteRoute(str, Enum):
    RT01_SUBJECT_TICK_CONTOUR = "rt01_subject_tick_contour"
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
class RegulationDomainState:
    pressure_level: float | None = None
    escalation_stage: str | None = None
    override_scope: str | None = None
    no_strong_override_claim: bool = False
    gate_accepted: bool = False
    source_state_ref: str | None = None
    updated_by_phase: str | None = None
    last_update_provenance: str | None = None


@dataclass(frozen=True, slots=True)
class ContinuityDomainState:
    c04_mode_claim: str | None = None
    c04_selected_mode: str | None = None
    mode_legitimacy: bool = False
    endogenous_tick_allowed: bool | None = None
    arbitration_confidence: float | None = None
    source_state_ref: str | None = None
    updated_by_phase: str | None = None
    last_update_provenance: str | None = None


@dataclass(frozen=True, slots=True)
class ValidityDomainState:
    c05_action_claim: str | None = None
    c05_validity_action: str | None = None
    legality_reuse_allowed: bool = False
    revalidation_required: bool = False
    no_safe_reuse: bool = False
    selective_scope_targets: tuple[str, ...] = ()
    source_state_ref: str | None = None
    updated_by_phase: str | None = None
    last_update_provenance: str | None = None


@dataclass(frozen=True, slots=True)
class SelfBoundaryDomainState:
    status: str = "not_materialized"


@dataclass(frozen=True, slots=True)
class WorldDomainState:
    status: str = "not_materialized"


@dataclass(frozen=True, slots=True)
class MemoryEconomicsDomainState:
    status: str = "not_materialized"


@dataclass(frozen=True, slots=True)
class RuntimeDomainsState:
    regulation: RegulationDomainState = field(default_factory=RegulationDomainState)
    continuity: ContinuityDomainState = field(default_factory=ContinuityDomainState)
    validity: ValidityDomainState = field(default_factory=ValidityDomainState)
    self_boundary: SelfBoundaryDomainState = field(default_factory=SelfBoundaryDomainState)
    world: WorldDomainState = field(default_factory=WorldDomainState)
    memory_economics: MemoryEconomicsDomainState = field(default_factory=MemoryEconomicsDomainState)


@dataclass(frozen=True, slots=True)
class DomainWriteClaim:
    phase: DomainWriterPhase
    domain_path: str
    transition_kind: TransitionKind
    route: DomainWriteRoute
    checkpoint_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class RuntimeDomainUpdate:
    regulation: RegulationDomainState | None = None
    continuity: ContinuityDomainState | None = None
    validity: ValidityDomainState | None = None
    write_claims: tuple[DomainWriteClaim, ...] = ()
    reason: str = "runtime_domain_update"


@dataclass(frozen=True, slots=True)
class RuntimeRouteAuthContext:
    route: DomainWriteRoute
    origin_phase: DomainWriterPhase
    transition_kind: TransitionKind
    tick_id: str
    authorized_domain_paths: tuple[str, ...]
    checkpoint_ids: tuple[str, ...]
    origin_contract: str
    auth_nonce: str


@dataclass(frozen=True, slots=True)
class RuntimeState:
    meta: RuntimeMeta = field(default_factory=RuntimeMeta)
    runtime: RuntimeCore = field(default_factory=RuntimeCore)
    turn: TurnState = field(default_factory=TurnState)
    failures: FailureState = field(default_factory=FailureState)
    trace: TraceState = field(default_factory=TraceState)
    domains: RuntimeDomainsState = field(default_factory=RuntimeDomainsState)


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
