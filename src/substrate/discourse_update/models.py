from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


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


class L06RestrictionCode(StrEnum):
    L06_OBJECT_PRESENCE_NOT_ACCEPTANCE = "l06_object_presence_not_acceptance"
    OBJECT_PRESENCE_NOT_PERMISSION = "object_presence_not_permission"
    L06_SOURCE_MODUS_REF_MUST_BE_READ = "l06_source_modus_ref_must_be_read"
    L06_SOURCE_MODUS_REF_KIND_MUST_BE_READ = "l06_source_modus_ref_kind_must_be_read"
    L06_SOURCE_MODUS_LINEAGE_REF_MUST_BE_READ = "l06_source_modus_lineage_ref_must_be_read"
    PROPOSAL_REQUIRES_ACCEPTANCE = "proposal_requires_acceptance"
    ACCEPTANCE_REQUIRED_MUST_BE_READ = "acceptance_required_must_be_read"
    ACCEPTED_PROPOSAL_NOT_ACCEPTED_UPDATE = "accepted_proposal_not_accepted_update"
    INTERPRETATION_NOT_EQUAL_ACCEPTED_UPDATE = "interpretation_not_equal_accepted_update"
    PROPOSAL_EFFECTS_NOT_YET_AUTHORIZED = "proposal_effects_not_yet_authorized"
    PROPOSAL_NOT_TRUTH = "proposal_not_truth"
    PROPOSAL_NOT_SELF_UPDATE = "proposal_not_self_update"
    UPDATE_RECORD_NOT_STATE_MUTATION = "update_record_not_state_mutation"
    REPAIR_TRIGGER_MUST_BE_LOCALIZED = "repair_trigger_must_be_localized"
    REPAIR_LOCALIZATION_MUST_BE_READ = "repair_localization_must_be_read"
    GENERIC_CLARIFICATION_FORBIDDEN = "generic_clarification_forbidden"
    BLOCKED_UPDATE_MUST_BE_READ = "blocked_update_must_be_read"
    GUARDED_CONTINUE_NOT_ACCEPTANCE = "guarded_continue_not_acceptance"
    GUARDED_CONTINUE_REQUIRES_LIMITS_READ = "guarded_continue_requires_limits_read"
    DOWNSTREAM_MUST_READ_BLOCK_OR_REPAIR = "downstream_must_read_block_or_repair"
    L06_OUTPUT_NOT_DIALOGUE_MANAGER = "l06_output_not_dialogue_manager"
    L06_OUTPUT_NOT_PLANNER = "l06_output_not_planner"
    L06_OUTPUT_NOT_COMMON_GROUND_MUTATOR = "l06_output_not_common_ground_mutator"
    REPAIR_LOCALIZATION_GAP_DETECTED = "repair_localization_gap_detected"
    GENERIC_CLARIFICATION_DETECTED = "generic_clarification_detected"
    BLOCKED_UPDATE_CONTRACT_GAP_DETECTED = "blocked_update_contract_gap_detected"
    ACCEPTANCE_LAUNDERING_DETECTED = "acceptance_laundering_detected"
    REPAIR_GUARD_CONTRACT_GAP_DETECTED = "repair_guard_contract_gap_detected"
    PROPOSAL_RESTRICTION_SHAPE_GAP_DETECTED = "proposal_restriction_shape_gap_detected"
    PROPOSAL_PERMISSION_SHAPE_GAP_DETECTED = "proposal_permission_shape_gap_detected"
    ABSTAIN_UPDATE_WITHHELD_MUST_BE_READ = "abstain_update_withheld_must_be_read"
    SOURCE_REF_RELABELING_WITHOUT_NOTICE = "source_ref_relabeling_without_notice"
    DOWNSTREAM_UPDATE_ACCEPTOR_ABSENT = "downstream_update_acceptor_absent"
    REPAIR_CONSUMER_ABSENT = "repair_consumer_absent"
    DISCOURSE_STATE_MUTATION_CONSUMER_ABSENT = "discourse_state_mutation_consumer_absent"
    LEGACY_BYPASS_RISK_PRESENT = "legacy_bypass_risk_present"
    LEGACY_BYPASS_RISK_MUST_BE_READ = "legacy_bypass_risk_must_be_read"
    LEGACY_BYPASS_FORBIDDEN = "legacy_bypass_forbidden"
    NO_USABLE_UPDATE_PROPOSALS = "no_usable_update_proposals"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"
    DEGRADED_L06_REQUIRES_RESTRICTIONS_READ = "degraded_l06_requires_restrictions_read"


