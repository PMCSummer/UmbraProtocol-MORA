from __future__ import annotations

from typing import Any

from experiments.embodied_playground.baselines import BaselineFairnessClass


def baseline_gets_more_info_than_mora(*, fairness_class: BaselineFairnessClass | str, used_hidden_or_eval: bool) -> bool:
    fairness = fairness_class.value if isinstance(fairness_class, BaselineFairnessClass) else str(fairness_class)
    return fairness == BaselineFairnessClass.FAIR_PUBLIC.value and used_hidden_or_eval


def hidden_oracle_treated_as_fair(*, controller_kind: str, fairness_class: BaselineFairnessClass | str) -> bool:
    fairness = fairness_class.value if isinstance(fairness_class, BaselineFairnessClass) else str(fairness_class)
    return controller_kind == "hidden_oracle_baseline" and fairness == BaselineFairnessClass.FAIR_PUBLIC.value


def direct_bridge_counted_as_subject_success(*, controller_kind: str, ap01_bypassed: bool, counted_as_honest: bool) -> bool:
    return controller_kind == "direct_bridge_bypass_baseline" and ap01_bypassed and counted_as_honest


def success_without_boundary_integrity(*, success_counted: bool, boundary_integrity_ok: bool) -> bool:
    return success_counted and not boundary_integrity_ok


def abstention_counted_as_simple_failure(*, abstained: bool, insufficient_basis: bool, counted_as_failure_only: bool) -> bool:
    return abstained and insufficient_basis and counted_as_failure_only


def heuristic_indistinguishable_from_mora(*, mora_actions: tuple[str | None, ...], heuristic_actions: tuple[str | None, ...]) -> bool:
    return mora_actions == heuristic_actions and len(mora_actions) > 0


def action_space_as_permission_baseline_not_detected(*, controller_kind: str, acted_from_surface_only: bool, weakness_recorded: bool) -> bool:
    return controller_kind == "action_space_greedy_baseline" and acted_from_surface_only and not weakness_recorded


def visible_object_as_pickup_baseline_not_detected(*, controller_kind: str, acted_from_visible_object_only: bool, weakness_recorded: bool) -> bool:
    return controller_kind == "visible_object_heuristic_baseline" and acted_from_visible_object_only and not weakness_recorded


def drive_as_permission_baseline_not_detected(*, controller_kind: str, acted_from_drive_only: bool, weakness_recorded: bool) -> bool:
    return controller_kind == "drive_only_baseline" and acted_from_drive_only and not weakness_recorded


def hidden_eval_usage_not_reported(*, used_hidden_eval: bool, reported_hidden_eval_usage: bool) -> bool:
    return used_hidden_eval and not reported_hidden_eval_usage


def mora_boundary_violation_not_reported(*, mora_boundary_violation: bool, reported: bool) -> bool:
    return mora_boundary_violation and not reported


def diagnostic_baseline_misreported_as_mora(*, controller_kind: str, attached_to_mora_trace: bool) -> bool:
    return controller_kind in {"hidden_oracle_baseline", "direct_bridge_bypass_baseline"} and attached_to_mora_trace


def effect_feedback_not_compared(*, compared: bool) -> bool:
    return not compared


def provenance_not_measured(*, metric_has_provenance: bool) -> bool:
    return not metric_has_provenance


def scenario_label_used_by_baseline(decision_payload: Any) -> bool:
    text = str(decision_payload).lower()
    markers = ("scenario_id", "scenario:", "expected_outcome", "test_name", "case_label")
    return any(marker in text for marker in markers)


def comparison_report_missing_mora_trace(report_payload: Any) -> bool:
    return not isinstance(report_payload, dict) or "mora_trace" not in report_payload


def comparison_report_missing_baseline_traces(report_payload: Any) -> bool:
    if not isinstance(report_payload, dict):
        return True
    traces = report_payload.get("baseline_traces")
    return not isinstance(traces, (list, tuple)) or len(traces) == 0


def comparison_report_missing_fairness_report(report_payload: Any) -> bool:
    if not isinstance(report_payload, dict):
        return True
    fairness = report_payload.get("fairness_report")
    required = {
        "fair_baselines",
        "diagnostic_unfair_baselines",
        "boundary_violation_baselines",
        "excluded_from_fair_comparison",
    }
    return not isinstance(fairness, dict) or not required.issubset(set(fairness.keys()))


def comparison_report_counts_unfair_oracle_as_fair_win(*, fairness_report: Any) -> bool:
    if not isinstance(fairness_report, dict):
        return True
    fair = set(fairness_report.get("fair_baselines", ()))
    return "baseline:hidden_oracle" in fair


def comparison_report_counts_direct_bridge_as_subject_success(*, boundary_violation_summary: Any) -> bool:
    if not isinstance(boundary_violation_summary, dict):
        return True
    return int(boundary_violation_summary.get("direct_bridge_success_count", 0)) > 0 and int(
        boundary_violation_summary.get("request_as_execution_count", 0)
    ) == 0


def comparison_report_missing_boundary_summary(report_payload: Any) -> bool:
    if not isinstance(report_payload, dict):
        return True
    summary = report_payload.get("boundary_violation_summary")
    required = {
        "ap01_bypass_count",
        "hidden_eval_usage_count",
        "scenario_label_usage_count",
        "request_as_execution_count",
    }
    return not isinstance(summary, dict) or not required.issubset(set(summary.keys()))


def comparison_report_missing_differentiator_summary(report_payload: Any) -> bool:
    if not isinstance(report_payload, dict):
        return True
    summary = report_payload.get("differentiator_summary")
    return not isinstance(summary, dict) or "key_differences" not in summary


def comparison_report_overclaims_general_intelligence(report_text: str) -> bool:
    lowered = report_text.lower()
    bad_markers = (
        "proves consciousness",
        "general autonomy proven",
        "general intelligence proven",
        "mora is conscious",
        "mora beats all baselines universally",
    )
    return any(marker in lowered for marker in bad_markers)


def matrix_report_missing_required_scenario(*, scenario_ids: tuple[str, ...] | list[str]) -> bool:
    required = {
        "visible_item_pickup_available",
        "visible_flask_no_drive",
        "water_need_no_visible_water",
        "inventory_capacity_block",
        "pickup_without_proximity",
        "action_space_only_no_candidate",
        "hidden_map_not_visible",
        "previous_blocked_effect_revalidation",
    }
    provided = set(scenario_ids)
    return not required.issubset(provided)


def metric_summary_missing_matched_information_score(metric_summary: Any) -> bool:
    if not isinstance(metric_summary, dict):
        return True
    return "matched_information_score" not in metric_summary
