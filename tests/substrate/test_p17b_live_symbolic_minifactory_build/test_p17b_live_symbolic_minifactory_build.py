from __future__ import annotations

from dataclasses import replace

from substrate.p17b_live_symbolic_minifactory import (
    P17BBlockedReason,
    P17BFactoryNeed,
    P17BRunStatus,
    P17BStepInput,
    P17BStepKind,
    P17BStepStatus,
    adapter_solution_sequence_blocked_fixture,
    blocked_station_fixture,
    build_p17b_factory_need,
    build_p17b_live_run,
    build_p17b_step_spec,
    contactspec_factory_script_blocked_fixture,
    cost_winner_permission_blocked_fixture,
    failed_intermediate_stops_chain_fixture,
    hidden_recipe_blocked_fixture,
    missing_ap01_blocks_step_fixture,
    missing_resource_blocks_chain_fixture,
    noop_not_completion_fixture,
    p17_proof_not_live_execution_fixture,
    provider_hint_truth_blocked_fixture,
    replay_trace_fixture,
    residue_recovery_partial_fixture,
    successful_bounded_chain_fixture,
    unverified_intermediate_blocks_downstream_fixture,
    validate_downstream_requires_verified_intermediate,
    validate_p17b_live_run,
    validate_step_requires_ap01_and_effect,
)


def _run(bundle):
    return bundle.run


def test_p17b_runs_bounded_live_minifactory_chain_through_world0() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert run.final_status is P17BRunStatus.COMPLETED_BOUNDED_FIXTURE
    assert run.world0_run_refs
    assert all(trace.cycle_refs for trace in run.step_traces)


def test_p17b_each_step_requires_ap01_and_world_effect_feedback() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert all(not validate_step_requires_ap01_and_effect(trace) for trace in run.step_traces)


def test_p17b_downstream_step_requires_verified_intermediate() -> None:
    run = _run(unverified_intermediate_blocks_downstream_fixture())
    decision = run.advance_decisions[0]
    issues = validate_downstream_requires_verified_intermediate(run.step_traces[0], decision)
    assert P17BBlockedReason.DOWNSTREAM_WITHOUT_VERIFIED_INTERMEDIATE in issues


def test_p17b_missing_ap01_prevents_backend_execution() -> None:
    run = _run(missing_ap01_blocks_step_fixture())
    assert P17BBlockedReason.MISSING_AP01_REQUEST in run.blocked_reasons
    assert not run.step_traces[0].backend_execution_refs


def test_p17b_failed_intermediate_preserves_residue_and_stops_chain() -> None:
    run = _run(failed_intermediate_stops_chain_fixture())
    assert run.residue_stop_frames
    assert run.residue_refs
    assert run.final_status in {P17BRunStatus.BLOCKED, P17BRunStatus.FAILED}


def test_p17b_missing_resource_blocks_chain() -> None:
    run = _run(missing_resource_blocks_chain_fixture())
    assert P17BBlockedReason.MISSING_PUBLIC_RESOURCE in run.blocked_reasons


def test_p17b_blocked_station_blocks_chain() -> None:
    run = _run(blocked_station_fixture())
    assert P17BBlockedReason.MISSING_STATION_AFFORDANCE in run.blocked_reasons


def test_p17b_expected_effect_is_not_verified_effect() -> None:
    run = _run(unverified_intermediate_blocks_downstream_fixture())
    assert P17BBlockedReason.EXPECTED_EFFECT_NOT_OBSERVED in run.blocked_reasons


def test_p17b_recipe_candidate_not_mature_skill_or_script() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert run.no_mature_skill_claim is True
    assert run.authority_flags.can_mature_recipe is False
    assert run.authority_flags.can_mature_skill is False


def test_p17b_provider_hint_not_recipe_truth_or_action_permission() -> None:
    run = _run(provider_hint_truth_blocked_fixture())
    assert P17BBlockedReason.PROVIDER_HINT_AS_TRUTH_DETECTED in run.blocked_reasons


def test_p17b_cost_winner_not_action_permission() -> None:
    run = _run(cost_winner_permission_blocked_fixture())
    assert P17BBlockedReason.COST_WINNER_AS_PERMISSION_DETECTED in run.blocked_reasons


def test_p17b_contactspec_cannot_encode_factory_script() -> None:
    run = _run(contactspec_factory_script_blocked_fixture())
    assert P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED in run.blocked_reasons


