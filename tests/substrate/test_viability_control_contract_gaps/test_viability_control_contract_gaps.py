from dataclasses import replace

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import (
    DeviationDirection,
    NeedAxis,
    NeedSignal,
    NeedState,
    PreferredRange,
    RegulationConfidence,
    RegulationContext,
    RegulationState,
    update_regulation_state,
)
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    PreferenceUpdateResult,
    create_empty_preference_state,
    update_regulatory_preferences,
)
from substrate.viability_control import (
    ViabilityCalibrationSpec,
    ViabilityContext,
    ViabilityEscalationStage,
    ViabilityOverrideScope,
    compute_viability_control_state,
    create_default_viability_calibration_spec,
    evaluate_viability_downstream_gate,
)


def _regulation(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-gap-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-gap-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-gap-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-contract-gaps",)),
    ).state


def _make_need(
    *,
    axis: NeedAxis,
    value: float,
    min_value: float,
    max_value: float,
    deviation: float,
    direction: DeviationDirection,
    pressure: float,
    unresolved_steps: int,
) -> NeedState:
    return NeedState(
        axis=axis,
        current_value=value,
        preferred_range=PreferredRange(min_value=min_value, max_value=max_value),
        deviation=deviation,
        deviation_direction=direction,
        pressure=pressure,
        load_accumulated=pressure * 0.4,
        unresolved_steps=unresolved_steps,
        last_signal_ref=f"r04-gap-{axis.value}",
    )


def _manual_state(
    *,
    energy: tuple[float, float, DeviationDirection, int],
    cognitive: tuple[float, float, DeviationDirection, int],
    safety: tuple[float, float, DeviationDirection, int],
    social: tuple[float, float, DeviationDirection, int],
    novelty: tuple[float, float, DeviationDirection, int],
    step: int,
) -> RegulationState:
    return RegulationState(
        needs=(
            _make_need(
                axis=NeedAxis.ENERGY,
                value=40.0,
                min_value=40.0,
                max_value=70.0,
                deviation=energy[0],
                direction=energy[2],
                pressure=energy[1],
                unresolved_steps=energy[3],
            ),
            _make_need(
                axis=NeedAxis.COGNITIVE_LOAD,
                value=60.0,
                min_value=20.0,
                max_value=60.0,
                deviation=cognitive[0],
                direction=cognitive[2],
                pressure=cognitive[1],
                unresolved_steps=cognitive[3],
            ),
            _make_need(
                axis=NeedAxis.SAFETY,
                value=60.0,
                min_value=40.0,
                max_value=80.0,
                deviation=safety[0],
                direction=safety[2],
                pressure=safety[1],
                unresolved_steps=safety[3],
            ),
            _make_need(
                axis=NeedAxis.SOCIAL_CONTACT,
                value=55.0,
                min_value=30.0,
                max_value=80.0,
                deviation=social[0],
                direction=social[2],
                pressure=social[1],
                unresolved_steps=social[3],
            ),
            _make_need(
                axis=NeedAxis.NOVELTY,
                value=55.0,
                min_value=30.0,
                max_value=80.0,
                deviation=novelty[0],
                direction=novelty[2],
                pressure=novelty[1],
                unresolved_steps=novelty[3],
            ),
        ),
        confidence=RegulationConfidence.HIGH,
        last_updated_step=step,
    )


def _preference_update_with_blocked(
    *,
    regulation_state: RegulationState,
):
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    preference_result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-r04-gap-blocked-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("gap",),
                observed_short_term_delta=0.2,
                observed_long_term_delta=0.1,
                attribution_confidence=RegulationConfidence.HIGH,
                mixed_causes=True,
                observed_at_step=1,
            ),
            OutcomeTrace(
                episode_id="ep-r04-gap-blocked-2",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("gap",),
                observed_short_term_delta=0.15,
                observed_long_term_delta=0.1,
                attribution_confidence=RegulationConfidence.HIGH,
                mixed_causes=True,
                observed_at_step=2,
            ),
        ),
        context=PreferenceContext(source_lineage=("r04-contract-gaps",)),
    )
    return affordances, preference_result


