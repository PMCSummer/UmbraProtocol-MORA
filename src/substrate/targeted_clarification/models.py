from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


class InterventionStatus(str, Enum):
    ASK_NOW = "ask_now"
    ABSTAIN_WITHOUT_QUESTION = "abstain_without_question"
    GUARDED_CONTINUE_WITH_LIMITS = "guarded_continue_with_limits"
    DEFER_UNTIL_NEEDED = "defer_until_needed"
    BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY = "blocked_due_to_insufficient_questionability"
    CLARIFICATION_NOT_WORTH_COST = "clarification_not_worth_cost"


class UncertaintyClass(str, Enum):
    OWNER_SCOPE_AMBIGUITY = "owner_scope_ambiguity"
    TEMPORAL_ANCHOR_AMBIGUITY = "temporal_anchor_ambiguity"
    FRAME_COMPETITION = "frame_competition"
    HIGH_IMPACT_BINDING_RISK = "high_impact_binding_risk"
    CONTEXT_ONLY_UNCERTAINTY = "context_only_uncertainty"
    RESIDUAL_UNCERTAINTY = "residual_uncertainty"
    REPAIR_TRIGGER_GAP = "repair_trigger_gap"


class InterventionUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class G07RestrictionCode(StrEnum):
    NO_FINAL_SEMANTIC_CLOSURE = "no_final_semantic_closure"
    INTERVENTION_OBJECT_PRESENCE_NOT_PERMISSION = (
        "intervention_object_presence_not_permission"
    )
    SOURCE_ACQUISITION_REF_MUST_BE_READ = "source_acquisition_ref_must_be_read"
    SOURCE_FRAMING_REF_MUST_BE_READ = "source_framing_ref_must_be_read"
    SOURCE_DISCOURSE_UPDATE_REF_MUST_BE_READ = "source_discourse_update_ref_must_be_read"
    SOURCE_REF_CLASS_MUST_BE_READ = "source_ref_class_must_be_read"
    L06_OBJECT_PRESENCE_NOT_ACCEPTANCE = "l06_object_presence_not_acceptance"
    INTERVENTION_STATUS_MUST_BE_READ = "intervention_status_must_be_read"
    UNCERTAINTY_TARGET_ID_MUST_BE_READ = "uncertainty_target_id_must_be_read"
    MINIMAL_QUESTION_SPEC_MUST_BE_READ = "minimal_question_spec_must_be_read"
    MINIMAL_QUESTION_SPEC_TARGET_BINDING_MUST_BE_READ = (
        "minimal_question_spec_target_binding_must_be_read"
    )
    FORBIDDEN_PRESUPPOSITIONS_MUST_BE_READ = "forbidden_presuppositions_must_be_read"
    EXPECTED_EVIDENCE_GAIN_MUST_BE_READ = "expected_evidence_gain_must_be_read"
    INTERVENTION_REQUIRES_TARGET_BINDING_READ = (
        "intervention_requires_target_binding_read"
    )
    DOWNSTREAM_LOCKOUTS_MUST_BE_READ = "downstream_lockouts_must_be_read"
    L06_UPSTREAM_BOUND_HERE_MUST_BE_READ = "l06_upstream_bound_here_must_be_read"
    L06_REPAIR_LOCALIZATION_MUST_BE_READ = "l06_repair_localization_must_be_read"
    L06_PROPOSAL_REQUIRES_ACCEPTANCE_READ = "l06_proposal_requires_acceptance_read"
    L06_UPDATE_NOT_ACCEPTED = "l06_update_not_accepted"
    L06_UPDATE_NOT_AUTHORIZED_YET = "l06_update_not_authorized_yet"
    CLARIFICATION_NOT_EQUAL_ACCEPTED_UPDATE = "clarification_not_equal_accepted_update"
    INTERVENTION_NOT_DISCOURSE_ACCEPTANCE = "intervention_not_discourse_acceptance"
    ACCEPTED_INTERVENTION_NOT_ACCEPTED_UPDATE = (
        "accepted_intervention_not_accepted_update"
    )
    L06_BLOCK_OR_GUARD_MUST_BE_READ = "l06_block_or_guard_must_be_read"
    L06_CONTINUATION_TOPOLOGY_PRESENT = "l06_continuation_topology_present"
    L06_G07_TARGET_ALIGNMENT_REQUIRED = "l06_g07_target_alignment_required"
    CLARIFICATION_NOT_EQUAL_REALIZED_QUESTION = (
        "clarification_not_equal_realized_question"
    )
    ASKED_QUESTION_NOT_EQUAL_RESOLVED_UNCERTAINTY = (
        "asked_question_not_equal_resolved_uncertainty"
    )
    ACCEPTED_INTERVENTION_NOT_RESOLUTION = "accepted_intervention_not_resolution"
    ASK_NOW_REQUIRES_ANSWER_BINDING_FOLLOWUP = (
        "ask_now_requires_answer_binding_followup"
    )
    GUARDED_CONTINUE_LIMITS_MUST_BE_READ = "guarded_continue_limits_must_be_read"
    DEFER_UNTIL_NEEDED_MUST_BE_READ = "defer_until_needed_must_be_read"
    ABSTAIN_WITHOUT_QUESTION_MUST_BE_READ = "abstain_without_question_must_be_read"
    CLARIFICATION_NOT_WORTH_COST_MUST_BE_READ = (
        "clarification_not_worth_cost_must_be_read"
    )
    BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY = (
        "blocked_due_to_insufficient_questionability"
    )
    TARGET_DRIFT_RISK_DETECTED = "target_drift_risk_detected"
    FORBIDDEN_PRESUPPOSITIONS_MISSING_OR_UNREADABLE = (
        "forbidden_presuppositions_missing_or_unreadable"
    )
    DOWNSTREAM_LOCKOUTS_MISSING_OR_UNREADABLE = (
        "downstream_lockouts_missing_or_unreadable"
    )
    STATUS_POLICY_ALIGNMENT_BROKEN = "status_policy_alignment_broken"
    ASK_NOW_WITHOUT_ANSWER_BINDING_FORBIDDEN = (
        "ask_now_without_answer_binding_forbidden"
    )
    HIGH_IMPACT_LOCKOUT_GAP_DETECTED = "high_impact_lockout_gap_detected"
    L06_G07_TARGET_DRIFT_DETECTED = "l06_g07_target_drift_detected"
    L06_REPAIR_LOCALIZATION_INCOMPATIBLE = "l06_repair_localization_incompatible"
    L06_REPAIR_BINDING_MISSING_FOR_ASK_NOW = "l06_repair_binding_missing_for_ask_now"
    L06_CONTINUATION_STATUS_UNREADABLE = "l06_continuation_status_unreadable"
    SOURCE_REF_RELABELING_WITHOUT_NOTICE = "source_ref_relabeling_without_notice"
    LINEAGE_IDENTITY_COLLAPSE_RISK = "lineage_identity_collapse_risk"
    ANSWER_BINDING_READY_REQUIRES_TARGETED_REOPEN = (
        "answer_binding_ready_requires_targeted_reopen"
    )
    ANSWER_BINDING_HOOKS_MUST_BE_READ = "answer_binding_hooks_must_be_read"
    ANSWER_BINDING_NOT_READY = "answer_binding_not_ready"
    L06_UPDATE_PROPOSAL_ABSENT = "l06_update_proposal_absent"
    L06_UPSTREAM_NOT_BOUND = "l06_upstream_not_bound"
    REPAIR_TRIGGER_BASIS_INCOMPLETE = "repair_trigger_basis_incomplete"
    RESPONSE_REALIZATION_CONTRACT_ABSENT = "response_realization_contract_absent"
    ANSWER_BINDING_CONSUMER_ABSENT = "answer_binding_consumer_absent"
    NO_USABLE_INTERVENTION_RECORDS = "no_usable_intervention_records"
    INTERVENTION_RECORD_CONTRACT_BROKEN = "intervention_record_contract_broken"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"
    DEGRADED_INTERVENTION_REQUIRES_RESTRICTIONS_READ = (
        "degraded_intervention_requires_restrictions_read"
    )


