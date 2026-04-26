from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class P04PolicyClass(str, Enum):
    COLLABORATIVE_CLARIFICATION = "collaborative_clarification"
    ASSERTIVE_BOUNDARY = "assertive_boundary"
    ESCALATORY_ENFORCEMENT = "escalatory_enforcement"
    DEESCALATORY_REPAIR = "deescalatory_repair"
    HOLD_AND_VERIFY = "hold_and_verify"


class P04BranchOutcomeStatus(str, Enum):
    SELECTABLE = "selectable"
    HAZARD_ONLY = "hazard_only"
    EXCLUDED = "excluded"


class P04UncertaintyStatus(str, Enum):
    STABLE = "stable"
    GUARDED = "guarded"
    UNSTABLE = "unstable"
    OUT_OF_HORIZON = "out_of_horizon"


class P04ExclusionReason(str, Enum):
    UNLICENSED_POLICY = "unlicensed_policy"
    SCOPE_OVERRUN = "scope_overrun"
    PROTECTIVE_CONFLICT = "protective_conflict"
    INVALID_CANDIDATE = "invalid_candidate"


class P04DominanceState(str, Enum):
    CLEAR_DOMINANCE = "clear_dominance"
    NO_CLEAR_DOMINANCE = "no_clear_dominance"
    UNSTABLE_REGION = "unstable_region"


class P04TransitionType(str, Enum):
    TRUST_INCREASE = "trust_increase"
    TRUST_DECREASE = "trust_decrease"
    RUPTURE_RISK_INCREASE = "rupture_risk_increase"
    RUPTURE_RISK_DECREASE = "rupture_risk_decrease"
    REPAIR_CAPACITY_INCREASE = "repair_capacity_increase"
    REPAIR_CAPACITY_DECREASE = "repair_capacity_decrease"
    PROJECT_PROGRESS_INCREASE = "project_progress_increase"
    PROJECT_PROGRESS_DECREASE = "project_progress_decrease"
    COERCION_RISK_INCREASE = "coercion_risk_increase"
    COERCION_RISK_DECREASE = "coercion_risk_decrease"
    COMMITMENT_STABILITY_INCREASE = "commitment_stability_increase"
    COMMITMENT_STABILITY_DECREASE = "commitment_stability_decrease"


class P04BeliefStateMode(str, Enum):
    SHARED_KNOWLEDGE = "shared_knowledge"
    INCOMPLETE_INFORMATION = "incomplete_information"
    FALSE_BELIEF = "false_belief"
    MISREAD = "misread"
    KNOWLEDGE_UNCERTAINTY = "knowledge_uncertainty"


class P04CandidateRole(str, Enum):
    SELECTABLE = "selectable"
    HAZARD_ONLY = "hazard_only"


class P04ComparisonReadiness(str, Enum):
    SELECTION_READY = "selection_ready"
    COMPARISON_ONLY = "comparison_only"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class P04PolicyCandidate:
    candidate_id: str
    policy_ref: str
    policy_class: P04PolicyClass
    action_class: str
    sequencing_rule: str
    escalation_stance: str
    de_escalation_stance: str
    clarification_strategy: str
    boundary_posture: str
    boundary_timing: str
    stopping_conditions: tuple[str, ...]
    horizon_steps: int
    candidate_role: P04CandidateRole = P04CandidateRole.SELECTABLE
    licensed: bool = True
    scope_overrun: bool = False
    protective_conflict: bool = False
    provenance: str = "p04.policy_candidate"


@dataclass(frozen=True, slots=True)
class P04PolicyCandidateSet:
    candidate_set_id: str
    candidates: tuple[P04PolicyCandidate, ...]
    reason: str
    provenance: str = "p04.policy_candidate_set"


@dataclass(frozen=True, slots=True)
class P04BeliefStateAssumption:
    assumption_id: str
    mode: P04BeliefStateMode
    other_agent_state_summary: str
    shared_knowledge_confidence: float
    incomplete_information_support: bool = False
    false_belief_case_support: bool = False
    misread_case_support: bool = False
    knowledge_uncertainty_support: bool = False
    reason: str = ""
    provenance: str = "p04.belief_state_assumption"


@dataclass(frozen=True, slots=True)
class P04SimulationInput:
    input_id: str
    candidate_set: P04PolicyCandidateSet
    input_state_refs: tuple[str, ...] = ()
    p02_episode_refs: tuple[str, ...] = ()
    p03_credit_refs: tuple[str, ...] = ()
    current_rupture_risk: float = 0.5
    current_trust_fragility: float = 0.5
    current_dependency_pressure: float = 0.5
    current_project_blockage: float = 0.5
    current_protective_load: float = 0.5
    current_commitment_strain: float = 0.5
    horizon_steps: int = 3
    assumptions: tuple[P04BeliefStateAssumption, ...] = ()
    missing_state_factors: tuple[str, ...] = ()
    assumption_perturbation_level: float = 0.0
    use_p03_priors: bool = True
    provenance: str = "p04.simulation_input"