def test_p17b_adapter_cannot_hardcode_solution_sequence() -> None:
    run = _run(adapter_solution_sequence_blocked_fixture())
    assert P17BBlockedReason.ADAPTER_SOLUTION_SEQUENCE_DETECTED in run.blocked_reasons


def test_p17b_hidden_recipe_or_worldstate_rejected() -> None:
    run = _run(hidden_recipe_blocked_fixture())
    assert P17BBlockedReason.HIDDEN_RECIPE_DETECTED in run.blocked_reasons


def test_p17b_scenario_label_cannot_mark_success() -> None:
    base = successful_bounded_chain_fixture().run
    poisoned = build_p17b_live_run(
        run_id="p17b:run:scenario_poison",
        need=base.need,
        step_inputs=tuple(),
        final_target_refs=base.final_target_refs,
        world0_run_refs=base.world0_run_refs,
        source_refs=base.source_refs,
        available_resources=(),
        station_affordances=(),
        metadata={"scenario_label": "eval:golden"},
    )
    assert P17BBlockedReason.SCENARIO_LABEL_DETECTED in poisoned.blocked_reasons
    assert poisoned.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_p17_proof_trace_not_counted_as_live_execution() -> None:
    run = _run(p17_proof_not_live_execution_fixture())
    assert P17BBlockedReason.P17_PROOF_AS_LIVE_EXECUTION_DETECTED in run.blocked_reasons


def test_p17b_trace_contains_need_operation_cost_ap01_effect_verification_residue() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert run.need.pressure_refs
    assert any(trace.micro_operation_refs for trace in run.step_traces)
    assert any(trace.cost_comparison_refs for trace in run.step_traces)
    assert any(trace.ap01_request_refs for trace in run.step_traces)
    assert any(trace.world_effect_feedback_refs for trace in run.step_traces)
    assert run.verification_records
    assert run.residue_refs


def test_p17b_noop_or_blocked_run_not_completion() -> None:
    run = _run(noop_not_completion_fixture())
    assert run.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_no_factory_automation_or_general_autonomy_claim() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert run.no_general_automation_claim is True
    assert run.no_general_autonomy_claim is True
    assert run.authority_flags.can_claim_automation is False
    assert run.authority_flags.can_claim_general_autonomy is False


def test_p17b_replay_trace_preserves_failed_and_blocked_cycles() -> None:
    run = _run(failed_intermediate_stops_chain_fixture())
    assert run.replay_trace_ref
    assert run.step_traces
    assert any(trace.status in {P17BStepStatus.FAILED, P17BStepStatus.BLOCKED, P17BStepStatus.UNRESOLVED} for trace in run.step_traces)


def test_p17b_step_selected_without_public_need_blocked() -> None:
    base = successful_bounded_chain_fixture().run
    need = replace(base.need, pressure_refs=(), public_basis_refs=())
    run = build_p17b_live_run(
        run_id="p17b:run:no_need",
        need=need,
        step_inputs=tuple(),
        final_target_refs=("target:widget",),
        world0_run_refs=(),
        source_refs=("source:test",),
        available_resources=(),
        station_affordances=(),
    )
    assert P17BBlockedReason.MISSING_PUBLIC_NEED in run.blocked_reasons


def test_p17b_station_use_requires_station_affordance_ref() -> None:
    run = _run(blocked_station_fixture())
    assert P17BBlockedReason.MISSING_STATION_AFFORDANCE in run.blocked_reasons


def test_p17b_intermediate_verified_by_config_rejected() -> None:
    run = _run(unverified_intermediate_blocks_downstream_fixture())
    assert P17BBlockedReason.EXPECTED_EFFECT_NOT_OBSERVED in run.blocked_reasons


def test_p17b_backend_worldstate_cannot_verify_intermediate() -> None:
    run = _run(hidden_recipe_blocked_fixture())
    assert P17BBlockedReason.HIDDEN_RECIPE_DETECTED in run.blocked_reasons


def test_p17b_contactspec_selected_action_blocked() -> None:
    run = _run(contactspec_factory_script_blocked_fixture())
    assert P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED in run.blocked_reasons


def test_p17b_world0_cycle_without_subject_tick_not_live() -> None:
    run = _run(missing_ap01_blocks_step_fixture())
    assert run.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_world0_noop_cycle_not_chain_progress() -> None:
    run = _run(noop_not_completion_fixture())
    assert run.final_status in {P17BRunStatus.NOOP, P17BRunStatus.BLOCKED, P17BRunStatus.PARTIAL}


