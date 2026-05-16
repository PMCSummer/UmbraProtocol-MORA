from __future__ import annotations

import json

from experiments.symbolic_trade.clarification_policy import ClarificationBudget, ResponseReadinessStatus, evaluate_response_readiness
from experiments.symbolic_trade.runner import run_stage4_cycle, stage4_result_to_dict
from experiments.symbolic_trade.stage4_trade_cycle_runner import STAGE4_SCENARIOS
from experiments.symbolic_trade.scripted_counterpart import build_scripted_stage1_scenario
from experiments.symbolic_trade.packets import emission_to_subject_packet
from experiments.symbolic_trade.transfer_affordance import infer_transfer_affordance_status
from experiments.symbolic_trade.internal_state import build_self_state_probe_for_scenario


def test_stage4_all_scenarios_run_with_falsifiers() -> None:
    for scenario in STAGE4_SCENARIOS:
        run = run_stage4_cycle(scenario, include_falsifiers=True)
        assert run.stage == "stage4_clarification_to_transfer_affordance_cycle"
        assert run.execution_level
        assert all(item["passed"] for item in run.falsifier_summary), scenario


def test_stage4_mirrored_offer_candidate_without_execution_by_default() -> None:
    run = run_stage4_cycle("mirrored_resource_asymmetry", include_falsifiers=False)
    assert run.offer_candidate_emitted is True
    assert run.transfer_attempt_record.attempted is False
    assert run.transfer_invocation_candidate.execution_requested is False


def test_stage4_mirrored_can_invoke_transfer_when_explicitly_enabled() -> None:
    run = run_stage4_cycle(
        "mirrored_resource_asymmetry",
        include_falsifiers=False,
        execute_transfer_affordance=True,
    )
    assert run.transfer_invocation_candidate.execution_requested is True
    assert run.transfer_attempt_record.attempted is True


def test_stage4_clarification_required_controls_do_not_emit_offer() -> None:
    surplus_only = run_stage4_cycle("b_surplus_only", include_falsifiers=False)
    need_only = run_stage4_cycle("b_need_only", include_falsifiers=False)
    assert surplus_only.offer_candidate_emitted is False
    assert need_only.offer_candidate_emitted is False
    assert surplus_only.readiness_decision.status.value in {"clarification_required", "revalidation_required"}
    assert need_only.readiness_decision.status.value in {"clarification_required", "revalidation_required"}


def test_stage4_clarification_resolves_missing_need_without_infinite_loop() -> None:
    run = run_stage4_cycle("clarification_resolves_missing_need", include_falsifiers=False)
    assert run.offer_candidate_emitted is True
    assert run.readiness_decision.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
    assert sum(1 for record in run.clarification_records if not record.progress_made) <= 1


def test_stage4_clarification_loop_guard_exhausts_to_non_offer_route() -> None:
    run = run_stage4_cycle("clarification_loop_guard", include_falsifiers=False)
    assert run.offer_candidate_emitted is False
    assert run.readiness_decision.status.value in {"revalidation_required", "observe_only", "abstain", "clarification_required"}
    assert run.transfer_attempt_record.attempted is False


def test_stage4_blocked_aperture_never_invokes_transfer() -> None:
    run = run_stage4_cycle("blocked_aperture", include_falsifiers=False, execute_transfer_affordance=True)
    assert run.transfer_affordance_record.status.value == "blocked"
    assert run.transfer_attempt_record.attempted is False


def test_stage4_false_noisy_failed_paths_keep_residue_or_revalidation() -> None:
    false_claim = run_stage4_cycle("false_counterpart_claim", include_falsifiers=False)
    noisy = run_stage4_cycle("noisy_signal", include_falsifiers=False)
    failed = run_stage4_cycle("claim_then_failed_transfer", include_falsifiers=False, execute_transfer_affordance=True)
    assert false_claim.w06_residue_or_revalidation is True or false_claim.offer_candidate_emitted is False
    assert noisy.w06_residue_or_revalidation is True
    assert failed.w06_residue_or_revalidation is True


