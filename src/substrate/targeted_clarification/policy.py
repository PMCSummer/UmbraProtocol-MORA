from __future__ import annotations

from substrate.targeted_clarification.models import (
    InterventionBundle,
    InterventionGateDecision,
    InterventionStatus,
    InterventionUsabilityClass,
    TargetedClarificationResult,
)


def evaluate_targeted_clarification_downstream_gate(
    targeted_clarification_result_or_bundle: object,
) -> InterventionGateDecision:
    if isinstance(targeted_clarification_result_or_bundle, TargetedClarificationResult):
        bundle = targeted_clarification_result_or_bundle.bundle
    elif isinstance(targeted_clarification_result_or_bundle, InterventionBundle):
        bundle = targeted_clarification_result_or_bundle
    else:
        raise TypeError(
            "targeted clarification gate requires typed TargetedClarificationResult/InterventionBundle"
        )

    restrictions: list[str] = [
        "no_final_semantic_closure",
        "intervention_object_presence_not_permission",
        "intervention_status_must_be_read",
        "uncertainty_target_id_must_be_read",
        "minimal_question_spec_must_be_read",
        "minimal_question_spec_target_binding_must_be_read",
        "forbidden_presuppositions_must_be_read",
        "expected_evidence_gain_must_be_read",
        "intervention_requires_target_binding_read",
        "downstream_lockouts_must_be_read",
        "clarification_not_equal_realized_question",
        "asked_question_not_equal_resolved_uncertainty",
        "accepted_intervention_not_resolution",
    ]

    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    has_blocked = False
    has_ask = False
    has_guarded = False
    has_defer = False
    has_abstain = False
    has_not_worth_cost = False
    has_target_drift_risk = False
    has_missing_presuppositions = False
    has_missing_lockouts = False
    has_invalid_status_policy_alignment = False
    has_unlawful_ask_without_binding = False
    has_high_impact_lockout_gap = False

    for record in bundle.intervention_records:
        status = record.intervention_status
        is_usable = status is not InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY
        scope = set(record.minimal_question_spec.clarification_intent.allowed_semantic_scope)
        target_scope_required = f"uncertainty_target:{record.uncertainty_target_id}"
        class_scope_required = f"uncertainty_class:{record.uncertainty_class.value}"
        target_bound = target_scope_required in scope and class_scope_required in scope
        if not target_bound:
            has_target_drift_risk = True

        presuppositions_present = bool(record.forbidden_presuppositions and record.minimal_question_spec.forbidden_assumptions)
        if not presuppositions_present:
            has_missing_presuppositions = True

        lockouts_present = bool(record.downstream_lockouts and "closure_blocked_until_answer" in record.downstream_lockouts)
        if not lockouts_present:
            has_missing_lockouts = True

        status_policy_aligned = True
        if status is InterventionStatus.ASK_NOW and not record.ask_policy.should_ask:
            status_policy_aligned = False
        if status in {
            InterventionStatus.ABSTAIN_WITHOUT_QUESTION,
            InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
            InterventionStatus.CLARIFICATION_NOT_WORTH_COST,
        } and not record.abstain_policy.should_abstain:
            status_policy_aligned = False
        if status in {
            InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS,
            InterventionStatus.DEFER_UNTIL_NEEDED,
        } and not record.guarded_continue_policy.should_continue:
            status_policy_aligned = False
        if not status_policy_aligned:
            has_invalid_status_policy_alignment = True

        ask_binding_lawful = True
        if status is InterventionStatus.ASK_NOW:
            ask_binding_lawful = (
                bundle.answer_binding_ready
                and bool(bundle.answer_binding_hooks)
                and record.expected_evidence_gain.worth_cost
            )
            if not ask_binding_lawful:
                has_unlawful_ask_without_binding = True

        if record.uncertainty_class.value in {
            "high_impact_binding_risk",
            "frame_competition",
        }:
            if (
                "planning_forbidden_on_current_frame" not in record.downstream_lockouts
                or "safety_escalation_not_authorized_from_current_evidence" not in record.downstream_lockouts
            ):
                has_high_impact_lockout_gap = True

        lawful = (
            target_bound
            and presuppositions_present
            and lockouts_present
            and status_policy_aligned
            and ask_binding_lawful
        )
        if is_usable and record.confidence >= 0.2 and lawful:
            accepted_ids.append(record.intervention_id)
        else:
            rejected_ids.append(record.intervention_id)

        if status is InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY:
            has_blocked = True
        elif status is InterventionStatus.ASK_NOW:
            has_ask = True
        elif status is InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS:
            has_guarded = True
        elif status is InterventionStatus.DEFER_UNTIL_NEEDED:
            has_defer = True
        elif status is InterventionStatus.ABSTAIN_WITHOUT_QUESTION:
            has_abstain = True
        elif status is InterventionStatus.CLARIFICATION_NOT_WORTH_COST:
            has_not_worth_cost = True

    if has_ask:
        restrictions.append("ask_now_requires_answer_binding_followup")
    if has_guarded:
        restrictions.append("guarded_continue_limits_must_be_read")
    if has_defer:
        restrictions.append("defer_until_needed_must_be_read")
    if has_abstain:
        restrictions.append("abstain_without_question_must_be_read")
    if has_not_worth_cost:
        restrictions.append("clarification_not_worth_cost_must_be_read")
    if has_blocked:
        restrictions.append("blocked_due_to_insufficient_questionability")
    if has_target_drift_risk:
        restrictions.append("target_drift_risk_detected")
    if has_missing_presuppositions:
        restrictions.append("forbidden_presuppositions_missing_or_unreadable")
    if has_missing_lockouts:
        restrictions.append("downstream_lockouts_missing_or_unreadable")
    if has_invalid_status_policy_alignment:
        restrictions.append("status_policy_alignment_broken")
    if has_unlawful_ask_without_binding:
        restrictions.append("ask_now_without_answer_binding_forbidden")
    if has_high_impact_lockout_gap:
        restrictions.append("high_impact_lockout_gap_detected")
    if bundle.answer_binding_ready:
        restrictions.append("answer_binding_ready_requires_targeted_reopen")
        restrictions.append("answer_binding_hooks_must_be_read")
    else:
        restrictions.append("answer_binding_not_ready")
    if bundle.l06_update_proposal_absent:
        restrictions.append("l06_update_proposal_absent")
    if bundle.repair_trigger_basis_incomplete:
        restrictions.append("repair_trigger_basis_incomplete")
    if bundle.response_realization_contract_absent:
        restrictions.append("response_realization_contract_absent")
    if bundle.answer_binding_consumer_absent:
        restrictions.append("answer_binding_consumer_absent")

    accepted = bool(accepted_ids)
    if not accepted:
        usability_class = InterventionUsabilityClass.BLOCKED
        reason = "targeted clarification produced no usable intervention records"
        restrictions.append("no_usable_intervention_records")
        restrictions.append("intervention_record_contract_broken")
    else:
        usability_class = InterventionUsabilityClass.USABLE_BOUNDED
        reason = "typed targeted clarification emitted with bounded intervention restrictions"

    degraded = (
        bundle.low_coverage_mode
        or bool(bundle.ambiguity_reasons)
        or bundle.downstream_authority_degraded
        or bundle.l06_update_proposal_absent
        or bundle.repair_trigger_basis_incomplete
        or bundle.response_realization_contract_absent
        or bundle.answer_binding_consumer_absent
        or has_blocked
        or has_abstain
        or has_defer
        or has_not_worth_cost
        or has_target_drift_risk
        or has_missing_presuppositions
        or has_missing_lockouts
        or has_invalid_status_policy_alignment
        or has_unlawful_ask_without_binding
        or has_high_impact_lockout_gap
    )
    if degraded:
        restrictions.append("downstream_authority_degraded")
        restrictions.append("degraded_intervention_requires_restrictions_read")
    if degraded and accepted:
        usability_class = InterventionUsabilityClass.DEGRADED_BOUNDED

    return InterventionGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_intervention_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_intervention_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_framing_ref,
    )
