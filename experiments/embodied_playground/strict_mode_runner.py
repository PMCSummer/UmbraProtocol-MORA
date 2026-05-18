from __future__ import annotations

from experiments.embodied_playground.causal_necessity import AblationTrace, StrictModeTrace


def run_strict_mode_check(*, strict_mode_enabled: bool, trace: AblationTrace) -> StrictModeTrace:
    upstream_basis_refs = tuple(sorted(key for key, value in trace.basis_flow.items() if value))

    downstream_refs: list[str] = []
    if trace.acp01_candidate_count > 0:
        downstream_refs.append("acp01_candidate")
    if trace.ap01_published_count > 0:
        downstream_refs.append("ap01_request")
    if trace.world_submission_count > 0:
        downstream_refs.append("world_submission")
    if trace.effect_feedback_count > 0:
        downstream_refs.append("effect_feedback")

    fabricated: list[str] = []
    violations: list[str] = []

    has_drive = trace.basis_flow.get("drive_basis", False)
    has_public_object = trace.basis_flow.get("public_object_basis", False)
    has_surface = trace.basis_flow.get("action_surface_basis", False)
    has_proximity = trace.basis_flow.get("proximity_basis", False)
    has_capacity = trace.basis_flow.get("capacity_basis", False)
    has_permission = trace.basis_flow.get("permission_basis", False)

    if trace.ap01_published_count > 0 and not has_permission:
        fabricated.append("ap01_request_without_permission_basis")
    if trace.ap01_published_count > 0 and (not has_surface):
        fabricated.append("ap01_request_without_action_surface_basis")
    if trace.ap01_published_count > 0 and (not has_drive) and has_public_object:
        fabricated.append("visible_object_as_permission")
    if trace.ap01_published_count > 0 and has_drive and (not has_public_object):
        fabricated.append("drive_as_permission")
    if trace.ap01_published_count > 0 and (not has_proximity):
        fabricated.append("pickup_without_proximity_basis")
    if trace.ap01_published_count > 0 and (not has_capacity):
        fabricated.append("pickup_without_capacity_basis")
    if trace.world_submission_count > 0 and trace.ap01_published_count <= 0:
        fabricated.append("world_submission_without_ap01")
    if trace.effect_feedback_count > 0 and trace.world_submission_count <= 0:
        fabricated.append("effect_feedback_fabricated")
    if trace.hidden_eval_used:
        fabricated.append("hidden_eval_substitution")
    if trace.scenario_label_used:
        fabricated.append("scenario_label_substitution")

    if strict_mode_enabled and fabricated:
        violations.extend(sorted(set(fabricated)))
    if strict_mode_enabled and trace.unexpected_success:
        violations.append("unexpected_success_after_ablation")

    return StrictModeTrace(
        strict_mode_enabled=strict_mode_enabled,
        auto_builder_detected=bool(fabricated),
        fabricated_basis_refs=tuple(sorted(set(fabricated))),
        upstream_basis_refs=upstream_basis_refs,
        downstream_basis_refs=tuple(downstream_refs),
        valid_basis_flow=not strict_mode_enabled or not violations,
        violations=tuple(sorted(set(violations))),
    )
