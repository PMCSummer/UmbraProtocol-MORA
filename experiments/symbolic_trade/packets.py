from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from substrate.w01_bounded_world_loop import W01WorldPacket

from .models import (
    ApertureState,
    CounterpartEmission,
    CounterpartSignalKind,
    ResourceKind,
    ResourceLevel,
    SignalAuthority,
    SubjectVisiblePacket,
    TransferOutcome,
)


def emission_to_subject_packet(emission: CounterpartEmission, *, packet_id: str) -> SubjectVisiblePacket:
    claim_marker = (
        emission.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM
        and emission.source_authority is SignalAuthority.COUNTERPART_CLAIM
    )
    return SubjectVisiblePacket(
        packet_id=packet_id,
        source_id=emission.source_actor_id,
        source_authority=emission.source_authority,
        signal_kind=emission.signal_kind,
        resource_kind=emission.resource_kind,
        reported_level=emission.reported_level,
        aperture_state=emission.aperture_state,
        timestamp_or_step=emission.emitted_at_step,
        provenance_ref=emission.provenance_ref,
        hidden_truth_excluded=True,
        claim_not_fact_marker=claim_marker,
        transfer_outcome=emission.transfer_outcome,
        item_kind=emission.item_kind,
    )


def packet_to_dict(packet: SubjectVisiblePacket) -> dict[str, object]:
    payload = asdict(packet)
    payload["source_authority"] = packet.source_authority.value
    payload["signal_kind"] = packet.signal_kind.value
    payload["aperture_state"] = packet.aperture_state.value
    payload["transfer_outcome"] = packet.transfer_outcome.value
    if packet.resource_kind is not None:
        payload["resource_kind"] = packet.resource_kind.value
    if packet.reported_level is not None:
        payload["reported_level"] = packet.reported_level.value
    if packet.item_kind is not None:
        payload["item_kind"] = packet.item_kind.value
    return payload


def packet_from_dict(payload: dict[str, object]) -> SubjectVisiblePacket:
    resource = payload.get("resource_kind")
    reported = payload.get("reported_level")
    item = payload.get("item_kind")
    return SubjectVisiblePacket(
        packet_id=str(payload["packet_id"]),
        source_id=str(payload["source_id"]),
        source_authority=SignalAuthority(str(payload["source_authority"])),
        signal_kind=CounterpartSignalKind(str(payload["signal_kind"])),
        resource_kind=ResourceKind(str(resource)) if resource is not None else None,
        reported_level=ResourceLevel(str(reported)) if reported is not None else None,
        aperture_state=ApertureState(str(payload["aperture_state"])),
        timestamp_or_step=int(payload["timestamp_or_step"]),
        provenance_ref=tuple(payload.get("provenance_ref", ())),
        hidden_truth_excluded=bool(payload["hidden_truth_excluded"]),
        claim_not_fact_marker=bool(payload["claim_not_fact_marker"]),
        transfer_outcome=TransferOutcome(str(payload.get("transfer_outcome", TransferOutcome.NOT_ATTEMPTED.value))),
        item_kind=ResourceKind(str(item)) if item is not None else None,
    )


def packet_to_w01_world_packet(packet: SubjectVisiblePacket, *, sequence: int, entity_ref: str = "aperture_slot") -> "W01WorldPacket":
    # Imported lazily so this harness package is importable from repo root without
    # requiring PYTHONPATH=src during plain module import checks.
    from substrate.w01_bounded_world_loop import (
        W01PacketIntegrityStatus,
        W01PresenceMode,
        W01SourceAuthority,
        W01WorldPacket,
    )

    authority = {
        SignalAuthority.COUNTERPART_CLAIM: W01SourceAuthority.WEAK_SCAFFOLD_PROVIDER,
        SignalAuthority.OBSERVED_EVENT: W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
        SignalAuthority.HARNESS_TRUTH: W01SourceAuthority.UNKNOWN_SOURCE,
        SignalAuthority.INFERRED_BY_HARNESS_FOR_EVAL_ONLY: W01SourceAuthority.UNKNOWN_SOURCE,
    }[packet.source_authority]

    presence = W01PresenceMode.PRESENT
    if packet.signal_kind is CounterpartSignalKind.ABSENCE:
        presence = W01PresenceMode.ABSENT
    elif packet.signal_kind is CounterpartSignalKind.CONTRADICTION:
        presence = W01PresenceMode.CONTRADICTORY

    integrity = (
        W01PacketIntegrityStatus.DEGRADED
        if packet.signal_kind in {CounterpartSignalKind.CONTRADICTION, CounterpartSignalKind.BLOCKED}
        else W01PacketIntegrityStatus.VALID
    )

    observation_payload = "|".join(
        part
        for part in (
            packet.signal_kind.value,
            packet.resource_kind.value if packet.resource_kind else "",
            packet.reported_level.value if packet.reported_level else "",
            packet.aperture_state.value,
            packet.transfer_outcome.value,
        )
        if part
    )

    action_ref = None
    effect_payload = None
    if packet.signal_kind is CounterpartSignalKind.TRANSFER_ATTEMPT:
        action_ref = f"transfer_attempt:{packet.packet_id}"
    if packet.signal_kind is CounterpartSignalKind.TRANSFER_RESULT:
        action_ref = f"transfer_attempt:{packet.packet_id}"
        effect_payload = packet.transfer_outcome.value

    return W01WorldPacket(
        packet_id=packet.packet_id,
        sequence=sequence,
        entity_ref=entity_ref,
        observation_payload=observation_payload,
        action_ref=action_ref,
        effect_payload=effect_payload,
        source_authority=authority,
        source_id=packet.source_id,
        timestamp_or_sequence=f"seq:{sequence}",
        presence_mode=presence,
        confidence=0.7,
        integrity_status=integrity,
        contradiction_markers=("counterpart_contradiction",)
        if packet.signal_kind is CounterpartSignalKind.CONTRADICTION
        else (),
        provenance_ref=packet.provenance_ref,
        raw_packet_ref=f"symbolic_trade:{packet.packet_id}",
        object_label="RESOURCE_TOKEN" if packet.item_kind is not None else None,
        object_stream_id=f"counterpart:{packet.source_id}",
        object_authority_tags=("symbolic_trade_harness",),
    )
