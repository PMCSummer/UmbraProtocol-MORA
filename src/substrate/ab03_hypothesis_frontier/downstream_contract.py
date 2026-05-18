from __future__ import annotations

from dataclasses import dataclass

from .models import AB3FrontierResult


@dataclass(frozen=True, slots=True)
class AB3DownstreamContract:
    frontier_id: str | None
    hypothesis_refs: tuple[str, ...]
    hypothesis_count: int
    closure_status: str
    may_be_consumed_as_fact: bool
    may_be_consumed_as_action_candidate: bool
    may_be_consumed_as_ap01_request: bool
    may_select_epistemic_action: bool
    reason: str


def build_ab3_downstream_contract(result: AB3FrontierResult) -> AB3DownstreamContract:
    if result.frontier is None:
        return AB3DownstreamContract(
            frontier_id=None,
            hypothesis_refs=(),
            hypothesis_count=0,
            closure_status="blocked",
            may_be_consumed_as_fact=False,
            may_be_consumed_as_action_candidate=False,
            may_be_consumed_as_ap01_request=False,
            may_select_epistemic_action=False,
            reason="ab3 requires lawful ab2 seed basis and remains non-action non-fact frontier",
        )
    return AB3DownstreamContract(
        frontier_id=result.frontier.frontier_id,
        hypothesis_refs=tuple(item.hypothesis_id for item in result.frontier.hypotheses),
        hypothesis_count=len(result.frontier.hypotheses),
        closure_status=result.frontier.closure_status.value,
        may_be_consumed_as_fact=False,
        may_be_consumed_as_action_candidate=False,
        may_be_consumed_as_ap01_request=False,
        may_select_epistemic_action=False,
        reason="ab3 maintains bounded explanation frontier only; no fact closure and no action authority",
    )
