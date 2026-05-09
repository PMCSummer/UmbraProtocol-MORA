from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class W01SourceAuthority(str, Enum):
    TRUSTED_WORLD_PROVIDER = "trusted_world_provider"
    WEAK_SCAFFOLD_PROVIDER = "weak_scaffold_provider"
    LANGUAGE_CONTEXT = "language_context"
    UNKNOWN_SOURCE = "unknown_source"
    REVOKED_SOURCE = "revoked_source"


class W01PresenceMode(str, Enum):
    ABSENT = "absent"
    SCAFFOLD_ONLY = "scaffold_only"
    PARTIAL = "partial"
    DEGRADED = "degraded"
    PRESENT = "present"
    CONTRADICTORY = "contradictory"
    REVOKED_OR_INVALID = "revoked_or_invalid"
    UNKNOWN = "unknown"


class W01PacketIntegrityStatus(str, Enum):
    VALID = "valid"
    DEGRADED = "degraded"
    MALFORMED = "malformed"
    MISSING_AUTHORITY = "missing_authority"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class W01WorldAdmissionState(str, Enum):
    ADMITTED = "admitted"
    ADMITTED_WITH_UNCERTAINTY = "admitted_with_uncertainty"
    SCAFFOLD_ONLY = "scaffold_only"
    ABSENT = "absent"
    CONTESTED = "contested"
    REJECTED = "rejected"
    REVOKED = "revoked"
    NO_CLEAN_WORLD_CLAIM = "no_clean_world_claim"


class W01ScaffoldTokenKind(str, Enum):
    OBSERVATION_ANCHOR = "observation_anchor"
    ACTION_SURFACE = "action_surface"
    EFFECT_TRACE = "effect_trace"
    RELATION_TO_ENTITY = "relation_to_entity"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    CONTRADICTION_MARKER = "contradiction_marker"
    ABSENCE_MARKER = "absence_marker"
    SCAFFOLD_ONLY_MARKER = "scaffold_only_marker"
    NON_MATURE_OBJECT_MARKER = "non_mature_object_marker"


class W01CausalLinkStatus(str, Enum):
    LINKED_PROVISIONAL = "linked_provisional"
    NOT_LINKED_MISSING_ACTION_REF = "not_linked_missing_action_ref"
    NOT_LINKED_TEMPORAL_MISMATCH = "not_linked_temporal_mismatch"
    NOT_LINKED_AUTHORITY_MISMATCH = "not_linked_authority_mismatch"
    NOT_LINKED_EFFECT_UNVERIFIED = "not_linked_effect_unverified"
    NOT_LINKED_PACKET_INVALID = "not_linked_packet_invalid"
    NO_LINK_CLAIM = "no_link_claim"


@dataclass(frozen=True, slots=True)
class W01WorldPacket:
    packet_id: str
    sequence: int
    entity_ref: str
    observation_payload: str | None
    action_ref: str | None
    effect_payload: str | None
    source_authority: W01SourceAuthority
    source_id: str
    timestamp_or_sequence: str
    presence_mode: W01PresenceMode
    confidence: float
    integrity_status: W01PacketIntegrityStatus
    contradiction_markers: tuple[str, ...]
    provenance_ref: tuple[str, ...]
    raw_packet_ref: str
    object_label: str | None = None
    object_stream_id: str | None = None
    object_authority_tags: tuple[str, ...] = ()
    revoked_ref: str | None = None


@dataclass(frozen=True, slots=True)
class W01WorldPacketSet:
    packet_set_id: str
    packets: tuple[W01WorldPacket, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class W01EntityCentricWorldScaffoldToken:
    token_id: str
    packet_ref: str
    entity_ref: str
    token_kind: W01ScaffoldTokenKind
    relation_to_entity: str
    unresolved_reference: bool
    contradiction_marker: bool
    absence_marker: bool
    scaffold_only_marker: bool
    non_mature_object_claim: bool
    confidence: float
    provenance_ref: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01ObservationActionEffectLinkage:
    linkage_id: str
    observation_packet_ref: str
    action_ref: str | None
    effect_packet_ref: str | None
    temporal_window_status: str
    authority_compatible: bool
    causal_link_status: W01CausalLinkStatus
    no_link_reason: str | None
    provenance_ref: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01WorldLoopAdmissionRecord:
    admission_id: str
    packet_ref: str
    cycle_id: str
    entity_id: str
    source_authority: W01SourceAuthority
    presence_mode_normalized: W01PresenceMode
    admission_state: W01WorldAdmissionState
    decision_reason_codes: tuple[str, ...]
    confidence_band: str
    uncertainty_markers: tuple[str, ...]
    provenance_ref: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01ContradictionLedgerEntry:
    conflict_id: str
    conflicting_packet_refs: tuple[str, ...]
    conflict_type: str
    unresolved_status: bool
    authority_comparison: str
    revocation_status: str
    required_downstream_behavior: tuple[str, ...]
    provenance_ref: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01DownstreamPermissionPacket:
    admission_ref: str
    may_use_as_world_scaffold: bool
    may_use_for_grounded_transition: bool
    may_claim_object_presence: bool
    must_abstain: bool
    must_escalate: bool
    must_preserve_uncertainty: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01Telemetry:
    packet_count: int
    admitted_count: int
    admitted_with_uncertainty_count: int
    scaffold_only_count: int
    absent_count: int
    contested_count: int
    rejected_count: int
    revoked_count: int
    contradiction_count: int
    linked_effect_count: int
    no_link_count: int
    source_authority_missing_count: int
    non_mature_object_claim_count: int
    consumer_ready_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class W01ScopeMarker:
    scope: str
    staged_world_scaffold_only: bool
    no_mature_object_claim: bool
    no_object_permanence_claim: bool
    no_scene_graph_maturity_claim: bool
    no_policy_selection_claim: bool
    no_world_truth_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W01GateDecision:
    consumer_ready: bool
    admission_required: bool
    clean_world_claim_allowed: bool
    accepted_count: int
    contested_count: int
    blocked_count: int
    revoked_count: int
    authority_missing_count: int
    object_overclaim_blocked_count: int
    contradiction_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01Result:
    packet_set_id: str
    packet_refs: tuple[str, ...]
    admission_records: tuple[W01WorldLoopAdmissionRecord, ...]
    scaffold_tokens: tuple[W01EntityCentricWorldScaffoldToken, ...]
    action_effect_linkages: tuple[W01ObservationActionEffectLinkage, ...]
    contradiction_ledger: tuple[W01ContradictionLedgerEntry, ...]
    downstream_permissions: tuple[W01DownstreamPermissionPacket, ...]
    telemetry: W01Telemetry
    scope_marker: W01ScopeMarker
    gate: W01GateDecision
    reason: str
