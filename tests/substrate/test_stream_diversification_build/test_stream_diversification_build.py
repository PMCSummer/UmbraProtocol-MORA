from __future__ import annotations

from dataclasses import replace

from substrate.stream_diversification import (
    AlternativePathClass,
    DiversificationDecisionStatus,
    DiversificationTransitionClass,
    ProgressEvidenceClass,
    StreamDiversificationContext,
    build_stream_diversification,
    choose_diversification_execution_mode,
    derive_stream_diversification_contract_view,
    select_alternative_path_candidates,
)
from substrate.tension_scheduler import (
    TensionLifecycleStatus,
    TensionSchedulerContext,
    TensionSchedulingMode,
    TensionWakeCause,
)
from tests.substrate.c03_testkit import build_c03_upstream


def _assessment_for(result, tension_id: str):
    for assessment in result.state.path_assessments:
        if assessment.tension_id == tension_id:
            return assessment
    raise AssertionError(f"missing assessment for tension_id={tension_id}")


def _with_first_tension(state, first_entry):
    return replace(state, tensions=(first_entry, *state.tensions[1:]))


def _build_with_prior(upstream, prior_result, **context_overrides):
    context = StreamDiversificationContext(
        prior_diversification_state=prior_result.state,
        **context_overrides,
    )
    return build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=context,
    )


def _build_repeated_result(upstream, *, repeats: int, **context_overrides):
    result = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    for _ in range(repeats):
        result = _build_with_prior(upstream, result, **context_overrides)
    return result


def test_c03_generates_typed_diversification_state_and_gate() -> None:
    upstream = build_c03_upstream(
        case_id="c03-gen",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )

    assert result.state.diversification_id
    assert result.state.path_assessments
    assert result.state.redundancy_scores
    assert result.state.decision_status in set(DiversificationDecisionStatus)
    assert result.telemetry.ledger_events
    assert result.no_text_antirepeat_dependency is True
    assert result.no_randomness_dependency is True
    assert result.no_planner_arbitration_dependency is True


