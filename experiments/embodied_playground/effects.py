from __future__ import annotations

from experiments.embodied_playground.models import (
    ActionEffectFrame,
    CorrelationStatus,
    EffectStatus,
    PublishedActionEnvelope,
)


def build_effect_from_envelope(
    *,
    effect_id: str,
    subject_id: str,
    tick_index: int,
    envelope: PublishedActionEnvelope,
    effect_status: EffectStatus | str,
    body_delta: dict[str, object] | None = None,
    inventory_delta: dict[str, object] | None = None,
    world_delta_public: dict[str, object] | None = None,
    observed_result_refs: tuple[str, ...] = (),
    blocked_reason: str | None = None,
    failure_reason: str | None = None,
    partial_reason: str | None = None,
) -> ActionEffectFrame:
    return ActionEffectFrame(
        effect_id=effect_id,
        subject_id=subject_id,
        tick_index=tick_index,
        request_ref=envelope.ap01_request_id,
        envelope_ref=envelope.envelope_id,
        action_kind=envelope.action_kind,
        target_ref=envelope.target_ref,
        effect_status=effect_status,
        body_delta=body_delta or {},
        inventory_delta=inventory_delta or {},
        world_delta_public=world_delta_public or {},
        observed_result_refs=observed_result_refs,
        blocked_reason=blocked_reason,
        failure_reason=failure_reason,
        partial_reason=partial_reason,
        correlation_status=CorrelationStatus.CORRELATED_TO_REQUEST,
    )


def build_passive_world_event(
    *,
    effect_id: str,
    subject_id: str,
    tick_index: int,
    action_kind: str = "passive_world_event",
    observed_result_refs: tuple[str, ...] = (),
) -> ActionEffectFrame:
    return ActionEffectFrame(
        effect_id=effect_id,
        subject_id=subject_id,
        tick_index=tick_index,
        request_ref=None,
        envelope_ref=None,
        action_kind=action_kind,
        target_ref=None,
        effect_status=EffectStatus.UNKNOWN,
        body_delta={},
        inventory_delta={},
        world_delta_public={},
        observed_result_refs=observed_result_refs,
        correlation_status=CorrelationStatus.PASSIVE_WORLD_EVENT,
    )
