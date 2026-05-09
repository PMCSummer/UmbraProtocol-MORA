from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class M02TraceKind(str, Enum):
    EVENT = "event"
    EPISODE = "episode"
    ROUTINE = "routine"
    OBSERVATION = "observation"


class M02TargetType(str, Enum):
    REGIME_DETECTION = "regime_detection"
    TOOL_SUCCESS_EXPECTATION = "tool_success_expectation"
    CAPABILITY_BOUNDARY_ANTICIPATION = "capability_boundary_anticipation"
    FAILURE_PRECURSOR_RECOGNITION = "failure_precursor_recognition"
    TIMING_EXPECTATION = "timing_expectation"
    CONTEXT_TRANSITION_EXPECTATION = "context_transition_expectation"


class M02UtilityHorizon(str, Enum):
    IMMEDIATE = "immediate"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    UNKNOWN = "unknown"


class M02PredictiveRelevanceDecision(str, Enum):
    STRONG_BORING_PREDICTOR = "strong_boring_predictor"
    REPEATED_WEAK_PREDICTOR = "repeated_weak_predictor"
    CONTEXT_LOCKED_PREDICTOR = "context_locked_predictor"
    PROVISIONAL_PREDICTOR = "provisional_predictor"
    SPURIOUS_PATTERN_RISK = "spurious_pattern_risk"
    WEAK_PREDICTIVE_SUPPORT = "weak_predictive_support"
    INSUFFICIENT_REPETITION = "insufficient_repetition"
    TARGET_UNCERTAIN = "target_uncertain"
    NO_SAFE_PREDICTIVE_MARK = "no_safe_predictive_mark"


class M02PredictiveLifecycleAdjustment(str, Enum):
    REINFORCE_AFTER_REPLICATION = "reinforce_after_replication"
    DECAY_AFTER_FAILED_TRANSFER = "decay_after_failed_transfer"
    NARROW_SCOPE_DUE_TO_CONTEXT_LOCK = "narrow_scope_due_to_context_lock"
    SUPPRESS_DUE_TO_SPURIOUS_RISK = "suppress_due_to_spurious_risk"
    NO_REINFORCEMENT_WITHOUT_GAIN = "no_reinforcement_without_gain"
    KEEP_PROVISIONAL_UNTIL_CORROBORATED = "keep_provisional_until_corroborated"
    NO_ADJUSTMENT = "no_adjustment"


@dataclass(frozen=True, slots=True)
class M02PredictiveTrace:
    trace_id: str
    trace_kind: M02TraceKind
    semantic_label: str
    boredom_level: float
    vividness_level: float
    novelty_level: float
    timestamp_or_sequence: str
    context_scope: str
    mode_context: str
    tool_context: str | None = None
    homeostatic_imprint_ref: str | None = None
    homeostatic_strength_hint: float | None = None
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class M02PredictionTarget:
    target_id: str
    target_type: M02TargetType
    utility_horizon: M02UtilityHorizon
    context_scope: str
    success_metric: str
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class M02PredictiveFeedback:
    feedback_id: str
    trace_id: str
    target_id: str
    prediction_gain: float
    error_delta: float
    corroboration_count: int
    failed_transfer_count: int
    spurious_risk_score: float
    context_locked: bool
    attribution_noise_risk: bool
    confidence: float
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class M02PredictiveRelevanceMark:
    predictive_mark_id: str
    source_trace_id: str
    predicted_target_types: tuple[M02TargetType, ...]
    decision: M02PredictiveRelevanceDecision
    relevance_strength: float
    utility_horizon: M02UtilityHorizon
    context_scope: str
    corroboration_count: int
    anti_spurious_limits: tuple[str, ...]
    retrieval_bias: float
    retention_bias: float
    replay_priority: float
    indexing_bias: float
    planning_support_recall_bias: float
    confidence: float
    reason_codes: tuple[str, ...]
    lifecycle_adjustment: M02PredictiveLifecycleAdjustment
    must_preserve_context: bool
    must_not_generalize: bool
    must_not_treat_as_generic_importance: bool
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class M02LedgerEntry:
    entry_id: str
    trace_id: str
    target_refs: tuple[str, ...]
    decision: M02PredictiveRelevanceDecision
    reason_codes: tuple[str, ...]
    utility_gain: float
    anti_spurious_result: str
    utility_horizon: M02UtilityHorizon
    context_scope: str
    lifecycle_adjustment: M02PredictiveLifecycleAdjustment


@dataclass(frozen=True, slots=True)
class M02Telemetry:
    trace_count: int
    predictive_mark_count: int
    clean_predictive_mark_count: int
    weak_mark_count: int
    context_locked_count: int
    spurious_risk_count: int
    no_safe_mark_count: int
    consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class M02ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    predictive_relevance_not_generic_importance: bool
    no_full_prediction_claim: bool
    no_full_memory_lifecycle_claim: bool
    no_planner_policy_claim: bool
    separate_from_homeostatic_imprint: bool
    reason: str


@dataclass(frozen=True, slots=True)
class M02GateDecision:
    consumer_ready: bool
    predictive_packet_consumer_ready: bool
    context_scope_consumer_ready: bool
    clean_predictive_mark_count: int
    weak_mark_count: int
    context_locked_count: int
    spurious_risk_count: int
    no_safe_mark_count: int
    downstream_must_preserve_context: bool
    downstream_must_not_generalize: bool
    downstream_must_not_treat_as_generic_importance: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class M02InputBundle:
    bundle_id: str
    traces: tuple[M02PredictiveTrace, ...]
    prediction_targets: tuple[M02PredictionTarget, ...]
    predictive_feedback: tuple[M02PredictiveFeedback, ...]
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class M02Result:
    bundle_id: str
    predictive_marks: tuple[M02PredictiveRelevanceMark, ...]
    ledger: tuple[M02LedgerEntry, ...]
    telemetry: M02Telemetry
    gate: M02GateDecision
    scope_marker: M02ScopeMarker
    reason: str
