from __future__ import annotations

from substrate.v02_communicative_intent_utterance_plan_bridge.models import (
    V02UtterancePlanResult,
)


def v02_communicative_intent_utterance_plan_bridge_snapshot(
    result: V02UtterancePlanResult,
) -> dict[str, object]:
    if not isinstance(result, V02UtterancePlanResult):
        raise TypeError(
            "v02_communicative_intent_utterance_plan_bridge_snapshot requires V02UtterancePlanResult"
        )
    return {
        "state": {
            "plan_id": result.state.plan_id,
            "plan_status": result.state.plan_status.value,
            "primary_branch_id": result.state.primary_branch_id,
            "alternative_branch_ids": result.state.alternative_branch_ids,
            "segment_count": result.state.segment_count,
            "branch_count": result.state.branch_count,
            "ordering_edge_count": result.state.ordering_edge_count,
            "mandatory_qualifier_attachment_count": (
                result.state.mandatory_qualifier_attachment_count
            ),
            "blocked_expansion_count": result.state.blocked_expansion_count,
            "protected_omission_count": result.state.protected_omission_count,
            "clarification_first_required": result.state.clarification_first_required,
            "refusal_dominant": result.state.refusal_dominant,
            "protective_boundary_first": result.state.protective_boundary_first,
            "partial_plan_only": result.state.partial_plan_only,
            "unresolved_branching": result.state.unresolved_branching,
            "realization_contract_ready": result.state.realization_contract_ready,
            "discourse_history_sensitive": result.state.discourse_history_sensitive,
            "downstream_consumer_ready": result.state.downstream_consumer_ready,
            "segment_ids": result.state.segment_ids,
            "source_act_ids": result.state.source_act_ids,
            "mandatory_qualifier_ids": result.state.mandatory_qualifier_ids,
            "blocked_expansion_ids": result.state.blocked_expansion_ids,
            "protected_omission_ids": result.state.protected_omission_ids,
            "justification_links": result.state.justification_links,
            "provenance": result.state.provenance,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "plan_consumer_ready": result.gate.plan_consumer_ready,
            "ordering_consumer_ready": result.gate.ordering_consumer_ready,
            "realization_contract_consumer_ready": result.gate.realization_contract_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "v02_first_slice_only": result.scope_marker.v02_first_slice_only,
            "v03_not_implemented": result.scope_marker.v03_not_implemented,
            "p02_not_implemented": result.scope_marker.p02_not_implemented,
            "p04_not_implemented": result.scope_marker.p04_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "plan_id": result.telemetry.plan_id,
            "tick_index": result.telemetry.tick_index,
            "plan_status": result.telemetry.plan_status.value,
            "segment_count": result.telemetry.segment_count,
            "branch_count": result.telemetry.branch_count,
            "ordering_edge_count": result.telemetry.ordering_edge_count,
            "mandatory_qualifier_attachment_count": (
                result.telemetry.mandatory_qualifier_attachment_count
            ),
            "blocked_expansion_count": result.telemetry.blocked_expansion_count,
            "protected_omission_count": result.telemetry.protected_omission_count,
            "clarification_first_required": result.telemetry.clarification_first_required,
            "refusal_dominant": result.telemetry.refusal_dominant,
            "protective_boundary_first": result.telemetry.protective_boundary_first,
            "partial_plan_only": result.telemetry.partial_plan_only,
            "unresolved_branching": result.telemetry.unresolved_branching,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
