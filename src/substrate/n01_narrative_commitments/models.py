from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class N01NarrativeClaimKind(str, Enum):
    SELF_DESCRIPTION = "self_description"
    STATE_DESCRIPTION = "state_description"
    CAPABILITY_CLAIM = "capability_claim"
    LIMITATION_CLAIM = "limitation_claim"
    INTENTION_CLAIM = "intention_claim"
    RELATION_CLAIM = "relation_claim"
    VALUE_LIKE_STANCE = "value_like_stance"
    CONTINUITY_CLAIM = "continuity_claim"
    PROVISIONAL_NARRATIVE = "provisional_narrative"
    UNKNOWN_OR_UNTYPED = "unknown_or_untyped"


class N01CommitmentDecision(str, Enum):
    CONFIRMED_COMMITMENT = "confirmed_commitment"
    PROVISIONAL_COMMITMENT = "provisional_commitment"
    STATEMENT_ONLY_RECORD = "statement_only_record"
    REVISED_COMMITMENT = "revised_commitment"
    RETIRED_COMMITMENT = "retired_commitment"
    CONTESTED_COMMITMENT = "contested_commitment"
    NO_CLEAN_COMMITMENT_CLAIM = "no_clean_commitment_claim"


class N01CommitmentStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    PROVISIONAL = "provisional"
    MODERATE = "moderate"
    STRONG = "strong"
    CONTESTED = "contested"


class N01CommitmentScope(str, Enum):
    MOMENTARY = "momentary"
    CURRENT_TURN = "current_turn"
    DIALOGUE_LOCAL = "dialogue_local"
    MODE_LOCAL = "mode_local"
    EPISODIC = "episodic"
    SHORT_HORIZON = "short_horizon"
    LONG_HORIZON = "long_horizon"
    GLOBAL_FORBIDDEN_UNLESS_EXPLICITLY_GROUNDED = (
        "global_forbidden_unless_explicitly_grounded"
    )


class N01GroundingBasisKind(str, Enum):
    EXPLICIT_SELF_REPORT = "explicit_self_report"
    INTERNAL_STATE_SUMMARY = "internal_state_summary"
    TEMPORAL_VALIDITY_SUPPORT = "temporal_validity_support"
    SELF_ATTRIBUTION_SUPPORT = "self_attribution_support"
    CAPABILITY_AFFORDANCE_SUPPORT = "capability_affordance_support"
    CAPABILITY_GAP_SUPPORT = "capability_gap_support"
    INTERNAL_TOOL_SUPPORT = "internal_tool_support"
    ACTIVE_MODE_SUPPORT = "active_mode_support"
    CONTINUITY_SUPPORT = "continuity_support"
    MIXED_OR_CONTESTED_BASIS = "mixed_or_contested_basis"
    INVALIDATED_BASIS = "invalidated_basis"
    INSUFFICIENT_BASIS = "insufficient_basis"


class N01ConflictStatus(str, Enum):
    NO_CONFLICT = "no_conflict"
    CONTRADICTS_EXISTING_STRONG = "contradicts_existing_strong"
    CONTRADICTS_EXISTING_PROVISIONAL = "contradicts_existing_provisional"
    SCOPE_CONFLICT = "scope_conflict"
    BASIS_INVALIDATION_CONFLICT = "basis_invalidation_conflict"
    UNRESOLVED_NARRATIVE_TENSION = "unresolved_narrative_tension"


class N01RevisionAction(str, Enum):
    NO_REVISION_NEEDED = "no_revision_needed"
    DOWNGRADE_STRENGTH = "downgrade_strength"
    NARROW_SCOPE = "narrow_scope"
    MARK_CONTESTED = "mark_contested"
    RETRACT = "retract"
    REPLACE_WITH_EXPLICIT_REVISION = "replace_with_explicit_revision"
    REQUIRE_REVALIDATION_BEFORE_REUSE = "require_revalidation_before_reuse"


