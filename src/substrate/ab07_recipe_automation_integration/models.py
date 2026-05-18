from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AB7ConstraintKind(str, Enum):
    REQUIRES_REPEATED_TRACE = "requires_repeated_trace"
    REQUIRES_EFFECT_CORRELATION = "requires_effect_correlation"
    REQUIRES_INPUT_REFS = "requires_input_refs"
    REQUIRES_STATION_AFFORDANCE = "requires_station_affordance"
    REQUIRES_CONFOUNDER_RESOLUTION = "requires_confounder_resolution"
    REQUIRES_DISCONFIRMATION_CHECK = "requires_disconfirmation_check"
    REQUIRES_ATTRIBUTION_SUPPORT = "requires_attribution_support"
    REQUIRES_FRONTIER_SUPPORT = "requires_frontier_support"
    REQUIRES_UPDATE_SUPPORT = "requires_update_support"
    REQUIRES_MISSING_EVIDENCE_RESOLUTION = "requires_missing_evidence_resolution"
    BLOCKS_MATURITY = "blocks_maturity"
    BLOCKS_AUTOMATION = "blocks_automation"


class AB7ConstraintStatus(str, Enum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    PARTIALLY_SATISFIED = "partially_satisfied"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class AB7MaturityGateStatus(str, Enum):
    BLOCKED = "blocked"
    WEAK = "weak"
    PROVISIONAL = "provisional"
    REPEATED_TRACE_SUPPORTED = "repeated_trace_supported"


class AB7AutomationReadinessStatus(str, Enum):
    NOT_READY = "not_ready"
    BLOCKED = "blocked"
    PROVISIONAL_ONLY = "provisional_only"
    EVIDENCE_REQUIRED = "evidence_required"
    AUTOMATION_FORBIDDEN_IN_AB7 = "automation_forbidden_in_AB7"


@dataclass(frozen=True, slots=True)
class AB7RecipeCandidateRecord:
    recipe_candidate_ref: str
    station_ref: str | None
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    supporting_trace_refs: tuple[str, ...]
    disconfirming_trace_refs: tuple[str, ...]
    p13_schema_candidate_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    maturity_status: str
    maturity_score: float
    hidden_recipe_used: bool = False
    protected_eval_used: bool = False


@dataclass(frozen=True, slots=True)
class AB7PrecursorCandidateRecord:
    precursor_candidate_ref: str
    precursor_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    support_status: str
    missing_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AB7RecipeAutomationInput:
    tick_ref: str
    recipe_candidates: tuple[AB7RecipeCandidateRecord, ...]
    precursor_candidates: tuple[AB7PrecursorCandidateRecord, ...]
    lived_trace_refs: tuple[str, ...]
    p13_credit_refs: tuple[str, ...]
    p14_station_affordance_refs: tuple[str, ...]
    ab_event_digest_refs: tuple[str, ...]
    ab_hypothesis_seed_refs: tuple[str, ...]
    ab_frontier_refs: tuple[str, ...]
    ab_update_refs: tuple[str, ...]
    ab_attribution_refs: tuple[str, ...]
    unresolved_frontier_refs: tuple[str, ...] = ()
    missing_evidence_refs: tuple[str, ...] = ()
    disconfirming_evidence_refs: tuple[str, ...] = ()
    active_confounder_refs: tuple[str, ...] = ()
    public_effect_refs: tuple[str, ...] = ()
    public_input_refs: tuple[str, ...] = ()
    protected_eval_only_rule: bool = False
    ambiguous_frontier: bool = False
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    source: str = "ab07_recipe_automation_input"


@dataclass(frozen=True, slots=True)
class AB7RecipeLearningConstraint:
    constraint_id: str
    constraint_kind: AB7ConstraintKind
    applies_to_candidate_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    status: AB7ConstraintStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AB7RecipeHypothesisBinding:
    binding_id: str
    recipe_candidate_ref: str
    hypothesis_refs: tuple[str, ...]
    frontier_refs: tuple[str, ...]
    update_refs: tuple[str, ...]
    attribution_refs: tuple[str, ...]
    explains_what: tuple[str, ...]
    does_not_explain: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    disconfirming_evidence_refs: tuple[str, ...]
    confidence: float
    confidence_policy: str
    fact_status: str = "not_fact"


@dataclass(frozen=True, slots=True)
class AB7AutomationReadinessAssessment:
    candidate_ref: str
    readiness_status: AB7AutomationReadinessStatus
    missing_requirements: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    automation_plan_created: bool = False


@dataclass(frozen=True, slots=True)
class AB7RecipeAutomationAbductiveFrame:
    frame_id: str
    recipe_candidate_refs: tuple[str, ...]
    precursor_candidate_refs: tuple[str, ...]
    lived_trace_refs: tuple[str, ...]
    p13_credit_refs: tuple[str, ...]
    p14_station_affordance_refs: tuple[str, ...]
    ab_event_digest_refs: tuple[str, ...]
    ab_hypothesis_seed_refs: tuple[str, ...]
    ab_frontier_refs: tuple[str, ...]
    ab_update_refs: tuple[str, ...]
    ab_attribution_refs: tuple[str, ...]
    abductive_constraints: tuple[AB7RecipeLearningConstraint, ...]
    bindings: tuple[AB7RecipeHypothesisBinding, ...]
    disconfirmation_requirements: tuple[str, ...]
    missing_evidence_requirements: tuple[str, ...]
    confounder_requirements: tuple[str, ...]
    maturity_gate_status: dict[str, str]
    automation_readiness: tuple[AB7AutomationReadinessAssessment, ...]
    blocked_reasons: tuple[str, ...]
    claim_boundary: str
    fact_claimed: bool = False
    cause_confirmed: bool = False
    mature_recipe_claimed: bool = False
    automation_claimed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class AB7ScopeMarker:
    scope: str
    recipe_automation_integration_only: bool
    no_recipe_candidate_generation_authority: bool
    no_recipe_execution_authority: bool
    no_automation_execution_authority: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_world_submission_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB7Telemetry:
    tick_ref: str
    recipe_candidate_count: int
    precursor_candidate_count: int
    constraint_count: int
    blocked_constraint_count: int
    unsatisfied_constraint_count: int
    binding_count: int
    blocked_readiness_count: int
    provisional_readiness_count: int
    unsafe_basis_count: int
    no_frame_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB7IntegrationEnvelope:
    tick_ref: str
    frame: AB7RecipeAutomationAbductiveFrame | None
    telemetry: AB7Telemetry
    scope_marker: AB7ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]
