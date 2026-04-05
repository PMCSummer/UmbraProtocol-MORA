from __future__ import annotations

from dataclasses import dataclass

from substrate.targeted_clarification.models import (
    G07LockoutCode,
    G07RestrictionCode,
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
    source_acquisition_ref_present: bool
    source_framing_ref_present: bool
    source_discourse_update_ref_present: bool
    source_ref_kind_phase_native: bool
    source_ref_distinct_from_lineage: bool
    requires_source_ref_class_read: bool
    requires_target_binding_read: bool
    requires_lockouts_read: bool
    requires_question_spec_target_binding_read: bool
    requires_forbidden_presuppositions_read: bool
    l06_upstream_bound_here: bool
    l06_repair_localization_must_be_read: bool
    l06_proposal_requires_acceptance_read: bool
    l06_update_not_accepted: bool
    intervention_not_discourse_acceptance: bool
    l06_block_or_guard_must_be_read: bool
    l06_continuation_topology_present: bool
    l06_g07_target_alignment_required: bool
    l06_g07_target_drift_detected: bool
    l06_repair_localization_incompatible: bool
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
        closure_blocked_until_answer=(G07LockoutCode.CLOSURE_BLOCKED_UNTIL_ANSWER in lockouts),
        planning_forbidden_on_current_frame=(
            G07LockoutCode.PLANNING_FORBIDDEN_ON_CURRENT_FRAME in lockouts
        ),
        memory_uptake_deferred=(G07LockoutCode.MEMORY_UPTAKE_DEFERRED in lockouts),
        appraisal_context_only=(G07LockoutCode.APPRAISAL_CONTEXT_ONLY in lockouts),
        narrative_commitment_forbidden=(
            G07LockoutCode.NARRATIVE_COMMITMENT_FORBIDDEN in lockouts
        ),
        safety_escalation_not_authorized_from_current_evidence=(
            G07LockoutCode.SAFETY_ESCALATION_NOT_AUTHORIZED_FROM_CURRENT_EVIDENCE
            in lockouts
        ),
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        source_acquisition_ref_present=bool(bundle.source_acquisition_ref),
        source_framing_ref_present=bool(bundle.source_framing_ref),
        source_discourse_update_ref_present=bool(bundle.source_discourse_update_ref),
        source_ref_kind_phase_native=(
            bundle.source_acquisition_ref_kind == "phase_native_derived_ref"
            and bundle.source_framing_ref_kind == "phase_native_derived_ref"
            and bundle.source_discourse_update_ref_kind == "phase_native_derived_ref"
        ),
        source_ref_distinct_from_lineage=(
            bundle.source_acquisition_ref != bundle.source_acquisition_lineage_ref
            and bundle.source_framing_ref != bundle.source_framing_lineage_ref
            and bundle.source_discourse_update_ref != bundle.source_discourse_update_lineage_ref
        ),
        requires_source_ref_class_read=(
            G07RestrictionCode.SOURCE_REF_CLASS_MUST_BE_READ in gate.restrictions
        ),
        requires_target_binding_read=(
            G07RestrictionCode.INTERVENTION_REQUIRES_TARGET_BINDING_READ
            in gate.restrictions
        ),
        requires_lockouts_read=(
            G07RestrictionCode.DOWNSTREAM_LOCKOUTS_MUST_BE_READ in gate.restrictions
        ),
        requires_question_spec_target_binding_read=(
            G07RestrictionCode.MINIMAL_QUESTION_SPEC_TARGET_BINDING_MUST_BE_READ
            in gate.restrictions
        ),
        requires_forbidden_presuppositions_read=(
            G07RestrictionCode.FORBIDDEN_PRESUPPOSITIONS_MUST_BE_READ
            in gate.restrictions
        ),
        l06_upstream_bound_here=bundle.l06_upstream_bound_here,
        l06_repair_localization_must_be_read=(
            G07RestrictionCode.L06_REPAIR_LOCALIZATION_MUST_BE_READ in gate.restrictions
        ),
        l06_proposal_requires_acceptance_read=(
            G07RestrictionCode.L06_PROPOSAL_REQUIRES_ACCEPTANCE_READ
            in gate.restrictions
        ),
        l06_update_not_accepted=(
            G07RestrictionCode.L06_UPDATE_NOT_ACCEPTED in gate.restrictions
        ),
        intervention_not_discourse_acceptance=(
            G07RestrictionCode.INTERVENTION_NOT_DISCOURSE_ACCEPTANCE
            in gate.restrictions
        ),
        l06_block_or_guard_must_be_read=(
            G07RestrictionCode.L06_BLOCK_OR_GUARD_MUST_BE_READ in gate.restrictions
        ),
        l06_continuation_topology_present=(
            G07RestrictionCode.L06_CONTINUATION_TOPOLOGY_PRESENT in gate.restrictions
        ),
        l06_g07_target_alignment_required=(
            G07RestrictionCode.L06_G07_TARGET_ALIGNMENT_REQUIRED
            in gate.restrictions
        ),
        l06_g07_target_drift_detected=(
            G07RestrictionCode.L06_G07_TARGET_DRIFT_DETECTED in gate.restrictions
        ),
        l06_repair_localization_incompatible=(
            G07RestrictionCode.L06_REPAIR_LOCALIZATION_INCOMPATIBLE
            in gate.restrictions
        ),
        answer_binding_ready=bundle.answer_binding_ready,
        answer_binding_hooks_required=(
            G07RestrictionCode.ANSWER_BINDING_HOOKS_MUST_BE_READ in gate.restrictions
        ),
        intervention_object_presence_not_permission=(
            G07RestrictionCode.INTERVENTION_OBJECT_PRESENCE_NOT_PERMISSION
            in gate.restrictions
        ),
        accepted_intervention_not_resolution=(
            G07RestrictionCode.ACCEPTED_INTERVENTION_NOT_RESOLUTION in gate.restrictions
        ),
        degraded_intervention_requires_restrictions_read=(
            G07RestrictionCode.DEGRADED_INTERVENTION_REQUIRES_RESTRICTIONS_READ
            in gate.restrictions
        ),
        strong_continue_permission=False,
        reason="g07 contract view enforces intervention-status and lockout-aware downstream obedience",
    )
