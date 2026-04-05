from __future__ import annotations

from substrate.discourse_update.models import (
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateGateDecision,
    L06ProposalPermissionCode,
    L06ProposalRestrictionCode,
    L06RestrictionCode,
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
        L06RestrictionCode.L06_OBJECT_PRESENCE_NOT_ACCEPTANCE,
        L06RestrictionCode.OBJECT_PRESENCE_NOT_PERMISSION,
        L06RestrictionCode.L06_SOURCE_MODUS_REF_MUST_BE_READ,
        L06RestrictionCode.L06_SOURCE_MODUS_REF_KIND_MUST_BE_READ,
        L06RestrictionCode.L06_SOURCE_MODUS_LINEAGE_REF_MUST_BE_READ,
        L06RestrictionCode.PROPOSAL_REQUIRES_ACCEPTANCE,
        L06RestrictionCode.ACCEPTANCE_REQUIRED_MUST_BE_READ,
        L06RestrictionCode.ACCEPTED_PROPOSAL_NOT_ACCEPTED_UPDATE,
        L06RestrictionCode.INTERPRETATION_NOT_EQUAL_ACCEPTED_UPDATE,
        L06RestrictionCode.PROPOSAL_EFFECTS_NOT_YET_AUTHORIZED,
        L06RestrictionCode.PROPOSAL_NOT_TRUTH,
        L06RestrictionCode.PROPOSAL_NOT_SELF_UPDATE,
        L06RestrictionCode.UPDATE_RECORD_NOT_STATE_MUTATION,
        L06RestrictionCode.REPAIR_TRIGGER_MUST_BE_LOCALIZED,
        L06RestrictionCode.REPAIR_LOCALIZATION_MUST_BE_READ,
        L06RestrictionCode.GENERIC_CLARIFICATION_FORBIDDEN,
        L06RestrictionCode.BLOCKED_UPDATE_MUST_BE_READ,
        L06RestrictionCode.GUARDED_CONTINUE_NOT_ACCEPTANCE,
        L06RestrictionCode.GUARDED_CONTINUE_REQUIRES_LIMITS_READ,
        L06RestrictionCode.DOWNSTREAM_MUST_READ_BLOCK_OR_REPAIR,
        L06RestrictionCode.L06_OUTPUT_NOT_DIALOGUE_MANAGER,
        L06RestrictionCode.L06_OUTPUT_NOT_PLANNER,
        L06RestrictionCode.L06_OUTPUT_NOT_COMMON_GROUND_MUTATOR,
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
            L06ProposalRestrictionCode.L06_OBJECT_PRESENCE_NOT_ACCEPTANCE,
            L06ProposalRestrictionCode.PROPOSAL_REQUIRES_ACCEPTANCE,
            L06ProposalRestrictionCode.ACCEPTANCE_REQUIRED_MUST_BE_READ,
            L06ProposalRestrictionCode.ACCEPTED_PROPOSAL_NOT_ACCEPTED_UPDATE,
            L06ProposalRestrictionCode.PROPOSAL_EFFECTS_NOT_YET_AUTHORIZED,
            L06ProposalRestrictionCode.PROPOSAL_NOT_TRUTH,
            L06ProposalRestrictionCode.PROPOSAL_NOT_SELF_UPDATE,
            L06ProposalRestrictionCode.UPDATE_RECORD_NOT_STATE_MUTATION,
            L06ProposalRestrictionCode.INTERPRETATION_NOT_EQUAL_ACCEPTED_UPDATE,
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
                and L06ProposalRestrictionCode.BLOCKED_UPDATE_MUST_BE_READ
                in proposal.downstream_restrictions
                and proposal.downstream_permissions
                == (L06ProposalPermissionCode.PROPOSAL_WITHHELD_PENDING_REPAIR,)
            )
            if not blocked_lawful:
                has_block_gap = True

        guarded_lawful = True
        if source_state.continuation_status is ContinuationStatus.GUARDED_CONTINUE:
            guarded_lawful = (
                proposal.proposal_id in guarded_ids
                and source_state.guarded_continue_allowed
                and not source_state.guarded_continue_forbidden
                and L06ProposalRestrictionCode.GUARDED_CONTINUE_REQUIRES_LIMITS_READ
                in proposal.downstream_restrictions
                and L06ProposalRestrictionCode.GUARDED_CONTINUE_NOT_ACCEPTANCE
                in proposal.downstream_restrictions
                and proposal.downstream_permissions
                == (
                    L06ProposalPermissionCode.PROPOSAL_GUARDED_FORWARDABLE_IF_LIMITS_READ,
                )
            )
            if not guarded_lawful:
                has_repair_guard_gap = True
        if source_state.continuation_status is ContinuationStatus.ABSTAIN_UPDATE_WITHHELD:
            has_abstain_withheld = True
            if (
                proposal.downstream_permissions
                != (L06ProposalPermissionCode.PROPOSAL_WITHHELD_NOT_FORWARDABLE,)
                or L06ProposalRestrictionCode.ABSTAIN_UPDATE_WITHHELD_MUST_BE_READ
                not in proposal.downstream_restrictions
            ):
                has_proposal_permission_gap = True

        lawful = acceptance_lawful and blocked_lawful and guarded_lawful and not has_proposal_restriction_gap and not has_proposal_permission_gap
        if lawful:
            accepted_proposals.append(proposal.proposal_id)
        else:
            rejected_proposals.append(proposal.proposal_id)

    if has_localization_gap:
        restrictions.append(L06RestrictionCode.REPAIR_LOCALIZATION_GAP_DETECTED)
    if has_generic_clarification:
        restrictions.append(L06RestrictionCode.GENERIC_CLARIFICATION_DETECTED)
    if has_block_gap:
        restrictions.append(L06RestrictionCode.BLOCKED_UPDATE_CONTRACT_GAP_DETECTED)
    if has_acceptance_laundering:
        restrictions.append(L06RestrictionCode.ACCEPTANCE_LAUNDERING_DETECTED)
    if has_repair_guard_gap:
        restrictions.append(L06RestrictionCode.REPAIR_GUARD_CONTRACT_GAP_DETECTED)
    if has_proposal_restriction_gap:
        restrictions.append(L06RestrictionCode.PROPOSAL_RESTRICTION_SHAPE_GAP_DETECTED)
    if has_proposal_permission_gap:
        restrictions.append(L06RestrictionCode.PROPOSAL_PERMISSION_SHAPE_GAP_DETECTED)
    if has_abstain_withheld:
        restrictions.append(L06RestrictionCode.ABSTAIN_UPDATE_WITHHELD_MUST_BE_READ)
    if has_source_ref_collapse:
        restrictions.append(L06RestrictionCode.SOURCE_REF_RELABELING_WITHOUT_NOTICE)

    if bundle.downstream_update_acceptor_absent:
        restrictions.append(L06RestrictionCode.DOWNSTREAM_UPDATE_ACCEPTOR_ABSENT)
    if bundle.repair_consumer_absent:
        restrictions.append(L06RestrictionCode.REPAIR_CONSUMER_ABSENT)
    if bundle.discourse_state_mutation_consumer_absent:
        restrictions.append(
            L06RestrictionCode.DISCOURSE_STATE_MUTATION_CONSUMER_ABSENT
        )
    if bundle.legacy_g01_bypass_risk_present:
        restrictions.append(L06RestrictionCode.LEGACY_BYPASS_RISK_PRESENT)
        restrictions.append(L06RestrictionCode.LEGACY_BYPASS_RISK_MUST_BE_READ)
        restrictions.append(L06RestrictionCode.LEGACY_BYPASS_FORBIDDEN)

    accepted = bool(accepted_proposals)
    if not accepted:
        usability_class = DiscourseUpdateUsabilityClass.BLOCKED
        restrictions.append(L06RestrictionCode.NO_USABLE_UPDATE_PROPOSALS)
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
        restrictions.append(L06RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        restrictions.append(
            L06RestrictionCode.DEGRADED_L06_REQUIRES_RESTRICTIONS_READ
        )
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
