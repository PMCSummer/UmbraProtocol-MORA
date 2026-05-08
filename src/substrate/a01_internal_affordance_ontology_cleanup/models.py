from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class A01AffordanceClass(str, Enum):
    SENSING_MONITORING = "sensing_monitoring"
    REGULATION_ADJUSTMENT = "regulation_adjustment"
    INTERNAL_MODE_SHIFT = "internal_mode_shift"
    REPAIR_RECOVERY = "repair_recovery"
    DEFER_REVISIT = "defer_revisit"
    COMMUNICATION_OUTPUT = "communication_output"
    INHIBITION_SUPPRESSION = "inhibition_suppression"
    EXPLORATION_DIVERSIFICATION = "exploration_diversification"
    WORLD_DIRECTED_ACTION = "world_directed_action"
    OBSERVATION_ONLY = "observation_only"
    INTERNAL_ONLY = "internal_only"


class A01MergeRelationType(str, Enum):
    TRUE_ALIAS = "true_alias"
    DUPLICATE_PROVENANCE_VARIANT = "duplicate_provenance_variant"
    SAME_LABEL_DIFFERENT_PRECONDITION = "same_label_different_precondition"
    SAME_OUTCOME_DIFFERENT_CONTROLLABILITY = "same_outcome_different_controllability"
    PARENT_CHILD_GRANULARITY = "parent_child_granularity"
    DISTINCT = "distinct"


class A01SplitRelationType(str, Enum):
    PRECONDITION_SPLIT = "precondition_split"
    CONTROLLABILITY_SPLIT = "controllability_split"
    CLASS_BOUNDARY_SPLIT = "class_boundary_split"
    GRANULARITY_SPLIT = "granularity_split"


class A01ValidityStatus(str, Enum):
    VALID = "valid"
    NARROWED = "narrowed"
    DEPRECATED = "deprecated"
    CONTESTED = "contested"
    UNAVAILABLE = "unavailable"


class A01ControllabilityClass(str, Enum):
    SELF_CONTROLLED = "self_controlled"
    SHARED_CONTROLLED = "shared_controlled"
    WORLD_DEPENDENT = "world_dependent"
    OBSERVATIONAL = "observational"
    UNKNOWN = "unknown"


class A01OwnershipRelevance(str, Enum):
    SELF_RELEVANT = "self_relevant"
    WORLD_RELEVANT = "world_relevant"
    MIXED_RELEVANT = "mixed_relevant"
    UNKNOWN_RELEVANCE = "unknown_relevance"


class A01CanonicalizationStatus(str, Enum):
    CANONICALIZED = "canonicalized"
    CONTESTED = "contested"
    DEPRECATED = "deprecated"
    UNAVAILABLE = "unavailable"


class A01DownstreamReadinessStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class A01PreconditionProfile:
    requirements: tuple[str, ...]
    temporal_constraints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A01EffectScopeProfile:
    primary_outcomes: tuple[str, ...]
    side_effect_channels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A01ControllabilityProfile:
    controllability_class: A01ControllabilityClass
    confidence: float
    basis_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class A01ObservationExpectation:
    expected_signals: tuple[str, ...]
    verification_required: bool


@dataclass(frozen=True, slots=True)
class A01IncompatibilityRecord:
    incompatibility_id: str
    with_affordance_ref: str
    reason: str


@dataclass(frozen=True, slots=True)
class A01RawAffordanceCandidate:
    candidate_id: str
    local_label: str
    affordance_class: A01AffordanceClass
    aliases: tuple[str, ...]
    provenance: str
    preconditions: A01PreconditionProfile
    effect_scope: A01EffectScopeProfile
    target_channels: tuple[str, ...]
    controllability: A01ControllabilityProfile
    observation_expectation: A01ObservationExpectation
    incompatibilities: tuple[A01IncompatibilityRecord, ...] = ()
    interruption_semantics: str = "bounded_interruptible"
    ownership_relevance: A01OwnershipRelevance = A01OwnershipRelevance.UNKNOWN_RELEVANCE
    self_world_relevance: str = "unknown"
    granularity_level: int = 1
    assumption_valid: bool = True
    effector_enabled: bool = True
    canonical_id_hint: str | None = None
    legacy_local_label_only: bool = False


