from __future__ import annotations

from types import SimpleNamespace

from experiments.embodied_playground.baseline_metrics import compute_baseline_metric_summary
from experiments.embodied_playground.baselines import BaselineFairnessClass
from experiments.embodied_playground.baseline_runner import run_baseline_competition


def _decision(
    *,
    abstained: bool,
    reason_codes: tuple[str, ...] = (),
    used_previous_effect: bool = False,
    expected_boundary_violation: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        abstained=abstained,
        reason_codes=reason_codes,
        used_previous_effect=used_previous_effect,
        expected_boundary_violation=expected_boundary_violation,
    )


def _record(
    *,
    abstained: bool,
    effect_status: str | None,
    invalid_action: bool,
    hidden_eval_usage: bool = False,
    ap01_bypassed: bool = False,
    reason_codes: tuple[str, ...] = (),
    used_previous_effect: bool = False,
    expected_boundary_violation: bool = False,
    recovery_marker: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        decision=_decision(
            abstained=abstained,
            reason_codes=reason_codes,
            used_previous_effect=used_previous_effect,
            expected_boundary_violation=expected_boundary_violation,
        ),
        effect_status=effect_status,
        invalid_action=invalid_action,
        hidden_eval_usage=hidden_eval_usage,
        ap01_bypassed=ap01_bypassed,
        provenance_coverage={
            "used_public_observation": 1.0,
            "used_action_space": 0.5,
            "used_drive_basis": 0.0,
            "used_previous_effect": 1.0 if used_previous_effect else 0.0,
            "used_hidden_or_eval": 1.0 if hidden_eval_usage else 0.0,
        },
        recovery_marker=recovery_marker,
    )


def test_metric_summary_has_all_required_metrics() -> None:
    fair_trace = SimpleNamespace(
        fairness_class=BaselineFairnessClass.FAIR_PUBLIC,
        hidden_eval_usage=False,
        decisions=(
            _record(abstained=False, effect_status="succeeded", invalid_action=False),
            _record(abstained=False, effect_status="blocked", invalid_action=True, recovery_marker="blind_retry_after_invalid"),
            _record(abstained=True, effect_status=None, invalid_action=False, reason_codes=("insufficient_basis",)),
        ),
    )
    unfair_trace = SimpleNamespace(
        fairness_class=BaselineFairnessClass.DIAGNOSTIC_UNFAIR,
        hidden_eval_usage=True,
        decisions=(
            _record(
                abstained=False,
                effect_status="succeeded",
                invalid_action=False,
                hidden_eval_usage=True,
                ap01_bypassed=True,
                expected_boundary_violation=True,
                used_previous_effect=True,
            ),
        ),
    )
    summary = compute_baseline_metric_summary(
        scenario_id="visible_flask_no_drive",
        mora_run=SimpleNamespace(),
        mora_summary=SimpleNamespace(abstention_count=2),
        baseline_traces=(fair_trace, unfair_trace),
    )
    assert hasattr(summary, "success_rate")
    assert hasattr(summary, "invalid_action_rate")
    assert hasattr(summary, "abstention_quality")
    assert hasattr(summary, "shortcut_violation_count")
    assert hasattr(summary, "provenance_coverage")
    assert hasattr(summary, "boundary_integrity")
    assert hasattr(summary, "recovery_after_failure")
    assert hasattr(summary, "effect_feedback_incorporation")
    assert hasattr(summary, "overclaim_rate")
    assert hasattr(summary, "matched_information_score")
    assert hasattr(summary, "differentiator_score")
    assert hasattr(summary, "fsm_equivalence_risk")


def test_boundary_violation_summary_counts_ap01_bypass() -> None:
    run = run_baseline_competition(
        scenario_id="visible_item_pickup_available",
        ticks=1,
        include_direct_bridge=True,
    )
    assert run.boundary_violation_summary.ap01_bypass_count >= 1
    assert run.boundary_violation_summary.request_as_execution_count >= 1


def test_matched_information_score_penalizes_hidden_eval_access() -> None:
    fair_hidden = SimpleNamespace(
        fairness_class=BaselineFairnessClass.FAIR_PUBLIC,
        hidden_eval_usage=True,
        decisions=(_record(abstained=False, effect_status="succeeded", invalid_action=False, hidden_eval_usage=True),),
    )
    summary = compute_baseline_metric_summary(
        scenario_id="hidden_map_not_visible",
        mora_run=SimpleNamespace(),
        mora_summary=SimpleNamespace(abstention_count=0),
        baseline_traces=(fair_hidden,),
    )
    assert summary.matched_information_score == 0.0
