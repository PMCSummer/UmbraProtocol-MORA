from __future__ import annotations

from substrate.a04_external_affordance_binding.models import (
    A04ExternalAffordanceBindingResult,
)


def a04_external_affordance_binding_snapshot(
    result: A04ExternalAffordanceBindingResult,
) -> dict[str, object]:
    if not isinstance(result, A04ExternalAffordanceBindingResult):
        raise TypeError(
            "a04_external_affordance_binding_snapshot requires A04ExternalAffordanceBindingResult"
        )
    return {
        "result": {
            "candidate_set_id": result.candidate_set_id,
            "reason": result.reason,
        },
        "ledger": {
            "accepted_count": result.ledger.accepted_count,
            "contested_count": result.ledger.contested_count,
            "blocked_count": result.ledger.blocked_count,
            "revoked_count": result.ledger.revoked_count,
            "authority_missing_count": result.ledger.authority_missing_count,
            "object_overclaim_blocked_count": result.ledger.object_overclaim_blocked_count,
            "contradiction_count": result.ledger.contradiction_count,
            "reason": result.ledger.reason,
        },
        "gate": {
            "binding_packet_consumer_ready": result.gate.binding_packet_consumer_ready,
            "authority_path_consumer_ready": result.gate.authority_path_consumer_ready,
            "consumer_ready": result.gate.consumer_ready,
            "downstream_readiness_status": result.gate.downstream_readiness_status.value,
            "required_restrictions": result.gate.required_restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "staged_scaffold_only": result.scope_marker.staged_scaffold_only,
            "entity_binding_not_object_perception": result.scope_marker.entity_binding_not_object_perception,
            "no_map_wide_claim": result.scope_marker.no_map_wide_claim,
            "no_execution_claim": result.scope_marker.no_execution_claim,
            "no_policy_selection_claim": result.scope_marker.no_policy_selection_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "a04_binding_count": result.telemetry.a04_binding_count,
            "a04_contested_count": result.telemetry.a04_contested_count,
            "a04_blocked_count": result.telemetry.a04_blocked_count,
            "a04_revoked_count": result.telemetry.a04_revoked_count,
            "a04_authority_missing_count": result.telemetry.a04_authority_missing_count,
            "a04_object_overclaim_blocked_count": result.telemetry.a04_object_overclaim_blocked_count,
            "a04_consumer_ready": result.telemetry.a04_consumer_ready,
            "a04_staged_scaffold_only": result.telemetry.a04_staged_scaffold_only,
            "a04_no_map_wide_claim": result.telemetry.a04_no_map_wide_claim,
            "emitted_at": result.telemetry.emitted_at,
        },
    }
