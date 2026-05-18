from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.mini_factory_chain import (
    ChainCompletionAssessment,
    ChainResidueRecord,
    FactoryStepTrace,
    IntermediateVerificationRecord,
    MiniFactoryChainRun,
    run_mini_factory_chain_case,
)
from experiments.embodied_playground.mini_factory_falsifiers import (
    AB7_constraint_ignored_in_chain,
    P13_confounder_erased_in_chain,
    P14_affordance_ignored_in_station_step,
    P16_value_as_action_permission,
    P17_overclaims_factory_intelligence,
    chain_emits_action_request_directly,
    chain_emits_unbounded_automation,
    chain_executes_world_directly,
    chain_uses_hidden_transformation_rule,
    clean_water_without_filter_chain,
    completion_without_full_chain,
    disconfirming_trace_ignored_in_chain,
    downstream_step_without_verified_input,
    effect_as_completion_oracle,
    evaluate_mini_factory_falsifiers,
    factory_chain_bypasses_AP01,
    failed_intermediate_erased,
    missing_input_erased,
    recipe_candidate_as_executable_skill,
    request_as_step_success,
    residue_not_propagated_downstream,
    resource_name_implies_intermediate,
    scenario_label_chain_completion,
)


def _base_run() -> MiniFactoryChainRun:
    return run_mini_factory_chain_case("full_chain_verified")


def _replace_step(run: MiniFactoryChainRun, index: int, **kwargs) -> MiniFactoryChainRun:
    steps = list(run.chain_step_traces)
    for i, step in enumerate(steps):
        if step.step_index == index:
            steps[i] = replace(step, **kwargs)
            break
    return replace(run, chain_step_traces=tuple(steps))


def _replace_verification(run: MiniFactoryChainRun, index: int, **kwargs) -> MiniFactoryChainRun:
    records = list(run.intermediate_verification_records)
    target_step = next(step for step in run.chain_step_traces if step.step_index == index)
    for i, rec in enumerate(records):
        if rec.step_id == target_step.step_id:
            records[i] = replace(rec, **kwargs)
            break
    return replace(run, intermediate_verification_records=tuple(records))


def test_p17_falsifier_completion_without_full_chain_negative_control() -> None:
    run = _base_run()
    completion = replace(run.completion_assessment, chain_complete=True, verified_step_count=2, required_step_count=3)
    run = replace(run, completion_assessment=completion)
    assert completion_without_full_chain(run=run)


def test_p17_falsifier_failed_intermediate_erased_negative_control() -> None:
    run = _base_run()
    run = _replace_step(run, 1, step_status="failed", residue_refs=())
    run = replace(run, chain_residue_records=())
    assert failed_intermediate_erased(run=run)


def test_p17_falsifier_downstream_step_without_verified_input_negative_control() -> None:
    run = _base_run()
    run = _replace_step(run, 2, step_status="succeeded")
    run = _replace_verification(run, 1, verification_status="missing")
    assert downstream_step_without_verified_input(run=run)


def test_p17_falsifier_clean_water_without_filter_chain_negative_control() -> None:
    run = _base_run()
    run = _replace_verification(run, 2, verification_status="missing")
    run = _replace_verification(run, 3, verification_status="verified")
    assert clean_water_without_filter_chain(run=run)


def test_p17_falsifier_factory_chain_bypasses_AP01_negative_control() -> None:
    run = _base_run()
    run = _replace_step(run, 1, ap01_request_ref=None, world_effect_ref=None, step_status="succeeded")
    assert factory_chain_bypasses_AP01(run=run)


def test_p17_falsifier_chain_uses_hidden_transformation_rule_negative_control() -> None:
    run = _base_run()
    run = replace(run, hidden_eval_used=True)
    assert chain_uses_hidden_transformation_rule(run=run)


def test_p17_falsifier_scenario_label_chain_completion_negative_control() -> None:
    run = _base_run()
    run = replace(run, scenario_label_used=True)
    assert scenario_label_chain_completion(run=run)


def test_p17_falsifier_resource_name_implies_intermediate_negative_control() -> None:
    run = _base_run()
    run = _replace_verification(run, 1, verification_status="verified", public_evidence_refs=())
    assert resource_name_implies_intermediate(run=run)


def test_p17_falsifier_recipe_candidate_as_executable_skill_negative_control() -> None:
    run = _base_run()
    readiness = replace(run.readiness, automation_forbidden=False)
    run = replace(run, readiness=readiness)
    assert recipe_candidate_as_executable_skill(run=run)


def test_p17_falsifier_AB7_constraint_ignored_in_chain_negative_control() -> None:
    run = _base_run()
    run = replace(run, ab7_constraint_refs=())
    assert AB7_constraint_ignored_in_chain(run=run)


def test_p17_falsifier_P16_value_as_action_permission_negative_control() -> None:
    run = _base_run()
    run = replace(run, value_chain_refs=())
    assert P16_value_as_action_permission(run=run)


def test_p17_falsifier_P14_affordance_ignored_in_station_step_negative_control() -> None:
    run = _base_run()
    run = replace(run, station_affordance_refs=())
    assert P14_affordance_ignored_in_station_step(run=run)


def test_p17_falsifier_P13_confounder_erased_in_chain_negative_control() -> None:
    run = _base_run()
    run = replace(run, recipe_candidate_refs=("confounder:active",), chain_residue_records=())
    assert P13_confounder_erased_in_chain(run=run)


