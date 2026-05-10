from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class W02ObjectMaturityLevel(str, Enum):
    TRACE_TOKEN = "trace_token"
    RECURRENT_SCAFFOLD = "recurrent_scaffold"
    PERSISTENT_INSTANCE_CANDIDATE = "persistent_instance_candidate"
    PERSISTENT_INSTANCE_HYPOTHESIS = "persistent_instance_hypothesis"
    KIND_CANDIDATE = "kind_candidate"
    STRUCTURAL_SIGNATURE_CANDIDATE = "structural_signature_candidate"
    AFFORDANCE_CANDIDATE = "affordance_candidate"
    SCENE_ROLE_CANDIDATE = "scene_role_candidate"
    LINEAGE_HYPOTHESIS = "lineage_hypothesis"
    BLOCKED = "blocked"
    CONTESTED = "contested"
    DOWNGRADED = "downgraded"
    MATURE_OBJECT_CLAIM_BLOCKED_OR_DEFERRED = "mature_object_claim_blocked_or_deferred"


class W02RegularityCandidateType(str, Enum):
    INSTANCE = "instance"
    KIND = "kind"
    STRUCTURAL_SIGNATURE = "structural_signature"
    AFFORDANCE = "affordance"
    SCENE_ROLE = "scene_role"
    LINEAGE = "lineage"
    UNKNOWN = "unknown"


class W02LineageHypothesisKind(str, Enum):
    SAME_INSTANCE = "same_instance"
    DUPLICATE_INSTANCE = "duplicate_instance"
    REPLACEMENT = "replacement"
    SPLIT_IDENTITY = "split_identity"
    MERGED_IDENTITY = "merged_identity"
    UNKNOWN_LINEAGE = "unknown_lineage"
    REVOKED_LINEAGE = "revoked_lineage"


class W02PresenceMode(str, Enum):
    PRESENT = "present"
    PARTIAL = "partial"
    SCAFFOLD_ONLY = "scaffold_only"
    ABSENT = "absent"
    CONTESTED = "contested"
    CONTRADICTORY = "contradictory"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class W02PromotionStatus(str, Enum):
    PROMOTED = "promoted"
    HELD = "held"
    BLOCKED = "blocked"
    CONTESTED = "contested"
    DOWNGRADED = "downgraded"
    REVALIDATION_REQUIRED = "revalidation_required"
    NO_CLEAN_REGULARITY_CLAIM = "no_clean_regularity_claim"


class W02ContradictionKind(str, Enum):
    IDENTITY_SWAP = "identity_swap"
    DUPLICATE_AMBIGUITY = "duplicate_ambiguity"
    REPLACEMENT_AMBIGUITY = "replacement_ambiguity"
    KIND_ROLE_COLLAPSE = "kind_role_collapse"
    STRUCTURAL_CONFLICT = "structural_conflict"
    AFFORDANCE_CONFLICT = "affordance_conflict"
    PRESENCE_MODE_CONFLICT = "presence_mode_conflict"
    SOURCE_AUTHORITY_CONFLICT = "source_authority_conflict"
    NEGATIVE_EVIDENCE = "negative_evidence"
    REVOKED_TRACE = "revoked_trace"
    MISSING_EXPECTED_TRACE = "missing_expected_trace"


@dataclass(frozen=True, slots=True)
class W02TraceRef:
    trace_id: str
    sequence_index: int
    entity_id: str
    source_authority: str
    presence_mode: W02PresenceMode
    admission_state: str
    confidence_band: str
    provenance_ref: tuple[str, ...]
    action_ref: str | None = None
    effect_ref: str | None = None
    structural_signature: str | None = None
    kind_label: str | None = None
    role_label: str | None = None
    provider_label: str | None = None
    contradiction_markers: tuple[str, ...] = ()
    is_duplicate_packet: bool = False
    provider_bias_marker: bool = False
    text_artifact_marker: bool = False
    revoked: bool = False
    candidate_type: W02RegularityCandidateType = W02RegularityCandidateType.INSTANCE


