from __future__ import annotations

from substrate.w04_applicability_gating.models import W04ResultBundle


def w04_applicability_gating_snapshot(result: W04ResultBundle) -> dict[str, object]:
    if not isinstance(result, W04ResultBundle):
        raise TypeError("w04_applicability_gating_snapshot requires W04ResultBundle")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
            "no_claim_markers": result.no_claim_markers,
        },
        "telemetry": {
            "desired_state_intake_count": result.telemetry.desired_state_intake_count,
            "w03_candidate_intake_count": result.telemetry.w03_candidate_intake_count,
            "applicability_decision_count": result.telemetry.applicability_decision_count,
            "allowed_count": result.telemetry.allowed_count,
            "blocked_count": result.telemetry.blocked_count,
            "narrowed_count": result.telemetry.narrowed_count,
            "hint_only_count": result.telemetry.hint_only_count,
            "revalidate_required_count": result.telemetry.revalidate_required_count,
            "abstain_count": result.telemetry.abstain_count,
            "relaxation_count": result.telemetry.relaxation_count,
            "hard_constraint_failure_count": result.telemetry.hard_constraint_failure_count,
            "unknown_hard_count": result.telemetry.unknown_hard_count,
            "malformed_desired_state_count": result.telemetry.malformed_desired_state_count,
            "perspective_block_count": result.telemetry.perspective_block_count,
            "authority_block_count": result.telemetry.authority_block_count,
            "stale_block_count": result.telemetry.stale_block_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "no_clean_applicability": result.telemetry.no_clean_applicability,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "no_clean_applicability": result.gate.no_clean_applicability,
            "blocked_count": result.gate.blocked_count,
            "revalidate_required_count": result.gate.revalidate_required_count,
            "abstain_count": result.gate.abstain_count,
            "hard_constraint_failure_count": result.gate.hard_constraint_failure_count,
            "unknown_hard_count": result.gate.unknown_hard_count,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "applicability_gating_only": result.scope_marker.applicability_gating_only,
            "no_planner_claim": result.scope_marker.no_planner_claim,
            "no_action_selector_claim": result.scope_marker.no_action_selector_claim,
            "no_world_model_expansion_claim": result.scope_marker.no_world_model_expansion_claim,
            "no_w05_or_w06_claim": result.scope_marker.no_w05_or_w06_claim,
            "reason": result.scope_marker.reason,
        },
    }