class G07DecisionBasisCode(StrEnum):
    QUESTIONABILITY_BLOCKED_UNRESOLVED_OWNER_SOURCE_OR_REPAIR_BASIS = (
        "questionability_blocked_by_unresolved_owner_source_or_repair_basis"
    )
    REPAIR_TRIGGER_BASIS_INCOMPLETE = "repair_trigger_basis_incomplete"
    L06_G07_TARGET_ALIGNMENT_REQUIRED = "l06_g07_target_alignment_required"
    L06_REPAIR_LOCALIZATION_INCOMPATIBLE = "l06_repair_localization_incompatible"
    L06_BLOCKED_UPDATE_TOPOLOGY = "l06_blocked_update_topology"
    L06_BLOCK_OR_GUARD_MUST_BE_READ = "l06_block_or_guard_must_be_read"
    CONTEXT_ONLY_UNCERTAINTY_LOW_GAIN = "context_only_uncertainty_low_gain"
    HIGH_VALUE_TARGETED_CLARIFICATION = "high_value_targeted_clarification"
    ASK_NOW_NOT_EQUAL_RESOLUTION = "ask_now_not_equal_resolution"
    LOW_EVIDENCE_GAIN = "low_evidence_gain"
    UNCERTAINTY_PRESERVED_WITH_DEFERRED_TARGETED_INTERVENTION = (
        "uncertainty_preserved_with_deferred_targeted_intervention"
    )
    NONBLOCKING_UNCERTAINTY_GUARDED_CONTINUE = (
        "nonblocking_uncertainty_guarded_continue"
    )
    ABSTAIN_WITHOUT_FORCED_QUESTION = "abstain_without_forced_question"
    L06_GUARDED_CONTINUE_TOPOLOGY = "l06_guarded_continue_topology"
    GUARDED_CONTINUE_NOT_ACCEPTANCE = "guarded_continue_not_acceptance"
    L06_ABSTAIN_UPDATE_WITHHELD_TOPOLOGY = "l06_abstain_update_withheld_topology"
    DEFER_UNTIL_NEEDED_MUST_BE_READ = "defer_until_needed_must_be_read"
    L06_G07_TARGET_DRIFT_DETECTED = "l06_g07_target_drift_detected"
    MISSING_G05_BASIS = "missing_g05_basis"


