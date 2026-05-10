from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class W03SchemaChannel(str, Enum):
    INSTANCE_PRIOR = "instance_prior"
    KIND_PRIOR = "kind_prior"
    SCENE_ROLE_PRIOR = "scene_role_prior"
    STRUCTURAL_SIGNATURE_PRIOR = "structural_signature_prior"
    AFFORDANCE_PRIOR = "affordance_prior"
    MULTI_CHANNEL_CONTESTED = "multi_channel_contested"


class W03SchemaStatus(str, Enum):
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    SCHEMA_CANDIDATE = "schema_candidate"
    NARROW_PRIOR = "narrow_prior"
    BOUNDED_PRIOR = "bounded_prior"
    OPERATIONAL_DEFAULT = "operational_default"
    CONTESTED = "contested"
    STALE = "stale"
    MUST_REVALIDATE = "must_revalidate"
    DOWNGRADED = "downgraded"
    QUARANTINED = "quarantined"
    SPLIT_REQUIRED = "split_required"
    NO_CLEAN_SCHEMA_CLAIM = "no_clean_schema_claim"


class W03ContradictionConsequenceRoute(str, Enum):
    INVALIDATE = "invalidate"
    DOWNGRADE = "downgrade"
    REVALIDATE = "revalidate"
    SPLIT = "split"
    QUARANTINE = "quarantine"
    BLOCK_DOWNSTREAM_USE = "block_downstream_use"
    RETAIN_AS_NARROW_CONTESTED_PRIOR = "retain_as_narrow_contested_prior"
    NO_CONSEQUENCE_BECAUSE_IRRELEVANT = "no_consequence_because_irrelevant"


class W03SchemaVersionTrigger(str, Enum):
    INITIAL_CONSOLIDATION = "initial_consolidation"
    SUPPORT_EXPANSION = "support_expansion"
    CONTRADICTION_DOWNGRADE = "contradiction_downgrade"
    STALE_REVALIDATION = "stale_revalidation"
    SPLIT_REQUIRED = "split_required"


@dataclass(frozen=True, slots=True)
class W03SchemaCandidateRecord:
    schema_id: str
    schema_channel: W03SchemaChannel
    support_regularities: tuple[str, ...]
    negative_evidence_refs: tuple[str, ...]
    source_authority_scope: tuple[str, ...]
    context_scope: tuple[str, ...]
    temporal_span: tuple[int, int]
    applicability_conditions: tuple[str, ...]
    confidence_band: str
    maturity_basis: tuple[str, ...]
    unresolved_contradictions: tuple[str, ...]
    stale_markers: tuple[str, ...]
    status: W03SchemaStatus
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W03EverydayPriorRecord:
    prior_id: str
    schema_id: str
    prior_statement: str
    operational_default_status: bool
    allowed_use_cases: tuple[str, ...]
    blocked_use_cases: tuple[str, ...]
    override_conditions: tuple[str, ...]
    revalidation_conditions: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    claim_boundary: str
    status: W03SchemaStatus
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W03SchemaChannelState:
    schema_channel: W03SchemaChannel
    support_count: int
    contradiction_count: int
    stale_count: int
    status: W03SchemaStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W03ContradictionConsequenceRecord:
    conflict_id: str
    consequence_route: W03ContradictionConsequenceRoute
    affected_schema_ids: tuple[str, ...]
    action_taken: str
    downstream_permission_change: tuple[str, ...]
    unresolved_status: bool
    future_revalidation_requirement: str


@dataclass(frozen=True, slots=True)
class W03SchemaVersionRecord:
    schema_id: str
    prior_version: int
    new_version: int
    update_trigger: W03SchemaVersionTrigger
    accepted_evidence_refs: tuple[str, ...]
    rejected_evidence_refs: tuple[str, ...]
    changed_commitments: tuple[str, ...]
    split_from: tuple[str, ...]
    merged_from: tuple[str, ...]
    downgraded_from: tuple[str, ...]
    audit_reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W03StaleSchemaAssessment:
    schema_id: str
    last_validated_at: str
    stale_risk: str
    drift_type: str
    missing_expected_evidence: tuple[str, ...]
    authority_revocation_status: bool
    revalidation_required: bool
    blocked_until_revalidated: bool


@dataclass(frozen=True, slots=True)
class W03DownstreamSchemaPermissionPacket:
    schema_id: str
    channel: W03SchemaChannel
    may_use_as_bounded_prior: bool
    may_use_as_schema_hint: bool
    may_use_as_operational_default: bool
    must_revalidate_before_use: bool
    must_preserve_contradiction: bool
    must_abstain: bool
    prohibited_claims: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W03Telemetry:
    regularity_intake_count: int
    schema_candidate_count: int
    everyday_prior_count: int
    operational_default_count: int
    contested_count: int
    stale_count: int
    must_revalidate_count: int
    must_abstain_count: int
    contradiction_count: int
    version_update_count: int
    consumer_ready: bool
    no_clean_schema: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class W03GateDecision:
    consumer_ready: bool
    no_clean_schema: bool
    must_revalidate_count: int
    must_abstain_count: int
    contradiction_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W03ScopeMarker:
    scope: str
    schema_consolidation_only: bool
    no_mature_world_truth_claim: bool
    no_common_sense_engine_claim: bool
    no_planner_claim: bool
    no_memory_lifecycle_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W03InputBundle:
    bundle_id: str
    source_lineage: tuple[str, ...]
    w02_regularity_records: tuple[object, ...]
    w02_permission_packets: tuple[object, ...]
    w02_contradiction_ledger: tuple[object, ...]
    reason: str = ""
    previous_schema_versions: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class W03ResultBundle:
    bundle_id: str
    schema_candidates: tuple[W03SchemaCandidateRecord, ...]
    everyday_priors: tuple[W03EverydayPriorRecord, ...]
    channel_states: tuple[W03SchemaChannelState, ...]
    contradiction_consequences: tuple[W03ContradictionConsequenceRecord, ...]
    version_records: tuple[W03SchemaVersionRecord, ...]
    stale_assessments: tuple[W03StaleSchemaAssessment, ...]
    split_or_merge_proposals: tuple[str, ...]
    downstream_permission_packets: tuple[W03DownstreamSchemaPermissionPacket, ...]
    telemetry: W03Telemetry
    gate: W03GateDecision
    scope_marker: W03ScopeMarker
    no_claim_markers: tuple[str, ...]
    reason: str
