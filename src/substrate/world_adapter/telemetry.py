from __future__ import annotations

from substrate.world_adapter.models import (
    WorldAdapterGateDecision,
    WorldAdapterResult,
    WorldAdapterState,
    WorldAdapterTelemetry,
)


def build_world_adapter_telemetry(
    *,
    state: WorldAdapterState,
    gate: WorldAdapterGateDecision,
    attempted_paths: tuple[str, ...],
) -> WorldAdapterTelemetry:
    return WorldAdapterTelemetry(
        source_lineage=state.source_lineage,
        world_link_status=state.world_link_status,
        effect_status=state.effect_status,
        adapter_presence=state.adapter_presence,
        adapter_available=state.adapter_available,
        adapter_degraded=state.adapter_degraded,
        world_grounded_transition_allowed=gate.world_grounded_transition_allowed,
        externally_effected_change_claim_allowed=gate.externally_effected_change_claim_allowed,
        world_action_success_claim_allowed=gate.world_action_success_claim_allowed,
        effect_feedback_correlated=gate.effect_feedback_correlated,
        restrictions=gate.restrictions,
        attempted_paths=attempted_paths,
        reason=gate.reason,
    )


def world_adapter_result_snapshot(result: WorldAdapterResult) -> dict[str, object]:
    return {
        "state": {
            "adapter_presence": result.state.adapter_presence,
            "adapter_available": result.state.adapter_available,
            "adapter_degraded": result.state.adapter_degraded,
            "world_link_status": result.state.world_link_status.value,
            "effect_status": result.state.effect_status.value,
            "effect_feedback_correlated": result.state.effect_feedback_correlated,
            "world_grounding_confidence": result.state.world_grounding_confidence,
            "unavailable_reason": result.state.unavailable_reason,
            "last_observation_packet": (
                None
                if result.state.last_observation_packet is None
                else {
                    "observation_id": result.state.last_observation_packet.observation_id,
                    "observation_kind": result.state.last_observation_packet.observation_kind,
                    "source_ref": result.state.last_observation_packet.source_ref,
                    "observed_at": result.state.last_observation_packet.observed_at,
                    "payload_ref": result.state.last_observation_packet.payload_ref,
                    "provenance": result.state.last_observation_packet.provenance,
                }
            ),
            "last_action_packet": (
                None
                if result.state.last_action_packet is None
                else {
                    "action_id": result.state.last_action_packet.action_id,
                    "action_kind": result.state.last_action_packet.action_kind,
                    "target_ref": result.state.last_action_packet.target_ref,
                    "requested_at": result.state.last_action_packet.requested_at,
                    "payload_ref": result.state.last_action_packet.payload_ref,
                    "provenance": result.state.last_action_packet.provenance,
                }
            ),
            "last_effect_packet": (
                None
                if result.state.last_effect_packet is None
                else {
                    "effect_id": result.state.last_effect_packet.effect_id,
                    "action_id": result.state.last_effect_packet.action_id,
                    "effect_kind": result.state.last_effect_packet.effect_kind,
                    "observed_at": result.state.last_effect_packet.observed_at,
                    "success": result.state.last_effect_packet.success,
                    "source_ref": result.state.last_effect_packet.source_ref,
                    "provenance": result.state.last_effect_packet.provenance,
                }
            ),
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "world_grounded_transition_allowed": result.gate.world_grounded_transition_allowed,
            "externally_effected_change_claim_allowed": result.gate.externally_effected_change_claim_allowed,
            "world_action_success_claim_allowed": result.gate.world_action_success_claim_allowed,
            "effect_feedback_correlated": result.gate.effect_feedback_correlated,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "world_link_status": result.telemetry.world_link_status.value,
            "effect_status": result.telemetry.effect_status.value,
            "adapter_presence": result.telemetry.adapter_presence,
            "adapter_available": result.telemetry.adapter_available,
            "adapter_degraded": result.telemetry.adapter_degraded,
            "world_grounded_transition_allowed": result.telemetry.world_grounded_transition_allowed,
            "externally_effected_change_claim_allowed": result.telemetry.externally_effected_change_claim_allowed,
            "world_action_success_claim_allowed": result.telemetry.world_action_success_claim_allowed,
            "effect_feedback_correlated": result.telemetry.effect_feedback_correlated,
            "restrictions": result.telemetry.restrictions,
            "attempted_paths": result.telemetry.attempted_paths,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
    }
