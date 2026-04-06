from __future__ import annotations

from substrate.tension_scheduler.models import (
    TensionSchedulerGateDecision,
    TensionSchedulerResult,
    TensionSchedulerState,
    TensionSchedulerTelemetry,
    TensionLedgerEvent,
)


def build_tension_scheduler_telemetry(
    *,
    state: TensionSchedulerState,
    ledger_events: tuple[TensionLedgerEvent, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: TensionSchedulerGateDecision,
    causal_basis: str,
) -> TensionSchedulerTelemetry:
    return TensionSchedulerTelemetry(
        source_lineage=state.source_lineage,
        scheduler_id=state.scheduler_id,
        source_stream_id=state.source_stream_id,
        source_stream_sequence_index=state.source_stream_sequence_index,
        tension_count=len(state.tensions),
        active_count=len(state.active_tension_ids),
        deferred_count=len(state.deferred_tension_ids),
        dormant_count=len(state.dormant_tension_ids),
        stale_count=len(state.stale_tension_ids),
        closed_count=len(state.closed_tension_ids),
        wake_queue_count=len(state.wake_queue_tension_ids),
        scheduling_modes=tuple(
            dict.fromkeys(entry.scheduling_mode.value for entry in state.tensions)
        ),
        wake_causes=tuple(
            dict.fromkeys(entry.reactivation_cause.value for entry in state.tensions)
        ),
        lifecycle_statuses=tuple(
            dict.fromkeys(entry.current_status.value for entry in state.tensions)
        ),
        tension_kinds=tuple(
            dict.fromkeys(entry.tension_kind.value for entry in state.tensions)
        ),
        unschedulable_count=sum(1 for entry in state.tensions if entry.unschedulable),
        no_safe_defer_count=sum(
            1
            for entry in state.tensions
            if entry.scheduling_mode.value == "no_safe_defer_claim"
        ),
        trigger_unknown_count=sum(1 for entry in state.tensions if entry.trigger_unknown),
        closure_uncertain_count=sum(
            1 for entry in state.tensions if entry.closure_uncertain
        ),
        scheduler_conflict_count=sum(
            1 for entry in state.tensions if entry.scheduler_conflict
        ),
        weak_wake_signal_ignored_count=sum(
            1 for entry in state.tensions if entry.weak_wake_signal_ignored
        ),
        weak_closure_signal_ignored_count=sum(
            1 for entry in state.tensions if entry.weak_closure_signal_ignored
        ),
        weak_reopen_signal_ignored_count=sum(
            1 for entry in state.tensions if entry.weak_reopen_signal_ignored
        ),
        threshold_edge_downgrade_count=sum(
            1 for entry in state.tensions if entry.threshold_edge_downgrade_applied
        ),
        kind_policy_applied_count=sum(
            1 for entry in state.tensions if entry.kind_policy_applied
        ),
        ledger_events=ledger_events,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def tension_scheduler_result_snapshot(result: TensionSchedulerResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_planner_backlog_dependency": result.no_planner_backlog_dependency,
        "no_retrieval_scheduler_dependency": result.no_retrieval_scheduler_dependency,
        "state": {
            "scheduler_id": state.scheduler_id,
            "source_stream_id": state.source_stream_id,
            "source_stream_sequence_index": state.source_stream_sequence_index,
            "active_tension_ids": state.active_tension_ids,
            "deferred_tension_ids": state.deferred_tension_ids,
            "dormant_tension_ids": state.dormant_tension_ids,
            "stale_tension_ids": state.stale_tension_ids,
            "closed_tension_ids": state.closed_tension_ids,
            "wake_queue_tension_ids": state.wake_queue_tension_ids,
            "suppression_active": state.suppression_active,
            "confidence": state.confidence,
            "source_c01_state_ref": state.source_c01_state_ref,
            "source_regulation_ref": state.source_regulation_ref,
            "source_affordance_ref": state.source_affordance_ref,
            "source_preference_ref": state.source_preference_ref,
            "source_viability_ref": state.source_viability_ref,
            "source_lineage": state.source_lineage,
            "last_update_provenance": state.last_update_provenance,
            "tensions": tuple(
                {
                    "tension_id": entry.tension_id,
                    "source_stream_id": entry.source_stream_id,
                    "source_stream_sequence_index": entry.source_stream_sequence_index,
                    "tension_kind": entry.tension_kind.value,
                    "causal_anchor": entry.causal_anchor,
                    "current_status": entry.current_status.value,
                    "revisit_priority": entry.revisit_priority,
                    "scheduling_mode": entry.scheduling_mode.value,
                    "earliest_revisit_step": entry.earliest_revisit_step,
                    "wake_conditions": entry.wake_conditions,
                    "matched_wake_triggers": entry.matched_wake_triggers,
                    "reactivation_cause": entry.reactivation_cause.value,
                    "wake_scope_matched": entry.wake_scope_matched,
                    "suppression_budget": entry.suppression_budget,
                    "suppression_remaining": entry.suppression_remaining,
                    "decay_state": entry.decay_state.value,
                    "stale": entry.stale,
                    "closure_criteria": entry.closure_criteria,
                    "reopen_criteria": entry.reopen_criteria,
                    "confidence": entry.confidence,
                    "trigger_unknown": entry.trigger_unknown,
                    "closure_uncertain": entry.closure_uncertain,
                    "scheduler_conflict": entry.scheduler_conflict,
                    "weak_wake_signal_ignored": entry.weak_wake_signal_ignored,
                    "weak_closure_signal_ignored": entry.weak_closure_signal_ignored,
                    "weak_reopen_signal_ignored": entry.weak_reopen_signal_ignored,
                    "threshold_edge_downgrade_applied": entry.threshold_edge_downgrade_applied,
                    "kind_policy_applied": entry.kind_policy_applied,
                    "unschedulable": entry.unschedulable,
                    "created_sequence_index": entry.created_sequence_index,
                    "last_touched_sequence_index": entry.last_touched_sequence_index,
                    "inactive_steps": entry.inactive_steps,
                    "reason": entry.reason,
                    "provenance": entry.provenance,
                }
                for entry in state.tensions
            ),
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
            "scheduler_id": result.telemetry.scheduler_id,
            "source_stream_id": result.telemetry.source_stream_id,
            "source_stream_sequence_index": result.telemetry.source_stream_sequence_index,
            "tension_count": result.telemetry.tension_count,
            "active_count": result.telemetry.active_count,
            "deferred_count": result.telemetry.deferred_count,
            "dormant_count": result.telemetry.dormant_count,
            "stale_count": result.telemetry.stale_count,
            "closed_count": result.telemetry.closed_count,
            "wake_queue_count": result.telemetry.wake_queue_count,
            "scheduling_modes": result.telemetry.scheduling_modes,
            "wake_causes": result.telemetry.wake_causes,
            "lifecycle_statuses": result.telemetry.lifecycle_statuses,
            "tension_kinds": result.telemetry.tension_kinds,
            "unschedulable_count": result.telemetry.unschedulable_count,
            "no_safe_defer_count": result.telemetry.no_safe_defer_count,
            "trigger_unknown_count": result.telemetry.trigger_unknown_count,
            "closure_uncertain_count": result.telemetry.closure_uncertain_count,
            "scheduler_conflict_count": result.telemetry.scheduler_conflict_count,
            "weak_wake_signal_ignored_count": result.telemetry.weak_wake_signal_ignored_count,
            "weak_closure_signal_ignored_count": result.telemetry.weak_closure_signal_ignored_count,
            "weak_reopen_signal_ignored_count": result.telemetry.weak_reopen_signal_ignored_count,
            "threshold_edge_downgrade_count": result.telemetry.threshold_edge_downgrade_count,
            "kind_policy_applied_count": result.telemetry.kind_policy_applied_count,
            "ledger_events": tuple(
                {
                    "event_id": event.event_id,
                    "event_kind": event.event_kind.value,
                    "tension_id": event.tension_id,
                    "stream_id": event.stream_id,
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
