from __future__ import annotations

from experiments.symbolic_trade import (
    ApertureState,
    CounterpartEmission,
    CounterpartSignalKind,
    ResourceKind,
    ResourceLevel,
    SignalAuthority,
    TransferOutcome,
    emission_to_subject_packet,
    packet_from_dict,
    packet_to_dict,
    packet_to_w01_world_packet,
)


def _emission() -> CounterpartEmission:
    return CounterpartEmission(
        emission_id="pkt:1",
        source_actor_id="counterpart_b",
        signal_kind=CounterpartSignalKind.RESOURCE_STATUS_CLAIM,
        resource_kind=ResourceKind.WATER,
        reported_level=ResourceLevel.SURPLUS,
        item_kind=None,
        aperture_state=ApertureState.OPEN,
        source_authority=SignalAuthority.COUNTERPART_CLAIM,
        emitted_at_step=1,
        provenance_ref=("tests.experiments", "packets"),
        visible_to_subject=True,
        eval_truth_ref="truth:1",
        transfer_outcome=TransferOutcome.NOT_ATTEMPTED,
    )


def test_typed_model_construction_and_claim_marker() -> None:
    packet = emission_to_subject_packet(_emission(), packet_id="visible:1")
    assert packet.claim_not_fact_marker is True
    assert packet.hidden_truth_excluded is True
    assert packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM


def test_serialization_roundtrip_preserves_packet_fields() -> None:
    packet = emission_to_subject_packet(_emission(), packet_id="visible:2")
    restored = packet_from_dict(packet_to_dict(packet))
    assert restored == packet


def test_hidden_truth_not_present_in_visible_packet_payload() -> None:
    packet = emission_to_subject_packet(_emission(), packet_id="visible:3")
    payload = packet_to_dict(packet)
    assert "hidden_inventory" not in payload
    assert "eval_truth_ref" not in payload
    assert payload["hidden_truth_excluded"] is True


def test_packet_adapter_to_w01_preserves_claim_boundary_markers() -> None:
    packet = emission_to_subject_packet(_emission(), packet_id="visible:4")
    w01_packet = packet_to_w01_world_packet(packet, sequence=1)
    assert w01_packet.source_authority.value == "weak_scaffold_provider"
    assert "resource_status_signal" in (w01_packet.observation_payload or "")
