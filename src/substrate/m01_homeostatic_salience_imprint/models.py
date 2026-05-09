from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class M01TraceKind(str, Enum):
    EVENT = "event"
    EPISODE = "episode"
    INTERVENTION = "intervention"
    RECOVERY = "recovery"


class M01RegulatoryDirection(str, Enum):
    WORSENING = "worsening"
    IMPROVING = "improving"
    STABILIZING = "stabilizing"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class M01TemporalWindowStatus(str, Enum):
    WITHIN_WINDOW = "within_window"
    DELAYED_BUT_PLAUSIBLE = "delayed_but_plausible"
    OUT_OF_WINDOW = "out_of_window"
    MISSING_TIMING = "missing_timing"
    CONTESTED_TIMING = "contested_timing"


class M01AttributionStatus(str, Enum):
    SELF_RELEVANT = "self_relevant"
    MIXED = "mixed"
    EXTERNALLY_DOMINATED = "externally_dominated"
    OBSERVATION_ARTIFACT_RISK = "observation_artifact_risk"
    ATTRIBUTION_UNCERTAIN = "attribution_uncertain"
    NO_CLEAN_ATTRIBUTION = "no_clean_attribution"


class M01ImprintDecisionType(str, Enum):
    STRONG_THREAT_IMPRINT = "strong_threat_imprint"
    STRONG_STRAIN_IMPRINT = "strong_strain_imprint"
    STRONG_RELIEF_IMPRINT = "strong_relief_imprint"
    STRONG_RECOVERY_IMPRINT = "strong_recovery_imprint"
    PROVISIONAL_MULTI_AXIS_IMPRINT = "provisional_multi_axis_imprint"
    WEAK_HOMEOSTATIC_LINK = "weak_homeostatic_link"
    ATTRIBUTION_LIMITED_IMPRINT = "attribution_limited_imprint"
    STALE_BASIS_NO_STRONG_IMPRINT = "stale_basis_no_strong_imprint"
    NO_SAFE_IMPRINT_CLAIM = "no_safe_imprint_claim"


class M01SignOfEffect(str, Enum):
    PERTURBATION = "perturbation"
    STRAIN = "strain"
    RELIEF = "relief"
    RECOVERY = "recovery"
    STABILIZATION = "stabilization"
    MIXED = "mixed"
    UNCLEAR = "unclear"


class M01LifecycleAdjustment(str, Enum):
    REINFORCE_EXISTING_IMPRINT = "reinforce_existing_imprint"
    DECAY_WITHOUT_RECONFIRMATION = "decay_without_reconfirmation"
    KEEP_NARROW_SCOPE_ONLY = "keep_narrow_scope_only"
    DOWNGRADE_DUE_TO_ATTRIBUTION_CHANGE = "downgrade_due_to_attribution_change"
    NO_ADJUSTMENT = "no_adjustment"


@dataclass(frozen=True, slots=True)
class M01TraceInput:
    trace_id: str
    trace_kind: M01TraceKind
    semantic_signature: str
    timestamp_or_sequence: str
    scope: str
    novelty_hint: float | None = None
    recency_hint: float | None = None
    outcome_hint: str | None = None
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class M01RegulatoryAxisDelta:
    delta_id: str
    axis_id: str
    before_value: float
    after_value: float
    deviation_before: float
    deviation_after: float
    direction: M01RegulatoryDirection
    intensity: float
    rate_hint: float
    measurement_confidence: float
    stabilization_marker: bool = False
    recovery_marker: bool = False
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class M01TemporalCouplingEvidence:
    trace_id: str
    regulatory_delta_refs: tuple[str, ...]
    temporal_window_status: M01TemporalWindowStatus
    confidence: float


@dataclass(frozen=True, slots=True)
class M01AttributionEvidence:
    trace_id: str
    attribution_status: M01AttributionStatus
    self_side_share: float
    residual_uncertainty: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class M01AllowedMemoryUse:
    may_bias_retention: bool
    may_bias_replay: bool
    may_bias_retrieval: bool
    must_preserve_axis_scope: bool
    must_preserve_transfer_limits: bool
    must_not_treat_as_general_importance: bool


@dataclass(frozen=True, slots=True)
class M01ImprintPacket:
    imprint_id: str
    source_trace_id: str
    affected_axes: tuple[str, ...]
    sign_of_effect: M01SignOfEffect
    decision: M01ImprintDecisionType
    imprint_strength: float
    retention_bias: float
    replay_priority: float
    retrieval_bias: float
    persistence_hint: str
    transfer_limits: tuple[str, ...]
    confidence: float
    reason_codes: tuple[str, ...]
    lifecycle_adjustment: M01LifecycleAdjustment
    allowed_memory_use: M01AllowedMemoryUse
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class M01LedgerEntry:
    entry_id: str
    source_trace_id: str
    decision: M01ImprintDecisionType
    temporal_window_status: M01TemporalWindowStatus
    attribution_status: M01AttributionStatus
    affected_axes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    anti_overgeneralization_limits: tuple[str, ...]
    lifecycle_adjustment: M01LifecycleAdjustment


@dataclass(frozen=True, slots=True)
class M01Telemetry:
    trace_count: int
    imprint_count: int
    strong_imprint_count: int
    weak_or_no_claim_count: int
    attribution_limited_count: int
    recovery_imprint_count: int
    no_safe_imprint_count: int
    consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class M01ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    homeostatic_imprint_not_general_importance: bool
    not_reward_function: bool
    not_narrative_relevance: bool
    not_full_memory_system: bool
    no_policy_claim: bool
    no_global_value_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class M01GateDecision:
    consumer_ready: bool
    imprint_packet_consumer_ready: bool
    axis_scope_consumer_ready: bool
    no_safe_imprint_claim: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class M01InputBundle:
    bundle_id: str
    traces: tuple[M01TraceInput, ...]
    regulatory_deltas: tuple[M01RegulatoryAxisDelta, ...]
    temporal_coupling: tuple[M01TemporalCouplingEvidence, ...]
    attribution: tuple[M01AttributionEvidence, ...]
    prior_imprints: tuple[M01ImprintPacket, ...] = ()
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class M01Result:
    bundle_id: str
    imprint_packets: tuple[M01ImprintPacket, ...]
    ledger: tuple[M01LedgerEntry, ...]
    telemetry: M01Telemetry
    gate: M01GateDecision
    scope_marker: M01ScopeMarker
    reason: str
