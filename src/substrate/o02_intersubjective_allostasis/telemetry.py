from __future__ import annotations

from substrate.o02_intersubjective_allostasis.models import (
    O02IntersubjectiveAllostasisResult,
)


def o02_intersubjective_allostasis_snapshot(
    result: O02IntersubjectiveAllostasisResult,
) -> dict[str, object]:
    if not isinstance(result, O02IntersubjectiveAllostasisResult):
        raise TypeError(
            "o02_intersubjective_allostasis_snapshot requires O02IntersubjectiveAllostasisResult"
        )
    return {
        "state": {
            "regulation_id": result.state.regulation_id,
            "tick_index": result.state.tick_index,
            "interaction_mode": result.state.interaction_mode.value,
            "predicted_other_load": result.state.predicted_other_load.value,
            "predicted_self_load": result.state.predicted_self_load.value,
            "repair_pressure": result.state.repair_pressure.value,
            "detail_budget": result.state.detail_budget.value,
            "pace_budget": result.state.pace_budget.value,
            "clarification_threshold": result.state.clarification_threshold,
            "initiative_posture": result.state.initiative_posture,
            "uncertainty_notice_policy": result.state.uncertainty_notice_policy,
            "boundary_protection_status": result.state.boundary_protection_status.value,
            "other_model_reliance_status": result.state.other_model_reliance_status.value,
            "lever_preferences": tuple(item.value for item in result.state.lever_preferences),
            "justification_links": result.state.justification_links,
            "no_safe_regulation_claim": result.state.no_safe_regulation_claim,
            "other_load_underconstrained": result.state.other_load_underconstrained,
            "self_other_constraint_conflict": result.state.self_other_constraint_conflict,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "repair_sensitive_consumer_ready": result.gate.repair_sensitive_consumer_ready,
            "boundary_preserving_consumer_ready": result.gate.boundary_preserving_consumer_ready,
            "clarification_ready": result.gate.clarification_ready,
            "downstream_consumer_ready": result.gate.downstream_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "o02_first_slice_only": result.scope_marker.o02_first_slice_only,
            "o03_not_implemented": result.scope_marker.o03_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "regulation_id": result.telemetry.regulation_id,
            "tick_index": result.telemetry.tick_index,
            "interaction_mode": result.telemetry.interaction_mode.value,
            "predicted_other_load": result.telemetry.predicted_other_load.value,
            "predicted_self_load": result.telemetry.predicted_self_load.value,
            "repair_pressure": result.telemetry.repair_pressure.value,
            "detail_budget": result.telemetry.detail_budget.value,
            "pace_budget": result.telemetry.pace_budget.value,
            "boundary_protection_status": result.telemetry.boundary_protection_status.value,
            "other_model_reliance_status": result.telemetry.other_model_reliance_status.value,
            "no_safe_regulation_claim": result.telemetry.no_safe_regulation_claim,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
