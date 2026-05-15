from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class W06ErrorType(str, Enum):
    EXPECTATION_VIOLATION = "expectation_violation"
    CONTRADICTION = "contradiction"
    AUTHORITY_CONFLICT = "authority_conflict"
    TEMPORAL_DRIFT = "temporal_drift"
    IDENTITY_CONFLICT = "identity_conflict"
    PROTECTED_BOUNDARY = "protected_boundary"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    AMBIGUOUS_MISMATCH = "ambiguous_mismatch"


class W06ViolatedExpectationSource(str, Enum):
    DESIRED = "desired"
    PREDICTED = "predicted"
    OBSERVED = "observed"
    PERMITTED = "permitted"
    PRIOR_SCHEMA_LINEAGE = "prior_schema_lineage"
    AUTHORITY_SCOPE = "authority_scope"
    TEMPORAL_WINDOW = "temporal_window"
    CONSTITUTIONAL_GUARD = "constitutional_guard"


class W06MismatchClass(str, Enum):
    NO_MISMATCH = "no_mismatch"
    WORLD_MODEL = "world_model"
    ACTION_EFFECT = "action_effect"
    AFFORDANCE = "affordance"
    OWNERSHIP = "ownership"
    GOAL_SATISFACTION = "goal_satisfaction"
    VALIDITY = "validity"
    AUTHORITY_SCOPE = "authority_scope"
    TEMPORAL_SCOPE = "temporal_scope"
    CONSTITUTIONAL_BOUNDARY = "constitutional_boundary"
    DESIRED_VS_PREDICTED = "desired_vs_predicted"
    PREDICTED_VS_OBSERVED = "predicted_vs_observed"
    OBSERVED_VS_PERMITTED = "observed_vs_permitted"
    DESIRED_VS_PERMITTED = "desired_vs_permitted"
    PRIOR_VS_CURRENT_EVIDENCE = "prior_vs_current_evidence"
    AMBIGUOUS_MULTI_CLASS = "ambiguous_multi_class"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    MALFORMED_SIGNAL_STACK = "malformed_signal_stack"


class W06ConsequenceType(str, Enum):
    INVALIDATE = "invalidate"
    DOWNGRADE = "downgrade"
    REVALIDATE = "revalidate"
    SPLIT_IDENTITY = "split_identity"
    BLOCK_CLAIM = "block_claim"
    QUARANTINE = "quarantine"
    RETAIN_UNRESOLVED = "retain_unresolved"
    CREATE_CAUSAL_CORRECTION_CANDIDATE = "create_causal_correction_candidate"
    NARROW_CONTINUATION = "narrow_continuation"
    ESCALATE_REVIEW = "escalate_review"
    ABSTAIN = "abstain"


class W06RevisionScope(str, Enum):
    LOCAL = "local"
    OBJECT_LEVEL = "object_level"
    SCHEMA_LEVEL = "schema_level"
    AFFORDANCE_LEVEL = "affordance_level"
    ACTION_EFFECT_LEVEL = "action_effect_level"
    OWNERSHIP_LEVEL = "ownership_level"
    GOAL_SATISFACTION_LEVEL = "goal_satisfaction_level"
    VALIDITY_LEVEL = "validity_level"
    TEMPORAL_WINDOW_LEVEL = "temporal_window_level"
    POLICY_HINT_LEVEL = "policy_hint_level"
    AUTHORITY_SCOPE_LEVEL = "authority_scope_level"
    GLOBAL = "global"


class W06ConfidenceDropPolicy(str, Enum):
    NO_DROP = "no_drop"
    SMALL_DROP = "small_drop"
    MODERATE_DROP = "moderate_drop"
    SEVERE_DROP = "severe_drop"
    HOLD_PENDING_REVALIDATION = "hold_pending_revalidation"
    FLOOR_AT_UNCERTAIN = "floor_at_uncertain"
    BLOCK_CONFIDENCE_CLAIM = "block_confidence_claim"


class W06IdentityRoute(str, Enum):
    NONE = "none"
    SPLIT_IDENTITY = "split_identity"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    REPLACEMENT_CANDIDATE = "replacement_candidate"
    MERGED_IDENTITY_CANDIDATE = "merged_identity_candidate"
    UNKNOWN_LINEAGE = "unknown_lineage"
    CONTINUITY_FAILURE = "continuity_failure"


