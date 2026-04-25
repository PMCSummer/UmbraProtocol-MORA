from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class C06CandidateClass(str, Enum):
    OPEN_QUESTION = "open_question"
    PENDING_CLARIFICATION = "pending_clarification"
    COMMITMENT_CARRYOVER = "commitment_carryover"
    THREATENED_COMMITMENT = "threatened_commitment"
    REPAIR_OBLIGATION = "repair_obligation"
    BOUNDARY_TO_PRESERVE = "boundary_to_preserve"
    PROJECT_CONTINUATION_CUE = "project_continuation_cue"
    PROTECTIVE_MONITOR = "protective_monitor"
    CLOSURE_CANDIDATE = "closure_candidate"
    WEAK_CANDIDATE = "weak_candidate"
    CLASS_AMBIGUOUS = "class_ambiguous"


class C06ContinuityHorizon(str, Enum):
    IMMEDIATE = "immediate"
    NEXT_TURN = "next_turn"
    SHORT_CHAIN = "short_chain"
    DEFERRED = "deferred"


class C06StrengthGrade(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    PROVISIONAL = "provisional"


class C06UncertaintyState(str, Enum):
    KNOWN = "known"
    PROVISIONAL = "provisional"
    UNRESOLVED = "unresolved"
    INSUFFICIENT_DELTA_BASIS = "insufficient_delta_basis"
    CANDIDATE_NEEDS_CONFIRMATION = "candidate_needs_confirmation"


class C06SuppressionReason(str, Enum):
    ALREADY_CLOSED = "already_closed"
    STYLISTICALLY_SALIENT_ONLY = "stylistically_salient_only"
    DUPLICATE_OF_STRONGER_CANDIDATE = "duplicate_of_stronger_candidate"
    OUTSIDE_CONTINUITY_HORIZON = "outside_continuity_horizon"
    INSUFFICIENT_BASIS = "insufficient_basis"
    UNRESOLVED_IDENTITY = "unresolved_identity"
    FRONTIER_NOT_PUBLISHED = "frontier_not_published"
    HIDDEN_WORKSPACE_ONLY = "hidden_workspace_only"


class C06SurfacingStatus(str, Enum):
    SURFACED = "surfaced"
    NO_CONTINUITY_CANDIDATES = "no_continuity_candidates"
    INSUFFICIENT_SURFACING_BASIS = "insufficient_surfacing_basis"


@dataclass(frozen=True, slots=True)
class C06SurfacingInput:
    input_id: str
    prior_unresolved_question_present: bool = False
    prior_commitment_carry_present: bool = False
    prior_repair_open: bool = False
    closure_resolved: bool = False
    discourse_state_tag: str = "open_discourse"
    published_frontier_item_ids: tuple[str, ...] = ()
    workspace_item_ids: tuple[str, ...] = ()
    unresolved_ambiguity_tokens: tuple[str, ...] = ()
    confidence_residue_tokens: tuple[str, ...] = ()
    salient_but_resolved_fragments: tuple[str, ...] = ()
    published_frontier_requirement: bool = True
    unresolved_ambiguity_preservation_required: bool = True
    confidence_residue_preservation_required: bool = True
    provenance: str = "c06.surfacing_input"


@dataclass(frozen=True, slots=True)
class C06SurfacedCandidate:
    candidate_id: str
    candidate_class: C06CandidateClass
    source_refs: tuple[str, ...]
    identity_hint: str
    identity_stabilizer: str
    continuity_horizon: C06ContinuityHorizon
    strength_grade: C06StrengthGrade
    uncertainty_state: C06UncertaintyState
    relation_to_current_project: str
    relation_to_discourse: str
    suggested_next_layer_consumers: tuple[str, ...]
    dismissal_risk: str
    rationale_codes: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class C06SuppressedItem:
    item_id: str
    suppression_reason: C06SuppressionReason
    source_refs: tuple[str, ...]
    rationale_codes: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class C06SuppressionReport:
    examined_item_count: int
    suppressed_item_count: int
    suppressed_items: tuple[C06SuppressedItem, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class C06CandidateSetMetadata:
    candidate_count: int
    ambiguous_candidate_count: int
    commitment_carryover_count: int
    repair_obligation_count: int
    protective_monitor_count: int
    closure_candidate_count: int
    duplicate_merge_count: int
    false_merge_detected: bool
    no_continuity_candidates: bool
    published_frontier_requirement: bool
    published_frontier_requirement_satisfied: bool
    unresolved_ambiguity_preserved: bool
    confidence_residue_preserved: bool
    source_lineage: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class C06SurfacedCandidateSet:
    candidate_set_id: str
    status: C06SurfacingStatus
    surfaced_candidates: tuple[C06SurfacedCandidate, ...]
    suppression_report: C06SuppressionReport
    metadata: C06CandidateSetMetadata
    reason: str


@dataclass(frozen=True, slots=True)
class C06SurfacingGateDecision:
    candidate_set_consumer_ready: bool
    suppression_report_consumer_ready: bool
    identity_merge_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class C06ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    c06_first_slice_only: bool
    c06_1_workspace_handoff_contract: bool
    no_retention_write_layer: bool
    no_project_reformation_layer: bool
    no_map_wide_rollout_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class C06Telemetry:
    candidate_set_id: str
    tick_index: int
    status: C06SurfacingStatus
    surfaced_candidate_count: int
    suppressed_item_count: int
    commitment_carryover_count: int
    repair_obligation_count: int
    protective_monitor_count: int
    closure_candidate_count: int
    ambiguous_candidate_count: int
    duplicate_merge_count: int
    false_merge_detected: bool
    published_frontier_requirement: bool
    unresolved_ambiguity_preserved: bool
    confidence_residue_preserved: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class C06SurfacingResult:
    candidate_set: C06SurfacedCandidateSet
    gate: C06SurfacingGateDecision
    scope_marker: C06ScopeMarker
    telemetry: C06Telemetry
    reason: str
