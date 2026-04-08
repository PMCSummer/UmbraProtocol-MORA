from __future__ import annotations

from substrate.world_adapter.models import (
    WorldAdapterGateDecision,
    WorldAdapterState,
    WorldEffectStatus,
    WorldLinkStatus,
)


def evaluate_world_adapter_claim_gate(
    state: WorldAdapterState,
) -> WorldAdapterGateDecision:
    if not isinstance(state, WorldAdapterState):
        raise TypeError("evaluate_world_adapter_claim_gate requires WorldAdapterState")

    restrictions = [
        "world_seam_contract_must_be_read",
        "world_seam_not_world_model",
        "world_grounding_requires_external_presence",
        "world_effect_claims_require_effect_feedback",
    ]
    world_grounded_transition_allowed = (
        state.adapter_presence
        and state.adapter_available
        and not state.adapter_degraded
        and state.last_observation_packet is not None
    )
    effect_feedback_correlated = state.effect_feedback_correlated
    externally_effected_change_claim_allowed = effect_feedback_correlated and state.effect_status in {
        WorldEffectStatus.OBSERVED_SUCCESS,
        WorldEffectStatus.OBSERVED_FAILURE,
    }
    world_action_success_claim_allowed = (
        effect_feedback_correlated and state.effect_status is WorldEffectStatus.OBSERVED_SUCCESS
    )

    if not state.adapter_presence:
        restrictions.append("world_adapter_absent")
    if state.adapter_presence and not state.adapter_available:
        restrictions.append("world_adapter_unavailable")
    if state.adapter_degraded:
        restrictions.append("world_adapter_degraded")
    if state.last_action_packet is not None and state.last_effect_packet is None:
        restrictions.append("action_emitted_without_effect_feedback")
    if state.last_effect_packet is not None and state.last_action_packet is None:
        restrictions.append("effect_feedback_without_action_trace")
    if state.last_effect_packet is not None and not effect_feedback_correlated:
        restrictions.append("effect_feedback_not_correlated_with_action")
    if state.last_observation_packet is None:
        restrictions.append("observation_missing_for_world_grounding")

    return WorldAdapterGateDecision(
        world_grounded_transition_allowed=world_grounded_transition_allowed,
        externally_effected_change_claim_allowed=externally_effected_change_claim_allowed,
        world_action_success_claim_allowed=world_action_success_claim_allowed,
        effect_feedback_correlated=effect_feedback_correlated,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="world adapter claim gate evaluated world seam grounding/effect requirements",
    )