class N01DownstreamObligationKind(str, Enum):
    MUST_REMAIN_CONSISTENT_IN_SELF_REPORT = "must_remain_consistent_in_self_report"
    MUST_NOT_CLAIM_BEYOND_SCOPE = "must_not_claim_beyond_scope"
    MUST_TRIGGER_RECHECK_BEFORE_REUSE = "must_trigger_recheck_before_reuse"
    MUST_CONSTRAIN_FUTURE_EXPLANATION = "must_constrain_future_explanation"
    MUST_SURFACE_CONTRADICTION = "must_surface_conflict"
    MAY_BE_REVISED_ONLY_UNDER_CONDITION = "may_be_revised_only_under_condition"
    NO_DOWNSTREAM_OBLIGATION = "no_downstream_obligation"


@dataclass(frozen=True, slots=True)
class N01NarrativeClaimCandidate:
    candidate_id: str
    claim_text_or_semantic_form: str
    claim_kind: N01NarrativeClaimKind
    requested_scope: N01CommitmentScope
    expression_channel: str
    addressee_or_audience_scope: str
    grounding_basis: tuple[N01GroundingBasisKind, ...]
    temporal_validity_status: str
    attribution_status: str
    self_side_confidence: float
    mixed_cause_marker: bool
    capability_support: bool = False
    limitation_support: bool = False
    affordance_support: bool = False
    gap_support: bool = False
    internal_tool_support: bool = False
    active_mode_support: bool = False
    continuity_support: bool = False
    conflict_marker: bool = False
    conflict_basis: str = ""
    existing_commitment_refs: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    timestamp_or_sequence: str = ""


@dataclass(frozen=True, slots=True)
class N01CommitmentEntry:
    commitment_id: str
    source_candidate_id: str
    claim_kind: N01NarrativeClaimKind
    semantic_content: str
    strength: N01CommitmentStrength
    scope: N01CommitmentScope
    grounding_basis: tuple[N01GroundingBasisKind, ...]
    temporal_horizon: str
    addressee_or_audience_scope: str
    referenced_commitment_refs: tuple[str, ...]
    revision_conditions: tuple[str, ...]
    invalidation_triggers: tuple[str, ...]
    conflict_status: N01ConflictStatus
    conflict_priority: int
    downstream_obligations: tuple[N01DownstreamObligationKind, ...]
    validation_status: str
    confidence: float
    decision: N01CommitmentDecision
    revision_action: N01RevisionAction
    reason_codes: tuple[str, ...]
    provenance: tuple[str, ...]
    prior_decision: N01CommitmentDecision | None = None
    prior_validation_status: str | None = None
    revision_reason: str | None = None


@dataclass(frozen=True, slots=True)
class N01CommitmentLedger:
    accepted_commitments: tuple[N01CommitmentEntry, ...]
    statement_only_candidates: tuple[N01NarrativeClaimCandidate, ...]
    contested_commitments: tuple[N01CommitmentEntry, ...]
    revised_commitments: tuple[N01CommitmentEntry, ...]
    retired_commitments: tuple[N01CommitmentEntry, ...]
    reason_codes: tuple[str, ...]
    no_safe_commit_count: int
    provenance: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class N01GateDecision:
    consumer_ready: bool
    consistency_consumer_ready: bool
    strong_commitment_count: int
    provisional_commitment_count: int
    statement_only_count: int
    contested_commitment_count: int
    revised_or_retired_count: int
    scope_narrowed_count: int
    ungrounded_capability_claim_count: int
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class N01Telemetry:
    candidate_count: int
    commitment_count: int
    strong_commitment_count: int
    provisional_commitment_count: int
    statement_only_count: int
    contested_commitment_count: int
    revised_count: int
    retired_count: int
    scope_narrowed_count: int
    ungrounded_capability_claim_count: int
    consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class N01ScopeMarker:
    scope: str
    frontier_only: bool
    narrow_slice_only: bool
    narrative_commitment_registry_only: bool
    no_identity_metaphysics_claim: bool
    no_full_autobiography_claim: bool
    no_memory_lifecycle_claim: bool
    no_policy_selection_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class N01InputBundle:
    bundle_id: str
    candidates: tuple[N01NarrativeClaimCandidate, ...]
    existing_commitments: tuple[N01CommitmentEntry, ...] = ()
    source_lineage: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class N01Result:
    bundle_id: str
    commitment_entries: tuple[N01CommitmentEntry, ...]
    ledger: N01CommitmentLedger
    telemetry: N01Telemetry
    gate: N01GateDecision
    scope_marker: N01ScopeMarker
    reason: str
