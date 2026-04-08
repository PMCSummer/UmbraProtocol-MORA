from __future__ import annotations

from dataclasses import dataclass

from substrate.downstream_obedience.models import DownstreamObedienceDecision


@dataclass(frozen=True, slots=True)
class DownstreamObedienceContractView:
    status: str
    fallback: str
    lawful_continue: bool
    source_of_truth_surface: str
    requires_restrictions_read: bool
    blocked_by_survival_override: bool
    invalidated_upstream_surface: bool
    authority_basis_ok: bool
    restriction_codes: tuple[str, ...]
    checkpoint_ids: tuple[str, ...]
    reason: str


def derive_downstream_obedience_contract_view(
    decision: DownstreamObedienceDecision,
) -> DownstreamObedienceContractView:
    return DownstreamObedienceContractView(
        status=decision.status.value,
        fallback=decision.fallback.value,
        lawful_continue=decision.lawful_continue,
        source_of_truth_surface=decision.source_of_truth_surface,
        requires_restrictions_read=decision.requires_restrictions_read,
        blocked_by_survival_override=decision.blocked_by_survival_override,
        invalidated_upstream_surface=decision.invalidated_upstream_surface,
        authority_basis_ok=decision.authority_basis_ok,
        restriction_codes=tuple(item.restriction_code for item in decision.restrictions),
        checkpoint_ids=tuple(item.checkpoint_id for item in decision.checkpoints),
        reason=decision.reason,
    )

