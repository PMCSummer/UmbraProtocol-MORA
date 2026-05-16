from __future__ import annotations

from experiments.symbolic_trade.clarification_policy import (
    ClarificationBudget,
    ResponseReadinessStatus,
    evaluate_response_readiness,
)
from experiments.symbolic_trade.internal_state import build_self_state_probe_for_scenario
from experiments.symbolic_trade.runner import run_stage1_scenario
from experiments.symbolic_trade.transfer_affordance import (
    TransferAffordancePolicy,
    TransferAffordanceStatus,
    build_invocation_candidate,
    build_transfer_affordance_record,
    execute_transfer_invocation,
    infer_transfer_affordance_status,
)


def _base_inputs(scenario: str):
    stage1 = run_stage1_scenario(scenario, include_falsifiers=False)
    self_state = build_self_state_probe_for_scenario(scenario)
    affordance = build_transfer_affordance_record(
        scenario_name=scenario,
        packets=stage1.emitted_packets,
        self_state=self_state,
    )
    readiness = evaluate_response_readiness(
        scenario_name=scenario,
        self_state=self_state,
        subject_visible_packets=stage1.emitted_packets,
        transfer_affordance_status=affordance.status.value,
        budget=ClarificationBudget(),
    )
    return stage1, self_state, affordance, readiness


def test_stage4_transfer_affordance_status_infers_blocked_and_available() -> None:
    blocked = run_stage1_scenario("blocked_aperture", include_falsifiers=False)
    mirrored = run_stage1_scenario("mirrored_resource_asymmetry", include_falsifiers=False)
    assert infer_transfer_affordance_status(blocked.emitted_packets) is TransferAffordanceStatus.BLOCKED
    assert infer_transfer_affordance_status(mirrored.emitted_packets) is TransferAffordanceStatus.AVAILABLE


def test_stage4_invocation_candidate_respects_explicit_execution_flag() -> None:
    stage1, _self_state, affordance, readiness = _base_inputs("mirrored_resource_asymmetry")
    assert readiness.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
    candidate = build_invocation_candidate(
        scenario_name=stage1.scenario_id,
        readiness=readiness,
        affordance=affordance,
        offer_candidate_id="offer:1",
        policy=TransferAffordancePolicy(execute_transfer_affordance=False),
    )
    assert candidate.execution_requested is False
    assert candidate.execution_prohibited is True


def test_stage4_transfer_invocation_successful_cycle_is_observed_not_oracle() -> None:
    stage1, _self_state, affordance, readiness = _base_inputs("successful_scripted_exchange_cycle")
    candidate = build_invocation_candidate(
        scenario_name=stage1.scenario_id,
        readiness=readiness,
        affordance=affordance,
        offer_candidate_id="offer:1",
        policy=TransferAffordancePolicy(execute_transfer_affordance=True),
    )
    attempt, result, episode = execute_transfer_invocation(
        scenario_name=stage1.scenario_id,
        invocation=candidate,
        packets=stage1.emitted_packets,
    )
    assert attempt.attempted is True
    assert result.observed is True
    assert result.outcome.value == "succeeded"
    assert episode.verified is True


def test_stage4_transfer_invocation_failure_preserves_residue() -> None:
    stage1, _self_state, affordance, readiness = _base_inputs("transfer_affordance_failure")
    candidate = build_invocation_candidate(
        scenario_name=stage1.scenario_id,
        readiness=readiness,
        affordance=affordance,
        offer_candidate_id="offer:1",
        policy=TransferAffordancePolicy(execute_transfer_affordance=True),
    )
    attempt, result, episode = execute_transfer_invocation(
        scenario_name=stage1.scenario_id,
        invocation=candidate,
        packets=stage1.emitted_packets,
    )
    assert attempt.attempted is True
    assert result.outcome.value != "succeeded"
    assert result.residue_required is True
    assert episode.residue_present is True
