from __future__ import annotations

from substrate.downstream_obedience.models import DownstreamObedienceDecision


def downstream_obedience_snapshot(decision: DownstreamObedienceDecision) -> dict[str, object]:
    return {
        "status": decision.status.value,
        "fallback": decision.fallback.value,
        "lawful_continue": decision.lawful_continue,
        "authority_basis_ok": decision.authority_basis_ok,
        "invalidated_upstream_surface": decision.invalidated_upstream_surface,
        "blocked_by_survival_override": decision.blocked_by_survival_override,
        "source_of_truth_surface": decision.source_of_truth_surface,
        "requires_restrictions_read": decision.requires_restrictions_read,
        "restrictions": tuple(
            {
                "restriction_code": item.restriction_code,
                "source_phase": item.source_phase,
                "authority_role": item.authority_role,
                "computational_role": item.computational_role,
                "source_of_truth_surface": item.source_of_truth_surface,
                "required_fallback": item.required_fallback.value,
                "reason": item.reason,
                "provenance_ref": item.provenance_ref,
            }
            for item in decision.restrictions
        ),
        "checkpoints": tuple(
            {
                "checkpoint_id": item.checkpoint_id,
                "status": item.status,
                "source_phase": item.source_phase,
                "relation_kind": item.relation_kind,
                "reason": item.reason,
            }
            for item in decision.checkpoints
        ),
        "reason": decision.reason,
    }

