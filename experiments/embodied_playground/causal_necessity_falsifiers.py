from __future__ import annotations

from typing import Any


def silent_bundle_fabrication(*, fabricated_basis_refs: tuple[str, ...]) -> bool:
    return bool(fabricated_basis_refs)


def ablation_no_effect(
    *,
    is_hard_no_effect: bool | None = None,
    baseline_signature: tuple[int, ...] | None = None,
    ablated_signature: tuple[int, ...] | None = None,
) -> bool:
    if is_hard_no_effect is not None:
        return is_hard_no_effect
    if baseline_signature is None or ablated_signature is None:
        return False
    return baseline_signature == ablated_signature


def hard_ablation_no_effect(*, is_hard_no_effect: bool) -> bool:
    return is_hard_no_effect


def candidate_without_acp01(*, acp01_suppressed: bool, acp01_candidate_count: int) -> bool:
    return acp01_suppressed and acp01_candidate_count > 0


def world_submission_without_ap01(*, ap01_published_count: int, world_submission_count: int) -> bool:
    return world_submission_count > 0 and ap01_published_count <= 0


def visible_object_alone_becomes_action(*, drive_present: bool, visible_object_present: bool, ap01_published_count: int) -> bool:
    return (not drive_present) and visible_object_present and ap01_published_count > 0


def drive_alone_becomes_action(*, drive_present: bool, public_object_present: bool, ap01_published_count: int) -> bool:
    return drive_present and (not public_object_present) and ap01_published_count > 0


def action_surface_fabricated(*, surface_basis_present: bool, ap01_published_count: int) -> bool:
    return (not surface_basis_present) and ap01_published_count > 0


def pickup_without_proximity_basis(*, proximity_basis_present: bool, ap01_published_count: int) -> bool:
    return (not proximity_basis_present) and ap01_published_count > 0


def pickup_without_capacity_basis(*, capacity_basis_present: bool, ap01_published_count: int) -> bool:
    return (not capacity_basis_present) and ap01_published_count > 0


def permission_without_w04_like_basis(*, permission_basis_present: bool, ap01_published_count: int) -> bool:
    return (not permission_basis_present) and ap01_published_count > 0


def prediction_or_desire_as_permission(*, desire_only_basis: bool, ap01_published_count: int) -> bool:
    return desire_only_basis and ap01_published_count > 0


def failure_erased_without_w06_like_residue(*, blocked_count: int, residue_count: int, world_submission_count: int) -> bool:
    return blocked_count > 0 and residue_count == 0 and world_submission_count > 0


def effect_feedback_fabricated(*, effect_feedback_count: int, world_submission_count: int) -> bool:
    return effect_feedback_count > 0 and world_submission_count == 0


def hidden_basis_substitution(*, hidden_eval_used: bool, ap01_published_count: int) -> bool:
    return hidden_eval_used and ap01_published_count > 0


def forbidden_fallback_after_ablation(*, fallback_markers: tuple[str, ...]) -> bool:
    return bool(fallback_markers)


def strict_mode_not_enforced(*, strict_mode_enabled: bool, violations: tuple[str, ...], verdict: str) -> bool:
    return strict_mode_enabled and bool(violations) and verdict in {"mora_causal_load_bearing", "partial_causal_evidence"}


def causal_necessity_report_overclaims(report_text: str) -> bool:
    lowered = report_text.lower()
    forbidden = (
        "consciousness proven",
        "general autonomy proven",
        "general intelligence proven",
        "human-like cognition proven",
    )
    return any(token in lowered for token in forbidden)


def diagnostic_success_counted_as_causal_necessity(*, diagnostic_success_count: int, counted_as_mora_win: bool) -> bool:
    return diagnostic_success_count > 0 and counted_as_mora_win
