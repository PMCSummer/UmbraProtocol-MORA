from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state


def test_competing_needs_remain_structured_and_tradeoff_is_explicit() -> None:
    result = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=15.0, source_ref="energy-low"),
            NeedSignal(axis=NeedAxis.NOVELTY, value=90.0, source_ref="novelty-high"),
            NeedSignal(axis=NeedAxis.SAFETY, value=40.0, source_ref="safety-low"),
        ),
        prior_state=None,
        context=RegulationContext(),
    )

    assert len(result.state.needs) == 5
    assert len({need.axis for need in result.state.needs}) == 5
    assert result.tradeoff.active_axes
    assert len(result.tradeoff.active_axes) >= 2
    assert result.tradeoff.competing_pairs
    assert result.tradeoff.dominant_axis is not None
    assert result.tradeoff.suppressed_axes


def test_no_single_stress_scalar_replaces_structured_pressures() -> None:
    result = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=85.0, source_ref="cog-high"),
            NeedSignal(axis=NeedAxis.SAFETY, value=35.0, source_ref="safety-low"),
        ),
        prior_state=None,
        context=RegulationContext(),
    )

    urgency_axes = {axis for axis, _ in result.bias.urgency_by_axis}
    assert urgency_axes == {need.axis for need in result.state.needs}
    assert not hasattr(result.state, "stress")
