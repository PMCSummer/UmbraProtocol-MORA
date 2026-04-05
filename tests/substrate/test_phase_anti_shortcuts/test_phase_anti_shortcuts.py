from __future__ import annotations

from dataclasses import replace

from substrate.discourse_update import (
    derive_discourse_update_contract_view,
    evaluate_discourse_update_downstream_gate,
)
from substrate.grounded_semantic import (
    derive_grounded_downstream_contract,
    evaluate_grounded_semantic_downstream_gate,
)
from substrate.modus_hypotheses import (
    IllocutionKind,
    derive_modus_hypothesis_contract_view,
    evaluate_modus_hypothesis_downstream_gate,
)
from substrate.targeted_clarification import (
    derive_targeted_clarification_contract_view,
    evaluate_targeted_clarification_downstream_gate,
)
from tests.substrate.phase_axis_testkit import build_phase_axis_context


def test_shortcut_likely_force_not_settled_intent_on_heldout_variants() -> None:
    for case_id, text in (
        ("shortcut-force-1", "please confirm alpha status"),
        ("shortcut-force-2", "could you clarify alpha status"),
        ("shortcut-force-3", "alpha status maybe changed"),
    ):
        ctx = build_phase_axis_context(text, case_id)
        gate = evaluate_modus_hypothesis_downstream_gate(ctx.modus)
        contract = derive_modus_hypothesis_contract_view(ctx.modus)
        assert "likely_illocution_not_settled_intent" in gate.restrictions
        assert "accepted_hypothesis_not_settled_intent" in gate.restrictions
        assert contract.multi_hypothesis_present is True
        assert all(
            IllocutionKind.UNKNOWN_FORCE_CANDIDATE
            in {hypothesis.illocution_kind for hypothesis in record.illocution_hypotheses}
            for record in ctx.modus.bundle.hypothesis_records
        )


def test_shortcut_quote_report_force_does_not_become_current_commitment() -> None:
    ctx = build_phase_axis_context('he said "you are tired"', "shortcut-quote-leak")
    l05_contract = derive_modus_hypothesis_contract_view(ctx.modus)
    assert l05_contract.quoted_force_separate_from_current_commitment is True
    report_like = [
        proposal
        for proposal in ctx.discourse_update.bundle.update_proposals
        if proposal.proposal_type.value
        in {"reported_content_update", "quoted_content_update", "echoic_content_update"}
    ]
    assert report_like
    assert all(proposal.commitment_candidate is False for proposal in report_like)


def test_shortcut_interpretation_not_equal_accepted_update_even_when_usable() -> None:
    ctx = build_phase_axis_context("alpha is stable", "shortcut-acceptance")
    gate = evaluate_discourse_update_downstream_gate(ctx.discourse_update)
    contract = derive_discourse_update_contract_view(ctx.discourse_update)
    assert ctx.discourse_update.bundle.update_proposals
    assert all(proposal.acceptance_required for proposal in ctx.discourse_update.bundle.update_proposals)
    assert all(proposal.acceptance_status.value == "not_accepted" for proposal in ctx.discourse_update.bundle.update_proposals)
    assert "interpretation_not_equal_accepted_update" in gate.restrictions
    assert contract.interpretation_not_yet_accepted is True
    assert contract.accepted_proposal_not_accepted_update is True


def test_shortcut_clarification_object_presence_not_permission() -> None:
    ctx = build_phase_axis_context("you are tired?", "shortcut-clarification-permission")
    gate = evaluate_targeted_clarification_downstream_gate(ctx.intervention)
    contract = derive_targeted_clarification_contract_view(ctx.intervention)
    assert ctx.intervention.bundle.intervention_records
    assert "intervention_object_presence_not_permission" in gate.restrictions
    assert contract.intervention_object_presence_not_permission is True
    assert contract.strong_continue_permission is False
    assert contract.intervention_not_discourse_acceptance is True


def test_shortcut_legacy_route_retired_and_normative_route_is_only_runtime_path() -> None:
    ctx = build_phase_axis_context("alpha is stable?", "shortcut-route-contrast")
    normative = derive_grounded_downstream_contract(ctx.grounded_normative)
    assert normative.normative_l05_l06_route_active is True
    assert normative.legacy_surface_cue_fallback_used is False
    assert normative.source_modus_ref_kind_phase_native is True
    assert normative.source_discourse_update_ref_kind_phase_native is True


def test_shortcut_source_lineage_identity_collapse_is_gate_visible() -> None:
    ctx = build_phase_axis_context("alpha is stable", "shortcut-lineage-collapse")
    malformed = replace(
        ctx.grounded_normative.bundle,
        source_modus_ref=ctx.grounded_normative.bundle.source_modus_lineage_ref,
        source_modus_ref_kind="upstream_lineage_ref",
    )
    gate = evaluate_grounded_semantic_downstream_gate(malformed)
    assert "source_ref_relabeling_without_notice" in gate.restrictions
    assert "downstream_authority_degraded" in gate.restrictions

