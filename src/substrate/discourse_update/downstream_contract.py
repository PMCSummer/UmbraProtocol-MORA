from __future__ import annotations

from dataclasses import dataclass

from substrate.discourse_update.models import (
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateResult,
    DiscourseUpdateUsabilityClass,
    L06RestrictionCode,
)
from substrate.discourse_update.policy import evaluate_discourse_update_downstream_gate


@dataclass(frozen=True, slots=True)
class DiscourseUpdateContractView:
    source_modus_ref_present: bool
    source_modus_ref_kind_phase_native: bool
    source_modus_lineage_ref_present: bool
    source_modus_ref_distinct_from_lineage_ref: bool
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
        source_modus_ref_present=bool(bundle.source_modus_ref),
        source_modus_ref_kind_phase_native=(bundle.source_modus_ref_kind == "phase_native_derived_ref"),
        source_modus_lineage_ref_present=bool(bundle.source_modus_lineage_ref),
        source_modus_ref_distinct_from_lineage_ref=(bundle.source_modus_ref != bundle.source_modus_lineage_ref),
        requires_acceptance_read=(
            L06RestrictionCode.PROPOSAL_REQUIRES_ACCEPTANCE in gate.restrictions
        ),
        requires_acceptance_required_marker_read=(
            L06RestrictionCode.ACCEPTANCE_REQUIRED_MUST_BE_READ in gate.restrictions
        ),
        requires_repair_read=(
            L06RestrictionCode.REPAIR_TRIGGER_MUST_BE_LOCALIZED in gate.restrictions
        ),
        requires_block_read=(
            L06RestrictionCode.BLOCKED_UPDATE_MUST_BE_READ in gate.restrictions
        ),
        requires_guard_limits_read=(
            L06RestrictionCode.GUARDED_CONTINUE_REQUIRES_LIMITS_READ
            in gate.restrictions
        ),
        proposal_requires_acceptance=all(proposal.acceptance_required for proposal in bundle.update_proposals) if bundle.update_proposals else True,
        repair_localization_present=repair_localization_present,
        blocked_update_present=ContinuationStatus.BLOCKED_PENDING_REPAIR in continuation_statuses,
        guarded_continue_present=ContinuationStatus.GUARDED_CONTINUE in continuation_statuses,
        abstain_update_withheld_present=ContinuationStatus.ABSTAIN_UPDATE_WITHHELD in continuation_statuses,
        interpretation_not_yet_accepted=(
            L06RestrictionCode.INTERPRETATION_NOT_EQUAL_ACCEPTED_UPDATE
            in gate.restrictions
        ),
        accepted_proposal_not_accepted_update=(
            L06RestrictionCode.ACCEPTED_PROPOSAL_NOT_ACCEPTED_UPDATE
            in gate.restrictions
        ),
        proposal_effects_not_yet_authorized=(
            L06RestrictionCode.PROPOSAL_EFFECTS_NOT_YET_AUTHORIZED
            in gate.restrictions
        ),
        proposal_not_truth=(L06RestrictionCode.PROPOSAL_NOT_TRUTH in gate.restrictions),
        proposal_not_self_update=(
            L06RestrictionCode.PROPOSAL_NOT_SELF_UPDATE in gate.restrictions
        ),
        update_record_not_state_mutation=(
            L06RestrictionCode.UPDATE_RECORD_NOT_STATE_MUTATION in gate.restrictions
        ),
        l06_object_presence_not_acceptance=(
            L06RestrictionCode.L06_OBJECT_PRESENCE_NOT_ACCEPTANCE
            in gate.restrictions
        ),
        generic_clarification_forbidden=(
            L06RestrictionCode.GENERIC_CLARIFICATION_FORBIDDEN in gate.restrictions
        ),
        downstream_authority_degraded=(
            L06RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED in gate.restrictions
        ),
        legacy_bypass_risk_present=(
            L06RestrictionCode.LEGACY_BYPASS_RISK_PRESENT in gate.restrictions
        ),
        legacy_bypass_risk_must_be_read=(
            L06RestrictionCode.LEGACY_BYPASS_RISK_MUST_BE_READ in gate.restrictions
        ),
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        strong_update_permission=False,
        reason="l06 contract view enforces acceptance/repair/block-aware downstream obedience",
    )
