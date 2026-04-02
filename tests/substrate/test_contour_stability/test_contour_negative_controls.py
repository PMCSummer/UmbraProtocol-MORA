from dataclasses import replace

import pytest

from substrate.affordances import AffordanceResult, create_default_capability_state, generate_regulation_affordances
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.morphosyntax import build_morphosyntax_candidate_space, evaluate_morphosyntax_downstream_gate
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    PreferenceState,
    update_regulatory_preferences,
)


def _prepare_regulation_stack():
    state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="neg"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref="neg"),
            NeedSignal(axis=NeedAxis.SAFETY, value=40.0, source_ref="neg"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=state,
        capability_state=create_default_capability_state(),
    )
    return state, affordances


def _dummy_downstream_rank(
    affordance_result: AffordanceResult,
    preference_state: PreferenceState,
    *,
    decision_step: int,
) -> tuple[str, ...]:
    if preference_state.last_updated_step > decision_step:
        raise ValueError("preference entries created after decision tick are not eligible")
    score_by_option: dict[object, float] = {}
    for entry in preference_state.entries:
        if entry.update_status.value == "frozen":
            continue
        signed = entry.preference_strength if entry.preference_sign.value == "positive" else (
            -entry.preference_strength if entry.preference_sign.value == "negative" else 0.0
        )
        prior = score_by_option.get(entry.option_class_id, -999.0)
        score_by_option[entry.option_class_id] = max(prior, signed)
    ranked = sorted(
        affordance_result.candidates,
        key=lambda candidate: (
            score_by_option.get(candidate.option_class, 0.0),
            candidate.expected_effect.effect_strength_estimate,
        ),
        reverse=True,
    )
    return tuple(candidate.affordance_id for candidate in ranked)


def test_r03_anti_backfill_changed_ledger_changes_downstream_sensitive_choice() -> None:
    regulation_state, affordances = _prepare_regulation_stack()
    a = affordances.candidates[0]
    b = affordances.candidates[min(1, len(affordances.candidates) - 1)]

    state_a = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-rank-a",
                option_class_id=a.option_class,
                affordance_id=a.affordance_id,
                target_need_or_set=a.target_axes,
                context_scope=("rank",),
                observed_short_term_delta=0.8,
                observed_long_term_delta=0.6,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    ).updated_preference_state
    state_b = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-rank-b",
                option_class_id=b.option_class,
                affordance_id=b.affordance_id,
                target_need_or_set=b.target_axes,
                context_scope=("rank",),
                observed_short_term_delta=0.95,
                observed_long_term_delta=0.7,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=2,
            ),
        ),
        preference_state=state_a,
        context=PreferenceContext(decay_per_step=0.0),
    ).updated_preference_state

    rank_a = _dummy_downstream_rank(affordances, state_a, decision_step=state_a.last_updated_step)
    rank_b = _dummy_downstream_rank(affordances, state_b, decision_step=state_b.last_updated_step)
    assert rank_a[0] != rank_b[0]


def test_r03_negative_controls_no_update_no_change_and_text_only_noise_no_effect() -> None:
    regulation_state, affordances = _prepare_regulation_stack()
    c = affordances.candidates[0]
    result_1 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-base",
                option_class_id=c.option_class,
                affordance_id=c.affordance_id,
                target_need_or_set=c.target_axes,
                context_scope=("stable",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="label-a",
                observed_at_step=1,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    )
    result_2 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(),
        preference_state=result_1.updated_preference_state,
        context=PreferenceContext(decay_per_step=0.0),
    )
    result_3 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-base-2",
                option_class_id=c.option_class,
                affordance_id=c.affordance_id,
                target_need_or_set=c.target_axes,
                context_scope=("stable",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                provenance="label-b-only-text-change",
                observed_at_step=2,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    )

    rank_1 = _dummy_downstream_rank(
        affordances, result_1.updated_preference_state, decision_step=result_1.updated_preference_state.last_updated_step
    )
    rank_2 = _dummy_downstream_rank(
        affordances, result_2.updated_preference_state, decision_step=result_2.updated_preference_state.last_updated_step
    )
    rank_3 = _dummy_downstream_rank(
        affordances, result_3.updated_preference_state, decision_step=result_3.updated_preference_state.last_updated_step
    )
    assert rank_1 == rank_2
    assert rank_1 == rank_3


def test_r03_preference_entry_must_preexist_downstream_use_tick() -> None:
    regulation_state, affordances = _prepare_regulation_stack()
    c = affordances.candidates[0]
    state = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-preexist",
                option_class_id=c.option_class,
                affordance_id=c.affordance_id,
                target_need_or_set=c.target_axes,
                context_scope=("preexist",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
    ).updated_preference_state
    with pytest.raises(ValueError):
        _dummy_downstream_rank(affordances, state, decision_step=0)


def test_schema_drift_and_measurement_shift_surface_honest_incompatibility() -> None:
    regulation_state, affordances = _prepare_regulation_stack()
    candidate = affordances.candidates[0]
    baseline = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-schema-base",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("schema",),
                observed_short_term_delta=0.6,
                observed_long_term_delta=0.45,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
    )
    schema_mismatch = replace(baseline.updated_preference_state, schema_version="r03.preference.v999")
    res_schema = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(),
        preference_state=schema_mismatch,
    )
    assert res_schema.abstain is True
    assert "schema_version incompatible" in (res_schema.abstain_reason or "")

    taxonomy_mismatch = replace(baseline.updated_preference_state, taxonomy_version="r02.affordance.v999")
    res_taxonomy = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(),
        preference_state=taxonomy_mismatch,
    )
    assert res_taxonomy.abstain is True
    assert "taxonomy_version incompatible" in (res_taxonomy.abstain_reason or "")

    out_of_scale = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-scale-drift",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("schema",),
                observed_short_term_delta=12.0,
                observed_long_term_delta=9.0,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=2,
            ),
        ),
    )
    assert not out_of_scale.updated_preference_state.entries
    assert out_of_scale.blocked_updates
    assert "measurement bounds" in out_of_scale.blocked_updates[0].reason


def test_silent_decorative_layer_falsifiers_for_r03_l01_l02() -> None:
    regulation_state, affordances = _prepare_regulation_stack()
    candidate = affordances.candidates[-1]
    pref_state = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-decorative",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("decorative",),
                observed_short_term_delta=0.8,
                observed_long_term_delta=0.6,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
    ).updated_preference_state
    ranked_with_r03 = _dummy_downstream_rank(
        affordances, pref_state, decision_step=pref_state.last_updated_step
    )
    ranked_without_r03 = tuple(
        item.affordance_id
        for item in sorted(
            affordances.candidates,
            key=lambda candidate_item: candidate_item.expected_effect.effect_strength_estimate,
            reverse=True,
        )
    )
    assert ranked_with_r03 != ranked_without_r03

    unit = ground_epistemic_input(
        InputMaterial(material_id="m-decorative-lang", content='we do not track "alpha" beta ...'),
        SourceMetadata(
            source_id="user-decorative-lang",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(unit.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    assert syntax.hypothesis_set.hypotheses
    assert syntax.hypothesis_set.no_selected_winner is True

    with pytest.raises(TypeError):
        build_morphosyntax_candidate_space(unit.unit.content)
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate(surface)
