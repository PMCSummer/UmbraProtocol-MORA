from __future__ import annotations

from substrate.s04_interoceptive_self_binding.models import (
    S04InteroceptiveSelfBindingResult,
)


def s04_interoceptive_self_binding_snapshot(
    result: S04InteroceptiveSelfBindingResult,
) -> dict[str, object]:
    if not isinstance(result, S04InteroceptiveSelfBindingResult):
        raise TypeError(
            "s04_interoceptive_self_binding_snapshot requires S04InteroceptiveSelfBindingResult"
        )
    return {
        "state": {
            "binding_id": result.state.binding_id,
            "tick_index": result.state.tick_index,
            "entries": tuple(
                {
                    "binding_entry_id": item.binding_entry_id,
                    "channel_or_group_id": item.channel_or_group_id,
                    "binding_status": item.binding_status.value,
                    "binding_strength": item.binding_strength,
                    "binding_basis": item.binding_basis,
                    "coupling_support": item.coupling_support,
                    "ownership_support": item.ownership_support,
                    "boundary_support": item.boundary_support,
                    "regulatory_support": item.regulatory_support,
                    "continuity_support": item.continuity_support,
                    "temporal_persistence": item.temporal_persistence,
                    "contamination_level": item.contamination_level,
                    "current_validity": item.current_validity,
                    "provenance": item.provenance,
                }
                for item in result.state.entries
            ),
            "core_bound_channels": result.state.core_bound_channels,
            "peripheral_or_weakly_bound_channels": (
                result.state.peripheral_or_weakly_bound_channels
            ),
            "contested_channels": result.state.contested_channels,
            "recently_unbound_channels": result.state.recently_unbound_channels,
            "no_stable_self_core_claim": result.state.no_stable_self_core_claim,
            "strongest_binding_strength": result.state.strongest_binding_strength,
            "contamination_detected": result.state.contamination_detected,
            "rebinding_event": result.state.rebinding_event,
            "stale_binding_drop_count": result.state.stale_binding_drop_count,
            "candidate_channels": result.state.candidate_channels,
            "excluded_channels": result.state.excluded_channels,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "core_consumer_ready": result.gate.core_consumer_ready,
            "contested_consumer_ready": result.gate.contested_consumer_ready,
            "no_stable_core_consumer_ready": result.gate.no_stable_core_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "s04_first_slice_only": result.scope_marker.s04_first_slice_only,
            "s05_implemented": result.scope_marker.s05_implemented,
            "full_self_model_implemented": result.scope_marker.full_self_model_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "binding_id": result.telemetry.binding_id,
            "tick_index": result.telemetry.tick_index,
            "strong_bound_count": result.telemetry.strong_bound_count,
            "weak_bound_count": result.telemetry.weak_bound_count,
            "provisional_count": result.telemetry.provisional_count,
            "contested_count": result.telemetry.contested_count,
            "no_stable_core_claim": result.telemetry.no_stable_core_claim,
            "strongest_binding_strength": result.telemetry.strongest_binding_strength,
            "contamination_detected": result.telemetry.contamination_detected,
            "rebinding_event": result.telemetry.rebinding_event,
            "stale_binding_drop_count": result.telemetry.stale_binding_drop_count,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
