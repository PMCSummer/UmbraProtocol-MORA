from __future__ import annotations

from experiments.embodied_playground.inner_state_calibration import (
    list_inner_state_calibration_cases,
    run_inner_state_calibration_ablation_checks,
    run_inner_state_calibration_case,
)


def test_p12_calibrates_clear_self_caused_effect() -> None:
    run = run_inner_state_calibration_case("clear_self_caused_effect")
    assert run.public_report.confidence_reported >= 0.45
    assert run.public_report.fact_claimed is False
    assert run.public_report.cause_confirmed is False


def test_p12_world_only_change_not_reported_as_self_certain() -> None:
    run = run_inner_state_calibration_case("world_only_change")
    assert "self_action" not in (run.public_report.attribution_status or "")
    assert run.falsifier_results["self_overclaim_in_report"] is False


def test_p12_other_actor_change_not_reported_as_self() -> None:
    run = run_inner_state_calibration_case("other_actor_change")
    assert run.public_report.attribution_status in {"other_actor", "unknown_cause", "unknown_or_blocked"}
    assert run.falsifier_results["self_overclaim_in_report"] is False


def test_p12_mixed_cause_preserves_conflict() -> None:
    run = run_inner_state_calibration_case("mixed_cause")
    assert run.public_report.conflict_reported is True
    assert run.falsifier_results["mixed_cause_erased"] is False


def test_p12_delayed_effect_preserves_delay_uncertainty() -> None:
    run = run_inner_state_calibration_case("delayed_effect")
    assert run.public_report.uncertainty_reported >= 0.4
    assert run.falsifier_results["delayed_effect_reported_immediate"] is False


def test_p12_sensor_projection_mismatch_not_world_fact() -> None:
    run = run_inner_state_calibration_case("sensor_projection_mismatch")
    assert run.public_report.attribution_status != "world_process"
    assert run.public_report.confidence_reported <= 0.45


def test_p12_unknown_cause_preserved() -> None:
    run = run_inner_state_calibration_case("unknown_cause")
    assert run.public_report.closure_status == "open"
    assert run.public_report.uncertainty_reported >= 0.6


def test_p12_conflicting_evidence_reports_conflict() -> None:
    run = run_inner_state_calibration_case("conflicting_evidence")
    assert run.public_report.conflict_reported is True
    assert run.public_report.closure_status == "open"
    assert run.falsifier_results["conflict_erased"] is False


def test_p12_residue_present_not_erased() -> None:
    run = run_inner_state_calibration_case("residue_present")
    assert run.public_report.residue_reported is True
    assert run.falsifier_results["residue_erased"] is False


def test_p12_hidden_eval_only_no_public_certainty() -> None:
    run = run_inner_state_calibration_case("hidden_eval_only_cause")
    assert run.hidden_leak_detected is False
    assert run.public_report.confidence_reported <= 0.4
    assert run.falsifier_results["hidden_truth_report_leak"] is False


def test_p12_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_inner_state_calibration_cases()}
    required = {
        "clear_self_caused_effect",
        "world_only_change",
        "other_actor_change",
        "mixed_cause",
        "delayed_effect",
        "sensor_projection_mismatch",
        "unknown_cause",
        "conflicting_evidence",
        "residue_present",
        "hidden_eval_only_cause",
    }
    assert required.issubset(ids)


def test_p12_ablation_checks_present() -> None:
    checks = run_inner_state_calibration_ablation_checks()
    names = {item.ablation_id for item in checks}
    required = {
        "remove_public_evidence_refs",
        "remove_residue_refs",
        "remove_conflict_markers",
        "hide_AP01_ref",
        "hide_effect_correlation",
        "hidden_eval_only",
        "ambiguous_public_evidence",
        "mixed_hidden_condition",
    }
    assert required.issubset(names)
