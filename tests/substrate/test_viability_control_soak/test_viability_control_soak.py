from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import ViabilityContext, ViabilityEscalationStage, compute_viability_control_state


def _regulation_state(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-soak-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-soak-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-soak-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-soak",)),
    ).state


def test_soak_sequence_preserves_persistence_and_allows_deescalation_after_recovery() -> None:
    sequence = (
        (20.0, 88.0, 44.0),  # elevated
        (17.0, 92.0, 40.0),  # worsening
        (15.0, 95.0, 36.0),  # critical/threat
        (14.0, 96.0, 35.0),  # failed local recovery
        (32.0, 72.0, 55.0),  # partial recovery
        (55.0, 56.0, 72.0),  # successful recovery
    )
    prior_reg = None
    prior_viability = None
    failed_attempts = 0
    observed_stages = []
    observed_pressure = []
    conflict_or_unknown_steps = 0

    for idx, (energy, cognitive, safety) in enumerate(sequence, start=1):
        regulation = _regulation_state(energy=energy, cognitive=cognitive, safety=safety)
        affordances = generate_regulation_affordances(
            regulation_state=regulation,
            capability_state=create_default_capability_state(),
        )
        result = compute_viability_control_state(
            regulation,
            affordances,
            create_empty_preference_state(),
            context=ViabilityContext(
                prior_regulation_state=prior_reg,
                prior_viability_state=prior_viability,
                recent_failed_recovery_attempts=failed_attempts,
                source_lineage=(f"r04-soak-step-{idx}",),
            ),
        )
        observed_stages.append(result.state.escalation_stage)
        observed_pressure.append(result.state.pressure_level)
        if result.state.uncertainty_state:
            conflict_or_unknown_steps += 1

        if prior_viability is not None and result.state.pressure_level >= prior_viability.pressure_level:
            failed_attempts += 1
        else:
            failed_attempts = max(0, failed_attempts - 1)

        prior_reg = regulation
        prior_viability = result.state

    assert max(observed_pressure) >= 0.7
    assert observed_stages[-1] in {ViabilityEscalationStage.BASELINE, ViabilityEscalationStage.ELEVATED}
    assert observed_pressure[-1] <= observed_pressure[2]
    assert conflict_or_unknown_steps >= 1
