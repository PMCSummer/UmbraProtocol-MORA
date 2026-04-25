from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class P02EpisodeStatus(str, Enum):
    CANDIDATE_EPISODE_ONLY = "candidate_episode_only"
    EXECUTED = "executed"
    COMPLETED_AS_LICENSED = "completed_as_licensed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    ABORTED = "aborted"
    DEFERRED = "deferred"
    AWAITING_VERIFICATION = "awaiting_verification"
    OVERRAN_SCOPE = "overran_scope"
    VERIFICATION_CONFLICTED = "verification_conflicted"
    OUTCOME_UNKNOWN = "outcome_unknown"


class P02ExecutionStatus(str, Enum):
    CANDIDATE_ONLY = "candidate_only"
    EXECUTED = "executed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    ABORTED = "aborted"
    DEFERRED = "deferred"


class P02OutcomeVerificationStatus(str, Enum):
    OUTCOME_UNKNOWN = "outcome_unknown"
    AWAITING_VERIFICATION = "awaiting_verification"
    OBSERVED_UNVERIFIED = "observed_unverified"
    VERIFIED = "verified"
    VERIFICATION_CONFLICTED = "verification_conflicted"


class P02ResidueKind(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    UNRESOLVED_SIDE_EFFECT = "unresolved_side_effect"
    FOLLOW_UP_OBLIGATION = "follow_up_obligation"
    CONTINUITY_HOOK = "continuity_hook"
    DISCHARGE_RECORD = "discharge_record"


@dataclass(frozen=True, slots=True)
class P02LicensedActionSnapshot:
    action_id: str
    source_license_ref: str
    license_scope_ref: str
    project_ref: str | None
    allowed: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class P02ExecutionEvent:
    event_id: str
    action_ref: str
    event_kind: str
    order_index: int
    source_license_ref: str | None = None
    project_ref: str | None = None
    continuation_hint: bool = True
    new_episode_hint: bool = False
    provenance: str = "p02.execution_event"


@dataclass(frozen=True, slots=True)
class P02OutcomeEvidence:
    evidence_id: str
    action_ref: str
    evidence_kind: str
    verified: bool = False
    conflicting: bool = False
    provenance: str = "p02.outcome_evidence"


@dataclass(frozen=True, slots=True)
class P02InterventionEpisodeInput:
    input_id: str
    licensed_actions: tuple[P02LicensedActionSnapshot, ...] = ()
    execution_events: tuple[P02ExecutionEvent, ...] = ()
    outcome_evidence: tuple[P02OutcomeEvidence, ...] = ()
    side_effect_refs: tuple[str, ...] = ()
    project_refs: tuple[str, ...] = ()
    provenance: str = "p02.intervention_episode_input"


@dataclass(frozen=True, slots=True)
class P02EpisodeBoundaryReport:
    boundary_window_start: int | None
    boundary_window_end: int | None
    action_trace_refs: tuple[str, ...]
    included_event_refs: tuple[str, ...]
    excluded_event_refs: tuple[str, ...]
    boundary_ambiguous: bool
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class P02CompletionAndVerificationState:
    execution_status: P02ExecutionStatus
    outcome_verification_status: P02OutcomeVerificationStatus
    status: P02EpisodeStatus
    completion_verified: bool
    awaiting_verification: bool
    verification_conflicted: bool
    outcome_unknown: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P02ResidueItem:
    residue_id: str
    residue_kind: P02ResidueKind
    ref_id: str
    unresolved: bool
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class P02InterventionEpisodeRecord:
    episode_id: str
    source_license_refs: tuple[str, ...]
    project_refs: tuple[str, ...]
    action_trace_refs: tuple[str, ...]
    excluded_event_refs: tuple[str, ...]
    boundary_window_start: int | None
    boundary_window_end: int | None
    boundary_report: P02EpisodeBoundaryReport
    status: P02EpisodeStatus
    completion_and_verification: P02CompletionAndVerificationState
    execution_status: P02ExecutionStatus
    outcome_verification_status: P02OutcomeVerificationStatus
    license_link_missing: bool
    overrun_detected: bool
    possible_overrun: bool
    side_effects: tuple[str, ...]
    residue: tuple[P02ResidueItem, ...]
    uncertainty_markers: tuple[str, ...]
    rationale_codes: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class P02EpisodeMetadata:
    episode_count: int
    completed_as_licensed_count: int
    partial_episode_count: int
    blocked_episode_count: int
    awaiting_verification_count: int
    completion_verified_count: int
    overrun_detected_count: int
    boundary_ambiguous_count: int
    license_link_missing_count: int
    residue_count: int
    side_effect_count: int
    source_lineage: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class P02EpisodeGateDecision:
    episode_consumer_ready: bool
    boundary_consumer_ready: bool
    verification_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class P02ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    p02_first_slice_only: bool
    no_project_formation_authority: bool
    no_action_licensing_authority: bool
    no_external_success_claim_without_evidence: bool
    no_memory_retention_authority: bool
    no_map_wide_rollout_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class P02Telemetry:
    episode_count: int
    completed_as_licensed_count: int
    partial_episode_count: int
    blocked_episode_count: int
    awaiting_verification_count: int
    overrun_detected_count: int
    boundary_ambiguous_count: int
    residue_count: int
    side_effect_count: int
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class P02InterventionEpisodeResult:
    episodes: tuple[P02InterventionEpisodeRecord, ...]
    metadata: P02EpisodeMetadata
    gate: P02EpisodeGateDecision
    scope_marker: P02ScopeMarker
    telemetry: P02Telemetry
    reason: str
