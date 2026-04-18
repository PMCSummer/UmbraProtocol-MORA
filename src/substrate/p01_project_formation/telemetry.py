from __future__ import annotations

from substrate.p01_project_formation.models import P01ProjectFormationResult


def p01_project_formation_snapshot(result: P01ProjectFormationResult) -> dict[str, object]:
    if not isinstance(result, P01ProjectFormationResult):
        raise TypeError("p01_project_formation_snapshot requires P01ProjectFormationResult")
    return {
        "state": {
            "stack_id": result.state.stack_id,
            "active_projects": tuple(
                _entry_snapshot(item) for item in result.state.active_projects
            ),
            "candidate_projects": tuple(
                _entry_snapshot(item) for item in result.state.candidate_projects
            ),
            "suspended_projects": tuple(
                _entry_snapshot(item) for item in result.state.suspended_projects
            ),
            "rejected_candidates": tuple(
                _entry_snapshot(item) for item in result.state.rejected_candidates
            ),
            "arbitration_records": tuple(
                {
                    "arbitration_id": record.arbitration_id,
                    "conflict_group_id": record.conflict_group_id,
                    "involved_project_ids": record.involved_project_ids,
                    "outcome": record.outcome.value,
                    "reason": record.reason,
                    "provenance": record.provenance,
                }
                for record in result.state.arbitration_records
            ),
            "no_safe_project_formation": result.state.no_safe_project_formation,
            "grounded_context_underconstrained": result.state.grounded_context_underconstrained,
            "prompt_local_capture_risk": result.state.prompt_local_capture_risk,
            "bypass_resistance_status": result.state.bypass_resistance_status,
            "conflicting_authority": result.state.conflicting_authority,
            "blocked_pending_grounding": result.state.blocked_pending_grounding,
            "candidate_only_without_activation_basis": (
                result.state.candidate_only_without_activation_basis
            ),
            "stale_active_project_detected": result.state.stale_active_project_detected,
            "justification_links": result.state.justification_links,
            "provenance": result.state.provenance,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "intention_stack_consumer_ready": result.gate.intention_stack_consumer_ready,
            "authority_bound_consumer_ready": result.gate.authority_bound_consumer_ready,
            "project_handoff_consumer_ready": result.gate.project_handoff_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "p01_first_slice_only": result.scope_marker.p01_first_slice_only,
            "p02_not_implemented": result.scope_marker.p02_not_implemented,
            "p03_not_implemented": result.scope_marker.p03_not_implemented,
            "p04_not_implemented": result.scope_marker.p04_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "stack_id": result.telemetry.stack_id,
            "tick_index": result.telemetry.tick_index,
            "active_project_count": result.telemetry.active_project_count,
            "candidate_project_count": result.telemetry.candidate_project_count,
            "suspended_project_count": result.telemetry.suspended_project_count,
            "rejected_project_count": result.telemetry.rejected_project_count,
            "arbitration_count": result.telemetry.arbitration_count,
            "no_safe_project_formation": result.telemetry.no_safe_project_formation,
            "conflicting_authority": result.telemetry.conflicting_authority,
            "blocked_pending_grounding": result.telemetry.blocked_pending_grounding,
            "prompt_local_capture_risk": result.telemetry.prompt_local_capture_risk,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }


def _entry_snapshot(entry: object) -> dict[str, object]:
    return {
        "project_id": getattr(entry, "project_id"),
        "project_identity_key": getattr(entry, "project_identity_key"),
        "project_class": getattr(entry, "project_class"),
        "source_of_authority": getattr(entry, "source_of_authority").value,
        "objective_summary_or_typed_target": getattr(entry, "objective_summary_or_typed_target"),
        "commitment_grade": getattr(entry, "commitment_grade").value,
        "priority_class": getattr(entry, "priority_class").value,
        "activation_conditions": getattr(entry, "activation_conditions"),
        "suspension_conditions": getattr(entry, "suspension_conditions"),
        "termination_conditions": getattr(entry, "termination_conditions"),
        "dependency_refs": getattr(entry, "dependency_refs"),
        "current_status": getattr(entry, "current_status").value,
        "admissibility_verdict": getattr(entry, "admissibility_verdict").value,
        "provenance": getattr(entry, "provenance"),
        "formation_trace_refs": getattr(entry, "formation_trace_refs"),
        "carryover_basis": getattr(entry, "carryover_basis"),
        "stale_risk_marker": getattr(entry, "stale_risk_marker"),
    }

