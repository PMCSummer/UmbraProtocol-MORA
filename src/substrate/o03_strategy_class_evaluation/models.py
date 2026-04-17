from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class O03StrategyClass(str, Enum):
    COOPERATIVE_PREFERRED = "cooperative_preferred"
    COOPERATIVE_BUT_COSTLY = "cooperative_but_costly"
    NEUTRAL_COORDINATION = "neutral_coordination"
    ASYMMETRY_PRESENT_BUT_BOUNDED = "asymmetry_present_but_bounded"
    MANIPULATION_RISK_HIGH = "manipulation_risk_high"
    STRATEGY_CLASS_UNDERCONSTRAINED = "strategy_class_underconstrained"
    NO_SAFE_CLASSIFICATION = "no_safe_classification"
    HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY = "high_local_gain_but_high_entropy"


class O03HiddenDivergenceBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O03AsymmetryExploitationBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O03DependencyRiskBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O03RepairabilityBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class O03ReversibilityBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class O03AutonomyPressureBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O03EntropyBurdenBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O03LocalEffectivenessBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O03CandidateMoveKind(str, Enum):
    EXPLANATION = "explanation"
    RECOMMENDATION = "recommendation"
    CONSTRAINT_PROPOSAL = "constraint_proposal"
    CLARIFICATION = "clarification"
    UNKNOWN = "unknown"


class O03StrategyLeverPreference(str, Enum):
    REQUIRE_TRANSPARENCY_INCREASE = "require_transparency_increase"
    REQUIRE_DISCLOSURE = "require_disclosure"
    REQUIRE_UNCERTAINTY_EXPOSURE = "require_uncertainty_exposure"
    REQUIRE_REVERSIBILITY_PRESERVATION = "require_reversibility_preservation"
    REQUIRE_CLARIFICATION = "require_clarification"
    DEMOTE_CANDIDATE = "demote_candidate"
    BLOCK_EXPLOITATIVE_MOVE = "block_exploitative_move"
    PREFER_COOPERATIVE_DEFAULT = "prefer_cooperative_default"
    PRESERVE_AUTONOMY_SPACE = "preserve_autonomy_space"


@dataclass(frozen=True, slots=True)
class O03CandidateStrategyInput:
    candidate_move_id: str = "o03:default_candidate"
    candidate_move_kind: O03CandidateMoveKind = O03CandidateMoveKind.UNKNOWN
    explicit_disclosure_present: bool = False
    material_uncertainty_omitted: bool = False
    selective_omission_risk_marker: bool = False
    asymmetry_opportunity_marker: bool = False
    autonomy_narrowing_marker: bool = False
    dependency_shaping_marker: bool = False
    reversibility_preserved: bool = True
    repairability_preserved: bool = True
    expected_local_effectiveness_band: O03LocalEffectivenessBand = O03LocalEffectivenessBand.MEDIUM
    strong_compliance_pull_marker: bool = False
    truthfulness_constraint_tension: float = 0.0
    authority_constraint_tension: float = 0.0
    downstream_effect_visibility_marker: bool = True
    repeated_dependency_pressure_count: int = 0


@dataclass(frozen=True, slots=True)
class O03StrategyEvaluationState:
    strategy_id: str
    candidate_move_id: str
    strategy_class: O03StrategyClass
    cooperation_score: float
    manipulation_risk_score: float
    hidden_divergence_cost: float
    asymmetry_exploitation_score: float
    dependency_induction_risk: float
    autonomy_pressure_score: float
    epistemic_distortion_cost: float
    repair_burden_forecast: float
    trust_fragility_forecast: float
    reversibility_score: float
    repairability_score: float
    transparency_score: float
    local_effectiveness_pressure: O03LocalEffectivenessBand
    hidden_divergence_band: O03HiddenDivergenceBand
    asymmetry_exploitation_band: O03AsymmetryExploitationBand
    dependency_risk_band: O03DependencyRiskBand
    repairability_band: O03RepairabilityBand
    reversibility_band: O03ReversibilityBand
    autonomy_pressure_band: O03AutonomyPressureBand
    entropy_burden_band: O03EntropyBurdenBand
    strategy_classification_confidence: float
    other_model_reliance_status: str
    truthfulness_constraint_binding: bool
    strategy_lever_preferences: tuple[O03StrategyLeverPreference, ...]
    justification_links: tuple[str, ...]
    provenance: str
    no_safe_classification: bool
    strategy_underconstrained: bool
    asymmetry_present_but_not_exploitative: bool
    concealed_state_divergence_required: bool
    high_local_gain_but_high_entropy: bool
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class O03StrategyEvaluationGateDecision:
    strategy_contract_consumer_ready: bool
    cooperative_selection_consumer_ready: bool
    transparency_preserving_consumer_ready: bool
    exploitative_move_block_required: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class O03ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    o03_first_slice_only: bool
    o04_not_implemented: bool
    r05_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class O03Telemetry:
    strategy_id: str
    tick_index: int
    candidate_move_id: str
    strategy_class: O03StrategyClass
    hidden_divergence_band: O03HiddenDivergenceBand
    asymmetry_exploitation_band: O03AsymmetryExploitationBand
    dependency_risk_band: O03DependencyRiskBand
    entropy_burden_band: O03EntropyBurdenBand
    strategy_classification_confidence: float
    no_safe_classification: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class O03StrategyEvaluationResult:
    state: O03StrategyEvaluationState
    gate: O03StrategyEvaluationGateDecision
    scope_marker: O03ScopeMarker
    telemetry: O03Telemetry
    reason: str

