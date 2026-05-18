from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.ownership_falsifiers import (
    ap01_request_as_effect,
    attribution_emits_action_request,
    attribution_selects_epistemic_action,
    attribution_updates_hypotheses,
    blocked_action_claimed_success,
    delayed_effect_misattributed_immediate,
    effect_without_correlation_claimed_self,
    evaluate_ownership_falsifiers,
    hidden_truth_attribution,
    other_action_claimed_as_self_action,
    ownership_confidence_without_evidence,
    ownership_overclaim,
    p11_report_overclaims,
    scenario_label_attribution,
    self_action_without_ap01_ref,
    sensor_mismatch_claimed_world_fact,
    unknown_cause_forced_closure,
    world_change_claimed_as_self_action,
    mixed_cause_erased,
)
from experiments.embodied_playground.ownership_perturbation import (
    AttributionCandidate,
    OwnershipAssessment,
)


def _base_assessment() -> OwnershipAssessment:
    candidate = AttributionCandidate(
        attribution_kind="self_action",
        supports=("ap01_request_present", "effect_ref_present"),
        does_not_explain=(),
        required_evidence=("ap01_request_ref", "effect_ref"),
        present_evidence=("ap01:req:1", "effect:1"),
        missing_evidence=(),
        confidence=0.72,
        confidence_policy="evidence_bounded",
        source_refs=("ap01:req:1",),
        effect_refs=("effect:1",),
        ap01_request_refs=("ap01:req:1",),
    )
    return OwnershipAssessment(
        assessment_id="p11:test:assessment",
        observed_effect_refs=("effect:1",),
        candidate_attributions=(candidate,),
        self_cause_status="supported",
        world_cause_status="not_supported",
        other_cause_status="not_supported",
        mixed_cause_status="not_supported",
        unknown_cause_status="not_supported",
        evidence_refs=("ap01:req:1", "effect:1"),
        missing_evidence=(),
        uncertainty=0.2,
        fact_claimed=False,
        cause_confirmed=False,
        self_overclaim=False,
        mixed_cause_preserved=True,
        unknown_preserved=True,
    )


def test_p11_falsifier_ownership_overclaim_negative_control() -> None:
    assert ownership_overclaim(assessment=replace(_base_assessment(), self_overclaim=True))


def test_p11_falsifier_world_change_claimed_as_self_action_negative_control() -> None:
    assert world_change_claimed_as_self_action(
        scenario_id="world_only_object_change",
        assessment=_base_assessment(),
    )


def test_p11_falsifier_other_action_claimed_as_self_action_negative_control() -> None:
    assert other_action_claimed_as_self_action(
        scenario_id="other_actor_object_change",
        assessment=_base_assessment(),
    )


def test_p11_falsifier_mixed_cause_erased_negative_control() -> None:
    assessment = replace(_base_assessment(), mixed_cause_status="not_supported")
    assert mixed_cause_erased(mixed_marker=True, assessment=assessment)


def test_p11_falsifier_unknown_cause_forced_closure_negative_control() -> None:
    assessment = replace(_base_assessment(), unknown_cause_status="not_supported")
    assert unknown_cause_forced_closure(
        scenario_id="unknown_unexplained_effect",
        assessment=assessment,
    )


def test_p11_falsifier_delayed_effect_misattributed_immediate_negative_control() -> None:
    assert delayed_effect_misattributed_immediate(
        delayed_marker=True,
        assessment=_base_assessment(),
    )


def test_p11_falsifier_self_action_without_ap01_ref_negative_control() -> None:
    assert self_action_without_ap01_ref(
        assessment=_base_assessment(),
        ap01_request_refs=(),
    )


def test_p11_falsifier_ap01_request_as_effect_negative_control() -> None:
    assert ap01_request_as_effect(
        ap01_request_refs=("ap01:req:1",),
        effect_refs=(),
        successful_delta=True,
    )


def test_p11_falsifier_effect_without_correlation_claimed_self_negative_control() -> None:
    assert effect_without_correlation_claimed_self(
        assessment=_base_assessment(),
        effect_correlated=False,
    )


def test_p11_falsifier_blocked_action_claimed_success_negative_control() -> None:
    assert blocked_action_claimed_success(blocked_action=True, successful_delta=True)


def test_p11_falsifier_hidden_truth_attribution_negative_control() -> None:
    assert hidden_truth_attribution(hidden_eval_used=True)


def test_p11_falsifier_scenario_label_attribution_negative_control() -> None:
    assert scenario_label_attribution(scenario_label_used=True)


def test_p11_falsifier_sensor_mismatch_claimed_world_fact_negative_control() -> None:
    assessment = replace(_base_assessment(), world_cause_status="supported")
    assert sensor_mismatch_claimed_world_fact(
        scenario_id="sensor_or_projection_mismatch",
        assessment=assessment,
    )


def test_p11_falsifier_ownership_confidence_without_evidence_negative_control() -> None:
    assessment = replace(_base_assessment(), evidence_refs=())
    assert ownership_confidence_without_evidence(assessment=assessment)


def test_p11_falsifier_attribution_emits_action_request_negative_control() -> None:
    assert attribution_emits_action_request(action_request_emitted=True)


def test_p11_falsifier_attribution_updates_hypotheses_negative_control() -> None:
    assert attribution_updates_hypotheses(hypothesis_updated=True)


def test_p11_falsifier_attribution_selects_epistemic_action_negative_control() -> None:
    assert attribution_selects_epistemic_action(epistemic_action_selected=True)


def test_p11_falsifier_p11_report_overclaims_negative_control() -> None:
    assert p11_report_overclaims(claim_boundary="This proves consciousness and full self-model.")


def test_p11_evaluate_ownership_falsifier_suite_smoke_negative_control() -> None:
    assessment = replace(_base_assessment(), self_overclaim=True)
    result = evaluate_ownership_falsifiers(
        scenario_id="world_only_object_change",
        perturbation_kind="external_world_change",
        assessment=assessment,
        ap01_request_refs=(),
        effect_refs=("effect:external",),
        external_event_refs=("external:world_process:object_change",),
        hidden_eval_used=False,
        scenario_label_used=False,
        mixed_marker=False,
        delayed_marker=False,
        blocked_action=False,
        successful_delta=True,
        effect_correlated=False,
        action_request_emitted=False,
        hypothesis_updated=False,
        epistemic_action_selected=False,
        claim_boundary="P11 battery only.",
    )
    assert result["ownership_overclaim"] is True
    assert result["world_change_claimed_as_self_action"] is True
