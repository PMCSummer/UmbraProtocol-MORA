from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import (
    ViabilityContext,
    ViabilityEscalationStage,
    ViabilityOverrideScope,
    compute_viability_control_state,
)


def _regulation_state(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-deesc-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-deesc-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-deesc-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-deescalation",)),
    ).state


def _stage_rank(stage: ViabilityEscalationStage) -> int:
    if stage == ViabilityEscalationStage.CRITICAL:
        return 4
    if stage == ViabilityEscalationStage.THREAT:
        return 3
    if stage == ViabilityEscalationStage.ELEVATED:
        return 2
    return 1


def _scope_rank(scope: ViabilityOverrideScope) -> int:
    if scope == ViabilityOverrideScope.EMERGENCY:
        return 5
    if scope == ViabilityOverrideScope.BROAD:
        return 4
    if scope == ViabilityOverrideScope.FOCUSED:
        return 3
    if scope == ViabilityOverrideScope.NARROW:
        return 2
    return 1


def test_successful_recovery_deescalates_pressure_and_override_scope() -> None:
    severe = _regulation_state(energy=14.0, cognitive=93.0, safety=34.0)
    recovered = _regulation_state(energy=56.0, cognitive=55.0, safety=72.0)
    affordances_severe = generate_regulation_affordances(
        regulation_state=severe,
        capability_state=create_default_capability_state(),
    )
    affordances_recovered = generate_regulation_affordances(
        regulation_state=recovered,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()

    severe_result = compute_viability_control_state(
        severe,
        affordances_severe,
        preferences,
        context=ViabilityContext(source_lineage=("r04-deesc-severe",)),
    )
    recovered_result = compute_viability_control_state(
        recovered,
        affordances_recovered,
        preferences,
        context=ViabilityContext(
            prior_regulation_state=severe,
            prior_viability_state=severe_result.state,
            source_lineage=("r04-deesc-recovered",),
        ),
    )

    assert _stage_rank(recovered_result.state.escalation_stage) <= _stage_rank(
        severe_result.state.escalation_stage
    )
    assert recovered_result.state.pressure_level <= severe_result.state.pressure_level
    assert _scope_rank(recovered_result.state.override_scope) <= _scope_rank(
        severe_result.state.override_scope
    )
    assert recovered_result.state.deescalation_conditions
