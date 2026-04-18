from __future__ import annotations

from substrate.r05_appraisal_sovereign_protective_regulation.models import (
    R05ProtectiveResult,
)


def r05_appraisal_sovereign_protective_regulation_snapshot(
    result: R05ProtectiveResult,
) -> dict[str, object]:
    if not isinstance(result, R05ProtectiveResult):
        raise TypeError(
            "r05_appraisal_sovereign_protective_regulation_snapshot requires R05ProtectiveResult"
        )
    return {
        "state": {
            "regulation_id": result.state.regulation_id,
            "protective_mode": result.state.protective_mode.value,
            "authority_level": result.state.authority_level.value,
            "trigger_ids": result.state.trigger_ids,
            "trigger_count": result.state.trigger_count,
            "structural_basis_score": result.state.structural_basis_score,
            "inhibited_surfaces": tuple(item.value for item in result.state.inhibited_surfaces),
            "project_override_active": result.state.project_override_active,
            "override_scope": result.state.override_scope,
            "release_pending": result.state.release_pending,
            "release_conditions": result.state.release_conditions,
            "release_satisfied": result.state.release_satisfied,
            "recovery_recheck_due": result.state.recovery_recheck_due,
            "hysteresis_hold_ticks": result.state.hysteresis_hold_ticks,
            "regulation_conflict": result.state.regulation_conflict,
            "insufficient_basis_for_override": result.state.insufficient_basis_for_override,
            "justification_links": result.state.justification_links,
            "provenance": result.state.provenance,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "protective_state_consumer_ready": result.gate.protective_state_consumer_ready,
            "surface_inhibition_consumer_ready": result.gate.surface_inhibition_consumer_ready,
            "release_contract_consumer_ready": result.gate.release_contract_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "r05_first_slice_only": result.scope_marker.r05_first_slice_only,
            "a05_not_implemented": result.scope_marker.a05_not_implemented,
            "v_line_not_implemented": result.scope_marker.v_line_not_implemented,
            "p04_not_implemented": result.scope_marker.p04_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "regulation_id": result.telemetry.regulation_id,
            "tick_index": result.telemetry.tick_index,
            "protective_mode": result.telemetry.protective_mode.value,
            "authority_level": result.telemetry.authority_level.value,
            "trigger_count": result.telemetry.trigger_count,
            "inhibited_surface_count": result.telemetry.inhibited_surface_count,
            "override_active": result.telemetry.override_active,
            "release_pending": result.telemetry.release_pending,
            "regulation_conflict": result.telemetry.regulation_conflict,
            "insufficient_basis_for_override": (
                result.telemetry.insufficient_basis_for_override
            ),
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "project_override_active": result.telemetry.project_override_active,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