def test_p17b_cost_comparison_trace_preserved_but_non_authoritative() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert any(trace.cost_comparison_refs for trace in run.step_traces)
    assert run.authority_flags.can_treat_cost_winner_as_permission is False


def test_p17b_provider_hint_trace_preserved_but_non_authoritative() -> None:
    run = _run(provider_hint_truth_blocked_fixture())
    assert run.authority_flags.can_treat_provider_hint_as_truth is False


def test_p17b_counters_match_step_trace() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert run.counters.step_count == len(run.step_traces)


def test_p17b_chain_advance_records_missing_intermediate() -> None:
    run = _run(unverified_intermediate_blocks_downstream_fixture())
    assert any(not decision.advance_allowed for decision in run.advance_decisions)


def test_p17b_completion_requires_final_verified_target() -> None:
    run = _run(unverified_intermediate_blocks_downstream_fixture())
    assert run.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_failed_step_cannot_be_erased_from_replay() -> None:
    run = _run(failed_intermediate_stops_chain_fixture())
    assert any(trace.step_id == "step:failed_transform" for trace in run.step_traces)


def test_p17b_no_mature_recipe_skill_value_or_automation_flags() -> None:
    run = _run(successful_bounded_chain_fixture())
    assert run.authority_flags.can_mature_recipe is False
    assert run.authority_flags.can_mature_skill is False
    assert run.authority_flags.can_claim_automation is False


def test_p17b_no_backend_specific_factory_logic_in_policy() -> None:
    run = _run(successful_bounded_chain_fixture())
    issues = validate_p17b_live_run(run)
    assert P17BBlockedReason.BACKEND_WORLDSTATE_DETECTED not in issues


