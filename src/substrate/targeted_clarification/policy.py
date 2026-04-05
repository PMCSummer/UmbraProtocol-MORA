from __future__ import annotations

from substrate.targeted_clarification.models import (
    G07LockoutCode,
    G07RestrictionCode,
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
        G07RestrictionCode.NO_FINAL_SEMANTIC_CLOSURE,
        G07RestrictionCode.INTERVENTION_OBJECT_PRESENCE_NOT_PERMISSION,
        G07RestrictionCode.SOURCE_ACQUISITION_REF_MUST_BE_READ,
        G07RestrictionCode.SOURCE_FRAMING_REF_MUST_BE_READ,
        G07RestrictionCode.SOURCE_DISCOURSE_UPDATE_REF_MUST_BE_READ,
        G07RestrictionCode.SOURCE_REF_CLASS_MUST_BE_READ,
        G07RestrictionCode.L06_OBJECT_PRESENCE_NOT_ACCEPTANCE,
        G07RestrictionCode.INTERVENTION_STATUS_MUST_BE_READ,
        G07RestrictionCode.UNCERTAINTY_TARGET_ID_MUST_BE_READ,
        G07RestrictionCode.MINIMAL_QUESTION_SPEC_MUST_BE_READ,
        G07RestrictionCode.MINIMAL_QUESTION_SPEC_TARGET_BINDING_MUST_BE_READ,
        G07RestrictionCode.FORBIDDEN_PRESUPPOSITIONS_MUST_BE_READ,
        G07RestrictionCode.EXPECTED_EVIDENCE_GAIN_MUST_BE_READ,
        G07RestrictionCode.INTERVENTION_REQUIRES_TARGET_BINDING_READ,
        G07RestrictionCode.DOWNSTREAM_LOCKOUTS_MUST_BE_READ,
        G07RestrictionCode.L06_UPSTREAM_BOUND_HERE_MUST_BE_READ,
        G07RestrictionCode.L06_REPAIR_LOCALIZATION_MUST_BE_READ,
        G07RestrictionCode.L06_PROPOSAL_REQUIRES_ACCEPTANCE_READ,
        G07RestrictionCode.L06_UPDATE_NOT_ACCEPTED,
        G07RestrictionCode.L06_UPDATE_NOT_AUTHORIZED_YET,
        G07RestrictionCode.CLARIFICATION_NOT_EQUAL_ACCEPTED_UPDATE,
        G07RestrictionCode.INTERVENTION_NOT_DISCOURSE_ACCEPTANCE,
        G07RestrictionCode.ACCEPTED_INTERVENTION_NOT_ACCEPTED_UPDATE,
        G07RestrictionCode.L06_BLOCK_OR_GUARD_MUST_BE_READ,
        G07RestrictionCode.L06_CONTINUATION_TOPOLOGY_PRESENT,
        G07RestrictionCode.L06_G07_TARGET_ALIGNMENT_REQUIRED,
        G07RestrictionCode.CLARIFICATION_NOT_EQUAL_REALIZED_QUESTION,
        G07RestrictionCode.ASKED_QUESTION_NOT_EQUAL_RESOLVED_UNCERTAINTY,
        G07RestrictionCode.ACCEPTED_INTERVENTION_NOT_RESOLUTION,
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
    has_l06_alignment_gap = False
    has_l06_repair_binding_gap = False
    has_l06_continuation_gap = False
    has_source_ref_class_gap = False

    if bundle.source_acquisition_ref_kind != "phase_native_derived_ref":
        has_source_ref_class_gap = True
    if bundle.source_framing_ref_kind != "phase_native_derived_ref":
        has_source_ref_class_gap = True
    if bundle.source_discourse_update_ref_kind != "phase_native_derived_ref":
        has_source_ref_class_gap = True
    if bundle.source_acquisition_ref == bundle.source_acquisition_lineage_ref:
        has_source_ref_class_gap = True
    if bundle.source_framing_ref == bundle.source_framing_lineage_ref:
        has_source_ref_class_gap = True
    if bundle.source_discourse_update_ref == bundle.source_discourse_update_lineage_ref:
        has_source_ref_class_gap = True

    for record in bundle.intervention_records:
        status = record.intervention_status
        is_usable = status is not InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY
        scope = set(record.minimal_question_spec.clarification_intent.allowed_semantic_scope)
        target_scope_required = f"uncertainty_target:{record.uncertainty_target_id}"
        class_scope_required = f"uncertainty_class:{record.uncertainty_class.value}"
        target_bound = target_scope_required in scope and class_scope_required in scope
        if not target_bound:
            has_target_drift_risk = True

        l06_alignment_lawful = True
        if bundle.l06_g07_target_alignment_required and not record.l06_alignment_ok:
            l06_alignment_lawful = False
            has_l06_alignment_gap = True

        if (
            bundle.l06_repair_localization_must_be_read
            and status is InterventionStatus.ASK_NOW
            and not record.l06_repair_binding_refs
        ):
            has_l06_repair_binding_gap = True
            l06_alignment_lawful = False

        if bundle.l06_block_or_guard_must_be_read and not record.l06_continuation_statuses:
            has_l06_continuation_gap = True
            l06_alignment_lawful = False

        presuppositions_present = bool(record.forbidden_presuppositions and record.minimal_question_spec.forbidden_assumptions)
        if not presuppositions_present:
            has_missing_presuppositions = True

        lockouts_present = bool(
            record.downstream_lockouts
            and G07LockoutCode.CLOSURE_BLOCKED_UNTIL_ANSWER in record.downstream_lockouts
        )
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
                G07LockoutCode.PLANNING_FORBIDDEN_ON_CURRENT_FRAME
                not in record.downstream_lockouts
                or G07LockoutCode.SAFETY_ESCALATION_NOT_AUTHORIZED_FROM_CURRENT_EVIDENCE
                not in record.downstream_lockouts
            ):
                has_high_impact_lockout_gap = True

        lawful = (
            target_bound
            and l06_alignment_lawful
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
        restrictions.append(G07RestrictionCode.ASK_NOW_REQUIRES_ANSWER_BINDING_FOLLOWUP)
    if has_guarded:
        restrictions.append(G07RestrictionCode.GUARDED_CONTINUE_LIMITS_MUST_BE_READ)
    if has_defer:
        restrictions.append(G07RestrictionCode.DEFER_UNTIL_NEEDED_MUST_BE_READ)
    if has_abstain:
        restrictions.append(G07RestrictionCode.ABSTAIN_WITHOUT_QUESTION_MUST_BE_READ)
    if has_not_worth_cost:
        restrictions.append(
            G07RestrictionCode.CLARIFICATION_NOT_WORTH_COST_MUST_BE_READ
        )
    if has_blocked:
        restrictions.append(
            G07RestrictionCode.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY
        )
    if has_target_drift_risk:
        restrictions.append(G07RestrictionCode.TARGET_DRIFT_RISK_DETECTED)
    if has_missing_presuppositions:
        restrictions.append(
            G07RestrictionCode.FORBIDDEN_PRESUPPOSITIONS_MISSING_OR_UNREADABLE
        )
    if has_missing_lockouts:
        restrictions.append(G07RestrictionCode.DOWNSTREAM_LOCKOUTS_MISSING_OR_UNREADABLE)
    if has_invalid_status_policy_alignment:
        restrictions.append(G07RestrictionCode.STATUS_POLICY_ALIGNMENT_BROKEN)
    if has_unlawful_ask_without_binding:
        restrictions.append(G07RestrictionCode.ASK_NOW_WITHOUT_ANSWER_BINDING_FORBIDDEN)
    if has_high_impact_lockout_gap:
        restrictions.append(G07RestrictionCode.HIGH_IMPACT_LOCKOUT_GAP_DETECTED)
    if has_l06_alignment_gap:
        restrictions.append(G07RestrictionCode.L06_G07_TARGET_DRIFT_DETECTED)
        restrictions.append(G07RestrictionCode.L06_REPAIR_LOCALIZATION_INCOMPATIBLE)
    if has_l06_repair_binding_gap:
        restrictions.append(G07RestrictionCode.L06_REPAIR_BINDING_MISSING_FOR_ASK_NOW)
    if has_l06_continuation_gap:
        restrictions.append(G07RestrictionCode.L06_CONTINUATION_STATUS_UNREADABLE)
    if has_source_ref_class_gap:
        restrictions.append(G07RestrictionCode.SOURCE_REF_RELABELING_WITHOUT_NOTICE)
        restrictions.append(G07RestrictionCode.LINEAGE_IDENTITY_COLLAPSE_RISK)
    if bundle.answer_binding_ready:
        restrictions.append(
            G07RestrictionCode.ANSWER_BINDING_READY_REQUIRES_TARGETED_REOPEN
        )
        restrictions.append(G07RestrictionCode.ANSWER_BINDING_HOOKS_MUST_BE_READ)
    else:
        restrictions.append(G07RestrictionCode.ANSWER_BINDING_NOT_READY)
    if bundle.l06_update_proposal_absent:
        restrictions.append(G07RestrictionCode.L06_UPDATE_PROPOSAL_ABSENT)
    if not bundle.l06_upstream_bound_here:
        restrictions.append(G07RestrictionCode.L06_UPSTREAM_NOT_BOUND)
    if bundle.l06_g07_target_drift_detected:
        restrictions.append(G07RestrictionCode.L06_G07_TARGET_DRIFT_DETECTED)
    if bundle.l06_repair_localization_incompatible:
        restrictions.append(G07RestrictionCode.L06_REPAIR_LOCALIZATION_INCOMPATIBLE)
    if bundle.repair_trigger_basis_incomplete:
        restrictions.append(G07RestrictionCode.REPAIR_TRIGGER_BASIS_INCOMPLETE)
    if bundle.response_realization_contract_absent:
        restrictions.append(G07RestrictionCode.RESPONSE_REALIZATION_CONTRACT_ABSENT)
    if bundle.answer_binding_consumer_absent:
        restrictions.append(G07RestrictionCode.ANSWER_BINDING_CONSUMER_ABSENT)

    accepted = bool(accepted_ids)
    if not accepted:
        usability_class = InterventionUsabilityClass.BLOCKED
        reason = "targeted clarification produced no usable intervention records"
        restrictions.append(G07RestrictionCode.NO_USABLE_INTERVENTION_RECORDS)
        restrictions.append(G07RestrictionCode.INTERVENTION_RECORD_CONTRACT_BROKEN)
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
        or has_l06_alignment_gap
        or has_l06_repair_binding_gap
        or has_l06_continuation_gap
        or has_source_ref_class_gap
        or bundle.l06_g07_target_drift_detected
        or bundle.l06_repair_localization_incompatible
    )
    if degraded:
        restrictions.append(G07RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        restrictions.append(
            G07RestrictionCode.DEGRADED_INTERVENTION_REQUIRES_RESTRICTIONS_READ
        )
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
