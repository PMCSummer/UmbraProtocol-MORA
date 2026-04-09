from __future__ import annotations

from substrate.n_minimal.models import NMinimalResult


def n_minimal_snapshot(result: NMinimalResult) -> dict[str, object]:
    if not isinstance(result, NMinimalResult):
        raise TypeError("n_minimal_snapshot requires NMinimalResult")
    return {
        "state": {
            "narrative_commitment_id": result.state.narrative_commitment_id,
            "commitment_status": result.state.commitment_status.value,
            "commitment_scope": result.state.commitment_scope,
            "narrative_basis_present": result.state.narrative_basis_present,
            "self_basis_present": result.state.self_basis_present,
            "world_basis_present": result.state.world_basis_present,
            "memory_basis_present": result.state.memory_basis_present,
            "capability_basis_present": result.state.capability_basis_present,
            "ambiguity_residue": result.state.ambiguity_residue,
            "contradiction_risk": result.state.contradiction_risk.value,
            "confidence": result.state.confidence,
            "degraded": result.state.degraded,
            "underconstrained": result.state.underconstrained,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "safe_narrative_commitment_allowed": (
                result.gate.safe_narrative_commitment_allowed
            ),
            "bounded_commitment_allowed": result.gate.bounded_commitment_allowed,
            "no_safe_narrative_claim": result.gate.no_safe_narrative_claim,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "admission": {
            "typed_narrative_commitment_surface_exists": (
                result.admission.typed_narrative_commitment_surface_exists
            ),
            "commitment_states_machine_readable": (
                result.admission.commitment_states_machine_readable
            ),
            "machine_readable_forbidden_shortcuts": (
                result.admission.machine_readable_forbidden_shortcuts
            ),
            "rt01_path_affecting_consumption_ready": (
                result.admission.rt01_path_affecting_consumption_ready
            ),
            "n01_implemented": result.admission.n01_implemented,
            "n02_implemented": result.admission.n02_implemented,
            "n03_implemented": result.admission.n03_implemented,
            "n04_implemented": result.admission.n04_implemented,
            "admission_ready_for_n01": result.admission.admission_ready_for_n01,
            "blockers": result.admission.blockers,
            "restrictions": result.admission.restrictions,
            "reason": result.admission.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "n_minimal_only": result.scope_marker.n_minimal_only,
            "readiness_gate_only": result.scope_marker.readiness_gate_only,
            "n01_implemented": result.scope_marker.n01_implemented,
            "n02_implemented": result.scope_marker.n02_implemented,
            "n03_implemented": result.scope_marker.n03_implemented,
            "n04_implemented": result.scope_marker.n04_implemented,
            "full_narrative_line_implemented": (
                result.scope_marker.full_narrative_line_implemented
            ),
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "narrative_commitment_id": result.telemetry.narrative_commitment_id,
            "commitment_status": result.telemetry.commitment_status.value,
            "commitment_scope": result.telemetry.commitment_scope,
            "ambiguity_residue": result.telemetry.ambiguity_residue,
            "contradiction_risk": result.telemetry.contradiction_risk.value,
            "confidence": result.telemetry.confidence,
            "degraded": result.telemetry.degraded,
            "underconstrained": result.telemetry.underconstrained,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "n01_admission_ready": result.telemetry.n01_admission_ready,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
