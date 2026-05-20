from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CostDimension(str, Enum):
    MATERIAL = "material"
    ENERGY = "energy"
    TIME = "time"
    TOOL_WEAR = "tool_wear"
    SETUP = "setup"
    THROUGHPUT = "throughput"
    STATION_OCCUPATION = "station_occupation"
    ROUTE = "route"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    UNCERTAINTY = "uncertainty"
    EVIDENCE_QUALITY = "evidence_quality"


class CostEvidenceKind(str, Enum):
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    PROVIDER_DECLARED = "provider_declared"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class CostComparisonStatus(str, Enum):
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    NOOP = "noop"


class CostPreferenceDirection(str, Enum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"
    BOUNDED_RANGE = "bounded_range"
    UNKNOWN_DIRECTION = "unknown_direction"
    CONTEXT_DEPENDENT = "context_dependent"


class CostDimensionStatus(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    UNKNOWN = "unknown"
    PARTIAL = "partial"
    STALE = "stale"
    LOSSY = "lossy"
    CONFLICTED = "conflicted"
    MISMATCH = "mismatch"


class ThroughputSupportStatus(str, Enum):
    NONE = "none"
    SINGLE_OBSERVATION_ONLY = "single_observation_only"
    PROVISIONAL_REPEATED = "provisional_repeated"
    SUPPORTED_REPEATED = "supported_repeated"
    CONFLICTED = "conflicted"


class CostBlockReason(str, Enum):
    MISSING_SOURCE_REFS = "missing_source_refs"
    OBSERVED_COST_WITHOUT_EFFECT_REFS = "observed_cost_without_effect_refs"
    DECLARED_COST_AS_OBSERVED = "declared_cost_as_observed"
    HIDDEN_BACKEND_COST_DETECTED = "hidden_backend_cost_detected"
    SCENARIO_LABEL_COST_DETECTED = "scenario_label_cost_detected"
    SELECTED_ACTION_ATTEMPTED = "selected_action_attempted"
    AP01_EMISSION_ATTEMPTED = "ap01_emission_attempted"
    WORLD_SUBMISSION_ATTEMPTED = "world_submission_attempted"
    VALUE_ASSIGNMENT_ATTEMPTED = "value_assignment_attempted"
    SCALAR_HIDES_DIMENSIONS = "scalar_hides_dimensions"
    UNKNOWN_DIMENSION_DEFAULTED_TO_ZERO = "unknown_dimension_defaulted_to_zero"
    THROUGHPUT_WITHOUT_REPETITION = "throughput_without_repetition"
    MISMATCH_WITHOUT_RESIDUE = "mismatch_without_residue"
    PRESSURE_CONTEXT_MISSING = "pressure_context_missing"
    PROVIDER_EFFICIENCY_AS_TRUTH = "provider_efficiency_as_truth"


@dataclass(frozen=True, slots=True)
class CostAuthorityFlags:
    can_select_action: bool = False
    can_publish_ap01: bool = False
    can_execute_world_action: bool = False
    can_claim_fact: bool = False
    can_confirm_cause: bool = False
    can_assign_value: bool = False
    can_mature_recipe: bool = False
    can_mature_skill: bool = False
    can_claim_automation: bool = False
    can_select_goal: bool = False
    can_claim_final_efficiency_truth: bool = False
    can_treat_provider_cost_as_observed: bool = False
    can_use_hidden_backend_cost: bool = False


@dataclass(frozen=True, slots=True)
class ActionCostDimension:
    dimension: CostDimension
    amount_ref: str | None = None
    amount_value: float | None = None
    unit: str | None = None
    evidence_kind: CostEvidenceKind = CostEvidenceKind.UNKNOWN
    source_refs: tuple[str, ...] = ()
    effect_refs: tuple[str, ...] = ()
    observation_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    status: CostDimensionStatus = CostDimensionStatus.UNKNOWN
    preference_direction: CostPreferenceDirection = CostPreferenceDirection.UNKNOWN_DIRECTION
    notes: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ActionCostVector:
    vector_id: str
    candidate_ref: str
    candidate_kind: str
    micro_operation_refs: tuple[str, ...]
    dimensions: tuple[ActionCostDimension, ...]
    source_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    observation_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    missing_dimension_refs: tuple[str, ...]
    current_pressure_context_refs: tuple[str, ...]
    authority_flags: CostAuthorityFlags
    validation_trace: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CostEvidenceRef:
    evidence_id: str
    evidence_kind: CostEvidenceKind
    dimension: CostDimension
    candidate_ref: str
    source_refs: tuple[str, ...]
    effect_refs: tuple[str, ...] = ()
    observation_refs: tuple[str, ...] = ()
    provider_refs: tuple[str, ...] = ()
    declared_by_ref: str | None = None
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    stale_marker: str | None = None
    blocked_reason: CostBlockReason | None = None


@dataclass(frozen=True, slots=True)
class DeclaredObservedCostDelta:
    delta_id: str
    candidate_ref: str
    dimension: CostDimension
    declared_cost_ref: str
    observed_cost_ref: str
    delta_direction: str
    delta_magnitude_ref: str | None = None
    mismatch_residue_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    status: CostDimensionStatus = CostDimensionStatus.MISMATCH


@dataclass(frozen=True, slots=True)
class ThroughputSupportFrame:
    throughput_id: str
    candidate_ref: str
    observation_trace_refs: tuple[str, ...]
    repeated_trace_count: int
    support_status: ThroughputSupportStatus
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    no_final_truth: bool = True


@dataclass(frozen=True, slots=True)
class EfficiencyEstimate:
    estimate_id: str
    candidate_ref: str
    support_vector_refs: tuple[str, ...]
    lower_cost_dimension_refs: tuple[str, ...]
    higher_cost_dimension_refs: tuple[str, ...]
    unknown_dimension_refs: tuple[str, ...]
    risk_warning_refs: tuple[str, ...]
    setup_warning_refs: tuple[str, ...]
    station_occupation_warning_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    confidence_band: str
    provisional: bool = True
    final_efficiency_truth: bool = False


@dataclass(frozen=True, slots=True)
class CostDimensionBreakdown:
    breakdown_id: str
    comparison_ref: str
    candidate_ref: str
    dimension_summaries: dict[str, str]
    missing_dimensions: tuple[str, ...]
    warnings: tuple[str, ...]
    no_hidden_scalar: bool = True


@dataclass(frozen=True, slots=True)
class CostComparisonCounters:
    vector_count: int = 0
    comparison_count: int = 0
    observed_dimension_count: int = 0
    estimated_dimension_count: int = 0
    provider_declared_dimension_count: int = 0
    inferred_dimension_count: int = 0
    unknown_dimension_count: int = 0
    missing_source_count: int = 0
    hidden_backend_cost_block_count: int = 0
    declared_as_observed_block_count: int = 0
    observed_without_effect_block_count: int = 0
    scalar_hiding_block_count: int = 0
    throughput_without_repetition_count: int = 0
    mismatch_residue_count: int = 0
    unknown_default_zero_block_count: int = 0
    selected_action_attempt_count: int = 0
    ap01_emission_attempt_count: int = 0
    value_assignment_attempt_count: int = 0
    risk_warning_count: int = 0
    setup_warning_count: int = 0
    station_occupation_warning_count: int = 0
    tool_wear_warning_count: int = 0
    uncertainty_warning_count: int = 0


@dataclass(frozen=True, slots=True)
class CostComparisonFrame:
    comparison_id: str
    compared_candidate_refs: tuple[str, ...]
    cost_vector_refs: tuple[str, ...]
    context_refs: tuple[str, ...]
    pressure_refs: tuple[str, ...]
    dimension_breakdown_refs: tuple[str, ...]
    efficiency_estimate_refs: tuple[str, ...]
    mismatch_residue_refs: tuple[str, ...]
    warning_refs: tuple[str, ...]
    comparison_trace_refs: tuple[str, ...]
    lower_cost_candidate_refs_by_dimension: dict[str, tuple[str, ...]]
    higher_cost_candidate_refs_by_dimension: dict[str, tuple[str, ...]]
    unresolved_candidate_refs: tuple[str, ...]
    blocked_candidate_refs: tuple[str, ...]
    no_selected_candidate: bool
    authority_flags: CostAuthorityFlags
    validation_status: CostComparisonStatus
    counters: CostComparisonCounters


@dataclass(frozen=True, slots=True)
class CostValidationResult:
    status: CostComparisonStatus
    blocked_reasons: tuple[CostBlockReason, ...]
    warnings: tuple[str, ...]
    counters: CostComparisonCounters
    vector_refs: tuple[str, ...]
    comparison: CostComparisonFrame | None
    vectors: tuple[ActionCostVector, ...]
    authority_flags: CostAuthorityFlags
    conformance_trace: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ActionCostVectorInput:
    vector_id: str
    candidate_ref: str
    candidate_kind: str
    micro_operation_refs: tuple[str, ...] = ()
    dimensions: tuple[ActionCostDimension, ...] = ()
    source_refs: tuple[str, ...] = ()
    effect_refs: tuple[str, ...] = ()
    observation_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    current_pressure_context_refs: tuple[str, ...] = ()
    metadata_refs: tuple[str, ...] = ()
    scalar_score_ref: str | None = None
    selected_action_attempt: bool = False
    ap01_emission_attempt: bool = False
    world_submission_attempt: bool = False
    value_assignment_attempt: bool = False


@dataclass(frozen=True, slots=True)
class CostComparisonInput:
    comparison_id: str
    vectors: tuple[ActionCostVector, ...]
    context_refs: tuple[str, ...] = ()
    pressure_refs: tuple[str, ...] = ()
    deltas: tuple[DeclaredObservedCostDelta, ...] = ()
    throughput_frames: tuple[ThroughputSupportFrame, ...] = ()
    selected_candidate_ref: str | None = None
    metadata_refs: tuple[str, ...] = ()
    ap01_emission_attempt: bool = False
    world_submission_attempt: bool = False
    value_assignment_attempt: bool = False
