from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import ViabilityContext, ViabilityEscalationStage, compute_viability_control_state


def _regulation(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-persist-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-persist-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-persist-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-persistence",)),
    ).state


def test_unresolved_critical_pressure_persists_across_local_unsuccessful_step_and_context_switch() -> None:
    step1_state = _regulation(energy=15.0, cognitive=95.0, safety=35.0)
    step1_affordances = generate_regulation_affordances(
        regulation_state=step1_state,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()
    step1 = compute_viability_control_state(
        step1_state,
        step1_affordances,
        preferences,
        context=ViabilityContext(source_lineage=("r04-persistence-step1",)),
    )
    assert step1.state.escalation_stage in {
        ViabilityEscalationStage.THREAT,
        ViabilityEscalationStage.CRITICAL,
    }

    step2_state = _regulation(energy=16.0, cognitive=93.0, safety=36.0)
    step2_affordances = generate_regulation_affordances(
        regulation_state=step2_state,
        capability_state=create_default_capability_state(),
    )
    step2 = compute_viability_control_state(
        step2_state,
        step2_affordances,
        preferences,
        context=ViabilityContext(
            prior_regulation_state=step1_state,
            prior_viability_state=step1.state,
            recent_failed_recovery_attempts=2,
            source_lineage=("r04-persistence-step2-context-shift",),
        ),
    )

    assert step2.state.escalation_stage in {
        ViabilityEscalationStage.THREAT,
        ViabilityEscalationStage.CRITICAL,
    }
    assert step2.state.persistence_state.value in {"persistent", "chronic", "emerging"}
    assert step2.state.pressure_level >= 0.55
