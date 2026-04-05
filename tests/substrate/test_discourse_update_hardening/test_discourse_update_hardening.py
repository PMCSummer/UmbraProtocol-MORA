from __future__ import annotations

from dataclasses import replace

from substrate.discourse_update import (
    derive_discourse_update_contract_view,
    evaluate_discourse_update_downstream_gate,
)
from tests.substrate.l06_testkit import build_l06_context


def test_l06_object_presence_cannot_be_overread_as_acceptance_or_truth() -> None:
    result = build_l06_context("you are tired", "l06-hardening-object").discourse_update
    gate = evaluate_discourse_update_downstream_gate(result)
    view = derive_discourse_update_contract_view(result)

    assert result.bundle.update_proposals
    assert "l06_object_presence_not_acceptance" in gate.restrictions
    assert "accepted_proposal_not_accepted_update" in gate.restrictions
    assert "proposal_not_truth" in gate.restrictions
    assert "proposal_not_self_update" in gate.restrictions
    assert view.strong_update_permission is False


def test_guarded_continue_is_not_near_acceptance() -> None:
    result = build_l06_context('he said "you are tired"', "l06-hardening-guarded").discourse_update
    gate = evaluate_discourse_update_downstream_gate(result)
    assert "guarded_continue_not_acceptance" in gate.restrictions
    assert "guarded_continue_requires_limits_read" in gate.restrictions
    assert "proposal_effects_not_yet_authorized" in gate.restrictions


def test_generic_repair_theater_is_detected_as_contract_violation() -> None:
    ctx = build_l06_context('he said "you are tired?"', "l06-hardening-generic-repair")
    malformed = replace(
        ctx.discourse_update.bundle,
        repair_triggers=tuple(
            replace(
                trigger,
                localized_trouble_source="generic",
                suggested_clarification_type="clarify",
                why_this_is_broken="generic clarification needed",
            )
            for trigger in ctx.discourse_update.bundle.repair_triggers
        ),
    )
    gate = evaluate_discourse_update_downstream_gate(malformed)
    assert "repair_localization_gap_detected" in gate.restrictions
    assert "generic_clarification_detected" in gate.restrictions


def test_ablation_of_acceptance_marker_degrades_legality() -> None:
    ctx = build_l06_context("you are tired", "l06-hardening-ablation-acceptance")
    malformed = replace(
        ctx.discourse_update.bundle,
        update_proposals=tuple(
            replace(
                proposal,
                acceptance_required=False,
            )
            for proposal in ctx.discourse_update.bundle.update_proposals
        ),
    )
    gate = evaluate_discourse_update_downstream_gate(malformed)
    assert gate.accepted is False
    assert "acceptance_laundering_detected" in gate.restrictions
    assert "no_usable_update_proposals" in gate.restrictions


def test_source_ref_collapse_is_detected_as_relabeling_gap() -> None:
    ctx = build_l06_context("you are tired", "l06-hardening-source-collapse")
    malformed = replace(
        ctx.discourse_update.bundle,
        source_modus_ref=ctx.discourse_update.bundle.source_modus_lineage_ref,
        source_modus_ref_kind="upstream_lineage_ref",
    )
    gate = evaluate_discourse_update_downstream_gate(malformed)
    assert "source_ref_relabeling_without_notice" in gate.restrictions
    assert "downstream_authority_degraded" in gate.restrictions
