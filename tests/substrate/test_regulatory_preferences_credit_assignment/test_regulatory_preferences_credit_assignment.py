from substrate.affordances import AffordanceOptionClass, create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceUncertainty,
    update_regulatory_preferences,
)


def _upstream():
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=21.0, source_ref="energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=92.0, source_ref="cog"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    return regulation_state, affordances


def test_mixed_cause_trace_is_blocked_instead_of_strongly_updating_preference() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-mixed-cause",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("mixed",),
                observed_short_term_delta=0.9,
                observed_long_term_delta=0.8,
                attribution_confidence=RegulationConfidence.HIGH,
                mixed_causes=True,
                observed_at_step=1,
            ),
        ),
    )

    assert not result.updated_preference_state.entries
    assert result.blocked_updates
    assert result.blocked_updates[0].uncertainty == PreferenceUncertainty.ATTRIBUTION_BLOCKED
    assert result.blocked_updates[0].frozen is True


def test_affordance_identity_mismatch_blocks_credit_assignment() -> None:
    regulation_state, affordances = _upstream()
    candidate = affordances.candidates[0]
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-bad-aff-id",
                option_class_id=candidate.option_class,
                affordance_id="aff-missing-from-r02",
                target_need_or_set=candidate.target_axes,
                context_scope=("id-mismatch",),
                observed_short_term_delta=0.5,
                observed_long_term_delta=0.2,
                attribution_confidence=RegulationConfidence.MEDIUM,
                observed_at_step=1,
            ),
        ),
    )

    assert not result.updated_preference_state.entries
    assert result.blocked_updates
    assert result.blocked_updates[0].uncertainty == PreferenceUncertainty.ATTRIBUTION_BLOCKED
    assert "affordance_id not traceable" in result.blocked_updates[0].reason


def test_r03_does_not_invent_option_classes_missing_from_r02_landscape() -> None:
    regulation_state, affordances = _upstream()
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-non-r02-option",
                option_class_id=AffordanceOptionClass.SAFETY_RECHECK,
                affordance_id=None,
                target_need_or_set=(NeedAxis.SAFETY,),
                context_scope=("non-r02-option",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.6,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
    )

    assert not result.updated_preference_state.entries
    assert result.blocked_updates
    assert result.blocked_updates[0].uncertainty == PreferenceUncertainty.ATTRIBUTION_BLOCKED
    assert "option_class absent" in result.blocked_updates[0].reason
