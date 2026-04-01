from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state


def _state_energy_cognitive():
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref="energy-low"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=88.0, source_ref="cog-high"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state


def _state_safety_social():
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.SAFETY, value=35.0, source_ref="safety-low"),
            NeedSignal(axis=NeedAxis.SOCIAL_CONTACT, value=20.0, source_ref="social-low"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state


def test_contrast_same_pressure_band_different_need_configuration_changes_landscape() -> None:
    state_a = _state_energy_cognitive()
    state_b = _state_safety_social()
    total_pressure_a = sum(need.pressure for need in state_a.needs)
    total_pressure_b = sum(need.pressure for need in state_b.needs)
    assert abs(total_pressure_a - total_pressure_b) < 25.0

    result_a = generate_regulation_affordances(
        regulation_state=state_a,
        capability_state=create_default_capability_state(),
    )
    result_b = generate_regulation_affordances(
        regulation_state=state_b,
        capability_state=create_default_capability_state(),
    )

    options_a = {candidate.option_class for candidate in result_a.candidates}
    options_b = {candidate.option_class for candidate in result_b.candidates}
    assert options_a != options_b
    assert result_a.gate.bias_hints != result_b.gate.bias_hints
