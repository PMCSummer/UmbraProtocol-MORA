from __future__ import annotations

from substrate.c06_surfacing_candidates.models import C06SurfacingResult


def c06_surfacing_candidates_snapshot(result: C06SurfacingResult) -> dict[str, object]:
    if not isinstance(result, C06SurfacingResult):
        raise TypeError("c06_surfacing_candidates_snapshot requires C06SurfacingResult")
    return {
        "candidate_set": {
            "candidate_set_id": result.candidate_set.candidate_set_id,
            "status": result.candidate_set.status.value,
            "surfaced_candidates": tuple(
                {
                    "candidate_id": item.candidate_id,
                    "candidate_class": item.candidate_class.value,
                    "source_refs": item.source_refs,
                    "identity_hint": item.identity_hint,
                    "identity_stabilizer": item.identity_stabilizer,
                    "continuity_horizon": item.continuity_horizon.value,
                    "strength_grade": item.strength_grade.value,
                    "uncertainty_state": item.uncertainty_state.value,
                    "relation_to_current_project": item.relation_to_current_project,
                    "relation_to_discourse": item.relation_to_discourse,
                    "suggested_next_layer_consumers": item.suggested_next_layer_consumers,
                    "dismissal_risk": item.dismissal_risk,
                    "rationale_codes": item.rationale_codes,
                    "provenance": item.provenance,
                }
                for item in result.candidate_set.surfaced_candidates
            ),
            "suppression_report": {
                "examined_item_count": result.candidate_set.suppression_report.examined_item_count,
                "suppressed_item_count": result.candidate_set.suppression_report.suppressed_item_count,
                "suppressed_items": tuple(
                    {
                        "item_id": item.item_id,
                        "suppression_reason": item.suppression_reason.value,
                        "source_refs": item.source_refs,
                        "rationale_codes": item.rationale_codes,
                        "provenance": item.provenance,
                    }
                    for item in result.candidate_set.suppression_report.suppressed_items
                ),
                "reason": result.candidate_set.suppression_report.reason,
            },
            "metadata": {
                "candidate_count": result.candidate_set.metadata.candidate_count,
                "ambiguous_candidate_count": result.candidate_set.metadata.ambiguous_candidate_count,
                "commitment_carryover_count": result.candidate_set.metadata.commitment_carryover_count,
                "repair_obligation_count": result.candidate_set.metadata.repair_obligation_count,
                "protective_monitor_count": result.candidate_set.metadata.protective_monitor_count,
                "closure_candidate_count": result.candidate_set.metadata.closure_candidate_count,
                "duplicate_merge_count": result.candidate_set.metadata.duplicate_merge_count,
                "false_merge_detected": result.candidate_set.metadata.false_merge_detected,
                "no_continuity_candidates": result.candidate_set.metadata.no_continuity_candidates,
                "published_frontier_requirement": result.candidate_set.metadata.published_frontier_requirement,
                "published_frontier_requirement_satisfied": (
                    result.candidate_set.metadata.published_frontier_requirement_satisfied
                ),
                "unresolved_ambiguity_preserved": result.candidate_set.metadata.unresolved_ambiguity_preserved,
                "confidence_residue_preserved": result.candidate_set.metadata.confidence_residue_preserved,
                "source_lineage": result.candidate_set.metadata.source_lineage,
            },
            "reason": result.candidate_set.reason,
        },
        "gate": {
            "candidate_set_consumer_ready": result.gate.candidate_set_consumer_ready,
            "suppression_report_consumer_ready": result.gate.suppression_report_consumer_ready,
            "identity_merge_consumer_ready": result.gate.identity_merge_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "c06_first_slice_only": result.scope_marker.c06_first_slice_only,
            "c06_1_workspace_handoff_contract": result.scope_marker.c06_1_workspace_handoff_contract,
            "no_retention_write_layer": result.scope_marker.no_retention_write_layer,
            "no_project_reformation_layer": result.scope_marker.no_project_reformation_layer,
            "no_map_wide_rollout_claim": result.scope_marker.no_map_wide_rollout_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "candidate_set_id": result.telemetry.candidate_set_id,
            "tick_index": result.telemetry.tick_index,
            "status": result.telemetry.status.value,
            "surfaced_candidate_count": result.telemetry.surfaced_candidate_count,
            "suppressed_item_count": result.telemetry.suppressed_item_count,
            "commitment_carryover_count": result.telemetry.commitment_carryover_count,
            "repair_obligation_count": result.telemetry.repair_obligation_count,
            "protective_monitor_count": result.telemetry.protective_monitor_count,
            "closure_candidate_count": result.telemetry.closure_candidate_count,
            "ambiguous_candidate_count": result.telemetry.ambiguous_candidate_count,
            "duplicate_merge_count": result.telemetry.duplicate_merge_count,
            "false_merge_detected": result.telemetry.false_merge_detected,
            "published_frontier_requirement": result.telemetry.published_frontier_requirement,
            "unresolved_ambiguity_preserved": result.telemetry.unresolved_ambiguity_preserved,
            "confidence_residue_preserved": result.telemetry.confidence_residue_preserved,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
