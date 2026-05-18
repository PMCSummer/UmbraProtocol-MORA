from __future__ import annotations

from dataclasses import dataclass

from .models import AB6CausalAttributionResult


@dataclass(frozen=True, slots=True)
class AB6DownstreamContract:
    attribution_frame_ref: str | None
    may_inform_downstream_attribution_consumer: bool
    may_update_hypotheses: bool
    may_select_epistemic_action: bool
    may_emit_action_candidate: bool
    may_emit_ap01_request: bool
    may_execute_world: bool
    may_claim_fact: bool
    reason: str


def build_ab6_downstream_contract(result: AB6CausalAttributionResult) -> AB6DownstreamContract:
    if result.frame is None:
        return AB6DownstreamContract(
            attribution_frame_ref=None,
            may_inform_downstream_attribution_consumer=False,
            may_update_hypotheses=False,
            may_select_epistemic_action=False,
            may_emit_action_candidate=False,
            may_emit_ap01_request=False,
            may_execute_world=False,
            may_claim_fact=False,
            reason="ab6 requires valid public attribution evidence frame",
        )
    return AB6DownstreamContract(
        attribution_frame_ref=result.frame.attribution_frame_id,
        may_inform_downstream_attribution_consumer=True,
        may_update_hypotheses=False,
        may_select_epistemic_action=False,
        may_emit_action_candidate=False,
        may_emit_ap01_request=False,
        may_execute_world=False,
        may_claim_fact=False,
        reason="ab6 emits bounded attribution frame only; no action/update/execution/fact authority",
    )
