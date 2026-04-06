from __future__ import annotations

from dataclasses import replace

from substrate.tension_scheduler import (
    C02RestrictionCode,
    TensionLifecycleStatus,
    TensionSignalOrigin,
    TensionWakeCause,
    TensionSchedulerContext,
    TensionSchedulingMode,
    build_tension_scheduler,
    choose_tension_execution_mode,
    derive_tension_scheduler_contract_view,
    select_revisit_tensions,
)
from tests.substrate.c02_testkit import build_c02_upstream


def _tension_by_anchor(result, anchor: str):
    for entry in result.state.tensions:
        if entry.causal_anchor == anchor:
            return entry
    return None


def test_c02_generates_typed_tension_scheduler_state_and_gate() -> None:
    upstream = build_c02_upstream(
        case_id="c02-gen",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )

    assert result.state.scheduler_id
    assert result.state.source_stream_id == upstream.stream.state.stream_id
    assert result.state.tensions
    assert result.telemetry.ledger_events
    assert result.downstream_gate.restrictions
    assert result.no_planner_backlog_dependency is True
    assert result.no_retrieval_scheduler_dependency is True


def test_c02_typed_only_boundary_rejects_raw_bypass() -> None:
    try:
        build_tension_scheduler("raw", "raw", "raw", "raw", "raw")  # type: ignore[arg-type]
    except TypeError:
        return
    assert False, "build_tension_scheduler must reject raw/non-typed bypass"


def test_c02_lifecycle_supports_close_reopen_stale_release_chain() -> None:
    first_upstream = build_c02_upstream(
        case_id="c02-life-1",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )
    anchor = first.state.tensions[0].causal_anchor

    second_upstream = build_c02_upstream(
        case_id="c02-life-2",
        energy=14.2,
        cognitive=94.0,
        safety=34.2,
        unresolved_preference=True,
        prior_stream_state=first_upstream.stream.state,
    )
    closed = build_tension_scheduler(
        second_upstream.stream,
        second_upstream.regulation,
        second_upstream.affordances,
        second_upstream.preferences,
        second_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            closure_evidence_anchor_keys=(anchor,),
        ),
    )
    closed_entry = _tension_by_anchor(closed, anchor)
    assert closed_entry is not None
    assert closed_entry.current_status == TensionLifecycleStatus.CLOSED

    third_upstream = build_c02_upstream(
        case_id="c02-life-3",
        energy=14.4,
        cognitive=93.5,
        safety=34.3,
        unresolved_preference=True,
        prior_stream_state=second_upstream.stream.state,
    )
    reopened = build_tension_scheduler(
        third_upstream.stream,
        third_upstream.regulation,
        third_upstream.affordances,
        third_upstream.preferences,
        third_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=closed.state,
            reopen_anchor_keys=(anchor,),
        ),
    )
    reopened_entry = _tension_by_anchor(reopened, anchor)
    assert reopened_entry is not None
    assert reopened_entry.current_status == TensionLifecycleStatus.REACTIVATED
    assert reopened_entry.scheduling_mode == TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER

    settled_stream = build_c02_upstream(
        case_id="c02-life-settled",
        energy=62.0,
        cognitive=45.0,
        safety=76.0,
        unresolved_preference=False,
        prior_stream_state=third_upstream.stream.state,
    )
    stale_step = build_tension_scheduler(
        settled_stream.stream,
        settled_stream.regulation,
        settled_stream.affordances,
        settled_stream.preferences,
        settled_stream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=reopened.state,
            stale_after_steps=1,
            release_after_steps=2,
        ),
    )
    release_step = build_tension_scheduler(
        settled_stream.stream,
        settled_stream.regulation,
        settled_stream.affordances,
        settled_stream.preferences,
        settled_stream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=stale_step.state,
            stale_after_steps=1,
            release_after_steps=2,
        ),
    )

    assert any(entry.current_status == TensionLifecycleStatus.STALE for entry in stale_step.state.tensions)
    assert any(
        entry.scheduling_mode == TensionSchedulingMode.RELEASE_AS_STALE
        for entry in release_step.state.tensions
    )


