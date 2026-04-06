from __future__ import annotations

from substrate.tension_scheduler.models import (
    C02RestrictionCode,
    TensionDecayState,
    TensionLifecycleStatus,
    TensionScheduleEntry,
    TensionSchedulerGateDecision,
    TensionSchedulerResult,
    TensionSchedulerState,
    TensionSchedulerUsabilityClass,
    TensionSchedulingMode,
)


def evaluate_tension_scheduler_downstream_gate(
    tension_scheduler_state_or_result: object,
) -> TensionSchedulerGateDecision:
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerResult):
        state = tension_scheduler_state_or_result.state
    elif isinstance(tension_scheduler_state_or_result, TensionSchedulerState):
        state = tension_scheduler_state_or_result
    else:
        raise TypeError(
            "evaluate_tension_scheduler_downstream_gate requires TensionSchedulerState/TensionSchedulerResult"
        )

    restrictions: list[C02RestrictionCode] = [
        C02RestrictionCode.TENSION_STATE_MUST_BE_READ,
        C02RestrictionCode.TENSION_LIFECYCLE_MUST_BE_READ,
        C02RestrictionCode.SCHEDULING_MODE_MUST_BE_READ,
        C02RestrictionCode.REVISIT_PRIORITY_MUST_BE_READ,
        C02RestrictionCode.WAKE_CONDITIONS_MUST_BE_READ,
        C02RestrictionCode.WAKE_CAUSE_MUST_BE_READ,
        C02RestrictionCode.WAKE_SCOPE_MUST_BE_READ,
        C02RestrictionCode.REACTIVATION_REQUIRES_LAWFUL_WAKE_CAUSE,
        C02RestrictionCode.SUPPRESSION_BUDGET_MUST_BE_READ,
        C02RestrictionCode.CLOSURE_CRITERIA_MUST_BE_READ,
        C02RestrictionCode.REOPEN_CRITERIA_MUST_BE_READ,
        C02RestrictionCode.C01_CARRYOVER_NOT_EQUAL_TENSION,
        C02RestrictionCode.RETRIEVAL_NOT_EQUAL_REOPEN,
        C02RestrictionCode.CLOSURE_REQUIRES_EVIDENCE,
        C02RestrictionCode.STALE_NOT_EQUAL_CLOSED,
        C02RestrictionCode.SUPPRESSION_NOT_EQUAL_DROP,
        C02RestrictionCode.KIND_POLICY_MUST_BE_READ,
        C02RestrictionCode.NO_PLANNER_BACKLOG_SUBSTITUTION,
    ]
    entries = state.tensions
    has_unschedulable = any(_is_unschedulable_entry(entry) for entry in entries)
    has_no_safe_defer = any(
        entry.scheduling_mode == TensionSchedulingMode.NO_SAFE_DEFER_CLAIM
        for entry in entries
    )
    has_scheduler_conflict = any(entry.scheduler_conflict for entry in entries)
    has_trigger_unknown = any(entry.trigger_unknown for entry in entries)
    has_closure_uncertain = any(entry.closure_uncertain for entry in entries)
    has_weak_wake_ignored = any(entry.weak_wake_signal_ignored for entry in entries)
    has_weak_closure_ignored = any(
        entry.weak_closure_signal_ignored for entry in entries
    )
    has_weak_reopen_ignored = any(entry.weak_reopen_signal_ignored for entry in entries)
    has_threshold_edge_degrade = any(
        entry.threshold_edge_downgrade_applied for entry in entries
    )
    has_kind_policy = any(entry.kind_policy_applied for entry in entries)
    has_illegal_reactivation = any(
        entry.current_status == TensionLifecycleStatus.REACTIVATED
        and entry.reactivation_cause.value == "none"
        for entry in entries
    )
    has_stale_release = any(
        entry.decay_state in {TensionDecayState.STALE, TensionDecayState.RELEASED}
        or entry.scheduling_mode == TensionSchedulingMode.RELEASE_AS_STALE
    for entry in entries
    )
    has_active_or_reactivated = any(
        entry.current_status
        in {TensionLifecycleStatus.ACTIVE, TensionLifecycleStatus.REACTIVATED}
        for entry in entries
    )

    accepted = bool(entries)
    usability = TensionSchedulerUsabilityClass.USABLE_BOUNDED
    reason = "typed unresolved tension scheduler state available for bounded downstream use"

    if has_unschedulable:
        restrictions.append(C02RestrictionCode.UNSCHEDULABLE_TENSION_PRESENT)
    if has_no_safe_defer:
        restrictions.append(C02RestrictionCode.NO_SAFE_DEFER_CLAIM_PRESENT)
    if has_stale_release:
        restrictions.append(C02RestrictionCode.STALE_RELEASE_MUST_BE_READ)
    if has_weak_wake_ignored:
        restrictions.append(C02RestrictionCode.WEAK_WAKE_SIGNAL_ORIGIN_IGNORED)
    if has_weak_closure_ignored:
        restrictions.append(C02RestrictionCode.WEAK_CLOSURE_SIGNAL_ORIGIN_IGNORED)
    if has_weak_reopen_ignored:
        restrictions.append(C02RestrictionCode.WEAK_REOPEN_SIGNAL_ORIGIN_IGNORED)
    if has_threshold_edge_degrade:
        restrictions.append(C02RestrictionCode.THRESHOLD_EDGE_DEGRADE_MUST_BE_READ)
    if has_kind_policy:
        restrictions.append(C02RestrictionCode.KIND_POLICY_MUST_BE_READ)

    degraded = has_trigger_unknown or has_closure_uncertain or has_stale_release
    degraded = (
        degraded
        or has_weak_wake_ignored
        or has_weak_closure_ignored
        or has_weak_reopen_ignored
        or has_threshold_edge_degrade
    )
    blocked = has_scheduler_conflict or has_unschedulable or (
        has_no_safe_defer and not has_active_or_reactivated
    )
    blocked = blocked or has_illegal_reactivation
    if blocked:
        accepted = False
        usability = TensionSchedulerUsabilityClass.BLOCKED
        restrictions.append(C02RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = (
            "unschedulable/no-safe-defer conflict blocks lawful downstream scheduler claim"
        )
    elif degraded:
        usability = TensionSchedulerUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(C02RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = (
            "scheduler uncertainty/stale pressure requires degraded downstream interpretation"
        )

    if not entries:
        accepted = False
        usability = TensionSchedulerUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(C02RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "no normalized unresolved tensions emitted by c02"

    return TensionSchedulerGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.scheduler_id}@{state.source_stream_sequence_index}",
    )


def _is_unschedulable_entry(entry: TensionScheduleEntry) -> bool:
    return (
        entry.unschedulable
        or entry.scheduling_mode
        == TensionSchedulingMode.UNSCHEDULABLE_TENSION
    )
