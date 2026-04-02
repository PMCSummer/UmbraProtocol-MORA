from dataclasses import fields

import pytest

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceEntry,
    PreferenceState,
    PreferenceUpdateResult,
    evaluate_preference_downstream_gate,
    update_regulatory_preferences,
)


def _result_with_ambiguity_pressure():
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=18.0, source_ref="energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=93.0, source_ref="cog"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    result = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-bound-pos",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("ambig",),
                observed_short_term_delta=0.8,
                observed_long_term_delta=0.6,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
            OutcomeTrace(
                episode_id="ep-bound-neg",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("ambig",),
                observed_short_term_delta=-0.9,
                observed_long_term_delta=-0.7,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=2,
            ),
        ),
    )
    return result


def test_public_r03_models_exclude_semantics_identity_and_planner_fields() -> None:
    forbidden = {
        "dictum",
        "semantic_parse",
        "truth",
        "intent",
        "illocution",
        "commitment",
        "identity",
        "values",
        "chosen_action",
        "policy",
    }
    field_names = (
        {f.name for f in fields(PreferenceEntry)}
        | {f.name for f in fields(PreferenceState)}
        | {f.name for f in fields(PreferenceUpdateResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_ambiguity_heavy_case_preserves_conflict_or_freeze_not_hidden_winner() -> None:
    result = _result_with_ambiguity_pressure()
    state = result.updated_preference_state
    assert result.no_final_selection_performed is True
    assert state.conflict_index or state.frozen_updates or state.unresolved_updates


def test_gate_rejects_raw_paths_and_accepts_typed_state() -> None:
    with pytest.raises(TypeError):
        evaluate_preference_downstream_gate("raw preference")
    with pytest.raises(TypeError):
        evaluate_preference_downstream_gate({"preference": "blob"})

    result = _result_with_ambiguity_pressure()
    gate = evaluate_preference_downstream_gate(result.updated_preference_state)
    assert gate.reason
