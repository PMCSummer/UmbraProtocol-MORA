from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.inner_state_calibration import PublicInnerStateReport
from experiments.embodied_playground.inner_state_calibration_falsifiers import (
    ambiguity_forced_closure,
    cause_confirmed_without_public_basis,
    certainty_without_evidence,
    confidence_not_calibrated_to_evidence,
    conflict_erased,
    delayed_effect_reported_immediate,
    evaluate_inner_state_calibration_falsifiers,
    hidden_truth_report_leak,
    missing_evidence_not_reported,
    mixed_cause_erased,
    report_overclaims_cognition,
    report_uses_eval_channel,
    residue_erased,
    scenario_label_report_basis,
    self_overclaim_in_report,
)


def _base_report() -> PublicInnerStateReport:
    return PublicInnerStateReport(
        report_id="p12:test:report",
        source_refs=("effect:1", "ap01:req:1"),
        uncertainty_reported=0.35,
        residue_reported=True,
        conflict_reported=True,
        missing_evidence_reported=("need:extra_obs",),
        confidence_reported=0.55,
        closure_status="open",
        attribution_status="mixed_cause",
        hypothesis_support_summary=("provisional",),
        fact_claimed=False,
        cause_confirmed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
    )


def test_p12_falsifier_certainty_without_evidence_negative_control() -> None:
    report = replace(_base_report(), source_refs=(), confidence_reported=0.9)
    assert certainty_without_evidence(report=report)


def test_p12_falsifier_residue_erased_negative_control() -> None:
    report = replace(_base_report(), residue_reported=False)
    assert residue_erased(report=report, unresolved_expected=True)


def test_p12_falsifier_conflict_erased_negative_control() -> None:
    report = replace(_base_report(), conflict_reported=False)
    assert conflict_erased(report=report, conflict_expected=True)


def test_p12_falsifier_hidden_truth_report_leak_negative_control() -> None:
    assert hidden_truth_report_leak(report_payload_text='{"sealed_hidden_condition":"x"}')


def test_p12_falsifier_scenario_label_report_basis_negative_control() -> None:
    assert scenario_label_report_basis(scenario_label_used=True)


def test_p12_falsifier_cause_confirmed_without_public_basis_negative_control() -> None:
    report = replace(_base_report(), source_refs=(), cause_confirmed=True)
    assert cause_confirmed_without_public_basis(report=report)


def test_p12_falsifier_ambiguity_forced_closure_negative_control() -> None:
    report = replace(_base_report(), closure_status="resolved")
    assert ambiguity_forced_closure(report=report, ambiguity_expected=True)


def test_p12_falsifier_mixed_cause_erased_negative_control() -> None:
    report = replace(_base_report(), attribution_status="self_action", conflict_reported=False)
    assert mixed_cause_erased(mixed_expected=True, report=report)


def test_p12_falsifier_delayed_effect_reported_immediate_negative_control() -> None:
    report = replace(_base_report(), attribution_status="self_action", confidence_reported=0.75)
    assert delayed_effect_reported_immediate(delayed_expected=True, report=report)


def test_p12_falsifier_self_overclaim_in_report_negative_control() -> None:
    report = replace(_base_report(), attribution_status="self_action", confidence_reported=0.7)
    assert self_overclaim_in_report(true_cause_class="world_process", report=report)


def test_p12_falsifier_confidence_not_calibrated_to_evidence_negative_control() -> None:
    report = replace(_base_report(), confidence_reported=0.7)
    assert confidence_not_calibrated_to_evidence(evidence_removed=True, report=report)


def test_p12_falsifier_missing_evidence_not_reported_negative_control() -> None:
    report = replace(_base_report(), missing_evidence_reported=())
    assert missing_evidence_not_reported(missing_required=True, report=report)


def test_p12_falsifier_report_uses_eval_channel_negative_control() -> None:
    assert report_uses_eval_channel(hidden_eval_used=True)


def test_p12_falsifier_report_overclaims_cognition_negative_control() -> None:
    assert report_overclaims_cognition(claim_boundary="This proves consciousness and full causal understanding.")


def test_p12_falsifier_suite_smoke_negative_control() -> None:
    report = replace(
        _base_report(),
        source_refs=(),
        confidence_reported=0.85,
        residue_reported=False,
        conflict_reported=False,
        missing_evidence_reported=(),
        closure_status="resolved",
        attribution_status="self_action",
    )
    falsifiers = evaluate_inner_state_calibration_falsifiers(
        report=report,
        report_payload_text='{"true_cause_class":"hidden"}',
        unresolved_expected=True,
        conflict_expected=True,
        ambiguity_expected=True,
        mixed_expected=True,
        delayed_expected=True,
        true_cause_class="world_process",
        evidence_removed=True,
        missing_required=True,
        hidden_eval_used=True,
        scenario_label_used=True,
        claim_boundary="proves consciousness",
    )
    assert falsifiers["certainty_without_evidence"] is True
    assert falsifiers["residue_erased"] is True
    assert falsifiers["conflict_erased"] is True
