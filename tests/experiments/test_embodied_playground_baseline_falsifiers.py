from __future__ import annotations

from experiments.embodied_playground.baseline_falsifiers import (
    abstention_counted_as_simple_failure,
    action_space_as_permission_baseline_not_detected,
    baseline_gets_more_info_than_mora,
    comparison_report_counts_direct_bridge_as_subject_success,
    comparison_report_counts_unfair_oracle_as_fair_win,
    comparison_report_missing_baseline_traces,
    comparison_report_missing_boundary_summary,
    comparison_report_missing_differentiator_summary,
    comparison_report_missing_fairness_report,
    comparison_report_missing_mora_trace,
    comparison_report_overclaims_general_intelligence,
    diagnostic_baseline_misreported_as_mora,
    direct_bridge_counted_as_subject_success,
    drive_as_permission_baseline_not_detected,
    effect_feedback_not_compared,
    heuristic_indistinguishable_from_mora,
    hidden_eval_usage_not_reported,
    hidden_oracle_treated_as_fair,
    matrix_report_missing_required_scenario,
    metric_summary_missing_matched_information_score,
    mora_boundary_violation_not_reported,
    provenance_not_measured,
    scenario_label_used_by_baseline,
    success_without_boundary_integrity,
    visible_object_as_pickup_baseline_not_detected,
)
from experiments.embodied_playground.baselines import BaselineFairnessClass


def test_baseline_falsifier_presence() -> None:
    required = [
        baseline_gets_more_info_than_mora,
        hidden_oracle_treated_as_fair,
        direct_bridge_counted_as_subject_success,
        success_without_boundary_integrity,
        abstention_counted_as_simple_failure,
        heuristic_indistinguishable_from_mora,
        action_space_as_permission_baseline_not_detected,
        visible_object_as_pickup_baseline_not_detected,
        drive_as_permission_baseline_not_detected,
        hidden_eval_usage_not_reported,
        mora_boundary_violation_not_reported,
        diagnostic_baseline_misreported_as_mora,
        effect_feedback_not_compared,
        provenance_not_measured,
        scenario_label_used_by_baseline,
        comparison_report_missing_mora_trace,
        comparison_report_missing_baseline_traces,
        comparison_report_missing_fairness_report,
        comparison_report_counts_unfair_oracle_as_fair_win,
        comparison_report_counts_direct_bridge_as_subject_success,
        comparison_report_missing_boundary_summary,
        comparison_report_missing_differentiator_summary,
        comparison_report_overclaims_general_intelligence,
        matrix_report_missing_required_scenario,
        metric_summary_missing_matched_information_score,
    ]
    assert len(required) == 25


def test_falsifier_negative_controls() -> None:
    assert baseline_gets_more_info_than_mora(
        fairness_class=BaselineFairnessClass.FAIR_PUBLIC,
        used_hidden_or_eval=True,
    ) is True
    assert baseline_gets_more_info_than_mora(
        fairness_class=BaselineFairnessClass.DIAGNOSTIC_UNFAIR,
        used_hidden_or_eval=True,
    ) is False

    assert hidden_oracle_treated_as_fair(
        controller_kind="hidden_oracle_baseline",
        fairness_class=BaselineFairnessClass.FAIR_PUBLIC,
    ) is True
    assert direct_bridge_counted_as_subject_success(
        controller_kind="direct_bridge_bypass_baseline",
        ap01_bypassed=True,
        counted_as_honest=True,
    ) is True
    assert success_without_boundary_integrity(success_counted=True, boundary_integrity_ok=False) is True
    assert abstention_counted_as_simple_failure(
        abstained=True,
        insufficient_basis=True,
        counted_as_failure_only=True,
    ) is True
    assert heuristic_indistinguishable_from_mora(
        mora_actions=(None,),
        heuristic_actions=(None,),
    ) is True
    assert action_space_as_permission_baseline_not_detected(
        controller_kind="action_space_greedy_baseline",
        acted_from_surface_only=True,
        weakness_recorded=False,
    ) is True
    assert visible_object_as_pickup_baseline_not_detected(
        controller_kind="visible_object_heuristic_baseline",
        acted_from_visible_object_only=True,
        weakness_recorded=False,
    ) is True
    assert drive_as_permission_baseline_not_detected(
        controller_kind="drive_only_baseline",
        acted_from_drive_only=True,
        weakness_recorded=False,
    ) is True
    assert hidden_eval_usage_not_reported(used_hidden_eval=True, reported_hidden_eval_usage=False) is True
    assert mora_boundary_violation_not_reported(mora_boundary_violation=True, reported=False) is True
    assert diagnostic_baseline_misreported_as_mora(
        controller_kind="hidden_oracle_baseline",
        attached_to_mora_trace=True,
    ) is True
    assert effect_feedback_not_compared(compared=False) is True
    assert provenance_not_measured(metric_has_provenance=False) is True
    assert scenario_label_used_by_baseline({"args": {"basis": "scenario_id:pickup_bias"}}) is True
    assert scenario_label_used_by_baseline({"args": {"basis": "observation_refs"}}) is False


def test_p8b_report_falsifier_negative_controls() -> None:
    payload = {
        "mora_trace": {"subject_tick_used": True},
        "baseline_traces": [{"controller_id": "baseline:random_action"}],
        "fairness_report": {
            "fair_baselines": ["baseline:random_action"],
            "diagnostic_unfair_baselines": ["baseline:hidden_oracle"],
            "boundary_violation_baselines": ["baseline:direct_bridge_bypass"],
            "excluded_from_fair_comparison": ["baseline:hidden_oracle", "baseline:direct_bridge_bypass"],
        },
        "boundary_violation_summary": {
            "ap01_bypass_count": 1,
            "hidden_eval_usage_count": 0,
            "scenario_label_usage_count": 0,
            "request_as_execution_count": 1,
        },
        "differentiator_summary": {"key_differences": ["visible_object_no_drive"]},
        "metric_summary": {"matched_information_score": 1.0},
    }
    assert comparison_report_missing_mora_trace(payload) is False
    assert comparison_report_missing_baseline_traces(payload) is False
    assert comparison_report_missing_fairness_report(payload) is False
    assert comparison_report_counts_unfair_oracle_as_fair_win(
        fairness_report=payload["fairness_report"]
    ) is False
    assert comparison_report_counts_direct_bridge_as_subject_success(
        boundary_violation_summary=payload["boundary_violation_summary"]
    ) is False
    assert comparison_report_missing_boundary_summary(payload) is False
    assert comparison_report_missing_differentiator_summary(payload) is False
    assert comparison_report_overclaims_general_intelligence(
        "MORA supports boundary evidence only, not consciousness proof."
    ) is False
    assert matrix_report_missing_required_scenario(
        scenario_ids=(
            "visible_item_pickup_available",
            "visible_flask_no_drive",
            "water_need_no_visible_water",
            "inventory_capacity_block",
            "pickup_without_proximity",
            "action_space_only_no_candidate",
            "hidden_map_not_visible",
            "previous_blocked_effect_revalidation",
        )
    ) is False
    assert metric_summary_missing_matched_information_score(payload["metric_summary"]) is False
