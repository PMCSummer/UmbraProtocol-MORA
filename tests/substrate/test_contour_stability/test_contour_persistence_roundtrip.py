from dataclasses import replace

from substrate.affordances import AffordanceOptionClass, create_default_capability_state, generate_regulation_affordances
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface, persist_surface_result_via_f01
from substrate.language_surface.models import (
    AlternativeSegmentation,
    AmbiguityKind,
    InsertionKind,
    InsertionSpan,
    NormalizationRecord,
    QuoteKind,
    QuotedSpan,
    RawSpan,
    SegmentAnchor,
    SegmentKind,
    SurfaceAmbiguity,
    TokenAnchor,
    TokenKind,
    UtteranceSurface,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space, persist_syntax_result_via_f01
from substrate.regulation import NeedAxis, NeedSignal, RegulationConfidence, RegulationContext, update_regulation_state
from substrate.regulatory_preferences import (
    BlockedPreferenceUpdate,
    OutcomeTrace,
    PreferenceConflictState,
    PreferenceContext,
    PreferenceEntry,
    PreferenceSign,
    PreferenceState,
    PreferenceTimeHorizon,
    PreferenceUncertainty,
    PreferenceUpdateStatus,
    persist_preference_result_via_f01,
    update_regulatory_preferences,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-contour-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-contour-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _reconstruct_preference_state(snapshot: dict[str, object]) -> PreferenceState:
    state = snapshot["preference_state"]
    entries = tuple(
        PreferenceEntry(
            entry_id=item["entry_id"],
            option_class_id=next(option for option in AffordanceOptionClass if option.value == item["option_class_id"]),
            target_need_or_set=tuple(
                next(axis for axis in NeedAxis if axis.value == axis_value)
                for axis_value in item["target_need_or_set"]
            ),
            preference_sign=next(sign for sign in PreferenceSign if sign.value == item["preference_sign"]),
            preference_strength=item["preference_strength"],
            expected_short_term_delta=item["expected_short_term_delta"],
            expected_long_term_delta=item["expected_long_term_delta"],
            confidence=next(level for level in RegulationConfidence if level.value == item["confidence"]),
            context_scope=tuple(item["context_scope"]),
            time_horizon=next(h for h in PreferenceTimeHorizon if h.value == item["time_horizon"]),
            conflict_state=next(c for c in PreferenceConflictState if c.value == item["conflict_state"]),
            episode_support=item["episode_support"],
            staleness_steps=item["staleness_steps"],
            decay_marker=item["decay_marker"],
            last_update_provenance=item["last_update_provenance"],
            update_status=next(s for s in PreferenceUpdateStatus if s.value == item["update_status"]),
        )
        for item in state["entries"]
    )
    unresolved = tuple(
        BlockedPreferenceUpdate(
            episode_id=item["episode_id"],
            option_class_id=(
                next(option for option in AffordanceOptionClass if option.value == item["option_class_id"])
                if item["option_class_id"] is not None
                else None
            ),
            uncertainty=next(u for u in PreferenceUncertainty if u.value == item["uncertainty"]),
            reason=item["reason"],
            frozen=item["frozen"],
            provenance=item["provenance"],
        )
        for item in state["unresolved_updates"]
    )
    frozen = tuple(block for block in unresolved if block.frozen)
    return PreferenceState(
        entries=entries,
        unresolved_updates=unresolved,
        conflict_index=tuple(state["conflict_index"]),
        frozen_updates=frozen,
        schema_version=state["schema_version"],
        taxonomy_version=state["taxonomy_version"],
        measurement_version=state["measurement_version"],
        last_updated_step=state["last_updated_step"],
    )


def _reconstruct_surface(snapshot: dict[str, object]) -> UtteranceSurface:
    surface = snapshot["surface"]
    tokens = tuple(
        TokenAnchor(
            token_id=item["token_id"],
            raw_span=RawSpan(start=item["span"][0], end=item["span"][1], raw_text=item["raw_text"]),
            raw_text=item["raw_text"],
            normalized_text=item["normalized_text"],
            token_kind=next(kind for kind in TokenKind if kind.value == item["token_kind"]),
            confidence=item["confidence"],
        )
        for item in surface["tokens"]
    )
    segments = tuple(
        SegmentAnchor(
            segment_id=item["segment_id"],
            raw_span=RawSpan(start=item["span"][0], end=item["span"][1], raw_text=surface["raw_text"][item["span"][0]:item["span"][1]]),
            segment_kind=next(kind for kind in SegmentKind if kind.value == item["segment_kind"]),
            token_ids=tuple(item["token_ids"]),
            confidence=item["confidence"],
        )
        for item in surface["segments"]
    )
    quotes = tuple(
        QuotedSpan(
            raw_span=RawSpan(start=item["span"][0], end=item["span"][1], raw_text=item["raw_text"]),
            quote_kind=next(kind for kind in QuoteKind if kind.value == item["quote_kind"]),
            confidence=item["confidence"],
        )
        for item in surface["quotes"]
    )
    insertions = tuple(
        InsertionSpan(
            raw_span=RawSpan(start=item["span"][0], end=item["span"][1], raw_text=item["raw_text"]),
            insertion_kind=next(kind for kind in InsertionKind if kind.value == item["insertion_kind"]),
            confidence=item["confidence"],
        )
        for item in surface["insertions"]
    )
    normalization = tuple(
        NormalizationRecord(
            op_name=item["op_name"],
            input_span_ref=item["input_span_ref"],
            before=item["before"],
            after=item["after"],
            reversible=item["reversible"],
            provenance=item["provenance"],
        )
        for item in surface["normalization_log"]
    )
    ambiguities = tuple(
        SurfaceAmbiguity(
            ambiguity_kind=next(kind for kind in AmbiguityKind if kind.value == item["ambiguity_kind"]),
            affected_span=RawSpan(start=item["span"][0], end=item["span"][1], raw_text=item["raw_text"]),
            alternatives_ref=tuple(item["alternatives_ref"]),
            confidence=item["confidence"],
            reason=item["reason"],
        )
        for item in surface["ambiguities"]
    )
    alternatives = tuple(
        AlternativeSegmentation(
            alternative_id=item["alternative_id"],
            segments=tuple(
                SegmentAnchor(
                    segment_id=seg["segment_id"],
                    raw_span=RawSpan(start=seg["span"][0], end=seg["span"][1], raw_text=surface["raw_text"][seg["span"][0]:seg["span"][1]]),
                    segment_kind=next(kind for kind in SegmentKind if kind.value == seg["segment_kind"]),
                    token_ids=tuple(seg["token_ids"]),
                    confidence=seg["confidence"],
                )
                for seg in item["segments"]
            ),
            confidence=item["confidence"],
            reason=item["reason"],
        )
        for item in surface["alternative_segmentations"]
    )
    return UtteranceSurface(
        epistemic_unit_ref=surface["epistemic_unit_ref"],
        raw_text=surface["raw_text"],
        tokens=tokens,
        segments=segments,
        quotes=quotes,
        insertions=insertions,
        normalization_log=normalization,
        ambiguities=ambiguities,
        alternative_segmentations=alternatives,
        reversible_span_map_present=surface["reversible_span_map_present"],
    )


def _regulation_pipeline():
    unit = ground_epistemic_input(
        InputMaterial(material_id="m-roundtrip-reg", content="reg signal"),
        SourceMetadata(
            source_id="sensor-roundtrip-reg",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.HIGH,
        ),
    )
    regulation_state = update_regulation_state(
        (
            NeedSignal(axis=NeedAxis.ENERGY, value=20.0, source_ref=unit.unit.unit_id),
            NeedSignal(axis=NeedAxis.COGNITIVE_LOAD, value=90.0, source_ref=unit.unit.unit_id),
            NeedSignal(axis=NeedAxis.SAFETY, value=40.0, source_ref=unit.unit.unit_id),
        ),
        prior_state=None,
        context=RegulationContext(source_lineage=(unit.unit.unit_id,)),
    ).state
    affordances = generate_regulation_affordances(
        regulation_state=regulation_state,
        capability_state=create_default_capability_state(),
    )
    return regulation_state, affordances, unit.unit.unit_id


def test_regulation_roundtrip_continuation_matches_non_interrupted_run() -> None:
    runtime = _bootstrapped_state()
    regulation_state, affordances, lineage = _regulation_pipeline()
    candidate = affordances.candidates[0]
    context = PreferenceContext(source_lineage=(lineage,), decay_per_step=0.0)

    step1 = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(
            OutcomeTrace(
                episode_id="ep-round-1",
                option_class_id=candidate.option_class,
                affordance_id=candidate.affordance_id,
                target_need_or_set=candidate.target_axes,
                context_scope=("rt",),
                observed_short_term_delta=0.7,
                observed_long_term_delta=0.5,
                attribution_confidence=RegulationConfidence.HIGH,
                observed_at_step=1,
            ),
        ),
        context=context,
    )
    persisted = persist_preference_result_via_f01(
        result=step1,
        runtime_state=runtime,
        transition_id="tr-roundtrip-reg-step1",
        requested_at="2026-04-02T00:05:00+00:00",
    )
    reconstructed_state = _reconstruct_preference_state(
        persisted.state.trace.events[-1].payload["preference_snapshot"]
    )

    outcome2 = OutcomeTrace(
        episode_id="ep-round-2",
        option_class_id=candidate.option_class,
        affordance_id=candidate.affordance_id,
        target_need_or_set=candidate.target_axes,
        context_scope=("rt",),
        observed_short_term_delta=0.75,
        observed_long_term_delta=0.55,
        attribution_confidence=RegulationConfidence.HIGH,
        observed_at_step=2,
    )
    uninterrupted = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(outcome2,),
        preference_state=step1.updated_preference_state,
        context=context,
    )
    roundtrip = update_regulatory_preferences(
        regulation_state=regulation_state,
        affordance_result=affordances,
        outcome_traces=(outcome2,),
        preference_state=reconstructed_state,
        context=context,
    )

    u = uninterrupted.updated_preference_state.entries[0]
    r = roundtrip.updated_preference_state.entries[0]
    assert (u.option_class_id, u.context_scope, u.preference_sign, round(u.preference_strength, 4)) == (
        r.option_class_id,
        r.context_scope,
        r.preference_sign,
        round(r.preference_strength, 4),
    )
    assert uninterrupted.telemetry.source_lineage == roundtrip.telemetry.source_lineage


