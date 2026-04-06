from __future__ import annotations

from dataclasses import dataclass

from substrate.tension_scheduler.models import (
    C02RestrictionCode,
    TensionLifecycleStatus,
    TensionScheduleEntry,
    TensionSchedulerResult,
    TensionSchedulerState,
    TensionSchedulerUsabilityClass,
    TensionSchedulingMode,
)
from substrate.tension_scheduler.policy import evaluate_tension_scheduler_downstream_gate


@dataclass(frozen=True, slots=True)
class TensionSchedulerContractView:
    scheduler_id: str
    source_stream_id: str
    tension_count: int
    active_present: bool
    deferred_present: bool
    dormant_present: bool
    stale_present: bool
    closed_present: bool
    wake_queue_present: bool
    suppression_active: bool
    revisit_now_present: bool
    no_safe_defer_present: bool
    unschedulable_present: bool
    closure_uncertain_present: bool
    trigger_unknown_present: bool
    weak_wake_signal_ignored_present: bool
    weak_closure_signal_ignored_present: bool
    weak_reopen_signal_ignored_present: bool
    wake_scope_mismatch_present: bool
    threshold_edge_downgrade_present: bool
    lawful_reactivation_present: bool
    retrieval_without_reopen_present: bool
    gate_accepted: bool
    restrictions: tuple[C02RestrictionCode, ...]
    usability_class: TensionSchedulerUsabilityClass
    requires_restrictions_read: bool
    reason: str


def derive_tension_scheduler_contract_view(
    tension_scheduler_result_or_state: TensionSchedulerResult | TensionSchedulerState,
) -> TensionSchedulerContractView:
    if isinstance(tension_scheduler_result_or_state, TensionSchedulerResult):
        state = tension_scheduler_result_or_state.state
    elif isinstance(tension_scheduler_result_or_state, TensionSchedulerState):
        state = tension_scheduler_result_or_state
    else:
        raise TypeError(
            "derive_tension_scheduler_contract_view requires TensionSchedulerResult/TensionSchedulerState"
        )

    gate = evaluate_tension_scheduler_downstream_gate(state)
    entries = state.tensions
    statuses = {entry.current_status for entry in entries}
    modes = {entry.scheduling_mode for entry in entries}
    retrieval_without_reopen_present = any(
        entry.provenance == "c02.retrieval_without_reopen" for entry in entries
    )
    weak_wake_signal_ignored_present = any(
        entry.weak_wake_signal_ignored for entry in entries
    )
    weak_closure_signal_ignored_present = any(
        entry.weak_closure_signal_ignored for entry in entries
    )
    weak_reopen_signal_ignored_present = any(
        entry.weak_reopen_signal_ignored for entry in entries
    )
    wake_scope_mismatch_present = any(
        entry.reactivation_cause.value in {"explicit_signal", "reopen_condition"}
        and not entry.wake_scope_matched
        for entry in entries
    )
    threshold_edge_downgrade_present = any(
        entry.threshold_edge_downgrade_applied for entry in entries
    )
    lawful_reactivation_present = any(
        entry.current_status == TensionLifecycleStatus.REACTIVATED
        and entry.reactivation_cause.value != "none"
        for entry in entries
    )
    return TensionSchedulerContractView(
        scheduler_id=state.scheduler_id,
        source_stream_id=state.source_stream_id,
        tension_count=len(entries),
        active_present=TensionLifecycleStatus.ACTIVE in statuses
        or TensionLifecycleStatus.REACTIVATED in statuses,
        deferred_present=TensionLifecycleStatus.DEFERRED in statuses,
        dormant_present=TensionLifecycleStatus.DORMANT in statuses,
        stale_present=TensionLifecycleStatus.STALE in statuses,
        closed_present=TensionLifecycleStatus.CLOSED in statuses,
        wake_queue_present=bool(state.wake_queue_tension_ids),
        suppression_active=state.suppression_active,
        revisit_now_present=(
            TensionSchedulingMode.REVISIT_NOW in modes
            or TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER in modes
        ),
        no_safe_defer_present=TensionSchedulingMode.NO_SAFE_DEFER_CLAIM in modes,
        unschedulable_present=any(
            entry.unschedulable
            or entry.scheduling_mode == TensionSchedulingMode.UNSCHEDULABLE_TENSION
            for entry in entries
        ),
        closure_uncertain_present=any(entry.closure_uncertain for entry in entries),
        trigger_unknown_present=any(entry.trigger_unknown for entry in entries),
        weak_wake_signal_ignored_present=weak_wake_signal_ignored_present,
        weak_closure_signal_ignored_present=weak_closure_signal_ignored_present,
        weak_reopen_signal_ignored_present=weak_reopen_signal_ignored_present,
        wake_scope_mismatch_present=wake_scope_mismatch_present,
        threshold_edge_downgrade_present=threshold_edge_downgrade_present,
        lawful_reactivation_present=lawful_reactivation_present,
        retrieval_without_reopen_present=retrieval_without_reopen_present,
        gate_accepted=gate.accepted,
        restrictions=gate.restrictions,
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason="contract requires typed tension lifecycle and scheduler restrictions read",
    )


def choose_tension_execution_mode(
    tension_scheduler_result_or_state: TensionSchedulerResult | TensionSchedulerState,
) -> str:
    view = derive_tension_scheduler_contract_view(tension_scheduler_result_or_state)
    if not view.gate_accepted or view.usability_class == TensionSchedulerUsabilityClass.BLOCKED:
        return "hold_or_repair"
    if (
        view.weak_wake_signal_ignored_present
        or view.weak_closure_signal_ignored_present
        or view.weak_reopen_signal_ignored_present
        or view.wake_scope_mismatch_present
    ):
        return "defer_and_monitor"
    if view.unschedulable_present or view.no_safe_defer_present:
        return "escalate_for_resolution"
    if view.revisit_now_present and view.active_present:
        if view.usability_class == TensionSchedulerUsabilityClass.DEGRADED_BOUNDED:
            return "revisit_with_limits"
        return "revisit_now"
    if view.wake_queue_present:
        return "revisit_with_limits"
    if view.deferred_present:
        return "defer_and_monitor"
    if view.suppression_active or view.dormant_present:
        return "monitor_background"
    if view.stale_present and not view.active_present:
        return "release_or_idle"
    if view.closed_present and not view.active_present:
        return "idle"
    return "idle"


def select_revisit_tensions(
    tension_scheduler_result_or_state: TensionSchedulerResult | TensionSchedulerState,
) -> tuple[str, ...]:
    if isinstance(tension_scheduler_result_or_state, TensionSchedulerResult):
        state = tension_scheduler_result_or_state.state
    elif isinstance(tension_scheduler_result_or_state, TensionSchedulerState):
        state = tension_scheduler_result_or_state
    else:
        raise TypeError(
            "select_revisit_tensions requires TensionSchedulerResult/TensionSchedulerState"
        )

    view = derive_tension_scheduler_contract_view(state)
    if not view.gate_accepted:
        return ()

    selected: list[TensionScheduleEntry] = [
        entry
        for entry in state.tensions
        if entry.scheduling_mode
        in {
            TensionSchedulingMode.REVISIT_NOW,
            TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
        }
        and entry.current_status
        in {
            TensionLifecycleStatus.ACTIVE,
            TensionLifecycleStatus.REACTIVATED,
        }
    ]
    selected.sort(key=lambda item: item.revisit_priority, reverse=True)
    return tuple(entry.tension_id for entry in selected)
