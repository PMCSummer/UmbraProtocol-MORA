from __future__ import annotations

from substrate.modus_hypotheses import (
    ModusUsabilityClass,
    derive_modus_hypothesis_contract_view,
    evaluate_modus_hypothesis_downstream_gate,
)
from tests.substrate.l05_testkit import build_l05_context


def test_contract_requires_force_addressivity_entropy_read() -> None:
    result = build_l05_context('he said "you are tired"', "l05-contract").modus
    view = derive_modus_hypothesis_contract_view(result)
    gate = evaluate_modus_hypothesis_downstream_gate(result)

    assert view.multi_hypothesis_present is True
    assert view.force_alternatives_present is True
    assert view.modality_evidentiality_profile_present is True
    assert view.addressivity_separate_from_force is True
    assert view.quoted_force_separate_from_current_commitment is True
    assert view.uncertainty_entropy_present is True
    assert view.requires_cautions_read is True
    assert view.strong_intent_resolution_permitted is False
    assert view.discourse_update_permission is False
    assert view.repair_planning_permission is False
    assert view.legacy_l04_g01_shortcut_operational_debt is True
    assert view.legacy_shortcut_bypass_risk is True
    assert "likely_illocution_not_settled_intent" in gate.restrictions
    assert "accepted_hypothesis_not_settled_intent" in gate.restrictions
    assert "quoted_force_not_current_commitment" in gate.restrictions
    assert "downstream_cautions_must_be_read" in gate.restrictions
    assert "legacy_shortcut_bypass_forbidden" in gate.restrictions


def test_record_presence_is_not_full_authority() -> None:
    result = build_l05_context("you are tired", "l05-contract-authority").modus
    gate = evaluate_modus_hypothesis_downstream_gate(result)

    assert gate.accepted is True
    assert gate.usability_class in {ModusUsabilityClass.DEGRADED_BOUNDED, ModusUsabilityClass.BLOCKED}
    assert "downstream_authority_degraded" in gate.restrictions
    assert "l06_downstream_not_bound_here" in gate.restrictions
    assert "l06_update_consumer_not_wired_here" in gate.restrictions
    assert "l06_repair_consumer_not_wired_here" in gate.restrictions
    assert "legacy_l04_g01_shortcut_operational_debt" in gate.restrictions
