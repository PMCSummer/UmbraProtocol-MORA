from __future__ import annotations

from substrate.world_adapter.models import (
    WorldActionPacket,
    WorldAdapterGateDecision,
    WorldAdapterInput,
    WorldAdapterResult,
    WorldAdapterState,
    WorldAdapterTelemetry,
    WorldEffectObservationPacket,
    WorldEffectStatus,
    WorldLinkStatus,
    WorldObservationPacket,
)
from substrate.world_adapter.policy import evaluate_world_adapter_claim_gate
from substrate.world_adapter.telemetry import (
    build_world_adapter_telemetry,
    world_adapter_result_snapshot,
)

ATTEMPTED_PATHS: tuple[str, ...] = (
    "world_adapter.read_observation",
    "world_adapter.form_action_candidate",
    "world_adapter.read_effect_feedback",
    "world_adapter.evaluate_claim_gate",
)


def run_world_adapter_cycle(
    *,
    tick_id: str,
    execution_mode: str,
    adapter_input: WorldAdapterInput | None = None,
    request_action_candidate: bool = False,
    source_lineage: tuple[str, ...] = (),
) -> WorldAdapterResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not execution_mode:
        raise ValueError("execution_mode is required")

    adapter_input = adapter_input or WorldAdapterInput()
    if not isinstance(adapter_input, WorldAdapterInput):
        raise TypeError("adapter_input must be WorldAdapterInput")

    observation = adapter_input.observation_packet
    action = adapter_input.action_packet
    effect = adapter_input.effect_packet
    if request_action_candidate and action is None and adapter_input.adapter_presence:
        action = build_world_action_candidate(
            tick_id=tick_id,
            execution_mode=execution_mode,
        )
    effect_feedback_correlated = bool(
        action is not None
        and effect is not None
        and effect.action_id == action.action_id
    )

    world_link_status, effect_status, confidence, unavailable_reason = _derive_link_effect_state(
        adapter_input=adapter_input,
        observation=observation,
        action=action,
        effect=effect,
    )
    state = WorldAdapterState(
        adapter_presence=adapter_input.adapter_presence,
        adapter_available=adapter_input.adapter_available,
        adapter_degraded=adapter_input.adapter_degraded,
        world_link_status=world_link_status,
        effect_status=effect_status,
        last_observation_packet=observation,
        last_action_packet=action,
        last_effect_packet=effect,
        effect_feedback_correlated=effect_feedback_correlated,
        world_grounding_confidence=confidence,
        unavailable_reason=unavailable_reason,
        source_lineage=tuple(dict.fromkeys((*source_lineage, *adapter_input.source_lineage))),
        provenance="minimal_world_adapter_external_seam_scaffold",
    )
    gate = evaluate_world_adapter_claim_gate(state)
    telemetry = build_world_adapter_telemetry(
        state=state,
        gate=gate,
        attempted_paths=ATTEMPTED_PATHS,
    )
    partial_known = state.adapter_degraded or state.world_link_status is not WorldLinkStatus.ACTION_EFFECT_OBSERVED
    partial_reason = (
        state.unavailable_reason
        if state.unavailable_reason is not None
        else "world effect not fully observed"
        if state.effect_status in {WorldEffectStatus.NO_ACTION, WorldEffectStatus.PENDING_FEEDBACK}
        else None
    )
    abstain = not gate.world_grounded_transition_allowed
    abstain_reason = None if not abstain else "world_grounded_transition_not_available"
    return WorldAdapterResult(
        state=state,
        gate=gate,
        telemetry=telemetry,
        partial_known=partial_known,
        partial_known_reason=partial_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def world_adapter_result_to_payload(result: WorldAdapterResult) -> dict[str, object]:
    return world_adapter_result_snapshot(result)


def build_world_action_candidate(
    *,
    tick_id: str,
    execution_mode: str,
    target_ref: str = "external_stub_target",
) -> WorldActionPacket:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not execution_mode:
        raise ValueError("execution_mode is required")
    return WorldActionPacket(
        action_id=f"world-action-{tick_id}",
        action_kind="emit_world_action",
        target_ref=target_ref,
        requested_at=tick_id,
        payload_ref=f"action_payload:{execution_mode}",
        provenance="rt01_world_adapter_action_candidate",
    )


def build_world_observation_packet(
    *,
    observation_id: str,
    source_ref: str,
    observed_at: str,
    payload_ref: str,
) -> WorldObservationPacket:
    return WorldObservationPacket(
        observation_id=observation_id,
        observation_kind="external_state_snapshot",
        source_ref=source_ref,
        observed_at=observed_at,
        payload_ref=payload_ref,
        provenance="world_adapter_observation_surface",
    )


def build_world_effect_packet(
    *,
    effect_id: str,
    action_id: str,
    observed_at: str,
    source_ref: str,
    success: bool,
) -> WorldEffectObservationPacket:
    return WorldEffectObservationPacket(
        effect_id=effect_id,
        action_id=action_id,
        effect_kind="world_effect_observation",
        observed_at=observed_at,
        success=success,
        source_ref=source_ref,
        provenance="world_adapter_effect_surface",
    )


def _derive_link_effect_state(
    *,
    adapter_input: WorldAdapterInput,
    observation: WorldObservationPacket | None,
    action: WorldActionPacket | None,
    effect: WorldEffectObservationPacket | None,
) -> tuple[WorldLinkStatus, WorldEffectStatus, float, str | None]:
    if not adapter_input.adapter_presence:
        return WorldLinkStatus.UNAVAILABLE, WorldEffectStatus.UNAVAILABLE, 0.0, "world_adapter_absent"
    if not adapter_input.adapter_available:
        return WorldLinkStatus.UNAVAILABLE, WorldEffectStatus.UNAVAILABLE, 0.05, "world_adapter_unavailable"
    if adapter_input.adapter_degraded:
        if action is not None and effect is None:
            return (
                WorldLinkStatus.DEGRADED,
                WorldEffectStatus.PENDING_FEEDBACK,
                0.25,
                "world_adapter_degraded_effect_pending",
            )
        return WorldLinkStatus.DEGRADED, WorldEffectStatus.NO_ACTION, 0.3, "world_adapter_degraded"
    if action is not None and effect is None:
        return (
            WorldLinkStatus.ACTION_PENDING_EFFECT,
            WorldEffectStatus.PENDING_FEEDBACK,
            0.45,
            "action_emitted_without_effect_feedback",
        )
    if action is not None and effect is not None:
        status = (
            WorldEffectStatus.OBSERVED_SUCCESS
            if effect.success
            else WorldEffectStatus.OBSERVED_FAILURE
        )
        return WorldLinkStatus.ACTION_EFFECT_OBSERVED, status, 0.85, None
    if observation is not None:
        return WorldLinkStatus.OBSERVATION_ONLY, WorldEffectStatus.NO_ACTION, 0.62, None
    return WorldLinkStatus.OBSERVATION_ONLY, WorldEffectStatus.NO_ACTION, 0.4, "observation_missing"