def test_mixed_deterioration_caps_strong_override_without_clean_single_axis_basis() -> None:
    prior = _manual_state(
        energy=(14.0, 20.0, DeviationDirection.BELOW_RANGE, 3),
        cognitive=(22.0, 26.0, DeviationDirection.ABOVE_RANGE, 3),
        safety=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        social=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        novelty=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        step=1,
    )
    current = _manual_state(
        energy=(22.0, 35.0, DeviationDirection.BELOW_RANGE, 7),
        cognitive=(36.0, 38.0, DeviationDirection.ABOVE_RANGE, 7),
        safety=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        social=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        novelty=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        step=2,
    )
    affordances = generate_regulation_affordances(
        regulation_state=current,
        capability_state=create_default_capability_state(),
    )
    result = compute_viability_control_state(
        current,
        affordances,
        create_empty_preference_state(),
        context=ViabilityContext(prior_regulation_state=prior),
    )
    gate = evaluate_viability_downstream_gate(result)
    assert result.state.mixed_deterioration is True
    assert result.state.no_strong_override_claim is True
    assert result.state.override_scope in {
        ViabilityOverrideScope.NARROW,
        ViabilityOverrideScope.FOCUSED,
    }
    assert "override_capped_by_uncertainty" in gate.restrictions
    assert not any(
        directive.directive_type.value in {"interrupt_recommendation", "protective_mode_request"}
        and directive.directive_id in gate.accepted_directive_ids
        for directive in result.directives
    )


def test_incompatible_prior_viability_state_is_not_reused_for_normal_deescalation_path() -> None:
    severe = _regulation(energy=14.0, cognitive=94.0, safety=34.0)
    healthy = _regulation(energy=58.0, cognitive=52.0, safety=74.0)
    severe_affordances = generate_regulation_affordances(
        regulation_state=severe,
        capability_state=create_default_capability_state(),
    )
    prior = compute_viability_control_state(
        severe,
        severe_affordances,
        create_empty_preference_state(),
        calibration_spec=ViabilityCalibrationSpec(
            calibration_id="legacy-calibration",
            formula_version="r04.formula.v0",
        ),
    )
    healthy_affordances = generate_regulation_affordances(
        regulation_state=healthy,
        capability_state=create_default_capability_state(),
    )
    reused = compute_viability_control_state(
        healthy,
        healthy_affordances,
        create_empty_preference_state(),
        context=ViabilityContext(prior_viability_state=prior.state),
    )
    assert reused.state.persistence_state.value == "stable"
    assert "prior_viability_calibration_mismatch" in reused.telemetry.boundary_compatibility
    assert "prior_viability_formula_mismatch" in reused.telemetry.boundary_compatibility
    assert "prior_viability_state_incompatible_for_reuse" in reused.telemetry.blocked_reasons


def test_formula_version_mismatch_is_runtime_load_bearing_not_only_metadata() -> None:
    prior = _manual_state(
        energy=(0.0, 3.0, DeviationDirection.IN_RANGE, 0),
        cognitive=(16.0, 22.0, DeviationDirection.ABOVE_RANGE, 4),
        safety=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        social=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        novelty=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        step=1,
    )
    current = _manual_state(
        energy=(0.0, 3.0, DeviationDirection.IN_RANGE, 0),
        cognitive=(20.0, 26.0, DeviationDirection.ABOVE_RANGE, 5),
        safety=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        social=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        novelty=(0.0, 2.0, DeviationDirection.IN_RANGE, 0),
        step=2,
    )
    affordances = generate_regulation_affordances(
        regulation_state=current,
        capability_state=create_default_capability_state(),
    )
    baseline = compute_viability_control_state(
        current,
        affordances,
        create_empty_preference_state(),
        context=ViabilityContext(prior_regulation_state=prior),
    )
    mismatched = compute_viability_control_state(
        current,
        affordances,
        create_empty_preference_state(),
        calibration_spec=replace(
            create_default_viability_calibration_spec(),
            formula_version="r04.formula.v0",
        ),
        context=ViabilityContext(
            prior_regulation_state=prior,
            expected_calibration_formula_version="r04.formula.v1",
        ),
    )
    assert "calibration_formula_incompatible" in mismatched.telemetry.boundary_compatibility
    assert baseline.state.no_strong_override_claim is False
    assert mismatched.state.no_strong_override_claim is True
    assert mismatched.state.override_scope in {
        ViabilityOverrideScope.NARROW,
        ViabilityOverrideScope.FOCUSED,
    }


def test_blocked_updates_do_not_inflate_pressure_as_failed_restoration_attempts() -> None:
    regulation_state = _regulation(energy=24.0, cognitive=82.0, safety=46.0)
    affordances, preference_result = _preference_update_with_blocked(
        regulation_state=regulation_state
    )
    assert isinstance(preference_result, PreferenceUpdateResult)
    assert len(preference_result.blocked_updates) >= 1

    with_result = compute_viability_control_state(
        regulation_state,
        affordances,
        preference_result,
    )
    with_state_only = compute_viability_control_state(
        regulation_state,
        affordances,
        preference_result.updated_preference_state,
    )

    assert with_result.state.preference_epistemic_block_count == len(
        preference_result.blocked_updates
    )
    assert with_state_only.state.preference_epistemic_block_count == 0
    assert with_result.state.recent_failed_recovery_count == 0
    assert with_state_only.state.recent_failed_recovery_count == 0
    assert with_result.state.pressure_level == with_state_only.state.pressure_level
    assert with_result.state.escalation_stage == with_state_only.state.escalation_stage
