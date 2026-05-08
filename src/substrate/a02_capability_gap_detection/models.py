from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class A02DemandClass(str, Enum):
    REGULATORY = "regulatory"
    CONTINUITY = "continuity"
    SELF_REPAIR = "self_repair"
    WORLD_FACING = "world_facing"
    COMMUNICATION = "communication"
    INTERNAL_TOOL = "internal_tool"
    EXPLORATORY = "exploratory"
    COMMITMENT_DRIVEN = "commitment_driven"


class A02DemandLegitimacyStatus(str, Enum):
    TYPED_LEGITIMATE = "typed_legitimate"
    WEAKLY_TYPED = "weakly_typed"
    NARRATIVE_WISH_ONLY = "narrative_wish_only"
    INVALID_NO_EFFECT_SCOPE = "invalid_no_effect_scope"


class A02CoverageStatus(str, Enum):
    FULLY_COVERED = "fully_covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_COVERED = "not_covered"
    BLOCKED = "blocked"
    CONTESTED = "contested"
    NO_CLEAN_COVERAGE_CLAIM = "no_clean_coverage_claim"


class A02GapKind(str, Enum):
    MISSING_AFFORDANCE = "missing_affordance"
    UNAVAILABLE_AFFORDANCE = "unavailable_affordance"
    LOW_RELIABILITY_AFFORDANCE = "low_reliability_affordance"
    INSUFFICIENT_EFFECT_SCOPE = "insufficient_effect_scope"
    COMPOSITION_GAP = "composition_gap"
    OWNERSHIP_BOUNDARY_GAP = "ownership_boundary_gap"
    RESOURCE_BLOCKED_GAP = "resource_blocked_gap"
    PRECONDITION_UNSATISFIED_GAP = "precondition_unsatisfied_gap"
    INVALIDATED_AFFORDANCE_GAP = "invalidated_affordance_gap"
    UNKNOWN_CAPABILITY_STATUS = "unknown_capability_status"
    NO_GAP = "no_gap"


class A02CompositionStatus(str, Enum):
    NO_COMPOSITION_NEEDED = "no_composition_needed"
    COVERED_BY_COMPOSITION = "covered_by_composition"
    COMPOSITION_POSSIBLE_BUT_UNVERIFIED = "composition_possible_but_unverified"
    COMPOSITION_MISSING = "composition_missing"
    COMPOSITION_FORBIDDEN = "composition_forbidden"
    COMPOSITION_UNKNOWN = "composition_unknown"


class A02ControllabilityStatus(str, Enum):
    CONTROLLABLE_CURRENTLY = "controllable_currently"
    CONTROLLABLE_ONLY_CONDITIONALLY = "controllable_only_conditionally"
    LOW_RELIABILITY = "low_reliability"
    OUTSIDE_CURRENT_CONTROL = "outside_current_control"
    MIXED_OR_CONTAMINATED = "mixed_or_contaminated"
    UNKNOWN = "unknown"


class A02BlockingKind(str, Enum):
    DISABLED_EFFECTOR = "disabled_effector"
    INVALIDATED_ASSUMPTION = "invalidated_assumption"
    MISSING_OBSERVATION_CHANNEL = "missing_observation_channel"
    MODE_RESTRICTED = "mode_restricted"
    RESOURCE_LIMITED = "resource_limited"
    TEMPORAL_VALIDITY_BLOCKED = "temporal_validity_blocked"
    OWNERSHIP_BOUNDARY_BLOCKED = "ownership_boundary_blocked"
    PRECONDITION_UNSATISFIED = "precondition_unsatisfied"


class A02DownstreamRouteHint(str, Enum):
    PROCEED_WITH_COVERED_DEMAND = "proceed_with_covered_demand"
    RESTORE_BLOCKING_CONDITION = "restore_blocking_condition"
    EXPLORE_MISSING_AFFORDANCE = "explore_missing_affordance"
    SEARCH_COMPOSITION = "search_composition"
    DEFER_DEMAND = "defer_demand"
    SUPPRESS_AGENCY_OVERCLAIM = "suppress_agency_overclaim"
    REVALIDATE_ONTOLOGY_OR_DEMAND = "revalidate_ontology_or_demand"


class A02ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_BASIS = "insufficient_basis"


