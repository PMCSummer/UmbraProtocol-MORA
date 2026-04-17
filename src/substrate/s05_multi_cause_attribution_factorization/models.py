from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class S05CauseClass(str, Enum):
    SELF_INITIATED_ACT = "self_initiated_act"
    ENDOGENOUS_MODE_CONTRIBUTION = "endogenous_mode_contribution"
    INTEROCEPTIVE_OR_REGULATORY_DRIFT = "interoceptive_or_regulatory_drift"
    EXTERNAL_OR_WORLD_CONTRIBUTION = "external_or_world_contribution"
    OBSERVATION_OR_CHANNEL_ARTIFACT = "observation_or_channel_artifact"
    UNEXPLAINED_RESIDUAL = "unexplained_residual"


class S05EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    CAPPED = "capped"
    INCOMPATIBLE = "incompatible"
    INSUFFICIENT_BASIS = "insufficient_basis"


class S05AttributionStatus(str, Enum):
    FACTORIZED_MULTI_CAUSE = "factorized_multi_cause"
    INSUFFICIENT_FACTOR_BASIS = "insufficient_factor_basis"
    UNDERDETERMINED_SPLIT = "underdetermined_split"
    INCOMPATIBLE_CAUSE_CANDIDATES = "incompatible_cause_candidates"
    RESIDUAL_TOO_LARGE = "residual_too_large"
    NO_CLEAN_FACTORIZATION_CLAIM = "no_clean_factorization_claim"
    BOUNDED_INTERVAL_ONLY = "bounded_interval_only"


class S05RevisionStatus(str, Enum):
    INITIAL_PROVISIONAL = "initial_provisional"
    STABLE_NO_REVISION = "stable_no_revision"
    REVISED_WITH_LATE_EVIDENCE = "revised_with_late_evidence"


class S05ScopeValidity(str, Enum):
    BOUNDED_VALID_FOR_ROUTING = "bounded_valid_for_routing"
    PROVISIONAL_REQUIRES_REVALIDATION = "provisional_requires_revalidation"
    INVALID_FOR_STRONG_CLAIMS = "invalid_for_strong_claims"


class S05ResidualClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class S05DownstreamRouteClass(str, Enum):
    SELF_ACT_HEAVY = "self_act_heavy"
    MODE_DRIFT_HEAVY = "mode_drift_heavy"
    INTEROCEPTIVE_DRIFT_HEAVY = "interoceptive_drift_heavy"
    WORLD_HEAVY = "world_heavy"
    OBSERVATION_ARTIFACT_HEAVY = "observation_artifact_heavy"
    HIGH_RESIDUAL_UNDERDETERMINED = "high_residual_underdetermined"
    MIXED_FACTORIZED = "mixed_factorized"


@dataclass(frozen=True, slots=True)
class S05OutcomePacketInput:
    outcome_packet_id: str
    mismatch_magnitude: float
    observed_delta_class: str
    expected_delta_class: str
    outcome_channel: str
    observed_tick: int
    preferred_tick: int
    expires_tick: int
    contaminated: bool
    source_ref: str


@dataclass(frozen=True, slots=True)
class S05CauseSlotEntry:
    cause_class: S05CauseClass
    eligibility_status: S05EligibilityStatus
    support_strength: float
    allocated_share: float | None
    bounded_share_interval: tuple[float, float] | None
    evidence_basis: tuple[str, ...]
    temporal_fit: float
    channel_fit: float
    contamination_penalty: float
    provenance: str


@dataclass(frozen=True, slots=True)
class S05FactorizationPacket:
    outcome_packet_id: str
    cause_slots: tuple[S05CauseSlotEntry, ...]
    slot_weights_or_bounded_shares: tuple[tuple[str, float | tuple[float, float]], ...]
    unexplained_residual: float
    residual_class: S05ResidualClass
    compatibility_basis: tuple[str, ...]
    temporal_alignment_basis: tuple[str, ...]
    contamination_notes: tuple[str, ...]
    confidence: float
    provenance: str
    revision_status: S05RevisionStatus
    attribution_status: S05AttributionStatus
    scope_validity: S05ScopeValidity
    downstream_route_class: S05DownstreamRouteClass


@dataclass(frozen=True, slots=True)
class S05MultiCauseAttributionState:
    factorization_id: str
    tick_index: int
    packets: tuple[S05FactorizationPacket, ...]
    latest_packet_id: str
    dominant_cause_classes: tuple[S05CauseClass, ...]
    unexplained_residual: float
    residual_class: S05ResidualClass
    underdetermined_split: bool
    incompatible_candidates_present: bool
    temporal_misalignment_present: bool
    contamination_present: bool
    reattribution_happened: bool
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class S05AttributionGateDecision:
    factorization_consumer_ready: bool
    learning_route_ready: bool
    no_binary_recollapse_required: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class S05ScopeMarker:
    scope: str
    rt01_contour_only: bool
    s05_first_slice_only: bool
    downstream_rollout_minimal: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class S05Telemetry:
    factorization_id: str
    tick_index: int
    dominant_slot_count: int
    residual_share: float
    residual_class: S05ResidualClass
    underdetermined_split: bool
    contamination_present: bool
    temporal_misalignment_present: bool
    reattribution_happened: bool
    downstream_route_class: S05DownstreamRouteClass
    factorization_consumer_ready: bool
    learning_route_ready: bool
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class S05MultiCauseAttributionResult:
    state: S05MultiCauseAttributionState
    gate: S05AttributionGateDecision
    scope_marker: S05ScopeMarker
    telemetry: S05Telemetry
    reason: str
