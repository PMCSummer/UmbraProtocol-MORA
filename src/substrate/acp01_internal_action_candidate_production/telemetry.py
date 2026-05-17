from __future__ import annotations

from substrate.acp01_internal_action_candidate_production.models import (
    ACP01CandidateProductionResult,
)


def acp01_internal_action_candidate_production_snapshot(
    result: ACP01CandidateProductionResult,
) -> dict[str, object]:
    if not isinstance(result, ACP01CandidateProductionResult):
        raise TypeError(
            "acp01_internal_action_candidate_production_snapshot requires ACP01CandidateProductionResult"
        )
    return {
        "result": {
            "tick_ref": result.tick_ref,
            "decision_count": len(result.decisions),
            "proposal_count": result.proposal_count,
            "proposed_count": result.proposed_count,
            "candidate_set_for_ap01_present": result.candidate_set_for_ap01 is not None,
            "reason": result.reason,
        },
        "decisions": [
            {
                "decision_id": item.decision_id,
                "status": item.status.value,
                "reason_codes": item.reason_codes,
                "proposal_id": None if item.proposal is None else item.proposal.candidate_id,
                "missing_requirements": item.missing_requirements,
                "blocked_refs": item.blocked_refs,
            }
            for item in result.decisions
        ],
        "telemetry": {
            "decision_count": result.telemetry.decision_count,
            "proposal_count": result.telemetry.proposal_count,
            "proposed_count": result.telemetry.proposed_count,
            "blocked_count": result.telemetry.blocked_count,
            "revalidation_required_count": result.telemetry.revalidation_required_count,
            "unsafe_basis_count": result.telemetry.unsafe_basis_count,
            "insufficient_basis_count": result.telemetry.insufficient_basis_count,
            "no_candidate_count": result.telemetry.no_candidate_count,
            "private_eval_excluded": result.telemetry.private_eval_excluded,
            "scenario_label_excluded": result.telemetry.scenario_label_excluded,
            "emitted_at": result.telemetry.emitted_at,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "candidate_production_only": result.scope_marker.candidate_production_only,
            "no_publication_authority": result.scope_marker.no_publication_authority,
            "no_execution_authority": result.scope_marker.no_execution_authority,
            "no_world_submission_authority": result.scope_marker.no_world_submission_authority,
            "no_phase_override_authority": result.scope_marker.no_phase_override_authority,
            "reason": result.scope_marker.reason,
        },
    }