class A02DownstreamReadinessStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class A02DemandPacket:
    demand_id: str
    demanded_change_class: A02DemandClass
    demanded_scope: tuple[str, ...]
    target_channels: tuple[str, ...]
    source_kind: str
    source_ref: str
    urgency: str
    severity: int
    allowed_latency: str
    legitimacy_status: A02DemandLegitimacyStatus
    required_controllability: A02ControllabilityStatus
    world_side_requirement: str
    provenance: tuple[str, ...] = ()
    planner_deadend_signal: bool = False
    low_confidence_signal: bool = False


@dataclass(frozen=True, slots=True)
class A02DemandSet:
    demand_set_id: str
    demands: tuple[A02DemandPacket, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class A02CapabilityGapInput:
    demand_set: A02DemandSet | None
    source_lineage: tuple[str, ...] = ()
    ownership_boundary_basis: tuple[str, ...] = ()
    composition_enabled: bool = True


@dataclass(frozen=True, slots=True)
class A02AffordanceCoverageCandidate:
    demand_id: str
    affordance_id: str
    coverage_scope: tuple[str, ...]
    missing_scope: tuple[str, ...]
    target_channel_overlap: tuple[str, ...]
    validity_status: str


@dataclass(frozen=True, slots=True)
class A02CoverageEvidence:
    demand_id: str
    matched_scope: tuple[str, ...]
    unmatched_scope: tuple[str, ...]
    matched_channels: tuple[str, ...]
    unmatched_channels: tuple[str, ...]
    basis_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A02BlockingConstraint:
    kind: A02BlockingKind
    detail: str
    source_ref: str


@dataclass(frozen=True, slots=True)
class A02PartialCoverageRecord:
    demand_id: str
    covered_scope: tuple[str, ...]
    residual_scope: tuple[str, ...]
    covered_channels: tuple[str, ...]
    residual_channels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A02CompositionStep:
    step_id: str
    affordance_id: str
    contributes_scope: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A02CompositionRoute:
    route_id: str
    steps: tuple[A02CompositionStep, ...]
    verified: bool


@dataclass(frozen=True, slots=True)
class A02CapabilityGapEntry:
    demand_id: str
    coverage_status: A02CoverageStatus
    gap_kind: A02GapKind
    matching_affordance_candidates: tuple[A02AffordanceCoverageCandidate, ...]
    blocked_by: tuple[A02BlockingConstraint, ...]
    required_conditions: tuple[str, ...]
    composition_status: A02CompositionStatus
    composition_route_refs: tuple[str, ...]
    partial_coverage: A02PartialCoverageRecord | None
    controllability_status: A02ControllabilityStatus
    ownership_boundary_status: str
    severity: int
    confidence: A02ConfidenceBand
    downstream_route_hint: A02DownstreamRouteHint
    coverage_evidence: A02CoverageEvidence
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class A02GapLedgerEntry:
    ledger_entry_id: str
    demand_id: str
    coverage_status: A02CoverageStatus
    gap_kind: A02GapKind
    reason: str


@dataclass(frozen=True, slots=True)
class A02CapabilityGapLedger:
    ledger_id: str
    entries: tuple[A02GapLedgerEntry, ...]
    source_lineage_refs: tuple[str, ...]
    source_lineage_count: int
    source_lineage_complete: bool
    canonical_id_hint_used_count: int
    canonical_id_generated_count: int
    canonical_id_coverage_complete: bool
    no_affordance_invention_observed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A02CapabilityGapGateDecision:
    gap_packet_consumer_ready: bool
    partial_coverage_consumer_ready: bool
    ownership_boundary_consumer_ready: bool
    composition_consumer_ready: bool
    downstream_readiness_status: A02DownstreamReadinessStatus
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A02ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    capability_gap_not_planner: bool
    depends_on_a01_canonical_ontology: bool
    no_map_wide_claim: bool
    no_affordance_discovery_claim: bool
    no_hidden_action_execution_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class A02Telemetry:
    demand_count: int
    gap_entry_count: int
    fully_covered_count: int
    partial_coverage_count: int
    missing_gap_count: int
    blocked_gap_count: int
    composition_gap_count: int
    composition_unverified_count: int
    ownership_boundary_gap_count: int
    no_clean_coverage_count: int
    source_lineage_count: int
    source_lineage_complete: bool
    canonical_id_hint_used_count: int
    canonical_id_generated_count: int
    canonical_id_coverage_complete: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class A02CapabilityGapResult:
    demand_set_id: str
    gap_entries: tuple[A02CapabilityGapEntry, ...]
    ledger: A02CapabilityGapLedger
    gate: A02CapabilityGapGateDecision
    scope_marker: A02ScopeMarker
    telemetry: A02Telemetry
    reason: str
