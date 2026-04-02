from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import ViabilityContext, ViabilityEscalationStage, compute_viability_control_state


def _regulation_state(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-meta-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-meta-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-meta-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-metamorphic",)),
    ).state


def _rank(stage: ViabilityEscalationStage) -> int:
    if stage == ViabilityEscalationStage.CRITICAL:
        return 4
    if stage == ViabilityEscalationStage.THREAT:
        return 3
    if stage == ViabilityEscalationStage.ELEVATED:
        return 2
    return 1


def test_small_safe_perturbations_do_not_randomly_jump_to_critical() -> None:
    base = _regulation_state(energy=36.0, cognitive=68.0, safety=50.0)
    perturbed = _regulation_state(energy=35.0, cognitive=69.0, safety=51.0)
    affordances_base = generate_regulation_affordances(
        regulation_state=base,
        capability_state=create_default_capability_state(),
    )
    affordances_perturbed = generate_regulation_affordances(
        regulation_state=perturbed,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()
    result_base = compute_viability_control_state(base, affordances_base, preferences)
    result_perturbed = compute_viability_control_state(perturbed, affordances_perturbed, preferences)

    assert result_perturbed.state.escalation_stage != ViabilityEscalationStage.CRITICAL
    assert abs(_rank(result_base.state.escalation_stage) - _rank(result_perturbed.state.escalation_stage)) <= 1


def test_structurally_relevant_worsening_perturbation_changes_pressure_predictably() -> None:
    current = _regulation_state(energy=19.0, cognitive=90.0, safety=40.0)
    prior_stable = _regulation_state(energy=21.0, cognitive=88.0, safety=42.0)
    prior_worsening = _regulation_state(energy=48.0, cognitive=62.0, safety=70.0)
    affordances = generate_regulation_affordances(
        regulation_state=current,
        capability_state=create_default_capability_state(),
    )
    preferences = create_empty_preference_state()
    stable = compute_viability_control_state(
        current,
        affordances,
        preferences,
        context=ViabilityContext(prior_regulation_state=prior_stable),
    )
    worsening = compute_viability_control_state(
        current,
        affordances,
        preferences,
        context=ViabilityContext(prior_regulation_state=prior_worsening),
    )
    assert worsening.state.pressure_level >= stable.state.pressure_level
