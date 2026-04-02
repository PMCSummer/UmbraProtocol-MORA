import random

from substrate.affordances import AffordanceOptionClass, create_default_capability_state, generate_regulation_affordances
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
    PreferenceUpdateKind,
    create_empty_preference_state,
    update_regulatory_preferences,
)


def _regulation_signal_triplet(kind: str, step: int, rng: random.Random) -> tuple[float, float, float]:
    if kind == "clean":
        return 22.0, 86.0, 42.0
    if kind == "noisy":
        return (
            max(5.0, min(95.0, 30.0 + rng.uniform(-18, 18))),
            max(5.0, min(95.0, 75.0 + rng.uniform(-22, 22))),
            max(5.0, min(95.0, 50.0 + rng.uniform(-20, 20))),
        )
    if kind == "mixed-cause":
        return 21.0, 90.0, 45.0
    if kind == "delayed":
        return 20.0, 88.0, 43.0
    if kind == "context-shifting":
        if step % 2 == 0:
            return 18.0, 92.0, 38.0
        return 30.0, 70.0, 55.0
    if kind == "conflict-heavy":
        return 20.0, 89.0, 41.0
    return 24.0, 80.0, 50.0


def _run_regulation_soak(kind: str, *, seed: int, steps: int = 24) -> dict[str, object]:
    rng = random.Random(seed)
    preference_state = create_empty_preference_state()
    updates = 0
    freezes = 0
    conflicts = 0
    seen_options: set[AffordanceOptionClass] = set()
    max_entries = 0
    stale_triggered = False
    last_result = None

    for step in range(steps):
        energy, cognitive, safety = _regulation_signal_triplet(kind, step, rng)
        regulation_state = update_regulation_state(
            (
                NeedSignal(axis=NeedAxis.ENERGY, value=energy, source_ref=f"{kind}:{step}"),
                NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=cognitive, source_ref=f"{kind}:{step}"),
                NeedSignal(axis=NeedAxis.SAFETY, value=safety, source_ref=f"{kind}:{step}"),
            ),
            prior_state=None,
            context=RegulationContext(),
        ).state
        affordances = generate_regulation_affordances(
            regulation_state=regulation_state,
            capability_state=create_default_capability_state(),
        )
        if kind == "conflict-heavy":
            candidate = affordances.candidates[0]
        else:
            candidate = affordances.candidates[step % len(affordances.candidates)]
        seen_options.add(candidate.option_class)

        context_scope = ("ctx-a",) if kind == "context-shifting" and step % 2 == 0 else ("ctx-b",)
        short_delta = 0.7
        long_delta = 0.5
        mixed = False
        delayed_window_complete = True
        if kind == "noisy":
            short_delta = rng.uniform(-0.35, 0.45)
            long_delta = rng.uniform(-0.35, 0.45)
        elif kind == "mixed-cause":
            mixed = True
            short_delta = rng.uniform(0.1, 0.8)
            long_delta = rng.uniform(0.1, 0.8)
        elif kind == "delayed":
            short_delta = 0.35
            if step % 2 == 0:
                long_delta = None
                delayed_window_complete = False
            else:
                long_delta = 0.55
        elif kind == "conflict-heavy":
            sign = -1 if step % 2 else 1
            short_delta = 0.8 * sign
            long_delta = 0.6 * sign

        outcome_traces = ()
        if step % 7 == 6:
            outcome_traces = ()
        else:
            outcome_traces = (
                OutcomeTrace(
                    episode_id=f"{kind}-ep-{step}",
                    option_class_id=candidate.option_class,
                    affordance_id=candidate.affordance_id,
                    target_need_or_set=candidate.target_axes,
                    context_scope=context_scope,
                    observed_short_term_delta=short_delta,
                    observed_long_term_delta=long_delta,
                    attribution_confidence=RegulationConfidence.HIGH,
                    mixed_causes=mixed,
                    delayed_window_complete=delayed_window_complete,
                    observed_at_step=step + 1,
                ),
            )

        result = update_regulatory_preferences(
            regulation_state=regulation_state,
            affordance_result=affordances,
            outcome_traces=outcome_traces,
            preference_state=preference_state,
            context=PreferenceContext(
                decay_per_step=0.03,
                step_delta=1 if outcome_traces else 2,
                source_lineage=(kind,),
            ),
        )
        preference_state = result.updated_preference_state
        last_result = result
        max_entries = max(max_entries, len(preference_state.entries))
        stale_triggered = stale_triggered or any(entry.staleness_steps > 0 for entry in preference_state.entries)
        conflicts += len(preference_state.conflict_index)
        freezes += len(preference_state.frozen_updates)
        updates += sum(
            1
            for event in result.update_events
            if event.update_kind
            in {
                PreferenceUpdateKind.STRENGTHEN,
                PreferenceUpdateKind.WEAKEN,
                PreferenceUpdateKind.INVERT,
                PreferenceUpdateKind.CONFLICT_REGISTER,
            }
        )

    assert last_result is not None
    return {
        "updates": updates,
        "freezes": freezes,
        "conflicts": conflicts,
        "max_entries": max_entries,
        "stale_triggered": stale_triggered,
        "seen_options": seen_options,
        "last_result": last_result,
    }


def test_regulation_soak_holds_mode_specific_invariants() -> None:
    clean = _run_regulation_soak("clean", seed=11)
    noisy = _run_regulation_soak("noisy", seed=12)
    mixed = _run_regulation_soak("mixed-cause", seed=13)
    delayed = _run_regulation_soak("delayed", seed=14)
    context_shift = _run_regulation_soak("context-shifting", seed=15)
    conflict = _run_regulation_soak("conflict-heavy", seed=16)

    assert clean["updates"] > 0
    assert clean["freezes"] < clean["updates"]
    assert mixed["freezes"] > 0
    assert delayed["freezes"] > 0
    assert conflict["conflicts"] > 0
    assert context_shift["max_entries"] >= 2
    assert clean["max_entries"] <= 32
    assert noisy["max_entries"] <= 32
    assert clean["stale_triggered"] is True
    assert clean["last_result"].no_final_selection_performed is True
    assert noisy["last_result"].no_final_selection_performed is True


def test_language_soak_keeps_inspectability_under_clean_and_noisy_sequences() -> None:
    texts = (
        "alpha beta.",
        "alpha beta; gamma delta.",
        '"quoted alpha" beta',
        "we do not track alpha beta",
        "alpha beta ... gamma",
        "!!! ... ??",
        "(open parenthetical alpha",
        "we is ready.",
    )
    for idx, text in enumerate(texts):
        unit = ground_epistemic_input(
            InputMaterial(material_id=f"m-soak-lang-{idx}", content=text),
            SourceMetadata(
                source_id=f"user-soak-{idx}",
                source_class=SourceClass.REPORTER,
                modality=ModalityClass.USER_TEXT,
                confidence_hint=ConfidenceLevel.MEDIUM,
            ),
        )
        surface = build_utterance_surface(unit.unit)
        syntax = build_morphosyntax_candidate_space(surface)

        assert surface.surface.reversible_span_map_present is True
        assert surface.surface.tokens
        assert surface.surface.normalization_log
        assert syntax.hypothesis_set.no_selected_winner is True
        if syntax.hypothesis_set.hypotheses:
            first = syntax.hypothesis_set.hypotheses[0]
            assert first.token_features
            assert first.clause_graph.clauses