@dataclass(frozen=True, slots=True)
class P04RelationalTransition:
    transition_id: str
    transition_type: P04TransitionType
    delta: float
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P04BranchRiskVector:
    rupture_risk: float
    trust_fragility: float
    coercion_risk: float
    repair_debt: float
    delay_cost: float


@dataclass(frozen=True, slots=True)
class P04BranchBenefitVector:
    project_progress: float
    clarity_gain: float
    trust_repair: float
    boundary_preservation: float


@dataclass(frozen=True, slots=True)
class P04ProtectiveLoadEffect:
    load_delta: float
    burden_class: str
    reason: str


@dataclass(frozen=True, slots=True)
class P04CommitmentEffect:
    commitment_delta: float
    commitment_stability_delta: float
    reason: str


@dataclass(frozen=True, slots=True)
class P04BranchAssumptionRecord:
    assumption_id: str
    mode: P04BeliefStateMode
    applied: bool
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class P04BranchUncertaintyEnvelope:
    status: P04UncertaintyStatus
    unstable_factors: tuple[str, ...]
    sensitivity: float
    out_of_horizon: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P04BranchRecord:
    branch_id: str
    policy_ref: str
    outcome_status: P04BranchOutcomeStatus
    hazard_only: bool
    input_state_refs: tuple[str, ...]
    assumption_records: tuple[P04BranchAssumptionRecord, ...]
    relational_transitions: tuple[P04RelationalTransition, ...]
    risk_vector: P04BranchRiskVector
    benefit_vector: P04BranchBenefitVector
    protective_load_effect: P04ProtectiveLoadEffect
    commitment_effect: P04CommitmentEffect
    uncertainty_envelope: P04BranchUncertaintyEnvelope
    out_of_horizon_marked: bool
    ranking_score_hint: float
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P04ContrastiveDifference:
    contrast_id: str
    lhs_policy_ref: str
    rhs_policy_ref: str
    faster_but_riskier: bool
    slower_but_safer: bool
    preserves_boundary_leaves_ambiguity: bool
    lowers_rupture_increases_delay: bool
    summary_codes: tuple[str, ...]
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P04ComparisonMatrix:
    matrix_id: str
    contrasts: tuple[P04ContrastiveDifference, ...]
    dominance_state: P04DominanceState
    comparison_readiness: P04ComparisonReadiness
    no_clear_dominance: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P04ExcludedPolicyRecord:
    excluded_id: str
    policy_ref: str
    reason_code: P04ExclusionReason
    hazard_only: bool
    selectable_candidate: bool
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P04UnstableRegion:
    region_id: str
    policy_refs: tuple[str, ...]
    trigger_factors: tuple[str, ...]
    no_clear_dominance: bool
    comparison_only: bool
    simulation_blocked: bool
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P04SimulationMetadata:
    simulation_id: str
    evaluated_candidate_count: int
    selectable_candidate_count: int
    excluded_policy_count: int
    belief_conditioned_rollout: bool
    incomplete_information_support: bool
    false_belief_case_support: bool
    misread_case_support: bool
    knowledge_uncertainty_support: bool
    source_lineage: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class P04CounterfactualPolicySimulationSet:
    simulation_id: str
    branch_records: tuple[P04BranchRecord, ...]
    excluded_policies: tuple[P04ExcludedPolicyRecord, ...]
    unstable_regions: tuple[P04UnstableRegion, ...]
    comparison_matrix: P04ComparisonMatrix
    metadata: P04SimulationMetadata
    reason: str


@dataclass(frozen=True, slots=True)
class P04SimulationGateDecision:
    branch_record_consumer_ready: bool
    comparison_consumer_ready: bool
    excluded_policy_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class P04ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    p04_frontier_slice_only: bool
    simulation_not_selector: bool
    no_hidden_policy_selection_authority: bool
    no_policy_mutation_authority: bool
    no_map_wide_prediction_claim: bool
    no_full_social_world_prediction_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P04Telemetry:
    branch_count: int
    selectable_branch_count: int
    excluded_policy_count: int
    unstable_region_count: int
    no_clear_dominance_count: int
    belief_conditioned_rollout: bool
    incomplete_information_support: bool
    false_belief_case_support: bool
    misread_case_support: bool
    knowledge_uncertainty_support: bool
    guardrail_exclusion_count: int
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class P04SimulationResult:
    simulation_set: P04CounterfactualPolicySimulationSet
    gate: P04SimulationGateDecision
    scope_marker: P04ScopeMarker
    telemetry: P04Telemetry
    reason: str
