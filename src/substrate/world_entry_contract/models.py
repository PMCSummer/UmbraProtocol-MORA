from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WorldPresenceMode(str, Enum):
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    OBSERVATION_ONLY = "observation_only"
    ACTION_PENDING_EFFECT = "action_pending_effect"
    ACTION_EFFECT_OBSERVED = "action_effect_observed"


class WorldClaimClass(str, Enum):
    EXTERNALLY_EFFECTED_CHANGE_CLAIM = "externally_effected_change_claim"
    WORLD_GROUNDED_SUCCESS_CLAIM = "world_grounded_success_claim"
    ENVIRONMENT_STATE_CHANGE_CLAIM = "environment_state_change_claim"
    ACTION_SUCCESS_IN_WORLD_CLAIM = "action_success_in_world_claim"
    STABLE_WORLD_REGULARIZATION_CLAIM = "stable_world_regularization_claim"
    WORLD_CALIBRATION_CLAIM = "world_calibration_claim"


class WorldClaimStatus(str, Enum):
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"
    UNDERCONSTRAINED = "underconstrained"
    NOT_ADMISSIBLE = "not_admissible"


@dataclass(frozen=True, slots=True)
class WorldEntryEpisode:
    world_episode_id: str
    observation_basis_present: bool
    action_trace_present: bool
    effect_basis_present: bool
    effect_feedback_correlated: bool
    episode_scope: str
    world_presence_mode: WorldPresenceMode
    evidence_window: tuple[str | None, str | None]
    source_lineage: tuple[str, ...]
    provenance: str
    confidence: float
    reliability: str
    degraded: bool
    incomplete: bool


@dataclass(frozen=True, slots=True)
class WorldClaimAdmission:
    claim_class: WorldClaimClass
    status: WorldClaimStatus
    admitted: bool
    required_basis: tuple[str, ...]
    missing_basis: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W01AdmissionCriteria:
    typed_world_episode_exists: bool
    observation_action_effect_linkable: bool
    basis_inspectable_and_provenance_aware: bool
    missing_world_fallback_explicit: bool
    forbidden_claims_machine_readable: bool
    rt01_world_seam_consumable_without_w01_rebrand: bool
    admission_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class WorldEntryScopeMarker:
    scope: str
    admission_layer_only: bool
    w01_implemented: bool
    w_line_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class WorldEntryTelemetry:
    world_episode_id: str
    world_presence_mode: WorldPresenceMode
    confidence: float
    reliability: str
    degraded: bool
    incomplete: bool
    forbidden_claim_classes: tuple[str, ...]
    w01_admission_ready: bool
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class WorldEntryContractResult:
    episode: WorldEntryEpisode
    claim_admissions: tuple[WorldClaimAdmission, ...]
    forbidden_claim_classes: tuple[str, ...]
    world_grounded_transition_admissible: bool
    world_effect_success_admissible: bool
    w01_admission: W01AdmissionCriteria
    scope_marker: WorldEntryScopeMarker
    telemetry: WorldEntryTelemetry
    reason: str
