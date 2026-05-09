from __future__ import annotations

from substrate.m01_homeostatic_salience_imprint.models import M01Result


def m01_homeostatic_salience_imprint_snapshot(result: M01Result) -> dict[str, object]:
    if not isinstance(result, M01Result):
        raise TypeError("m01_homeostatic_salience_imprint_snapshot requires M01Result")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
        },
        "telemetry": {
            "trace_count": result.telemetry.trace_count,
            "imprint_count": result.telemetry.imprint_count,
            "strong_imprint_count": result.telemetry.strong_imprint_count,
            "weak_or_no_claim_count": result.telemetry.weak_or_no_claim_count,
            "attribution_limited_count": result.telemetry.attribution_limited_count,
            "recovery_imprint_count": result.telemetry.recovery_imprint_count,
            "no_safe_imprint_count": result.telemetry.no_safe_imprint_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "imprint_packet_consumer_ready": result.gate.imprint_packet_consumer_ready,
            "axis_scope_consumer_ready": result.gate.axis_scope_consumer_ready,
            "no_safe_imprint_claim": result.gate.no_safe_imprint_claim,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "homeostatic_imprint_not_general_importance": result.scope_marker.homeostatic_imprint_not_general_importance,
            "not_reward_function": result.scope_marker.not_reward_function,
            "not_narrative_relevance": result.scope_marker.not_narrative_relevance,
            "not_full_memory_system": result.scope_marker.not_full_memory_system,
            "no_policy_claim": result.scope_marker.no_policy_claim,
            "no_global_value_claim": result.scope_marker.no_global_value_claim,
            "reason": result.scope_marker.reason,
        },
    }
