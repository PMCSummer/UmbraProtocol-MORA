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


def test_p8_falsifier_baseline_gets_more_info_than_mora_negative_control() -> None:
    assert baseline_gets_more_info_than_mora(
        fairness_class=BaselineFairnessClass.FAIR_PUBLIC,
        used_hidden_or_eval=True,
    ) is True


def test_p8_falsifier_hidden_oracle_treated_as_fair_negative_control() -> None:
    assert hidden_oracle_treated_as_fair(
        controller_kind="hidden_oracle_baseline",
        fairness_class=BaselineFairnessClass.FAIR_PUBLIC,
    ) is True


def test_p8_falsifier_direct_bridge_counted_as_subject_success_negative_control() -> None:
    assert direct_bridge_counted_as_subject_success(
        controller_kind="direct_bridge_bypass_baseline",
        ap01_bypassed=True,
        counted_as_honest=True,
    ) is True


def test_p8_falsifier_success_without_boundary_integrity_negative_control() -> None:
    assert success_without_boundary_integrity(success_counted=True, boundary_integrity_ok=False) is True


def test_p8_falsifier_abstention_counted_as_simple_failure_negative_control() -> None:
    assert abstention_counted_as_simple_failure(
        abstained=True,
        insufficient_basis=True,
        counted_as_failure_only=True,
    ) is True


def test_p8_falsifier_heuristic_indistinguishable_from_mora_negative_control() -> None:
    assert heuristic_indistinguishable_from_mora(
        mora_actions=("pickup", None),
        heuristic_actions=("pickup", None),
    ) is True


def test_p8_falsifier_action_space_as_permission_baseline_not_detected_negative_control() -> None:
    assert action_space_as_permission_baseline_not_detected(
        controller_kind="action_space_greedy_baseline",
        acted_from_surface_only=True,
        weakness_recorded=False,
    ) is True


def test_p8_falsifier_visible_object_as_pickup_baseline_not_detected_negative_control() -> None:
    assert visible_object_as_pickup_baseline_not_detected(
        controller_kind="visible_object_heuristic_baseline",
        acted_from_visible_object_only=True,
        weakness_recorded=False,
    ) is True


def test_p8_falsifier_drive_as_permission_baseline_not_detected_negative_control() -> None:
    assert drive_as_permission_baseline_not_detected(
        controller_kind="drive_only_baseline",
        acted_from_drive_only=True,
        weakness_recorded=False,
    ) is True


def test_p8_falsifier_hidden_eval_usage_not_reported_negative_control() -> None:
    assert hidden_eval_usage_not_reported(used_hidden_eval=True, reported_hidden_eval_usage=False) is True


def test_p8_falsifier_mora_boundary_violation_not_reported_negative_control() -> None:
    assert mora_boundary_violation_not_reported(mora_boundary_violation=True, reported=False) is True


def test_p8_falsifier_diagnostic_baseline_misreported_as_mora_negative_control() -> None:
    assert diagnostic_baseline_misreported_as_mora(
        controller_kind="hidden_oracle_baseline",
        attached_to_mora_trace=True,
    ) is True


def test_p8_falsifier_effect_feedback_not_compared_negative_control() -> None:
    assert effect_feedback_not_compared(compared=False) is True


def test_p8_falsifier_provenance_not_measured_negative_control() -> None:
    assert provenance_not_measured(metric_has_provenance=False) is True


def test_p8_falsifier_scenario_label_used_by_baseline_negative_control() -> None:
    assert scenario_label_used_by_baseline({"args": {"basis": "scenario_id:pickup_bias"}}) is True


def test_p8b_falsifier_comparison_report_missing_mora_trace_negative_control() -> None:
    assert comparison_report_missing_mora_trace({"baseline_traces": []}) is True


def test_p8b_falsifier_comparison_report_missing_baseline_traces_negative_control() -> None:
    assert comparison_report_missing_baseline_traces({"mora_trace": {}}) is True


def test_p8b_falsifier_comparison_report_missing_fairness_report_negative_control() -> None:
    assert comparison_report_missing_fairness_report({"mora_trace": {}, "baseline_traces": [{}]}) is True


def test_p8b_falsifier_comparison_report_counts_unfair_oracle_as_fair_win_negative_control() -> None:
    fairness = {"fair_baselines": ["baseline:hidden_oracle"]}
    assert comparison_report_counts_unfair_oracle_as_fair_win(fairness_report=fairness) is True


def test_p8b_falsifier_comparison_report_counts_direct_bridge_as_subject_success_negative_control() -> None:
    boundary = {"direct_bridge_success_count": 1, "request_as_execution_count": 0}
    assert comparison_report_counts_direct_bridge_as_subject_success(boundary_violation_summary=boundary) is True


def test_p8b_falsifier_comparison_report_missing_boundary_summary_negative_control() -> None:
    payload = {"mora_trace": {}, "baseline_traces": [{}], "fairness_report": {"fair_baselines": []}}
    assert comparison_report_missing_boundary_summary(payload) is True


def test_p8b_falsifier_comparison_report_missing_differentiator_summary_negative_control() -> None:
    payload = {"mora_trace": {}, "baseline_traces": [{}], "fairness_report": {"fair_baselines": []}}
    assert comparison_report_missing_differentiator_summary(payload) is True


def test_p8b_falsifier_comparison_report_overclaims_general_intelligence_negative_control() -> None:
    assert comparison_report_overclaims_general_intelligence("general intelligence proven") is True


def test_p8b_falsifier_matrix_report_missing_required_scenario_negative_control() -> None:
    assert matrix_report_missing_required_scenario(
        scenario_ids=("visible_item_pickup_available", "visible_flask_no_drive"),
    ) is True


def test_p8b_falsifier_metric_summary_missing_matched_information_score_negative_control() -> None:
    assert metric_summary_missing_matched_information_score({"success_rate": 1.0}) is True
