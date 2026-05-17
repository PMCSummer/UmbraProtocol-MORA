from __future__ import annotations

from substrate.ap01_subject_action_publication.models import AP01SubjectActionPublicationResult


def ap01_subject_action_publication_snapshot(
    result: AP01SubjectActionPublicationResult,
) -> dict[str, object]:
    if not isinstance(result, AP01SubjectActionPublicationResult):
        raise TypeError(
            "ap01_subject_action_publication_snapshot requires AP01SubjectActionPublicationResult"
        )
    return {
        "result": {
            "candidate_set_id": result.candidate_set_id,
            "decision_count": len(result.decisions),
            "published_request_count": len(result.published_requests),
            "reason": result.reason,
        },
        "decisions": [
            {
                "decision_id": item.decision_id,
                "candidate_id": item.candidate_id,
                "decision_status": item.decision_status.value,
                "reason_codes": item.reason_codes,
                "blocked_reason": item.blocked_reason,
                "missing_requirements": item.missing_requirements,
                "preserved_residue_refs": item.preserved_residue_refs,
                "downstream_permission_delta": item.downstream_permission_delta,
                "published_request_id": (
                    None if item.published_request is None else item.published_request.request_id
                ),
            }
            for item in result.decisions
        ],
        "gate": {
            "execution_boundary_preserved": result.telemetry.execution_boundary_preserved,
            "must_wait_for_effect": result.telemetry.must_wait_for_effect,
            "no_hidden_truth_used": result.telemetry.no_hidden_truth_used,
            "no_eval_only_used": result.telemetry.no_eval_only_used,
            "no_scenario_label_used": result.telemetry.no_scenario_label_used,
        },
        "telemetry": {
            "candidate_count": result.telemetry.candidate_count,
            "published_request_count": result.telemetry.published_request_count,
            "blocked_count": result.telemetry.blocked_count,
            "revalidation_required_count": result.telemetry.revalidation_required_count,
            "abstain_count": result.telemetry.abstain_count,
            "malformed_count": result.telemetry.malformed_count,
            "unsafe_basis_count": result.telemetry.unsafe_basis_count,
            "execution_boundary_preserved": result.telemetry.execution_boundary_preserved,
            "must_wait_for_effect": result.telemetry.must_wait_for_effect,
            "no_hidden_truth_used": result.telemetry.no_hidden_truth_used,
            "no_eval_only_used": result.telemetry.no_eval_only_used,
            "no_scenario_label_used": result.telemetry.no_scenario_label_used,
            "emitted_at": result.telemetry.emitted_at,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "publication_not_planner": result.scope_marker.publication_not_planner,
            "publication_not_execution": result.scope_marker.publication_not_execution,
            "no_world_mutation_inside_subject": (
                result.scope_marker.no_world_mutation_inside_subject
            ),
            "no_phase_override_authority": result.scope_marker.no_phase_override_authority,
            "reason": result.scope_marker.reason,
        },
    }
