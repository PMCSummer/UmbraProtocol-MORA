from __future__ import annotations

from dataclasses import dataclass

from .models import AB5UpdateEnvelope


@dataclass(frozen=True, slots=True)
class AB5DownstreamContract:
    prior_frontier_ref: str | None
    update_ref: str | None
    may_update_local_frontier_snapshot: bool
    may_emit_action_candidate: bool
    may_emit_ap01_request: bool
    may_execute_world: bool
    may_claim_fact: bool
    reason: str


def build_ab5_downstream_contract(envelope: AB5UpdateEnvelope) -> AB5DownstreamContract:
    if envelope.update is None:
        return AB5DownstreamContract(
            prior_frontier_ref=None,
            update_ref=None,
            may_update_local_frontier_snapshot=False,
            may_emit_action_candidate=False,
            may_emit_ap01_request=False,
            may_execute_world=False,
            may_claim_fact=False,
            reason="ab5 requires prior frontier with public correlated evidence to emit support deltas",
        )
    return AB5DownstreamContract(
        prior_frontier_ref=envelope.update.prior_frontier_ref,
        update_ref=envelope.update.update_id,
        may_update_local_frontier_snapshot=envelope.update.updated_frontier_snapshot is not None,
        may_emit_action_candidate=False,
        may_emit_ap01_request=False,
        may_execute_world=False,
        may_claim_fact=False,
        reason="ab5 updates bounded hypothesis support only; no action/publication/execution/fact authority",
    )