@dataclass(frozen=True, slots=True)
class W02ObjectRegularityRecord:
    regularity_id: str
    source_trace_refs: tuple[str, ...]
    maturity_level: W02ObjectMaturityLevel
    candidate_type: W02RegularityCandidateType
    source_authority_set: tuple[str, ...]
    temporal_span: tuple[int, int]
    evidence_count: int
    confidence_band: str
    uncertainty_markers: tuple[str, ...]
    promotion_status: W02PromotionStatus
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W02DisambiguationSlot:
    value: str | None
    confidence_band: str
    contradiction_status: str
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W02InstanceKindRoleDisambiguationRecord:
    instance_id_candidate: W02DisambiguationSlot
    kind_id_candidate: W02DisambiguationSlot
    role_id_candidate: W02DisambiguationSlot
    structural_signature_id: W02DisambiguationSlot
    affordance_pattern_id: W02DisambiguationSlot


@dataclass(frozen=True, slots=True)
class W02LineageHypothesis:
    lineage_kind: W02LineageHypothesisKind
    evidence_refs: tuple[str, ...]
    unresolved: bool


@dataclass(frozen=True, slots=True)
class W02LineageHypothesisSet:
    entity_id: str
    hypotheses: tuple[W02LineageHypothesis, ...]


@dataclass(frozen=True, slots=True)
class W02ContradictionLedgerEntry:
    conflict_id: str
    conflicting_trace_refs: tuple[str, ...]
    conflict_type: W02ContradictionKind
    affected_maturity_level: W02ObjectMaturityLevel
    severity: str
    unresolved_status: bool
    downgrade_action: str
    revalidation_requirement: str


@dataclass(frozen=True, slots=True)
class W02PromotionDecisionRecord:
    attempted_transition: str
    prior_level: W02ObjectMaturityLevel
    new_level: W02ObjectMaturityLevel
    gate_results: tuple[str, ...]
    failed_criteria: tuple[str, ...]
    passed_criteria: tuple[str, ...]
    decision_reason_codes: tuple[str, ...]
    consumer_visible_claim_boundary: str


@dataclass(frozen=True, slots=True)
class W02DowngradeOrRevalidationRecord:
    trigger_trace_ref: str
    violated_assumption: str
    downgraded_from: W02ObjectMaturityLevel
    downgraded_to: W02ObjectMaturityLevel
    blocked_downstream_permissions: tuple[str, ...]
    required_future_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W02DownstreamRegularityPermissionPacket:
    regularity_id: str
    may_use_as_scaffold: bool
    may_use_as_instance_hypothesis: bool
    may_use_as_kind_hint: bool
    may_use_as_affordance_hint: bool
    may_use_as_scene_role_hint: bool
    may_claim_stable_identity: bool
    must_preserve_uncertainty: bool
    must_abstain: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W02Telemetry:
    trace_selection_count: int
    candidate_count: int
    promoted_count: int
    blocked_count: int
    contested_count: int
    downgraded_count: int
    contradiction_count: int
    lineage_ambiguity_count: int
    consumer_ready: bool
    no_clean_regularities: bool
    must_abstain_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class W02ScopeMarker:
    scope: str
    staged_regularity_only: bool
    no_mature_object_identity_claim: bool
    no_object_permanence_claim: bool
    no_scene_graph_truth_claim: bool
    no_policy_selection_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W02GateDecision:
    consumer_ready: bool
    clean_regularity_claim_allowed: bool
    accepted_count: int
    blocked_count: int
    contested_count: int
    downgraded_count: int
    contradiction_count: int
    lineage_ambiguity_count: int
    must_abstain_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W02InputBundle:
    bundle_id: str
    traces: tuple[W02TraceRef, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class W02ResultBundle:
    bundle_id: str
    regularity_records: tuple[W02ObjectRegularityRecord, ...]
    disambiguation_records: tuple[W02InstanceKindRoleDisambiguationRecord, ...]
    promotion_decisions: tuple[W02PromotionDecisionRecord, ...]
    contradiction_ledger: tuple[W02ContradictionLedgerEntry, ...]
    lineage_hypotheses: tuple[W02LineageHypothesisSet, ...]
    downgrade_records: tuple[W02DowngradeOrRevalidationRecord, ...]
    downstream_permission_packets: tuple[W02DownstreamRegularityPermissionPacket, ...]
    telemetry: W02Telemetry
    scope_marker: W02ScopeMarker
    gate: W02GateDecision
    reason: str
