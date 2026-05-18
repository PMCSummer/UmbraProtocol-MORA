from __future__ import annotations

from dataclasses import dataclass

from .models import AB2HypothesisSeedResult


@dataclass(frozen=True, slots=True)
class AB2DownstreamContract:
    seed_set_id: str | None
    hypothesis_refs: tuple[str, ...]
    hypothesis_count: int
    may_be_consumed_as_fact: bool
    may_be_consumed_as_frontier: bool
    may_be_consumed_as_action_candidate: bool
    may_be_consumed_as_ap01_request: bool
    closure_status: str
    reason: str


def build_ab2_downstream_contract(result: AB2HypothesisSeedResult) -> AB2DownstreamContract:
    if result.seed_set is None:
        return AB2DownstreamContract(
            seed_set_id=None,
            hypothesis_refs=(),
            hypothesis_count=0,
            may_be_consumed_as_fact=False,
            may_be_consumed_as_frontier=False,
            may_be_consumed_as_action_candidate=False,
            may_be_consumed_as_ap01_request=False,
            closure_status="blocked",
            reason="ab2 requires public event/residue basis and does not emit facts/actions",
        )
    hypotheses = result.seed_set.hypotheses
    return AB2DownstreamContract(
        seed_set_id=result.seed_set.seed_set_id,
        hypothesis_refs=tuple(item.hypothesis_id for item in hypotheses),
        hypothesis_count=len(hypotheses),
        may_be_consumed_as_fact=False,
        may_be_consumed_as_frontier=False,
        may_be_consumed_as_action_candidate=False,
        may_be_consumed_as_ap01_request=False,
        closure_status=result.seed_set.closure_status.value,
        reason="ab2 emits bounded hypothesis seeds only; no fact closure, no frontier resolution, no action authority",
    )
