from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceConflictState,
    PreferenceContext,
    PreferenceTimeHorizon,
    PreferenceUncertainty,
    PreferenceUpdateStatus,
    update_regulatory_preferences,
)


def _upstream():
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref="energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref="cog"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    return regulation_state, affordances


def test_short_term_vs_long_term_contrast_is_explicit_and_not_collapsed() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-temporal-mixed",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("recovery",),
                observed_short_term_delta=0.9,
                observed_long_term_delta=-0.7,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    )

    entry = result.updated_preference_state.entries[0]
    assert entry.time_horizon == PreferenceTimeHorizon.MIXED
    assert entry.conflict_state == PreferenceConflictState.CONFLICTING
    assert entry.expected_short_term_delta > 0
    assert entry.expected_long_term_delta < 0


def test_delayed_effect_unresolved_freezes_update_instead_of_forcing_claim() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-delayed-unresolved",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("delayed-window",),
                observed_short_term_delta=0.3,
                observed_long_term_delta=None,
                attribution_confidence=RegulationConfidence.MEDIUM,
                delayed_window_complete=False,
                observed_at_step=3,
            ),
        ),
    )

    assert not result.updated_preference_state.entries
    assert result.blocked_updates
    assert result.blocked_updates[0].uncertainty == PreferenceUncertainty.DELAYED_EFFECT_UNRESOLVED
    assert result.blocked_updates[0].frozen is True


def test_decay_and_staleness_progress_when_no_new_episode_support_arrives() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]
    step1 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-decay-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("decay",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.45,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.1, step_delta=1),
    )
    entry1 = step1.updated_preference_state.entries[0]
    step2 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(),
        preference_state=step1.updated_preference_state,
        context=PreferenceContext(decay_per_step=0.1, step_delta=2),
    )
    entry2 = step2.updated_preference_state.entries[0]

    assert entry2.preference_strength < entry1.preference_strength
    assert entry2.staleness_steps >= entry1.staleness_steps + 2
    assert entry2.update_status in {PreferenceUpdateStatus.STALE, PreferenceUpdateStatus.FROZEN}
