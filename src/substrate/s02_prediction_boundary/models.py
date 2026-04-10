from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class S02BoundaryStatus(str, Enum):
    INSIDE_SELF_PREDICTIVE_SEAM = "inside_self_predictive_seam"
    MIXED_SOURCE_BOUNDARY = "mixed_source_boundary"
    EXTERNALLY_DOMINATED_BOUNDARY = "externally_dominated_boundary"
    CONTROLLABLE_BUT_UNRELIABLE = "controllable_but_unreliable"
    PREDICTABLE_BUT_NOT_SELF_DRIVEN = "predictable_but_not_self_driven"
    BOUNDARY_UNCERTAIN = "boundary_uncertain"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    NO_CLEAN_SEAM_CLAIM = "no_clean_seam_claim"
    SEAM_INVALIDATED_FOR_CONTEXT = "seam_invalidated_for_context"


class ForbiddenS02Shortcut(str, Enum):
    HARDCODED_CHANNEL_SELF_WORLD_MAP = "hardcoded_channel_self_world_map"
    ONE_SHOT_SEAM_FROM_SINGLE_SUCCESS = "one_shot_seam_from_single_success"
    PREDICTION_SUCCESS_AS_SELF_CONTROL_PROXY = (
        "prediction_success_as_self_control_proxy"
    )
    PREDICTABLE_COLLAPSED_INTO_SELF_SIDE = "predictable_collapsed_into_self_side"
    MIXED_SOURCE_BINARIZED = "mixed_source_binarized"
    STALE_SEAM_CARRIED_WITHOUT_REVALIDATION = (
        "stale_seam_carried_without_revalidation"
    )


@dataclass(frozen=True, slots=True)
class S02EvidenceCounters:
    repeated_outcome_support: int
    matched_support: int
    mismatch_support: int
    contamination_support: int
    unexpected_residual_support: int
    internal_control_support: int
    external_regularity_support: int


@dataclass(frozen=True, slots=True)
class S02SeamEntry:
    seam_entry_id: str
    channel_or_effect_class: str
    boundary_status: S02BoundaryStatus
    controllability_estimate: float
    prediction_reliability_estimate: float
    external_dominance_estimate: float
    mixed_source_score: float
    context_scope: tuple[str, ...]
    validity_marker: str
    boundary_confidence: float
    provenance: str
    evidence_counters: S02EvidenceCounters
    last_boundary_update: int


@dataclass(frozen=True, slots=True)
class S02PredictionBoundaryState:
    boundary_id: str
    tick_index: int
    seam_entries: tuple[S02SeamEntry, ...]
    active_boundary_status: S02BoundaryStatus
    boundary_uncertain: bool
    insufficient_coverage: bool
    no_clean_seam_claim: bool
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class S02BoundaryGateDecision:
    boundary_consumer_ready: bool
    controllability_consumer_ready: bool
    mixed_source_consumer_ready: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class S02ScopeMarker:
    scope: str
    rt01_contour_only: bool
    s02_first_slice_only: bool
    s03_implemented: bool
    s04_implemented: bool
    s05_implemented: bool
    full_self_model_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class S02Telemetry:
    boundary_id: str
    tick_index: int
    seam_entries_count: int
    active_boundary_status: S02BoundaryStatus
    boundary_uncertain: bool
    insufficient_coverage: bool
    no_clean_seam_claim: bool
    boundary_consumer_ready: bool
    controllability_consumer_ready: bool
    mixed_source_consumer_ready: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class S02PredictionBoundaryResult:
    state: S02PredictionBoundaryState
    gate: S02BoundaryGateDecision
    scope_marker: S02ScopeMarker
    telemetry: S02Telemetry
    reason: str
