from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class S03CandidateTargetClass(str, Enum):
    INTERNAL_CONTROL_PREDICTION = "internal_control_prediction"
    WORLD_SIDE_PREDICTION = "world_side_prediction"
    OBSERVATION_CALIBRATION = "observation_calibration"
    ANOMALY_CHANNEL = "anomaly_channel"


class S03OwnershipUpdateClass(str, Enum):
    SELF_UPDATE_DOMINANT = "self_update_dominant"
    WORLD_UPDATE_DOMINANT = "world_update_dominant"
    MIXED_SPLIT_UPDATE = "mixed_split_update"
    NO_SAFE_UPDATE = "no_safe_update"
    OBSERVATION_CHANNEL_RECALIBRATION_CANDIDATE = (
        "observation_channel_recalibration_candidate"
    )
    ANOMALY_ONLY_ROUTING = "anomaly_only_routing"


class S03CommitClass(str, Enum):
    COMMIT_UPDATE = "commit_update"
    CAP_UPDATE_MAGNITUDE = "cap_update_magnitude"
    DEFER_UNTIL_REVALIDATION = "defer_until_revalidation"
    ROUTE_TO_WORLD_MODEL_ONLY = "route_to_world_model_only"
    ROUTE_TO_INTERNAL_MODEL_ONLY = "route_to_internal_model_only"
    SPLIT_ACROSS_TARGETS = "split_across_targets"
    BLOCK_DUE_TO_CONFLICT = "block_due_to_conflict"


class S03AmbiguityClass(str, Enum):
    INSUFFICIENT_OWNERSHIP_BASIS = "insufficient_ownership_basis"
    ATTRIBUTION_CONFLICT = "attribution_conflict"
    MIXED_SOURCE_UPDATE_ONLY = "mixed_source_update_only"
    FREEZE_PENDING_REVALIDATION = "freeze_pending_revalidation"
    NO_SAFE_UPDATE_TARGET = "no_safe_update_target"


class S03FreezeOrDeferStatus(str, Enum):
    NONE = "none"
    CAPPED = "cap_update_magnitude"
    DEFERRED = "defer_until_revalidation"
    FROZEN = "freeze_pending_revalidation"
    BLOCKED = "block_due_to_conflict"


@dataclass(frozen=True, slots=True)
class S03TargetAllocation:
    target_class: S03CandidateTargetClass
    weight: float


@dataclass(frozen=True, slots=True)
class S03LearningAttributionPacket:
    outcome_packet_id: str
    attribution_basis: tuple[str, ...]
    update_class: S03OwnershipUpdateClass
    commit_class: S03CommitClass
    ambiguity_class: S03AmbiguityClass | None
    self_update_weight: float
    world_update_weight: float
    observation_update_weight: float
    anomaly_update_weight: float
    freeze_or_defer_status: S03FreezeOrDeferStatus
    target_model_classes: tuple[S03CandidateTargetClass, ...]
    target_allocations: tuple[S03TargetAllocation, ...]
    update_scope: str
    confidence: float
    repeated_support: int
    convergent_support: bool
    validity_status: str
    stale_or_invalidated: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class S03OwnershipWeightedLearningState:
    learning_id: str
    tick_index: int
    packets: tuple[S03LearningAttributionPacket, ...]
    latest_packet_id: str
    latest_update_class: S03OwnershipUpdateClass
    latest_commit_class: S03CommitClass
    latest_ambiguity_class: S03AmbiguityClass | None
    freeze_or_defer_state: S03FreezeOrDeferStatus
    requested_revalidation: bool
    repeated_self_support: int
    repeated_world_support: int
    repeated_mixed_support: int
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class S03LearningGateDecision:
    learning_packet_consumer_ready: bool
    mixed_update_consumer_ready: bool
    freeze_obedience_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class S03ScopeMarker:
    scope: str
    rt01_contour_only: bool
    s03_first_slice_only: bool
    s04_implemented: bool
    s05_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class S03Telemetry:
    learning_id: str
    tick_index: int
    latest_packet_id: str
    latest_update_class: str
    latest_commit_class: str
    freeze_or_defer_state: str
    requested_revalidation: bool
    self_update_weight: float
    world_update_weight: float
    observation_update_weight: float
    anomaly_update_weight: float
    repeated_self_support: int
    repeated_world_support: int
    repeated_mixed_support: int
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class S03OwnershipWeightedLearningResult:
    state: S03OwnershipWeightedLearningState
    gate: S03LearningGateDecision
    scope_marker: S03ScopeMarker
    telemetry: S03Telemetry
    reason: str
