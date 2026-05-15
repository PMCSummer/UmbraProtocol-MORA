from __future__ import annotations

from dataclasses import replace

from experiments.symbolic_trade.falsifiers import run_symbolic_trade_falsifiers
from experiments.symbolic_trade.runner import run_stage1_scenario


def _result_map(result) -> dict[str, bool]:
    return {item.name: item.passed for item in result}


def test_required_falsifiers_pass_on_clean_scenarios() -> None:
    for scenario in (
        "presence_only",
        "resource_claim_contact",
        "mirrored_resource_asymmetry",
        "false_counterpart_claim",
        "blocked_aperture",
        "noisy_signal",
        "transfer_seen_without_trade_token",
        "eval_label_leak_attack",
    ):
        result = run_stage1_scenario(scenario, include_falsifiers=True)
        assert all(item.passed for item in result.falsifier_results), scenario


def test_hidden_state_leakage_negative_control_fails() -> None:
    result = run_stage1_scenario("resource_claim_contact", include_falsifiers=False)
    leaked_packet = replace(result.emitted_packets[0], hidden_truth_excluded=False)
    tampered = replace(result, emitted_packets=(leaked_packet,) + result.emitted_packets[1:])
    outcomes = _result_map(run_symbolic_trade_falsifiers(tampered))
    assert outcomes["hidden_state_leakage"] is False


def test_claim_promoted_to_fact_negative_control_fails() -> None:
    result = run_stage1_scenario("resource_claim_contact", include_falsifiers=False)
    packet = next(p for p in result.emitted_packets if p.claim_not_fact_marker)
    tampered_packet = replace(packet, claim_not_fact_marker=False)
    tampered_packets = tuple(tampered_packet if p.packet_id == packet.packet_id else p for p in result.emitted_packets)
    outcomes = _result_map(run_symbolic_trade_falsifiers(replace(result, emitted_packets=tampered_packets)))
    assert outcomes["claim_promoted_to_fact"] is False


def test_mutual_benefit_oracle_leak_negative_control_fails() -> None:
    result = run_stage1_scenario("mirrored_resource_asymmetry", include_falsifiers=False)
    packet = result.emitted_packets[0]
    tampered_packet = replace(packet, packet_id=f"{packet.packet_id}:mutually_beneficial_trade_possible")
    tampered = replace(result, emitted_packets=(tampered_packet,) + result.emitted_packets[1:])
    outcomes = _result_map(run_symbolic_trade_falsifiers(tampered))
    assert outcomes["mutual_benefit_oracle_leak"] is False


def test_blocked_aperture_ignored_negative_control_fails() -> None:
    result = run_stage1_scenario("blocked_aperture", include_falsifiers=False)
    trace_summary = dict(result.trace_summary)
    trace_summary["transfer_feasible"] = True
    outcomes = _result_map(run_symbolic_trade_falsifiers(replace(result, trace_summary=trace_summary)))
    assert outcomes["blocked_aperture_ignored"] is False


def test_correction_candidate_executed_negative_control_fails() -> None:
    result = run_stage1_scenario("noisy_signal", include_falsifiers=False)
    trace_summary = dict(result.trace_summary)
    trace_summary["correction_candidate_executed"] = True
    outcomes = _result_map(run_symbolic_trade_falsifiers(replace(result, trace_summary=trace_summary)))
    assert outcomes["correction_candidate_executed"] is False


def test_transfer_result_as_permission_negative_control_fails() -> None:
    result = run_stage1_scenario("transfer_seen_without_trade_token", include_falsifiers=False)
    trace_summary = dict(result.trace_summary)
    trace_summary["transfer_result_grants_permission"] = True
    outcomes = _result_map(run_symbolic_trade_falsifiers(replace(result, trace_summary=trace_summary)))
    assert outcomes["transfer_result_as_permission"] is False


def test_noisy_signal_cleaned_negative_control_fails() -> None:
    result = run_stage1_scenario("noisy_signal", include_falsifiers=False)
    markers = tuple(marker for marker in result.claim_discipline_markers if marker != "contradiction_visible_without_cleanup")
    outcomes = _result_map(run_symbolic_trade_falsifiers(replace(result, claim_discipline_markers=markers)))
    assert outcomes["noisy_signal_cleaned"] is False
