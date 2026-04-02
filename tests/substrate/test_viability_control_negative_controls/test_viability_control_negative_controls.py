from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    update_regulatory_preferences,
)
from substrate.viability_control import ViabilityEscalationStage, compute_viability_control_state


def _regulation_state(*, energy: float, cognitive: float, safety: float):
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref="r04-neg-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref="r04-neg-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref="r04-neg-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r04-negative-controls",)),
    ).state


def _preference_state(regulation_state, affordances, *, short_delta: float, long_delta: float):
    candidate = affordances.candidates[0]
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id=f"ep-r04-neg-{short_delta}-{long_delta}",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("negative-control",),
                observed_short_term_delta=short_delta,
                observed_long_term_delta=long_delta,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(source_lineage=("r04-negative-controls",)),
    )
    return result.updated_preference_state


def test_preference_strength_does_not_replace_survival_threat_magnitude() -> None:
    regulation = _regulation_state(energy=17.0, cognitive=94.0, safety=35.0)
    affordances = generate_regulation_affordances(
        regulation_state=regulation,
        capability_state=create_default_capability_state(),
    )
    positive_pref = _preference_state(
        regulation,
        affordances,
        short_delta=0.8,
        long_delta=0.6,
    )
    negative_pref = _preference_state(
        regulation,
        affordances,
        short_delta=-0.8,
        long_delta=-0.6,
    )
    positive = compute_viability_control_state(regulation, affordances, positive_pref)
    negative = compute_viability_control_state(regulation, affordances, negative_pref)

    assert positive.state.escalation_stage == negative.state.escalation_stage
    assert abs(positive.state.pressure_level - negative.state.pressure_level) <= 0.08


def test_low_threat_state_is_not_escalated_by_preference_only_signal() -> None:
    low_threat = _regulation_state(energy=55.0, cognitive=50.0, safety=70.0)
    affordances = generate_regulation_affordances(
        regulation_state=low_threat,
        capability_state=create_default_capability_state(),
    )
    negative_pref = _preference_state(
        low_threat,
        affordances,
        short_delta=-0.95,
        long_delta=-0.95,
    )
    result = compute_viability_control_state(low_threat, affordances, negative_pref)
    assert result.state.escalation_stage in {
        ViabilityEscalationStage.BASELINE,
        ViabilityEscalationStage.ELEVATED,
    }


def test_cosmetic_context_lineage_does_not_trigger_hardcoded_emergency() -> None:
    regulation = _regulation_state(energy=24.0, cognitive=80.0, safety=46.0)
    affordances = generate_regulation_affordances(
        regulation_state=regulation,
        capability_state=create_default_capability_state(),
    )
    preference = _preference_state(regulation, affordances, short_delta=0.4, long_delta=0.3)
    a = compute_viability_control_state(regulation, affordances, preference)
    b = compute_viability_control_state(regulation, affordances, preference)
    assert a.state.escalation_stage == b.state.escalation_stage
    assert abs(a.state.pressure_level - b.state.pressure_level) <= 0.01


def test_benign_noise_does_not_inflate_to_false_emergency() -> None:
    mild_a = _regulation_state(energy=52.0, cognitive=62.0, safety=60.0)
    mild_b = _regulation_state(energy=49.0, cognitive=64.0, safety=58.0)
    affordances_a = generate_regulation_affordances(
        regulation_state=mild_a,
        capability_state=create_default_capability_state(),
    )
    affordances_b = generate_regulation_affordances(
        regulation_state=mild_b,
        capability_state=create_default_capability_state(),
    )
    pref_a = _preference_state(mild_a, affordances_a, short_delta=0.2, long_delta=0.15)
    pref_b = _preference_state(mild_b, affordances_b, short_delta=0.2, long_delta=0.15)
    result_a = compute_viability_control_state(mild_a, affordances_a, pref_a)
    result_b = compute_viability_control_state(mild_b, affordances_b, pref_b)

    assert result_a.state.escalation_stage != ViabilityEscalationStage.CRITICAL
    assert result_b.state.escalation_stage != ViabilityEscalationStage.CRITICAL
