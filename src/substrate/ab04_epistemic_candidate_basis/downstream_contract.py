from __future__ import annotations

from dataclasses import dataclass

from .models import AB4EpistemicBasisResult


@dataclass(frozen=True, slots=True)
class AB4DownstreamContract:
    frontier_ref: str | None
    basis_refs: tuple[str, ...]
    basis_count: int
    may_be_consumed_as_acp01_basis: bool
    may_be_consumed_as_action_candidate: bool
    may_be_consumed_as_ap01_request: bool
    may_execute_world: bool
    reason: str


def build_ab4_downstream_contract(result: AB4EpistemicBasisResult) -> AB4DownstreamContract:
    if not result.bases:
        return AB4DownstreamContract(
            frontier_ref=result.frontier_ref,
            basis_refs=(),
            basis_count=0,
            may_be_consumed_as_acp01_basis=False,
            may_be_consumed_as_action_candidate=False,
            may_be_consumed_as_ap01_request=False,
            may_execute_world=False,
            reason="ab4 requires lawful open frontier with uncertainty and discriminating tests",
        )
    return AB4DownstreamContract(
        frontier_ref=result.frontier_ref,
        basis_refs=tuple(item.basis_id for item in result.bases),
        basis_count=len(result.bases),
        may_be_consumed_as_acp01_basis=True,
        may_be_consumed_as_action_candidate=False,
        may_be_consumed_as_ap01_request=False,
        may_execute_world=False,
        reason="ab4 emits bounded epistemic basis for potential acp01 consumption only",
    )