def test_language_roundtrip_continuation_matches_non_interrupted_run() -> None:
    runtime = _bootstrapped_state()
    unit = ground_epistemic_input(
        InputMaterial(material_id="m-roundtrip-lang", content='("alpha") we do not track beta ... gamma'),
        SourceMetadata(
            source_id="user-roundtrip-lang",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(unit.unit)
    syntax_direct = build_morphosyntax_candidate_space(surface)

    persisted_surface = persist_surface_result_via_f01(
        result=surface,
        runtime_state=runtime,
        transition_id="tr-roundtrip-lang-surface",
        requested_at="2026-04-02T00:06:00+00:00",
    )
    restored_surface = _reconstruct_surface(
        persisted_surface.state.trace.events[-1].payload["surface_snapshot"]
    )
    syntax_from_restored = build_morphosyntax_candidate_space(restored_surface)

    assert syntax_direct.hypothesis_set.no_selected_winner is True
    assert syntax_from_restored.hypothesis_set.no_selected_winner is True
    assert syntax_direct.telemetry.clause_count == syntax_from_restored.telemetry.clause_count
    assert (
        syntax_direct.telemetry.unresolved_edge_count
        == syntax_from_restored.telemetry.unresolved_edge_count
    )
    assert (
        syntax_direct.telemetry.negation_carrier_count
        == syntax_from_restored.telemetry.negation_carrier_count
    )

    persisted_syntax = persist_syntax_result_via_f01(
        result=syntax_from_restored,
        runtime_state=persisted_surface.state,
        transition_id="tr-roundtrip-lang-syntax",
        requested_at="2026-04-02T00:07:00+00:00",
    )
    snapshot = persisted_syntax.state.trace.events[-1].payload["syntax_snapshot"]
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["hypothesis_set"]["source_surface_ref"] == restored_surface.epistemic_unit_ref
