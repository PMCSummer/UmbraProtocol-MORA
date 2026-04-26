from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class P03AttributionClass(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NULL = "null"
    UNRESOLVED = "unresolved"
    CONFOUNDED_ASSOCIATION = "confounded_association"


class P03ContributionMode(str, Enum):
    DIRECT = "direct"
    ENABLING = "enabling"
    BLOCKING = "blocking"
    ADVERSE_SIDE_EFFECT = "adverse_side_effect"
    NEUTRAL_ASSOCIATION = "neutral_association"
    HYPOTHESIZED = "hypothesized"


class P03UpdateRecommendationKind(str, Enum):
    STRENGTHEN_GUARDED = "strengthen_guarded"
    WEAKEN_GUARDED = "weaken_guarded"
    ADD_PRECONDITION = "add_precondition"
    ADD_VERIFICATION_REQUIREMENT = "add_verification_requirement"
    SPLIT_INTERVENTION_CLASS = "split_intervention_class"
    KEEP_UNCHANGED = "keep_unchanged"
    DO_NOT_UPDATE = "do_not_update"


class P03WindowEvidenceStatus(str, Enum):
    WITHIN_WINDOW = "within_window"
    OUT_OF_WINDOW = "out_of_window"
    WINDOW_STILL_OPEN = "window_still_open"
    OUTCOME_UNVERIFIED = "outcome_unverified"
    EVIDENCE_CONFLICTED = "evidence_conflicted"


class P03ConfounderKind(str, Enum):
    PARALLEL_INTERVENTION = "parallel_intervention"
    BACKGROUND_DRIFT = "background_drift"
    MISSING_VERIFICATION = "missing_verification"
    EXTERNAL_CHANGE = "external_change"
    UNRESOLVED_RESIDUE = "unresolved_residue"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class P03OutcomeObservation:
    observation_id: str
    episode_ref: str
    horizon_class: str
    target_dimension: str
    effect_polarity: str
    magnitude: float
    verified: bool
    is_social_approval_signal: bool = False
    conflicted: bool = False
    occurred_order: int | None = None
    provenance: str = "p03.outcome_observation"


@dataclass(frozen=True, slots=True)
class P03ConfounderSignal:
    confounder_id: str
    episode_ref: str | None
    kind: P03ConfounderKind
    strength: float
    active: bool = True
    reason: str = ""
    provenance: str = "p03.confounder_signal"


@dataclass(frozen=True, slots=True)
class P03OutcomeWindow:
    window_id: str
    episode_ref: str
    start_order: int | None
    end_order: int | None
    evaluation_order: int | None
    status: P03WindowEvidenceStatus
    reason: str
    provenance: str = "p03.outcome_window"


@dataclass(frozen=True, slots=True)
class P03CreditAssignmentInput:
    input_id: str
    outcome_observations: tuple[P03OutcomeObservation, ...] = ()
    confounder_signals: tuple[P03ConfounderSignal, ...] = ()
    outcome_windows: tuple[P03OutcomeWindow, ...] = ()
    continuity_resolution_refs: tuple[str, ...] = ()
    delayed_outcome_refs: tuple[str, ...] = ()
    confounder_bundle_ref: str | None = None
    provenance: str = "p03.credit_assignment_input"


@dataclass(frozen=True, slots=True)
class P03AttributionConflict:
    conflict_id: str
    episode_ref: str
    reason_code: str
    conflicting_observation_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    unresolved: bool
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P03LearningRecommendation:
    recommendation_id: str
    episode_ref: str
    recommendation: P03UpdateRecommendationKind
    guarded: bool
    rationale_codes: tuple[str, ...]
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P03CreditRecord:
    record_id: str
    episode_ref: str
    attribution_class: P03AttributionClass
    contribution_mode: P03ContributionMode
    window_status: P03WindowEvidenceStatus
    primary_outcome_refs: tuple[str, ...]
    side_effect_outcome_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    side_effect_dominant: bool
    conflicts: tuple[P03AttributionConflict, ...]
    recommendation: P03LearningRecommendation
    confidence_band: str
    rationale_codes: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class P03NoUpdateRecord:
    record_id: str
    episode_ref: str
    attribution_class: P03AttributionClass
    window_status: P03WindowEvidenceStatus
    reason_code: str
    confounder_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    recommendation: P03LearningRecommendation
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P03CreditAssignmentRecordSet:
    assignment_id: str
    evaluated_episode_refs: tuple[str, ...]
    credit_records: tuple[P03CreditRecord, ...]
    no_update_records: tuple[P03NoUpdateRecord, ...]
    conflicts: tuple[P03AttributionConflict, ...]
    continuity_resolution_refs: tuple[str, ...]
    confounder_bundle_ref: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class P03CreditAssignmentGateDecision:
    credit_record_consumer_ready: bool
    no_update_consumer_ready: bool
    update_recommendation_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class P03ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    p03_frontier_slice_only: bool
    no_policy_mutation_authority: bool
    no_scalar_reward_shortcut: bool
    no_raw_approval_shortcut: bool
    no_full_causal_discovery_claim: bool
    no_map_wide_rollout_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P03Telemetry:
    evaluated_episode_count: int
    credit_record_count: int
    no_update_count: int
    positive_credit_count: int
    negative_credit_count: int
    mixed_credit_count: int
    unresolved_credit_count: int
    confounded_credit_count: int
    guarded_update_count: int
    side_effect_dominant_count: int
    outcome_window_open_count: int
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class P03CreditAssignmentResult:
    record_set: P03CreditAssignmentRecordSet
    gate: P03CreditAssignmentGateDecision
    scope_marker: P03ScopeMarker
    telemetry: P03Telemetry
    reason: str
