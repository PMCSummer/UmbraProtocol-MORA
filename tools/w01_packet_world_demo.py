from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.w01_bounded_world_loop import (
    W01PacketIntegrityStatus,
    W01PresenceMode,
    W01SourceAuthority,
    W01WorldPacket,
    W01WorldPacketSet,
    build_w01_bounded_world_loop,
)


def _packet(
    *,
    packet_id: str,
    sequence: int,
    entity_ref: str,
    presence: W01PresenceMode,
    authority: W01SourceAuthority,
    integrity: W01PacketIntegrityStatus,
    action_ref: str | None = None,
    effect_payload: str | None = None,
    observation_payload: str | None = "obs",
) -> W01WorldPacket:
    return W01WorldPacket(
        packet_id=packet_id,
        sequence=sequence,
        entity_ref=entity_ref,
        observation_payload=observation_payload,
        action_ref=action_ref,
        effect_payload=effect_payload,
        source_authority=authority,
        source_id="demo.world.provider",
        timestamp_or_sequence=f"seq:{sequence}",
        presence_mode=presence,
        confidence=0.82,
        integrity_status=integrity,
        contradiction_markers=(),
        provenance_ref=("tools.w01_packet_world_demo",),
        raw_packet_ref=f"raw:{packet_id}",
        object_label="CIRCLE" if entity_ref.endswith("A") else "SQUARE",
        object_stream_id=f"stream:{entity_ref}",
        object_authority_tags=("demo-provider",),
    )


def _scenario_packets(scenario: str) -> tuple[W01WorldPacket, ...]:
    if scenario == "present":
        return (
            _packet(
                packet_id="wp_001",
                sequence=1,
                entity_ref="slot_A",
                presence=W01PresenceMode.PRESENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
            ),
        )
    if scenario == "absent":
        return (
            _packet(
                packet_id="wp_001",
                sequence=1,
                entity_ref="slot_A",
                presence=W01PresenceMode.ABSENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
            ),
        )
    if scenario == "partial":
        return (
            _packet(
                packet_id="wp_001",
                sequence=1,
                entity_ref="slot_A",
                presence=W01PresenceMode.PARTIAL,
                authority=W01SourceAuthority.WEAK_SCAFFOLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.DEGRADED,
            ),
        )
    if scenario == "contradictory":
        return (
            _packet(
                packet_id="wp_001",
                sequence=1,
                entity_ref="slot_A",
                presence=W01PresenceMode.PRESENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
            ),
            _packet(
                packet_id="wp_002",
                sequence=2,
                entity_ref="slot_A",
                presence=W01PresenceMode.ABSENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
            ),
        )
    if scenario == "revoked":
        revoked = _packet(
            packet_id="wp_001",
            sequence=1,
            entity_ref="slot_A",
            presence=W01PresenceMode.REVOKED_OR_INVALID,
            authority=W01SourceAuthority.REVOKED_SOURCE,
            integrity=W01PacketIntegrityStatus.REVOKED,
        )
        return (revoked,)
    if scenario == "action_effect_valid":
        return (
            _packet(
                packet_id="wp_001_probe",
                sequence=1,
                entity_ref="slot_A",
                presence=W01PresenceMode.PRESENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
                action_ref="act_001_probe_A",
                observation_payload="probe_seen",
            ),
            _packet(
                packet_id="wp_002_effect",
                sequence=2,
                entity_ref="slot_A",
                presence=W01PresenceMode.PRESENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
                action_ref="act_001_probe_A",
                effect_payload="effect_confirmed",
                observation_payload="effect_seen",
            ),
        )
    if scenario == "action_effect_broken":
        return (
            _packet(
                packet_id="wp_001_probe",
                sequence=1,
                entity_ref="slot_A",
                presence=W01PresenceMode.PRESENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
                action_ref="act_001_probe_A",
                observation_payload="probe_seen",
            ),
            _packet(
                packet_id="wp_002_effect",
                sequence=8,
                entity_ref="slot_A",
                presence=W01PresenceMode.PRESENT,
                authority=W01SourceAuthority.TRUSTED_WORLD_PROVIDER,
                integrity=W01PacketIntegrityStatus.VALID,
                action_ref="act_001_probe_A",
                effect_payload="effect_confirmed",
                observation_payload="effect_seen",
            ),
        )
    raise ValueError(f"Unsupported scenario: {scenario}")


def _render_world_view() -> str:
    return "\n".join(
        (
            "WORLD PROVIDER VIEW",
            "[ A ] = CIRCLE / staged",
            "[ B ] = SQUARE / staged",
            "[ C ] = empty",
        )
    )


def _print_report(scenario: str) -> None:
    packets = _scenario_packets(scenario)
    packet_set = W01WorldPacketSet(
        packet_set_id=f"demo:{scenario}",
        packets=packets,
        source_lineage=("tools.w01_packet_world_demo", scenario),
        reason=f"demo scenario {scenario}",
    )
    result = build_w01_bounded_world_loop(
        tick_id=f"demo:{scenario}",
        tick_index=1,
        packet_set=packet_set,
    )

    print(_render_world_view())
    print("\nINCOMING PACKETS")
    for packet in packets:
        print(
            f"{packet.packet_id} source={packet.source_authority.value} "
            f"presence={packet.presence_mode.value} integrity={packet.integrity_status.value} entity={packet.entity_ref}"
        )

    first_state = (
        result.admission_records[0].admission_state.value
        if result.admission_records
        else "no_clean_world_claim"
    )
    print("\nW01 ADMISSION")
    print(f"admission={first_state}")
    print("non_mature_object_claim=true")
    print(
        f"may_use_as_world_scaffold={any(item.may_use_as_world_scaffold for item in result.downstream_permissions)}"
    )
    print(
        f"may_claim_object_presence={any(item.may_claim_object_presence for item in result.downstream_permissions)}"
    )
    print(
        f"must_preserve_uncertainty={any(item.must_preserve_uncertainty for item in result.downstream_permissions)}"
    )

    print("\nACTION/EFFECT")
    if result.action_effect_linkages:
        link = result.action_effect_linkages[0]
        print(f"action_ref={link.action_ref}")
        print(f"effect_packet={link.effect_packet_ref}")
        print(f"linkage={link.causal_link_status.value}")
    else:
        print("action_ref=None")
        print("effect_packet=None")
        print("linkage=no_link_claim")


def main() -> int:
    parser = argparse.ArgumentParser(description="W01 bounded world-loop packet demo")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=(
            "present",
            "absent",
            "partial",
            "contradictory",
            "revoked",
            "action_effect_valid",
            "action_effect_broken",
        ),
    )
    args = parser.parse_args()
    _print_report(args.scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