def test_c02_contrast_same_visibility_but_different_causal_weight_changes_schedule() -> None:
    strong = build_c02_upstream(
        case_id="c02-contrast-strong",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    weak = build_c02_upstream(
        case_id="c02-contrast-weak",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    strong_result = build_tension_scheduler(
        strong.stream,
        strong.regulation,
        strong.affordances,
        strong.preferences,
        strong.viability,
    )
    weak_result = build_tension_scheduler(
        weak.stream,
        weak.regulation,
        weak.affordances,
        weak.preferences,
        weak.viability,
    )

    strong_mode = choose_tension_execution_mode(strong_result)
    weak_mode = choose_tension_execution_mode(weak_result)
    assert strong_mode in {"revisit_now", "revisit_with_limits", "defer_and_monitor"}
    assert weak_mode in {"monitor_background", "defer_and_monitor", "release_or_idle", "idle"}
    assert strong_mode != weak_mode or strong_result.state.wake_queue_tension_ids != weak_result.state.wake_queue_tension_ids


def test_c02_suppression_keeps_tension_and_returns_on_explicit_trigger() -> None:
    first_upstream = build_c02_upstream(
        case_id="c02-suppress-1",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    first = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )
    suppressed = [
        entry for entry in first.state.tensions if entry.scheduling_mode == TensionSchedulingMode.SUPPRESS_TEMPORARILY
    ]
    assert suppressed, "expected at least one temporarily suppressed tension"
    target = suppressed[0]

    second_upstream = build_c02_upstream(
        case_id="c02-suppress-2",
        energy=66.2,
        cognitive=43.8,
        safety=74.1,
        unresolved_preference=False,
        prior_stream_state=first_upstream.stream.state,
    )
    second = build_tension_scheduler(
        second_upstream.stream,
        second_upstream.regulation,
        second_upstream.affordances,
        second_upstream.preferences,
        second_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(target.causal_anchor,),
            wake_signal_origin=TensionSignalOrigin.C01_PHASE_NATIVE,
        ),
    )
    reactivated = _tension_by_anchor(second, target.causal_anchor)
    assert reactivated is not None
    assert reactivated.current_status == TensionLifecycleStatus.REACTIVATED
    assert reactivated.scheduling_mode == TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER


def test_c02_false_closure_adversarial_requires_real_closure_evidence() -> None:
    first_upstream = build_c02_upstream(
        case_id="c02-false-close-1",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )
    anchor = first.state.tensions[0].causal_anchor

    second_upstream = build_c02_upstream(
        case_id="c02-false-close-2",
        energy=14.1,
        cognitive=94.8,
        safety=34.1,
        unresolved_preference=True,
        prior_stream_state=first_upstream.stream.state,
    )
    second = build_tension_scheduler(
        second_upstream.stream,
        second_upstream.regulation,
        second_upstream.affordances,
        second_upstream.preferences,
        second_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            closure_evidence_anchor_keys=(f"{anchor}-weak-hint",),
            retrieved_episode_refs=(anchor,),
        ),
    )
    entry = _tension_by_anchor(second, anchor)
    assert entry is not None
    assert entry.current_status != TensionLifecycleStatus.CLOSED


def test_c02_wake_trigger_perturbation_changes_reactivation_outcome() -> None:
    first_upstream = build_c02_upstream(
        case_id="c02-trigger-1",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    first = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )
    target = first.state.tensions[0].causal_anchor
    second_upstream = build_c02_upstream(
        case_id="c02-trigger-2",
        energy=66.1,
        cognitive=44.2,
        safety=74.1,
        unresolved_preference=False,
        prior_stream_state=first_upstream.stream.state,
    )
    matched = build_tension_scheduler(
        second_upstream.stream,
        second_upstream.regulation,
        second_upstream.affordances,
        second_upstream.preferences,
        second_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(target,),
            wake_signal_origin=TensionSignalOrigin.C01_PHASE_NATIVE,
        ),
    )
    unmatched = build_tension_scheduler(
        second_upstream.stream,
        second_upstream.regulation,
        second_upstream.affordances,
        second_upstream.preferences,
        second_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=("other-anchor",),
            wake_signal_origin=TensionSignalOrigin.C01_PHASE_NATIVE,
        ),
    )
    matched_entry = _tension_by_anchor(matched, target)
    unmatched_entry = _tension_by_anchor(unmatched, target)
    assert matched_entry is not None and unmatched_entry is not None
    assert matched_entry.current_status == TensionLifecycleStatus.REACTIVATED
    assert matched_entry.reactivation_cause == TensionWakeCause.EXPLICIT_SIGNAL
    assert unmatched_entry.current_status != TensionLifecycleStatus.REACTIVATED
    assert unmatched_entry.reactivation_cause == TensionWakeCause.NONE


