from __future__ import annotations

from substrate.v01_normative_permission_commitment_licensing.models import V01LicenseResult


def v01_normative_permission_commitment_licensing_snapshot(
    result: V01LicenseResult,
) -> dict[str, object]:
    if not isinstance(result, V01LicenseResult):
        raise TypeError(
            "v01_normative_permission_commitment_licensing_snapshot requires V01LicenseResult"
        )
    return {
        "state": {
            "license_id": result.state.license_id,
            "candidate_act_count": result.state.candidate_act_count,
            "licensed_act_count": result.state.licensed_act_count,
            "denied_act_count": result.state.denied_act_count,
            "conditional_act_count": result.state.conditional_act_count,
            "commitment_delta_count": result.state.commitment_delta_count,
            "mandatory_qualifier_count": result.state.mandatory_qualifier_count,
            "protective_defer_required": result.state.protective_defer_required,
            "insufficient_license_basis": result.state.insufficient_license_basis,
            "qualification_required": result.state.qualification_required,
            "assertion_allowed_commitment_denied": (
                result.state.assertion_allowed_commitment_denied
            ),
            "clarification_before_commitment": result.state.clarification_before_commitment,
            "cannot_license_advice": result.state.cannot_license_advice,
            "promise_like_act_denied": result.state.promise_like_act_denied,
            "alternative_narrowed_act_available": (
                result.state.alternative_narrowed_act_available
            ),
            "justification_links": result.state.justification_links,
            "provenance": result.state.provenance,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "license_consumer_ready": result.gate.license_consumer_ready,
            "commitment_delta_consumer_ready": result.gate.commitment_delta_consumer_ready,
            "qualifier_binding_consumer_ready": result.gate.qualifier_binding_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "v01_first_slice_only": result.scope_marker.v01_first_slice_only,
            "v02_not_implemented": result.scope_marker.v02_not_implemented,
            "v03_not_implemented": result.scope_marker.v03_not_implemented,
            "p02_not_implemented": result.scope_marker.p02_not_implemented,
            "p04_not_implemented": result.scope_marker.p04_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "license_id": result.telemetry.license_id,
            "tick_index": result.telemetry.tick_index,
            "candidate_act_count": result.telemetry.candidate_act_count,
            "licensed_act_count": result.telemetry.licensed_act_count,
            "denied_act_count": result.telemetry.denied_act_count,
            "conditional_act_count": result.telemetry.conditional_act_count,
            "commitment_delta_count": result.telemetry.commitment_delta_count,
            "mandatory_qualifier_count": result.telemetry.mandatory_qualifier_count,
            "protective_defer_required": result.telemetry.protective_defer_required,
            "insufficient_license_basis": result.telemetry.insufficient_license_basis,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "promise_like_act_denied": result.telemetry.promise_like_act_denied,
            "alternative_narrowed_act_available": (
                result.telemetry.alternative_narrowed_act_available
            ),
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
