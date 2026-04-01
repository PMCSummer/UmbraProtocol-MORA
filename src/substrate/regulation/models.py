from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class NeedAxis(str, Enum):
    ENERGY = "energy"
    COGNITIVE_LOAD = "cognitive_load"
    SAFETY = "safety"
    SOCIAL_CONTACT = "social_contact"
    NOVELTY = "novelty"


class RegulationConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeviationDirection(str, Enum):
    BELOW_RANGE = "below_range"
    ABOVE_RANGE = "above_range"
    IN_RANGE = "in_range"


@dataclass(frozen=True, slots=True)
class PreferredRange:
    min_value: float
    max_value: float


@dataclass(frozen=True, slots=True)
class NeedSignal:
    axis: NeedAxis
    value: float
    source_ref: str | None = None
    confidence: RegulationConfidence | None = None


@dataclass(frozen=True, slots=True)
class NeedState:
    axis: NeedAxis
    current_value: float
    preferred_range: PreferredRange
    deviation: float
    deviation_direction: DeviationDirection
    pressure: float
    load_accumulated: float
    unresolved_steps: int
    last_signal_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DeviationRecord:
    axis: NeedAxis
    preferred_range: PreferredRange
    current_value: float
    deviation: float
    direction: DeviationDirection


@dataclass(frozen=True, slots=True)
class PressureState:
    axis: NeedAxis
    pressure: float
    load_accumulated: float
    unresolved_steps: int


@dataclass(frozen=True, slots=True)
class TradeoffPair:
    first_axis: NeedAxis
    second_axis: NeedAxis
    reason: str


@dataclass(frozen=True, slots=True)
class TradeoffState:
    active_axes: tuple[NeedAxis, ...]
    dominant_axis: NeedAxis | None
    suppressed_axes: tuple[NeedAxis, ...]
    competing_pairs: tuple[TradeoffPair, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class PartialKnownMarker:
    missing_axes: tuple[NeedAxis, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class AbstentionMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class RegulationBias:
    urgency_by_axis: tuple[tuple[NeedAxis, float], ...]
    salience_order: tuple[NeedAxis, ...]
    coping_mode: str
    claim_strength: str
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class RegulationState:
    needs: tuple[NeedState, ...]
    confidence: RegulationConfidence
    partial_known: PartialKnownMarker | None = None
    abstention: AbstentionMarker | None = None
    last_updated_step: int = 0


@dataclass(frozen=True, slots=True)
class RegulationContext:
    step_delta: int = 1
    source_lineage: tuple[str, ...] = ()
    require_strong_claim: bool = False


@dataclass(frozen=True, slots=True)
class RegulationTelemetry:
    tracked_axes: tuple[NeedAxis, ...]
    source_lineage: tuple[str, ...]
    signal_refs: tuple[str, ...]
    used_preferred_ranges: tuple[tuple[NeedAxis, PreferredRange], ...]
    deviations: tuple[DeviationRecord, ...]
    pressures: tuple[PressureState, ...]
    tradeoff: TradeoffState
    downstream_bias: RegulationBias
    confidence: RegulationConfidence
    partial_known_reason: str | None
    abstain_reason: str | None
    causal_basis: str
    attempted_paths: tuple[str, ...]
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class RegulationResult:
    state: RegulationState
    tradeoff: TradeoffState
    bias: RegulationBias
    telemetry: RegulationTelemetry
