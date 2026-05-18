from __future__ import annotations

from dataclasses import dataclass

from .models import AB7IntegrationEnvelope


@dataclass(frozen=True, slots=True)
class AB7DownstreamContract:
    frame_ref: str | None
    may_emit_recipe_candidate: bool
    may_emit_mature_recipe_claim: bool
    may_emit_automation_plan: bool
    may_emit_action_candidate: bool
    may_emit_ap01_request: bool
    may_execute_world: bool
    reason: str


def build_ab7_downstream_contract(envelope: AB7IntegrationEnvelope) -> AB7DownstreamContract:
    if envelope.frame is None:
        return AB7DownstreamContract(
            frame_ref=None,
            may_emit_recipe_candidate=False,
            may_emit_mature_recipe_claim=False,
            may_emit_automation_plan=False,
            may_emit_action_candidate=False,
            may_emit_ap01_request=False,
            may_execute_world=False,
            reason="ab7 requires public abductive + p13/p14 constraints to emit integration frame",
        )
    return AB7DownstreamContract(
        frame_ref=envelope.frame.frame_id,
        may_emit_recipe_candidate=False,
        may_emit_mature_recipe_claim=False,
        may_emit_automation_plan=False,
        may_emit_action_candidate=False,
        may_emit_ap01_request=False,
        may_execute_world=False,
        reason="ab7 emits constraint frame only; no automation/action/execution/fact authority",
    )
