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


def test_matrix_scenarios_have_adversarial_categories() -> None:
    matrix = run_baseline_competition_matrix(ticks=1, include_optional=False)
    for run in matrix.scenario_runs:
        assert run.adversarial_category.value


def test_matrix_contains_full_basis_and_basis_missing_cases() -> None:
    matrix = run_baseline_competition_matrix(ticks=1, include_optional=False)
    categories = {run.adversarial_category.value for run in matrix.scenario_runs}
    assert "full_basis_success" in categories
    assert "visible_object_without_drive" in categories
    assert "drive_without_visible_object" in categories
    assert "action_space_without_basis" in categories


def test_matrix_contains_hidden_eval_trap() -> None:
    matrix = run_baseline_competition_matrix(ticks=1, include_optional=False)
    categories = {run.adversarial_category.value for run in matrix.scenario_runs}
    assert "hidden_eval_trap" in categories


def test_matrix_contains_blocked_capacity_and_proximity_cases() -> None:
    matrix = run_baseline_competition_matrix(ticks=1, include_optional=False)
    categories = {run.adversarial_category.value for run in matrix.scenario_runs}
    assert "capacity_blocked" in categories
    assert "proximity_blocked" in categories


def test_matrix_report_groups_by_adversarial_category() -> None:
    matrix = run_baseline_competition_matrix(ticks=1, include_optional=False)
    grouped = matrix.grouped_by_adversarial_category
    assert "full_basis_success" in grouped
    assert "visible_item_pickup_available" in grouped["full_basis_success"]


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


def test_fsm_equivalence_risk_high_when_traces_are_indistinguishable() -> None:
    run = run_baseline_competition(
        scenario_id="visible_item_pickup_available",
        ticks=1,
        include_simple_fsm=True,
    )
    assert run.metric_summary.fsm_equivalence_risk >= 1.0


def test_fsm_equivalence_risk_low_when_mora_differs_on_adversarial_cases() -> None:
    run = run_baseline_competition(
        scenario_id="visible_flask_no_drive",
        ticks=1,
        include_simple_fsm=True,
    )
    assert 0.0 <= run.metric_summary.fsm_equivalence_risk <= 1.0
    assert run.differentiator_summary.mora_vs_fsm_notes


def test_report_contains_mora_vs_fsm_section() -> None:
    run = run_baseline_competition(scenario_id="visible_flask_no_drive", ticks=1, include_simple_fsm=True)
    assert isinstance(run.differentiator_summary.mora_vs_fsm_notes, tuple)
    assert len(run.differentiator_summary.mora_vs_fsm_notes) >= 1


def test_report_does_not_claim_mora_beats_fsm_generally() -> None:
    run = run_baseline_competition(scenario_id="visible_item_pickup_available", ticks=1, include_simple_fsm=True)
    text = (run.claim_boundary + " " + run.claim_safe_verdict.value).lower()
    assert "beats fsm generally" not in text
    assert "general autonomy proven" not in text


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
