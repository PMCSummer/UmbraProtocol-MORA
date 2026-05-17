from __future__ import annotations

from dataclasses import dataclass

from experiments.embodied_playground.models import (
    ActionEffectFrame,
    ActionSpaceFrame,
    EvalOnlyWorldTruth,
    ObservationFrame,
    PublishedActionEnvelope,
    PublicWorldSnapshot,
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    reason: str


def validate_subject_visible_observation(frame: ObservationFrame) -> ValidationResult:
    if not frame.hidden_truth_excluded or not frame.eval_only_excluded:
        raise ValueError("subject-visible observation cannot include hidden/eval-only truth")
    return ValidationResult(ok=True, reason="subject_visible_observation_valid")


def validate_action_space_is_not_permission(frame: ActionSpaceFrame) -> ValidationResult:
    if frame.action_space_is_permission or frame.action_space_is_selection or frame.action_space_is_execution:
        raise ValueError("action space cannot claim permission/selection/execution")
    for surface in frame.available_surfaces:
        if surface.is_permission:
            raise ValueError("surface availability cannot claim permission")
    return ValidationResult(ok=True, reason="action_space_boundary_preserved")


def validate_published_action_envelope(envelope: PublishedActionEnvelope) -> ValidationResult:
    if not envelope.request_boundary_preserved:
        raise ValueError("published action envelope must preserve AP01 request boundary")
    if envelope.submitted_to_world or envelope.executed_by_world:
        raise ValueError("published action envelope cannot claim world submission/execution at creation")
    if not envelope.ap01_request_id:
        raise ValueError("published action envelope requires AP01 request reference")
    return ValidationResult(ok=True, reason="envelope_boundary_preserved")


def validate_effect_correlates_to_request(
    effect: ActionEffectFrame,
    envelope: PublishedActionEnvelope,
) -> ValidationResult:
    if effect.request_ref != envelope.ap01_request_id:
        raise ValueError("effect/request correlation mismatch")
    if effect.envelope_ref != envelope.envelope_id:
        raise ValueError("effect/envelope correlation mismatch")
    return ValidationResult(ok=True, reason="effect_request_correlation_valid")


def validate_eval_truth_not_in_subject_visible(
    observation: ObservationFrame,
    snapshot: PublicWorldSnapshot,
    eval_truth: EvalOnlyWorldTruth,
) -> ValidationResult:
    if not observation.eval_only_excluded or not snapshot.hidden_truth_excluded:
        raise ValueError("subject-visible payload must exclude eval/hidden truth")
    if not eval_truth.must_never_enter_subject_visible:
        raise ValueError("eval-only truth must remain isolated")
    return ValidationResult(ok=True, reason="eval_truth_boundary_preserved")


def validate_no_execution_without_ap01_envelope(
    effect: ActionEffectFrame,
    envelope: PublishedActionEnvelope | None,
) -> ValidationResult:
    correlation = str(getattr(effect.correlation_status, "value", effect.correlation_status))
    if envelope is None and correlation == "correlated_to_request":
        raise ValueError("cannot claim correlated effect without AP01 envelope")
    return ValidationResult(ok=True, reason="no_execution_without_ap01_envelope")