@dataclass(frozen=True, slots=True)
class A01RawAffordanceCandidateSet:
    candidate_set_id: str
    candidates: tuple[A01RawAffordanceCandidate, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class A01AffordanceAliasRecord:
    alias_id: str
    canonical_affordance_id: str
    alias_label: str
    source_candidate_ref: str
    relation_type: A01MergeRelationType


@dataclass(frozen=True, slots=True)
class A01ParentChildRelation:
    relation_id: str
    parent_affordance_id: str
    child_affordance_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class A01MergeDecision:
    decision_id: str
    relation_type: A01MergeRelationType
    kept_candidate_ref: str
    merged_candidate_refs: tuple[str, ...]
    canonical_affordance_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class A01SplitDecision:
    decision_id: str
    relation_type: A01SplitRelationType
    source_candidate_refs: tuple[str, ...]
    produced_affordance_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A01ContestedCanonicalization:
    contested_id: str
    candidate_refs: tuple[str, ...]
    contested_reason: str
    unresolved: bool


@dataclass(frozen=True, slots=True)
class A01GranularityConflict:
    conflict_id: str
    candidate_refs: tuple[str, ...]
    parent_child_possible: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A01ValidityStatusRecord:
    affordance_id: str
    status: A01ValidityStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A01CanonicalAffordanceEntry:
    affordance_id: str
    canonical_label: str
    affordance_class: A01AffordanceClass
    aliases: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    validity_status: A01ValidityStatus
    canonicalization_status: A01CanonicalizationStatus
    preconditions: A01PreconditionProfile
    effect_scope: A01EffectScopeProfile
    target_channels: tuple[str, ...]
    controllability: A01ControllabilityProfile
    observation_expectation: A01ObservationExpectation
    incompatibilities: tuple[A01IncompatibilityRecord, ...]
    interruption_semantics: str
    ownership_relevance: A01OwnershipRelevance
    self_world_relevance: str
    parent_affordance_id: str | None
    child_affordance_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A01OntologyCleanupLedger:
    ledger_id: str
    merge_decisions: tuple[A01MergeDecision, ...]
    split_decisions: tuple[A01SplitDecision, ...]
    alias_records: tuple[A01AffordanceAliasRecord, ...]
    parent_child_relations: tuple[A01ParentChildRelation, ...]
    contested: tuple[A01ContestedCanonicalization, ...]
    granularity_conflicts: tuple[A01GranularityConflict, ...]
    validity_records: tuple[A01ValidityStatusRecord, ...]
    same_label_diff_precondition_count: int
    class_conflict_count: int
    legacy_label_bypass_detected: bool
    source_lineage_refs: tuple[str, ...]
    source_lineage_count: int
    source_lineage_complete: bool
    canonical_id_hint_used_count: int
    canonical_id_generated_count: int
    canonical_id_coverage_complete: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A01CanonicalOntologySnapshot:
    snapshot_id: str
    canonical_entries: tuple[A01CanonicalAffordanceEntry, ...]
    ledger: A01OntologyCleanupLedger
    reason: str


@dataclass(frozen=True, slots=True)
class A01OntologyGateDecision:
    canonical_affordance_consumer_ready: bool
    contested_affordance_consumer_ready: bool
    deprecated_affordance_consumer_ready: bool
    downstream_readiness_status: A01DownstreamReadinessStatus
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A01ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    ontology_cleanup_not_planner_selection: bool
    no_hidden_planner_selection_authority: bool
    no_map_wide_migration_claim: bool
    no_world_ontology_completeness_claim: bool
    no_affordance_discovery_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A01Telemetry:
    raw_candidate_count: int
    canonical_entry_count: int
    merged_alias_group_count: int
    split_decision_count: int
    contested_entry_count: int
    deprecated_entry_count: int
    parent_child_relation_count: int
    same_label_diff_precondition_count: int
    class_conflict_count: int
    legacy_label_bypass_detected: bool
    source_lineage_count: int
    source_lineage_complete: bool
    canonical_id_hint_used_count: int
    canonical_id_generated_count: int
    canonical_id_coverage_complete: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class A01CanonicalOntologyResult:
    ontology_snapshot: A01CanonicalOntologySnapshot
    gate: A01OntologyGateDecision
    scope_marker: A01ScopeMarker
    telemetry: A01Telemetry
    reason: str
