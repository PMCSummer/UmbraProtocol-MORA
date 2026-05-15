from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class W04ConstraintType(str, Enum):
    WORLD_CONSTRAINT = "world_constraint"
    LEGALITY_CONSTRAINT = "legality_constraint"
    EPISTEMIC_CONSTRAINT = "epistemic_constraint"
    TEMPORAL_CONSTRAINT = "temporal_constraint"
    PERSPECTIVE_CONSTRAINT = "perspective_constraint"
    AUTHORITY_CONSTRAINT = "authority_constraint"
    SAFETY_CONSTRAINT = "safety_constraint"
    DOWNSTREAM_CONTRACT_CONSTRAINT = "downstream_contract_constraint"


class W04ConstraintHardness(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    ADVISORY = "advisory"
    UNKNOWN_HARD_UNTIL_VERIFIED = "unknown_hard_until_verified"


class W04ConstraintEvaluationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"
    MALFORMED = "malformed"
    STALE = "stale"
    AUTHORITY_MISMATCH = "authority_mismatch"
    PERSPECTIVE_MISMATCH = "perspective_mismatch"
    TEMPORAL_INVALID = "temporal_invalid"
    BLOCKED_BY_UPSTREAM_PERMISSION = "blocked_by_upstream_permission"


class W04ApplicabilityDecisionStatus(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    NARROWED = "narrowed"
    RELAXABLE = "relaxable"
    ALLOWED_WITH_RELAXATION = "allowed_with_relaxation"
    REVALIDATE_REQUIRED = "revalidate_required"
    HINT_ONLY = "hint_only"
    ABSTAIN = "abstain"
    MALFORMED_REQUEST = "malformed_request"
    NO_CLEAN_APPLICABILITY = "no_clean_applicability"


@dataclass(frozen=True, slots=True)
class W04Constraint:
    constraint_id: str
    constraint_type: W04ConstraintType
    hard_or_soft: W04ConstraintHardness
    source_authority: str
    target_scope: tuple[str, ...]
    required_condition: tuple[str, ...]
    forbidden_condition: tuple[str, ...]
    current_status: str
    enforcement_route: str
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04DesiredStateRequest:
    desired_state_id: str
    requested_outcome: str
    actor_id: str
    target_subject: str
    perspective_id: str
    intended_use: str
    priority: str
    temporal_window: tuple[int, int] | None
    acceptable_relaxation_dimensions: tuple[str, ...]
    non_negotiable_constraints: tuple[str, ...]
    source_authority: str
    provenance: tuple[str, ...]
    malformed_markers: tuple[str, ...] = ()
    embedded_forbidden_conclusions: tuple[str, ...] = ()
    requested_schema_or_prior_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class W04ActiveApplicabilityContext:
    context_id: str
    cycle_id: str
    stream_id: str
    current_time_or_sequence: int
    world_context_refs: tuple[str, ...]
    regularity_refs: tuple[str, ...]
    schema_refs: tuple[str, ...]
    contradiction_refs: tuple[str, ...]
    stale_context_markers: tuple[str, ...]
    unavailable_or_unknown_markers: tuple[str, ...]
    active_actor_id: str
    active_perspective_id: str
    source_context_scope: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04PerspectiveFrame:
    actor_scope: str
    observer_scope: str
    subject_scope: str
    source_perspective: str
    requested_perspective: str
    allowed_perspective_transfer: tuple[str, ...]
    blocked_perspective_transfer: tuple[str, ...]
    self_other_boundary: str
    authority_boundary: str
    leakage_risk: str


@dataclass(frozen=True, slots=True)
class W04W03IntakeView:
    prior_id: str
    schema_id: str
    candidate_id: str
    permission_packet_ref: str
    support_refs: tuple[str, ...]
    authority_scope: tuple[str, ...]
    context_scope: tuple[str, ...]
    applicability_conditions: tuple[str, ...]
    stale_or_revalidation_status: tuple[str, ...]
    contradiction_status: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    allowed_use_cases: tuple[str, ...]
    blocked_use_cases: tuple[str, ...]
    override_conditions: tuple[str, ...]
    may_use_as_bounded_prior: bool
    may_use_as_schema_hint: bool
    may_use_as_operational_default: bool
    must_revalidate_before_use: bool
    must_preserve_contradiction: bool
    must_abstain: bool


@dataclass(frozen=True, slots=True)
class W04ConstraintProfile:
    profile_id: str
    world_constraints: tuple[W04Constraint, ...]
    legality_constraints: tuple[W04Constraint, ...]
    epistemic_constraints: tuple[W04Constraint, ...]
    temporal_constraints: tuple[W04Constraint, ...]
    perspective_constraints: tuple[W04Constraint, ...]
    authority_constraints: tuple[W04Constraint, ...]
    safety_constraints: tuple[W04Constraint, ...]
    downstream_contract_constraints: tuple[W04Constraint, ...]
    profile_source_authority: str
    hard_constraint_count: int
    soft_constraint_count: int
    unknown_hard_count: int
    malformed_markers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class W04IntersectionAssessment:
    assessment_id: str
    evaluated_constraint_ids: tuple[str, ...]
    hard_constraint_results: tuple[str, ...]
    soft_constraint_results: tuple[str, ...]
    empty_intersection_status: str
    feasible_region: tuple[str, ...]
    infeasible_region: tuple[str, ...]
    unknown_region: tuple[str, ...]
    narrowed_applicability_conditions: tuple[str, ...]
    hard_failure_ids: tuple[str, ...]
    soft_conflict_ids: tuple[str, ...]
    unknown_hard_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04ConstraintEvaluationRecord:
    constraint_id: str
    constraint_type: W04ConstraintType
    hard_or_soft: W04ConstraintHardness
    source_authority: str
    passed: bool
    failed: bool
    unknown: bool
    violated_by: tuple[str, ...]
    enforcement_action: str
    reason_codes: tuple[str, ...]
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04RelaxationLedgerEntry:
    relaxation_id: str
    relaxed_field: str
    original_constraint: str
    relaxed_constraint: str
    relaxation_bound: str
    relaxation_authority: str
    residual_risk: str
    downstream_effect: str
    non_relaxable_constraints_preserved: tuple[str, ...]
    reason_codes: tuple[str, ...]
    audit_ref: str


@dataclass(frozen=True, slots=True)
class W04PerspectiveSafetyRecord:
    actor_scope: str
    observer_scope: str
    subject_scope: str
    source_perspective: str
    requested_perspective: str
    allowed_perspective_transfer: tuple[str, ...]
    blocked_transfer: bool
    authority_boundary: str
    leakage_risk: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04RevalidationRequest:
    request_id: str
    target_schema_or_prior: str
    reason: str
    missing_evidence: tuple[str, ...]
    stale_field: str
    contradiction_ref: str
    required_upstream_layer: str
    deadline_or_priority: str
    blocked_until_revalidated: bool


@dataclass(frozen=True, slots=True)
class W04BlockedApplicabilityRecord:
    blocked_reason: str
    violated_hard_constraints: tuple[str, ...]
    malformed_desired_state_markers: tuple[str, ...]
    authority_scope_violation: bool
    temporal_violation: bool
    perspective_violation: bool
    unknown_hard_feasibility: bool
    downstream_abstain_requirement: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04DownstreamApplicabilityPermissionPacket:
    decision_id: str
    candidate_id: str
    may_deploy_candidate: bool
    may_use_as_hint_only: bool
    may_use_after_revalidation: bool
    may_use_with_relaxation: bool
    must_abstain: bool
    must_block: bool
    must_revalidate: bool
    must_preserve_hard_constraints: bool
    must_preserve_perspective_scope: bool
    must_preserve_authority_scope: bool
    action_authorization_granted: bool
    prohibited_uses: tuple[str, ...]
    required_preserved_markers: tuple[str, ...]
    blocked_reason: str
    decision_reason_codes: tuple[str, ...]
    violated_hard_constraints: tuple[str, ...]
    unknown_hard_constraints: tuple[str, ...]
    perspective_boundary_markers: tuple[str, ...]
    authority_boundary_markers: tuple[str, ...]
    stale_or_revalidation_markers: tuple[str, ...]
    relaxation_ledger_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04ApplicabilityDecision:
    decision_id: str
    candidate_id: str
    schema_id: str
    prior_id: str
    desired_state_id: str
    decision_status: W04ApplicabilityDecisionStatus
    allowed_scope: tuple[str, ...]
    blocked_scope: tuple[str, ...]
    narrowed_scope: tuple[str, ...]
    decision_reason_codes: tuple[str, ...]
    blocked_reason: str
    confidence_band: str
    audit_ref: str
    intersection_assessment: W04IntersectionAssessment
    constraint_evaluations: tuple[W04ConstraintEvaluationRecord, ...]
    perspective_safety: W04PerspectiveSafetyRecord
    relaxation_ledger: tuple[W04RelaxationLedgerEntry, ...]
    revalidation_requests: tuple[W04RevalidationRequest, ...]
    downstream_permission_packet: W04DownstreamApplicabilityPermissionPacket
    no_claim_markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W04Telemetry:
    desired_state_intake_count: int
    w03_candidate_intake_count: int
    applicability_decision_count: int
    allowed_count: int
    blocked_count: int
    narrowed_count: int
    hint_only_count: int
    revalidate_required_count: int
    abstain_count: int
    relaxation_count: int
    hard_constraint_failure_count: int
    unknown_hard_count: int
    malformed_desired_state_count: int
    perspective_block_count: int
    authority_block_count: int
    stale_block_count: int
    consumer_ready: bool
    no_clean_applicability: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class W04GateDecision:
    consumer_ready: bool
    no_clean_applicability: bool
    blocked_count: int
    revalidate_required_count: int
    abstain_count: int
    hard_constraint_failure_count: int
    unknown_hard_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W04ScopeMarker:
    scope: str
    applicability_gating_only: bool
    no_planner_claim: bool
    no_action_selector_claim: bool
    no_world_model_expansion_claim: bool
    no_w05_or_w06_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class W04InputBundle:
    bundle_id: str
    source_lineage: tuple[str, ...]
    w03_intake_views: tuple[W04W03IntakeView, ...]
    desired_state_request: W04DesiredStateRequest | None
    active_context: W04ActiveApplicabilityContext | None
    perspective_frame: W04PerspectiveFrame | None
    constraint_profile: W04ConstraintProfile | None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class W04ResultBundle:
    bundle_id: str
    applicability_decisions: tuple[W04ApplicabilityDecision, ...]
    intersection_assessments: tuple[W04IntersectionAssessment, ...]
    constraint_evaluations: tuple[W04ConstraintEvaluationRecord, ...]
    perspective_safety_records: tuple[W04PerspectiveSafetyRecord, ...]
    relaxation_ledger_entries: tuple[W04RelaxationLedgerEntry, ...]
    revalidation_requests: tuple[W04RevalidationRequest, ...]
    blocked_records: tuple[W04BlockedApplicabilityRecord, ...]
    downstream_permission_packets: tuple[W04DownstreamApplicabilityPermissionPacket, ...]
    telemetry: W04Telemetry
    gate: W04GateDecision
    scope_marker: W04ScopeMarker
    no_claim_markers: tuple[str, ...]
    reason: str
