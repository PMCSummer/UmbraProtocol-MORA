from __future__ import annotations

from substrate.s03_ownership_weighted_learning.models import (
    S03OwnershipWeightedLearningResult,
)


def s03_ownership_weighted_learning_snapshot(
    result: S03OwnershipWeightedLearningResult,
) -> dict[str, object]:
    if not isinstance(result, S03OwnershipWeightedLearningResult):
        raise TypeError(
            "s03_ownership_weighted_learning_snapshot requires S03OwnershipWeightedLearningResult"
        )
    packet = result.state.packets[-1]
    return {
        "state": {
            "learning_id": result.state.learning_id,
            "tick_index": result.state.tick_index,
            "latest_packet_id": result.state.latest_packet_id,
            "latest_update_class": result.state.latest_update_class.value,
            "latest_commit_class": result.state.latest_commit_class.value,
            "latest_ambiguity_class": (
                None
                if result.state.latest_ambiguity_class is None
                else result.state.latest_ambiguity_class.value
            ),
            "freeze_or_defer_state": result.state.freeze_or_defer_state.value,
            "requested_revalidation": result.state.requested_revalidation,
            "repeated_self_support": result.state.repeated_self_support,
            "repeated_world_support": result.state.repeated_world_support,
            "repeated_mixed_support": result.state.repeated_mixed_support,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "latest_packet": {
            "outcome_packet_id": packet.outcome_packet_id,
            "attribution_basis": packet.attribution_basis,
            "update_class": packet.update_class.value,
            "commit_class": packet.commit_class.value,
            "ambiguity_class": (
                None if packet.ambiguity_class is None else packet.ambiguity_class.value
            ),
            "self_update_weight": packet.self_update_weight,
            "world_update_weight": packet.world_update_weight,
            "observation_update_weight": packet.observation_update_weight,
            "anomaly_update_weight": packet.anomaly_update_weight,
            "freeze_or_defer_status": packet.freeze_or_defer_status.value,
            "target_model_classes": tuple(item.value for item in packet.target_model_classes),
            "target_allocations": tuple(
                {
                    "target_class": item.target_class.value,
                    "weight": item.weight,
                }
                for item in packet.target_allocations
            ),
            "update_scope": packet.update_scope,
            "confidence": packet.confidence,
            "repeated_support": packet.repeated_support,
            "convergent_support": packet.convergent_support,
            "validity_status": packet.validity_status,
            "stale_or_invalidated": packet.stale_or_invalidated,
            "provenance": packet.provenance,
        },
        "gate": {
            "learning_packet_consumer_ready": result.gate.learning_packet_consumer_ready,
            "mixed_update_consumer_ready": result.gate.mixed_update_consumer_ready,
            "freeze_obedience_consumer_ready": result.gate.freeze_obedience_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "s03_first_slice_only": result.scope_marker.s03_first_slice_only,
            "s04_implemented": result.scope_marker.s04_implemented,
            "s05_implemented": result.scope_marker.s05_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "learning_id": result.telemetry.learning_id,
            "tick_index": result.telemetry.tick_index,
            "latest_packet_id": result.telemetry.latest_packet_id,
            "latest_update_class": result.telemetry.latest_update_class,
            "latest_commit_class": result.telemetry.latest_commit_class,
            "freeze_or_defer_state": result.telemetry.freeze_or_defer_state,
            "requested_revalidation": result.telemetry.requested_revalidation,
            "self_update_weight": result.telemetry.self_update_weight,
            "world_update_weight": result.telemetry.world_update_weight,
            "observation_update_weight": result.telemetry.observation_update_weight,
            "anomaly_update_weight": result.telemetry.anomaly_update_weight,
            "repeated_self_support": result.telemetry.repeated_self_support,
            "repeated_world_support": result.telemetry.repeated_world_support,
            "repeated_mixed_support": result.telemetry.repeated_mixed_support,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
