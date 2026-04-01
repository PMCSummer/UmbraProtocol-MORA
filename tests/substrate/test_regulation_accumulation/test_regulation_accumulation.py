from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state


def test_unresolved_deficit_accumulates_over_steps() -> None:
    context = RegulationContext(step_delta=1)
    step1 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=15.0, source_ref="e1"),),
        prior_state=None,
        context=context,
    )
    step2 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=15.0, source_ref="e2"),),
        prior_state=step1.state,
        context=context,
    )
    step3 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=15.0, source_ref="e3"),),
        prior_state=step2.state,
        context=context,
    )

    energy1 = next(need for need in step1.state.needs if need.axis == NeedAxis.ENERGY)
    energy3 = next(need for need in step3.state.needs if need.axis == NeedAxis.ENERGY)
    assert energy3.pressure > energy1.pressure
    assert energy3.load_accumulated > energy1.load_accumulated
    assert energy3.unresolved_steps > energy1.unresolved_steps


def test_recovery_reduces_pressure_without_magic_reset() -> None:
    stressed = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=10.0, source_ref="e-low"),),
        prior_state=None,
        context=RegulationContext(step_delta=1),
    )
    stressed_more = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=10.0, source_ref="e-low-2"),),
        prior_state=stressed.state,
        context=RegulationContext(step_delta=1),
    )
    recovery = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=55.0, source_ref="e-recovery"),),
        prior_state=stressed_more.state,
        context=RegulationContext(step_delta=1),
    )

    pressure_before = next(
        need.pressure for need in stressed_more.state.needs if need.axis == NeedAxis.ENERGY
    )
    pressure_after = next(
        need.pressure for need in recovery.state.needs if need.axis == NeedAxis.ENERGY
    )
    load_after = next(
        need.load_accumulated for need in recovery.state.needs if need.axis == NeedAxis.ENERGY
    )
    assert pressure_after < pressure_before
    assert pressure_after > 0.0
    assert load_after > 0.0
