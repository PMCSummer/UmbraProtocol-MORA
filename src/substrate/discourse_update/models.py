from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ProposalType(str, Enum):
    ASSERTION_UPDATE = "assertion_update"
    QUESTION_INTERPRETATION_UPDATE = "question_interpretation_update"
    DIRECTIVE_INTERPRETATION_UPDATE = "directive_interpretation_update"
    REPORTED_CONTENT_UPDATE = "reported_content_update"
    QUOTED_CONTENT_UPDATE = "quoted_content_update"
    ECHOIC_CONTENT_UPDATE = "echoic_content_update"
    UNKNOWN_INTERPRETATION_UPDATE = "unknown_interpretation_update"


class AcceptanceStatus(str, Enum):
    ACCEPTANCE_REQUIRED = "acceptance_required"
    NOT_ACCEPTED = "not_accepted"
    ACCEPTED = "accepted"


class RepairClass(str, Enum):
    REFERENCE_REPAIR = "reference_repair"
    FORCE_REPAIR = "force_repair"
    SCOPE_REPAIR = "scope_repair"
    POLARITY_REPAIR = "polarity_repair"
    MISSING_ARGUMENT_REPAIR = "missing_argument_repair"
    TARGET_APPLICABILITY_REPAIR = "target_applicability_repair"


class ContinuationStatus(str, Enum):
    PROPOSAL_ALLOWED_BUT_ACCEPTANCE_REQUIRED = "proposal_allowed_but_acceptance_required"
    BLOCKED_PENDING_REPAIR = "blocked_pending_repair"
    GUARDED_CONTINUE = "guarded_continue"
    ABSTAIN_UPDATE_WITHHELD = "abstain_update_withheld"


class DiscourseUpdateUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class UpdateProposal:
    proposal_id: str
    source_record_ids: tuple[str, ...]
    proposal_type: ProposalType
    target_discourse_surface: str
    proposed_effects: tuple[str, ...]
    acceptance_required: bool
    acceptance_status: AcceptanceStatus
    commitment_candidate: bool
    proposal_basis: tuple[str, ...]
    uncertainty_markers: tuple[str, ...]
    downstream_permissions: tuple[str, ...]
    downstream_restrictions: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class RepairTrigger:
    repair_id: str
    repair_class: RepairClass
    localized_trouble_source: str
    localized_ref_ids: tuple[str, ...]
    why_this_is_broken: str
    suggested_clarification_type: str
    blocked_updates: tuple[str, ...]
    guarded_continue_allowed: bool
    guarded_continue_forbidden: bool
    repair_basis: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class GuardedContinuationState:
    continuation_id: str
    source_record_id: str
    continuation_status: ContinuationStatus
    blocked_update_ids: tuple[str, ...]
    guarded_continue_allowed: bool
    guarded_continue_forbidden: bool
    acceptance_required: bool
    block_or_guard_reason: str
    localized_repair_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscourseUpdateBundle:
    source_modus_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_modus_record_ids: tuple[str, ...]
    update_proposals: tuple[UpdateProposal, ...]
    repair_triggers: tuple[RepairTrigger, ...]
    continuation_states: tuple[GuardedContinuationState, ...]
    blocked_update_ids: tuple[str, ...]
    guarded_update_ids: tuple[str, ...]
    acceptance_required_count: int
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    interpretation_not_equal_accepted_update: bool
    no_common_ground_mutation_performed: bool
    no_self_state_mutation_performed: bool
    no_final_acceptance_performed: bool
    downstream_update_acceptor_absent: bool
    repair_consumer_absent: bool
    discourse_state_mutation_consumer_absent: bool
    legacy_g01_bypass_risk_present: bool
    downstream_authority_degraded: bool
    reason: str


@dataclass(frozen=True, slots=True)
class DiscourseUpdateGateDecision:
    accepted: bool
    usability_class: DiscourseUpdateUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_proposal_ids: tuple[str, ...]
    rejected_proposal_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DiscourseUpdateTelemetry:
    source_lineage: tuple[str, ...]
    source_modus_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    proposal_count: int
    repair_count: int
    continuation_count: int
    proposal_classes: tuple[str, ...]
    repair_classes: tuple[str, ...]
    continuation_statuses: tuple[str, ...]
    blocked_update_count: int
    guarded_update_count: int
    acceptance_required_count: int
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    downstream_update_acceptor_absent: bool
    repair_consumer_absent: bool
    discourse_state_mutation_consumer_absent: bool
    legacy_g01_bypass_risk_present: bool
    attempted_paths: tuple[str, ...]
    downstream_gate: DiscourseUpdateGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class DiscourseUpdateResult:
    bundle: DiscourseUpdateBundle
    telemetry: DiscourseUpdateTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_acceptance_performed: bool
