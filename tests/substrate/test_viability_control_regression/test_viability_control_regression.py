from dataclasses import replace

from substrate.affordances import (
    CapabilitySpec,
    CapabilityState,
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    update_regulatory_preferences,
)
from substrate.viability_control import (
    ViabilityContext,
    ViabilityUncertaintyState,
    compute_viability_control_state,
    create_default_viability_boundary_spec,
)


def _regulation(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-reg-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-reg-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-reg-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-regression",)),
    ).state


def _preference(regulation_state, affordances, *, short_delta: float, long_delta: float):
    candidate = affordances.candidates[0]
    return update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id=f"ep-r04-reg-{short_delta}-{long_delta}",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("regression",),
                observed_short_term_delta=short_delta,
                observed_long_term_delta=long_delta,
                attribution_confidence=regulation_state.confidence,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=("r04-regression",)),
    ).updated_preference_state


def test_same_deficit_different_worsening_regression_case() -> None:
    current = _regulation(energy=19.0, cognitive=90.0, safety=40.0)
    prior_low = _regulation(energy=21.0, cognitive=87.0, safety=43.0)
    prior_high = _regulation(energy=47.0, cognitive=62.0, safety=70.0)
    affordances = generate_regulation_affordances(
        regulation_state=current,
        capability_state=create_default_capability_state(),
    )
    prefs = _preference(current, affordances, short_delta=0.3, long_delta=0.2)
    low = compute_viability_control_state(
        current,
        affordances,
        prefs,
        context=ViabilityContext(prior_regulation_state=prior_low),
    )
    high = compute_viability_control_state(
        current,
        affordances,
        prefs,
        context=ViabilityContext(prior_regulation_state=prior_high),
    )
    assert high.state.pressure_level >= low.state.pressure_level


def test_high_preference_low_threat_regression_case_stays_noncritical() -> None:
    low_threat = _regulation(energy=56.0, cognitive=54.0, safety=74.0)
    affordances = generate_regulation_affordances(
        regulation_state=low_threat,
        capability_state=create_default_capability_state(),
    )
    strong_positive_pref = _preference(low_threat, affordances, short_delta=0.95, long_delta=0.95)
    result = compute_viability_control_state(low_threat, affordances, strong_positive_pref)
    assert result.state.escalation_stage.value in {"baseline", "elevated"}


def test_high_threat_poor_recoverability_with_weak_means_preference_regression_case() -> None:
    high_threat = _regulation(energy=14.0, cognitive=94.0, safety=34.0)
    base_caps = create_default_capability_state()
    disabled_caps = CapabilityState(
        capabilities=tuple(
            CapabilitySpec(
                option_class=spec.option_class,
                enabled=False,
                max_intensity=spec.max_intensity,
                cooldown_steps_remaining=spec.cooldown_steps_remaining,
                risk_multiplier=spec.risk_multiplier,
                source_ref=spec.source_ref,
            )
            for spec in base_caps.capabilities
        ),
        confidence=base_caps.confidence,
    )
    affordances = generate_regulation_affordances(
        regulation_state=high_threat,
        capability_state=disabled_caps,
    )
    weak_pref = _preference(high_threat, affordances, short_delta=-0.2, long_delta=-0.1)
    result = compute_viability_control_state(high_threat, affordances, weak_pref)
    markers = set(result.state.uncertainty_state)
    assert ViabilityUncertaintyState.DEGRADED_MODE_ONLY in markers
    assert result.state.recoverability_estimate is None


def test_noisy_fluctuations_without_boundary_approach_do_not_overescalate() -> None:
    a = _regulation(energy=49.0, cognitive=61.0, safety=59.0)
    b = _regulation(energy=51.0, cognitive=60.0, safety=61.0)
    affordances_a = generate_regulation_affordances(
        regulation_state=a,
        capability_state=create_default_capability_state(),
    )
    prefs_a = _preference(a, affordances_a, short_delta=0.1, long_delta=0.1)
    result_a = compute_viability_control_state(a, affordances_a, prefs_a)

    affordances_b = generate_regulation_affordances(
        regulation_state=b,
        capability_state=create_default_capability_state(),
    )
    prefs_b = _preference(b, affordances_b, short_delta=0.1, long_delta=0.1)
    result_b = compute_viability_control_state(b, affordances_b, prefs_b)
    assert result_a.state.escalation_stage.value != "critical"
    assert result_b.state.escalation_stage.value != "critical"


def test_incompatible_boundary_schema_is_not_silently_ignored() -> None:
    regulation = _regulation(energy=18.0, cognitive=89.0, safety=42.0)
    affordances = generate_regulation_affordances(
        regulation_state=regulation,
        capability_state=create_default_capability_state(),
    )
    prefs = _preference(regulation, affordances, short_delta=0.4, long_delta=0.25)
    incompatible_boundary = replace(
        create_default_viability_boundary_spec(),
        schema_version="r04.boundary.v0",
    )
    result = compute_viability_control_state(
        regulation,
        affordances,
        prefs,
        boundary_spec=incompatible_boundary,
    )
    assert "boundary_schema_incompatible" in result.telemetry.boundary_compatibility
    assert result.state.no_strong_override_claim is True
