from __future__ import annotations

from substrate.s01_efference_copy.models import S01EfferenceCopyResult


def s01_efference_copy_snapshot(result: S01EfferenceCopyResult) -> dict[str, object]:
    if not isinstance(result, S01EfferenceCopyResult):
        raise TypeError("s01_efference_copy_snapshot requires S01EfferenceCopyResult")
    return {
        "state": {
            "efference_id": result.state.efference_id,
            "tick_index": result.state.tick_index,
            "pending_predictions": tuple(
                {
                    "prediction_id": item.prediction_id,
                    "packet_id": item.packet_id,
                    "source_kind": item.source_kind.value,
                    "source_ref": item.source_ref,
                    "axis": item.axis.value,
                    "created_tick": item.created_tick,
                    "earliest_tick": item.earliest_tick,
                    "preferred_tick": item.preferred_tick,
                    "expires_tick": item.expires_tick,
                    "expected_bool": item.expected_bool,
                    "expected_token": item.expected_token,
                    "expected_direction": item.expected_direction,
                    "expected_magnitude": item.expected_magnitude,
                    "tolerance": item.tolerance,
                    "baseline_value": item.baseline_value,
                    "contamination_sensitive": item.contamination_sensitive,
                }
                for item in result.state.pending_predictions
            ),
            "forward_packets": tuple(
                {
                    "packet_id": item.packet_id,
                    "intended_change": item.intended_change,
                    "expected_consequence": item.expected_consequence,
                    "action_context": item.action_context,
                    "timing_window": item.timing_window,
                    "mismatch_hooks": item.mismatch_hooks,
                    "created_tick": item.created_tick,
                    "expires_tick": item.expires_tick,
                    "source_ref": item.source_ref,
                }
                for item in result.state.forward_packets
            ),
            "comparisons": tuple(
                {
                    "comparison_id": item.comparison_id,
                    "prediction_id": item.prediction_id,
                    "axis": item.axis.value,
                    "status": item.status.value,
                    "attribution_status": item.attribution_status.value,
                    "observed_tick": item.observed_tick,
                    "latency_ticks": item.latency_ticks,
                    "magnitude_error": item.magnitude_error,
                    "observed_direction": item.observed_direction,
                    "contamination_markers": item.contamination_markers,
                    "reason": item.reason,
                }
                for item in result.state.comparisons
            ),
            "latest_comparison_status": (
                None
                if result.state.latest_comparison_status is None
                else result.state.latest_comparison_status.value
            ),
            "comparison_blocked_by_contamination": (
                result.state.comparison_blocked_by_contamination
            ),
            "stale_prediction_detected": result.state.stale_prediction_detected,
            "unexpected_change_detected": result.state.unexpected_change_detected,
            "strong_self_attribution_allowed": result.state.strong_self_attribution_allowed,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "comparison_ready": result.gate.comparison_ready,
            "prediction_validity_ready": result.gate.prediction_validity_ready,
            "unexpected_change_detected": result.gate.unexpected_change_detected,
            "no_post_hoc_prediction_fabrication": (
                result.gate.no_post_hoc_prediction_fabrication
            ),
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "s01_first_slice_only": result.scope_marker.s01_first_slice_only,
            "s02_implemented": result.scope_marker.s02_implemented,
            "s03_implemented": result.scope_marker.s03_implemented,
            "s04_implemented": result.scope_marker.s04_implemented,
            "s05_implemented": result.scope_marker.s05_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "efference_id": result.telemetry.efference_id,
            "tick_index": result.telemetry.tick_index,
            "pending_predictions_count": result.telemetry.pending_predictions_count,
            "comparisons_count": result.telemetry.comparisons_count,
            "latest_comparison_status": result.telemetry.latest_comparison_status,
            "comparison_blocked_by_contamination": (
                result.telemetry.comparison_blocked_by_contamination
            ),
            "stale_prediction_detected": result.telemetry.stale_prediction_detected,
            "unexpected_change_detected": result.telemetry.unexpected_change_detected,
            "no_post_hoc_prediction_fabrication": (
                result.telemetry.no_post_hoc_prediction_fabrication
            ),
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
