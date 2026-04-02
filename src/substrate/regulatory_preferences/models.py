from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.affordances.models import AffordanceOptionClass
from substrate.regulation.models import NeedAxis, RegulationConfidence, RegulationState


class PreferenceSign(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class PreferenceConflictState(str, Enum):
    NONE = "none"
    CONFLICTING = "conflicting"


class PreferenceUpdateStatus(str, Enum):
    ACTIVE = "active"
    PROVISIONAL = "provisional"
    FROZEN = "frozen"
    STALE = "stale"


class PreferenceTimeHorizon(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PreferenceUncertainty(str, Enum):
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    ATTRIBUTION_BLOCKED = "attribution_blocked"
    DELAYED_EFFECT_UNRESOLVED = "delayed_effect_unresolved"
    PROVISIONAL_COLD_START = "provisional_cold_start"


class PreferenceUpdateKind(str, Enum):
    STRENGTHEN = "strengthen"
    WEAKEN = "weaken"
    INVERT = "invert"
    FREEZE = "freeze"
    CONFLICT_REGISTER = "conflict_register"
    NO_CLAIM = "no_claim"
    DECAY = "decay"


@dataclass(frozen=True, slots=True)
class OutcomeTrace:
    episode_id: str
    option_class_id: AffordanceOptionClass
    affordance_id: str | None
    target_need_or_set: tuple[NeedAxis, ...]
    context_scope: tuple[str, ...]
    observed_short_term_delta: float
    observed_long_term_delta: float | None
    attribution_confidence: RegulationConfidence
    mixed_causes: bool = False
    delayed_window_complete: bool = True
    source_ref: str | None = None
    provenance: str = ""
    observed_at_step: int = 0


@dataclass(frozen=True, slots=True)
class PreferenceEntry:
    entry_id: str
    option_class_id: AffordanceOptionClass
    target_need_or_set: tuple[NeedAxis, ...]
    preference_sign: PreferenceSign
    preference_strength: float
    expected_short_term_delta: float
    expected_long_term_delta: float
    confidence: RegulationConfidence
    context_scope: tuple[str, ...]
    time_horizon: PreferenceTimeHorizon
    conflict_state: PreferenceConflictState
    episode_support: int
    staleness_steps: int
    decay_marker: float
    last_update_provenance: str
    update_status: PreferenceUpdateStatus


@dataclass(frozen=True, slots=True)
class BlockedPreferenceUpdate:
    episode_id: str
    option_class_id: AffordanceOptionClass | None
    uncertainty: PreferenceUncertainty
    reason: str
    frozen: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class PreferenceUpdateEvent:
    event_id: str
    entry_id: str | None
    prior_entry_ref: str | None
    observed_episode_ref: str
    update_kind: PreferenceUpdateKind
    reason_tags: tuple[str, ...]
    provenance: str
    delta_strength: float
    short_term_delta: float | None
    long_term_delta: float | None


@dataclass(frozen=True, slots=True)
class PreferenceState:
    entries: tuple[PreferenceEntry, ...]
    unresolved_updates: tuple[BlockedPreferenceUpdate, ...]
    conflict_index: tuple[str, ...]
    frozen_updates: tuple[BlockedPreferenceUpdate, ...]
    schema_version: str = "r03.preference.v1"
    taxonomy_version: str = "r02.affordance.v1"
    measurement_version: str = "r01.regulation.v1"
    last_updated_step: int = 0


@dataclass(frozen=True, slots=True)
class PreferenceContext:
    source_lineage: tuple[str, ...] = ()
    step_delta: int = 1
    learning_rate: float = 0.25
    decay_per_step: float = 0.03
    min_strong_confidence: RegulationConfidence = RegulationConfidence.MEDIUM
    require_long_term_signal: bool = False
    freeze_on_mixed_causes: bool = True
    conflict_threshold: float = 0.2
    max_abs_observed_delta: float = 1.0
    expected_schema_version: str = "r03.preference.v1"
    expected_taxonomy_version: str = "r02.affordance.v1"
    expected_measurement_version: str = "r01.regulation.v1"


@dataclass(frozen=True, slots=True)
class PreferenceGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_entry_ids: tuple[str, ...]
    rejected_entry_ids: tuple[str, ...]
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class PreferenceTelemetry:
    source_lineage: tuple[str, ...]
    input_regulation_snapshot_ref: str
    input_affordance_ids: tuple[str, ...]
    processed_episode_ids: tuple[str, ...]
    updated_entry_ids: tuple[str, ...]
    blocked_update_count: int
    conflict_count: int
    freeze_update_count: int
    short_term_signal_count: int
    long_term_signal_count: int
    attribution_blocked_reasons: tuple[str, ...]
    context_keys_used: tuple[str, ...]
    decay_events: tuple[str, ...]
    downstream_gate: PreferenceGateDecision
    causal_basis: str
    attempted_update_paths: tuple[str, ...]
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class PreferenceUpdateResult:
    updated_preference_state: PreferenceState
    update_events: tuple[PreferenceUpdateEvent, ...]
    blocked_updates: tuple[BlockedPreferenceUpdate, ...]
    downstream_gate: PreferenceGateDecision
    telemetry: PreferenceTelemetry
    regulation_state_ref: RegulationState
    no_final_selection_performed: bool
    abstain: bool
    abstain_reason: str | None
