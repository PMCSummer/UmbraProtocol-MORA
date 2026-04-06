from __future__ import annotations

from substrate.stream_diversification.models import (
    StreamDiversificationGateDecision,
    StreamDiversificationResult,
    StreamDiversificationState,
    StreamDiversificationTelemetry,
    DiversificationLedgerEvent,
)


def build_stream_diversification_telemetry(
    *,
    state: StreamDiversificationState,
    ledger_events: tuple[DiversificationLedgerEvent, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: StreamDiversificationGateDecision,
    causal_basis: str,
) -> StreamDiversificationTelemetry:
    return StreamDiversificationTelemetry(
        source_lineage=state.source_lineage,
        diversification_id=state.diversification_id,
        stream_id=state.stream_id,
        source_stream_sequence_index=state.source_stream_sequence_index,
        path_count=len(state.path_assessments),
        stagnation_signature_count=len(state.stagnation_signatures),
        repeat_requires_justification_count=len(state.repeat_requires_justification_for),
        protected_recurrence_count=len(state.protected_recurrence_classes),
        no_safe_diversification_count=sum(
            1 for assessment in state.path_assessments if assessment.no_safe_diversification
        ),
        actionable_alternative_count=sum(
            len(assessment.actionable_alternative_classes)
            for assessment in state.path_assessments
        ),
        edge_band_applied_count=sum(
            1 for assessment in state.path_assessments if assessment.edge_band_applied
        ),
        survival_filtered_alternative_count=sum(
            1
            for assessment in state.path_assessments
            if assessment.survival_filtered_alternatives
        ),
        diversification_pressure=state.diversification_pressure,
        decision_status=state.decision_status,
        allowed_alternative_classes=tuple(
            dict.fromkeys(path_class.value for path_class in state.allowed_alternative_classes)
        ),
        transition_classes=tuple(
            dict.fromkeys(
                assessment.transition_class.value for assessment in state.path_assessments
            )
        ),
        ledger_events=ledger_events,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def stream_diversification_result_snapshot(
    result: StreamDiversificationResult,
) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_text_antirepeat_dependency": result.no_text_antirepeat_dependency,
        "no_randomness_dependency": result.no_randomness_dependency,
        "no_planner_arbitration_dependency": result.no_planner_arbitration_dependency,
        "state": {
            "diversification_id": state.diversification_id,
            "stream_id": state.stream_id,
            "source_stream_sequence_index": state.source_stream_sequence_index,
            "source_scheduler_id": state.source_scheduler_id,
            "stagnation_signatures": tuple(sig.value for sig in state.stagnation_signatures),
            "redundancy_scores": tuple(
                {
                    "path_id": score.path_id,
                    "transition_class": score.transition_class.value,
                    "repetition_count": score.repetition_count,
                    "progress_delta": score.progress_delta,
                    "redundancy_score": score.redundancy_score,
                    "repeat_requires_justification": score.repeat_requires_justification,
                    "protected_recurrence": score.protected_recurrence,
                }
                for score in state.redundancy_scores
            ),
            "diversification_pressure": state.diversification_pressure,
            "allowed_alternative_classes": tuple(
                path_class.value for path_class in state.allowed_alternative_classes
            ),
            "actionable_alternative_classes": tuple(
                path_class.value for path_class in state.actionable_alternative_classes
            ),
            "repeat_requires_justification_for": state.repeat_requires_justification_for,
            "protected_recurrence_classes": tuple(
                path_class.value for path_class in state.protected_recurrence_classes
            ),
            "decision_status": state.decision_status.value,
            "no_safe_diversification": state.no_safe_diversification,
            "diversification_conflict_with_survival": state.diversification_conflict_with_survival,
            "low_confidence_stagnation": state.low_confidence_stagnation,
            "confidence": state.confidence,
            "source_c01_state_ref": state.source_c01_state_ref,
            "source_c02_state_ref": state.source_c02_state_ref,
            "source_regulation_ref": state.source_regulation_ref,
            "source_affordance_ref": state.source_affordance_ref,
            "source_preference_ref": state.source_preference_ref,
            "source_viability_ref": state.source_viability_ref,
            "source_lineage": state.source_lineage,
            "last_update_provenance": state.last_update_provenance,
            "recent_path_counts": tuple(
                {"path_key": item.path_key, "count": item.count}
                for item in state.recent_path_counts
            ),
            "path_assessments": tuple(
                {
                    "assessment_id": assessment.assessment_id,
                    "path_id": assessment.path_id,
                    "tension_id": assessment.tension_id,
                    "causal_anchor": assessment.causal_anchor,
                    "transition_class": assessment.transition_class.value,
                    "current_status": assessment.current_status,
                    "current_mode": assessment.current_mode,
                    "revisit_priority": assessment.revisit_priority,
                    "repetition_count": assessment.repetition_count,
                    "progress_delta": assessment.progress_delta,
                    "progress_evidence_axes": assessment.progress_evidence_axes,
                    "progress_evidence_class": assessment.progress_evidence_class.value,
                    "new_causal_input": assessment.new_causal_input,
                    "edge_band_applied": assessment.edge_band_applied,
                    "stagnation_signatures": tuple(
                        signature.value for signature in assessment.stagnation_signatures
                    ),
                    "redundancy_score": assessment.redundancy_score,
                    "repeat_requires_justification": assessment.repeat_requires_justification,
                    "protected_recurrence": assessment.protected_recurrence,
                    "alternative_classes": tuple(
                        path_class.value for path_class in assessment.alternative_classes
                    ),
                    "actionable_alternative_classes": tuple(
                        path_class.value
                        for path_class in assessment.actionable_alternative_classes
                    ),
                    "survival_filtered_alternatives": assessment.survival_filtered_alternatives,
                    "no_safe_diversification": assessment.no_safe_diversification,
                    "confidence": assessment.confidence,
                    "reason": assessment.reason,
                    "provenance": assessment.provenance,
                }
                for assessment in state.path_assessments
            ),
        },
        "downstream_gate": {
            "accepted": result.downstream_gate.accepted,
            "usability_class": result.downstream_gate.usability_class.value,
            "restrictions": tuple(
                restriction.value for restriction in result.downstream_gate.restrictions
            ),
            "reason": result.downstream_gate.reason,
            "state_ref": result.downstream_gate.state_ref,
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "diversification_id": result.telemetry.diversification_id,
            "stream_id": result.telemetry.stream_id,
            "source_stream_sequence_index": result.telemetry.source_stream_sequence_index,
            "path_count": result.telemetry.path_count,
            "stagnation_signature_count": result.telemetry.stagnation_signature_count,
            "repeat_requires_justification_count": result.telemetry.repeat_requires_justification_count,
            "protected_recurrence_count": result.telemetry.protected_recurrence_count,
            "no_safe_diversification_count": result.telemetry.no_safe_diversification_count,
            "actionable_alternative_count": result.telemetry.actionable_alternative_count,
            "edge_band_applied_count": result.telemetry.edge_band_applied_count,
            "survival_filtered_alternative_count": result.telemetry.survival_filtered_alternative_count,
            "diversification_pressure": result.telemetry.diversification_pressure,
            "decision_status": result.telemetry.decision_status.value,
            "allowed_alternative_classes": result.telemetry.allowed_alternative_classes,
            "transition_classes": result.telemetry.transition_classes,
            "ledger_events": tuple(
                {
                    "event_id": event.event_id,
                    "event_kind": event.event_kind.value,
                    "path_id": event.path_id,
                    "tension_id": event.tension_id,
                    "stream_id": event.stream_id,
                    "reason": event.reason,
                    "reason_code": event.reason_code,
                    "provenance": event.provenance,
                }
                for event in result.telemetry.ledger_events
            ),
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": tuple(
                    code.value for code in result.telemetry.downstream_gate.restrictions
                ),
                "reason": result.telemetry.downstream_gate.reason,
                "state_ref": result.telemetry.downstream_gate.state_ref,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
