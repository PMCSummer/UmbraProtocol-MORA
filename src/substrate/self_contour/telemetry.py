from __future__ import annotations

from substrate.self_contour.models import SMinimalContourResult


def s_minimal_contour_snapshot(result: SMinimalContourResult) -> dict[str, object]:
    if not isinstance(result, SMinimalContourResult):
        raise TypeError("s_minimal_contour_snapshot requires SMinimalContourResult")
    return {
        "state": {
            "boundary_state_id": result.state.boundary_state_id,
            "self_attribution_basis_present": result.state.self_attribution_basis_present,
            "world_attribution_basis_present": result.state.world_attribution_basis_present,
            "controllability_estimate": result.state.controllability_estimate,
            "ownership_estimate": result.state.ownership_estimate,
            "attribution_confidence": result.state.attribution_confidence,
            "internal_vs_external_source_status": result.state.internal_vs_external_source_status.value,
            "boundary_breach_risk": result.state.boundary_breach_risk.value,
            "attribution_class": result.state.attribution_class.value,
            "no_safe_self_claim": result.state.no_safe_self_claim,
            "no_safe_world_claim": result.state.no_safe_world_claim,
            "degraded": result.state.degraded,
            "underconstrained": result.state.underconstrained,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "self_owned_state_claim_allowed": result.gate.self_owned_state_claim_allowed,
            "self_caused_change_claim_allowed": result.gate.self_caused_change_claim_allowed,
            "self_controlled_transition_claim_allowed": result.gate.self_controlled_transition_claim_allowed,
            "externally_caused_change_claim_allowed": result.gate.externally_caused_change_claim_allowed,
            "world_caused_perturbation_claim_allowed": result.gate.world_caused_perturbation_claim_allowed,
            "mixed_or_underconstrained_attribution": result.gate.mixed_or_underconstrained_attribution,
            "no_safe_self_claim": result.gate.no_safe_self_claim,
            "no_safe_world_claim": result.gate.no_safe_world_claim,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "admission": {
            "s_minimal_contour_materialized": result.admission.s_minimal_contour_materialized,
            "typed_boundary_surface_exists": result.admission.typed_boundary_surface_exists,
            "ownership_controllability_discipline_exists": (
                result.admission.ownership_controllability_discipline_exists
            ),
            "self_attribution_basis_sufficient": result.admission.self_attribution_basis_sufficient,
            "controllability_basis_sufficient": result.admission.controllability_basis_sufficient,
            "ownership_basis_sufficient": result.admission.ownership_basis_sufficient,
            "attribution_underconstrained": result.admission.attribution_underconstrained,
            "mixed_boundary_instability": result.admission.mixed_boundary_instability,
            "no_safe_self_basis": result.admission.no_safe_self_basis,
            "no_safe_world_basis": result.admission.no_safe_world_basis,
            "forbidden_shortcuts_machine_readable": (
                result.admission.forbidden_shortcuts_machine_readable
            ),
            "rt01_path_affecting_consumption_ready": (
                result.admission.rt01_path_affecting_consumption_ready
            ),
            "future_s01_s05_remain_open": result.admission.future_s01_s05_remain_open,
            "full_self_model_implemented": result.admission.full_self_model_implemented,
            "admission_ready_for_s01": result.admission.admission_ready_for_s01,
            "readiness_blockers": result.admission.readiness_blockers,
            "restrictions": result.admission.restrictions,
            "reason": result.admission.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "s_minimal_only": result.scope_marker.s_minimal_only,
            "s01_implemented": result.scope_marker.s01_implemented,
            "s_line_implemented": result.scope_marker.s_line_implemented,
            "minimal_contour_only": result.scope_marker.minimal_contour_only,
            "s01_s05_implemented": result.scope_marker.s01_s05_implemented,
            "full_self_model_implemented": result.scope_marker.full_self_model_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "boundary_state_id": result.telemetry.boundary_state_id,
            "attribution_class": result.telemetry.attribution_class.value,
            "source_status": result.telemetry.source_status.value,
            "boundary_breach_risk": result.telemetry.boundary_breach_risk.value,
            "controllability_estimate": result.telemetry.controllability_estimate,
            "ownership_estimate": result.telemetry.ownership_estimate,
            "attribution_confidence": result.telemetry.attribution_confidence,
            "degraded": result.telemetry.degraded,
            "underconstrained": result.telemetry.underconstrained,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
