from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class A04AdmissionStatus(str, Enum):
    ADMITTED = "admitted"
    PROVISIONAL = "provisional"
    CONTESTED = "contested"
    BLOCKED = "blocked"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class A04BindingStatus(str, Enum):
    ADMITTED = "admitted"
    PROVISIONAL = "provisional"
    CONTESTED = "contested"
    BLOCKED = "blocked"
    REVOKED = "revoked"
    NO_CLEAN_EXTERNAL_AFFORDANCE_CLAIM = "no_clean_external_affordance_claim"


class A04LegalityStatus(str, Enum):
    PERMITTED = "permitted"
    RESTRICTED = "restricted"
    FORBIDDEN = "forbidden"
    UNKNOWN = "unknown"


class A04ObjectMaturityStatus(str, Enum):
    NOT_PROVIDED = "not_provided"
    SCAFFOLD_ONLY = "scaffold_only"
    MATURE_UNAVAILABLE_IN_A04 = "mature_unavailable_in_a04"
    CONTESTED = "contested"


class A04NormalizationDecision(str, Enum):
    ADMITTED_ENTITY_SCOPED_BINDING = "admitted_entity_scoped_binding"
    ADMITTED_OBJECT_SCAFFOLD_BINDING = "admitted_object_scaffold_binding"
    CONTESTED_NOISY_SCAFFOLD = "contested_noisy_scaffold"
    BLOCKED_ABSENT_SCAFFOLD = "blocked_absent_scaffold"
    BLOCKED_NO_AUTHORITY = "blocked_no_authority"
    BLOCKED_OBJECT_MATURITY_OVERCLAIM = "blocked_object_maturity_overclaim"
    BLOCKED_UNSUPPORTED_CANDIDATE = "blocked_unsupported_candidate"
    BLOCKED_CONTRADICTORY_WORLD_PACKETS = "blocked_contradictory_world_packets"
    REVOKED_BINDING = "revoked_binding"
    NO_CLEAN_EXTERNAL_AFFORDANCE_CLAIM = "no_clean_external_affordance_claim"


class A04DownstreamReadinessStatus(str, Enum):
    READY = "ready"
    MISSING_BINDING_PACKET_CONSUMER = "missing_binding_packet_consumer"
    MISSING_AUTHORITY_PATH_CONSUMER = "missing_authority_path_consumer"
    NO_SAFE_DOWNSTREAM_EXTERNAL_AFFORDANCE_CLAIM = "no_safe_downstream_external_affordance_claim"


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceCandidate:
    candidate_id: str
    entity_ref: str
    object_ref: str | None
    affordance_class: str
    candidate_label: str
    source_authority: str
    scaffold_scope: str
    epistemic_basis: tuple[str, ...]
    permission_basis: tuple[str, ...]
    temporal_validity: str
    confidence: float
    provenance: tuple[str, ...]
    contradiction_refs: tuple[str, ...] = ()
    revocation_refs: tuple[str, ...] = ()
    required_world_scaffold_refs: tuple[str, ...] = ()
    admission_hint: A04AdmissionStatus | None = None


@dataclass(frozen=True, slots=True)
class A04WorldEntityScaffold:
    entity_ref: str
    source_authority: str
    scaffold_scope: str
    admission_status: A04AdmissionStatus
    confidence: float
    temporal_validity: str
    provenance: tuple[str, ...]
    supported_affordance_classes: tuple[str, ...] = ()
    entity_kind: str | None = None
    object_ref: str | None = None
    object_maturity_status: A04ObjectMaturityStatus = A04ObjectMaturityStatus.SCAFFOLD_ONLY
    revocation_status: bool = False
    revocation_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceCandidateSet:
    candidate_set_id: str
    candidates: tuple[A04ExternalAffordanceCandidate, ...]
    world_scaffolds: tuple[A04WorldEntityScaffold, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceBinding:
    binding_id: str
    candidate_id: str
    entity_ref: str
    object_ref: str | None
    affordance_class: str
    binding_status: A04BindingStatus
    admission_status: A04AdmissionStatus
    source_authority: str
    scaffold_scope: str
    epistemic_basis: tuple[str, ...]
    legality_status: A04LegalityStatus
    temporal_validity: str
    confidence: float
    downstream_scope: str
    authority_preserved: bool
    object_maturity_claim_blocked: bool
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A04BlockedCandidate:
    candidate_id: str
    decision: A04NormalizationDecision
    reason: str
    contradiction_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A04ContestedCandidate:
    candidate_id: str
    decision: A04NormalizationDecision
    reason: str
    contradiction_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A04BindingLedgerEntry:
    entry_id: str
    candidate_id: str
    decision: A04NormalizationDecision
    status: A04BindingStatus
    reason: str
    contradiction_refs: tuple[str, ...] = ()
    revocation_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A04BindingLedger:
    ledger_id: str
    entries: tuple[A04BindingLedgerEntry, ...]
    accepted_count: int
    contested_count: int
    blocked_count: int
    revoked_count: int
    authority_missing_count: int
    object_overclaim_blocked_count: int
    contradiction_count: int
    reason: str


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceGateDecision:
    accepted_count: int
    contested_count: int
    blocked_count: int
    revoked_count: int
    authority_missing_count: int
    object_overclaim_blocked_count: int
    contradiction_count: int
    binding_packet_consumer_ready: bool
    authority_path_consumer_ready: bool
    consumer_ready: bool
    required_restrictions: tuple[str, ...]
    downstream_readiness_status: A04DownstreamReadinessStatus
    no_map_wide_claim: bool
    staged_scaffold_only: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A04ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    staged_scaffold_only: bool
    entity_binding_not_object_perception: bool
    no_map_wide_claim: bool
    no_execution_claim: bool
    no_policy_selection_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A04Telemetry:
    a04_binding_count: int
    a04_contested_count: int
    a04_blocked_count: int
    a04_revoked_count: int
    a04_authority_missing_count: int
    a04_object_overclaim_blocked_count: int
    a04_consumer_ready: bool
    a04_staged_scaffold_only: bool
    a04_no_map_wide_claim: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceBindingResult:
    candidate_set_id: str
    bindings: tuple[A04ExternalAffordanceBinding, ...]
    blocked_candidates: tuple[A04BlockedCandidate, ...]
    contested_candidates: tuple[A04ContestedCandidate, ...]
    ledger: A04BindingLedger
    gate: A04ExternalAffordanceGateDecision
    telemetry: A04Telemetry
    scope_marker: A04ScopeMarker
    reason: str
