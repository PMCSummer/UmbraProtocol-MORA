from __future__ import annotations

from dataclasses import dataclass

from substrate.w01_bounded_world_loop import (
    W01PacketIntegrityStatus,
    W01PresenceMode,
    W01Result,
    W01SourceAuthority,
    W01WorldPacket,
    W01WorldPacketSet,
    build_w01_bounded_world_loop,
)


@dataclass(frozen=True, slots=True)
class W01HarnessCase:
    case_id: str
    packet_set: W01WorldPacketSet | None
    enforcement_enabled: bool = True


@dataclass(frozen=True, slots=True)
class W01HarnessRun:
    w01_result: W01Result


def w01_packet(
    *,
    packet_id: str,
    sequence: int,
    entity_ref: str,
    source_authority: W01SourceAuthority = W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
    presence_mode: W01PresenceMode = W01PresenceMode.PRESENT,
    integrity_status: W01PacketIntegrityStatus = W01PacketIntegrityStatus.VALID,
    source_id: str = "provider.world",
    observation_payload: str | None = "obs",
    action_ref: str | None = None,
    effect_payload: str | None = None,
    confidence: float = 0.8,
    contradiction_markers: tuple[str, ...] = (),
    provenance_ref: tuple[str, ...] = ("tests.w01",),
    raw_packet_ref: str = "raw.packet",
    object_label: str | None = None,
    object_stream_id: str | None = None,
    object_authority_tags: tuple[str, ...] = (),
    revoked_ref: str | None = None,
) -> W01WorldPacket:
    return W01WorldPacket(
        packet_id=packet_id,
        sequence=sequence,
        entity_ref=entity_ref,
        observation_payload=observation_payload,
        action_ref=action_ref,
        effect_payload=effect_payload,
        source_authority=source_authority,
        source_id=source_id,
        timestamp_or_sequence=f"seq:{sequence}",
        presence_mode=presence_mode,
        confidence=confidence,
        integrity_status=integrity_status,
        contradiction_markers=contradiction_markers,
        provenance_ref=provenance_ref,
        raw_packet_ref=raw_packet_ref,
        object_label=object_label,
        object_stream_id=object_stream_id,
        object_authority_tags=object_authority_tags,
        revoked_ref=revoked_ref,
    )


def w01_packet_set(
    *,
    set_id: str,
    packets: tuple[W01WorldPacket, ...],
    source_lineage: tuple[str, ...] | None = None,
    reason: str = "tests.w01 fixture",
) -> W01WorldPacketSet:
    return W01WorldPacketSet(
        packet_set_id=set_id,
        packets=packets,
        source_lineage=source_lineage if source_lineage is not None else ("tests.w01", set_id),
        reason=reason,
    )


def build_w01_harness_case(case: W01HarnessCase) -> W01HarnessRun:
    result = build_w01_bounded_world_loop(
        tick_id=f"tests.w01:{case.case_id}",
        tick_index=1,
        packet_set=case.packet_set,
        enforcement_enabled=case.enforcement_enabled,
    )
    return W01HarnessRun(w01_result=result)
