from __future__ import annotations

from substrate.p02_intervention_episode_layer_licensed_action_trace.models import (
    P02InterventionEpisodeResult,
)


def p02_intervention_episode_layer_licensed_action_trace_snapshot(
    result: P02InterventionEpisodeResult,
) -> dict[str, object]:
    if not isinstance(result, P02InterventionEpisodeResult):
        raise TypeError(
            "p02_intervention_episode_layer_licensed_action_trace_snapshot requires P02InterventionEpisodeResult"
        )
    return {
        "metadata": {
            "episode_count": result.metadata.episode_count,
            "completed_as_licensed_count": result.metadata.completed_as_licensed_count,
            "partial_episode_count": result.metadata.partial_episode_count,
            "blocked_episode_count": result.metadata.blocked_episode_count,
            "awaiting_verification_count": result.metadata.awaiting_verification_count,
            "completion_verified_count": result.metadata.completion_verified_count,
            "overrun_detected_count": result.metadata.overrun_detected_count,
            "boundary_ambiguous_count": result.metadata.boundary_ambiguous_count,
            "license_link_missing_count": result.metadata.license_link_missing_count,
            "residue_count": result.metadata.residue_count,
            "side_effect_count": result.metadata.side_effect_count,
            "source_lineage": result.metadata.source_lineage,
        },
        "episodes": tuple(
            {
                "episode_id": item.episode_id,
                "source_license_refs": item.source_license_refs,
                "project_refs": item.project_refs,
                "action_trace_refs": item.action_trace_refs,
                "excluded_event_refs": item.excluded_event_refs,
                "boundary_window_start": item.boundary_window_start,
                "boundary_window_end": item.boundary_window_end,
                "status": item.status.value,
                "execution_status": item.execution_status.value,
                "outcome_verification_status": item.outcome_verification_status.value,
                "license_link_missing": item.license_link_missing,
                "overrun_detected": item.overrun_detected,
                "possible_overrun": item.possible_overrun,
                "side_effects": item.side_effects,
                "residue_count": len(item.residue),
                "uncertainty_markers": item.uncertainty_markers,
            }
            for item in result.episodes
        ),
        "gate": {
            "episode_consumer_ready": result.gate.episode_consumer_ready,
            "boundary_consumer_ready": result.gate.boundary_consumer_ready,
            "verification_consumer_ready": result.gate.verification_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "p02_first_slice_only": result.scope_marker.p02_first_slice_only,
            "no_project_formation_authority": result.scope_marker.no_project_formation_authority,
            "no_action_licensing_authority": result.scope_marker.no_action_licensing_authority,
            "no_external_success_claim_without_evidence": (
                result.scope_marker.no_external_success_claim_without_evidence
            ),
            "no_memory_retention_authority": result.scope_marker.no_memory_retention_authority,
            "no_map_wide_rollout_claim": result.scope_marker.no_map_wide_rollout_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "episode_count": result.telemetry.episode_count,
            "completed_as_licensed_count": result.telemetry.completed_as_licensed_count,
            "partial_episode_count": result.telemetry.partial_episode_count,
            "blocked_episode_count": result.telemetry.blocked_episode_count,
            "awaiting_verification_count": result.telemetry.awaiting_verification_count,
            "overrun_detected_count": result.telemetry.overrun_detected_count,
            "boundary_ambiguous_count": result.telemetry.boundary_ambiguous_count,
            "residue_count": result.telemetry.residue_count,
            "side_effect_count": result.telemetry.side_effect_count,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
