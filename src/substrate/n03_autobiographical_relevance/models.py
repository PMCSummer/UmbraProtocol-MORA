from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class N03AutobiographicalTraceKind(str, Enum):
    PRIOR_FAILURE = "prior_failure"
    PRIOR_RECOVERY = "prior_recovery"
    PRIOR_COMMITMENT_KEPT = "prior_commitment_kept"
    PRIOR_COMMITMENT_BROKEN = "prior_commitment_broken"
    CAPABILITY_BOUNDARY_TRACE = "capability_boundary_trace"
    TOOL_USE_TRACE = "tool_use_trace"
    REGULATORY_BREAKDOWN = "regulatory_breakdown"
    REGULATORY_STABILIZATION = "regulatory_stabilization"
    IDENTITY_DRIFT_SENSITIVE_TRACE = "identity_drift_sensitive_trace"
    GENERIC_MEMORY_ONLY = "generic_memory_only"


class N03CurrentTargetKind(str, Enum):
    REGULATION_DEMAND = "regulation_demand"
    PLANNING_DEMAND = "planning_demand"
    CAPABILITY_GAP_DEMAND = "capability_gap_demand"
    COMMITMENT_UNDER_LOAD = "commitment_under_load"
    RECOVERY_NEED = "recovery_need"
    PLAN_CONSTRAINT_NEED = "plan_constraint_need"
    STABILIZATION_NEED = "stabilization_need"


class N03RelevanceKind(str, Enum):
    REGULATORY_WARNING = "regulatory_warning"
    PLANNING_CONSTRAINT = "planning_constraint"
    CAUTIONARY_RELEVANCE = "cautionary_relevance"
    COMMITMENT_PRESERVING_RELEVANCE = "commitment_preserving_relevance"
    CAPABILITY_BOUNDARY_RELEVANCE = "capability_boundary_relevance"
    RECOVERY_PATTERN_RELEVANCE = "recovery_pattern_relevance"
    IDENTITY_STABILITY_RELEVANCE = "identity_stability_relevance"
    NO_AUTOBIOGRAPHICAL_RELEVANCE = "no_autobiographical_relevance"


class N03TransferDecision(str, Enum):
    USE_AS_CAUTION = "use_as_caution"
    USE_AS_SUPPORTING_PATTERN = "use_as_supporting_pattern"
    USE_AS_COMMITMENT_ANCHOR = "use_as_commitment_anchor"
    USE_AS_REGULATORY_WARNING = "use_as_regulatory_warning"
    USE_AS_PLAN_CONSTRAINT = "use_as_plan_constraint"
    USE_AS_RECOVERY_TEMPLATE = "use_as_recovery_template"
    DO_NOT_TRANSFER = "do_not_transfer"
    PROVISIONAL_TRANSFER_ONLY = "provisional_transfer_only"
    NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER = "no_safe_autobiographical_transfer"
    CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE = "conflicting_autobiographical_guidance"


class N03TransferScope(str, Enum):
    CURRENT_TICK_ONLY = "current_tick_only"
    CURRENT_DEMAND_ONLY = "current_demand_only"
    CURRENT_CONTEXT_ONLY = "current_context_only"
    SAME_COMMITMENT_REGION_ONLY = "same_commitment_region_only"
    SAME_CAPABILITY_BOUNDARY_ONLY = "same_capability_boundary_only"
    SAME_RECOVERY_PATTERN_ONLY = "same_recovery_pattern_only"
    BROAD_TRANSFER_BLOCKED = "broad_transfer_blocked"


class N03StructuralDimension(str, Enum):
    COMMITMENT_MATCH = "commitment_match"
    CAPABILITY_GAP_MATCH = "capability_gap_match"
    AFFORDANCE_CONTOUR_MATCH = "affordance_contour_match"
    INTERNAL_TOOL_MATCH = "internal_tool_match"
    SELF_BINDING_MATCH = "self_binding_match"
    ATTRIBUTION_MATCH = "attribution_match"
    FAILURE_PATTERN_MATCH = "failure_pattern_match"
    RECOVERY_PATTERN_MATCH = "recovery_pattern_match"
    IDENTITY_DRIFT_COMPATIBLE = "identity_drift_compatible"
    TEMPORAL_VALIDITY_SUPPORTED = "temporal_validity_supported"
    SEMANTIC_SIMILARITY_ONLY = "semantic_similarity_only"


