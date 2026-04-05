from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


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
    source_framing_ref: str
    source_discourse_update_ref: str
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
    source_framing_ref: str
    source_discourse_update_ref: str
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
