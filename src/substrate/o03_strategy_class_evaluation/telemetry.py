from __future__ import annotations

from substrate.o03_strategy_class_evaluation.models import O03StrategyEvaluationResult


def o03_strategy_class_evaluation_snapshot(
    result: O03StrategyEvaluationResult,
) -> dict[str, object]:
    if not isinstance(result, O03StrategyEvaluationResult):
        raise TypeError(
            "o03_strategy_class_evaluation_snapshot requires O03StrategyEvaluationResult"
        )
    return {
        "state": {
            "strategy_id": result.state.strategy_id,
            "candidate_move_id": result.state.candidate_move_id,
            "strategy_class": result.state.strategy_class.value,
            "cooperation_score": result.state.cooperation_score,
            "manipulation_risk_score": result.state.manipulation_risk_score,
            "hidden_divergence_cost": result.state.hidden_divergence_cost,
            "asymmetry_exploitation_score": result.state.asymmetry_exploitation_score,
            "dependency_induction_risk": result.state.dependency_induction_risk,
            "autonomy_pressure_score": result.state.autonomy_pressure_score,
            "epistemic_distortion_cost": result.state.epistemic_distortion_cost,
            "repair_burden_forecast": result.state.repair_burden_forecast,
            "trust_fragility_forecast": result.state.trust_fragility_forecast,
            "reversibility_score": result.state.reversibility_score,
            "repairability_score": result.state.repairability_score,
            "transparency_score": result.state.transparency_score,
            "local_effectiveness_pressure": result.state.local_effectiveness_pressure.value,
            "hidden_divergence_band": result.state.hidden_divergence_band.value,
            "asymmetry_exploitation_band": result.state.asymmetry_exploitation_band.value,
            "dependency_risk_band": result.state.dependency_risk_band.value,
            "repairability_band": result.state.repairability_band.value,
            "reversibility_band": result.state.reversibility_band.value,
            "autonomy_pressure_band": result.state.autonomy_pressure_band.value,
            "entropy_burden_band": result.state.entropy_burden_band.value,
            "strategy_classification_confidence": result.state.strategy_classification_confidence,
            "other_model_reliance_status": result.state.other_model_reliance_status,
            "truthfulness_constraint_binding": result.state.truthfulness_constraint_binding,
            "strategy_lever_preferences": tuple(
                item.value for item in result.state.strategy_lever_preferences
            ),
            "justification_links": result.state.justification_links,
            "provenance": result.state.provenance,
            "no_safe_classification": result.state.no_safe_classification,
            "strategy_underconstrained": result.state.strategy_underconstrained,
            "asymmetry_present_but_not_exploitative": (
                result.state.asymmetry_present_but_not_exploitative
            ),
            "concealed_state_divergence_required": (
                result.state.concealed_state_divergence_required
            ),
            "high_local_gain_but_high_entropy": result.state.high_local_gain_but_high_entropy,
            "source_lineage": result.state.source_lineage,
            "last_update_provenance": result.state.last_update_provenance,
        },
        "gate": {
            "strategy_contract_consumer_ready": result.gate.strategy_contract_consumer_ready,
            "cooperative_selection_consumer_ready": (
                result.gate.cooperative_selection_consumer_ready
            ),
            "transparency_preserving_consumer_ready": (
                result.gate.transparency_preserving_consumer_ready
            ),
            "exploitative_move_block_required": result.gate.exploitative_move_block_required,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_hosted_only": result.scope_marker.rt01_hosted_only,
            "o03_first_slice_only": result.scope_marker.o03_first_slice_only,
            "o04_not_implemented": result.scope_marker.o04_not_implemented,
            "r05_not_implemented": result.scope_marker.r05_not_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "strategy_id": result.telemetry.strategy_id,
            "tick_index": result.telemetry.tick_index,
            "candidate_move_id": result.telemetry.candidate_move_id,
            "strategy_class": result.telemetry.strategy_class.value,
            "hidden_divergence_band": result.telemetry.hidden_divergence_band.value,
            "asymmetry_exploitation_band": result.telemetry.asymmetry_exploitation_band.value,
            "dependency_risk_band": result.telemetry.dependency_risk_band.value,
            "entropy_burden_band": result.telemetry.entropy_burden_band.value,
            "strategy_classification_confidence": (
                result.telemetry.strategy_classification_confidence
            ),
            "no_safe_classification": result.telemetry.no_safe_classification,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