class G07LockoutCode(StrEnum):
    NARRATIVE_COMMITMENT_FORBIDDEN = "narrative_commitment_forbidden"
    CLOSURE_BLOCKED_UNTIL_ANSWER = "closure_blocked_until_answer"
    MEMORY_UPTAKE_DEFERRED = "memory_uptake_deferred"
    APPRAISAL_CONTEXT_ONLY = "appraisal_context_only"
    PLANNING_FORBIDDEN_ON_CURRENT_FRAME = "planning_forbidden_on_current_frame"
    SAFETY_ESCALATION_NOT_AUTHORIZED_FROM_CURRENT_EVIDENCE = (
        "safety_escalation_not_authorized_from_current_evidence"
    )
    GUARDED_CONTINUE_LIMITS_MUST_BE_READ = "guarded_continue_limits_must_be_read"
    DEFER_UNTIL_NEEDED_MUST_BE_READ = "defer_until_needed_must_be_read"
    ABSTAIN_WITHOUT_QUESTION_MUST_BE_READ = "abstain_without_question_must_be_read"
    QUESTIONABILITY_BLOCKED_REQUIRES_REPAIR_BASIS = (
        "questionability_blocked_requires_repair_basis"
    )
    CLARIFICATION_NOT_WORTH_COST_MUST_BE_READ = (
        "clarification_not_worth_cost_must_be_read"
    )
    ASK_NOW_REQUIRES_ANSWER_BINDING = "ask_now_requires_answer_binding"
    L06_BLOCKED_UPDATE_MUST_BE_READ = "l06_blocked_update_must_be_read"
    L06_GUARDED_CONTINUE_MUST_BE_READ = "l06_guarded_continue_must_be_read"
    L06_ABSTAIN_UPDATE_WITHHELD_MUST_BE_READ = (
        "l06_abstain_update_withheld_must_be_read"
    )


