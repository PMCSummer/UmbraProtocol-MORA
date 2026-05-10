from __future__ import annotations

from substrate.w03_schema_consolidation.models import W03ResultBundle


def w03_schema_consolidation_snapshot(result: W03ResultBundle) -> dict[str, object]:
    if not isinstance(result, W03ResultBundle):
        raise TypeError("w03_schema_consolidation_snapshot requires W03ResultBundle")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
            "no_claim_markers": result.no_claim_markers,
        },
        "telemetry": {
            "regularity_intake_count": result.telemetry.regularity_intake_count,
            "schema_candidate_count": result.telemetry.schema_candidate_count,
            "everyday_prior_count": result.telemetry.everyday_prior_count,
            "operational_default_count": result.telemetry.operational_default_count,
            "contested_count": result.telemetry.contested_count,
            "stale_count": result.telemetry.stale_count,
            "must_revalidate_count": result.telemetry.must_revalidate_count,
            "must_abstain_count": result.telemetry.must_abstain_count,
            "contradiction_count": result.telemetry.contradiction_count,
            "version_update_count": result.telemetry.version_update_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "no_clean_schema": result.telemetry.no_clean_schema,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "no_clean_schema": result.gate.no_clean_schema,
            "must_revalidate_count": result.gate.must_revalidate_count,
            "must_abstain_count": result.gate.must_abstain_count,
            "contradiction_count": result.gate.contradiction_count,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "schema_consolidation_only": result.scope_marker.schema_consolidation_only,
            "no_mature_world_truth_claim": result.scope_marker.no_mature_world_truth_claim,
            "no_common_sense_engine_claim": result.scope_marker.no_common_sense_engine_claim,
            "no_planner_claim": result.scope_marker.no_planner_claim,
            "no_memory_lifecycle_claim": result.scope_marker.no_memory_lifecycle_claim,
            "reason": result.scope_marker.reason,
        },
    }