def test_stage4_json_default_excludes_eval_only_and_include_scoped() -> None:
    run = run_stage4_cycle("mirrored_resource_asymmetry", include_falsifiers=True, include_eval_only=True)
    payload = stage4_result_to_dict(run, include_eval_only=False, include_transfer_episode=True, include_clarification_state=True)
    assert "eval_only" not in payload
    flat = json.dumps(payload, sort_keys=True)
    assert "harness_truth" not in flat

    eval_payload = stage4_result_to_dict(run, include_eval_only=True, include_transfer_episode=True, include_clarification_state=True)
    assert "eval_only" in eval_payload
    candidates_flat = json.dumps(
        {
            "readiness_decision": eval_payload.get("readiness_decision"),
            "transfer_invocation_candidate": eval_payload.get("transfer_invocation_candidate"),
            "transfer_result_record": eval_payload.get("transfer_result_record"),
        },
        sort_keys=True,
    )
    assert "harness_truth" not in candidates_flat


def test_stage4_readiness_transition_depends_on_structural_packets_not_scenario_id() -> None:
    scenario = build_scripted_stage1_scenario("clarification_resolves_missing_need")
    self_state = build_self_state_probe_for_scenario("clarification_resolves_missing_need")
    packets = tuple(
        emission_to_subject_packet(item, packet_id=f"{scenario.scenario_id}:packet:{index}")
        for index, item in enumerate(scenario.emissions, start=1)
    )
    transfer_status = infer_transfer_affordance_status(packets)

    mirrored = evaluate_response_readiness(
        scenario_name="clarification_resolves_missing_need",
        self_state=self_state,
        subject_visible_packets=packets,
        transfer_affordance_status=transfer_status.value,
        budget=ClarificationBudget(),
    )
    renamed = evaluate_response_readiness(
        scenario_name="renamed_structural_equivalent",
        self_state=self_state,
        subject_visible_packets=packets,
        transfer_affordance_status=transfer_status.value,
        budget=ClarificationBudget(),
    )
    assert mirrored.status is renamed.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
    assert mirrored.critical_missing_fields == renamed.critical_missing_fields


def test_stage4_same_scenario_id_without_structural_resolution_does_not_become_sufficient() -> None:
    scenario = build_scripted_stage1_scenario("clarification_resolves_missing_need")
    self_state = build_self_state_probe_for_scenario("clarification_resolves_missing_need")
    packets = tuple(
        emission_to_subject_packet(item, packet_id=f"{scenario.scenario_id}:packet:{index}")
        for index, item in enumerate(scenario.emissions[:2], start=1)
    )
    transfer_status = infer_transfer_affordance_status(packets)
    decision = evaluate_response_readiness(
        scenario_name="clarification_resolves_missing_need",
        self_state=self_state,
        subject_visible_packets=packets,
        transfer_affordance_status=transfer_status.value,
        budget=ClarificationBudget(),
    )
    assert decision.status is not ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER


def test_stage4_noexec_transfer_packets_are_passive_not_causal() -> None:
    run = run_stage4_cycle("successful_scripted_exchange_cycle", include_falsifiers=False)
    assert run.transfer_attempt_record.attempted is False
    assert run.transfer_result_record.outcome.value == "not_attempted"
    assert all(not item.caused_by_transfer_invocation for item in run.scripted_b_response_details)
    assert all(item.response_record_source == "passive_scenario_packet" for item in run.scripted_b_response_details)
    assert run.exchange_completion_claim is False


def test_stage4_exec_transfer_packets_are_causal_when_invoked() -> None:
    run = run_stage4_cycle(
        "successful_scripted_exchange_cycle",
        include_falsifiers=False,
        execute_transfer_affordance=True,
    )
    assert run.transfer_attempt_record.attempted is True
    assert run.post_invocation_response_count > 0
    assert all(item.caused_by_transfer_invocation for item in run.scripted_b_response_details)
    assert all(item.causing_invocation_id == run.transfer_invocation_candidate.invocation_id for item in run.scripted_b_response_details)
