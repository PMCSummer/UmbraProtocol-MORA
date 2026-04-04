from __future__ import annotations

from substrate.discourse_update import ProposalType
from tests.substrate.l06_testkit import build_l06_context


def test_quoted_content_does_not_become_accepted_current_commitment() -> None:
    quoted = build_l06_context('he said "you are tired"', "l06-role-quoted").discourse_update
    direct = build_l06_context("you are tired", "l06-role-direct").discourse_update

    quoted_types = {proposal.proposal_type for proposal in quoted.bundle.update_proposals}
    direct_types = {proposal.proposal_type for proposal in direct.bundle.update_proposals}
    assert ProposalType.QUOTED_CONTENT_UPDATE in quoted_types or ProposalType.REPORTED_CONTENT_UPDATE in quoted_types
    assert ProposalType.QUOTED_CONTENT_UPDATE not in direct_types
    assert all(proposal.acceptance_required for proposal in quoted.bundle.update_proposals)
    assert all(proposal.acceptance_status.value != "accepted" for proposal in quoted.bundle.update_proposals)


def test_addressivity_trouble_routes_to_localized_repairs() -> None:
    result = build_l06_context("this is true", "l06-role-addressivity").discourse_update
    assert result.bundle.repair_triggers
    assert any(
        trigger.repair_class.value in {"reference_repair", "missing_argument_repair", "target_applicability_repair"}
        for trigger in result.bundle.repair_triggers
    )
    assert all(trigger.localized_ref_ids for trigger in result.bundle.repair_triggers)
