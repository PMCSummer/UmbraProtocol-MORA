from __future__ import annotations

from substrate.w02_regularity_extraction.models import W02ResultBundle


def w02_regularity_extraction_snapshot(result: W02ResultBundle) -> dict[str, object]:
    if not isinstance(result, W02ResultBundle):
        raise TypeError("w02_regularity_extraction_snapshot requires W02ResultBundle")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
        },
        "telemetry": {
            "trace_selection_count": result.telemetry.trace_selection_count,
            "candidate_count": result.telemetry.candidate_count,
            "promoted_count": result.telemetry.promoted_count,
            "blocked_count": result.telemetry.blocked_count,
            "contested_count": result.telemetry.contested_count,
            "downgraded_count": result.telemetry.downgraded_count,
            "contradiction_count": result.telemetry.contradiction_count,
            "lineage_ambiguity_count": result.telemetry.lineage_ambiguity_count,
            "must_abstain_count": result.telemetry.must_abstain_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "no_clean_regularities": result.telemetry.no_clean_regularities,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "clean_regularity_claim_allowed": result.gate.clean_regularity_claim_allowed,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "staged_regularity_only": result.scope_marker.staged_regularity_only,
            "no_mature_object_identity_claim": result.scope_marker.no_mature_object_identity_claim,
            "no_object_permanence_claim": result.scope_marker.no_object_permanence_claim,
            "no_scene_graph_truth_claim": result.scope_marker.no_scene_graph_truth_claim,
            "no_policy_selection_claim": result.scope_marker.no_policy_selection_claim,
            "reason": result.scope_marker.reason,
        },
    }
