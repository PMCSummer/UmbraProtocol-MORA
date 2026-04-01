from substrate.affordances import (
    AffordanceContext,
    AffordanceOptionClass,
    AffordanceStatus,
    CapabilitySpec,
    CapabilityState,
    create_default_capability_state,
    generate_regulation_affordances,
)
from substrate.regulation import (
    NeedAxis,
    NeedSignal,
    RegulationConfidence,
    RegulationContext,
    update_regulation_state,
)


def _safety_pressure_state():
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.SAFETY, value=30.0, source_ref="safety-low"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=95.0, source_ref="cog-high"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state


def test_capability_disabled_marks_candidate_unavailable() -> None:
    base = create_default_capability_state()
    specs = tuple(
        CapabilitySpec(
            option_class=spec.option_class,
            enabled=False if spec.option_class == AffordanceOptionClass.LOAD_SHEDDING else spec.enabled,
            max_intensity=spec.max_intensity,
            cooldown_steps_remaining=spec.cooldown_steps_remaining,
            risk_multiplier=spec.risk_multiplier,
            source_ref=spec.source_ref,
        )
        for spec in base.capabilities
    )
    result = generate_regulation_affordances(
        regulation_state=_safety_pressure_state(),
        capability_state=CapabilityState(capabilities=specs, confidence=base.confidence),
    )

    target = next(
        candidate
        for candidate in result.candidates
        if candidate.option_class == AffordanceOptionClass.LOAD_SHEDDING
    )
    assert target.status == AffordanceStatus.UNAVAILABLE
    assert target.unavailable_marker is not None


def test_context_conflict_blocks_protective_suppression_and_risk_can_be_unsafe() -> None:
    state = _safety_pressure_state()
    blocked = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
        context=AffordanceContext(allow_protective_suppression=False),
    )
    blocked_candidate = next(
        candidate
        for candidate in blocked.candidates
        if candidate.option_class == AffordanceOptionClass.SAFETY_RECHECK
    )
    assert blocked_candidate.status == AffordanceStatus.BLOCKED
    assert blocked_candidate.blocked_marker is not None

    unsafe = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
        context=AffordanceContext(max_risk_tolerance=0.2),
    )
    unsafe_candidate = next(
        candidate
        for candidate in unsafe.candidates
        if candidate.option_class == AffordanceOptionClass.SAFETY_RECHECK
    )
    assert unsafe_candidate.status == AffordanceStatus.UNSAFE
    assert unsafe_candidate.unsafe_marker is not None


def test_low_confidence_inputs_create_provisional_unknown_effect_candidates() -> None:
    low_conf_regulation = update_regulation_state(
        signals=(),
        prior_state=None,
        context=RegulationContext(),
    ).state
    result = generate_regulation_affordances(
        regulation_state=low_conf_regulation,
        capability_state=CapabilityState(
            capabilities=create_default_capability_state().capabilities,
            confidence=RegulationConfidence.LOW,
        ),
    )

    assert any(candidate.status == AffordanceStatus.PROVISIONAL for candidate in result.candidates)
    assert any(candidate.unknown_effect is not None for candidate in result.candidates)
