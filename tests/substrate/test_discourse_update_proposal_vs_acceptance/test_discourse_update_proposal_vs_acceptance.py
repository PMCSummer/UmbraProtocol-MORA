from __future__ import annotations

from substrate.discourse_update import evaluate_discourse_update_downstream_gate
from tests.substrate.l06_testkit import build_l06_context


def test_proposal_presence_does_not_imply_acceptance() -> None:
    result = build_l06_context("you are tired", "l06-proposal-vs-acceptance").discourse_update
    assert result.bundle.update_proposals
    assert all(proposal.acceptance_required for proposal in result.bundle.update_proposals)
    assert all(proposal.acceptance_status.value != "accepted" for proposal in result.bundle.update_proposals)
    assert result.bundle.interpretation_not_equal_accepted_update is True


def test_gate_restrictions_preserve_acceptance_boundary() -> None:
    result = build_l06_context('he said "you are tired?"', "l06-proposal-gate").discourse_update
    gate = evaluate_discourse_update_downstream_gate(result)
    assert "proposal_requires_acceptance" in gate.restrictions
    assert "interpretation_not_equal_accepted_update" in gate.restrictions
    assert "guarded_continue_not_acceptance" in gate.restrictions
    assert "proposal_not_truth" in gate.restrictions
