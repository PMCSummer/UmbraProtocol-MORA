from __future__ import annotations

from experiments.embodied_playground.causal_necessity_falsifiers import (
    ablation_no_effect,
    action_surface_fabricated,
    candidate_without_acp01,
    causal_necessity_report_overclaims,
    diagnostic_success_counted_as_causal_necessity,
    drive_alone_becomes_action,
    effect_feedback_fabricated,
    failure_erased_without_w06_like_residue,
    forbidden_fallback_after_ablation,
    hidden_basis_substitution,
    permission_without_w04_like_basis,
    pickup_without_capacity_basis,
    pickup_without_proximity_basis,
    prediction_or_desire_as_permission,
    silent_bundle_fabrication,
    strict_mode_not_enforced,
    visible_object_alone_becomes_action,
    world_submission_without_ap01,
)


def test_causal_necessity_falsifier_presence() -> None:
    required = [
        silent_bundle_fabrication,
        ablation_no_effect,
        candidate_without_acp01,
        world_submission_without_ap01,
        visible_object_alone_becomes_action,
        drive_alone_becomes_action,
        action_surface_fabricated,
        pickup_without_proximity_basis,
        pickup_without_capacity_basis,
        permission_without_w04_like_basis,
        prediction_or_desire_as_permission,
        failure_erased_without_w06_like_residue,
        effect_feedback_fabricated,
        hidden_basis_substitution,
        forbidden_fallback_after_ablation,
        strict_mode_not_enforced,
        causal_necessity_report_overclaims,
        diagnostic_success_counted_as_causal_necessity,
    ]
    assert len(required) == 18


def test_causal_necessity_falsifier_negative_controls() -> None:
    assert silent_bundle_fabrication(fabricated_basis_refs=("x",)) is True
    assert ablation_no_effect(baseline_signature=(1, 2), ablated_signature=(1, 2)) is True
    assert candidate_without_acp01(acp01_suppressed=True, acp01_candidate_count=1) is True
    assert world_submission_without_ap01(ap01_published_count=0, world_submission_count=1) is True
    assert visible_object_alone_becomes_action(
        drive_present=False,
        visible_object_present=True,
        ap01_published_count=1,
    ) is True
    assert drive_alone_becomes_action(
        drive_present=True,
        public_object_present=False,
        ap01_published_count=1,
    ) is True
    assert action_surface_fabricated(surface_basis_present=False, ap01_published_count=1) is True
    assert pickup_without_proximity_basis(proximity_basis_present=False, ap01_published_count=1) is True
    assert pickup_without_capacity_basis(capacity_basis_present=False, ap01_published_count=1) is True
    assert permission_without_w04_like_basis(permission_basis_present=False, ap01_published_count=1) is True
    assert prediction_or_desire_as_permission(desire_only_basis=True, ap01_published_count=1) is True
    assert failure_erased_without_w06_like_residue(
        blocked_count=1,
        residue_count=0,
        world_submission_count=1,
    ) is True
    assert effect_feedback_fabricated(effect_feedback_count=1, world_submission_count=0) is True
    assert hidden_basis_substitution(hidden_eval_used=True, ap01_published_count=1) is True
    assert forbidden_fallback_after_ablation(fallback_markers=("manual_provider",)) is True
    assert strict_mode_not_enforced(
        strict_mode_enabled=True,
        violations=("x",),
        verdict="mora_causal_load_bearing",
    ) is True
    assert causal_necessity_report_overclaims("consciousness proven") is True
    assert diagnostic_success_counted_as_causal_necessity(
        diagnostic_success_count=1,
        counted_as_mora_win=True,
    ) is True


def test_p9_falsifier_ablation_no_effect_ignores_non_informative_cases() -> None:
    assert ablation_no_effect(is_hard_no_effect=False) is False
