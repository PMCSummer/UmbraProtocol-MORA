from __future__ import annotations

from dataclasses import replace

from substrate.mode_arbitration import (
    EndogenousTickKind,
    HoldSwitchDecision,
    ModeArbitrationContext,
    SubjectMode,
    build_mode_arbitration,
    can_run_mode_candidate,
    choose_subject_execution_mode,
    derive_mode_arbitration_contract_view,
    eligible_mode_candidates,
)
from substrate.tension_scheduler import TensionSchedulerContext
from tests.substrate.c04_testkit import build_c04_upstream


def _build_result(upstream, **context_overrides):
    return build_mode_arbitration(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=ModeArbitrationContext(**context_overrides),
    )


def test_c04_generates_typed_mode_arbitration_state_and_gate() -> None:
    upstream = build_c04_upstream(
        case_id="c04-gen",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = _build_result(upstream)

    assert result.state.arbitration_id
    assert result.state.tick_id
    assert result.state.active_mode in set(SubjectMode)
    assert result.state.mode_priority_vector
    assert result.state.candidate_modes
    assert result.downstream_gate.restrictions
    assert result.no_planner_mode_selection_dependency is True
    assert result.no_background_loop_dependency is True
    assert result.no_external_turn_substitution_dependency is True


def test_c04_endogenous_no_external_input_vs_safe_idle() -> None:
    pressured = build_c04_upstream(
        case_id="c04-endogenous-pressure",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    pressured_result = _build_result(pressured, external_turn_present=False)

    quiet = build_c04_upstream(
        case_id="c04-endogenous-quiet",
        energy=72.0,
        cognitive=38.0,
        safety=80.0,
        unresolved_preference=False,
    )
    quiet_result = _build_result(
        quiet,
        external_turn_present=False,
        allow_endogenous_tick=False,
    )

    assert pressured_result.state.endogenous_tick_kind in {
        EndogenousTickKind.ENDOGENOUS,
        EndogenousTickKind.DEGRADED_ENDOGENOUS,
    }
    assert pressured_result.state.active_mode != SubjectMode.SAFE_IDLE
    assert quiet_result.state.active_mode == SubjectMode.SAFE_IDLE
    assert quiet_result.state.hold_or_switch_decision in {
        HoldSwitchDecision.SAFE_IDLE_ONLY,
        HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
    }


def test_c04_same_external_context_different_internal_pressures_changes_mode() -> None:
    survival = build_c04_upstream(
        case_id="c04-contrast-survival",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    diversified = build_c04_upstream(
        case_id="c04-contrast-diversified",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    survival_result = _build_result(survival, external_turn_present=True)
    diversified_result = _build_result(diversified, external_turn_present=True)

    assert survival_result.state.active_mode != diversified_result.state.active_mode or (
        survival_result.state.hold_or_switch_decision
        != diversified_result.state.hold_or_switch_decision
    )


def test_c04_hold_vs_switch_governance() -> None:
    seed = build_c04_upstream(
        case_id="c04-hold-seed",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = _build_result(seed)
    second = _build_result(
        seed,
        prior_mode_arbitration_state=first.state,
        external_turn_present=False,
    )

    assert second.state.hold_or_switch_decision in {
        HoldSwitchDecision.CONTINUE_CURRENT_MODE,
        HoldSwitchDecision.SWITCH_TO_MODE,
        HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
    }
    assert second.state.dwell_budget_remaining <= first.state.dwell_budget_remaining


def test_c04_dwell_budget_perturbation_changes_rearbitration_timing() -> None:
    upstream = build_c04_upstream(
        case_id="c04-dwell",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    first = _build_result(upstream, default_dwell_budget=1)
    second = _build_result(
        upstream,
        prior_mode_arbitration_state=first.state,
        default_dwell_budget=1,
    )
    third = _build_result(
        upstream,
        prior_mode_arbitration_state=second.state,
        default_dwell_budget=1,
    )

    assert second.state.dwell_budget_remaining <= first.state.dwell_budget_remaining
    assert third.state.forced_rearbitration is True or third.state.hold_or_switch_decision in {
        HoldSwitchDecision.FORCED_REARBITRATION,
        HoldSwitchDecision.SWITCH_TO_MODE,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
    }


def test_c04_interruption_governance_survival_progress_and_weak_event() -> None:
    base = build_c04_upstream(
        case_id="c04-interruption",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    strong_survival = _build_result(base)
    weak_event = _build_result(
        base,
        prior_mode_arbitration_state=strong_survival.state,
        weak_external_event=True,
        external_turn_present=True,
    )
    progress_event = _build_result(
        base,
        prior_mode_arbitration_state=strong_survival.state,
        closure_progress_event=True,
        external_turn_present=False,
    )

    assert strong_survival.state.active_mode in {
        SubjectMode.RECOVERY_MODE,
        SubjectMode.REVISIT_UNRESOLVED_TENSION,
        SubjectMode.HOLD_CURRENT_STREAM,
    }
    assert weak_event.state.hold_or_switch_decision in {
        HoldSwitchDecision.CONTINUE_CURRENT_MODE,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
    }
    assert progress_event.state.endogenous_tick_allowed is True


def test_c04_reactive_masquerade_external_only_degrades_endogenous_claim() -> None:
    upstream = build_c04_upstream(
        case_id="c04-reactive",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    endogenous = _build_result(upstream, external_turn_present=False)
    reactive_only = _build_result(
        upstream,
        external_turn_present=True,
        allow_endogenous_tick=False,
    )

    assert endogenous.state.endogenous_tick_allowed is True
    assert reactive_only.state.endogenous_tick_kind == EndogenousTickKind.EXTERNAL_REACTIVE
    assert reactive_only.state.endogenous_tick_allowed is False
    assert reactive_only.state.active_mode in {
        SubjectMode.SAFE_IDLE,
        SubjectMode.PASSIVE_MONITORING,
        SubjectMode.HOLD_CURRENT_STREAM,
    }


def test_c04_mode_churn_adversarial_prefers_conflict_or_hold() -> None:
    upstream = build_c04_upstream(
        case_id="c04-churn",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    first = _build_result(upstream)
    second = _build_result(
        upstream,
        prior_mode_arbitration_state=first.state,
        conflict_margin=0.25,
        min_confidence_for_switch=0.7,
    )

    assert second.state.hold_or_switch_decision in {
        HoldSwitchDecision.ARBITRATION_CONFLICT,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
        HoldSwitchDecision.CONTINUE_CURRENT_MODE,
        HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
    }


def test_c04_permanent_hold_adversarial_forces_recheck() -> None:
    upstream = build_c04_upstream(
        case_id="c04-hold-recheck",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    first = _build_result(upstream, default_dwell_budget=0)
    second = _build_result(
        upstream,
        prior_mode_arbitration_state=first.state,
        default_dwell_budget=0,
    )

    assert second.state.forced_rearbitration is True or second.state.hold_or_switch_decision in {
        HoldSwitchDecision.FORCED_REARBITRATION,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
    }


def test_c04_ablation_survival_diversification_and_dwell_are_load_bearing() -> None:
    pressure = build_c04_upstream(
        case_id="c04-ablation-pressure",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    base = _build_result(pressure)
    no_endogenous = _build_result(
        pressure,
        allow_endogenous_tick=False,
        external_turn_present=True,
    )
    non_survival = build_c04_upstream(
        case_id="c04-ablation-nondwell",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    no_dwell_seed = _build_result(non_survival, default_dwell_budget=0)
    no_dwell = _build_result(
        non_survival,
        prior_mode_arbitration_state=no_dwell_seed.state,
        default_dwell_budget=0,
    )

    assert base.state.endogenous_tick_allowed is True
    assert no_endogenous.state.endogenous_tick_allowed is False
    assert no_endogenous.state.active_mode != base.state.active_mode or (
        no_endogenous.state.hold_or_switch_decision != base.state.hold_or_switch_decision
    )
    assert no_dwell.state.forced_rearbitration is True or (
        no_dwell.state.hold_or_switch_decision
        in {
            HoldSwitchDecision.FORCED_REARBITRATION,
            HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
        }
    )


def test_c04_downstream_obedience_with_and_without_governance() -> None:
    pressured = build_c04_upstream(
        case_id="c04-consumer-pressure",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    governed = _build_result(pressured)
    degraded = _build_result(
        pressured,
        allow_endogenous_tick=False,
        external_turn_present=True,
    )

    governed_mode = choose_subject_execution_mode(governed)
    degraded_mode = choose_subject_execution_mode(degraded)
    governed_candidates = eligible_mode_candidates(governed)
    degraded_candidates = eligible_mode_candidates(degraded)

    assert governed_mode != degraded_mode or governed_candidates != degraded_candidates
    assert can_run_mode_candidate(governed, governed.state.active_mode.value) is True
    assert can_run_mode_candidate(degraded, SubjectMode.DIVERSIFICATION_PROBE.value) is False or (
        degraded.state.endogenous_tick_allowed is False
    )


def test_c04_causal_contour_stability_bounded_role() -> None:
    upstream = build_c04_upstream(
        case_id="c04-contour-role",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
        scheduler_context=TensionSchedulerContext(require_strong_priority_basis=False),
    )
    result = _build_result(upstream, external_turn_present=False)
    view = derive_mode_arbitration_contract_view(result)

    assert result.state.arbitration_basis
    assert SubjectMode.SAFE_IDLE in set(SubjectMode)
    assert view.active_mode == result.state.active_mode
    assert view.requires_restrictions_read is True
    assert result.state.active_mode != SubjectMode.DIVERSIFICATION_PROBE or (
        upstream.diversification.state.actionable_alternative_classes
    )


def test_c04_weak_basis_monotonic_fallback() -> None:
    none_upstream = build_c04_upstream(
        case_id="c04-weak-basis-none",
        energy=72.0,
        cognitive=38.0,
        safety=80.0,
        unresolved_preference=False,
    )
    none_result = _build_result(
        none_upstream,
        external_turn_present=False,
        allow_endogenous_tick=False,
    )

    weak_upstream = build_c04_upstream(
        case_id="c04-weak-basis-weak",
        energy=64.0,
        cognitive=46.0,
        safety=70.0,
        unresolved_preference=True,
    )
    weak_result = _build_result(
        weak_upstream,
        external_turn_present=False,
        allow_endogenous_tick=True,
        min_confidence_for_switch=0.7,
    )

    strong_upstream = build_c04_upstream(
        case_id="c04-weak-basis-strong",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    strong_result = _build_result(
        strong_upstream,
        external_turn_present=False,
        allow_endogenous_tick=True,
    )

    assert none_result.state.active_mode == SubjectMode.SAFE_IDLE
    assert "continuity_carryover_present" in weak_result.state.arbitration_basis
    assert weak_result.state.active_mode in {
        SubjectMode.PASSIVE_MONITORING,
        SubjectMode.HOLD_CURRENT_STREAM,
        SubjectMode.REVISIT_UNRESOLVED_TENSION,
        SubjectMode.RECOVERY_MODE,
        SubjectMode.OUTPUT_PREPARATION,
        SubjectMode.DIVERSIFICATION_PROBE,
    }
    assert strong_result.state.active_mode != SubjectMode.SAFE_IDLE
    assert strong_result.state.arbitration_confidence >= weak_result.state.arbitration_confidence


def test_c04_repeated_forced_rearb_chain_does_not_spin_forever() -> None:
    upstream = build_c04_upstream(
        case_id="c04-rearb-chain",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )

    prior = None
    chain = []
    for _ in range(7):
        result = _build_result(
            upstream,
            prior_mode_arbitration_state=prior,
            external_turn_present=False,
            conflict_margin=0.2,
            min_confidence_for_switch=0.7,
            default_dwell_budget=1,
        )
        chain.append(result)
        prior = result.state

    forced_flags = [
        item.state.forced_rearbitration
        or item.state.hold_or_switch_decision == HoldSwitchDecision.FORCED_REARBITRATION
        for item in chain
    ]
    max_consecutive_forced = 0
    current = 0
    for flag in forced_flags:
        if flag:
            current += 1
            max_consecutive_forced = max(max_consecutive_forced, current)
        else:
            current = 0

    assert max_consecutive_forced <= 1
    assert any(
        item.state.hold_or_switch_decision == HoldSwitchDecision.NO_CLEAR_MODE_WINNER
        for item in chain
    )


def test_c04_external_reactive_cannot_mimic_strong_endogenous_continue_without_extra_basis() -> None:
    upstream = build_c04_upstream(
        case_id="c04-external-vs-endogenous",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    seed = _build_result(
        upstream,
        external_turn_present=False,
        allow_endogenous_tick=True,
        conflict_margin=0.03,
        min_confidence_for_switch=0.55,
    )
    assert seed.state.active_mode == SubjectMode.HOLD_CURRENT_STREAM

    endogenous_follow = _build_result(
        upstream,
        prior_mode_arbitration_state=seed.state,
        external_turn_present=False,
        allow_endogenous_tick=True,
    )
    external_no_basis = _build_result(
        upstream,
        prior_mode_arbitration_state=seed.state,
        external_turn_present=True,
        allow_endogenous_tick=False,
        closure_progress_event=False,
    )

    endogenous_mode = choose_subject_execution_mode(endogenous_follow)
    external_mode = choose_subject_execution_mode(external_no_basis)

    assert external_mode != "continue_stream"
    assert external_no_basis.state.hold_or_switch_decision != HoldSwitchDecision.CONTINUE_CURRENT_MODE
    assert endogenous_mode != external_mode or (
        endogenous_follow.state.active_mode != external_no_basis.state.active_mode
    )


def test_c04_survival_hold_deescalates_without_monopoly_after_pressure_weakens() -> None:
    critical_upstream = build_c04_upstream(
        case_id="c04-survival-deescalation-critical",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    first = _build_result(critical_upstream, external_turn_present=False)

    deescalated_upstream = build_c04_upstream(
        case_id="c04-survival-deescalation-elevated",
        energy=76.0,
        cognitive=36.0,
        safety=86.0,
        unresolved_preference=False,
        prior_stream_state=critical_upstream.stream.state,
        prior_scheduler_state=critical_upstream.scheduler.state,
        prior_diversification_state=critical_upstream.diversification.state,
    )
    second = _build_result(
        deescalated_upstream,
        prior_mode_arbitration_state=first.state,
        external_turn_present=False,
    )
    third = _build_result(
        deescalated_upstream,
        prior_mode_arbitration_state=second.state,
        external_turn_present=False,
    )
    fourth = _build_result(
        deescalated_upstream,
        prior_mode_arbitration_state=third.state,
        external_turn_present=False,
    )

    assert first.state.active_mode == SubjectMode.RECOVERY_MODE
    assert any(
        state.state.active_mode != SubjectMode.RECOVERY_MODE
        for state in (second, third, fourth)
    )
    assert all(
        state.state.hold_or_switch_decision
        != HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL
        for state in (second, third, fourth)
    )
    assert any(
        any(
            score.enabled and score.mode != SubjectMode.RECOVERY_MODE
            for score in state.state.mode_priority_vector
        )
        for state in (second, third, fourth)
    )
