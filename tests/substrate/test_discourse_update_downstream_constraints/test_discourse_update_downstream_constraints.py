from __future__ import annotations

from substrate.discourse_update import (
    derive_discourse_update_contract_view,
    evaluate_discourse_update_downstream_gate,
)
from tests.substrate.l06_testkit import build_l06_context


def test_contract_requires_acceptance_repair_and_block_reads() -> None:
    result = build_l06_context('he said "you are tired?"', "l06-contract").discourse_update
    view = derive_discourse_update_contract_view(result)
    gate = evaluate_discourse_update_downstream_gate(result)

    assert view.requires_acceptance_read is True
    assert view.requires_acceptance_required_marker_read is True
    assert view.requires_repair_read is True
    assert view.requires_block_read is True
    assert view.requires_guard_limits_read is True
    assert view.proposal_requires_acceptance is True
    assert view.interpretation_not_yet_accepted is True
    assert view.accepted_proposal_not_accepted_update is True
    assert view.proposal_effects_not_yet_authorized is True
    assert view.proposal_not_truth is True
    assert view.proposal_not_self_update is True
    assert view.update_record_not_state_mutation is True
    assert view.l06_object_presence_not_acceptance is True
    assert view.generic_clarification_forbidden is True
    assert view.strong_update_permission is False
    assert view.legacy_bypass_risk_must_be_read is True
    assert "l06_object_presence_not_acceptance" in gate.restrictions
    assert "acceptance_required_must_be_read" in gate.restrictions
    assert "accepted_proposal_not_accepted_update" in gate.restrictions
    assert "proposal_effects_not_yet_authorized" in gate.restrictions
    assert "update_record_not_state_mutation" in gate.restrictions
    assert "guarded_continue_requires_limits_read" in gate.restrictions
    assert "object_presence_not_permission" in gate.restrictions
    assert "proposal_requires_acceptance" in gate.restrictions
    assert "interpretation_not_equal_accepted_update" in gate.restrictions
    assert "downstream_must_read_block_or_repair" in gate.restrictions


def test_downstream_authority_is_degraded_without_consumers() -> None:
    result = build_l06_context("you are tired", "l06-contract-degraded").discourse_update
    view = derive_discourse_update_contract_view(result)
    gate = evaluate_discourse_update_downstream_gate(result)
    assert view.downstream_authority_degraded is True
    assert view.legacy_bypass_risk_present is True
    assert "downstream_update_acceptor_absent" in gate.restrictions
    assert "repair_consumer_absent" in gate.restrictions
    assert "discourse_state_mutation_consumer_absent" in gate.restrictions
    assert "legacy_bypass_risk_present" in gate.restrictions
    assert "legacy_bypass_risk_must_be_read" in gate.restrictions
