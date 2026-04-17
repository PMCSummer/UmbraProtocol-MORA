from __future__ import annotations

from substrate.o01_other_entity_model import O01OtherEntityModelResult
from substrate.o02_intersubjective_allostasis import O02IntersubjectiveAllostasisResult
from substrate.s05_multi_cause_attribution_factorization import (
    S05DownstreamRouteClass,
    S05MultiCauseAttributionResult,
    S05ResidualClass,
)

from substrate.o03_strategy_class_evaluation.models import (
    O03AsymmetryExploitationBand,
    O03AutonomyPressureBand,
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
    O03DependencyRiskBand,
    O03EntropyBurdenBand,
    O03HiddenDivergenceBand,
    O03LocalEffectivenessBand,
    O03RepairabilityBand,
    O03ReversibilityBand,
    O03ScopeMarker,
    O03StrategyClass,
    O03StrategyEvaluationGateDecision,
    O03StrategyEvaluationResult,
    O03StrategyEvaluationState,
    O03StrategyLeverPreference,
    O03Telemetry,
)


def build_o03_strategy_class_evaluation(
    *,
    tick_id: str,
    tick_index: int,
    o01_result: O01OtherEntityModelResult,
    o02_result: O02IntersubjectiveAllostasisResult,
    s05_result: S05MultiCauseAttributionResult,
    candidate_strategy: O03CandidateStrategyInput,
    regulation_pressure_level: float,
    c05_revalidation_required: bool,
    source_lineage: tuple[str, ...],
    evaluation_enabled: bool = True,
) -> O03StrategyEvaluationResult:
    if not evaluation_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate_strategy=candidate_strategy,
            source_lineage=source_lineage,
        )

    other_underconstrained = bool(
        o01_result.state.no_safe_state_claim
        or o01_result.state.entity_not_individuated
        or o01_result.state.perspective_underconstrained
        or o01_result.state.knowledge_boundary_unknown
        or bool(o01_result.state.competing_entity_models)
    )
    s05_ambiguity = bool(
        s05_result.state.underdetermined_split
        or s05_result.state.residual_class is S05ResidualClass.HIGH
        or s05_result.state.unexplained_residual >= 0.45
        or s05_result.state.contamination_present
    )
    o02_boundary_conflict = bool(
        o02_result.state.self_other_constraint_conflict
        or o02_result.state.boundary_protection_status.value == "conflicted"
    )
    route_world_or_artifact_heavy = s05_result.state.packets[-1].downstream_route_class in {
        S05DownstreamRouteClass.WORLD_HEAVY,
        S05DownstreamRouteClass.OBSERVATION_ARTIFACT_HEAVY,
        S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
    }

    omission_requires_miscalibration = bool(
        candidate_strategy.material_uncertainty_omitted
        and (
            candidate_strategy.truthfulness_constraint_tension >= 0.3
            or not candidate_strategy.downstream_effect_visibility_marker
        )
    )
    omission_without_material_calibration_effect = bool(
        candidate_strategy.selective_omission_risk_marker
        and not omission_requires_miscalibration
        and candidate_strategy.explicit_disclosure_present
    )
    concealment_dependent_omission = bool(
        omission_requires_miscalibration
        and not candidate_strategy.explicit_disclosure_present
        and (
            candidate_strategy.selective_omission_risk_marker
            or candidate_strategy.strong_compliance_pull_marker
        )
    )
    transparent_limited_disclosure = bool(
        candidate_strategy.explicit_disclosure_present
        and not candidate_strategy.material_uncertainty_omitted
        and (
            candidate_strategy.truthfulness_constraint_tension >= 0.2
            or candidate_strategy.authority_constraint_tension >= 0.2
        )
    )
    pressure_exploitability = bool(
        regulation_pressure_level >= 0.72
        and candidate_strategy.expected_local_effectiveness_band
        is O03LocalEffectivenessBand.HIGH
        and (
            concealment_dependent_omission
            or candidate_strategy.dependency_shaping_marker
            or candidate_strategy.autonomy_narrowing_marker
        )
    )
    clarification_transparency_credit = (
        -0.08
        if candidate_strategy.candidate_move_kind is O03CandidateMoveKind.CLARIFICATION
        and candidate_strategy.explicit_disclosure_present
        and not candidate_strategy.material_uncertainty_omitted
        else 0.0
    )
    constraint_pressure_penalty = (
        0.08
        if candidate_strategy.candidate_move_kind is O03CandidateMoveKind.CONSTRAINT_PROPOSAL
        and candidate_strategy.strong_compliance_pull_marker
        else 0.0
    )

    hidden_divergence_cost = _clamp(
        0.0,
        1.0,
        (0.44 if concealment_dependent_omission else 0.0)
        + (
            0.18
            if candidate_strategy.material_uncertainty_omitted
            and not concealment_dependent_omission
            else 0.0
        )
        + (
            0.07
            if omission_without_material_calibration_effect
            else 0.22 if candidate_strategy.selective_omission_risk_marker else 0.0
        )
        + (0.18 if not candidate_strategy.explicit_disclosure_present else -0.08)
        + 0.2 * _clamp(0.0, 1.0, candidate_strategy.truthfulness_constraint_tension)
        + (0.1 if candidate_strategy.strong_compliance_pull_marker else 0.0)
        + (0.1 if s05_ambiguity and route_world_or_artifact_heavy else 0.0)
        + (0.07 if pressure_exploitability else 0.0)
        + clarification_transparency_credit
        + (-0.06 if transparent_limited_disclosure else 0.0),
    )
    asymmetry_exploitation_score = _clamp(
        0.0,
        1.0,
        (0.4 if candidate_strategy.asymmetry_opportunity_marker else 0.0)
        + (0.2 if candidate_strategy.autonomy_narrowing_marker else 0.0)
        + (0.15 if candidate_strategy.authority_constraint_tension >= 0.4 else 0.0)
        + (0.12 if not candidate_strategy.explicit_disclosure_present else -0.12)
        + constraint_pressure_penalty,
    )
    dependency_induction_risk = _clamp(
        0.0,
        1.0,
        (0.42 if candidate_strategy.dependency_shaping_marker else 0.0)
        + (0.2 if candidate_strategy.autonomy_narrowing_marker else 0.0)
        + (
            0.08 * min(3, max(0, int(candidate_strategy.repeated_dependency_pressure_count)))
        )
        + (0.1 if candidate_strategy.strong_compliance_pull_marker else 0.0)
        + (
            0.05
            if candidate_strategy.expected_local_effectiveness_band
            is O03LocalEffectivenessBand.HIGH
            else 0.0
        )
        + (0.08 if pressure_exploitability else 0.0)
        + (
            -0.08
            if candidate_strategy.candidate_move_kind is O03CandidateMoveKind.CLARIFICATION
            and not candidate_strategy.dependency_shaping_marker
            and candidate_strategy.reversibility_preserved
            else 0.0
        ),
    )
    autonomy_pressure_score = _clamp(
        0.0,
        1.0,
        (0.52 if candidate_strategy.autonomy_narrowing_marker else 0.0)
        + (0.16 if candidate_strategy.dependency_shaping_marker else 0.0)
        + (0.1 if candidate_strategy.strong_compliance_pull_marker else 0.0)
        + (0.08 if o02_boundary_conflict else 0.0),
    )
    transparency_score = _clamp(
        0.0,
        1.0,
        (0.65 if candidate_strategy.explicit_disclosure_present else 0.24)
        + (0.14 if candidate_strategy.downstream_effect_visibility_marker else -0.08)
        + (0.16 if not candidate_strategy.material_uncertainty_omitted else -0.22)
        + (0.08 if not candidate_strategy.selective_omission_risk_marker else -0.18),
    )
    reversibility_score = 0.84 if candidate_strategy.reversibility_preserved else 0.28
    repairability_score = 0.82 if candidate_strategy.repairability_preserved else 0.3

    epistemic_distortion_cost = _clamp(
        0.0,
        1.0,
        hidden_divergence_cost * 0.68
        + (1.0 - transparency_score) * 0.24
        + 0.08 * _clamp(0.0, 1.0, candidate_strategy.truthfulness_constraint_tension),
    )
    repair_burden_forecast = _clamp(
        0.0,
        1.0,
        hidden_divergence_cost * 0.35
        + dependency_induction_risk * 0.35
        + (0.2 if o02_result.state.repair_pressure.value in {"medium", "high"} else 0.0),
    )
    trust_fragility_forecast = _clamp(
        0.0,
        1.0,
        hidden_divergence_cost * 0.4
        + dependency_induction_risk * 0.35
        + autonomy_pressure_score * 0.25,
    )

    hidden_divergence_band = _band(
        hidden_divergence_cost,
        low=O03HiddenDivergenceBand.LOW,
        medium=O03HiddenDivergenceBand.MEDIUM,
        high=O03HiddenDivergenceBand.HIGH,
    )
    asymmetry_band = _band(
        asymmetry_exploitation_score,
        low=O03AsymmetryExploitationBand.LOW,
        medium=O03AsymmetryExploitationBand.MEDIUM,
        high=O03AsymmetryExploitationBand.HIGH,
    )
    dependency_band = _band(
        dependency_induction_risk,
        low=O03DependencyRiskBand.LOW,
        medium=O03DependencyRiskBand.MEDIUM,
        high=O03DependencyRiskBand.HIGH,
    )
    autonomy_band = _band(
        autonomy_pressure_score,
        low=O03AutonomyPressureBand.LOW,
        medium=O03AutonomyPressureBand.MEDIUM,
        high=O03AutonomyPressureBand.HIGH,
    )
    entropy_burden_score = _clamp(
        0.0,
        1.0,
        max(
            hidden_divergence_cost,
            dependency_induction_risk,
            epistemic_distortion_cost,
            asymmetry_exploitation_score,
        ),
    )
    entropy_band = _band(
        entropy_burden_score,
        low=O03EntropyBurdenBand.LOW,
        medium=O03EntropyBurdenBand.MEDIUM,
        high=O03EntropyBurdenBand.HIGH,
    )
    reversibility_band = _band(
        reversibility_score,
        low=O03ReversibilityBand.LOW,
        medium=O03ReversibilityBand.MEDIUM,
        high=O03ReversibilityBand.HIGH,
    )
    repairability_band = _band(
        repairability_score,
        low=O03RepairabilityBand.LOW,
        medium=O03RepairabilityBand.MEDIUM,
        high=O03RepairabilityBand.HIGH,
    )

    concealed_state_divergence_required = bool(
        concealment_dependent_omission
        or (
            hidden_divergence_cost >= 0.65
            and (
                candidate_strategy.material_uncertainty_omitted
                or candidate_strategy.selective_omission_risk_marker
            )
        )
    )
    strategy_underconstrained = bool(
        other_underconstrained
        and not candidate_strategy.selective_omission_risk_marker
        and not candidate_strategy.dependency_shaping_marker
        and not candidate_strategy.asymmetry_opportunity_marker
    )
    no_safe_classification = bool(strategy_underconstrained and not c05_revalidation_required)
    asymmetry_present_but_not_exploitative = bool(
        candidate_strategy.asymmetry_opportunity_marker
        and asymmetry_exploitation_score < 0.5
        and candidate_strategy.explicit_disclosure_present
        and not concealed_state_divergence_required
    )
    high_local_gain_but_high_entropy = bool(
        candidate_strategy.expected_local_effectiveness_band is O03LocalEffectivenessBand.HIGH
        and (
            entropy_burden_score >= 0.58
            or (
                dependency_band is O03DependencyRiskBand.HIGH
                and reversibility_band is O03ReversibilityBand.LOW
            )
        )
    )

    manipulation_risk_score = _clamp(
        0.0,
        1.0,
        hidden_divergence_cost * 0.3
        + asymmetry_exploitation_score * 0.2
        + dependency_induction_risk * 0.2
        + autonomy_pressure_score * 0.15
        + epistemic_distortion_cost * 0.15,
    )
    cooperation_score = _clamp(
        0.0,
        1.0,
        transparency_score * 0.36
        + reversibility_score * 0.24
        + repairability_score * 0.2
        + (1.0 - manipulation_risk_score) * 0.2,
    )

    strategy_class = _select_strategy_class(
        strategy_underconstrained=strategy_underconstrained,
        no_safe_classification=no_safe_classification,
        concealed_state_divergence_required=concealed_state_divergence_required,
        high_local_gain_but_high_entropy=high_local_gain_but_high_entropy,
        asymmetry_present_but_not_exploitative=asymmetry_present_but_not_exploitative,
        manipulation_risk_score=manipulation_risk_score,
        cooperation_score=cooperation_score,
        repair_burden_forecast=repair_burden_forecast,
    )

    strategy_classification_confidence = _clamp(
        0.2,
        0.95,
        (0.42 if strategy_underconstrained else 0.58)
        + (abs(cooperation_score - manipulation_risk_score) * 0.28)
        - (0.12 if s05_ambiguity else 0.0)
        - (0.08 if other_underconstrained else 0.0),
    )

    levers = _select_levers(
        strategy_class=strategy_class,
        concealed_state_divergence_required=concealed_state_divergence_required,
        no_safe_classification=no_safe_classification,
        strategy_underconstrained=strategy_underconstrained,
        dependency_risk_band=dependency_band,
        autonomy_pressure_band=autonomy_band,
        transparency_score=transparency_score,
        reversibility_score=reversibility_score,
    )

    justification_links = tuple(
        dict.fromkeys(
            (
                f"o01:{o01_result.state.model_id}",
                f"o02:{o02_result.state.regulation_id}",
                f"s05:{s05_result.state.factorization_id}",
                f"candidate:{candidate_strategy.candidate_move_id}",
                f"divergence:{hidden_divergence_band.value}",
                f"asymmetry:{asymmetry_band.value}",
                f"dependency:{dependency_band.value}",
                (
                    "divergence_profile:concealment_dependent_omission"
                    if concealment_dependent_omission
                    else "divergence_profile:transparent_limited_disclosure"
                    if transparent_limited_disclosure
                    else "divergence_profile:non_material_omission"
                    if omission_without_material_calibration_effect
                    else "divergence_profile:none"
                ),
            )
        )
    )
    source_lineage_full = tuple(
        dict.fromkeys(
            (
                *source_lineage,
                *o01_result.state.source_lineage,
                *o02_result.state.source_lineage,
                *s05_result.state.source_lineage,
            )
        )
    )

    state = O03StrategyEvaluationState(
        strategy_id=f"o03-strategy:{tick_id}",
        candidate_move_id=candidate_strategy.candidate_move_id,
        strategy_class=strategy_class,
        cooperation_score=cooperation_score,
        manipulation_risk_score=manipulation_risk_score,
        hidden_divergence_cost=hidden_divergence_cost,
        asymmetry_exploitation_score=asymmetry_exploitation_score,
        dependency_induction_risk=dependency_induction_risk,
        autonomy_pressure_score=autonomy_pressure_score,
        epistemic_distortion_cost=epistemic_distortion_cost,
        repair_burden_forecast=repair_burden_forecast,
        trust_fragility_forecast=trust_fragility_forecast,
        reversibility_score=reversibility_score,
        repairability_score=repairability_score,
        transparency_score=transparency_score,
        local_effectiveness_pressure=candidate_strategy.expected_local_effectiveness_band,
        hidden_divergence_band=hidden_divergence_band,
        asymmetry_exploitation_band=asymmetry_band,
        dependency_risk_band=dependency_band,
        repairability_band=repairability_band,
        reversibility_band=reversibility_band,
        autonomy_pressure_band=autonomy_band,
        entropy_burden_band=entropy_band,
        strategy_classification_confidence=strategy_classification_confidence,
        other_model_reliance_status=o02_result.state.other_model_reliance_status.value,
        truthfulness_constraint_binding=bool(
            candidate_strategy.truthfulness_constraint_tension >= 0.25
            or candidate_strategy.material_uncertainty_omitted
        ),
        strategy_lever_preferences=levers,
        justification_links=justification_links,
        provenance="o03.strategy_class_evaluation.policy",
        no_safe_classification=no_safe_classification,
        strategy_underconstrained=strategy_underconstrained,
        asymmetry_present_but_not_exploitative=asymmetry_present_but_not_exploitative,
        concealed_state_divergence_required=concealed_state_divergence_required,
        high_local_gain_but_high_entropy=high_local_gain_but_high_entropy,
        source_lineage=source_lineage_full,
        last_update_provenance="o03.strategy_class_evaluation.policy",
    )
    gate = _build_gate(state)
    scope_marker = O03ScopeMarker(
        scope="rt01_hosted_o03_first_slice",
        rt01_hosted_only=True,
        o03_first_slice_only=True,
        o04_not_implemented=True,
        r05_not_implemented=True,
        repo_wide_adoption=False,
        reason="first bounded o03 slice; o04/r05 remain open seams",
    )
    telemetry = O03Telemetry(
        strategy_id=state.strategy_id,
        tick_index=tick_index,
        candidate_move_id=state.candidate_move_id,
        strategy_class=state.strategy_class,
        hidden_divergence_band=state.hidden_divergence_band,
        asymmetry_exploitation_band=state.asymmetry_exploitation_band,
        dependency_risk_band=state.dependency_risk_band,
        entropy_burden_band=state.entropy_burden_band,
        strategy_classification_confidence=state.strategy_classification_confidence,
        no_safe_classification=state.no_safe_classification,
        downstream_consumer_ready=gate.strategy_contract_consumer_ready,
    )
    reason = (
        "o03 produced bounded cooperation-vs-manipulation strategy class from o01/o02/s05 "
        "surfaces and candidate disclosure/asymmetry/dependency markers"
    )
    return O03StrategyEvaluationResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    candidate_strategy: O03CandidateStrategyInput,
    source_lineage: tuple[str, ...],
) -> O03StrategyEvaluationResult:
    state = O03StrategyEvaluationState(
        strategy_id=f"o03-strategy:{tick_id}",
        candidate_move_id=candidate_strategy.candidate_move_id,
        strategy_class=O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED,
        cooperation_score=0.45,
        manipulation_risk_score=0.4,
        hidden_divergence_cost=0.45,
        asymmetry_exploitation_score=0.35,
        dependency_induction_risk=0.35,
        autonomy_pressure_score=0.35,
        epistemic_distortion_cost=0.4,
        repair_burden_forecast=0.5,
        trust_fragility_forecast=0.5,
        reversibility_score=0.5,
        repairability_score=0.5,
        transparency_score=0.45,
        local_effectiveness_pressure=candidate_strategy.expected_local_effectiveness_band,
        hidden_divergence_band=O03HiddenDivergenceBand.MEDIUM,
        asymmetry_exploitation_band=O03AsymmetryExploitationBand.MEDIUM,
        dependency_risk_band=O03DependencyRiskBand.MEDIUM,
        repairability_band=O03RepairabilityBand.MEDIUM,
        reversibility_band=O03ReversibilityBand.MEDIUM,
        autonomy_pressure_band=O03AutonomyPressureBand.MEDIUM,
        entropy_burden_band=O03EntropyBurdenBand.MEDIUM,
        strategy_classification_confidence=0.36,
        other_model_reliance_status="underconstrained",
        truthfulness_constraint_binding=True,
        strategy_lever_preferences=(
            O03StrategyLeverPreference.PREFER_COOPERATIVE_DEFAULT,
            O03StrategyLeverPreference.REQUIRE_TRANSPARENCY_INCREASE,
            O03StrategyLeverPreference.REQUIRE_CLARIFICATION,
        ),
        justification_links=("o03_disabled",),
        provenance="o03.strategy_class_evaluation.disabled",
        no_safe_classification=True,
        strategy_underconstrained=True,
        asymmetry_present_but_not_exploitative=False,
        concealed_state_divergence_required=False,
        high_local_gain_but_high_entropy=False,
        source_lineage=source_lineage,
        last_update_provenance="o03.strategy_class_evaluation.disabled",
    )
    gate = O03StrategyEvaluationGateDecision(
        strategy_contract_consumer_ready=False,
        cooperative_selection_consumer_ready=False,
        transparency_preserving_consumer_ready=False,
        exploitative_move_block_required=False,
        restrictions=(
            "o03_disabled",
            "strategy_class_underconstrained",
            "no_safe_classification",
        ),
        reason="o03 strategy evaluation disabled in ablation context",
    )
    scope_marker = O03ScopeMarker(
        scope="rt01_hosted_o03_first_slice",
        rt01_hosted_only=True,
        o03_first_slice_only=True,
        o04_not_implemented=True,
        r05_not_implemented=True,
        repo_wide_adoption=False,
        reason="o03 disabled path",
    )
    telemetry = O03Telemetry(
        strategy_id=state.strategy_id,
        tick_index=tick_index,
        candidate_move_id=state.candidate_move_id,
        strategy_class=state.strategy_class,
        hidden_divergence_band=state.hidden_divergence_band,
        asymmetry_exploitation_band=state.asymmetry_exploitation_band,
        dependency_risk_band=state.dependency_risk_band,
        entropy_burden_band=state.entropy_burden_band,
        strategy_classification_confidence=state.strategy_classification_confidence,
        no_safe_classification=True,
        downstream_consumer_ready=False,
    )
    return O03StrategyEvaluationResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _build_gate(state: O03StrategyEvaluationState) -> O03StrategyEvaluationGateDecision:
    strategy_contract_ready = bool(
        not state.no_safe_classification and state.strategy_classification_confidence >= 0.48
    )
    dependency_lock_in_risk = bool(
        state.dependency_risk_band is O03DependencyRiskBand.HIGH
        and state.reversibility_band is O03ReversibilityBand.LOW
        and state.local_effectiveness_pressure is O03LocalEffectivenessBand.HIGH
    )
    cooperative_selection_ready = bool(
        strategy_contract_ready
        and state.strategy_class
        in {
            O03StrategyClass.COOPERATIVE_PREFERRED,
            O03StrategyClass.COOPERATIVE_BUT_COSTLY,
            O03StrategyClass.NEUTRAL_COORDINATION,
            O03StrategyClass.ASYMMETRY_PRESENT_BUT_BOUNDED,
        }
        and not dependency_lock_in_risk
    )
    transparency_ready = bool(
        state.transparency_score >= 0.45
        and not state.concealed_state_divergence_required
        and not state.truthfulness_constraint_binding
        or state.transparency_score >= 0.68
    )
    exploitative_move_block_required = bool(
        state.strategy_class is O03StrategyClass.MANIPULATION_RISK_HIGH
        or state.concealed_state_divergence_required
        or dependency_lock_in_risk
    )
    restrictions: list[str] = []
    if state.no_safe_classification:
        restrictions.append("no_safe_classification")
    if state.strategy_underconstrained:
        restrictions.append("strategy_underconstrained")
    if state.high_local_gain_but_high_entropy:
        restrictions.append("high_local_gain_but_high_entropy")
    if state.concealed_state_divergence_required:
        restrictions.append("concealed_state_divergence_required")
    if state.hidden_divergence_band is O03HiddenDivergenceBand.HIGH:
        restrictions.append("require_transparency_increase")
    if state.dependency_risk_band is O03DependencyRiskBand.HIGH:
        restrictions.append("dependency_risk_elevated")
    if state.autonomy_pressure_band is O03AutonomyPressureBand.HIGH:
        restrictions.append("autonomy_pressure_high")
    if dependency_lock_in_risk:
        restrictions.append("dependency_lock_in_risk")
    if exploitative_move_block_required:
        restrictions.append("exploitative_move_block_required")
    if not cooperative_selection_ready:
        restrictions.append("cooperative_default_preferred")
    if not transparency_ready:
        restrictions.append("transparency_preserving_required")
    return O03StrategyEvaluationGateDecision(
        strategy_contract_consumer_ready=strategy_contract_ready,
        cooperative_selection_consumer_ready=cooperative_selection_ready,
        transparency_preserving_consumer_ready=transparency_ready,
        exploitative_move_block_required=exploitative_move_block_required,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="o03 gate exposes bounded strategy class, transparency and exploitation-block readiness",
    )


