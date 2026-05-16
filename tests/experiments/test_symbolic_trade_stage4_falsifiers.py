from __future__ import annotations

from dataclasses import replace

import experiments.symbolic_trade.falsifiers as falsifier_module
from experiments.symbolic_trade.runner import run_stage4_cycle


def _outcomes(items) -> dict[str, bool]:
    return {item.name: item.passed for item in items}


def test_stage4_falsifiers_exist_and_pass_on_clean_scenarios() -> None:
    expected = {
        "clarification_loop_without_progress",
        "clarification_when_sufficient_info_exists",
        "generic_clarification_without_target",
        "offer_without_counterpart_need",
        "offer_without_counterpart_surplus",
        "offer_without_a_surplus",
        "offer_without_a_deficit",
        "offer_when_aperture_blocked",
        "transfer_without_affordance",
        "transfer_without_offer_candidate",
        "transfer_without_explicit_execution_flag",
        "transfer_candidate_executes_directly",
        "counterpart_claim_as_fact",
        "hidden_b_inventory_used_for_offer",
        "mutual_benefit_oracle_used",
        "surplus_as_automatic_offer",
        "deficit_as_permission",
        "b_surplus_as_guaranteed_availability",
        "offer_executes_transfer_directly",
        "transfer_result_as_trade_success_oracle",
        "failed_transfer_erases_residue",
        "w06_correction_candidate_executed",
        "pre_scripted_response_as_invocation_response",
        "passive_transfer_packet_as_trade_success",
        "offer_candidate_as_transfer_execution",
        "available_affordance_as_invoked",
        "b_response_without_invocation_causality",
        "a04_binding_without_authority",
        "a02_gap_silently_ignored",
        "p02_episode_completion_inflation",
        "core_contamination",
    }
    for scenario in (
        "mirrored_resource_asymmetry",
        "b_surplus_only",
        "b_need_only",
        "blocked_aperture",
        "false_counterpart_claim",
        "noisy_signal",
        "transfer_affordance_failure",
        "successful_scripted_exchange_cycle",
    ):
        run = run_stage4_cycle(scenario, include_falsifiers=False)
        results = falsifier_module.run_stage4_cycle_falsifiers(run)
        names = {item.name for item in results}
        assert expected.issubset(names)
        assert all(item.passed for item in results), scenario


def test_stage4_falsifier_negative_controls_offer_without_need_and_deficit_permission() -> None:
    run = run_stage4_cycle("b_surplus_only", include_falsifiers=False)
    mutated = replace(
        run,
        offer_candidate_emitted=True,
        offer_candidate_id="forced_offer",
    )
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["offer_without_counterpart_need"] is False
    assert outcomes["deficit_as_permission"] is False


def test_stage4_falsifier_negative_controls_blocked_transfer_and_execution_flag() -> None:
    run = run_stage4_cycle("blocked_aperture", include_falsifiers=False)
    bad_invocation = replace(
        run.transfer_invocation_candidate,
        eligible=True,
        execution_requested=False,
        execution_prohibited=False,
    )
    bad_attempt = replace(
        run.transfer_attempt_record,
        attempted=True,
        world_executed_by_harness=True,
        execution_prohibited=False,
    )
    mutated = replace(
        run,
        transfer_invocation_candidate=bad_invocation,
        transfer_attempt_record=bad_attempt,
        offer_candidate_emitted=True,
        offer_candidate_id="forced_offer",
    )
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["offer_when_aperture_blocked"] is False
    assert outcomes["transfer_without_affordance"] is False
    assert outcomes["transfer_without_explicit_execution_flag"] is False


def test_stage4_falsifier_negative_controls_hidden_oracle_leak() -> None:
    run = run_stage4_cycle("mirrored_resource_asymmetry", include_falsifiers=False)
    visible = list(run.visible_packets)
    visible[0] = {**visible[0], "harness_truth": {"b_true_inventory": "water_surplus"}}
    mutated = replace(run, visible_packets=tuple(visible))
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["hidden_b_inventory_used_for_offer"] is False


def test_stage4_falsifier_negative_controls_transfer_result_success_oracle_typed_fields() -> None:
    run = run_stage4_cycle(
        "successful_scripted_exchange_cycle",
        include_falsifiers=False,
        execute_transfer_affordance=True,
    )
    bad_episode = replace(
        run.transfer_episode_record,
        verified=False,
        exchange_completion_claim=True,
        reciprocal_transfer_observed=False,
    )
    mutated = replace(run, transfer_episode_record=bad_episode, exchange_completion_claim=True)
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["transfer_result_as_trade_success_oracle"] is False

    bad_result = replace(
        run.transfer_result_record,
        result_used_as_success_authority=True,
    )
    mutated2 = replace(run, transfer_result_record=bad_result)
    outcomes2 = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated2))
    assert outcomes2["transfer_result_as_trade_success_oracle"] is False


def test_stage4_falsifier_negative_controls_w06_typed_non_execution_boundary() -> None:
    run = run_stage4_cycle("transfer_affordance_failure", include_falsifiers=False, execute_transfer_affordance=True)
    bad_w06 = replace(
        run.w06_correction_boundary,
        correction_candidate_created=True,
        correction_execution_prohibited=False,
        correction_executed=True,
    )
    mutated = replace(run, w06_correction_boundary=bad_w06)
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["w06_correction_candidate_executed"] is False


def test_stage4_falsifier_negative_controls_pre_scripted_response_causality() -> None:
    run = run_stage4_cycle("successful_scripted_exchange_cycle", include_falsifiers=False)
    bad_detail = replace(
        run.scripted_b_response_details[0],
        caused_by_transfer_invocation=True,
        causing_invocation_id="fake:invocation",
        response_record_source="pre_scripted_visible_packet",
        causal_status="causally_after_invocation",
    )
    mutated = replace(run, scripted_b_response_details=(bad_detail, *run.scripted_b_response_details[1:]))
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["pre_scripted_response_as_invocation_response"] is False


def test_stage4_falsifier_negative_controls_available_not_equal_invoked() -> None:
    run = run_stage4_cycle("mirrored_resource_asymmetry", include_falsifiers=False)
    bad_attempt = replace(run.transfer_attempt_record, attempted=True, world_executed_by_harness=True, execution_prohibited=False)
    bad_invocation = replace(run.transfer_invocation_candidate, execution_requested=False, execution_prohibited=False, eligible=True)
    mutated = replace(run, transfer_attempt_record=bad_attempt, transfer_invocation_candidate=bad_invocation)
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(mutated))
    assert outcomes["available_affordance_as_invoked"] is False


def test_stage4_core_contamination_detects_untracked_forbidden_path(monkeypatch) -> None:
    run = run_stage4_cycle("presence_only", include_falsifiers=False)
    monkeypatch.setattr(falsifier_module, "_modified_paths", lambda _repo_root: ())
    monkeypatch.setattr(
        falsifier_module,
        "_untracked_paths",
        lambda _repo_root: ("src/substrate/subject_tick/stage4_probe_leak.py",),
    )
    outcomes = _outcomes(falsifier_module.run_stage4_cycle_falsifiers(run))
    assert outcomes["core_contamination"] is False