def test_c03_structural_vs_cosmetic_contrast_is_not_text_antirepeat() -> None:
    prior_upstream = build_c03_upstream(
        case_id="c03-structural-prior",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    prior = build_stream_diversification(
        prior_upstream.stream,
        prior_upstream.scheduler,
        prior_upstream.regulation,
        prior_upstream.affordances,
        prior_upstream.preferences,
        prior_upstream.viability,
    )
    target_anchor = prior_upstream.scheduler.state.tensions[0].causal_anchor

    same_surface = build_c03_upstream(
        case_id="c03-structural-prior",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        prior_stream_state=prior_upstream.stream.state,
        prior_scheduler_state=prior_upstream.scheduler.state,
    )
    shifted_causal = build_c03_upstream(
        case_id="c03-structural-prior",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        prior_stream_state=prior_upstream.stream.state,
        prior_scheduler_state=prior_upstream.scheduler.state,
        scheduler_context=TensionSchedulerContext(
            prior_scheduler_state=prior_upstream.scheduler.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(target_anchor,),
        ),
    )
    same_result = build_stream_diversification(
        same_surface.stream,
        same_surface.scheduler,
        same_surface.regulation,
        same_surface.affordances,
        same_surface.preferences,
        same_surface.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )
    shifted_result = build_stream_diversification(
        shifted_causal.stream,
        shifted_causal.scheduler,
        shifted_causal.regulation,
        shifted_causal.affordances,
        shifted_causal.preferences,
        shifted_causal.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    assert same_result.state.diversification_pressure >= shifted_result.state.diversification_pressure
    assert same_result.state.decision_status != shifted_result.state.decision_status or (
        same_result.state.stagnation_signatures != shifted_result.state.stagnation_signatures
    )


def test_c03_near_threshold_monotonicity_hardening() -> None:
    upstream = build_c03_upstream(
        case_id="c03-threshold",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    prior = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    first = upstream.scheduler.state.tensions[0]

    weak_noise_state = _with_first_tension(
        upstream.scheduler.state,
        replace(first, revisit_priority=min(1.0, first.revisit_priority + 0.05)),
    )
    weak_noise = build_stream_diversification(
        upstream.stream,
        weak_noise_state,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    just_below_state = _with_first_tension(
        upstream.scheduler.state,
        replace(
            first,
            scheduling_mode=TensionSchedulingMode.DEFER_UNTIL_CONDITION,
            revisit_priority=min(1.0, first.revisit_priority + 0.11),
        ),
    )
    just_below = build_stream_diversification(
        upstream.stream,
        just_below_state,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    just_above_state = _with_first_tension(
        upstream.scheduler.state,
        replace(
            first,
            current_status=TensionLifecycleStatus.DEFERRED,
            scheduling_mode=TensionSchedulingMode.DEFER_UNTIL_CONDITION,
            revisit_priority=max(0.0, first.revisit_priority - 0.13),
            reactivation_cause=TensionWakeCause.EXPLICIT_SIGNAL,
            matched_wake_triggers=("defer_window_expiry",),
        ),
    )
    just_above = build_stream_diversification(
        upstream.stream,
        just_above_state,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    strong_progress_state = _with_first_tension(
        upstream.scheduler.state,
        replace(
            first,
            current_status=TensionLifecycleStatus.CLOSED,
            scheduling_mode=TensionSchedulingMode.MONITOR_PASSIVELY,
            revisit_priority=0.0,
        ),
    )
    strong_progress = build_stream_diversification(
        upstream.stream,
        strong_progress_state,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )

    weak_noise_assessment = _assessment_for(weak_noise, first.tension_id)
    just_below_assessment = _assessment_for(just_below, first.tension_id)
    just_above_assessment = _assessment_for(just_above, first.tension_id)
    strong_progress_assessment = _assessment_for(strong_progress, first.tension_id)

    assert weak_noise_assessment.progress_evidence_class == ProgressEvidenceClass.WEAK
    assert just_below_assessment.progress_evidence_class == ProgressEvidenceClass.WEAK
    assert just_above_assessment.progress_evidence_class in {
        ProgressEvidenceClass.MODERATE,
        ProgressEvidenceClass.STRONG,
    }
    assert strong_progress_assessment.progress_evidence_class == ProgressEvidenceClass.STRONG
    assert weak_noise.state.diversification_pressure >= just_below.state.diversification_pressure
    assert just_below.state.diversification_pressure >= just_above.state.diversification_pressure
    assert just_above.state.diversification_pressure >= strong_progress.state.diversification_pressure
    assert weak_noise.state.decision_status != DiversificationDecisionStatus.ALTERNATIVE_PATH_OPENING
    assert just_below.state.decision_status != DiversificationDecisionStatus.ALTERNATIVE_PATH_OPENING


def test_c03_weak_progress_noise_does_not_clear_repeat_justification() -> None:
    upstream = build_c03_upstream(
        case_id="c03-weak-noise",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    prior = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    first = upstream.scheduler.state.tensions[0]
    noisy_state = _with_first_tension(
        upstream.scheduler.state,
        replace(first, revisit_priority=min(1.0, first.revisit_priority + 0.05)),
    )
    noisy = build_stream_diversification(
        upstream.stream,
        noisy_state,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )
    assessment = _assessment_for(noisy, first.tension_id)

    assert assessment.progress_evidence_class == ProgressEvidenceClass.WEAK
    assert assessment.progress_evidence_axes <= 1
    assert assessment.protected_recurrence is False
    assert assessment.repeat_requires_justification is True
    assert assessment.path_id in noisy.state.repeat_requires_justification_for


def test_c03_productive_recurrence_not_over_penalized() -> None:
    upstream = build_c03_upstream(
        case_id="c03-productive",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    prior = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    first = upstream.scheduler.state.tensions[0]

    no_progress = _build_with_prior(upstream, prior)
    small_real_state = _with_first_tension(
        upstream.scheduler.state,
        replace(
            first,
            current_status=TensionLifecycleStatus.DEFERRED,
            scheduling_mode=TensionSchedulingMode.DEFER_UNTIL_CONDITION,
            revisit_priority=max(0.0, first.revisit_priority - 0.13),
            reactivation_cause=TensionWakeCause.EXPLICIT_SIGNAL,
            matched_wake_triggers=("defer_window_expiry",),
        ),
    )
    small_real = build_stream_diversification(
        upstream.stream,
        small_real_state,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamDiversificationContext(prior_diversification_state=prior.state),
    )
    no_progress_assessment = _assessment_for(no_progress, first.tension_id)
    small_real_assessment = _assessment_for(small_real, first.tension_id)

    assert no_progress_assessment.progress_evidence_class == ProgressEvidenceClass.WEAK
    assert small_real_assessment.progress_evidence_class in {
        ProgressEvidenceClass.MODERATE,
        ProgressEvidenceClass.STRONG,
    }
    assert small_real_assessment.redundancy_score < no_progress_assessment.redundancy_score
    assert len(small_real_assessment.stagnation_signatures) <= len(
        no_progress_assessment.stagnation_signatures
    )
    assert small_real.state.diversification_pressure <= no_progress.state.diversification_pressure


def test_c03_alternative_opening_materiality_in_narrow_harness() -> None:
    pressured_upstream = build_c03_upstream(
        case_id="c03-alternatives-pressure",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    pressured = _build_repeated_result(
        pressured_upstream,
        repeats=3,
        stagnation_pressure_gain=0.34,
        pressure_edge_band=0.03,
    )
    pressured_mode = choose_diversification_execution_mode(pressured)
    pressured_candidates = select_alternative_path_candidates(pressured)

    protected_upstream = build_c03_upstream(
        case_id="c03-alternatives-protected",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        prior_stream_state=pressured_upstream.stream.state,
        prior_scheduler_state=pressured_upstream.scheduler.state,
        scheduler_context=TensionSchedulerContext(
            prior_scheduler_state=pressured_upstream.scheduler.state,
            explicit_wake_triggers=("defer_window_expiry",),
            wake_anchor_scope=(pressured_upstream.scheduler.state.tensions[0].causal_anchor,),
        ),
    )
    protected = build_stream_diversification(
        protected_upstream.stream,
        protected_upstream.scheduler,
        protected_upstream.regulation,
        protected_upstream.affordances,
        protected_upstream.preferences,
        protected_upstream.viability,
        context=StreamDiversificationContext(
            prior_diversification_state=pressured.state,
            stagnation_pressure_gain=0.34,
            pressure_edge_band=0.03,
        ),
    )
    protected_mode = choose_diversification_execution_mode(protected)
    protected_candidates = select_alternative_path_candidates(protected)

    assert pressured.state.diversification_pressure >= 0.4
    assert len(pressured_candidates) >= len(protected_candidates)
    assert bool(pressured.state.actionable_alternative_classes) or bool(
        pressured.state.allowed_alternative_classes
    )
    assert pressured_mode != protected_mode or pressured_candidates != protected_candidates


def test_c03_survival_protected_recurrence_filters_unsafe_candidates() -> None:
    upstream = build_c03_upstream(
        case_id="c03-survival-filter",
        energy=12.0,
        cognitive=95.0,
        safety=33.0,
        unresolved_preference=True,
    )
    result = _build_repeated_result(
        upstream,
        repeats=3,
        stagnation_pressure_gain=0.34,
        pressure_edge_band=0.03,
    )
    mode = choose_diversification_execution_mode(result)
    candidates = set(select_alternative_path_candidates(result))

    assert DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE in result.state.protected_recurrence_classes
    assert mode != "open_alternative_paths"
    assert not {
        AlternativePathClass.RAISE_BRANCH_CANDIDATE.value,
        AlternativePathClass.REFRAME_TENSION_ACCESS.value,
        AlternativePathClass.SWITCH_PROCESSING_MODE_CANDIDATE.value,
    }.intersection(candidates)


def test_c03_mixed_topology_conflict_degrades_candidate_freedom() -> None:
    upstream = build_c03_upstream(
        case_id="c03-survival-conflict",
        energy=12.0,
        cognitive=95.0,
        safety=33.0,
        unresolved_preference=True,
    )
    result = _build_repeated_result(
        upstream,
        repeats=4,
        stagnation_pressure_gain=0.34,
        pressure_edge_band=0.03,
    )
    mode = choose_diversification_execution_mode(result)
    candidates = select_alternative_path_candidates(result)

    assert DiversificationTransitionClass.SURVIVAL_PROTECTED_ROUTE in result.state.protected_recurrence_classes
    assert result.state.diversification_conflict_with_survival is True
    assert candidates == ()
    assert mode in {"continue_with_protection", "hold_current_route", "request_additional_basis"}


def test_c03_anti_repeat_baseline_comparison_not_equivalent_to_naive_block() -> None:
    def _naive_mode(repetition_count: int) -> str:
        return "diversify" if repetition_count >= 2 else "continue"

    upstream = build_c03_upstream(
        case_id="c03-baseline",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    result = _build_repeated_result(
        upstream,
        repeats=2,
        stagnation_pressure_gain=0.34,
        pressure_edge_band=0.03,
    )
    mode = choose_diversification_execution_mode(result)
    repetition = max(assessment.repetition_count for assessment in result.state.path_assessments)

    assert _naive_mode(repetition) == "diversify"
    assert mode in {
        "continue_current_route",
        "monitor_for_stagnation",
        "request_additional_basis",
        "open_alternative_paths",
        "continue_with_protection",
        "hold_current_route",
    }
    assert mode != "open_alternative_paths" or bool(result.state.actionable_alternative_classes)


def test_c03_ablation_without_structural_detection_degrades_loop_handling() -> None:
    upstream = build_c03_upstream(
        case_id="c03-ablation",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    prior = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    full = _build_with_prior(upstream, prior)
    ablated = _build_with_prior(
        upstream,
        prior,
        disable_structural_stagnation_detection=True,
        disable_repeat_justification_gating=True,
    )

    assert full.state.diversification_pressure >= ablated.state.diversification_pressure
    assert bool(full.state.stagnation_signatures) or bool(full.state.repeat_requires_justification_for)
    assert not ablated.state.stagnation_signatures


def test_c03_narrow_contour_regression_keeps_c01_c02_roles_intact() -> None:
    upstream = build_c03_upstream(
        case_id="c03-contour",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    view = derive_stream_diversification_contract_view(result)

    assert upstream.scheduler.state.tensions
    assert all(
        assessment.current_status in {entry.current_status.value for entry in upstream.scheduler.state.tensions}
        for assessment in result.state.path_assessments
    )
    assert view.decision_status != DiversificationDecisionStatus.NO_SAFE_DIVERSIFICATION or (
        view.no_safe_diversification is True
    )