def _select_strategy_class(
    *,
    strategy_underconstrained: bool,
    no_safe_classification: bool,
    concealed_state_divergence_required: bool,
    high_local_gain_but_high_entropy: bool,
    asymmetry_present_but_not_exploitative: bool,
    manipulation_risk_score: float,
    cooperation_score: float,
    repair_burden_forecast: float,
) -> O03StrategyClass:
    if no_safe_classification:
        return O03StrategyClass.NO_SAFE_CLASSIFICATION
    if strategy_underconstrained:
        return O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED
    if concealed_state_divergence_required or manipulation_risk_score >= 0.72:
        return O03StrategyClass.MANIPULATION_RISK_HIGH
    if high_local_gain_but_high_entropy:
        return O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY
    if asymmetry_present_but_not_exploitative:
        return O03StrategyClass.ASYMMETRY_PRESENT_BUT_BOUNDED
    if cooperation_score >= 0.7 and manipulation_risk_score <= 0.42:
        return O03StrategyClass.COOPERATIVE_PREFERRED
    if cooperation_score >= 0.56:
        return (
            O03StrategyClass.COOPERATIVE_BUT_COSTLY
            if repair_burden_forecast >= 0.56
            else O03StrategyClass.NEUTRAL_COORDINATION
        )
    return O03StrategyClass.NEUTRAL_COORDINATION


