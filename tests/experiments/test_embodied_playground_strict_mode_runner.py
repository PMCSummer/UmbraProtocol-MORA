from __future__ import annotations

from experiments.embodied_playground.causal_necessity import AblationTrace
from experiments.embodied_playground.strict_mode_runner import run_strict_mode_check


def _trace(**overrides: object) -> AblationTrace:
    base = dict(
        ablation_id="x",
        scenario_id="visible_item_pickup_available",
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
        notes=(),
    )
    base.update(overrides)
    return AblationTrace(**base)


def test_strict_mode_passes_valid_full_basis_pickup() -> None:
    strict = run_strict_mode_check(strict_mode_enabled=True, trace=_trace())
    assert strict.valid_basis_flow is True
    assert strict.auto_builder_detected is False


def test_strict_mode_flags_missing_upstream_basis() -> None:
    strict = run_strict_mode_check(
        strict_mode_enabled=True,
        trace=_trace(basis_flow={
            "drive_basis": True,
            "public_object_basis": True,
            "action_surface_basis": True,
            "proximity_basis": True,
            "capacity_basis": True,
            "permission_basis": False,
        }),
    )
    assert strict.valid_basis_flow is False
    assert "ap01_request_without_permission_basis" in strict.fabricated_basis_refs


def test_strict_mode_flags_hidden_eval_substitution() -> None:
    strict = run_strict_mode_check(
        strict_mode_enabled=True,
        trace=_trace(hidden_eval_used=True),
    )
    assert strict.valid_basis_flow is False
    assert "hidden_eval_substitution" in strict.fabricated_basis_refs


def test_strict_mode_flags_effect_feedback_fabrication() -> None:
    strict = run_strict_mode_check(
        strict_mode_enabled=True,
        trace=_trace(effect_feedback_count=1, world_submission_count=0),
    )
    assert strict.valid_basis_flow is False
    assert "effect_feedback_fabricated" in strict.fabricated_basis_refs


def test_strict_mode_flags_forbidden_fallback_after_ablation() -> None:
    strict = run_strict_mode_check(
        strict_mode_enabled=True,
        trace=_trace(
            unexpected_success=True,
            basis_flow={
                "drive_basis": False,
                "public_object_basis": True,
                "action_surface_basis": True,
                "proximity_basis": True,
                "capacity_basis": True,
                "permission_basis": True,
            },
            ap01_published_count=1,
        ),
    )
    assert strict.valid_basis_flow is False
    assert "visible_object_as_permission" in strict.fabricated_basis_refs


def test_strict_mode_does_not_count_abstention_under_missing_basis_as_failure() -> None:
    strict = run_strict_mode_check(
        strict_mode_enabled=True,
        trace=_trace(
            acp01_candidate_count=0,
            ap01_published_count=0,
            world_submission_count=0,
            effect_feedback_count=0,
            basis_flow={
                "drive_basis": False,
                "public_object_basis": True,
                "action_surface_basis": True,
                "proximity_basis": True,
                "capacity_basis": True,
                "permission_basis": True,
            },
        ),
    )
    assert strict.valid_basis_flow is True
    assert strict.fabricated_basis_refs == ()
