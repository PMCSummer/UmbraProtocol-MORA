from __future__ import annotations

from substrate.p03_long_horizon_credit_assignment_intervention_learning.models import (
    P03CreditAssignmentResult,
)


def p03_long_horizon_credit_assignment_intervention_learning_snapshot(
    result: P03CreditAssignmentResult,
) -> dict[str, object]:
    if not isinstance(result, P03CreditAssignmentResult):
        raise TypeError(
            "p03_long_horizon_credit_assignment_intervention_learning_snapshot requires P03CreditAssignmentResult"
        )
    return {
        "record_set": {
            "assignment_id": result.record_set.assignment_id,
            "evaluated_episode_refs": result.record_set.evaluated_episode_refs,
            "credit_record_count": len(result.record_set.credit_records),
            "no_update_count": len(result.record_set.no_update_records),
            "conflict_count": len(result.record_set.conflicts),
            "continuity_resolution_refs": result.record_set.continuity_resolution_refs,
            "confounder_bundle_ref": result.record_set.confounder_bundle_ref,
            "reason": result.record_set.reason,
        },
        "gate": {
            "credit_record_consumer_ready": result.gate.credit_record_consumer_ready,
            "no_update_consumer_ready": result.gate.no_update_consumer_ready,
            "update_recommendation_consumer_ready": result.gate.update_recommendation_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "p03_frontier_slice_only": result.scope_marker.p03_frontier_slice_only,
            "no_policy_mutation_authority": result.scope_marker.no_policy_mutation_authority,
            "no_scalar_reward_shortcut": result.scope_marker.no_scalar_reward_shortcut,
            "no_raw_approval_shortcut": result.scope_marker.no_raw_approval_shortcut,
            "no_full_causal_discovery_claim": result.scope_marker.no_full_causal_discovery_claim,
            "no_map_wide_rollout_claim": result.scope_marker.no_map_wide_rollout_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "evaluated_episode_count": result.telemetry.evaluated_episode_count,
            "credit_record_count": result.telemetry.credit_record_count,
            "no_update_count": result.telemetry.no_update_count,
            "positive_credit_count": result.telemetry.positive_credit_count,
            "negative_credit_count": result.telemetry.negative_credit_count,
            "mixed_credit_count": result.telemetry.mixed_credit_count,
            "unresolved_credit_count": result.telemetry.unresolved_credit_count,
            "confounded_credit_count": result.telemetry.confounded_credit_count,
            "guarded_update_count": result.telemetry.guarded_update_count,
            "side_effect_dominant_count": result.telemetry.side_effect_dominant_count,
            "outcome_window_open_count": result.telemetry.outcome_window_open_count,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