def test_c02_broad_trigger_is_scoped_not_mass_fanout() -> None:
    upstream = build_c02_upstream(
        case_id="c02-fanout",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    assert len(first.state.tensions) >= 2
    target_anchor = first.state.tensions[0].causal_anchor
    second = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(target_anchor,),
            wake_signal_origin=TensionSignalOrigin.C01_PHASE_NATIVE,
        ),
    )
    reactivated = [
        entry
        for entry in second.state.tensions
        if entry.current_status == TensionLifecycleStatus.REACTIVATED
    ]
    assert reactivated
    assert all(entry.causal_anchor == target_anchor for entry in reactivated)


def test_c02_reactivation_requires_lawful_wake_not_priority_escalation() -> None:
    upstream = build_c02_upstream(
        case_id="c02-reactivation-guard",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    target = first.state.tensions[0]
    forced_stale = replace(
        target,
        current_status=TensionLifecycleStatus.STALE,
        scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
        reactivation_cause=TensionWakeCause.NONE,
        stale=True,
        decay_state=target.decay_state,
    )
    patched_tensions = tuple(
        forced_stale if entry.tension_id == target.tension_id else entry
        for entry in first.state.tensions
    )
    prior_state = replace(
        first.state,
        tensions=patched_tensions,
        stale_tension_ids=tuple(
            dict.fromkeys((*first.state.stale_tension_ids, target.tension_id))
        ),
    )
    second = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(prior_scheduler_state=prior_state),
    )
    entry = _tension_by_anchor(second, target.causal_anchor)
    assert entry is not None
    assert entry.current_status != TensionLifecycleStatus.REACTIVATED
    assert entry.reactivation_cause == TensionWakeCause.NONE
    assert entry.scheduling_mode != TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER


def test_c02_near_threshold_triads_do_not_flip_arbitrarily() -> None:
    modes = []
    shapes = []
    for idx, values in enumerate(
        (
            (66.0, 44.0, 74.0),
            (66.1, 43.9, 74.1),
            (65.9, 44.1, 73.9),
        ),
        start=1,
    ):
        upstream = build_c02_upstream(
            case_id=f"c02-threshold-{idx}",
            energy=values[0],
            cognitive=values[1],
            safety=values[2],
            unresolved_preference=False,
        )
        result = build_tension_scheduler(
            upstream.stream,
            upstream.regulation,
            upstream.affordances,
            upstream.preferences,
            upstream.viability,
        )
        modes.append(choose_tension_execution_mode(result))
        shapes.append(tuple((entry.scheduling_mode.value, round(entry.revisit_priority, 3)) for entry in result.state.tensions))
    assert len(set(modes)) == 1
    assert len(set(shapes)) == 1


def test_c02_kind_sensitive_consequence_same_band_diff_kind() -> None:
    focused = build_c02_upstream(
        case_id="c02-kind-focus",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    focused_result = build_tension_scheduler(
        focused.stream,
        focused.regulation,
        focused.affordances,
        focused.preferences,
        focused.viability,
    )
    pressured = build_c02_upstream(
        case_id="c02-kind-pressure",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    pressured_result = build_tension_scheduler(
        pressured.stream,
        pressured.regulation,
        pressured.affordances,
        pressured.preferences,
        pressured.viability,
    )
    focus_entry = focused_result.state.tensions[0]
    pressure_entry = pressured_result.state.tensions[0]
    assert focus_entry.tension_kind != pressure_entry.tension_kind
    assert (
        focus_entry.scheduling_mode != pressure_entry.scheduling_mode
        or focus_entry.kind_policy_applied != pressure_entry.kind_policy_applied
    )


def test_c02_weak_origin_wake_signal_is_ignored() -> None:
    upstream = build_c02_upstream(
        case_id="c02-weak-wake",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    first = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    target = first.state.tensions[0].causal_anchor
    second = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(target,),
            wake_signal_origin=TensionSignalOrigin.EXTERNAL_UNTRUSTED,
        ),
    )
    entry = _tension_by_anchor(second, target)
    assert entry is not None
    assert entry.current_status != TensionLifecycleStatus.REACTIVATED
    assert entry.weak_wake_signal_ignored is True
    assert C02RestrictionCode.WEAK_WAKE_SIGNAL_ORIGIN_IGNORED in second.downstream_gate.restrictions


def test_c02_weak_origin_closure_signal_is_ignored() -> None:
    upstream = build_c02_upstream(
        case_id="c02-weak-closure",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    anchor = first.state.tensions[0].causal_anchor
    second = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            closure_evidence_anchor_keys=(anchor,),
            closure_signal_origin=TensionSignalOrigin.EXTERNAL_UNTRUSTED,
        ),
    )
    entry = _tension_by_anchor(second, anchor)
    assert entry is not None
    assert entry.current_status != TensionLifecycleStatus.CLOSED
    assert entry.weak_closure_signal_ignored is True
    assert C02RestrictionCode.WEAK_CLOSURE_SIGNAL_ORIGIN_IGNORED in second.downstream_gate.restrictions


