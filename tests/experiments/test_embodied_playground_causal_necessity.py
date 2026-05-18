from __future__ import annotations

from experiments.embodied_playground.ablation_runner import run_causal_necessity_case
from experiments.embodied_playground.causal_necessity import (
    CausalNecessityRun,
    CausalNecessityClaimSafeVerdict,
    required_ablation_specs,
)
from experiments.embodied_playground.strict_mode_runner import run_strict_mode_check
from experiments.embodied_playground.causal_necessity import AblationTrace


def test_causal_necessity_run_structure() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_acp01",
        ticks=1,
        strict_mode=True,
    )
    assert isinstance(run, CausalNecessityRun)
    assert run.ablation_traces
    assert run.expected_degradations
    assert isinstance(run.claim_safe_verdict, CausalNecessityClaimSafeVerdict)


def test_metric_summary_fields_present() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_acp01",
        ticks=1,
        strict_mode=True,
    )
    metrics = run.metric_summary
    assert 0.0 <= metrics.ablation_sensitivity_score <= 1.0
    assert metrics.silent_fabrication_count >= 0
    assert metrics.unexpected_success_count >= 0
    assert 0.0 <= metrics.boundary_integrity_score <= 1.0
    assert 0.0 <= metrics.basis_flow_integrity_score <= 1.0
    assert 0.0 <= metrics.degradation_match_rate <= 1.0


def test_strict_mode_detects_valid_basis_flow() -> None:
    trace = AblationTrace(
        ablation_id="ok",
        scenario_id="x",
        subject_tick_used=True,
        acp01_used=True,
        acp01_candidate_count=1,
        ap01_published_count=1,
        world_submission_count=1,
        effect_feedback_count=1,
        revalidation_count=0,
        residue_count=0,
        blocked_count=0,
        hidden_eval_used=False,
        scenario_label_used=False,
        degradation_observed=True,
        unexpected_success=False,
        boundary_violations=(),
        basis_flow={
            "drive_basis": True,
            "public_object_basis": True,
            "action_surface_basis": True,
            "proximity_basis": True,
            "capacity_basis": True,
            "permission_basis": True,
        },
    )
    strict = run_strict_mode_check(strict_mode_enabled=True, trace=trace)
    assert strict.valid_basis_flow is True
    assert strict.fabricated_basis_refs == ()


def test_strict_mode_detects_fabricated_downstream_basis() -> None:
    trace = AblationTrace(
        ablation_id="fabricated",
        scenario_id="x",
        subject_tick_used=True,
        acp01_used=True,
        acp01_candidate_count=1,
        ap01_published_count=1,
        world_submission_count=1,
        effect_feedback_count=0,
        revalidation_count=0,
        residue_count=0,
        blocked_count=0,
        hidden_eval_used=False,
        scenario_label_used=False,
        degradation_observed=False,
        unexpected_success=True,
        boundary_violations=(),
        basis_flow={
            "drive_basis": True,
            "public_object_basis": True,
            "action_surface_basis": True,
            "proximity_basis": True,
            "capacity_basis": True,
            "permission_basis": False,
        },
    )
    strict = run_strict_mode_check(strict_mode_enabled=True, trace=trace)
    assert strict.valid_basis_flow is False
    assert "ap01_request_without_permission_basis" in strict.fabricated_basis_refs


def test_expected_degradation_representation() -> None:
    specs = required_ablation_specs()
    assert any(spec.ablation_id == "no_acp01" for spec in specs)
    assert any(spec.ablation_id == "hidden_eval_substitution_attempt" for spec in specs)


def test_claim_safe_verdict_language_is_bounded() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_acp01",
        ticks=1,
        strict_mode=True,
    )
    text = (run.summary + " " + run.claim_boundary).lower()
    assert "consciousness proven" not in text
    assert "general autonomy proven" not in text
