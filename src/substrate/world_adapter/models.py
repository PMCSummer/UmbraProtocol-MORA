from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WorldLinkStatus(str, Enum):
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    OBSERVATION_ONLY = "observation_only"
    ACTION_PENDING_EFFECT = "action_pending_effect"
    ACTION_EFFECT_OBSERVED = "action_effect_observed"


class WorldEffectStatus(str, Enum):
    NO_ACTION = "no_action"
    PENDING_FEEDBACK = "pending_feedback"
    OBSERVED_SUCCESS = "observed_success"
    OBSERVED_FAILURE = "observed_failure"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class WorldObservationPacket:
    observation_id: str
    observation_kind: str
    source_ref: str
    observed_at: str
    payload_ref: str
    provenance: str


@dataclass(frozen=True, slots=True)
class WorldActionPacket:
    action_id: str
    action_kind: str
    target_ref: str
    requested_at: str
    payload_ref: str
    provenance: str


@dataclass(frozen=True, slots=True)
class WorldEffectObservationPacket:
    effect_id: str
    action_id: str
    effect_kind: str
    observed_at: str
    success: bool
    source_ref: str
    provenance: str


@dataclass(frozen=True, slots=True)
class WorldAdapterInput:
    adapter_presence: bool = False
    adapter_available: bool = False
    adapter_degraded: bool = False
    observation_packet: WorldObservationPacket | None = None
    action_packet: WorldActionPacket | None = None
    effect_packet: WorldEffectObservationPacket | None = None
    source_lineage: tuple[str, ...] = ()
    reason: str = "world_adapter_input"


@dataclass(frozen=True, slots=True)
class WorldAdapterState:
    adapter_presence: bool
    adapter_available: bool
    adapter_degraded: bool
    world_link_status: WorldLinkStatus
    effect_status: WorldEffectStatus
    last_observation_packet: WorldObservationPacket | None
    last_action_packet: WorldActionPacket | None
    last_effect_packet: WorldEffectObservationPacket | None
    effect_feedback_correlated: bool
    world_grounding_confidence: float
    unavailable_reason: str | None
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class WorldAdapterGateDecision:
    world_grounded_transition_allowed: bool
    externally_effected_change_claim_allowed: bool
    world_action_success_claim_allowed: bool
    effect_feedback_correlated: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class WorldAdapterTelemetry:
    source_lineage: tuple[str, ...]
    world_link_status: WorldLinkStatus
    effect_status: WorldEffectStatus
    adapter_presence: bool
    adapter_available: bool
    adapter_degraded: bool
    world_grounded_transition_allowed: bool
    externally_effected_change_claim_allowed: bool
    world_action_success_claim_allowed: bool
    effect_feedback_correlated: bool
    restrictions: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class WorldAdapterResult:
    state: WorldAdapterState
    gate: WorldAdapterGateDecision
    telemetry: WorldAdapterTelemetry
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
