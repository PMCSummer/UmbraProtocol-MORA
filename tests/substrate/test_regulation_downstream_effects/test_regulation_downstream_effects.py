from substrate.regulation import (
    NeedAxis,
    NeedSignal,
    RegulationConfidence,
    RegulationContext,
    RegulationState,
    evaluate_downstream_regulation_gate,
    update_regulation_state,
)


def _energy_urgency(state: RegulationState, result) -> float:
    for axis, urgency in result.bias.urgency_by_axis:
        if axis == NeedAxis.ENERGY:
            return urgency
    raise AssertionError("energy urgency not found")


def test_same_external_input_diff_prior_state_changes_downstream_bias() -> None:
    external_signals = (
        NeedSignal(axis=NeedAxis.SAFETY, value=70.0, source_ref="safe-signal"),
    )
    neutral = update_regulation_state(
        external_signals,
        prior_state=None,
        context=RegulationContext(),
    )

    stressed_1 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=10.0, source_ref="low-energy-1"),),
        prior_state=None,
        context=RegulationContext(),
    )
    stressed_2 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.ENERGY, value=10.0, source_ref="low-energy-2"),),
        prior_state=stressed_1.state,
        context=RegulationContext(),
    )
    stressed_with_same_external = update_regulation_state(
        external_signals,
        prior_state=stressed_2.state,
        context=RegulationContext(),
    )

    assert neutral.bias.coping_mode != stressed_with_same_external.bias.coping_mode
    assert _energy_urgency(neutral.state, neutral) < _energy_urgency(
        stressed_with_same_external.state, stressed_with_same_external
    )


def test_growing_deficit_changes_downstream_urgency_surface() -> None:
    step1 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref="c1"),),
        prior_state=None,
        context=RegulationContext(),
    )
    step2 = update_regulation_state(
        (NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref="c2"),),
        prior_state=step1.state,
        context=RegulationContext(),
    )

    urgency1 = dict(step1.bias.urgency_by_axis)[NeedAxis.COGNITIVE_LOAD]
    urgency2 = dict(step2.bias.urgency_by_axis)[NeedAxis.COGNITIVE_LOAD]
    assert urgency2 > urgency1


def test_honest_uncertainty_partial_known_and_abstain_on_bad_signals() -> None:
    result = update_regulation_state(
        signals=(),
        prior_state=None,
        context=RegulationContext(require_strong_claim=True),
    )

    assert result.state.partial_known is not None
    assert result.state.abstention is not None
    assert result.state.confidence.value == "low"
    assert "abstain" in result.bias.restrictions
    assert "low_confidence" in result.bias.restrictions


def test_boundary_non_overreach_no_semantics_intent_or_action_policy() -> None:
    result = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=30.0, source_ref="energy-boundary"),
        ),
        prior_state=None,
        context=RegulationContext(),
    )

    assert not hasattr(result, "world_truth")
    assert not hasattr(result, "intent")
    assert not hasattr(result, "action_plan")


def test_downstream_contract_surface_enforces_bias_restrictions() -> None:
    weak = update_regulation_state(
        signals=(),
        prior_state=None,
        context=RegulationContext(require_strong_claim=True),
    )
    strong_candidate = update_regulation_state(
        (
            NeedSignal(
                axis=NeedAxis.ENERGY,
                value=20.0,
                source_ref="energy-hi",
                confidence=RegulationConfidence.HIGH,
            ),
            NeedSignal(
                axis=NeedAxis.SAFETY,
                value=30.0,
                source_ref="safety-hi",
                confidence=RegulationConfidence.HIGH,
            ),
            NeedSignal(
                axis=NeedAxis.COGNITIVE_LOAD,
                value=80.0,
                source_ref="cog-hi",
                confidence=RegulationConfidence.HIGH,
            ),
            NeedSignal(
                axis=NeedAxis.SOCIAL_CONTACT,
                value=50.0,
                source_ref="social-mid",
                confidence=RegulationConfidence.HIGH,
            ),
            NeedSignal(
                axis=NeedAxis.NOVELTY,
                value=45.0,
                source_ref="novelty-mid",
                confidence=RegulationConfidence.HIGH,
            ),
        ),
        prior_state=None,
        context=RegulationContext(require_strong_claim=True),
    )

    weak_decision = evaluate_downstream_regulation_gate(
        weak.bias, require_strong_claim=True
    )
    strong_decision = evaluate_downstream_regulation_gate(
        strong_candidate.bias, require_strong_claim=True
    )

    assert weak_decision.allowed is False
    assert strong_decision.allowed is True
