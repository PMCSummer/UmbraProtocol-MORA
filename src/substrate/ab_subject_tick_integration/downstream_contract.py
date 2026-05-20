from __future__ import annotations

from dataclasses import dataclass

from .models import ABLiveTickResult


@dataclass(frozen=True, slots=True)
class ABLiveDownstreamContract:
    result_ref: str
    may_emit_action_candidate: bool
    may_emit_ap01_request: bool
    may_execute_world: bool
    may_claim_fact: bool
    may_claim_cause_confirmation: bool
    may_claim_mature_recipe: bool
    may_claim_automation: bool
    reason: str


def build_ab_live_downstream_contract(result: ABLiveTickResult) -> ABLiveDownstreamContract:
    return ABLiveDownstreamContract(
        result_ref=f"ab_live:{result.tick_id}",
        may_emit_action_candidate=False,
        may_emit_ap01_request=False,
        may_execute_world=False,
        may_claim_fact=False,
        may_claim_cause_confirmation=False,
        may_claim_mature_recipe=False,
        may_claim_automation=False,
        reason="ab-int emits bounded abductive artifacts only and preserves ap01/acp01 authority boundary",
    )
