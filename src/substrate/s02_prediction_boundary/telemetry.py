from __future__ import annotations

from substrate.s02_prediction_boundary.models import S02PredictionBoundaryResult


def s02_prediction_boundary_snapshot(result: S02PredictionBoundaryResult) -> dict[str, object]:
    if not isinstance(result, S02PredictionBoundaryResult):
        raise TypeError("s02_prediction_boundary_snapshot requires S02PredictionBoundaryResult")
    return {
        "state": {
            "boundary_id": result.state.boundary_id,
            "tick_index": result.state.tick_index,
            "active_boundary_status": result.state.active_boundary_status.value,
            "boundary_uncertain": result.state.boundary_uncertain,
            "insufficient_coverage": result.state.insufficient_coverage,
            "no_clean_seam_claim": result.state.no_clean_seam_claim,
            "seam_entries": tuple(
                {
                    "seam_entry_id": item.seam_entry_id,
                    "channel_or_effect_class": item.channel_or_effect_class,
                    "boundary_status": item.boundary_status.value,
                    "controllability_estimate": item.controllability_estimate,
                    "prediction_reliability_estimate": item.prediction_reliability_estimate,
                    "external_dominance_estimate": item.external_dominance_estimate,
                    "mixed_source_score": item.mixed_source_score,
                    "context_scope": item.context_scope,
                    "validity_marker": item.validity_marker,
                    "boundary_confidence": item.boundary_confidence,
                    "evidence_counters": {
                        "repeated_outcome_support": item.evidence_counters.repeated_outcome_support,
                        "matched_support": item.evidence_counters.matched_support,
                        "mismatch_support": item.evidence_counters.mismatch_support,
                        "contamination_support": item.evidence_counters.contamination_support,
                        "unexpected_residual_support": item.evidence_counters.unexpected_residual_support,
                        "internal_control_support": item.evidence_counters.internal_control_support,
                        "external_regularity_support": item.evidence_counters.external_regularity_support,
                    },
                    "provenance": item.provenance,
                    "last_boundary_update": item.last_boundary_update,
                }
                for item in result.state.seam_entries
            ),
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "boundary_consumer_ready": result.gate.boundary_consumer_ready,
            "controllability_consumer_ready": result.gate.controllability_consumer_ready,
            "mixed_source_consumer_ready": result.gate.mixed_source_consumer_ready,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "s02_first_slice_only": result.scope_marker.s02_first_slice_only,
            "s03_implemented": result.scope_marker.s03_implemented,
            "s04_implemented": result.scope_marker.s04_implemented,
            "s05_implemented": result.scope_marker.s05_implemented,
            "full_self_model_implemented": result.scope_marker.full_self_model_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "boundary_id": result.telemetry.boundary_id,
            "tick_index": result.telemetry.tick_index,
            "seam_entries_count": result.telemetry.seam_entries_count,
            "active_boundary_status": result.telemetry.active_boundary_status.value,
            "boundary_uncertain": result.telemetry.boundary_uncertain,
            "insufficient_coverage": result.telemetry.insufficient_coverage,
            "no_clean_seam_claim": result.telemetry.no_clean_seam_claim,
            "boundary_consumer_ready": result.telemetry.boundary_consumer_ready,
            "controllability_consumer_ready": result.telemetry.controllability_consumer_ready,
            "mixed_source_consumer_ready": result.telemetry.mixed_source_consumer_ready,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
