from __future__ import annotations

from substrate.v03_surface_verbalization_causality_constrained_realization.models import (
    V03ConstrainedRealizationResult,
)


def v03_surface_verbalization_causality_constrained_realization_snapshot(
    result: V03ConstrainedRealizationResult,
) -> dict[str, object]:
    if not isinstance(result, V03ConstrainedRealizationResult):
        raise TypeError(
            "v03_surface_verbalization_causality_constrained_realization_snapshot requires "
            "V03ConstrainedRealizationResult"
        )
    return {
        "realization_status": result.realization_status.value,
        "artifact": {
            "realization_id": result.artifact.realization_id,
            "surface_text": result.artifact.surface_text,
            "segment_order": result.artifact.segment_order,
            "realized_segment_ids": result.artifact.realized_segment_ids,
            "omitted_segment_ids": result.artifact.omitted_segment_ids,
            "source_act_ids": result.artifact.source_act_ids,
            "selected_branch_id": result.artifact.selected_branch_id,
            "blocked_expansion_ids": result.artifact.blocked_expansion_ids,
            "protected_omission_ids": result.artifact.protected_omission_ids,
            "partial_realization_only": result.artifact.partial_realization_only,
            "provenance": result.artifact.provenance,
        },
        "alignment_map": {
            "alignments": tuple(
                {
                    "segment_id": alignment.segment_id,
                    "start_index": alignment.start_index,
                    "end_index": alignment.end_index,
                    "realized_text": alignment.realized_text,
                    "source_act_ref": alignment.source_act_ref,
                    "realized": alignment.realized,
                    "qualifier_locality_pass": alignment.qualifier_locality_pass,
                    "ordering_pass": alignment.ordering_pass,
                }
                for alignment in result.alignment_map.alignments
            ),
            "aligned_segment_count": result.alignment_map.aligned_segment_count,
            "unaligned_segment_ids": result.alignment_map.unaligned_segment_ids,
            "branch_compliance_pass": result.alignment_map.branch_compliance_pass,
            "ordering_pass": result.alignment_map.ordering_pass,
            "qualifier_locality_pass": result.alignment_map.qualifier_locality_pass,
        },
        "constraint_report": {
            "hard_constraint_violation_count": result.constraint_report.hard_constraint_violation_count,
            "qualifier_locality_failures": result.constraint_report.qualifier_locality_failures,
            "blocked_expansion_leak_detected": result.constraint_report.blocked_expansion_leak_detected,
            "protected_omission_violation_detected": result.constraint_report.protected_omission_violation_detected,
            "boundary_before_explanation_required": result.constraint_report.boundary_before_explanation_required,
            "boundary_before_explanation_satisfied": result.constraint_report.boundary_before_explanation_satisfied,
            "clarification_before_assertion_required": result.constraint_report.clarification_before_assertion_required,
            "clarification_before_assertion_satisfied": result.constraint_report.clarification_before_assertion_satisfied,
            "branch_compliance_pass": result.constraint_report.branch_compliance_pass,
            "ordering_pass": result.constraint_report.ordering_pass,
            "implicit_commitment_leak_detected": result.constraint_report.implicit_commitment_leak_detected,
            "violation_codes": result.constraint_report.violation_codes,
            "satisfied_codes": result.constraint_report.satisfied_codes,
        },
        "failure_state": {
            "failed": result.failure_state.failed,
            "failure_code": result.failure_state.failure_code,
            "partial_realization_only": result.failure_state.partial_realization_only,
            "replan_required": result.failure_state.replan_required,
            "reason": result.failure_state.reason,
        },
        "gate": {
            "realization_consumer_ready": result.gate.realization_consumer_ready,
            "alignment_consumer_ready": result.gate.alignment_consumer_ready,
            "constraint_report_consumer_ready": result.gate.constraint_report_consumer_ready,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "v03_first_slice_only": result.scope_marker.v03_first_slice_only,
            "v_line_not_map_wide_ready": result.scope_marker.v_line_not_map_wide_ready,
            "p02_not_implemented": result.scope_marker.p02_not_implemented,
            "map_wide_realization_enforcement": result.scope_marker.map_wide_realization_enforcement,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "realization_id": result.telemetry.realization_id,
            "tick_index": result.telemetry.tick_index,
            "realization_status": result.telemetry.realization_status.value,
            "segment_count": result.telemetry.segment_count,
            "aligned_segment_count": result.telemetry.aligned_segment_count,
            "hard_constraint_violation_count": result.telemetry.hard_constraint_violation_count,
            "qualifier_locality_failures": result.telemetry.qualifier_locality_failures,
            "blocked_expansion_leak_detected": result.telemetry.blocked_expansion_leak_detected,
            "protected_omission_count": result.telemetry.protected_omission_count,
            "boundary_before_explanation_required": result.telemetry.boundary_before_explanation_required,
            "boundary_before_explanation_satisfied": result.telemetry.boundary_before_explanation_satisfied,
            "partial_realization_only": result.telemetry.partial_realization_only,
            "replan_required": result.telemetry.replan_required,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }

