from __future__ import annotations

from experiments.symbolic_trade import CounterpartSignalKind, list_scenarios, run_stage1_scenario


def test_stage1_scenarios_run_deterministically() -> None:
    for scenario in list_scenarios():
        first = run_stage1_scenario(scenario, include_falsifiers=False)
        second = run_stage1_scenario(scenario, include_falsifiers=False)
        assert first.trace_summary == second.trace_summary
        assert tuple(p.packet_id for p in first.emitted_packets) == tuple(p.packet_id for p in second.emitted_packets)


def test_stage1_presence_only_has_no_resource_claim() -> None:
    result = run_stage1_scenario("presence_only", include_falsifiers=False)
    assert any(packet.signal_kind is CounterpartSignalKind.PRESENCE_PING for packet in result.emitted_packets)
    assert all(packet.signal_kind is not CounterpartSignalKind.RESOURCE_STATUS_CLAIM for packet in result.emitted_packets)


def test_stage1_resource_claim_contact_exposes_claims_not_facts() -> None:
    result = run_stage1_scenario("resource_claim_contact", include_falsifiers=False)
    claims = [packet for packet in result.emitted_packets if packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM]
    assert len(claims) == 2
    assert all(packet.claim_not_fact_marker for packet in claims)


def test_stage1_mirrored_resource_asymmetry_keeps_eval_only_reciprocity_label() -> None:
    result = run_stage1_scenario("mirrored_resource_asymmetry", include_falsifiers=False)
    assert "potential_reciprocity_eval_only" in result.success_labels
    packet_strings = " ".join(packet.signal_kind.value for packet in result.emitted_packets)
    assert "potential_reciprocity_eval_only" not in packet_strings


def test_stage1_false_counterpart_claim_has_no_hidden_truth_leakage() -> None:
    result = run_stage1_scenario("false_counterpart_claim", include_falsifiers=False)
    assert all(packet.hidden_truth_excluded for packet in result.emitted_packets)
    assert all(packet.source_authority.value != "harness_truth" for packet in result.emitted_packets)


def test_stage1_blocked_aperture_marks_transfer_not_feasible() -> None:
    result = run_stage1_scenario("blocked_aperture", include_falsifiers=False)
    assert result.trace_summary["blocked_aperture_seen"] is True
    assert result.trace_summary["transfer_feasible"] is False


def test_stage1_noisy_signal_represents_contradiction_without_cleanup() -> None:
    result = run_stage1_scenario("noisy_signal", include_falsifiers=False)
    assert result.trace_summary["contradiction_seen"] is True
    assert "contradiction_visible_without_cleanup" in result.claim_discipline_markers


def test_stage1_transfer_seen_without_trade_token_is_object_event_observation() -> None:
    result = run_stage1_scenario("transfer_seen_without_trade_token", include_falsifiers=False)
    kinds = {packet.signal_kind for packet in result.emitted_packets}
    assert CounterpartSignalKind.ITEM_SEEN_AT_APERTURE in kinds
    assert CounterpartSignalKind.TRANSFER_ATTEMPT in kinds


def test_stage1_eval_label_leak_attack_keeps_eval_label_outside_subject_packets() -> None:
    result = run_stage1_scenario("eval_label_leak_attack", include_falsifiers=False)
    label = "mutually_beneficial_trade_possible_eval_only"
    assert label in result.success_labels
    packet_strings = " ".join(packet.packet_id + packet.signal_kind.value for packet in result.emitted_packets)
    assert label not in packet_strings


def test_stage1_result_contains_phase_obligation_summary() -> None:
    result = run_stage1_scenario("resource_claim_contact", include_falsifiers=False)
    assert "w04_applicability_only_not_action_selection" in result.phase_obligation_summary
    assert "w05_channel_separation_and_mismatch_routing" in result.phase_obligation_summary
    assert "w06_operational_consequence_no_correction_execution" in result.phase_obligation_summary
