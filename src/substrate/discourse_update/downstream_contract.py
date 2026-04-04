from __future__ import annotations

from dataclasses import dataclass

from substrate.discourse_update.models import (
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateResult,
    DiscourseUpdateUsabilityClass,
)
from substrate.discourse_update.policy import evaluate_discourse_update_downstream_gate


@dataclass(frozen=True, slots=True)
class DiscourseUpdateContractView:
    requires_acceptance_read: bool
    requires_acceptance_required_marker_read: bool
    requires_repair_read: bool
    requires_block_read: bool
    requires_guard_limits_read: bool
    proposal_requires_acceptance: bool
    repair_localization_present: bool
    blocked_update_present: bool
    guarded_continue_present: bool
    abstain_update_withheld_present: bool
    interpretation_not_yet_accepted: bool
    accepted_proposal_not_accepted_update: bool
    proposal_effects_not_yet_authorized: bool
    proposal_not_truth: bool
    proposal_not_self_update: bool
    update_record_not_state_mutation: bool
    l06_object_presence_not_acceptance: bool
    generic_clarification_forbidden: bool
    downstream_authority_degraded: bool
    legacy_bypass_risk_present: bool
    legacy_bypass_risk_must_be_read: bool
    usability_class: DiscourseUpdateUsabilityClass
    restrictions: tuple[str, ...]
    strong_update_permission: bool
    reason: str


def derive_discourse_update_contract_view(
    discourse_update_result_or_bundle: DiscourseUpdateResult | DiscourseUpdateBundle,
) -> DiscourseUpdateContractView:
    if isinstance(discourse_update_result_or_bundle, DiscourseUpdateResult):
        bundle = discourse_update_result_or_bundle.bundle
    elif isinstance(discourse_update_result_or_bundle, DiscourseUpdateBundle):
        bundle = discourse_update_result_or_bundle
    else:
        raise TypeError(
            "derive_discourse_update_contract_view requires DiscourseUpdateResult/DiscourseUpdateBundle"
        )

    gate = evaluate_discourse_update_downstream_gate(bundle)
    continuation_statuses = {state.continuation_status for state in bundle.continuation_states}
    repair_localization_present = all(bool(trigger.localized_ref_ids) for trigger in bundle.repair_triggers) if bundle.repair_triggers else False
    return DiscourseUpdateContractView(
        requires_acceptance_read=("proposal_requires_acceptance" in gate.restrictions),
        requires_acceptance_required_marker_read=("acceptance_required_must_be_read" in gate.restrictions),
        requires_repair_read=("repair_trigger_must_be_localized" in gate.restrictions),
        requires_block_read=("blocked_update_must_be_read" in gate.restrictions),
        requires_guard_limits_read=("guarded_continue_requires_limits_read" in gate.restrictions),
        proposal_requires_acceptance=all(proposal.acceptance_required for proposal in bundle.update_proposals) if bundle.update_proposals else True,
        repair_localization_present=repair_localization_present,
        blocked_update_present=ContinuationStatus.BLOCKED_PENDING_REPAIR in continuation_statuses,
        guarded_continue_present=ContinuationStatus.GUARDED_CONTINUE in continuation_statuses,
        abstain_update_withheld_present=ContinuationStatus.ABSTAIN_UPDATE_WITHHELD in continuation_statuses,
        interpretation_not_yet_accepted=("interpretation_not_equal_accepted_update" in gate.restrictions),
        accepted_proposal_not_accepted_update=("accepted_proposal_not_accepted_update" in gate.restrictions),
        proposal_effects_not_yet_authorized=("proposal_effects_not_yet_authorized" in gate.restrictions),
        proposal_not_truth=("proposal_not_truth" in gate.restrictions),
        proposal_not_self_update=("proposal_not_self_update" in gate.restrictions),
        update_record_not_state_mutation=("update_record_not_state_mutation" in gate.restrictions),
        l06_object_presence_not_acceptance=("l06_object_presence_not_acceptance" in gate.restrictions),
        generic_clarification_forbidden=("generic_clarification_forbidden" in gate.restrictions),
        downstream_authority_degraded=("downstream_authority_degraded" in gate.restrictions),
        legacy_bypass_risk_present=("legacy_bypass_risk_present" in gate.restrictions),
        legacy_bypass_risk_must_be_read=("legacy_bypass_risk_must_be_read" in gate.restrictions),
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        strong_update_permission=False,
        reason="l06 contract view enforces acceptance/repair/block-aware downstream obedience",
    )
