from __future__ import annotations

from tests.substrate.l06_testkit import build_l06_context


def test_close_wording_but_different_ambiguity_source_changes_repair_class() -> None:
    reference_case = build_l06_context("this is true", "l06-meta-reference").discourse_update
    polarity_case = build_l06_context("i did not say that", "l06-meta-polarity").discourse_update

    reference_classes = {trigger.repair_class.value for trigger in reference_case.bundle.repair_triggers}
    polarity_classes = {trigger.repair_class.value for trigger in polarity_case.bundle.repair_triggers}
    assert reference_classes != polarity_classes


def test_quote_report_shift_changes_update_repair_topology() -> None:
    quoted = build_l06_context('he said "you are tired"', "l06-meta-quoted").discourse_update
    direct = build_l06_context("you are tired", "l06-meta-direct").discourse_update

    quoted_blocked = set(quoted.bundle.blocked_update_ids)
    direct_blocked = set(direct.bundle.blocked_update_ids)
    quoted_types = {proposal.proposal_type.value for proposal in quoted.bundle.update_proposals}
    direct_types = {proposal.proposal_type.value for proposal in direct.bundle.update_proposals}
    assert quoted_types != direct_types or quoted_blocked != direct_blocked