class W06RouteStatus(str, Enum):
    CLEAN_REVISION_ROUTE = "clean_revision_route"
    CONTESTED_REVISION_ROUTE = "contested_revision_route"
    REVALIDATION_REQUIRED = "revalidation_required"
    CORRECTION_CANDIDATE_ONLY = "correction_candidate_only"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"
    NARROW_CONTINUATION = "narrow_continuation"
    ESCALATED = "escalated"
    ABSTAIN = "abstain"


@dataclass(frozen=True, slots=True)
class W06MismatchIntakeView:
    mismatch_id: str
    compared_channels: tuple[str, ...]
    mismatch_class: W06MismatchClass
    mismatch_direction: str
    severity: str
    confidence: float
    evidence_refs: tuple[str, ...]
    ambiguity_markers: tuple[str, ...]
    competing_class_candidates: tuple[str, ...]
    target_scope: tuple[str, ...]
    target_layer: str
    update_candidate_type: str
    execution_prohibited: bool
    constitutional_guard_flags: tuple[str, ...]
    required_revalidation: bool
    source_reliability: float
    evidence_precision: float
    prior_strength: float = 0.0
    effective_prior_gain: float = 0.0
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class W06ContradictionIntakeView:
    contradiction_id: str
    conflict_type: str
    conflicting_trace_refs: tuple[str, ...]
    affected_scope: tuple[str, ...]
    affected_maturity_level: str = ""
    schema_id: str = ""
    prior_id: str = ""
    object_id: str = ""
    severity: str = "medium"
    unresolved_status: bool = True
    previous_consequence: str = ""
    evidence_refs: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class W06PriorSchemaLineageView:
    prior_id: str
    schema_id: str
    regularity_id: str = ""
    object_id: str = ""
    maturity_level: str = ""
    authority_scope: tuple[str, ...] = ()
    context_scope: tuple[str, ...] = ()
    stale_status: bool = False
    confidence_band: str = "uncertain"
    negative_evidence_refs: tuple[str, ...] = ()
    contradiction_refs: tuple[str, ...] = ()
    prohibited_claims: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class W06RevisionContext:
    cycle_id: str
    stream_id: str
    temporal_window: tuple[int, int] | None
    revalidation_loop_id: str
    repeated_revalidation_count: int
    progress_detected: bool
    protected_targets: tuple[str, ...]
    allowed_revision_scopes: tuple[W06RevisionScope, ...]
    global_revision_allowed: bool
    consumer_id: str = ""
    loop_threshold: int = 3


@dataclass(frozen=True, slots=True)
class W06OperationalConsequenceRecord:
    consequence_type: W06ConsequenceType
    revision_scope: W06RevisionScope
    criteria_passed: tuple[str, ...]
    criteria_failed: tuple[str, ...]
    affected_targets: tuple[str, ...]
    allowed_continuation_scope: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    required_revalidation: bool
    guardrail_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W06RevisionDecision:
    revision_id: str
    source_mismatch_id: str
    source_contradiction_id: str
    consequence_type: W06ConsequenceType
    revision_scope: W06RevisionScope
    affected_targets: tuple[str, ...]
    severity: str
    confidence: float
    allowed_continuation_scope: tuple[str, ...]
    blocked_claims: tuple[str, ...]
    decision_reason_codes: tuple[str, ...]
    route_status: W06RouteStatus
    audit_ref: str


@dataclass(frozen=True, slots=True)
class W06RevisionLedgerEntry:
    ledger_id: str
    error_type: W06ErrorType
    violated_expectation_source: W06ViolatedExpectationSource
    revision_scope: W06RevisionScope
    confidence_drop_policy: W06ConfidenceDropPolicy
    retained_uncertainty_residue: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    prior_state_ref: str
    new_state_ref: str
    downstream_permission_effects: tuple[str, ...]
    reason_codes: tuple[str, ...]
    created_at_cycle: str


@dataclass(frozen=True, slots=True)
class W06ConfidenceAdjustmentRecord:
    target_id: str
    prior_confidence: float
    new_confidence: float
    drop_or_hold_reason: str
    evidence_precision: float
    source_reliability: float
    mismatch_severity: str
    maturity_sensitivity: str
    floor_bound: float
    ceiling_bound: float
    global_collapse_prevented: bool


