from __future__ import annotations

from substrate.m02_predictive_relevance.models import M02Result


def m02_predictive_relevance_snapshot(result: M02Result) -> dict[str, object]:
    if not isinstance(result, M02Result):
        raise TypeError("m02_predictive_relevance_snapshot requires M02Result")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
        },
        "telemetry": {
            "trace_count": result.telemetry.trace_count,
            "predictive_mark_count": result.telemetry.predictive_mark_count,
            "clean_predictive_mark_count": result.telemetry.clean_predictive_mark_count,
            "weak_mark_count": result.telemetry.weak_mark_count,
            "context_locked_count": result.telemetry.context_locked_count,
            "spurious_risk_count": result.telemetry.spurious_risk_count,
            "no_safe_mark_count": result.telemetry.no_safe_mark_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "predictive_packet_consumer_ready": result.gate.predictive_packet_consumer_ready,
            "context_scope_consumer_ready": result.gate.context_scope_consumer_ready,
            "downstream_must_preserve_context": result.gate.downstream_must_preserve_context,
            "downstream_must_not_generalize": result.gate.downstream_must_not_generalize,
            "downstream_must_not_treat_as_generic_importance": result.gate.downstream_must_not_treat_as_generic_importance,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "predictive_relevance_not_generic_importance": result.scope_marker.predictive_relevance_not_generic_importance,
            "no_full_prediction_claim": result.scope_marker.no_full_prediction_claim,
            "no_full_memory_lifecycle_claim": result.scope_marker.no_full_memory_lifecycle_claim,
            "no_planner_policy_claim": result.scope_marker.no_planner_policy_claim,
            "separate_from_homeostatic_imprint": result.scope_marker.separate_from_homeostatic_imprint,
            "reason": result.scope_marker.reason,
        },
    }
