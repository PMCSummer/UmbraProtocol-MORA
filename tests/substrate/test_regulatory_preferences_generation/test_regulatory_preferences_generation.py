from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationContext, RegulationConfidence, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    PreferenceUpdateResult,
    update_regulatory_preferences,
)


def _r01_state():
    return update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=22.0, source_ref="r01-energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref="r01-cog"),
            NeedSignal(axis=NeedAxis.SAFETY, value=45.0, source_ref="r01-safety"),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=("r01",)),
    ).state


def _r02_result(regulation_state):
    return generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )


def test_generation_produces_typed_preference_state_and_update_ledger() -> None:
    regulation_state = _r01_state()
    affordances = _r02_result(regulation_state)
    candidate = affordances.candidates[0]

    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-r03-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("baseline",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.45,
                attribution_confidence=RegulationConfidence.HIGH,
                source_ref=candidate.affordance_id,
                provenance="r03-test",
                observed_at_step=1,
            ),
        ),
    )

    assert isinstance(result, PreferenceUpdateResult)
    assert result.updated_preference_state.entries
    assert result.update_events
    assert result.telemetry.input_affordance_ids
    assert result.no_final_selection_performed is True
    assert not hasattr(result, "selected_action")

    entry = result.updated_preference_state.entries[0]
    assert entry.option_class_id == candidate.option_class
    assert entry.context_scope == ("baseline",)
    assert entry.episode_support == 1
    assert entry.last_update_provenance


def test_repeated_consistent_evidence_strengthens_same_entry_predictably() -> None:
    regulation_state = _r01_state()
    affordances = _r02_result(regulation_state)
    candidate = affordances.candidates[0]
    context = PreferenceContext(learning_rate=0.45, decay_per_step=0.0)

    step1 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-r03-repeat-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("focused",),
                observed_short_term_delta=0.65,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="repeat",
                observed_at_step=1,
            ),
        ),
        context=context,
    )
    step2 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-r03-repeat-2",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("focused",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.55,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="repeat",
                observed_at_step=2,
            ),
        ),
        preference_state=step1.updated_preference_state,
        context=context,
    )

    first = step1.updated_preference_state.entries[0]
    second = step2.updated_preference_state.entries[0]
    assert second.entry_id == first.entry_id
    assert second.episode_support == first.episode_support + 1
    assert second.preference_strength >= first.preference_strength
    assert second.confidence in {RegulationConfidence.MEDIUM, RegulationConfidence.HIGH}