class L06CoverageCode(StrEnum):
    ABSTAIN = "abstain"
    DOWNSTREAM_UPDATE_ACCEPTOR_ABSENT = "downstream_update_acceptor_absent"
    REPAIR_CONSUMER_ABSENT = "repair_consumer_absent"
    DISCOURSE_STATE_MUTATION_CONSUMER_ABSENT = "discourse_state_mutation_consumer_absent"
    LEGACY_G01_BYPASS_RISK_PRESENT = "legacy_g01_bypass_risk_present"


class L06ProposalPermissionCode(StrEnum):
    PROPOSAL_WITHHELD_PENDING_REPAIR = "proposal_withheld_pending_repair"
    PROPOSAL_GUARDED_FORWARDABLE_IF_LIMITS_READ = (
        "proposal_guarded_forwardable_if_limits_read"
    )
    PROPOSAL_WITHHELD_NOT_FORWARDABLE = "proposal_withheld_not_forwardable"
    PROPOSAL_FORWARDABLE_IF_ACCEPTOR_EXISTS = "proposal_forwardable_if_acceptor_exists"


class L06ProposalRestrictionCode(StrEnum):
    L06_OBJECT_PRESENCE_NOT_ACCEPTANCE = "l06_object_presence_not_acceptance"
    PROPOSAL_REQUIRES_ACCEPTANCE = "proposal_requires_acceptance"
    ACCEPTANCE_REQUIRED_MUST_BE_READ = "acceptance_required_must_be_read"
    ACCEPTED_PROPOSAL_NOT_ACCEPTED_UPDATE = "accepted_proposal_not_accepted_update"
    PROPOSAL_EFFECTS_NOT_YET_AUTHORIZED = "proposal_effects_not_yet_authorized"
    PROPOSAL_NOT_TRUTH = "proposal_not_truth"
    PROPOSAL_NOT_SELF_UPDATE = "proposal_not_self_update"
    UPDATE_RECORD_NOT_STATE_MUTATION = "update_record_not_state_mutation"
    INTERPRETATION_NOT_EQUAL_ACCEPTED_UPDATE = "interpretation_not_equal_accepted_update"
    REPAIR_LOCALIZATION_MUST_BE_READ = "repair_localization_must_be_read"
    BLOCKED_UPDATE_MUST_BE_READ = "blocked_update_must_be_read"
    GUARDED_CONTINUE_REQUIRES_LIMITS_READ = "guarded_continue_requires_limits_read"
    GUARDED_CONTINUE_NOT_ACCEPTANCE = "guarded_continue_not_acceptance"
    ABSTAIN_UPDATE_WITHHELD_MUST_BE_READ = "abstain_update_withheld_must_be_read"


class L06ContinuationReasonCode(StrEnum):
    BLOCKED_PENDING_LOCALIZED_REPAIR = "blocked_pending_localized_repair"
    GUARDED_WITH_LOCALIZED_REPAIR = "guarded_with_localized_repair"
    REPAIR_REQUIRED_BEFORE_ACCEPTANCE = "repair_required_before_acceptance"
    HIGH_ENTROPY_GUARDED_CONTINUE = "high_entropy_guarded_continue"
    HIGH_ENTROPY_WITHHELD_UPDATE = "high_entropy_withheld_update"
    PROPOSAL_ALLOWED_ACCEPTANCE_REQUIRED = "proposal_allowed_acceptance_required"


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
    block_or_guard_reason_code: L06ContinuationReasonCode
    block_or_guard_reason: str
    localized_repair_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscourseUpdateBundle:
    bundle_ref: str
    source_modus_ref: str
    source_modus_ref_kind: str
    source_modus_lineage_ref: str
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
    bundle_ref: str
    source_modus_ref: str
    source_modus_ref_kind: str
    source_modus_lineage_ref: str
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
