from __future__ import annotations

from substrate.s01_efference_copy import (
    S01ComparisonStatus,
    derive_s01_contract_view,
)
from tests.substrate.s01_efference_copy_testkit import build_s01


def test_s01_pre_observation_registry_is_created_before_observation() -> None:
    first = build_s01(
        case_id="registry",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
    )
    view = derive_s01_contract_view(first)
    assert view.pending_predictions_count > 0
    assert view.comparisons_count == 0
    assert view.no_post_hoc_prediction_fabrication is True


def test_s01_internal_act_match_case() -> None:
    first = build_s01(
        case_id="internal-match",
        tick_index=1,
        emit_world_action_candidate=True,
    )
    second = build_s01(
        case_id="internal-match",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
        prior_state=first.state,
    )
    statuses = {item.status for item in second.state.comparisons}
    assert S01ComparisonStatus.MATCHED_AS_EXPECTED in statuses or S01ComparisonStatus.LATENCY_MISMATCH in statuses


def test_s01_expected_but_unobserved_after_expiry() -> None:
    first = build_s01(
        case_id="unobserved",
        tick_index=1,
        emit_world_action_candidate=True,
    )
    second = build_s01(
        case_id="unobserved",
        tick_index=2,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
        prior_state=first.state,
    )
    third = build_s01(
        case_id="unobserved",
        tick_index=4,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
        prior_state=second.state,
    )
    assert third.state.stale_prediction_detected is True
    assert any(
        item.status == S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED
        for item in third.state.comparisons
    )


def test_s01_delayed_effect_stays_provisional_before_expiry_and_closes_after_observation() -> None:
    first = build_s01(
        case_id="delay",
        tick_index=1,
        emit_world_action_candidate=True,
    )
    second = build_s01(
        case_id="delay",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
        prior_state=first.state,
    )
    assert any(
        item.status == S01ComparisonStatus.PARTIAL_MATCH
        for item in second.state.comparisons
    )
    third = build_s01(
        case_id="delay",
        tick_index=3,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
        prior_state=second.state,
    )
    assert any(
        item.status in {
            S01ComparisonStatus.MATCHED_AS_EXPECTED,
            S01ComparisonStatus.LATENCY_MISMATCH,
        }
        for item in third.state.comparisons
    )


def test_s01_external_perturbation_without_live_prediction_is_unexpected_change() -> None:
    result = build_s01(
        case_id="unexpected",
        tick_index=1,
        register_prediction=False,
        world_effect_feedback_correlated=True,
    )
    assert result.state.unexpected_change_detected is True
    assert any(
        item.status == S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED
        for item in result.state.comparisons
    )


def test_s01_mixed_cause_contamination_blocks_strong_comparison_claim() -> None:
    first = build_s01(case_id="contamination", tick_index=1, emit_world_action_candidate=True)
    second = build_s01(
        case_id="contamination",
        tick_index=2,
        prior_state=first.state,
        c05_dependency_contaminated=True,
        world_degraded=True,
    )
    assert second.state.comparison_blocked_by_contamination is True
    assert second.state.strong_self_attribution_allowed is False
    assert any(
        item.status == S01ComparisonStatus.COMPARISON_BLOCKED_BY_CONTAMINATION
        for item in second.state.comparisons
    )


def test_s01_mode_driven_transition_generates_mode_mismatch_entry() -> None:
    first = build_s01(case_id="mode-transition", tick_index=1, c04_selected_mode="continue_stream")
    second = build_s01(
        case_id="mode-transition",
        tick_index=2,
        c04_selected_mode="run_recovery",
        prior_selected_mode="continue_stream",
        prior_state=first.state,
    )
    assert any(
        item.axis.value == "mode_token"
        and item.status == S01ComparisonStatus.DIRECTION_MISMATCH
        for item in second.state.comparisons
    )


def test_s01_stale_prediction_is_not_reused_after_expiry() -> None:
    first = build_s01(case_id="stale", tick_index=1, emit_world_action_candidate=True)
    first_prediction_ids = {item.prediction_id for item in first.state.pending_predictions}
    late = build_s01(
        case_id="stale",
        tick_index=5,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
        prior_state=first.state,
    )
    assert late.state.stale_prediction_detected is True
    late_prediction_ids = {item.prediction_id for item in late.state.pending_predictions}
    assert first_prediction_ids.isdisjoint(late_prediction_ids)


def test_s01_ablation_without_pre_observation_prediction_collapses_claimed_behavior() -> None:
    registered_first = build_s01(case_id="ablation", tick_index=1, emit_world_action_candidate=True)
    registered_second = build_s01(
        case_id="ablation",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
        prior_state=registered_first.state,
    )
    ablated_second = build_s01(
        case_id="ablation",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
        prior_state=None,
        register_prediction=False,
    )
    assert registered_second.state.unexpected_change_detected is False
    assert ablated_second.state.unexpected_change_detected is True


def test_s01_mismatch_typing_is_graded_not_binary() -> None:
    first = build_s01(
        case_id="graded",
        tick_index=1,
        emit_world_action_candidate=True,
        world_confidence=0.60,
    )
    second = build_s01(
        case_id="graded",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
        world_confidence=0.30,
        prior_state=first.state,
    )
    statuses = {item.status for item in second.state.comparisons}
    assert S01ComparisonStatus.PARTIAL_MATCH in statuses
    assert (
        S01ComparisonStatus.DIRECTION_MISMATCH in statuses
        or S01ComparisonStatus.MAGNITUDE_MISMATCH in statuses
    )
