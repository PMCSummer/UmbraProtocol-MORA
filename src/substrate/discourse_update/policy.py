from __future__ import annotations

from substrate.discourse_update.models import (
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateGateDecision,
    DiscourseUpdateResult,
    DiscourseUpdateUsabilityClass,
)


def evaluate_discourse_update_downstream_gate(
    discourse_update_result_or_bundle: object,
) -> DiscourseUpdateGateDecision:
    if isinstance(discourse_update_result_or_bundle, DiscourseUpdateResult):
        bundle = discourse_update_result_or_bundle.bundle
    elif isinstance(discourse_update_result_or_bundle, DiscourseUpdateBundle):
        bundle = discourse_update_result_or_bundle
    else:
        raise TypeError(
            "discourse update gate requires typed DiscourseUpdateResult/DiscourseUpdateBundle"
        )

    restrictions: list[str] = [
        "l06_object_presence_not_acceptance",
        "object_presence_not_permission",
        "l06_source_modus_ref_must_be_read",
        "l06_source_modus_ref_kind_must_be_read",
        "l06_source_modus_lineage_ref_must_be_read",
        "proposal_requires_acceptance",
        "acceptance_required_must_be_read",
        "accepted_proposal_not_accepted_update",
        "interpretation_not_equal_accepted_update",
        "proposal_effects_not_yet_authorized",
        "proposal_not_truth",
        "proposal_not_self_update",
        "update_record_not_state_mutation",
        "repair_trigger_must_be_localized",
        "repair_localization_must_be_read",
        "generic_clarification_forbidden",
        "blocked_update_must_be_read",
        "guarded_continue_not_acceptance",
        "guarded_continue_requires_limits_read",
        "downstream_must_read_block_or_repair",
        "l06_output_not_dialogue_manager",
        "l06_output_not_planner",
        "l06_output_not_common_ground_mutator",
    ]

    accepted_proposals: list[str] = []
    rejected_proposals: list[str] = []
    has_localization_gap = False
    has_generic_clarification = False
    has_block_gap = False
    has_acceptance_laundering = False
    has_repair_guard_gap = False
    has_proposal_restriction_gap = False
    has_proposal_permission_gap = False
    has_abstain_withheld = False
    has_source_ref_collapse = False

    if bundle.source_modus_ref == bundle.source_modus_lineage_ref:
        has_source_ref_collapse = True
    if bundle.source_modus_ref_kind != "phase_native_derived_ref":
        has_source_ref_collapse = True

    blocked_ids = set(bundle.blocked_update_ids)
    guarded_ids = set(bundle.guarded_update_ids)
    continuation_by_source = {
        state.source_record_id: state for state in bundle.continuation_states
    }
    repair_refs = {
        ref_id
        for trigger in bundle.repair_triggers
        for ref_id in trigger.localized_ref_ids
    }
    repair_ids = {trigger.repair_id for trigger in bundle.repair_triggers}

    for trigger in bundle.repair_triggers:
        if not trigger.localized_ref_ids:
            has_localization_gap = True
        if trigger.localized_trouble_source.lower().strip() in {"generic", "unknown", "clarification"}:
            has_localization_gap = True
        if trigger.suggested_clarification_type.lower().strip() in {
            "generic",
            "can_you_clarify",
            "clarify",
        }:
            has_generic_clarification = True
        if not trigger.suggested_clarification_type.lower().startswith("bounded_"):
            has_generic_clarification = True
        if "generic" in trigger.why_this_is_broken.lower():
            has_generic_clarification = True

    for proposal in bundle.update_proposals:
        source_id = proposal.source_record_ids[0] if proposal.source_record_ids else ""
        source_state = continuation_by_source.get(source_id)
        required_proposal_restrictions = {
            "l06_object_presence_not_acceptance",
            "proposal_requires_acceptance",
            "acceptance_required_must_be_read",
            "accepted_proposal_not_accepted_update",
            "proposal_effects_not_yet_authorized",
            "proposal_not_truth",
            "proposal_not_self_update",
            "update_record_not_state_mutation",
            "interpretation_not_equal_accepted_update",
        }
        if not required_proposal_restrictions.issubset(set(proposal.downstream_restrictions)):
            has_proposal_restriction_gap = True
        acceptance_lawful = (
            proposal.acceptance_required
            and proposal.acceptance_status.value == "not_accepted"
        )
        if not acceptance_lawful:
            has_acceptance_laundering = True

        if source_state is None:
            has_repair_guard_gap = True
            rejected_proposals.append(proposal.proposal_id)
            continue

        blocked_lawful = True
        if source_state.continuation_status is ContinuationStatus.BLOCKED_PENDING_REPAIR:
            blocked_lawful = (
                proposal.proposal_id in blocked_ids
                and bool(source_state.localized_repair_refs)
                and all(ref in repair_ids for ref in source_state.localized_repair_refs)
                and bool(repair_refs)
                and "blocked_update_must_be_read" in proposal.downstream_restrictions
                and proposal.downstream_permissions == ("proposal_withheld_pending_repair",)
            )
            if not blocked_lawful:
                has_block_gap = True

        guarded_lawful = True
        if source_state.continuation_status is ContinuationStatus.GUARDED_CONTINUE:
            guarded_lawful = (
                proposal.proposal_id in guarded_ids
                and source_state.guarded_continue_allowed
                and not source_state.guarded_continue_forbidden
                and "guarded_continue_requires_limits_read" in proposal.downstream_restrictions
                and "guarded_continue_not_acceptance" in proposal.downstream_restrictions
                and proposal.downstream_permissions == ("proposal_guarded_forwardable_if_limits_read",)
            )
            if not guarded_lawful:
                has_repair_guard_gap = True
        if source_state.continuation_status is ContinuationStatus.ABSTAIN_UPDATE_WITHHELD:
            has_abstain_withheld = True
            if (
                proposal.downstream_permissions != ("proposal_withheld_not_forwardable",)
                or "abstain_update_withheld_must_be_read" not in proposal.downstream_restrictions
            ):
                has_proposal_permission_gap = True

        lawful = acceptance_lawful and blocked_lawful and guarded_lawful and not has_proposal_restriction_gap and not has_proposal_permission_gap
        if lawful:
            accepted_proposals.append(proposal.proposal_id)
        else:
            rejected_proposals.append(proposal.proposal_id)

    if has_localization_gap:
        restrictions.append("repair_localization_gap_detected")
    if has_generic_clarification:
        restrictions.append("generic_clarification_detected")
    if has_block_gap:
        restrictions.append("blocked_update_contract_gap_detected")
    if has_acceptance_laundering:
        restrictions.append("acceptance_laundering_detected")
    if has_repair_guard_gap:
        restrictions.append("repair_guard_contract_gap_detected")
    if has_proposal_restriction_gap:
        restrictions.append("proposal_restriction_shape_gap_detected")
    if has_proposal_permission_gap:
        restrictions.append("proposal_permission_shape_gap_detected")
    if has_abstain_withheld:
        restrictions.append("abstain_update_withheld_must_be_read")
    if has_source_ref_collapse:
        restrictions.append("source_ref_relabeling_without_notice")

    if bundle.downstream_update_acceptor_absent:
        restrictions.append("downstream_update_acceptor_absent")
    if bundle.repair_consumer_absent:
        restrictions.append("repair_consumer_absent")
    if bundle.discourse_state_mutation_consumer_absent:
        restrictions.append("discourse_state_mutation_consumer_absent")
    if bundle.legacy_g01_bypass_risk_present:
        restrictions.append("legacy_bypass_risk_present")
        restrictions.append("legacy_bypass_risk_must_be_read")
        restrictions.append("legacy_bypass_forbidden")

    accepted = bool(accepted_proposals)
    if not accepted:
        usability_class = DiscourseUpdateUsabilityClass.BLOCKED
        restrictions.append("no_usable_update_proposals")
        reason = "l06 produced no lawful update proposals for downstream use"
    else:
        usability_class = DiscourseUpdateUsabilityClass.USABLE_BOUNDED
        reason = "typed l06 proposals/repairs emitted with bounded acceptance requirements"

    degraded = (
        bundle.low_coverage_mode
        or bool(bundle.ambiguity_reasons)
        or bundle.downstream_authority_degraded
        or bundle.downstream_update_acceptor_absent
        or bundle.repair_consumer_absent
        or bundle.discourse_state_mutation_consumer_absent
        or bundle.legacy_g01_bypass_risk_present
        or has_localization_gap
        or has_generic_clarification
        or has_block_gap
        or has_acceptance_laundering
        or has_repair_guard_gap
        or has_proposal_restriction_gap
        or has_proposal_permission_gap
        or has_abstain_withheld
        or has_source_ref_collapse
    )
    if degraded:
        restrictions.append("downstream_authority_degraded")
        restrictions.append("degraded_l06_requires_restrictions_read")
    if degraded and accepted:
        usability_class = DiscourseUpdateUsabilityClass.DEGRADED_BOUNDED

    return DiscourseUpdateGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_proposal_ids=tuple(dict.fromkeys(accepted_proposals)),
        rejected_proposal_ids=tuple(dict.fromkeys(rejected_proposals)),
        bundle_ref=bundle.bundle_ref,
    )