@dataclass(frozen=True, slots=True)
class W06ResidualUncertaintyRecord:
    residue_id: str
    residue_type: str
    affected_scope: tuple[str, ...]
    retained_markers: tuple[str, ...]
    future_trigger_conditions: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    visibility_to_downstream: bool
    relevance_bound: str
    decay_or_release_condition: str


@dataclass(frozen=True, slots=True)
class W06AntiParalysisState:
    revalidation_loop_id: str
    repeated_revalidation_count: int
    progress_detected: bool
    loop_threshold: int
    chosen_escape_route: W06ConsequenceType
    bounded_continuation_permissions: tuple[str, ...]
    escalation_status: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W06IdentityRevisionRecord:
    affected_identity_candidate: str
    same_instance_status: str
    split_identity_candidate: str
    duplicate_candidate: str
    replacement_candidate: str
    merged_identity_candidate: str
    unknown_lineage_marker: bool
    required_future_evidence: tuple[str, ...]
    continuity_claim_blocked: bool
    identity_route: W06IdentityRoute


@dataclass(frozen=True, slots=True)
class W06ClaimBlockPacket:
    affected_claim_ids: tuple[str, ...]
    blocked_claim_types: tuple[str, ...]
    blocked_reason: str
    required_revalidation: bool
    downgrade_level: str
    downstream_must_abstain: bool
    allowed_narrow_claims: tuple[str, ...]
    provenance_preserved: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W06CausalCorrectionCandidate:
    candidate_id: str
    suspected_causal_error: str
    target_scope: tuple[str, ...]
    required_evidence: tuple[str, ...]
    proposed_update_kind: str
    guardrails: tuple[str, ...]
    execution_prohibited: bool
    owner_layer: str
    future_update_seam_ref: str
    confidence: float
    competing_candidates: tuple[str, ...]
    residue_ref: str


@dataclass(frozen=True, slots=True)
class W06DownstreamRevisionPermissionPacket:
    may_continue_narrowly: bool
    may_use_with_residue: bool
    must_revalidate: bool
    must_block_claim: bool
    must_split_identity: bool
    must_not_execute_correction: bool
    must_escalate: bool
    must_quarantine: bool
    preserved_uncertainty_markers: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    correction_candidate_refs: tuple[str, ...]
    blocked_claim_packet_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W06TelemetryTrace:
    mismatch_intake_count: int
    contradiction_intake_count: int
    consequence_matrix_count: int
    revision_scope_count: int
    confidence_policy_count: int
    residue_retention_count: int
    anti_paralysis_count: int
    identity_route_count: int
    correction_candidate_count: int
    downstream_packet_count: int
    revalidate_count: int
    downgrade_count: int
    invalidate_count: int
    split_identity_count: int
    block_claim_count: int
    quarantine_count: int
    retain_unresolved_count: int
    global_scope_count: int
    local_scope_count: int
    confidence_drop_count: int
    must_not_execute_correction: bool
    claim_blocked: bool
    consumer_ready: bool
    no_clean_revision: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class W06GateDecision:
    consumer_ready: bool
    no_clean_revision: bool
    must_not_execute_correction: bool
    must_block_claim: bool
    must_revalidate: bool
    must_escalate: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W06ScopeMarker:
    scope: str
    revision_routing_only: bool
    no_update_execution_claim: bool
    no_planner_claim: bool
    no_action_selector_claim: bool
    no_schema_mutation_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W06InputBundle:
    bundle_id: str
    source_lineage: tuple[str, ...]
    mismatch_intake: W06MismatchIntakeView | None
    contradiction_intake: tuple[W06ContradictionIntakeView, ...]
    lineage_view: W06PriorSchemaLineageView | None
    revision_context: W06RevisionContext | None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class W06ResultBundle:
    bundle_id: str
    decision: W06RevisionDecision
    ledger: W06RevisionLedgerEntry
    consequence: W06OperationalConsequenceRecord
    confidence_adjustment: W06ConfidenceAdjustmentRecord
    residual_uncertainty: W06ResidualUncertaintyRecord
    anti_paralysis_state: W06AntiParalysisState
    identity_revision: W06IdentityRevisionRecord
    claim_block_packet: W06ClaimBlockPacket
    correction_candidate: W06CausalCorrectionCandidate
    downstream_packet: W06DownstreamRevisionPermissionPacket
    telemetry: W06TelemetryTrace
    gate: W06GateDecision
    scope_marker: W06ScopeMarker
    no_claim_markers: tuple[str, ...]
    reason: str
