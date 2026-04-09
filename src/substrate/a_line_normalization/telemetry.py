from __future__ import annotations

from substrate.a_line_normalization.models import ALineNormalizationResult


def a_line_normalization_snapshot(result: ALineNormalizationResult) -> dict[str, object]:
    if not isinstance(result, ALineNormalizationResult):
        raise TypeError("a_line_normalization_snapshot requires ALineNormalizationResult")
    return {
        "state": {
            "capability_id": result.state.capability_id,
            "affordance_id": result.state.affordance_id,
            "capability_class": result.state.capability_class.value,
            "capability_status": result.state.capability_status.value,
            "availability_basis_present": result.state.availability_basis_present,
            "world_dependency_present": result.state.world_dependency_present,
            "self_dependency_present": result.state.self_dependency_present,
            "controllability_dependency_present": (
                result.state.controllability_dependency_present
            ),
            "legitimacy_dependency_present": result.state.legitimacy_dependency_present,
            "confidence": result.state.confidence,
            "degraded": result.state.degraded,
            "underconstrained": result.state.underconstrained,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "available_capability_claim_allowed": result.gate.available_capability_claim_allowed,
            "world_conditioned_capability_claim_allowed": (
                result.gate.world_conditioned_capability_claim_allowed
            ),
            "self_conditioned_capability_claim_allowed": (
                result.gate.self_conditioned_capability_claim_allowed
            ),
            "policy_conditioned_capability_present": (
                result.gate.policy_conditioned_capability_present
            ),
            "underconstrained_capability": result.gate.underconstrained_capability,
            "no_safe_capability_claim": result.gate.no_safe_capability_claim,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "a04_readiness": {
            "typed_a01_a03_substrate_exists": (
                result.a04_readiness.typed_a01_a03_substrate_exists
            ),
            "capability_states_machine_readable": (
                result.a04_readiness.capability_states_machine_readable
            ),
            "dependency_linkage_world_self_policy_inspectable": (
                result.a04_readiness.dependency_linkage_world_self_policy_inspectable
            ),
            "structurally_present_but_not_ready": (
                result.a04_readiness.structurally_present_but_not_ready
            ),
            "capability_basis_missing": result.a04_readiness.capability_basis_missing,
            "world_dependency_unmet": result.a04_readiness.world_dependency_unmet,
            "self_dependency_unmet": result.a04_readiness.self_dependency_unmet,
            "policy_legitimacy_unmet": result.a04_readiness.policy_legitimacy_unmet,
            "underconstrained_capability_surface": (
                result.a04_readiness.underconstrained_capability_surface
            ),
            "external_means_not_justified": (
                result.a04_readiness.external_means_not_justified
            ),
            "forbidden_shortcuts_machine_readable": (
                result.a04_readiness.forbidden_shortcuts_machine_readable
            ),
            "rt01_path_affecting_consumption_ready": (
                result.a04_readiness.rt01_path_affecting_consumption_ready
            ),
            "a04_implemented": result.a04_readiness.a04_implemented,
            "a05_touched": result.a04_readiness.a05_touched,
            "admission_ready_for_a04": result.a04_readiness.admission_ready_for_a04,
            "blockers": result.a04_readiness.blockers,
            "restrictions": result.a04_readiness.restrictions,
            "reason": result.a04_readiness.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "a_line_normalization_only": result.scope_marker.a_line_normalization_only,
            "readiness_gate_only": result.scope_marker.readiness_gate_only,
            "a04_implemented": result.scope_marker.a04_implemented,
            "a05_touched": result.scope_marker.a05_touched,
            "full_agency_stack_implemented": (
                result.scope_marker.full_agency_stack_implemented
            ),
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "capability_id": result.telemetry.capability_id,
            "capability_status": result.telemetry.capability_status.value,
            "capability_class": result.telemetry.capability_class.value,
            "confidence": result.telemetry.confidence,
            "degraded": result.telemetry.degraded,
            "underconstrained": result.telemetry.underconstrained,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "a04_admission_ready": result.telemetry.a04_admission_ready,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
