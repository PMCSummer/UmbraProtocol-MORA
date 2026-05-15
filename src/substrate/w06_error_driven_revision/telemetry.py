from __future__ import annotations

from substrate.w06_error_driven_revision.models import W06ResultBundle


def w06_error_driven_revision_snapshot(result: W06ResultBundle) -> dict[str, object]:
    if not isinstance(result, W06ResultBundle):
        raise TypeError("w06_error_driven_revision_snapshot requires W06ResultBundle")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
            "no_claim_markers": result.no_claim_markers,
        },
        "decision": {
            "revision_id": result.decision.revision_id,
            "consequence_type": result.decision.consequence_type.value,
            "revision_scope": result.decision.revision_scope.value,
            "route_status": result.decision.route_status.value,
            "severity": result.decision.severity,
            "confidence": result.decision.confidence,
            "blocked_claims": result.decision.blocked_claims,
            "decision_reason_codes": result.decision.decision_reason_codes,
        },
        "telemetry": {
            "mismatch_intake_count": result.telemetry.mismatch_intake_count,
            "contradiction_intake_count": result.telemetry.contradiction_intake_count,
            "consequence_matrix_count": result.telemetry.consequence_matrix_count,
            "revision_scope_count": result.telemetry.revision_scope_count,
            "confidence_policy_count": result.telemetry.confidence_policy_count,
            "residue_retention_count": result.telemetry.residue_retention_count,
            "anti_paralysis_count": result.telemetry.anti_paralysis_count,
            "identity_route_count": result.telemetry.identity_route_count,
            "correction_candidate_count": result.telemetry.correction_candidate_count,
            "downstream_packet_count": result.telemetry.downstream_packet_count,
            "revalidate_count": result.telemetry.revalidate_count,
            "downgrade_count": result.telemetry.downgrade_count,
            "invalidate_count": result.telemetry.invalidate_count,
            "split_identity_count": result.telemetry.split_identity_count,
            "block_claim_count": result.telemetry.block_claim_count,
            "quarantine_count": result.telemetry.quarantine_count,
            "retain_unresolved_count": result.telemetry.retain_unresolved_count,
            "global_scope_count": result.telemetry.global_scope_count,
            "local_scope_count": result.telemetry.local_scope_count,
            "confidence_drop_count": result.telemetry.confidence_drop_count,
            "must_not_execute_correction": result.telemetry.must_not_execute_correction,
            "claim_blocked": result.telemetry.claim_blocked,
            "consumer_ready": result.telemetry.consumer_ready,
            "no_clean_revision": result.telemetry.no_clean_revision,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "no_clean_revision": result.gate.no_clean_revision,
            "must_not_execute_correction": result.gate.must_not_execute_correction,
            "must_block_claim": result.gate.must_block_claim,
            "must_revalidate": result.gate.must_revalidate,
            "must_escalate": result.gate.must_escalate,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "revision_routing_only": result.scope_marker.revision_routing_only,
            "no_update_execution_claim": result.scope_marker.no_update_execution_claim,
            "no_planner_claim": result.scope_marker.no_planner_claim,
            "no_action_selector_claim": result.scope_marker.no_action_selector_claim,
            "no_schema_mutation_claim": result.scope_marker.no_schema_mutation_claim,
            "reason": result.scope_marker.reason,
        },
    }