class N03LimitingReason(str, Enum):
    SEMANTIC_SIMILARITY_ONLY = "semantic_similarity_only"
    RECENCY_ONLY = "recency_only"
    VIVIDNESS_NOT_SUFFICIENT = "vividness_not_sufficient"
    GENERIC_MEMORY_NOT_SELF_LINE = "generic_memory_not_self_line"
    IDENTITY_DRIFT_REDUCES_TRANSFER = "identity_drift_reduces_transfer"
    AFFORDANCE_SPACE_CHANGED = "affordance_space_changed"
    CAPABILITY_BOUNDARY_CHANGED = "capability_boundary_changed"
    SELF_BINDING_MISMATCH = "self_binding_mismatch"
    ATTRIBUTION_TOO_MIXED = "attribution_too_mixed"
    SINGLE_EPISODE_OVERGENERALIZATION_RISK = "single_episode_overgeneralization_risk"
    CURRENT_EVIDENCE_CONTRADICTS_PAST_TRACE = "current_evidence_contradicts_past_trace"
    TRACE_OUTDATED = "trace_outdated"
    CONFLICTING_TRACE_SET = "conflicting_trace_set"
    INSUFFICIENT_STRUCTURAL_MATCH = "insufficient_structural_match"


@dataclass(frozen=True, slots=True)
class N03TraceCandidate:
    source_trace_id: str
    trace_kind: N03AutobiographicalTraceKind
    semantic_topic_tags: tuple[str, ...]
    commitment_refs: tuple[str, ...]
    capability_gap_refs: tuple[str, ...]
    affordance_refs: tuple[str, ...]
    internal_tool_refs: tuple[str, ...]
    self_binding_refs: tuple[str, ...]
    attribution_profile: str
    failure_or_recovery_signature: str
    identity_region_refs: tuple[str, ...]
    temporal_validity_status: str
    recurrence_count: int
    vividness_hint: float
    recency_hint: float
    confidence: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class N03CurrentTarget:
    current_target_id: str
    target_kind: N03CurrentTargetKind
    active_commitment_refs: tuple[str, ...]
    active_capability_gap_refs: tuple[str, ...]
    active_affordance_refs: tuple[str, ...]
    active_internal_tool_refs: tuple[str, ...]
    active_self_binding_refs: tuple[str, ...]
    active_identity_region_refs: tuple[str, ...]
    active_drift_markers: tuple[str, ...]
    semantic_topic_tags: tuple[str, ...]
    attribution_profile: str
    regulation_or_planning_pressure: float
    current_evidence_signature: str
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class N03AutobiographicalRelevanceEntry:
    relevance_id: str
    source_trace_id: str
    current_target_id: str
    relevance_kind: N03RelevanceKind
    relevance_strength: float
    transfer_decision: N03TransferDecision
    transfer_scope: N03TransferScope
    supported_by_dimensions: tuple[N03StructuralDimension, ...]
    anti_generalization_limits: tuple[str, ...]
    limiting_reasons: tuple[N03LimitingReason, ...]
    drift_adjustment: str
    confidence: float
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class N03LedgerEntry:
    ledger_entry_id: str
    source_trace_id: str
    current_target_id: str
    transfer_decision: N03TransferDecision
    reason_codes: tuple[str, ...]
    supported_dimensions: tuple[N03StructuralDimension, ...]
    limiting_reasons: tuple[N03LimitingReason, ...]
    transfer_scope: N03TransferScope


@dataclass(frozen=True, slots=True)
class N03GateDecision:
    consumer_ready: bool
    transfer_packet_consumer_ready: bool
    consistency_consumer_ready: bool
    relevant_trace_count: int
    blocked_transfer_count: int
    conflict_count: int
    provisional_transfer_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class N03Telemetry:
    trace_candidate_count: int
    current_target_count: int
    relevance_entry_count: int
    relevant_trace_count: int
    blocked_transfer_count: int
    conflict_count: int
    provisional_transfer_count: int
    no_safe_transfer_count: int
    consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class N03ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    autobiographical_relevance_not_retrieval: bool
    autobiographical_relevance_not_planner: bool
    autobiographical_relevance_not_memory_lifecycle: bool
    autobiographical_relevance_not_identity_generator: bool
    reason: str


@dataclass(frozen=True, slots=True)
class N03InputBundle:
    bundle_id: str
    trace_candidates: tuple[N03TraceCandidate, ...]
    current_targets: tuple[N03CurrentTarget, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class N03Result:
    bundle_id: str
    relevance_entries: tuple[N03AutobiographicalRelevanceEntry, ...]
    ledger: tuple[N03LedgerEntry, ...]
    telemetry: N03Telemetry
    gate: N03GateDecision
    scope_marker: N03ScopeMarker
    reason: str
