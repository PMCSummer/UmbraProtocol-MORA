from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import substrate.world0_generic_runner.policy as world0_policy
from substrate.world0_generic_runner import (
    WorldRunnerBlockReason,
    WorldRunnerCycleInput,
    WorldRunnerCycleStatus,
    WorldRunnerExecutionStatus,
    adapter_action_selection_blocked_fixture,
    ap01_execution_fixture,
    backend_worldstate_blocked_fixture,
    blocked_contact_fixture,
    contactspec_plan_blocked_fixture,
    effect_without_correlation_blocked_fixture,
    factory_solution_blocked_fixture,
    failed_backend_execution_fixture,
    no_ap01_no_execution_fixture,
    noop_world_fixture,
    passive_event_fixture,
    replay_trace_fixture,
    run_world_cycle,
    run_world_loop,
    scenario_label_blocked_fixture,
    timeout_max_tick_fixture,
    two_backend_grid_fixture,
    two_backend_inventory_fixture,
)
from substrate.umwelts_symbolic_contact import ContactSpec


def _cycle(bundle):
    cycle = bundle.loop_input.cycle_inputs[0]
    return run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)


def test_world0_runs_noop_cycle_without_ap01_request() -> None:
    bundle = noop_world_fixture()
    result = _cycle(bundle)
    assert result.execution_status is WorldRunnerExecutionStatus.SKIPPED_NO_AP01
    assert result.cycle_status is WorldRunnerCycleStatus.NOOP
    assert not result.backend_results


def test_world0_executes_backend_only_with_ap01_envelope() -> None:
    ok = _cycle(ap01_execution_fixture())
    no = _cycle(no_ap01_no_execution_fixture())
    assert ok.execution_status is WorldRunnerExecutionStatus.EXECUTED_FROM_AP01
    assert ok.backend_results
    assert no.execution_status is WorldRunnerExecutionStatus.SKIPPED_NO_AP01
    assert not no.backend_results


def test_world0_never_creates_ap01_request() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], runner_created_ap01_refs=("ap01:req:runner_generated",))
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.RUNNER_AP01_CREATION_ATTEMPT in result.blocked_reasons


