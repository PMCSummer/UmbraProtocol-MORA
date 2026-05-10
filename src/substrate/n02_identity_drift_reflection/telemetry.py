from __future__ import annotations

from substrate.n02_identity_drift_reflection.models import N02Result


def n02_identity_drift_snapshot(result: N02Result) -> dict[str, object]:
    if not isinstance(result, N02Result):
        raise TypeError("n02_identity_drift_snapshot requires N02Result")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
        },
        "telemetry": {
            "baseline_count": result.telemetry.baseline_count,
            "current_reference_count": result.telemetry.current_reference_count,
            "substrate_change_count": result.telemetry.substrate_change_count,
            "drift_entry_count": result.telemetry.drift_entry_count,
            "stable_continuation_count": result.telemetry.stable_continuation_count,
            "bounded_revision_count": result.telemetry.bounded_revision_count,
            "reflection_needed_count": result.telemetry.reflection_needed_count,
            "unresolved_identity_tension_count": result.telemetry.unresolved_identity_tension_count,
            "context_split_count": result.telemetry.context_split_count,
            "no_clean_drift_count": result.telemetry.no_clean_drift_count,
            "baseline_uncertain_count": result.telemetry.baseline_uncertain_count,
            "overreflection_guard_count": result.telemetry.overreflection_guard_count,
            "text_diff_only_blocked_count": result.telemetry.text_diff_only_blocked_count,
            "substrate_ablation_or_missing_count": result.telemetry.substrate_ablation_or_missing_count,
            "downstream_caution_count": result.telemetry.downstream_caution_count,
            "n02_consumer_ready": result.telemetry.n02_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "n02_consumer_ready": result.gate.n02_consumer_ready,
            "reflection_consumer_ready": result.gate.reflection_consumer_ready,
            "consistency_consumer_ready": result.gate.consistency_consumer_ready,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "identity_drift_reflection_registry_only": result.scope_marker.identity_drift_reflection_registry_only,
            "no_metaphysical_identity_claim": result.scope_marker.no_metaphysical_identity_claim,
            "no_autobiographical_relevance_claim": result.scope_marker.no_autobiographical_relevance_claim,
            "no_memory_lifecycle_claim": result.scope_marker.no_memory_lifecycle_claim,
            "no_user_model_claim": result.scope_marker.no_user_model_claim,
            "no_commitment_rewrite_claim": result.scope_marker.no_commitment_rewrite_claim,
            "reason": result.scope_marker.reason,
        },
    }
