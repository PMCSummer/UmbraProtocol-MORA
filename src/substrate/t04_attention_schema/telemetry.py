from __future__ import annotations

from substrate.t04_attention_schema.models import T04AttentionSchemaResult


def t04_attention_schema_snapshot(result: T04AttentionSchemaResult) -> dict[str, object]:
    if not isinstance(result, T04AttentionSchemaResult):
        raise TypeError("t04_attention_schema_snapshot requires T04AttentionSchemaResult")
    return {
        "state": {
            "schema_id": result.state.schema_id,
            "source_t03_competition_id": result.state.source_t03_competition_id,
            "focus_targets": tuple(
                {
                    "target_id": item.target_id,
                    "source_hypothesis_id": item.source_hypothesis_id,
                    "prominence_score": item.prominence_score,
                    "owner_confidence": item.owner_confidence,
                    "status": item.status.value,
                    "provenance": item.provenance,
                }
                for item in result.state.focus_targets
            ),
            "peripheral_targets": tuple(
                {
                    "target_id": item.target_id,
                    "source_hypothesis_id": item.source_hypothesis_id,
                    "prominence_score": item.prominence_score,
                    "owner_confidence": item.owner_confidence,
                    "status": item.status.value,
                    "provenance": item.provenance,
                }
                for item in result.state.peripheral_targets
            ),
            "attention_owner": result.state.attention_owner.value,
            "focus_mode": result.state.focus_mode.value,
            "control_estimate": result.state.control_estimate,
            "stability_estimate": result.state.stability_estimate,
            "redirect_cost": result.state.redirect_cost,
            "reportability_status": result.state.reportability_status.value,
            "source_authority_tags": result.state.source_authority_tags,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "focus_ownership_consumer_ready": result.gate.focus_ownership_consumer_ready,
            "reportable_focus_consumer_ready": result.gate.reportable_focus_consumer_ready,
            "peripheral_preservation_ready": result.gate.peripheral_preservation_ready,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "t04_first_slice_only": result.scope_marker.t04_first_slice_only,
            "o01_implemented": result.scope_marker.o01_implemented,
            "o02_implemented": result.scope_marker.o02_implemented,
            "o03_implemented": result.scope_marker.o03_implemented,
            "full_attention_line_implemented": result.scope_marker.full_attention_line_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "schema_id": result.telemetry.schema_id,
            "source_t03_competition_id": result.telemetry.source_t03_competition_id,
            "focus_targets_count": result.telemetry.focus_targets_count,
            "peripheral_targets_count": result.telemetry.peripheral_targets_count,
            "attention_owner": result.telemetry.attention_owner.value,
            "focus_mode": result.telemetry.focus_mode.value,
            "control_estimate": result.telemetry.control_estimate,
            "stability_estimate": result.telemetry.stability_estimate,
            "redirect_cost": result.telemetry.redirect_cost,
            "reportability_status": result.telemetry.reportability_status.value,
            "focus_ownership_consumer_ready": result.telemetry.focus_ownership_consumer_ready,
            "reportable_focus_consumer_ready": result.telemetry.reportable_focus_consumer_ready,
            "peripheral_preservation_ready": result.telemetry.peripheral_preservation_ready,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
