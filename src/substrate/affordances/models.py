from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.regulation.models import NeedAxis, RegulationConfidence, RegulationState


class AffordanceOptionClass(str, Enum):
    ATTENTIONAL_NARROWING = "attentional_narrowing"
    LOAD_SHEDDING = "load_shedding"
    RECOVERY_PAUSE = "recovery_pause"
    NOVELTY_SUPPRESSION = "novelty_suppression"
    SAFETY_RECHECK = "safety_recheck"
    SOCIAL_REGULATION_BIAS = "social_regulation_bias"
    RESOURCE_CONSERVATION = "resource_conservation"


class AffordanceStatus(str, Enum):
    AVAILABLE = "available"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    UNSAFE = "unsafe"
    PROVISIONAL = "provisional"


class EffectClass(str, Enum):
    IMMEDIATE_RELIEF = "immediate_relief"
    DELAYED_RECOVERY = "delayed_recovery"
    PREVENTIVE_REGULATION = "preventive_regulation"
    PROTECTIVE_SUPPRESSION = "protective_suppression"


class EffectDirection(str, Enum):
    REDUCE_PRESSURE = "reduce_pressure"
    INCREASE_STABILITY = "increase_stability"
    SHIFT_SALIENCE = "shift_salience"
    REDUCE_EXPOSURE = "reduce_exposure"


@dataclass(frozen=True, slots=True)
class CapabilitySpec:
    option_class: AffordanceOptionClass
    enabled: bool = True
    max_intensity: float = 1.0
    cooldown_steps_remaining: int = 0
    risk_multiplier: float = 1.0
    source_ref: str | None = None


@dataclass(frozen=True, slots=True)
class CapabilityState:
    capabilities: tuple[CapabilitySpec, ...]
    confidence: RegulationConfidence = RegulationConfidence.MEDIUM
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AffordanceContext:
    source_lineage: tuple[str, ...] = ()
    max_risk_tolerance: float = 0.65
    allow_protective_suppression: bool = True
    require_available_candidates: bool = False


@dataclass(frozen=True, slots=True)
class ExpectedEffect:
    effect_class: EffectClass
    effect_direction: EffectDirection
    target_axes: tuple[NeedAxis, ...]
    effect_strength_estimate: float
    confidence: RegulationConfidence
    basis: str


@dataclass(frozen=True, slots=True)
class AffordanceCost:
    energy_cost: float
    cognitive_cost: float
    social_cost: float
    basis: str


@dataclass(frozen=True, slots=True)
class AffordanceRisk:
    level: float
    risk_note: str


@dataclass(frozen=True, slots=True)
class AffordanceApplicability:
    conditions: tuple[str, ...]
    blockers: tuple[str, ...]
    context_bounds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AffordanceTradeoffProfile:
    immediate_relief_score: float
    delayed_recovery_score: float
    preventive_score: float
    side_effect_axes: tuple[NeedAxis, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class UnknownEffectMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class BlockedMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class UnavailableMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class UnsafeMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class RegulationAffordance:
    affordance_id: str
    option_class: AffordanceOptionClass
    target_axes: tuple[NeedAxis, ...]
    status: AffordanceStatus
    expected_effect: ExpectedEffect
    cost: AffordanceCost
    risk: AffordanceRisk
    latency_steps: int
    duration_steps: int
    applicability: AffordanceApplicability
    blockers: tuple[str, ...]
    tradeoff: AffordanceTradeoffProfile
    confidence: RegulationConfidence
    provenance_basis: str
    unknown_effect: UnknownEffectMarker | None = None
    blocked_marker: BlockedMarker | None = None
    unavailable_marker: UnavailableMarker | None = None
    unsafe_marker: UnsafeMarker | None = None


@dataclass(frozen=True, slots=True)
class AffordanceSetSummary:
    total_candidates: int
    available_count: int
    blocked_count: int
    unavailable_count: int
    unsafe_count: int
    provisional_count: int
    no_selection_performed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AffordanceGateDecision:
    accepted_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    restrictions: tuple[str, ...]
    bias_hints: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class AffordanceAbstentionMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class AffordanceTelemetry:
    regulation_input_snapshot: dict[str, object]
    capability_snapshot: dict[str, object]
    generated_candidate_ids: tuple[str, ...]
    candidate_statuses: tuple[tuple[str, AffordanceStatus], ...]
    candidate_reasons: tuple[tuple[str, str], ...]
    expected_effects: tuple[tuple[str, float], ...]
    cost_risk_surface: tuple[tuple[str, float, float], ...]
    tradeoff_surface: tuple[tuple[str, float, float], ...]
    downstream_gate: AffordanceGateDecision
    confidence: RegulationConfidence
    abstain_reason: str | None
    causal_basis: str
    source_lineage: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AffordanceResult:
    regulation_state: RegulationState
    candidates: tuple[RegulationAffordance, ...]
    summary: AffordanceSetSummary
    gate: AffordanceGateDecision
    telemetry: AffordanceTelemetry
    abstention: AffordanceAbstentionMarker | None = None
