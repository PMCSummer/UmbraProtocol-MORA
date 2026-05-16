from __future__ import annotations

import json

from experiments.symbolic_trade import CounterpartSignalKind, packet_to_dict, run_stage0_packet_dry_run


_FORBIDDEN = ("trade", "offer", "request", "ack", "deal", "bargain", "exchange", "market")


def test_stage0_no_trade_specific_communication_acts() -> None:
    names = [member.name.lower() for member in CounterpartSignalKind]
    values = [member.value.lower() for member in CounterpartSignalKind]
    for token in _FORBIDDEN:
        assert all(token not in name for name in names)
        assert all(token not in value for value in values)


def test_stage0_eval_labels_not_subject_visible() -> None:
    result = run_stage0_packet_dry_run(include_falsifiers=False)
    packet_strings = " ".join(packet.packet_id + packet.source_id + packet.signal_kind.value for packet in result.emitted_packets)
    serialized_packets = json.dumps([packet_to_dict(packet) for packet in result.emitted_packets], sort_keys=True)
    for label in result.success_labels:
        assert label not in packet_strings
        assert label not in serialized_packets


def test_stage0_harness_truth_separated_from_subject_visible_events() -> None:
    result = run_stage0_packet_dry_run(include_falsifiers=False)
    assert "harness_truth" in result.eval_only
    assert result.eval_only["hidden_truth_is_subject_invisible"] is True
    assert all(packet.hidden_truth_excluded for packet in result.emitted_packets)


def test_stage0_adapter_keeps_claim_vs_fact_boundary() -> None:
    result = run_stage0_packet_dry_run(include_falsifiers=False)
    claim_packets = [p for p in result.emitted_packets if p.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM]
    assert claim_packets
    assert all(p.claim_not_fact_marker for p in claim_packets)
