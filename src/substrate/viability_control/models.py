from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.regulation.models import NeedAxis, RegulationConfidence


class ViabilityEscalationStage(str, Enum):
    BASELINE = "baseline"
    ELEVATED = "elevated"
    THREAT = "threat"
    CRITICAL = "critical"


class ViabilityPersistenceState(str, Enum):
    STABLE = "stable"
    EMERGING = "emerging"
    PERSISTENT = "persistent"
    CHRONIC = "chronic"
    RECOVERING = "recovering"


class ViabilityOverrideScope(str, Enum):
    NONE = "none"
    NARROW = "narrow"
    FOCUSED = "focused"
    BROAD = "broad"
    EMERGENCY = "emergency"


class ViabilityUncertaintyState(str, Enum):
    INSUFFICIENT_OBSERVABILITY = "insufficient_observability"
    BOUNDARY_UNCERTAIN = "boundary_uncertain"
    MIXED_DETERIORATION = "mixed_deterioration"
    UNRESOLVED_CONFLICT = "unresolved_conflict"
    DEGRADED_MODE_ONLY = "degraded_mode_only"
    NO_STRONG_OVERRIDE_CLAIM = "no_strong_override_claim"


class ViabilityDirectiveType(str, Enum):
    PRIORITY_RAISE = "priority_raise"
    TASK_PERMISSIVENESS_REDUCTION = "task_permissiveness_reduction"
    INTERRUPT_RECOMMENDATION = "interrupt_recommendation"
    FOCUS_RETENTION = "focus_retention"
    PROTECTIVE_MODE_REQUEST = "protective_mode_request"


@dataclass(frozen=True, slots=True)
class ViabilityCalibrationSpec:
    calibration_id: str
    schema_version: str = "r04.calibration.v1"
    formula_version: str = "r04.formula.v1"
    base_weight: float = 1.0
    worsening_weight: float = 1.0
    persistence_weight: float = 1.0
    failed_recovery_weight: float = 1.0
    time_to_boundary_critical_boost: float = 0.22
    time_to_boundary_threat_boost: float = 0.1
    worsening_normalizer: float = 40.0
    persistence_normalizer_steps: float = 20.0
    failed_recovery_step_penalty: float = 0.05
    max_worsening_component: float = 0.2
    max_persistence_component: float = 0.2
    max_failed_component: float = 0.15
    pressure_elevated_threshold: float = 0.35
    pressure_threat_threshold: float = 0.65
    pressure_critical_threshold: float = 0.85
    min_recoverability_evidence_quality: float = 0.2
    strong_override_min_recoverability_evidence: float = 0.35
    mixed_deterioration_requires_cap: bool = True
    mixed_deterioration_dominance_margin: float = 0.2
    epistemic_block_override_cap_threshold: int = 2


@dataclass(frozen=True, slots=True)
class ViabilityAxisBoundary:
    axis: NeedAxis
    elevated_pressure: float
    threat_pressure: float
    critical_pressure: float
    elevated_deviation: float
    threat_deviation: float
    critical_deviation: float
    threat_unresolved_steps: int
    critical_unresolved_steps: int


@dataclass(frozen=True, slots=True)
class ViabilityBoundarySpec:
    boundary_id: str
    axis_boundaries: tuple[ViabilityAxisBoundary, ...]
    critical_time_to_boundary: float
    threat_time_to_boundary: float
    schema_version: str = "r04.boundary.v1"
    taxonomy_version: str = "r02.affordance.v1"
    measurement_version: str = "r01.regulation.v1"


@dataclass(frozen=True, slots=True)
class ViabilityContext:
    source_lineage: tuple[str, ...] = ()
    prior_regulation_state: object | None = None
    prior_viability_state: ViabilityControlState | None = None
    recent_failed_recovery_attempts: int = 0
    step_delta: int = 1
    require_strong_override: bool = False
    expected_preference_schema_version: str = "r03.preference.v1"
    expected_taxonomy_version: str = "r02.affordance.v1"
    expected_measurement_version: str = "r01.regulation.v1"
    expected_boundary_schema_version: str = "r04.boundary.v1"
    expected_calibration_schema_version: str = "r04.calibration.v1"
    expected_calibration_id: str | None = None
    expected_calibration_formula_version: str = "r04.formula.v1"


@dataclass(frozen=True, slots=True)
class ViabilityRecoverabilityComponents:
    viable_affordance_coverage: float
    restorative_capacity_evidence: float
    blocked_or_unavailable_fraction: float
    preference_support_bias: float
    evidence_quality: float
    recent_failed_restoration_penalty: float


@dataclass(frozen=True, slots=True)
class ViabilityControlDirective:
    directive_id: str
    directive_type: ViabilityDirectiveType
    intensity: float
    affected_need_ids: tuple[NeedAxis, ...]
    override_scope: ViabilityOverrideScope
    reason: str
    capped_by_uncertainty: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class ViabilityControlState:
    pressure_level: float
    escalation_stage: ViabilityEscalationStage
    affected_need_ids: tuple[NeedAxis, ...]
    predicted_time_to_boundary: float | None
    recoverability_estimate: float | None
    recoverability_components: ViabilityRecoverabilityComponents | None
    calibration_id: str
    calibration_schema_version: str
    calibration_formula_version: str
    override_scope: ViabilityOverrideScope
    persistence_state: ViabilityPersistenceState
    deescalation_conditions: tuple[str, ...]
    confidence: RegulationConfidence
    uncertainty_state: tuple[ViabilityUncertaintyState, ...]
    recent_failed_recovery_count: int
    preference_epistemic_block_count: int
    mixed_deterioration: bool
    no_strong_override_claim: bool
    input_regulation_snapshot_ref: str
    input_affordance_ref: str
    input_preference_ref: str
    provenance: str


@dataclass(frozen=True, slots=True)
class ViabilityGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_directive_ids: tuple[str, ...]
    rejected_directive_ids: tuple[str, ...]
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ViabilityTelemetry:
    source_lineage: tuple[str, ...]
    input_regulation_snapshot_ref: str
    input_affordance_ref: str
    input_preference_ref: str
    affected_need_ids: tuple[NeedAxis, ...]
    computed_pressure_level: float
    computed_escalation_stage: ViabilityEscalationStage
    predicted_time_to_boundary: float | None
    recoverability_estimate: float | None
    recoverability_components: ViabilityRecoverabilityComponents | None
    calibration_id: str
    calibration_schema_version: str
    calibration_formula_version: str
    override_scope: ViabilityOverrideScope
    persistence_status: ViabilityPersistenceState
    deescalation_condition_markers: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    uncertainty_reasons: tuple[str, ...]
    downstream_gate: ViabilityGateDecision
    causal_basis: str
    attempted_computation_paths: tuple[str, ...]
    recent_failed_recovery_count: int
    preference_epistemic_block_count: int
    boundary_compatibility: tuple[str, ...]
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ViabilityControlResult:
    state: ViabilityControlState
    directives: tuple[ViabilityControlDirective, ...]
    downstream_gate: ViabilityGateDecision
    telemetry: ViabilityTelemetry
    abstain: bool
    abstain_reason: str | None
    no_action_selection_performed: bool
