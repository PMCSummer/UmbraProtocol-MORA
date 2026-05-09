from __future__ import annotations

from substrate.n01_narrative_commitments.models import N01Result


def n01_narrative_commitment_snapshot(result: N01Result) -> dict[str, object]:
    if not isinstance(result, N01Result):
        raise TypeError("n01_narrative_commitment_snapshot requires N01Result")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
        },
        "telemetry": {
            "candidate_count": result.telemetry.candidate_count,
            "commitment_count": result.telemetry.commitment_count,
            "strong_commitment_count": result.telemetry.strong_commitment_count,
            "provisional_commitment_count": result.telemetry.provisional_commitment_count,
            "statement_only_count": result.telemetry.statement_only_count,
            "contested_commitment_count": result.telemetry.contested_commitment_count,
            "revised_count": result.telemetry.revised_count,
            "retired_count": result.telemetry.retired_count,
            "scope_narrowed_count": result.telemetry.scope_narrowed_count,
            "ungrounded_capability_claim_count": result.telemetry.ungrounded_capability_claim_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "consistency_consumer_ready": result.gate.consistency_consumer_ready,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "narrative_commitment_registry_only": result.scope_marker.narrative_commitment_registry_only,
            "no_identity_metaphysics_claim": result.scope_marker.no_identity_metaphysics_claim,
            "no_full_autobiography_claim": result.scope_marker.no_full_autobiography_claim,
            "no_memory_lifecycle_claim": result.scope_marker.no_memory_lifecycle_claim,
            "no_policy_selection_claim": result.scope_marker.no_policy_selection_claim,
            "reason": result.scope_marker.reason,
        },
    }
