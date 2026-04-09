from __future__ import annotations

from substrate.m_minimal.models import MMinimalResult


def m_minimal_snapshot(result: MMinimalResult) -> dict[str, object]:
    if not isinstance(result, MMinimalResult):
        raise TypeError("m_minimal_snapshot requires MMinimalResult")
    return {
        "state": {
            "memory_item_id": result.state.memory_item_id,
            "memory_packet_id": result.state.memory_packet_id,
            "lifecycle_status": result.state.lifecycle_status.value,
            "retention_class": result.state.retention_class.value,
            "bounded_persistence_allowed": result.state.bounded_persistence_allowed,
            "temporary_carry_allowed": result.state.temporary_carry_allowed,
            "review_required": result.state.review_required,
            "reactivation_eligible": result.state.reactivation_eligible,
            "decay_eligible": result.state.decay_eligible,
            "pruning_eligible": result.state.pruning_eligible,
            "stale_risk": result.state.stale_risk.value,
            "conflict_risk": result.state.conflict_risk.value,
            "confidence": result.state.confidence,
            "reliability": result.state.reliability,
            "degraded": result.state.degraded,
            "underconstrained": result.state.underconstrained,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "safe_memory_claim_allowed": result.gate.safe_memory_claim_allowed,
            "bounded_retained_claim_allowed": result.gate.bounded_retained_claim_allowed,
            "no_safe_memory_claim": result.gate.no_safe_memory_claim,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "admission": {
            "typed_memory_lifecycle_surface_exists": (
                result.admission.typed_memory_lifecycle_surface_exists
            ),
            "lifecycle_states_machine_readable": (
                result.admission.lifecycle_states_machine_readable
            ),
            "safe_lifecycle_discipline_materialized": (
                result.admission.safe_lifecycle_discipline_materialized
            ),
            "machine_readable_forbidden_shortcuts": (
                result.admission.machine_readable_forbidden_shortcuts
            ),
            "rt01_path_affecting_consumption_ready": (
                result.admission.rt01_path_affecting_consumption_ready
            ),
            "m01_implemented": result.admission.m01_implemented,
            "m02_implemented": result.admission.m02_implemented,
            "m03_implemented": result.admission.m03_implemented,
            "admission_ready_for_m01": result.admission.admission_ready_for_m01,
            "structurally_present_but_not_ready": (
                result.admission.structurally_present_but_not_ready
            ),
            "stale_risk_unacceptable": result.admission.stale_risk_unacceptable,
            "conflict_risk_unacceptable": result.admission.conflict_risk_unacceptable,
            "reactivation_requires_review": (
                result.admission.reactivation_requires_review
            ),
            "temporary_carry_not_stable_enough": (
                result.admission.temporary_carry_not_stable_enough
            ),
            "no_safe_memory_basis": result.admission.no_safe_memory_basis,
            "provenance_insufficient": result.admission.provenance_insufficient,
            "lifecycle_underconstrained": result.admission.lifecycle_underconstrained,
            "blockers": result.admission.blockers,
            "restrictions": result.admission.restrictions,
            "reason": result.admission.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "m_minimal_only": result.scope_marker.m_minimal_only,
            "readiness_gate_only": result.scope_marker.readiness_gate_only,
            "m01_implemented": result.scope_marker.m01_implemented,
            "m02_implemented": result.scope_marker.m02_implemented,
            "m03_implemented": result.scope_marker.m03_implemented,
            "full_memory_stack_implemented": (
                result.scope_marker.full_memory_stack_implemented
            ),
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "memory_item_id": result.telemetry.memory_item_id,
            "lifecycle_status": result.telemetry.lifecycle_status.value,
            "retention_class": result.telemetry.retention_class.value,
            "stale_risk": result.telemetry.stale_risk.value,
            "conflict_risk": result.telemetry.conflict_risk.value,
            "confidence": result.telemetry.confidence,
            "reliability": result.telemetry.reliability,
            "degraded": result.telemetry.degraded,
            "underconstrained": result.telemetry.underconstrained,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "m01_admission_ready": result.telemetry.m01_admission_ready,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