def test_world0_rejects_fake_ap01_ref_execution() -> None:
    bundle = noop_world_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    forged = ap01_execution_fixture().loop_input.cycle_inputs[0].external_ap01_result.published_requests[0]
    injected = replace(cycle, external_ap01_requests=(forged,))
    result = run_world_cycle(injected, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.RUNNER_AP01_CREATION_ATTEMPT in result.blocked_reasons
    assert not result.backend_results


def test_world0_contact_projection_not_worldstate() -> None:
    result = _cycle(backend_worldstate_blocked_fixture())
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in result.blocked_reasons
    assert not result.projection_result


def test_world0_blocked_contact_blocks_execution() -> None:
    result = _cycle(blocked_contact_fixture())
    assert WorldRunnerBlockReason.CONTACT_BLOCKED in result.blocked_reasons
    assert not result.backend_results


def test_world0_effect_frame_correlates_to_request_ref() -> None:
    result = _cycle(ap01_execution_fixture())
    assert result.effect_feedback
    assert result.effect_feedback[0].request_ref == "ap01:req:cycle:ap01"


def test_world0_passive_event_feedback_not_cause_proof() -> None:
    result = _cycle(passive_event_fixture())
    assert result.execution_status is WorldRunnerExecutionStatus.PASSIVE_EVENT_ONLY
    assert result.authority_flags.can_confirm_cause is False


def test_world0_failed_backend_execution_preserves_residue() -> None:
    result = _cycle(failed_backend_execution_fixture())
    assert result.backend_results[0].failed is True
    assert result.residue_refs


def test_world0_runner_trace_contains_contact_tick_ap01_effect_refs() -> None:
    result = _cycle(ap01_execution_fixture())
    trace = result.cycle_trace
    assert trace.contact_frame_refs
    assert trace.projection_refs
    assert trace.subject_tick_ref is not None
    assert trace.ap01_request_refs
    assert trace.world_effect_frame_refs


def test_world0_adapter_cannot_select_action() -> None:
    result = _cycle(adapter_action_selection_blocked_fixture())
    assert WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in result.blocked_reasons


def test_world0_rejects_adapter_selected_action_in_metadata() -> None:
    bundle = noop_world_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    bad_spec = replace(cycle.adapter_spec, metadata={"selected_action": "inspect"})
    result = run_world_cycle(replace(cycle, adapter_spec=bad_spec), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in result.blocked_reasons


def test_world0_contactspec_not_interpreted_as_plan() -> None:
    result = _cycle(contactspec_plan_blocked_fixture())
    assert WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED in result.blocked_reasons


def test_world0_rejects_contactspec_recipe_oracle_metadata() -> None:
    bundle = contactspec_plan_blocked_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    bad_spec: ContactSpec = replace(cycle.contact_spec, metadata={"recipe_oracle": "true_recipe_table"})  # type: ignore[arg-type]
    result = run_world_cycle(replace(cycle, contact_spec=bad_spec), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.INVALID_CONTACT_SPEC in result.blocked_reasons


def test_world0_rejects_contactspec_route_truth_metadata() -> None:
    bundle = contactspec_plan_blocked_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    bad_spec: ContactSpec = replace(cycle.contact_spec, metadata={"route_plan": "best_route"})  # type: ignore[arg-type]
    result = run_world_cycle(replace(cycle, contact_spec=bad_spec), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.CONTACT_SPEC_PLAN_DETECTED in result.blocked_reasons


def test_world0_no_factory_hardcoded_solution() -> None:
    result = _cycle(factory_solution_blocked_fixture())
    assert WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED in result.blocked_reasons


def test_world0_no_backend_specific_logic_in_subject_path() -> None:
    result = _cycle(backend_worldstate_blocked_fixture())
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in result.blocked_reasons


def test_world0_two_symbolic_backends_same_runner() -> None:
    grid = _cycle(two_backend_grid_fixture())
    inv = _cycle(two_backend_inventory_fixture())
    assert grid.cycle_trace.adapter_ref != inv.cycle_trace.adapter_ref
    assert grid.execution_status is WorldRunnerExecutionStatus.SKIPPED_NO_AP01
    assert inv.execution_status is WorldRunnerExecutionStatus.SKIPPED_NO_AP01


def test_world0_scenario_label_does_not_drive_cycle() -> None:
    result = _cycle(scenario_label_blocked_fixture())
    assert WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED in result.blocked_reasons


def test_world0_no_worldstate_to_subject_tick() -> None:
    result = _cycle(backend_worldstate_blocked_fixture())
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in result.blocked_reasons
    assert result.subject_tick_result is None


def test_world0_rejects_backend_worldstate_nested_metadata() -> None:
    bundle = noop_world_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    nested_obs = replace(cycle.observation_packet, metadata={"outer": {"worldstate": "raw_state:full_map"}})
    result = run_world_cycle(replace(cycle, observation_packet=nested_obs), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in result.blocked_reasons


def test_world0_rejects_hidden_label_nested_metadata() -> None:
    bundle = noop_world_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    nested_obs = replace(cycle.observation_packet, metadata={"outer": {"hidden_label": "backend_only"}})
    result = run_world_cycle(replace(cycle, observation_packet=nested_obs), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in result.blocked_reasons


def test_world0_rejects_true_recipe_nested_metadata() -> None:
    bundle = noop_world_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    nested_obs = replace(cycle.observation_packet, metadata={"outer": {"true_recipe": "authoritative"}})
    result = run_world_cycle(replace(cycle, observation_packet=nested_obs), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED in result.blocked_reasons


def test_world0_rejects_scenario_label_nested_metadata() -> None:
    bundle = noop_world_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    nested_obs = replace(cycle.observation_packet, metadata={"outer": {"scenario_label": "eval:golden"}})
    result = run_world_cycle(replace(cycle, observation_packet=nested_obs), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.SCENARIO_LABEL_DECISION_DETECTED in result.blocked_reasons


def test_world0_no_automation_or_factory_claim() -> None:
    result = _run_loop(ap01_execution_fixture())
    assert result.automation_claimed is False
    assert result.factory_solution_hardcoded is False


def test_world0_timeout_and_max_tick_bounds() -> None:
    result = _run_loop(timeout_max_tick_fixture())
    assert WorldRunnerBlockReason.MAX_TICKS_REACHED in result.blocked_reasons
    assert result.counters.max_tick_stop_count == 1


def test_world0_replay_trace_preserves_residue_and_uncertainty() -> None:
    result = _run_loop(replay_trace_fixture())
    assert result.replay_trace_ref is not None
    assert result.residue_refs
    assert result.uncertainty_refs


def test_world0_no_ap01_no_backend_execution() -> None:
    result = _cycle(no_ap01_no_execution_fixture())
    assert not result.backend_results
    assert result.execution_status is WorldRunnerExecutionStatus.SKIPPED_NO_AP01


def test_world0_effect_without_request_or_passive_marker_blocked() -> None:
    result = _cycle(effect_without_correlation_blocked_fixture())
    assert WorldRunnerBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER in result.blocked_reasons


def test_world0_adapter_goal_selection_blocked() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], metadata_refs=("selected_goal:resource_chain",))
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in result.blocked_reasons


def test_world0_runner_does_not_rank_candidates() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], metadata_refs=("ranked_candidate:candidate_a",))
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in result.blocked_reasons


def test_world0_runner_does_not_select_micro_operation() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], metadata_refs=("selected_micro_operation:micro1:1",))
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in result.blocked_reasons


def test_world0_runner_does_not_choose_cost_winner() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], metadata_refs=("cost_winner:candidate_a",))
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.ADAPTER_ACTION_SELECTION_ATTEMPT in result.blocked_reasons


