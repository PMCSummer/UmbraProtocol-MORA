from __future__ import annotations

from substrate.s05_multi_cause_attribution_factorization.models import (
    S05MultiCauseAttributionResult,
)


def s05_multi_cause_attribution_snapshot(
    result: S05MultiCauseAttributionResult,
) -> dict[str, object]:
    if not isinstance(result, S05MultiCauseAttributionResult):
        raise TypeError(
            "s05_multi_cause_attribution_snapshot requires S05MultiCauseAttributionResult"
        )
    latest = result.state.packets[-1]
    return {
        "state": {
            "factorization_id": result.state.factorization_id,
            "tick_index": result.state.tick_index,
            "latest_packet_id": result.state.latest_packet_id,
            "dominant_cause_classes": tuple(
                item.value for item in result.state.dominant_cause_classes
            ),
            "unexplained_residual": result.state.unexplained_residual,
            "residual_class": result.state.residual_class.value,
            "underdetermined_split": result.state.underdetermined_split,
            "incompatible_candidates_present": result.state.incompatible_candidates_present,
            "temporal_misalignment_present": result.state.temporal_misalignment_present,
            "contamination_present": result.state.contamination_present,
            "reattribution_happened": result.state.reattribution_happened,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "latest_packet": {
            "outcome_packet_id": latest.outcome_packet_id,
            "cause_slots": tuple(
                {
                    "cause_class": slot.cause_class.value,
                    "eligibility_status": slot.eligibility_status.value,
                    "support_strength": slot.support_strength,
                    "allocated_share": slot.allocated_share,
                    "bounded_share_interval": slot.bounded_share_interval,
                    "evidence_basis": slot.evidence_basis,
                    "temporal_fit": slot.temporal_fit,
                    "channel_fit": slot.channel_fit,
                    "contamination_penalty": slot.contamination_penalty,
                    "provenance": slot.provenance,
                }
                for slot in latest.cause_slots
            ),
            "slot_weights_or_bounded_shares": latest.slot_weights_or_bounded_shares,
            "unexplained_residual": latest.unexplained_residual,
            "residual_class": latest.residual_class.value,
            "compatibility_basis": latest.compatibility_basis,
            "temporal_alignment_basis": latest.temporal_alignment_basis,
            "contamination_notes": latest.contamination_notes,
            "confidence": latest.confidence,
            "provenance": latest.provenance,
            "revision_status": latest.revision_status.value,
            "attribution_status": latest.attribution_status.value,
            "scope_validity": latest.scope_validity.value,
            "downstream_route_class": latest.downstream_route_class.value,
        },
        "gate": {
            "factorization_consumer_ready": result.gate.factorization_consumer_ready,
            "learning_route_ready": result.gate.learning_route_ready,
            "no_binary_recollapse_required": result.gate.no_binary_recollapse_required,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "s05_first_slice_only": result.scope_marker.s05_first_slice_only,
            "downstream_rollout_minimal": result.scope_marker.downstream_rollout_minimal,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "factorization_id": result.telemetry.factorization_id,
            "tick_index": result.telemetry.tick_index,
            "dominant_slot_count": result.telemetry.dominant_slot_count,
            "residual_share": result.telemetry.residual_share,
            "residual_class": result.telemetry.residual_class.value,
            "underdetermined_split": result.telemetry.underdetermined_split,
            "contamination_present": result.telemetry.contamination_present,
            "temporal_misalignment_present": result.telemetry.temporal_misalignment_present,
            "reattribution_happened": result.telemetry.reattribution_happened,
            "downstream_route_class": result.telemetry.downstream_route_class.value,
            "factorization_consumer_ready": result.telemetry.factorization_consumer_ready,
            "learning_route_ready": result.telemetry.learning_route_ready,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
