from __future__ import annotations

from substrate.w01_bounded_world_loop.models import W01Result


def w01_bounded_world_loop_snapshot(result: W01Result) -> dict[str, object]:
    if not isinstance(result, W01Result):
        raise TypeError("w01_bounded_world_loop_snapshot requires W01Result")
    return {
        "result": {
            "packet_set_id": result.packet_set_id,
            "packet_refs": result.packet_refs,
            "reason": result.reason,
        },
        "telemetry": {
            "packet_count": result.telemetry.packet_count,
            "admitted_count": result.telemetry.admitted_count,
            "admitted_with_uncertainty_count": result.telemetry.admitted_with_uncertainty_count,
            "scaffold_only_count": result.telemetry.scaffold_only_count,
            "absent_count": result.telemetry.absent_count,
            "contested_count": result.telemetry.contested_count,
            "rejected_count": result.telemetry.rejected_count,
            "revoked_count": result.telemetry.revoked_count,
            "contradiction_count": result.telemetry.contradiction_count,
            "linked_effect_count": result.telemetry.linked_effect_count,
            "no_link_count": result.telemetry.no_link_count,
            "source_authority_missing_count": result.telemetry.source_authority_missing_count,
            "non_mature_object_claim_count": result.telemetry.non_mature_object_claim_count,
            "consumer_ready_count": result.telemetry.consumer_ready_count,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "admission_required": result.gate.admission_required,
            "clean_world_claim_allowed": result.gate.clean_world_claim_allowed,
            "accepted_count": result.gate.accepted_count,
            "contested_count": result.gate.contested_count,
            "blocked_count": result.gate.blocked_count,
            "revoked_count": result.gate.revoked_count,
            "authority_missing_count": result.gate.authority_missing_count,
            "object_overclaim_blocked_count": result.gate.object_overclaim_blocked_count,
            "contradiction_count": result.gate.contradiction_count,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "staged_world_scaffold_only": result.scope_marker.staged_world_scaffold_only,
            "no_mature_object_claim": result.scope_marker.no_mature_object_claim,
            "no_object_permanence_claim": result.scope_marker.no_object_permanence_claim,
            "no_scene_graph_maturity_claim": result.scope_marker.no_scene_graph_maturity_claim,
            "no_policy_selection_claim": result.scope_marker.no_policy_selection_claim,
            "no_world_truth_claim": result.scope_marker.no_world_truth_claim,
            "reason": result.scope_marker.reason,
        },
    }
