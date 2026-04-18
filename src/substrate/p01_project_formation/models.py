from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class P01AuthoritySourceKind(str, Enum):
    EXPLICIT_USER_DIRECTIVE = "explicit_user_directive"
    STANDING_OBLIGATION = "standing_obligation"
    SYSTEM_MAINTENANCE_REQUIREMENT = "system_maintenance_requirement"
    CONTINUATION_COMMITMENT = "continuation_commitment"
    CLARIFICATION_REQUIRED_PRECONDITION = "clarification_required_precondition"
    POLICY_GUARDRAIL_REQUIREMENT = "policy_guardrail_requirement"
    LOW_AUTHORITY_SUGGESTION = "low_authority_suggestion"
    DISALLOWED_SELF_GENERATED_IDEA = "disallowed_self_generated_idea"


class P01ProjectStatus(str, Enum):
    ACTIVE = "active"
    CANDIDATE_ONLY = "candidate_only"
    SUSPENDED = "suspended"
    BLOCKED_BY_MISSING_PRECONDITION = "blocked_by_missing_precondition"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    COMPLETED_CANDIDATE_ONLY = "completed_candidate_only"
    TERMINATED = "terminated"


class P01CommitmentGrade(str, Enum):
    NONE = "none"
    PROVISIONAL = "provisional"
    TASK_BOUND = "task_bound"
    OBLIGATION_BOUND = "obligation_bound"
    PERSISTENT_BUT_BOUNDED = "persistent_but_bounded"


class P01PriorityClass(str, Enum):
    BLOCKING = "blocking"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DEFERRED = "deferred"
    BACKGROUND = "background"


class P01AdmissibilityVerdict(str, Enum):
    ADMITTED = "admitted"
    CANDIDATE_ONLY = "candidate_only"
    REJECTED_AS_OUT_OF_SCOPE = "rejected_as_out_of_scope"
    CONFLICTING_AUTHORITY = "conflicting_authority"
    INSUFFICIENT_BASIS_FOR_PROJECT = "insufficient_basis_for_project"
    BLOCKED_PENDING_GROUNDING = "blocked_pending_grounding"


class P01ArbitrationOutcome(str, Enum):
    COEXIST = "coexist"
    DISPLACE_LOWER_PRIORITY = "displace_lower_priority"
    DEFER_CONFLICT = "defer_conflict"
    REJECT_WEAKER_SOURCE = "reject_weaker_source"
    NO_SAFE_RESOLUTION = "no_safe_resolution"


@dataclass(frozen=True, slots=True)
class P01ProjectSignalInput:
    signal_id: str
    signal_kind: str
    authority_source_kind: P01AuthoritySourceKind
    target_summary: str
    grounded_basis_present: bool
    open_loop_marker: bool = False
    blocker_present: bool = False
    missing_precondition_marker: bool = False
    resource_bound_marker: bool = False
    temporal_validity_marker: bool = True
    continuation_of_prior_project_id: str | None = None
    completion_evidence_present: bool = False
    policy_disallow_marker: bool = False
    clarification_block_marker: bool = False
    priority_hint: P01PriorityClass | None = None
    persistent_obligation_marker: bool = False
    conflict_group_id: str | None = None
    provenance: str = "p01.signal"


@dataclass(frozen=True, slots=True)
class P01ProjectEntry:
    project_id: str
    project_identity_key: str
    project_class: str
    source_of_authority: P01AuthoritySourceKind
    objective_summary_or_typed_target: str
    commitment_grade: P01CommitmentGrade
    priority_class: P01PriorityClass
    activation_conditions: tuple[str, ...]
    suspension_conditions: tuple[str, ...]
    termination_conditions: tuple[str, ...]
    dependency_refs: tuple[str, ...]
    current_status: P01ProjectStatus
    admissibility_verdict: P01AdmissibilityVerdict
    provenance: str
    formation_trace_refs: tuple[str, ...]
    carryover_basis: str | None
    stale_risk_marker: bool


@dataclass(frozen=True, slots=True)
class P01ArbitrationRecord:
    arbitration_id: str
    conflict_group_id: str
    involved_project_ids: tuple[str, ...]
    outcome: P01ArbitrationOutcome
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P01IntentionStackState:
    stack_id: str
    active_projects: tuple[P01ProjectEntry, ...]
    candidate_projects: tuple[P01ProjectEntry, ...]
    suspended_projects: tuple[P01ProjectEntry, ...]
    rejected_candidates: tuple[P01ProjectEntry, ...]
    arbitration_records: tuple[P01ArbitrationRecord, ...]
    no_safe_project_formation: bool
    grounded_context_underconstrained: bool
    prompt_local_capture_risk: bool
    bypass_resistance_status: str
    conflicting_authority: bool
    blocked_pending_grounding: bool
    candidate_only_without_activation_basis: bool
    stale_active_project_detected: bool
    justification_links: tuple[str, ...]
    provenance: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class P01ProjectFormationGateDecision:
    intention_stack_consumer_ready: bool
    authority_bound_consumer_ready: bool
    project_handoff_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class P01ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    p01_first_slice_only: bool
    p02_not_implemented: bool
    p03_not_implemented: bool
    p04_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P01Telemetry:
    stack_id: str
    tick_index: int
    active_project_count: int
    candidate_project_count: int
    suspended_project_count: int
    rejected_project_count: int
    arbitration_count: int
    no_safe_project_formation: bool
    conflicting_authority: bool
    blocked_pending_grounding: bool
    prompt_local_capture_risk: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class P01ProjectFormationResult:
    state: P01IntentionStackState
    gate: P01ProjectFormationGateDecision
    scope_marker: P01ScopeMarker
    telemetry: P01Telemetry
    reason: str
