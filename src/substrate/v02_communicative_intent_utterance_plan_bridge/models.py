from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class V02PlanStatus(str, Enum):
    FULL_PLAN_READY = "full_plan_ready"
    PARTIAL_PLAN_ONLY = "partial_plan_only"
    CLARIFICATION_FIRST_PLAN = "clarification_first_plan"
    REFUSAL_DOMINANT_PLAN = "refusal_dominant_plan"
    PROTECTIVE_DEFER_PLAN = "protective_defer_plan"
    MULTIPLE_BRANCHES_UNRESOLVED = "multiple_branches_unresolved"
    CANNOT_ORDER_WITH_CURRENT_HISTORY = "cannot_order_with_current_history"
    INSUFFICIENT_PLAN_BASIS = "insufficient_plan_basis"


class V02SegmentRole(str, Enum):
    ANSWER = "answer"
    QUALIFICATION = "qualification"
    BOUNDARY = "boundary"
    CLARIFICATION_REQUEST = "clarification_request"
    REFUSAL = "refusal"
    WARNING = "warning"
    COMMITMENT_LIMITER = "commitment_limiter"
    NEXT_STEP_HANDOFF = "next_step_handoff"


class V02UncertaintyState(str, Enum):
    BOUNDED = "bounded"
    QUALIFIED = "qualified"
    UNRESOLVED = "unresolved"


class V02OptionalityStatus(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"


@dataclass(frozen=True, slots=True)
class V02UtterancePlanInput:
    input_id: str
    prior_unresolved_question: bool = False
    prior_refusal_present: bool = False
    prior_commitment_carry_present: bool = False
    prior_repair_required: bool = False
    discourse_pressure_hint: float = 0.0
    provenance: str = "v02.utterance_plan_input"


@dataclass(frozen=True, slots=True)
class V02PlanSegment:
    segment_id: str
    source_act_ref: str
    segment_role: V02SegmentRole
    content_refs: tuple[str, ...]
    target_update: str
    mandatory_qualifier_ids: tuple[str, ...]
    blocked_expansion_ids: tuple[str, ...]
    protected_omission_ids: tuple[str, ...]
    prerequisite_segment_ids: tuple[str, ...]
    must_precede_segment_ids: tuple[str, ...]
    mutually_exclusive_segment_ids: tuple[str, ...]
    uncertainty_state: V02UncertaintyState
    optionality_status: V02OptionalityStatus


@dataclass(frozen=True, slots=True)
class V02OrderingEdge:
    from_segment_id: str
    to_segment_id: str
    relation: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class V02UtterancePlanState:
    plan_id: str
    plan_status: V02PlanStatus
    primary_branch_id: str
    alternative_branch_ids: tuple[str, ...]
    segment_graph: tuple[V02PlanSegment, ...]
    ordering_edges: tuple[V02OrderingEdge, ...]
    segment_ids: tuple[str, ...]
    source_act_ids: tuple[str, ...]
    mandatory_qualifier_ids: tuple[str, ...]
    blocked_expansion_ids: tuple[str, ...]
    protected_omission_ids: tuple[str, ...]
    unresolved_branching: bool
    clarification_first_required: bool
    refusal_dominant: bool
    protective_boundary_first: bool
    partial_plan_only: bool
    realization_contract_ready: bool
    discourse_history_sensitive: bool
    downstream_consumer_ready: bool
    segment_count: int
    branch_count: int
    ordering_edge_count: int
    mandatory_qualifier_attachment_count: int
    blocked_expansion_count: int
    protected_omission_count: int
    justification_links: tuple[str, ...]
    provenance: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class V02PlanGateDecision:
    plan_consumer_ready: bool
    ordering_consumer_ready: bool
    realization_contract_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class V02ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    v02_first_slice_only: bool
    v03_not_implemented: bool
    p02_not_implemented: bool
    p04_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class V02Telemetry:
    plan_id: str
    tick_index: int
    plan_status: V02PlanStatus
    segment_count: int
    branch_count: int
    ordering_edge_count: int
    mandatory_qualifier_attachment_count: int
    blocked_expansion_count: int
    protected_omission_count: int
    clarification_first_required: bool
    refusal_dominant: bool
    protective_boundary_first: bool
    partial_plan_only: bool
    unresolved_branching: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class V02UtterancePlanResult:
    state: V02UtterancePlanState
    gate: V02PlanGateDecision
    scope_marker: V02ScopeMarker
    telemetry: V02Telemetry
    reason: str