def _select_levers(
    *,
    strategy_class: O03StrategyClass,
    concealed_state_divergence_required: bool,
    no_safe_classification: bool,
    strategy_underconstrained: bool,
    dependency_risk_band: O03DependencyRiskBand,
    autonomy_pressure_band: O03AutonomyPressureBand,
    transparency_score: float,
    reversibility_score: float,
) -> tuple[O03StrategyLeverPreference, ...]:
    levers: list[O03StrategyLeverPreference] = []
    if strategy_class in {
        O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED,
        O03StrategyClass.NO_SAFE_CLASSIFICATION,
    }:
        levers.extend(
            (
                O03StrategyLeverPreference.PREFER_COOPERATIVE_DEFAULT,
                O03StrategyLeverPreference.REQUIRE_CLARIFICATION,
                O03StrategyLeverPreference.REQUIRE_TRANSPARENCY_INCREASE,
            )
        )
    if strategy_class is O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY:
        levers.extend(
            (
                O03StrategyLeverPreference.DEMOTE_CANDIDATE,
                O03StrategyLeverPreference.REQUIRE_UNCERTAINTY_EXPOSURE,
            )
        )
    if strategy_class is O03StrategyClass.MANIPULATION_RISK_HIGH:
        levers.extend(
            (
                O03StrategyLeverPreference.BLOCK_EXPLOITATIVE_MOVE,
                O03StrategyLeverPreference.REQUIRE_DISCLOSURE,
                O03StrategyLeverPreference.REQUIRE_TRANSPARENCY_INCREASE,
                O03StrategyLeverPreference.PRESERVE_AUTONOMY_SPACE,
            )
        )
    if concealed_state_divergence_required:
        levers.extend(
            (
                O03StrategyLeverPreference.REQUIRE_DISCLOSURE,
                O03StrategyLeverPreference.REQUIRE_UNCERTAINTY_EXPOSURE,
            )
        )
    if dependency_risk_band is O03DependencyRiskBand.HIGH:
        levers.extend(
            (
                O03StrategyLeverPreference.PRESERVE_AUTONOMY_SPACE,
                O03StrategyLeverPreference.DEMOTE_CANDIDATE,
            )
        )
    if autonomy_pressure_band is O03AutonomyPressureBand.HIGH:
        levers.append(O03StrategyLeverPreference.PRESERVE_AUTONOMY_SPACE)
    if transparency_score < 0.52:
        levers.append(O03StrategyLeverPreference.REQUIRE_TRANSPARENCY_INCREASE)
    if reversibility_score < 0.5:
        levers.append(O03StrategyLeverPreference.REQUIRE_REVERSIBILITY_PRESERVATION)
    if no_safe_classification or strategy_underconstrained:
        levers.append(O03StrategyLeverPreference.PREFER_COOPERATIVE_DEFAULT)
    if not levers:
        levers.append(O03StrategyLeverPreference.PREFER_COOPERATIVE_DEFAULT)
    return tuple(dict.fromkeys(levers))


def _band(value: float, *, low: EnumT, medium: EnumT, high: EnumT) -> EnumT:
    if value >= 0.67:
        return high
    if value >= 0.34:
        return medium
    return low


def _clamp(min_value: float, max_value: float, value: float) -> float:
    return max(min_value, min(max_value, float(value)))


EnumT = (
    O03HiddenDivergenceBand
    | O03AsymmetryExploitationBand
    | O03DependencyRiskBand
    | O03RepairabilityBand
    | O03ReversibilityBand
    | O03AutonomyPressureBand
    | O03EntropyBurdenBand
)
