from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import create_empty_preference_state
from substrate.viability_control import ViabilityUncertaintyState, compute_viability_control_state


def _bundle(regulation_result_or_state):
    if hasattr(regulation_result_or_state, "state"):
        state = regulation_result_or_state.state
    else:
        state = regulation_result_or_state
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    return affordances, create_empty_preference_state()


def test_insufficient_observability_and_no_strong_override_are_explicit() -> None:
    low_obs_state = update_regulation_state(
        (),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-unc-low-observability",)),
    ).state
    affordances, preferences = _bundle(low_obs_state)
    result = compute_viability_control_state(low_obs_state, affordances, preferences)

    markers = set(result.state.uncertainty_state)
    assert ViabilityUncertaintyState.INSUFFICIENT_OBSERVABILITY in markers
    assert ViabilityUncertaintyState.NO_STRONG_OVERRIDE_CLAIM in markers


def test_mixed_deterioration_and_boundary_uncertain_paths_are_visible() -> None:
    mixed_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=14.0, source_ref="r04-unc-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=96.0, source_ref="r04-unc-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=38.0, source_ref="r04-unc-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-unc-mixed",)),
    ).state
    affordances, preferences = _bundle(mixed_state)
    result = compute_viability_control_state(mixed_state, affordances, preferences)
    markers = set(result.state.uncertainty_state)
    assert ViabilityUncertaintyState.MIXED_DETERIORATION in markers
    assert ViabilityUncertaintyState.BOUNDARY_UNCERTAIN in markers


def test_unresolved_conflict_marker_surfaces_from_tradeoff_competition() -> None:
    conflict_result = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref="r04-unc-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=95.0, source_ref="r04-unc-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=34.0, source_ref="r04-unc-safety"),
            NeedSignal(axis=NeedAxis.SOCIAL_CONTACT, value=20.0, source_ref="r04-unc-social"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-unc-conflict",)),
    )
    affordances, preferences = _bundle(conflict_result)
    result = compute_viability_control_state(conflict_result, affordances, preferences)
    markers = set(result.state.uncertainty_state)
    assert ViabilityUncertaintyState.UNRESOLVED_CONFLICT in markers