def test_p17b_rejects_fake_or_local_ap01_refs() -> None:
    spec = build_p17b_step_spec(
        step_id="step:fake_ap01",
        step_kind=P17BStepKind.USE_STATION,
        required_input_refs=("resource:ore",),
        required_station_refs=("station:smelter",),
        expected_output_refs=("target:widget",),
        required_micro_operation_kinds=("use_station",),
        allowed_action_surface_refs=("surface:use_station",),
        source_refs=("source:test",),
    )
    step = P17BStepInput(
        step_spec=spec,
        cycle_refs=("cycle:fake",),
        world0_run_ref="run:fake",
        micro_operation_refs=("micro:fake_ap01",),
        cost_comparison_refs=("cost:fake_ap01",),
        ap01_request_refs=("local:ap01",),
        backend_execution_refs=("backend_exec:fake",),
        world_effect_feedback_refs=("world_effect:backend_exec:fake",),
        observed_effect_refs=("target:widget",),
        residue_refs=("residue:fake",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:fake_ap01",
        need=build_p17b_factory_need(
            need_id="need:fake_ap01",
            target_ref="target:widget",
            pressure_refs=("pressure:factory_target",),
            source_refs=("source:test",),
            public_basis_refs=("basis:public:need",),
        ),
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=("run:fake",),
        source_refs=("source:test",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
    )
    assert P17BBlockedReason.INVALID_AP01_LINEAGE in run.blocked_reasons
    assert run.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_rejects_p17b_created_ap01_marker() -> None:
    bundle = successful_bounded_chain_fixture()
    poisoned_step = replace(
        bundle.run.step_specs[0],
        metadata={"p17b_created_ap01": True},
    )
    step = P17BStepInput(
        step_spec=poisoned_step,
        cycle_refs=bundle.run.step_traces[0].cycle_refs,
        world0_run_ref=bundle.run.world0_run_refs[0],
        micro_operation_refs=bundle.run.step_traces[0].micro_operation_refs,
        cost_comparison_refs=bundle.run.step_traces[0].cost_comparison_refs,
        ap01_request_refs=bundle.run.step_traces[0].ap01_request_refs,
        backend_execution_refs=bundle.run.step_traces[0].backend_execution_refs,
        world_effect_feedback_refs=bundle.run.step_traces[0].world_effect_feedback_refs,
        observed_effect_refs=bundle.run.step_traces[0].observed_effect_refs,
        residue_refs=bundle.run.step_traces[0].residue_refs,
        uncertainty_refs=bundle.run.step_traces[0].uncertainty_refs,
    )
    run = build_p17b_live_run(
        run_id="p17b:run:created_ap01",
        need=bundle.run.need,
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=bundle.run.world0_run_refs,
        source_refs=("source:test",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
    )
    assert P17BBlockedReason.INVALID_AP01_LINEAGE in run.blocked_reasons


def test_p17b_rejects_execution_without_world0_cycle_ref() -> None:
    spec = build_p17b_step_spec(
        step_id="step:no_world0_cycle",
        step_kind=P17BStepKind.USE_STATION,
        required_input_refs=("resource:ore",),
        required_station_refs=("station:smelter",),
        expected_output_refs=("target:widget",),
        required_micro_operation_kinds=("use_station",),
        allowed_action_surface_refs=("surface:use_station",),
        source_refs=("source:test",),
    )
    step = P17BStepInput(
        step_spec=spec,
        cycle_refs=(),
        world0_run_ref=None,
        micro_operation_refs=("micro:no_world0",),
        cost_comparison_refs=("cost:no_world0",),
        ap01_request_refs=("ap01:req:fake",),
        backend_execution_refs=("backend_exec:fake",),
        world_effect_feedback_refs=("world_effect:backend_exec:fake",),
        observed_effect_refs=("target:widget",),
        residue_refs=("residue:no_world0",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:no_world0_cycle",
        need=build_p17b_factory_need(
            need_id="need:no_world0",
            target_ref="target:widget",
            pressure_refs=("pressure:factory_target",),
            source_refs=("source:test",),
            public_basis_refs=("basis:public:need",),
        ),
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=(),
        source_refs=("source:test",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
    )
    assert P17BBlockedReason.MISSING_WORLD0_LINEAGE in run.blocked_reasons
    assert run.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_rejects_hidden_goal_or_scenario_need() -> None:
    base = successful_bounded_chain_fixture().run
    hidden_goal_need = P17BFactoryNeed(
        need_id=base.need.need_id,
        target_ref=base.need.target_ref,
        pressure_refs=base.need.pressure_refs,
        source_refs=base.need.source_refs,
        urgency=base.need.urgency,
        public_basis_refs=base.need.public_basis_refs,
        hidden_goal_used=True,
        scenario_label_used=False,
    )
    scenario_need = P17BFactoryNeed(
        need_id=base.need.need_id,
        target_ref=base.need.target_ref,
        pressure_refs=base.need.pressure_refs,
        source_refs=base.need.source_refs,
        urgency=base.need.urgency,
        public_basis_refs=base.need.public_basis_refs,
        hidden_goal_used=False,
        scenario_label_used=True,
    )
    hidden_run = build_p17b_live_run(
        run_id="p17b:run:hidden_goal",
        need=hidden_goal_need,
        step_inputs=tuple(),
        final_target_refs=("target:widget",),
        world0_run_refs=(),
        source_refs=("source:test",),
        available_resources=(),
        station_affordances=(),
    )
    scenario_run = build_p17b_live_run(
        run_id="p17b:run:scenario_need",
        need=scenario_need,
        step_inputs=tuple(),
        final_target_refs=("target:widget",),
        world0_run_refs=(),
        source_refs=("source:test",),
        available_resources=(),
        station_affordances=(),
    )
    assert P17BBlockedReason.MISSING_PUBLIC_NEED in hidden_run.blocked_reasons
    assert P17BBlockedReason.SCENARIO_LABEL_DETECTED in scenario_run.blocked_reasons


def test_p17b_rejects_provider_hint_as_action_permission() -> None:
    bundle = successful_bounded_chain_fixture()
    spec = build_p17b_step_spec(
        step_id="step:provider_permission",
        step_kind=P17BStepKind.USE_STATION,
        required_input_refs=("resource:ore",),
        required_station_refs=("station:smelter",),
        expected_output_refs=("target:widget",),
        required_micro_operation_kinds=("use_station",),
        allowed_action_surface_refs=("surface:use_station",),
        source_refs=("source:test",),
    )
    step = P17BStepInput(
        step_spec=spec,
        cycle_refs=bundle.run.step_traces[0].cycle_refs,
        world0_run_ref=bundle.run.world0_run_refs[0],
        micro_operation_refs=("micro:provider_permission",),
        cost_comparison_refs=("cost:provider_permission",),
        ap01_request_refs=bundle.run.step_traces[0].ap01_request_refs,
        backend_execution_refs=bundle.run.step_traces[0].backend_execution_refs,
        world_effect_feedback_refs=bundle.run.step_traces[0].world_effect_feedback_refs,
        observed_effect_refs=("target:widget",),
        residue_refs=bundle.run.step_traces[0].residue_refs,
        provider_hint_refs=("selected_action:use_station",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:provider_permission",
        need=bundle.run.need,
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=bundle.run.world0_run_refs,
        source_refs=("source:test",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
    )
    assert P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED in run.blocked_reasons


def test_p17b_rejects_solution_sequence_in_nested_metadata() -> None:
    spec = build_p17b_step_spec(
        step_id="step:nested_solution_sequence",
        step_kind=P17BStepKind.USE_STATION,
        required_input_refs=("resource:ore",),
        required_station_refs=("station:smelter",),
        expected_output_refs=("target:widget",),
        required_micro_operation_kinds=("use_station",),
        allowed_action_surface_refs=("surface:use_station",),
        source_refs=("source:test",),
        metadata={"backend": {"plan": {"solution_sequence": ["gather", "smelt", "assemble"]}}},
    )
    step = P17BStepInput(step_spec=spec, micro_operation_refs=("micro:nested",))
    run = build_p17b_live_run(
        run_id="p17b:run:nested_solution_sequence",
        need=build_p17b_factory_need(
            need_id="need:nested",
            target_ref="target:widget",
            pressure_refs=("pressure:factory_target",),
            source_refs=("source:test",),
            public_basis_refs=("basis:public:need",),
        ),
        step_inputs=(step,),
        final_target_refs=("target:widget",),
        world0_run_refs=(),
        source_refs=("source:test",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
    )
    assert P17BBlockedReason.CONTACTSPEC_FACTORY_SCRIPT_DETECTED in run.blocked_reasons


def test_p17b_rejects_station_output_without_effect() -> None:
    bundle = successful_bounded_chain_fixture()
    spec = build_p17b_step_spec(
        step_id="step:station_without_effect",
        step_kind=P17BStepKind.USE_STATION,
        required_input_refs=("resource:ore",),
        required_station_refs=("station:smelter",),
        expected_output_refs=("intermediate:heated_ingot",),
        required_micro_operation_kinds=("use_station",),
        allowed_action_surface_refs=("surface:use_station",),
        source_refs=("source:test",),
    )
    step = P17BStepInput(
        step_spec=spec,
        cycle_refs=bundle.run.step_traces[0].cycle_refs,
        world0_run_ref=bundle.run.world0_run_refs[0],
        micro_operation_refs=("micro:station_without_effect",),
        cost_comparison_refs=("cost:station_without_effect",),
        ap01_request_refs=bundle.run.step_traces[0].ap01_request_refs,
        backend_execution_refs=bundle.run.step_traces[0].backend_execution_refs,
        world_effect_feedback_refs=(),
        observed_effect_refs=("intermediate:heated_ingot",),
        residue_refs=("residue:station_without_effect",),
    )
    run = build_p17b_live_run(
        run_id="p17b:run:station_without_effect",
        need=bundle.run.need,
        step_inputs=(step,),
        final_target_refs=("intermediate:heated_ingot",),
        world0_run_refs=bundle.run.world0_run_refs,
        source_refs=("source:test",),
        available_resources=("resource:ore",),
        station_affordances=("station:smelter",),
    )
    assert P17BBlockedReason.MISSING_WORLD_EFFECT in run.blocked_reasons
    assert run.final_status is not P17BRunStatus.COMPLETED_BOUNDED_FIXTURE


def test_p17b_docs_demo_keep_bounded_claim() -> None:
    doc = open("docs/adr/ADR-P17B-live-symbolic-mini-factory.md", encoding="utf-8").read()
    demo = open("tools/p17b_live_symbolic_minifactory_demo.py", encoding="utf-8").read()
    assert "bounded live symbolic mini-factory fixture chain" in doc
    assert "does not claim general factory automation or autonomy" in demo


def test_p17b_replay_trace_cannot_omit_failed_step() -> None:
    run = _run(failed_intermediate_stops_chain_fixture())
    tampered = replace(run, step_traces=())
    issues = validate_p17b_live_run(tampered)
    assert P17BBlockedReason.TRACE_OMITS_FAILED_STEP in issues


def test_p17b_counters_must_match_step_trace() -> None:
    run = _run(successful_bounded_chain_fixture())
    tampered = replace(run, counters=replace(run.counters, completed_step_count=run.counters.completed_step_count + 1))
    issues = validate_p17b_live_run(tampered)
    assert P17BBlockedReason.COUNTERS_MISMATCH in issues
