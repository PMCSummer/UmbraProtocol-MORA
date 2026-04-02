from __future__ import annotations

from substrate.viability_control.models import (
    ViabilityCalibrationSpec,
    ViabilityControlDirective,
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityGateDecision,
    ViabilityTelemetry,
)


def build_viability_telemetry(
    *,
    state: ViabilityControlState,
    directives: tuple[ViabilityControlDirective, ...],
    source_lineage: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
    boundary_compatibility: tuple[str, ...],
    calibration: ViabilityCalibrationSpec,
    downstream_gate: ViabilityGateDecision,
    causal_basis: str,
    attempted_computation_paths: tuple[str, ...],
) -> ViabilityTelemetry:
    _ = directives
    return ViabilityTelemetry(
        source_lineage=source_lineage,
        input_regulation_snapshot_ref=state.input_regulation_snapshot_ref,
        input_affordance_ref=state.input_affordance_ref,
        input_preference_ref=state.input_preference_ref,
        affected_need_ids=state.affected_need_ids,
        computed_pressure_level=state.pressure_level,
        computed_escalation_stage=state.escalation_stage,
        predicted_time_to_boundary=state.predicted_time_to_boundary,
        recoverability_estimate=state.recoverability_estimate,
        recoverability_components=state.recoverability_components,
        calibration_id=calibration.calibration_id,
        calibration_schema_version=calibration.schema_version,
        override_scope=state.override_scope,
        persistence_status=state.persistence_state,
        deescalation_condition_markers=state.deescalation_conditions,
        blocked_reasons=blocked_reasons,
        uncertainty_reasons=tuple(marker.value for marker in state.uncertainty_state),
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
        attempted_computation_paths=attempted_computation_paths,
        recent_failed_recovery_count=state.recent_failed_recovery_count,
        boundary_compatibility=boundary_compatibility,
    )


def viability_result_snapshot(result: ViabilityControlResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_action_selection_performed": result.no_action_selection_performed,
        "state": {
            "pressure_level": state.pressure_level,
            "escalation_stage": state.escalation_stage.value,
            "affected_need_ids": tuple(axis.value for axis in state.affected_need_ids),
            "predicted_time_to_boundary": state.predicted_time_to_boundary,
            "recoverability_estimate": state.recoverability_estimate,
            "recoverability_components": (
                {
                    "viable_affordance_coverage": state.recoverability_components.viable_affordance_coverage,
                    "restorative_capacity_evidence": state.recoverability_components.restorative_capacity_evidence,
                    "blocked_or_unavailable_fraction": state.recoverability_components.blocked_or_unavailable_fraction,
                    "preference_support_bias": state.recoverability_components.preference_support_bias,
                    "evidence_quality": state.recoverability_components.evidence_quality,
                    "recent_failed_restoration_penalty": state.recoverability_components.recent_failed_restoration_penalty,
                }
                if state.recoverability_components is not None
                else None
            ),
            "calibration_id": state.calibration_id,
            "calibration_schema_version": state.calibration_schema_version,
            "override_scope": state.override_scope.value,
            "persistence_state": state.persistence_state.value,
            "deescalation_conditions": state.deescalation_conditions,
            "confidence": state.confidence.value,
            "uncertainty_state": tuple(marker.value for marker in state.uncertainty_state),
            "recent_failed_recovery_count": state.recent_failed_recovery_count,
            "mixed_deterioration": state.mixed_deterioration,
            "no_strong_override_claim": state.no_strong_override_claim,
            "input_regulation_snapshot_ref": state.input_regulation_snapshot_ref,
            "input_affordance_ref": state.input_affordance_ref,
            "input_preference_ref": state.input_preference_ref,
            "provenance": state.provenance,
        },
        "directives": tuple(
            {
                "directive_id": directive.directive_id,
                "directive_type": directive.directive_type.value,
                "intensity": directive.intensity,
                "affected_need_ids": tuple(axis.value for axis in directive.affected_need_ids),
                "override_scope": directive.override_scope.value,
                "reason": directive.reason,
                "capped_by_uncertainty": directive.capped_by_uncertainty,
                "provenance": directive.provenance,
            }
            for directive in result.directives
        ),
        "downstream_gate": {
            "accepted": result.downstream_gate.accepted,
            "restrictions": result.downstream_gate.restrictions,
            "reason": result.downstream_gate.reason,
            "accepted_directive_ids": result.downstream_gate.accepted_directive_ids,
            "rejected_directive_ids": result.downstream_gate.rejected_directive_ids,
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "input_regulation_snapshot_ref": result.telemetry.input_regulation_snapshot_ref,
            "input_affordance_ref": result.telemetry.input_affordance_ref,
            "input_preference_ref": result.telemetry.input_preference_ref,
            "affected_need_ids": tuple(axis.value for axis in result.telemetry.affected_need_ids),
            "computed_pressure_level": result.telemetry.computed_pressure_level,
            "computed_escalation_stage": result.telemetry.computed_escalation_stage.value,
            "predicted_time_to_boundary": result.telemetry.predicted_time_to_boundary,
            "recoverability_estimate": result.telemetry.recoverability_estimate,
            "recoverability_components": (
                {
                    "viable_affordance_coverage": result.telemetry.recoverability_components.viable_affordance_coverage,
                    "restorative_capacity_evidence": result.telemetry.recoverability_components.restorative_capacity_evidence,
                    "blocked_or_unavailable_fraction": result.telemetry.recoverability_components.blocked_or_unavailable_fraction,
                    "preference_support_bias": result.telemetry.recoverability_components.preference_support_bias,
                    "evidence_quality": result.telemetry.recoverability_components.evidence_quality,
                    "recent_failed_restoration_penalty": result.telemetry.recoverability_components.recent_failed_restoration_penalty,
                }
                if result.telemetry.recoverability_components is not None
                else None
            ),
            "calibration_id": result.telemetry.calibration_id,
            "calibration_schema_version": result.telemetry.calibration_schema_version,
            "override_scope": result.telemetry.override_scope.value,
            "persistence_status": result.telemetry.persistence_status.value,
            "deescalation_condition_markers": result.telemetry.deescalation_condition_markers,
            "blocked_reasons": result.telemetry.blocked_reasons,
            "uncertainty_reasons": result.telemetry.uncertainty_reasons,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_directive_ids": result.telemetry.downstream_gate.accepted_directive_ids,
                "rejected_directive_ids": result.telemetry.downstream_gate.rejected_directive_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
            "attempted_computation_paths": result.telemetry.attempted_computation_paths,
            "recent_failed_recovery_count": result.telemetry.recent_failed_recovery_count,
            "boundary_compatibility": result.telemetry.boundary_compatibility,
        },
    }
