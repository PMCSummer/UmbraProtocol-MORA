from __future__ import annotations

from substrate.n03_autobiographical_relevance.models import N03Result


def n03_autobiographical_relevance_snapshot(result: N03Result) -> dict[str, object]:
    if not isinstance(result, N03Result):
        raise TypeError("n03_autobiographical_relevance_snapshot requires N03Result")
    return {
        "result": {
            "bundle_id": result.bundle_id,
            "reason": result.reason,
        },
        "telemetry": {
            "trace_candidate_count": result.telemetry.trace_candidate_count,
            "current_target_count": result.telemetry.current_target_count,
            "relevance_entry_count": result.telemetry.relevance_entry_count,
            "relevant_trace_count": result.telemetry.relevant_trace_count,
            "blocked_transfer_count": result.telemetry.blocked_transfer_count,
            "conflict_count": result.telemetry.conflict_count,
            "provisional_transfer_count": result.telemetry.provisional_transfer_count,
            "no_safe_transfer_count": result.telemetry.no_safe_transfer_count,
            "consumer_ready": result.telemetry.consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "gate": {
            "consumer_ready": result.gate.consumer_ready,
            "transfer_packet_consumer_ready": result.gate.transfer_packet_consumer_ready,
            "consistency_consumer_ready": result.gate.consistency_consumer_ready,
            "required_restrictions": result.gate.required_restrictions,
            "reason_codes": result.gate.reason_codes,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "autobiographical_relevance_not_retrieval": result.scope_marker.autobiographical_relevance_not_retrieval,
            "autobiographical_relevance_not_planner": result.scope_marker.autobiographical_relevance_not_planner,
            "autobiographical_relevance_not_memory_lifecycle": result.scope_marker.autobiographical_relevance_not_memory_lifecycle,
            "autobiographical_relevance_not_identity_generator": result.scope_marker.autobiographical_relevance_not_identity_generator,
            "reason": result.scope_marker.reason,
        },
    }