class G07CoverageCode(StrEnum):
    ABSTAIN = "abstain"
    L06_UPDATE_PROPOSAL_ABSENT = "l06_update_proposal_absent"
    L06_REPAIR_CONSUMER_ABSENT = "l06_repair_consumer_absent"
    L06_DOWNSTREAM_UPDATE_ACCEPTOR_ABSENT = "l06_downstream_update_acceptor_absent"
    L06_DISCOURSE_STATE_MUTATION_CONSUMER_ABSENT = (
        "l06_discourse_state_mutation_consumer_absent"
    )
    LEGACY_G01_BYPASS_RISK_PRESENT = "legacy_g01_bypass_risk_present"
    RESPONSE_REALIZATION_CONTRACT_ABSENT = "response_realization_contract_absent"
    ANSWER_BINDING_CONSUMER_ABSENT = "answer_binding_consumer_absent"
    ANSWER_BINDING_NOT_READY = "answer_binding_not_ready"
    ASK_NOW_WITHOUT_ANSWER_BINDING_EXECUTOR = "ask_now_without_answer_binding_executor"
    L06_G07_TARGET_DRIFT_DETECTED = "l06_g07_target_drift_detected"
    L06_REPAIR_LOCALIZATION_INCOMPATIBLE = "l06_repair_localization_incompatible"
    L06_UPDATE_ACCEPTANCE_STATE_UNEXPECTED = "l06_update_acceptance_state_unexpected"
    L06_CONTINUATION_TOPOLOGY_MISSING = "l06_continuation_topology_missing"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


@dataclass(frozen=True, slots=True)
class ClarificationIntent:
    intent_id: str
    target_contrast: str
    allowed_semantic_scope: tuple[str, ...]
    allowed_answer_form: str
    conceptual_stretch_bound: str


@dataclass(frozen=True, slots=True)
class MinimalQuestionSpec:
    spec_id: str
    clarification_intent: ClarificationIntent
    questionability_reason: str
    forbidden_assumptions: tuple[str, ...]
    preferred_answer_forbidden: bool
    realization_contract_marker: str


@dataclass(frozen=True, slots=True)
class ExpectedEvidenceGain:
    gain_score: float
    gain_level: str
    gain_reason: str
    impact_scope: tuple[str, ...]
    worth_cost: bool


@dataclass(frozen=True, slots=True)
class AskPolicy:
    should_ask: bool
    urgency: str
    reason: str


@dataclass(frozen=True, slots=True)
class AbstainPolicy:
    should_abstain: bool
    mode: str
    reason: str


@dataclass(frozen=True, slots=True)
class GuardedContinuePolicy:
    should_continue: bool
    required_limits: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class InterventionDecision:
    selected_status: InterventionStatus
    decision_basis: tuple[str, ...]
    blocking_uncertainty: bool
    questionability_sufficient: bool
    cost_worthwhile: bool