def test_c02_stale_is_not_closed_and_release_remains_distinct() -> None:
    upstream = build_c02_upstream(
        case_id="c02-stale-closed",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    anchor = first.state.tensions[0].causal_anchor
    closed = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            closure_evidence_anchor_keys=(anchor,),
        ),
    )
    staleish = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            stale_after_steps=1,
            release_after_steps=2,
            closure_evidence_anchor_keys=(),
        ),
    )
    closed_entry = _tension_by_anchor(closed, anchor)
    stale_entry = _tension_by_anchor(staleish, anchor)
    assert closed_entry is not None and stale_entry is not None
    assert closed_entry.current_status == TensionLifecycleStatus.CLOSED
    assert stale_entry.current_status != TensionLifecycleStatus.CLOSED
    assert stale_entry.scheduling_mode != TensionSchedulingMode.MONITOR_PASSIVELY or stale_entry.decay_state.value in {"stale", "released", "decaying"}


def test_c02_ablation_without_suppression_changes_lifecycle_topology() -> None:
    upstream = build_c02_upstream(
        case_id="c02-ablate",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    baseline = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(allow_suppression=True),
    )
    ablated = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TensionSchedulerContext(allow_suppression=False),
    )

    baseline_modes = {entry.scheduling_mode for entry in baseline.state.tensions}
    ablated_modes = {entry.scheduling_mode for entry in ablated.state.tensions}
    assert (
        TensionSchedulingMode.SUPPRESS_TEMPORARILY in baseline_modes
        or baseline.state.suppression_active
    )
    assert TensionSchedulingMode.SUPPRESS_TEMPORARILY not in ablated_modes


def test_c02_memory_retrieval_without_reopen_does_not_activate_closed_tension() -> None:
    first_upstream = build_c02_upstream(
        case_id="c02-memory-1",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
    )
    anchor = first.state.tensions[0].causal_anchor
    closed = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=first.state,
            closure_evidence_anchor_keys=(anchor,),
        ),
    )
    retrieval_only = build_tension_scheduler(
        first_upstream.stream,
        first_upstream.regulation,
        first_upstream.affordances,
        first_upstream.preferences,
        first_upstream.viability,
        context=TensionSchedulerContext(
            prior_scheduler_state=closed.state,
            retrieved_episode_refs=(anchor,),
        ),
    )
    entry = _tension_by_anchor(retrieval_only, anchor)
    assert entry is not None
    assert entry.current_status == TensionLifecycleStatus.CLOSED
    assert entry.scheduling_mode == TensionSchedulingMode.MONITOR_PASSIVELY


def test_c02_downstream_consumer_obedience_changes_with_schedule_state() -> None:
    active_upstream = build_c02_upstream(
        case_id="c02-consumer-active",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    active = build_tension_scheduler(
        active_upstream.stream,
        active_upstream.regulation,
        active_upstream.affordances,
        active_upstream.preferences,
        active_upstream.viability,
    )
    active_mode = choose_tension_execution_mode(active)
    active_targets = select_revisit_tensions(active)

    weak_upstream = build_c02_upstream(
        case_id="c02-consumer-weak",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    weak = build_tension_scheduler(
        weak_upstream.stream,
        weak_upstream.regulation,
        weak_upstream.affordances,
        weak_upstream.preferences,
        weak_upstream.viability,
        context=TensionSchedulerContext(require_strong_priority_basis=True),
    )
    weak_mode = choose_tension_execution_mode(weak)
    weak_targets = select_revisit_tensions(weak)
    weak_view = derive_tension_scheduler_contract_view(weak)

    assert active_mode in {"revisit_now", "revisit_with_limits", "defer_and_monitor"}
    assert len(active_targets) >= 1
    assert weak_mode in {"hold_or_repair", "escalate_for_resolution", "monitor_background", "idle"}
    assert weak_view.unschedulable_present or weak_view.no_safe_defer_present or weak_view.usability_class.value != "usable_bounded"
    assert active_mode != weak_mode or active_targets != weak_targets