def test_world0_backend_execution_result_not_truth() -> None:
    result = _cycle(ap01_execution_fixture())
    assert result.backend_results[0].no_truth_claim is True
    assert result.effect_feedback[0].no_fact_claim is True


def test_world0_failed_tick_not_erased_from_trace() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], skip_subject_tick=True)
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert result.cycle_status is WorldRunnerCycleStatus.FAILED
    assert WorldRunnerBlockReason.SUBJECT_TICK_FAILED in result.blocked_reasons


def test_world0_noop_tick_not_progress_claim() -> None:
    result = _cycle(noop_world_fixture())
    assert result.cycle_status is WorldRunnerCycleStatus.NOOP
    assert result.authority_flags.can_claim_automation is False


def test_world0_adapter_config_change_does_not_require_subject_code_change() -> None:
    grid = _cycle(two_backend_grid_fixture())
    inv = _cycle(two_backend_inventory_fixture())
    assert grid.subject_tick_result is not None
    assert inv.subject_tick_result is not None


def test_world0_contact_projection_gate_block_preserved(monkeypatch) -> None:
    blocked_projection = SimpleNamespace(
        projection_status="blocked",
        projection_id="projection:blocked",
        projected_ab_input=SimpleNamespace(residue_refs=("residue:projection",), uncertainty_refs=("uncertain:projection",)),
    )
    monkeypatch.setattr(world0_policy, "project_world_contact", lambda cycle_id, contact_result: blocked_projection)
    result = _cycle(noop_world_fixture())
    assert WorldRunnerBlockReason.PROJECTION_BLOCKED in result.blocked_reasons
    assert result.cycle_status is WorldRunnerCycleStatus.BLOCKED
    assert result.subject_tick_result is None


def test_world0_invalid_contactspec_creates_blocked_cycle() -> None:
    bundle = contactspec_plan_blocked_fixture()
    cycle = bundle.loop_input.cycle_inputs[0]
    bad_spec: ContactSpec = replace(cycle.contact_spec, channel_declarations=())  # type: ignore[arg-type]
    result = run_world_cycle(replace(cycle, contact_spec=bad_spec), adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.INVALID_CONTACT_SPEC in result.blocked_reasons


def test_world0_backend_specific_factory_metadata_rejected() -> None:
    bundle = noop_world_fixture()
    cycle = replace(bundle.loop_input.cycle_inputs[0], metadata_refs=("build_factory:hardcoded_sequence",))
    result = run_world_cycle(cycle, adapter=bundle.adapter, config=bundle.loop_input.config)
    assert WorldRunnerBlockReason.FACTORY_SOLUTION_DETECTED in result.blocked_reasons


def test_world0_runner_counters_match_cycle_trace() -> None:
    loop = _run_loop(ap01_execution_fixture())
    assert loop.counters.cycle_count == len(loop.cycle_traces)


def test_world0_replay_trace_has_no_hidden_worldstate() -> None:
    loop = _run_loop(replay_trace_fixture())
    assert WorldRunnerBlockReason.BACKEND_WORLDSTATE_DETECTED not in loop.blocked_reasons


def test_world0_demo_fixture_not_p17b_claim() -> None:
    loop = _run_loop(ap01_execution_fixture())
    assert loop.factory_solution_hardcoded is False
    assert loop.automation_claimed is False


def _run_loop(bundle):
    return run_world_loop(bundle.loop_input, adapter=bundle.adapter)
