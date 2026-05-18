from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.instrumental_value import (
    InstrumentalValueFrame,
    InstrumentalValueRun,
    MeansCandidate,
    ResourceNeedBinding,
    ValueChain,
    ValueReadinessAssessment,
    run_instrumental_value_case,
)
from experiments.embodied_playground.instrumental_value_falsifiers import (
    ab5_support_as_value_oracle,
    ab6_attribution_as_value_oracle,
    ab7_constraint_ignored,
    disconfirmation_ignored,
    evaluate_instrumental_value_falsifiers,
    filter_without_water_problem,
    hidden_eval_value_rule_used,
    instrumental_value_becomes_intrinsic_goal,
    iron_magic_value,
    missing_evidence_erased,
    p14_affordance_ignored_for_value,
    p13_confounder_ignored_for_value,
    p16_overclaims_automation_or_value_learning,
    recipe_candidate_as_automation_value,
    resource_value_without_need,
    scenario_label_value_assignment,
    value_emits_action_request,
    value_executes_world,
    value_without_effect_chain,
    value_without_evidence_refs,
    value_without_resource_refs,
)


def _base_run() -> InstrumentalValueRun:
    return run_instrumental_value_case("resource_with_need_and_recipe_chain")


def test_p16_falsifier_iron_magic_value_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], resource_ref="resource:iron", need_refs=(), value_status="provisional_instrumental")
    run = replace(run, instrumental_value_frames=(frame,))
    assert iron_magic_value(run=run)


def test_p16_falsifier_filter_without_water_problem_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], resource_ref="resource:filter", need_refs=(), effect_refs=(), value_status="weak_instrumental")
    run = replace(run, instrumental_value_frames=(frame,))
    assert filter_without_water_problem(run=run)


def test_p16_falsifier_resource_value_without_need_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], need_refs=(), value_status="provisional_instrumental")
    run = replace(run, instrumental_value_frames=(frame,))
    assert resource_value_without_need(run=run)


def test_p16_falsifier_value_without_effect_chain_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], effect_refs=(), value_status="provisional_instrumental")
    run = replace(run, instrumental_value_frames=(frame,))
    assert value_without_effect_chain(run=run)


def test_p16_falsifier_instrumental_value_becomes_intrinsic_goal_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], intrinsic_value_claimed=True)
    run = replace(run, instrumental_value_frames=(frame,), intrinsic_value_claimed=True)
    assert instrumental_value_becomes_intrinsic_goal(run=run)


def test_p16_falsifier_recipe_candidate_as_automation_value_negative_control() -> None:
    run = _base_run()
    means = replace(run.means_candidates[0], readiness_status="automation_forbidden_in_P16")
    run = replace(run, means_candidates=(means,))
    assert recipe_candidate_as_automation_value(run=run)


def test_p16_falsifier_ab7_constraint_ignored_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], value_status="provisional_instrumental")
    run = replace(run, ab7_constraint_refs=(), instrumental_value_frames=(frame,))
    assert ab7_constraint_ignored(run=run)


def test_p16_falsifier_p13_confounder_ignored_for_value_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], value_status="repeated_trace_supported")
    run = replace(run, confounder_refs=("confounder:c1",), instrumental_value_frames=(frame,))
    assert p13_confounder_ignored_for_value(run=run)


def test_p16_falsifier_p14_affordance_ignored_for_value_negative_control() -> None:
    run = _base_run()
    chain = replace(run.value_chains[0], chain_kind="resource_to_station_input")
    frame = replace(run.instrumental_value_frames[0], value_status="provisional_instrumental")
    run = replace(run, value_chains=(chain,), p14_affordance_refs=(), instrumental_value_frames=(frame,))
    assert p14_affordance_ignored_for_value(run=run)


def test_p16_falsifier_ab5_support_as_value_oracle_negative_control() -> None:
    run = _base_run()
    run = replace(run, effect_chain_refs=("ab5_update:x",))
    assert ab5_support_as_value_oracle(run=run)


def test_p16_falsifier_ab6_attribution_as_value_oracle_negative_control() -> None:
    run = _base_run()
    run = replace(run, effect_chain_refs=("ab6_attribution:x",))
    assert ab6_attribution_as_value_oracle(run=run)


def test_p16_falsifier_hidden_eval_value_rule_used_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], hidden_eval_used=True)
    run = replace(run, instrumental_value_frames=(frame,), hidden_eval_used=True)
    assert hidden_eval_value_rule_used(run=run)


def test_p16_falsifier_scenario_label_value_assignment_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], scenario_label_used=True)
    run = replace(run, instrumental_value_frames=(frame,), scenario_label_used=True)
    assert scenario_label_value_assignment(run=run)


def test_p16_falsifier_value_without_resource_refs_negative_control() -> None:
    run = _base_run()
    run = replace(run, resource_refs=())
    assert value_without_resource_refs(run=run)


def test_p16_falsifier_value_without_evidence_refs_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], evidence_refs=())
    run = replace(run, instrumental_value_frames=(frame,))
    assert value_without_evidence_refs(run=run)


