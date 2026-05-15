from __future__ import annotations

from substrate.w05_predictive_prior_injection.models import W05ResultBundle


def w05_predictive_prior_injection_snapshot(result: W05ResultBundle) -> dict[str, object]:
    if not isinstance(result, W05ResultBundle):
        raise TypeError("w05_predictive_prior_injection_snapshot requires W05ResultBundle")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
            "no_claim_markers": result.no_claim_markers,
        },
        "telemetry": {
            "signal_stack_count": result.telemetry.signal_stack_count,
            "prediction_use_count": result.telemetry.prediction_use_count,
            "prior_gain_suppressed_count": result.telemetry.prior_gain_suppressed_count,
            "prior_gain_amplified_count": result.telemetry.prior_gain_amplified_count,
            "prior_gain_unchanged_count": result.telemetry.prior_gain_unchanged_count,
            "mismatch_count": result.telemetry.mismatch_count,
            "ambiguous_mismatch_count": result.telemetry.ambiguous_mismatch_count,
            "revalidate_route_count": result.telemetry.revalidate_route_count,
            "escalate_route_count": result.telemetry.escalate_route_count,
            "abstain_count": result.telemetry.abstain_count,
            "constitutional_guard_count": result.telemetry.constitutional_guard_count,
            "protected_target_block_count": result.telemetry.protected_target_block_count,
            "must_not_execute_update_count": result.telemetry.must_not_execute_update_count,
            "permitted_channel_block_count": result.telemetry.permitted_channel_block_count,
            "channel_collapse_block_count": result.telemetry.channel_collapse_block_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "no_clean_routing": result.telemetry.no_clean_routing,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "no_clean_routing": result.gate.no_clean_routing,
            "must_not_execute_update_count": result.gate.must_not_execute_update_count,
            "revalidate_route_count": result.gate.revalidate_route_count,
            "escalate_route_count": result.gate.escalate_route_count,
            "abstain_count": result.gate.abstain_count,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "prior_injection_only": result.scope_marker.prior_injection_only,
            "no_w06_revision_claim": result.scope_marker.no_w06_revision_claim,
            "no_planner_claim": result.scope_marker.no_planner_claim,
            "no_action_selector_claim": result.scope_marker.no_action_selector_claim,
            "no_execution_claim": result.scope_marker.no_execution_claim,
            "reason": result.scope_marker.reason,
        },
    }
