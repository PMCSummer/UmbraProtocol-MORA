from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceConflictState,
    PreferenceContext,
    PreferenceUpdateKind,
    update_regulatory_preferences,
)


def _upstream():
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=88.0, source_ref="cog"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    return regulation_state, affordances


def test_conflicting_outcomes_register_conflict_not_silent_average() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]
    context = PreferenceContext(learning_rate=0.5, decay_per_step=0.0, conflict_threshold=0.2)

    first = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-conflict-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("stress",),
                observed_short_term_delta=0.8,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="conflict-test",
                observed_at_step=1,
            ),
        ),
        context=context,
    )
    second = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-conflict-2",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("stress",),
                observed_short_term_delta=-0.85,
                observed_long_term_delta=-0.55,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="conflict-test",
                observed_at_step=2,
            ),
        ),
        preference_state=first.updated_preference_state,
        context=context,
    )

    entry = second.updated_preference_state.entries[0]
    assert entry.conflict_state == PreferenceConflictState.CONFLICTING
    assert second.updated_preference_state.conflict_index
    assert any(
        event.update_kind
        in {
            PreferenceUpdateKind.CONFLICT_REGISTER,
            PreferenceUpdateKind.FREEZE,
            PreferenceUpdateKind.INVERT,
        }
        for event in second.update_events
    )


def test_same_option_in_different_contexts_keeps_context_scoped_entries() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]

    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-ctx-a",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("mode:overload",),
                observed_short_term_delta=0.6,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
            OutcomeTrace(
                episode_id="ep-ctx-b",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("mode:social",),
                observed_short_term_delta=-0.5,
                observed_long_term_delta=-0.4,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=2,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    )

    entries = [
        entry
        for entry in result.updated_preference_state.entries
        if entry.option_class_id == candidate.option_class
    ]
    assert len(entries) == 2
    assert {entry.context_scope for entry in entries} == {
        ("mode:overload",),
        ("mode:social",),
    }
