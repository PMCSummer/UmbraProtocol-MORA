from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AP01DecisionStatus(str, Enum):
    PUBLISHED = "published"
    BLOCKED = "blocked"
    REVALIDATION_REQUIRED = "revalidation_required"
    ABSTAIN = "abstain"
    MALFORMED = "malformed"
    UNSAFE_BASIS = "unsafe_basis"


class AP01CandidateOrigin(str, Enum):
    CORE_INTERNAL_CANDIDATE = "core_internal_candidate"
    SUBJECT_TICK_CANDIDATE_BASIS = "subject_tick_candidate_basis"
    TEST_FIXTURE_CANDIDATE = "test_fixture_candidate"
    UNSAFE_EXTERNAL_OR_HARNESS_CANDIDATE = "unsafe_external_or_harness_candidate"


class AP01ExecutionBoundary(str, Enum):
    EXTERNAL_WORLD_ONLY = "external_world_only"


class AP01WorldExecutionStatus(str, Enum):
    NOT_EXECUTED_BY_SUBJECT = "not_executed_by_subject"


ALLOWED_ACTION_KINDS: tuple[str, ...] = (
    "wait",
    "turn_left",
    "turn_right",
    "move_forward",
    "move_backward",
    "strafe_left",
    "strafe_right",
    "inspect",
    "pickup",
    "drop",
    "interact",
    "use_station",
    "communicate",
)

FORBIDDEN_MAGIC_ACTION_KINDS: tuple[str, ...] = (
    "trade_offer",
    "barter",
    "deal_success",
    "exchange_oracle",
    "wants_trade",
    "should_trade",
    "mutual_benefit",
)

TARGET_REQUIRED_ACTION_KINDS: tuple[str, ...] = (
    "pickup",
    "drop",
    "interact",
    "use_station",
)

TARGET_OPTIONAL_ACTION_KINDS: tuple[str, ...] = (
    "wait",
    "turn_left",
    "turn_right",
    "move_forward",
    "move_backward",
    "strafe_left",
    "strafe_right",
    "inspect",
    "communicate",
)


@dataclass(frozen=True, slots=True)
class AP01ActionPublicationCandidate:
    candidate_id: str
    action_kind: str
    target_ref: str | None
    args: dict[str, object]
    intended_effect: str
    source_tick_ref: str
    source_cycle_ref: str
    source_phase_refs: tuple[str, ...]
    affordance_binding_refs: tuple[str, ...]
    permission_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    episode_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    revalidation_refs: tuple[str, ...]
    blocked_claim_refs: tuple[str, ...]
    desired_refs: tuple[str, ...]
    predicted_refs: tuple[str, ...]
    observed_refs: tuple[str, ...]
    permitted_refs: tuple[str, ...]
    candidate_origin: AP01CandidateOrigin
    forbidden_basis_markers: tuple[str, ...]
    no_hidden_truth_used: bool
    no_eval_only_used: bool
    no_scenario_label_used: bool

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.action_kind:
            raise ValueError("action_kind is required")
        if not isinstance(self.args, dict):
            raise TypeError("args must be a dict")
        if not self.source_tick_ref:
            raise ValueError("source_tick_ref is required")
        if not self.source_cycle_ref:
            raise ValueError("source_cycle_ref is required")


@dataclass(frozen=True, slots=True)
class AP01ActionPublicationCandidateSet:
    candidate_set_id: str
    candidates: tuple[AP01ActionPublicationCandidate, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = "ap01_action_publication_candidate_set"

    def __post_init__(self) -> None:
        if not self.candidate_set_id:
            raise ValueError("candidate_set_id is required")


@dataclass(frozen=True, slots=True)
class AP01SubjectActionRequestPacket:
    request_id: str
    source_candidate_id: str
    action_kind: str
    target_ref: str | None
    args: dict[str, object]
    intended_effect: str
    source_tick_ref: str
    source_phase_refs: tuple[str, ...]
    affordance_binding_refs: tuple[str, ...]
    permission_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    episode_refs: tuple[str, ...]
    execution_boundary: AP01ExecutionBoundary
    executed_by_subject: bool
    world_execution_status: AP01WorldExecutionStatus
    must_wait_for_world_effect: bool
    effect_feedback_required: bool
    no_hidden_truth_used: bool
    no_eval_only_used: bool
    no_scenario_label_used: bool
    publication_confidence: float
    uncertainty_markers: tuple[str, ...]
    claim_boundary: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.execution_boundary is not AP01ExecutionBoundary.EXTERNAL_WORLD_ONLY:
            raise ValueError("execution_boundary must be external_world_only")
        if self.executed_by_subject:
            raise ValueError("AP01 request cannot be executed by subject")
        if self.world_execution_status is not AP01WorldExecutionStatus.NOT_EXECUTED_BY_SUBJECT:
            raise ValueError("world_execution_status must be not_executed_by_subject")
        if not self.must_wait_for_world_effect:
            raise ValueError("must_wait_for_world_effect must be True")
        if not self.effect_feedback_required:
            raise ValueError("effect_feedback_required must be True")
        if self.publication_confidence < 0.0 or self.publication_confidence > 1.0:
            raise ValueError("publication_confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class AP01ActionPublicationDecision:
    decision_id: str
    candidate_id: str
    decision_status: AP01DecisionStatus
    reason_codes: tuple[str, ...]
    blocked_reason: str | None
    missing_requirements: tuple[str, ...]
    preserved_residue_refs: tuple[str, ...]
    downstream_permission_delta: tuple[str, ...]
    published_request: AP01SubjectActionRequestPacket | None


@dataclass(frozen=True, slots=True)
class AP01ActionPublicationTelemetry:
    candidate_count: int
    published_request_count: int
    blocked_count: int
    revalidation_required_count: int
    abstain_count: int
    malformed_count: int
    unsafe_basis_count: int
    execution_boundary_preserved: bool
    must_wait_for_effect: bool
    no_hidden_truth_used: bool
    no_eval_only_used: bool
    no_scenario_label_used: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AP01ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    publication_not_planner: bool
    publication_not_execution: bool
    no_world_mutation_inside_subject: bool
    no_phase_override_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AP01SubjectActionPublicationResult:
    candidate_set_id: str
    decisions: tuple[AP01ActionPublicationDecision, ...]
    published_requests: tuple[AP01SubjectActionRequestPacket, ...]
    telemetry: AP01ActionPublicationTelemetry
    scope_marker: AP01ScopeMarker
    reason: str
