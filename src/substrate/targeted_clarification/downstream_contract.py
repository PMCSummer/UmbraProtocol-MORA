from __future__ import annotations

from dataclasses import dataclass

from substrate.targeted_clarification.models import (
    InterventionBundle,
    InterventionStatus,
    InterventionUsabilityClass,
    TargetedClarificationResult,
)
from substrate.targeted_clarification.policy import evaluate_targeted_clarification_downstream_gate


@dataclass(frozen=True, slots=True)
class TargetedClarificationContractView:
    ask_now_present: bool
    abstain_without_question_present: bool
    guarded_continue_with_limits_present: bool
    defer_until_needed_present: bool
    blocked_due_to_insufficient_questionability_present: bool
    clarification_not_worth_cost_present: bool
    closure_blocked_until_answer: bool
    planning_forbidden_on_current_frame: bool
    memory_uptake_deferred: bool
    appraisal_context_only: bool
    narrative_commitment_forbidden: bool
    safety_escalation_not_authorized_from_current_evidence: bool
    usability_class: InterventionUsabilityClass
    restrictions: tuple[str, ...]
    requires_target_binding_read: bool
    requires_lockouts_read: bool
    requires_question_spec_target_binding_read: bool
    requires_forbidden_presuppositions_read: bool
    answer_binding_ready: bool
    answer_binding_hooks_required: bool
    intervention_object_presence_not_permission: bool
    accepted_intervention_not_resolution: bool
    degraded_intervention_requires_restrictions_read: bool
    strong_continue_permission: bool
    reason: str


def derive_targeted_clarification_contract_view(
    targeted_clarification_result_or_bundle: TargetedClarificationResult | InterventionBundle,
) -> TargetedClarificationContractView:
    if isinstance(targeted_clarification_result_or_bundle, TargetedClarificationResult):
        bundle = targeted_clarification_result_or_bundle.bundle
    elif isinstance(targeted_clarification_result_or_bundle, InterventionBundle):
        bundle = targeted_clarification_result_or_bundle
    else:
        raise TypeError(
            "derive_targeted_clarification_contract_view requires TargetedClarificationResult/InterventionBundle"
        )

    gate = evaluate_targeted_clarification_downstream_gate(bundle)
    statuses = [record.intervention_status for record in bundle.intervention_records]
    lockouts = [
        lockout
        for record in bundle.intervention_records
        for lockout in record.downstream_lockouts
    ]

    return TargetedClarificationContractView(
        ask_now_present=InterventionStatus.ASK_NOW in statuses,
        abstain_without_question_present=InterventionStatus.ABSTAIN_WITHOUT_QUESTION in statuses,
        guarded_continue_with_limits_present=InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS in statuses,
        defer_until_needed_present=InterventionStatus.DEFER_UNTIL_NEEDED in statuses,
        blocked_due_to_insufficient_questionability_present=(
            InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in statuses
        ),
        clarification_not_worth_cost_present=InterventionStatus.CLARIFICATION_NOT_WORTH_COST in statuses,
        closure_blocked_until_answer=("closure_blocked_until_answer" in lockouts),
        planning_forbidden_on_current_frame=("planning_forbidden_on_current_frame" in lockouts),
        memory_uptake_deferred=("memory_uptake_deferred" in lockouts),
        appraisal_context_only=("appraisal_context_only" in lockouts),
        narrative_commitment_forbidden=("narrative_commitment_forbidden" in lockouts),
        safety_escalation_not_authorized_from_current_evidence=(
            "safety_escalation_not_authorized_from_current_evidence" in lockouts
        ),
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_target_binding_read=("intervention_requires_target_binding_read" in gate.restrictions),
        requires_lockouts_read=("downstream_lockouts_must_be_read" in gate.restrictions),
        requires_question_spec_target_binding_read=("minimal_question_spec_target_binding_must_be_read" in gate.restrictions),
        requires_forbidden_presuppositions_read=("forbidden_presuppositions_must_be_read" in gate.restrictions),
        answer_binding_ready=bundle.answer_binding_ready,
        answer_binding_hooks_required=("answer_binding_hooks_must_be_read" in gate.restrictions),
        intervention_object_presence_not_permission=("intervention_object_presence_not_permission" in gate.restrictions),
        accepted_intervention_not_resolution=("accepted_intervention_not_resolution" in gate.restrictions),
        degraded_intervention_requires_restrictions_read=(
            "degraded_intervention_requires_restrictions_read" in gate.restrictions
        ),
        strong_continue_permission=False,
        reason="g07 contract view enforces intervention-status and lockout-aware downstream obedience",
    )
