from __future__ import annotations

from substrate.stream_kernel.models import (
    StreamKernelGateDecision,
    StreamKernelResult,
    StreamKernelState,
    StreamKernelTelemetry,
    StreamLedgerEvent,
)


def build_stream_kernel_telemetry(
    *,
    state: StreamKernelState,
    ledger_events: tuple[StreamLedgerEvent, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: StreamKernelGateDecision,
    causal_basis: str,
) -> StreamKernelTelemetry:
    return StreamKernelTelemetry(
        source_lineage=state.source_lineage,
        stream_id=state.stream_id,
        sequence_index=state.sequence_index,
        link_decision=state.link_decision,
        carryover_count=len(state.carryover_items),
        unresolved_anchor_count=len(state.unresolved_anchors),
        pending_operation_count=len(state.pending_operations),
        interruption_status=state.interruption_status,
        branch_status=state.branch_status,
        decay_state=state.decay_state,
        stale_marker_count=len(state.stale_markers),
        continuity_confidence=state.continuity_confidence,
        source_regulation_ref=state.source_regulation_ref,
        source_affordance_ref=state.source_affordance_ref,
        source_preference_ref=state.source_preference_ref,
        source_viability_ref=state.source_viability_ref,
        ledger_events=ledger_events,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def stream_kernel_result_snapshot(result: StreamKernelResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_downstream_scheduler_selection_performed": result.no_downstream_scheduler_selection_performed,
        "no_transcript_replay_dependency": result.no_transcript_replay_dependency,
        "no_memory_retrieval_dependency": result.no_memory_retrieval_dependency,
        "no_planner_hidden_flag_dependency": result.no_planner_hidden_flag_dependency,
        "state": {
            "stream_id": state.stream_id,
            "sequence_index": state.sequence_index,
            "link_decision": state.link_decision.value,
            "carryover_items": tuple(
                {
                    "item_id": item.item_id,
                    "carryover_class": item.carryover_class.value,
                    "anchor_key": item.anchor_key,
                    "source_ref": item.source_ref,
                    "strength": item.strength,
                    "created_sequence_index": item.created_sequence_index,
                    "last_seen_sequence_index": item.last_seen_sequence_index,
                    "decay_steps": item.decay_steps,
                    "stale": item.stale,
                    "provisional": item.provisional,
                    "released": item.released,
                    "reason": item.reason,
                }
                for item in state.carryover_items
            ),
            "unresolved_anchors": state.unresolved_anchors,
            "pending_operations": state.pending_operations,
            "interruption_status": state.interruption_status.value,
            "branch_status": state.branch_status.value,
            "decay_state": state.decay_state.value,
            "stale_markers": state.stale_markers,
            "continuity_confidence": state.continuity_confidence,
            "source_regulation_ref": state.source_regulation_ref,
            "source_affordance_ref": state.source_affordance_ref,
            "source_preference_ref": state.source_preference_ref,
            "source_viability_ref": state.source_viability_ref,
            "source_lineage": state.source_lineage,
            "last_update_provenance": state.last_update_provenance,
        },
        "downstream_gate": {
            "accepted": result.downstream_gate.accepted,
            "usability_class": result.downstream_gate.usability_class.value,
            "restrictions": tuple(code.value for code in result.downstream_gate.restrictions),
            "reason": result.downstream_gate.reason,
            "state_ref": result.downstream_gate.state_ref,
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "stream_id": result.telemetry.stream_id,
            "sequence_index": result.telemetry.sequence_index,
            "link_decision": result.telemetry.link_decision.value,
            "carryover_count": result.telemetry.carryover_count,
            "unresolved_anchor_count": result.telemetry.unresolved_anchor_count,
            "pending_operation_count": result.telemetry.pending_operation_count,
            "interruption_status": result.telemetry.interruption_status.value,
            "branch_status": result.telemetry.branch_status.value,
            "decay_state": result.telemetry.decay_state.value,
            "stale_marker_count": result.telemetry.stale_marker_count,
            "continuity_confidence": result.telemetry.continuity_confidence,
            "source_regulation_ref": result.telemetry.source_regulation_ref,
            "source_affordance_ref": result.telemetry.source_affordance_ref,
            "source_preference_ref": result.telemetry.source_preference_ref,
            "source_viability_ref": result.telemetry.source_viability_ref,
            "ledger_events": tuple(
                {
                    "event_id": event.event_id,
                    "event_kind": event.event_kind.value,
                    "stream_id": event.stream_id,
                    "item_id": event.item_id,
                    "anchor_key": event.anchor_key,
                    "reason": event.reason,
                    "reason_code": event.reason_code,
                    "provenance": event.provenance,
                }
                for event in result.telemetry.ledger_events
            ),
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": tuple(
                    code.value for code in result.telemetry.downstream_gate.restrictions
                ),
                "reason": result.telemetry.downstream_gate.reason,
                "state_ref": result.telemetry.downstream_gate.state_ref,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
