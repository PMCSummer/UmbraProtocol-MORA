from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SourceScopeClass(str, Enum):
    DIRECT_ASSERTION = "direct_assertion"
    QUOTED = "quoted"
    REPORTED = "reported"
    QUESTIONED = "questioned"
    HYPOTHETICAL = "hypothetical"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class TargetScopeClass(str, Enum):
    SELF_DIRECTED = "self_directed"
    USER_DIRECTED = "user_directed"
    THIRD_PARTY_DIRECTED = "third_party_directed"
    WORLD_DIRECTED = "world_directed"
    DISCOURSE_DIRECTED = "discourse_directed"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class ApplicabilityClass(str, Enum):
    SELF_APPLICABLE = "self_applicable"
    SELF_MENTIONED_BUT_NOT_SELF_APPLICABLE = "self_mentioned_but_not_self_applicable"
    USER_APPLICABLE = "user_applicable"
    THIRD_PARTY_APPLICABLE = "third_party_applicable"
    WORLD_DESCRIPTIVE = "world_descriptive"
    QUOTED_EXTERNAL = "quoted_external"
    REPORTED_EXTERNAL = "reported_external"
    HYPOTHETICAL_NONCOMMITTING = "hypothetical_noncommitting"
    DENIED_NONUPDATING = "denied_nonupdating"
    MIXED_APPLICABILITY = "mixed_applicability"
    UNRESOLVED_APPLICABILITY = "unresolved_applicability"


class CommitmentLevel(str, Enum):
    NONCOMMITTING = "noncommitting"
    ASSERTIVE_BOUNDED = "assertive_bounded"
    DENIED = "denied"
    QUESTIONED = "questioned"
    HYPOTHETICAL = "hypothetical"
    EXTERNAL_REPORTED = "external_reported"


class SelfApplicabilityStatus(str, Enum):
    SELF_APPLICABLE = "self_applicable"
    SELF_MENTIONED_BLOCKED = "self_mentioned_blocked"
    NOT_SELF_TARGETED = "not_self_targeted"
    UNRESOLVED_SELF_REFERENCE = "unresolved_self_reference"


class ApplicabilityUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ApplicabilityRecord:
    attribution_id: str
    semantic_unit_id: str | None
    proposition_id: str
    source_scope_class: SourceScopeClass
    target_scope_class: TargetScopeClass
    applicability_class: ApplicabilityClass
    commitment_level: CommitmentLevel
    self_applicability_status: SelfApplicabilityStatus
    downstream_permissions: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class PermissionMapping:
    proposition_id: str
    permissions: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class ApplicabilityBundle:
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_proposition_ids: tuple[str, ...]
    linked_semantic_unit_ids: tuple[str, ...]
    records: tuple[ApplicabilityRecord, ...]
    permission_mappings: tuple[PermissionMapping, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    no_truth_upgrade: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ApplicabilityGateDecision:
    accepted: bool
    usability_class: ApplicabilityUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_record_ids: tuple[str, ...]
    rejected_record_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ApplicabilityTelemetry:
    source_lineage: tuple[str, ...]
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    record_count: int
    permission_mapping_count: int
    source_scope_classes: tuple[str, ...]
    target_scope_classes: tuple[str, ...]
    applicability_classes: tuple[str, ...]
    self_applicability_statuses: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: ApplicabilityGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ApplicabilityResult:
    bundle: ApplicabilityBundle
    telemetry: ApplicabilityTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_truth_upgrade: bool
