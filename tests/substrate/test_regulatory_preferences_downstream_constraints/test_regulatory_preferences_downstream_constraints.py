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


def _typed_result() -> PreferenceUpdateResult:
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="energy"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=87.0, source_ref="cog"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    candidate = affordances.candidates[0]
    return update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-gate-ok",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("gate",),
                observed_short_term_delta=0.75,
                observed_long_term_delta=0.55,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
    )


def test_downstream_gate_rejects_raw_input_and_accepts_typed_preference_artifacts() -> None:
    with pytest.raises(TypeError):
        evaluate_preference_downstream_gate("raw-score-blob")
    with pytest.raises(TypeError):
        evaluate_preference_downstream_gate({"scores": [0.1, 0.2]})

    typed_result = _typed_result()
    gate_from_result = evaluate_preference_downstream_gate(typed_result)
    gate_from_state = evaluate_preference_downstream_gate(typed_result.updated_preference_state)

    assert gate_from_result.accepted is True
    assert gate_from_state.accepted is True
    assert gate_from_result.accepted_entry_ids
    assert gate_from_state.accepted_entry_ids


def test_no_hidden_selection_and_no_semantic_overreach_in_public_r03_models() -> None:
    forbidden = {
        "selected_action",
        "chosen_affordance",
        "policy_decision",
        "dictum",
        "semantics",
        "truth",
        "intent",
        "illocution",
        "commitment",
        "identity",
        "values",
        "referent",
    }
    field_names = (
        {f.name for f in fields(PreferenceEntry)}
        | {f.name for f in fields(PreferenceState)}
        | {f.name for f in fields(PreferenceUpdateResult)}
    )
    assert forbidden.isdisjoint(field_names)

    result = _typed_result()
    assert result.no_final_selection_performed is True
    assert not hasattr(result, "selected_action")


def test_ablation_lite_raw_path_cannot_replace_typed_preference_path() -> None:
    result = _typed_result()
    gate = evaluate_preference_downstream_gate(result.updated_preference_state)
    assert gate.accepted is True

    with pytest.raises(TypeError):
        evaluate_preference_downstream_gate(result.telemetry.input_affordance_ids)
