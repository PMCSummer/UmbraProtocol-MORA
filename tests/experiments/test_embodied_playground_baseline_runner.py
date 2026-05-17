from __future__ import annotations

from dataclasses import asdict

from experiments.embodied_playground.baseline_runner import (
    BaselineCompetitionRun,
    run_baseline_competition,
    run_baseline_competition_matrix,
)


def test_comparison_run_contains_mora_trace_and_baseline_traces() -> None:
    run = run_baseline_competition(scenario_id="visible_item_pickup_available", ticks=1, seed=11)
    assert isinstance(run, BaselineCompetitionRun)
    assert run.mora_trace.subject_tick_used is True
    assert run.baseline_traces


def test_matrix_runner_includes_required_scenarios() -> None:
    matrix = run_baseline_competition_matrix(ticks=1, include_optional=False)
    scenario_ids = set(matrix.scenario_ids)
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
    assert required.issubset(scenario_ids)


def test_fairness_report_excludes_hidden_oracle_from_fair_comparison() -> None:
    run = run_baseline_competition(
        scenario_id="hidden_map_not_visible",
        ticks=1,
        drive_kinds=("water_need",),
        include_hidden_oracle=True,
    )
    assert "baseline:hidden_oracle" not in run.fairness_report.fair_baselines
    assert "baseline:hidden_oracle" in run.fairness_report.excluded_from_fair_comparison
    assert run.fairness_report.hidden_oracle_marked_unfair is True


def test_direct_bridge_success_is_not_counted_as_subject_success() -> None:
    run = run_baseline_competition(
        scenario_id="visible_item_pickup_available",
        ticks=1,
        include_direct_bridge=True,
    )
    assert run.fairness_report.direct_bridge_marked_bypass is True
    assert "baseline:direct_bridge_bypass" in run.fairness_report.excluded_from_fair_comparison
    assert run.boundary_violation_summary.request_as_execution_count >= 1


def test_differentiator_summary_identifies_no_drive_visible_item_case() -> None:
    run = run_baseline_competition(scenario_id="visible_flask_no_drive", ticks=1)
    assert run.differentiator_summary.visible_object_no_drive_mora_abstains is True
    assert any("visible_object_no_drive" in note for note in run.differentiator_summary.key_differences)


def test_claim_safe_verdict_does_not_overclaim() -> None:
    run = run_baseline_competition(scenario_id="visible_flask_no_drive", ticks=1)
    text = (run.claim_boundary + " " + run.claim_safe_verdict.value).lower()
    assert "consciousness" in run.claim_boundary.lower()
    assert "proves consciousness" not in text
    assert "general autonomy proven" not in text


def test_runner_output_is_json_serializable() -> None:
    run = run_baseline_competition(scenario_id="visible_item_pickup_available", ticks=1)
    payload = asdict(run)
    assert "mora_trace" in payload
    assert "baseline_traces" in payload
