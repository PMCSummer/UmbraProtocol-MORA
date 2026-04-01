from substrate.regulation import (
    DeviationDirection,
    NeedAxis,
    NeedSignal,
    RegulationContext,
    RegulationResult,
    regulation_result_to_payload,
    update_regulation_state,
)


def test_one_step_regulation_update_produces_typed_result_and_telemetry() -> None:
    signals = (
        NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="epu-energy"),
        NeedSignal(axis=NeedAxis.SAFETY, value=35.0, source_ref="epu-safety"),
        NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=80.0, source_ref="epu-cog"),
    )
    result = update_regulation_state(signals, prior_state=None, context=RegulationContext())

    assert isinstance(result, RegulationResult)
    energy = next(need for need in result.state.needs if need.axis == NeedAxis.ENERGY)
    safety = next(need for need in result.state.needs if need.axis == NeedAxis.SAFETY)
    cognitive = next(
        need for need in result.state.needs if need.axis == NeedAxis.COGNITIVE_LOAD
    )
    assert energy.deviation > 0.0
    assert safety.deviation > 0.0
    assert cognitive.deviation > 0.0
    assert energy.deviation_direction == DeviationDirection.BELOW_RANGE
    assert cognitive.deviation_direction == DeviationDirection.ABOVE_RANGE
    assert result.telemetry.deviations
    assert result.telemetry.used_preferred_ranges
    assert result.telemetry.attempted_paths
    assert result.bias.urgency_by_axis


def test_regulation_snapshot_payload_preserves_structured_mechanism_state() -> None:
    result = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=25.0, source_ref="energy-signal"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=82.0, source_ref="cog-signal"),
        ),
        prior_state=None,
        context=RegulationContext(),
    )
    payload = regulation_result_to_payload(result)

    assert "needs" in payload
    assert "stress" not in payload
    assert set(payload["needs"].keys()) == {
        "energy",
        "cognitive_load",
        "safety",
        "social_contact",
        "novelty",
    }
    assert payload["needs"]["energy"]["deviation"] > 0.0