def test_p16_falsifier_missing_evidence_erased_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], missing_evidence=())
    run = replace(run, blocked_reasons=("effect_chain_refs_required",), instrumental_value_frames=(frame,))
    assert missing_evidence_erased(run=run)


def test_p16_falsifier_disconfirmation_ignored_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], value_status="provisional_instrumental")
    run = replace(run, disconfirmation_refs=("trace:bad",), instrumental_value_frames=(frame,))
    assert disconfirmation_ignored(run=run)


def test_p16_falsifier_value_emits_action_request_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], action_request_emitted=True)
    means = replace(run.means_candidates[0], action_request_emitted=True)
    run = replace(run, instrumental_value_frames=(frame,), means_candidates=(means,), action_request_emitted=True)
    assert value_emits_action_request(run=run)


def test_p16_falsifier_value_executes_world_negative_control() -> None:
    run = _base_run()
    frame = replace(run.instrumental_value_frames[0], world_submission_emitted=True)
    means = replace(run.means_candidates[0], world_submission_emitted=True)
    run = replace(run, instrumental_value_frames=(frame,), means_candidates=(means,), world_submission_emitted=True)
    assert value_executes_world(run=run)


def test_p16_falsifier_P16_overclaims_automation_or_value_learning_negative_control() -> None:
    assert p16_overclaims_automation_or_value_learning(
        claim_boundary="This proves intrinsic value learning, mature automation, and consciousness."
    )


def test_p16_falsifier_suite_smoke_negative_control() -> None:
    run = _base_run()
    frame = InstrumentalValueFrame(
        frame_id="bad:frame",
        resource_ref="resource:iron",
        need_refs=(),
        recipe_candidate_refs=(),
        precursor_candidate_refs=(),
        value_chain_refs=("bad:chain",),
        evidence_refs=(),
        effect_refs=(),
        station_affordance_refs=(),
        ab7_constraint_refs=(),
        confounder_refs=("confounder:c1",),
        missing_evidence=(),
        value_status="repeated_trace_supported",
        value_kind="unknown_or_unbound",
        confidence=0.9,
        confidence_policy="evidence_bounded",
        intrinsic_value_claimed=True,
        mature_automation_claimed=True,
        action_request_emitted=True,
        world_submission_emitted=True,
        hidden_eval_used=True,
        scenario_label_used=True,
    )
    chain = ValueChain(
        chain_id="bad:chain",
        chain_kind="resource_to_station_input",
        start_refs=("resource:iron",),
        intermediate_refs=(),
        terminal_refs=(),
        required_refs=(),
        missing_refs=(),
        evidence_refs=(),
        effect_refs=(),
        status="complete_public_chain",
        reason_codes=(),
    )
    means = MeansCandidate(
        means_candidate_id="bad:means",
        resource_ref="resource:iron",
        means_for_refs=(),
        required_context_refs=(),
        blocked_context_refs=(),
        supporting_trace_refs=(),
        disconfirming_trace_refs=(),
        confounder_refs=("confounder:c1",),
        readiness_status="automation_forbidden_in_P16",
        fact_claimed=False,
        action_request_emitted=True,
        world_submission_emitted=True,
    )
    binding = ResourceNeedBinding(
        binding_id="bad:binding",
        resource_ref="resource:iron",
        need_refs=(),
        chain_refs=("bad:chain",),
        status="bound",
        missing_refs=(),
        reason_codes=(),
    )
    readiness = ValueReadinessAssessment(
        value_candidate_count=1,
        weak_value_count=0,
        provisional_value_count=1,
        blocked_value_count=0,
        disconfirmed_value_count=0,
        intrinsic_value_detected=True,
        magic_value_detected=True,
        missing_need_detected=True,
        missing_effect_chain_detected=True,
        automation_claimed=True,
        action_request_emitted=True,
        calibration_score=0.1,
    )
    bad = replace(
        run,
        resource_refs=(),
        instrumental_value_frames=(frame,),
        value_chains=(chain,),
        means_candidates=(means,),
        resource_need_bindings=(binding,),
        ab7_constraint_refs=(),
        p14_affordance_refs=(),
        effect_chain_refs=(),
        confounder_refs=("confounder:c1",),
        disconfirmation_refs=("trace:bad",),
        blocked_reasons=("effect_chain_refs_required",),
        value_readiness_assessment=readiness,
        intrinsic_value_claimed=True,
        mature_automation_claimed=True,
        action_request_emitted=True,
        world_submission_emitted=True,
        hidden_eval_used=True,
        scenario_label_used=True,
    )
    result = evaluate_instrumental_value_falsifiers(run=bad, claim_boundary="intrinsic value learning and consciousness")
    assert result["iron_magic_value"] is True
    assert result["resource_value_without_need"] is True
    assert result["value_without_effect_chain"] is True
    assert result["value_emits_action_request"] is True
    assert result["value_executes_world"] is True
    assert result["P16_overclaims_automation_or_value_learning"] is True
