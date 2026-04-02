from dataclasses import replace

from substrate.affordances import create_default_capability_state, generate_regulation_affordances
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    OutcomeTrace,
    PreferenceContext,
    update_regulatory_preferences,
)


def _regulation_upstream():
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref="meta"),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref="meta"),
            NeedSignal(axis=NeedAxis.SAFETY, value=41.0, source_ref="meta"),
        ),
        prior_state=None,
        context=RegulationContext(),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    return regulation_state, affordances


def _surface(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


def _entry_signature(result):
    entry = result.updated_preference_state.entries[0]
    return (
        entry.option_class_id.value,
        entry.preference_sign.value,
        round(entry.preference_strength, 4),
        entry.conflict_state.value,
        round(entry.expected_short_term_delta, 4),
        round(entry.expected_long_term_delta, 4),
        entry.time_horizon.value,
    )


def test_regulation_metamorphic_permutation_and_cosmetic_changes_do_not_change_semantics() -> None:
    regulation_state, affordances = _regulation_upstream()
    candidate = affordances.candidates[0]
    outcome = OutcomeTrace(
        episode_id="ep-meta-1",
        option_class_id=candidate.option_class,
        affordance_id=candidate.affordance_id,
        target_need_or_set=candidate.target_axes,
        context_scope=("meta",),
        observed_short_term_delta=0.72,
        observed_long_term_delta=0.5,
        attribution_confidence=RegulationConfidence.HIGH,
        provenance="a",
        observed_at_step=1,
    )

    baseline = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(outcome,),
        context=PreferenceContext(decay_per_step=0.0),
    )

    reversed_affordances = replace(affordances, candidates=tuple(reversed(affordances.candidates)))
    reordered = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=reversed_affordances,
        outcome_traces=(replace(outcome, provenance="b"),),
        context=PreferenceContext(decay_per_step=0.0),
    )

    relabeled_candidate = replace(candidate, affordance_id=f"{candidate.affordance_id}-renamed")
    relabeled_candidates = tuple(
        relabeled_candidate if item.affordance_id == candidate.affordance_id else item
        for item in affordances.candidates
    )
    relabeled_affordances = replace(affordances, candidates=relabeled_candidates)
    relabeled = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=relabeled_affordances,
        outcome_traces=(replace(outcome, affordance_id=relabeled_candidate.affordance_id),),
        context=PreferenceContext(decay_per_step=0.0),
    )

    assert _entry_signature(baseline) == _entry_signature(reordered)
    assert _entry_signature(baseline) == _entry_signature(relabeled)


def test_regulation_metamorphic_attribution_and_context_changes_behave_honestly() -> None:
    regulation_state, affordances = _regulation_upstream()
    candidate = affordances.candidates[0]
    valid = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-meta-valid",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("ctx-a",),
                observed_short_term_delta=0.65,
                observed_long_term_delta=0.55,
                attribution_confidence=RegulationConfidence.HIGH,
                mixed_causes=False,
                observed_at_step=1,
            ),
        ),
    )
    mixed = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-meta-mixed",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("ctx-a",),
                observed_short_term_delta=0.65,
                observed_long_term_delta=0.55,
                attribution_confidence=RegulationConfidence.HIGH,
                mixed_causes=True,
                observed_at_step=2,
            ),
        ),
    )
    assert valid.updated_preference_state.entries
    assert not mixed.updated_preference_state.entries
    assert mixed.blocked_updates

    with_context = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            replace(
                OutcomeTrace(
                    episode_id="ep-meta-ctx-1",
                    option_class_id=candidate.option_class,
                    affordance_id=candidate.affordance_id,
                    target_need_or_set=candidate.target_axes,
                    context_scope=("ctx-a",),
                    observed_short_term_delta=0.6,
                    observed_long_term_delta=0.4,
                    attribution_confidence=RegulationConfidence.HIGH,
                    observed_at_step=3,
                ),
                episode_id="ep-meta-ctx-1",
            ),
            OutcomeTrace(
                episode_id="ep-meta-ctx-2",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("ctx-b",),
                observed_short_term_delta=-0.55,
                observed_long_term_delta=-0.45,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=4,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    )
    no_context = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-meta-global-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=(),
                observed_short_term_delta=0.6,
                observed_long_term_delta=0.4,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=3,
            ),
            OutcomeTrace(
                episode_id="ep-meta-global-2",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=(),
                observed_short_term_delta=-0.55,
                observed_long_term_delta=-0.45,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=4,
            ),
        ),
        context=PreferenceContext(decay_per_step=0.0),
    )
    assert len(with_context.updated_preference_state.entries) > len(no_context.updated_preference_state.entries)


def test_language_metamorphic_changes_are_predictable_and_reversible() -> None:
    compact = _surface("alpha beta.", "m-meta-compact")
    spaced = _surface("  alpha\tbeta.  ", "m-meta-spaced")
    assert compact.surface.reversible_span_map_present is True
    assert spaced.surface.reversible_span_map_present is True
    assert [token.normalized_text for token in compact.surface.tokens] == [
        token.normalized_text for token in spaced.surface.tokens
    ]

    punct_plain = build_morphosyntax_candidate_space(_surface("alpha beta gamma", "m-meta-p1"))
    punct_changed = build_morphosyntax_candidate_space(_surface("alpha beta; gamma.", "m-meta-p2"))
    assert punct_changed.telemetry.clause_count >= punct_plain.telemetry.clause_count

    quoted = _surface('"alpha beta"', "m-meta-q1")
    unquoted = _surface("alpha beta", "m-meta-q2")
    assert len(quoted.surface.quotes) != len(unquoted.surface.quotes)

    stable = _surface("alpha beta ... gamma", "m-meta-a1")
    clearer = _surface("alpha beta. gamma.", "m-meta-a2")
    assert stable.surface.ambiguities
    assert len(stable.surface.ambiguities) >= len(clearer.surface.ambiguities)

    syntax_stable = build_morphosyntax_candidate_space(stable)
    syntax_clearer = build_morphosyntax_candidate_space(clearer)
    unresolved_stable = sum(
        len(h.unresolved_attachments) for h in syntax_stable.hypothesis_set.hypotheses
    )
    unresolved_clearer = sum(
        len(h.unresolved_attachments) for h in syntax_clearer.hypothesis_set.hypotheses
    )
    assert unresolved_stable >= unresolved_clearer