def test_p17_falsifier_disconfirming_trace_ignored_in_chain_negative_control() -> None:
    run = _base_run()
    residue = ChainResidueRecord(
        residue_id="residue:disconfirm",
        step_id=next(item.step_id for item in run.chain_step_traces if item.step_index == 1),
        residue_kind="disconfirmed_step",
        residue_refs=("disconfirming",),
        downstream_blocked_steps=("x",),
        unresolved=True,
    )
    completion = replace(run.completion_assessment, chain_complete=True)
    run = replace(run, chain_residue_records=(residue,), completion_assessment=completion)
    assert disconfirming_trace_ignored_in_chain(run=run)


def test_p17_falsifier_request_as_step_success_negative_control() -> None:
    run = _base_run()
    run = _replace_step(run, 1, ap01_request_ref="ap01_request:x", world_effect_ref=None, step_status="succeeded")
    assert request_as_step_success(run=run)


def test_p17_falsifier_effect_as_completion_oracle_negative_control() -> None:
    run = _base_run()
    completion = replace(run.completion_assessment, chain_complete=True, verified_step_count=1, required_step_count=3)
    run = replace(run, completion_assessment=completion, action_effect_refs=("effect:x",))
    assert effect_as_completion_oracle(run=run)


def test_p17_falsifier_missing_input_erased_negative_control() -> None:
    run = _base_run()
    run = _replace_step(run, 1, step_status="blocked", required_precondition_refs=("resource:ore",), missing_precondition_refs=())
    assert missing_input_erased(run=run)


def test_p17_falsifier_residue_not_propagated_downstream_negative_control() -> None:
    run = _base_run()
    residue = ChainResidueRecord(
        residue_id="residue:no_downstream",
        step_id=next(item.step_id for item in run.chain_step_traces if item.step_index == 1),
        residue_kind="failed_effect",
        residue_refs=("expected_effect_missing",),
        downstream_blocked_steps=(),
        unresolved=True,
    )
    run = replace(run, chain_residue_records=(residue,))
    assert residue_not_propagated_downstream(run=run)


def test_p17_falsifier_chain_emits_unbounded_automation_negative_control() -> None:
    run = _base_run()
    completion = replace(run.completion_assessment, automation_claimed=True, mature_factory_skill_claimed=True)
    run = replace(run, completion_assessment=completion)
    assert chain_emits_unbounded_automation(run=run)


def test_p17_falsifier_chain_emits_action_request_directly_negative_control() -> None:
    run = _base_run()
    run = replace(run, action_request_emitted=True)
    assert chain_emits_action_request_directly(run=run)


def test_p17_falsifier_chain_executes_world_directly_negative_control() -> None:
    run = _base_run()
    run = replace(run, world_submission_emitted=True)
    assert chain_executes_world_directly(run=run)


def test_p17_falsifier_P17_overclaims_factory_intelligence_negative_control() -> None:
    assert P17_overclaims_factory_intelligence(claim_boundary="This proves general automation, minecraft crafting, and consciousness")


def test_p17_falsifier_suite_smoke_negative_control() -> None:
    run = _base_run()
    bad_step = FactoryStepTrace(
        step_id="bad:step",
        step_index=1,
        step_kind="resource_transform",
        input_resource_refs=("resource:ore",),
        output_resource_refs=("resource:plate",),
        station_refs=(),
        recipe_candidate_refs=(),
        value_chain_refs=(),
        ab7_constraint_refs=(),
        required_precondition_refs=("resource:ore",),
        missing_precondition_refs=(),
        ap01_request_ref="ap01_request:bad",
        world_effect_ref=None,
        effect_correlation_status="missing",
        step_status="succeeded",
        residue_refs=(),
        hidden_eval_used=True,
        scenario_label_used=True,
        action_request_emitted_by_p17=True,
        world_submission_emitted_by_p17=True,
    )
    bad_verify = IntermediateVerificationRecord(
        verification_id="verify:bad",
        step_id="bad:step",
        expected_intermediate_refs=("resource:plate",),
        observed_intermediate_refs=("resource:plate",),
        effect_refs=(),
        inventory_delta_refs=(),
        public_evidence_refs=(),
        verification_status="verified",
        missing_evidence=(),
        confidence=0.9,
        confidence_policy="evidence_bounded",
    )
    bad_residue = ChainResidueRecord(
        residue_id="residue:bad",
        step_id="bad:step",
        residue_kind="failed_effect",
        residue_refs=("x",),
        downstream_blocked_steps=(),
        unresolved=True,
    )
    completion = ChainCompletionAssessment(
        chain_complete=True,
        completion_status="complete_verified",
        verified_step_count=1,
        required_step_count=3,
        missing_step_refs=(),
        failed_step_refs=(),
        residue_refs=("residue:bad",),
        completion_claimed=True,
        automation_claimed=True,
        mature_factory_skill_claimed=True,
        action_request_emitted=False,
        world_submission_emitted=False,
    )
    run = replace(
        run,
        chain_step_traces=(bad_step,),
        intermediate_verification_records=(bad_verify,),
        chain_residue_records=(bad_residue,),
        value_chain_refs=(),
        ab7_constraint_refs=(),
        station_affordance_refs=(),
        recipe_candidate_refs=("confounder:active",),
        completion_assessment=completion,
        hidden_eval_used=True,
        scenario_label_used=True,
        action_request_emitted=True,
        world_submission_emitted=True,
    )
    result = evaluate_mini_factory_falsifiers(run=run, claim_boundary="general automation and consciousness")
    assert result["factory_chain_bypasses_AP01"] is True
    assert result["chain_uses_hidden_transformation_rule"] is True
    assert result["scenario_label_chain_completion"] is True
    assert result["chain_emits_action_request_directly"] is True
    assert result["chain_executes_world_directly"] is True
    assert result["P17_overclaims_factory_intelligence"] is True
