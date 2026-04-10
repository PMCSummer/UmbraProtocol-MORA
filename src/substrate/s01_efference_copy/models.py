from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class S01SourceKind(str, Enum):
    INTERNAL_ACT = "internal_act"
    MODE_TRANSITION = "mode_transition"


class S01ComparisonAxis(str, Enum):
    MODE_TOKEN = "mode_token"
    WORLD_GROUNDED = "world_grounded"
    WORLD_EFFECT_FEEDBACK = "world_effect_feedback"
    WORLD_CONFIDENCE_DELTA = "world_confidence_delta"


class S01ComparisonStatus(str, Enum):
    MATCHED_AS_EXPECTED = "matched_as_expected"
    PARTIAL_MATCH = "partial_match"
    MAGNITUDE_MISMATCH = "magnitude_mismatch"
    DIRECTION_MISMATCH = "direction_mismatch"
    LATENCY_MISMATCH = "latency_mismatch"
    EXPECTED_BUT_UNOBSERVED = "expected_but_unobserved"
    UNEXPECTED_CHANGE_DETECTED = "unexpected_change_detected"
    COMPARISON_BLOCKED_BY_CONTAMINATION = "comparison_blocked_by_contamination"


class S01AttributionStatus(str, Enum):
    PREDICTED_COMPATIBLE_ONLY = "predicted_compatible_only"
    MIXED_CAUSE_CONTAMINATED = "mixed_cause_contaminated"
    ATTRIBUTION_BLOCKED = "attribution_blocked"


@dataclass(frozen=True, slots=True)
class S01ForwardModelPacket:
    packet_id: str
    intended_change: str
    expected_consequence: str
    action_context: tuple[str, ...]
    timing_window: tuple[int, int]
    mismatch_hooks: tuple[str, ...]
    created_tick: int
    expires_tick: int
    source_ref: str


@dataclass(frozen=True, slots=True)
class S01Prediction:
    prediction_id: str
    packet_id: str
    source_kind: S01SourceKind
    source_ref: str
    axis: S01ComparisonAxis
    created_tick: int
    earliest_tick: int
    preferred_tick: int
    expires_tick: int
    expected_bool: bool | None
    expected_token: str | None
    expected_direction: int | None
    expected_magnitude: float | None
    tolerance: float
    baseline_value: float | None
    contamination_sensitive: bool


@dataclass(frozen=True, slots=True)
class S01ObservedWindow:
    tick_index: int
    selected_mode: str
    mode_transition_detected: bool
    world_grounded_transition_admissible: bool
    world_effect_feedback_correlated: bool
    world_confidence: float | None
    contaminated: bool
    incomplete: bool
    source_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class S01ComparisonEntry:
    comparison_id: str
    prediction_id: str | None
    axis: S01ComparisonAxis
    status: S01ComparisonStatus
    attribution_status: S01AttributionStatus
    observed_tick: int
    latency_ticks: int | None
    magnitude_error: float | None
    observed_direction: int | None
    contamination_markers: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class S01EfferenceCopyState:
    efference_id: str
    tick_index: int
    pending_predictions: tuple[S01Prediction, ...]
    forward_packets: tuple[S01ForwardModelPacket, ...]
    comparisons: tuple[S01ComparisonEntry, ...]
    latest_comparison_status: S01ComparisonStatus | None
    comparison_blocked_by_contamination: bool
    stale_prediction_detected: bool
    unexpected_change_detected: bool
    strong_self_attribution_allowed: bool
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class S01GateDecision:
    comparison_ready: bool
    prediction_validity_ready: bool
    unexpected_change_detected: bool
    no_post_hoc_prediction_fabrication: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class S01ScopeMarker:
    scope: str
    rt01_contour_only: bool
    s01_first_slice_only: bool
    s02_implemented: bool
    s03_implemented: bool
    s04_implemented: bool
    s05_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class S01Telemetry:
    efference_id: str
    tick_index: int
    pending_predictions_count: int
    comparisons_count: int
    latest_comparison_status: str | None
    comparison_blocked_by_contamination: bool
    stale_prediction_detected: bool
    unexpected_change_detected: bool
    no_post_hoc_prediction_fabrication: bool
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class S01EfferenceCopyResult:
    state: S01EfferenceCopyState
    gate: S01GateDecision
    scope_marker: S01ScopeMarker
    telemetry: S01Telemetry
    reason: str
