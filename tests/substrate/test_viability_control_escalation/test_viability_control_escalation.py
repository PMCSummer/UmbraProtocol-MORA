from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import ViabilityContext, compute_viability_control_state


def _regulation_state(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-esc-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-esc-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-esc-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-escalation",)),
    ).state


def test_same_current_deficit_diff_worsening_gives_distinct_escalation_interpretation() -> None:
    current = _regulation_state(energy=20.0, cognitive=90.0, safety=42.0)
    prior_stable = _regulation_state(energy=22.0, cognitive=88.0, safety=44.0)
    prior_worsening = _regulation_state(energy=48.0, cognitive=60.0, safety=75.0)

    affordances = generate_regulation_affordances(
        regulation_state=current,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()

    stable_result = compute_viability_control_state(
        current,
        affordances,
        preferences,
        context=ViabilityContext(
            prior_regulation_state=prior_stable,
            source_lineage=("r04-escalation-stable",),
        ),
    )
    worsening_result = compute_viability_control_state(
        current,
        affordances,
        preferences,
        context=ViabilityContext(
            prior_regulation_state=prior_worsening,
            source_lineage=("r04-escalation-worsening",),
        ),
    )

    assert worsening_result.state.pressure_level >= stable_result.state.pressure_level
    assert worsening_result.state.predicted_time_to_boundary is not None
    if stable_result.state.predicted_time_to_boundary is not None:
        assert worsening_result.state.predicted_time_to_boundary <= stable_result.state.predicted_time_to_boundary
    assert worsening_result.state.escalation_stage.value in {"threat", "critical"}
