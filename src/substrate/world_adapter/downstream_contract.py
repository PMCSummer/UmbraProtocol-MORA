from __future__ import annotations

from dataclasses import dataclass

from substrate.world_adapter.models import WorldAdapterResult


@dataclass(frozen=True, slots=True)
class WorldAdapterContractView:
    world_link_status: str
    effect_status: str
    world_grounded_transition_allowed: bool
    externally_effected_change_claim_allowed: bool
    world_action_success_claim_allowed: bool
    effect_feedback_correlated: bool
    adapter_presence: bool
    adapter_available: bool
    adapter_degraded: bool
    restrictions: tuple[str, ...]
    requires_restrictions_read: bool
    reason: str


def derive_world_adapter_contract_view(result: WorldAdapterResult) -> WorldAdapterContractView:
    if not isinstance(result, WorldAdapterResult):
        raise TypeError("derive_world_adapter_contract_view requires WorldAdapterResult")
    return WorldAdapterContractView(
        world_link_status=result.state.world_link_status.value,
        effect_status=result.state.effect_status.value,
        world_grounded_transition_allowed=result.gate.world_grounded_transition_allowed,
        externally_effected_change_claim_allowed=result.gate.externally_effected_change_claim_allowed,
        world_action_success_claim_allowed=result.gate.world_action_success_claim_allowed,
        effect_feedback_correlated=result.gate.effect_feedback_correlated,
        adapter_presence=result.state.adapter_presence,
        adapter_available=result.state.adapter_available,
        adapter_degraded=result.state.adapter_degraded,
        restrictions=result.gate.restrictions,
        requires_restrictions_read=True,
        reason=result.gate.reason,
    )