@dataclass(frozen=True, slots=True)
class InterventionRecord:
    intervention_id: str
    source_record_ids: tuple[str, ...]
    uncertainty_target_id: str
    uncertainty_class: UncertaintyClass
    intervention_status: InterventionStatus
    ask_policy: AskPolicy
    abstain_policy: AbstainPolicy
    guarded_continue_policy: GuardedContinuePolicy
    minimal_question_spec: MinimalQuestionSpec
    forbidden_presuppositions: tuple[str, ...]
    expected_evidence_gain: ExpectedEvidenceGain
    downstream_lockouts: tuple[str, ...]
    l06_repair_binding_refs: tuple[str, ...]
    l06_repair_classes: tuple[str, ...]
    l06_continuation_statuses: tuple[str, ...]
    l06_alignment_ok: bool
    reopen_conditions: tuple[str, ...]
    decision: InterventionDecision
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class InterventionBundle:
    source_acquisition_ref: str
    source_acquisition_ref_kind: str
    source_acquisition_lineage_ref: str
    source_framing_ref: str
    source_framing_ref_kind: str
    source_framing_lineage_ref: str
    source_discourse_update_ref: str
    source_discourse_update_ref_kind: str
    source_discourse_update_lineage_ref: str
    source_perspective_chain_ref: str
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_acquisition_ids: tuple[str, ...]
    linked_framing_ids: tuple[str, ...]
    linked_update_proposal_ids: tuple[str, ...]
    linked_repair_ids: tuple[str, ...]
    intervention_records: tuple[InterventionRecord, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    l06_upstream_bound_here: bool
    l06_repair_basis_bound_here: bool
    l06_update_proposal_absent: bool
    l06_repair_localization_must_be_read: bool
    l06_proposal_requires_acceptance_read: bool
    l06_update_not_accepted: bool
    intervention_not_discourse_acceptance: bool
    l06_block_or_guard_must_be_read: bool
    l06_continuation_topology_present: bool
    l06_g07_target_alignment_required: bool
    l06_g07_target_drift_detected: bool
    l06_repair_localization_incompatible: bool
    repair_trigger_basis_incomplete: bool
    response_realization_contract_absent: bool
    answer_binding_consumer_absent: bool
    answer_binding_ready: bool
    answer_binding_hooks: tuple[str, ...]
    intervention_requires_target_binding_read: bool
    downstream_lockouts_must_be_read: bool
    clarification_not_equal_realized_question: bool
    asked_question_not_equal_resolved_uncertainty: bool
    downstream_authority_degraded: bool
    no_final_semantic_closure: bool
    reason: str


@dataclass(frozen=True, slots=True)
class InterventionGateDecision:
    accepted: bool
    usability_class: InterventionUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_intervention_ids: tuple[str, ...]
    rejected_intervention_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class TargetedClarificationTelemetry:
    source_lineage: tuple[str, ...]
    source_acquisition_ref: str
    source_acquisition_ref_kind: str
    source_acquisition_lineage_ref: str
    source_framing_ref: str
    source_framing_ref_kind: str
    source_framing_lineage_ref: str
    source_discourse_update_ref: str
    source_discourse_update_ref_kind: str
    source_discourse_update_lineage_ref: str
    source_perspective_chain_ref: str
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    intervention_record_count: int
    intervention_statuses: tuple[str, ...]
    uncertainty_classes: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    l06_upstream_bound_here: bool
    l06_repair_basis_bound_here: bool
    l06_update_proposal_absent: bool
    l06_repair_localization_must_be_read: bool
    l06_proposal_requires_acceptance_read: bool
    l06_update_not_accepted: bool
    l06_block_or_guard_must_be_read: bool
    l06_continuation_topology_present: bool
    l06_g07_target_drift_detected: bool
    l06_repair_localization_incompatible: bool
    repair_trigger_basis_incomplete: bool
    response_realization_contract_absent: bool
    answer_binding_consumer_absent: bool
    attempted_paths: tuple[str, ...]
    downstream_gate: InterventionGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class TargetedClarificationResult:
    bundle: InterventionBundle
    telemetry: TargetedClarificationTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_semantic_closure: bool
