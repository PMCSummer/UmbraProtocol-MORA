from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEpisodeStatus,
    LexicalUnknownClass,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    LexiconQueryContext,
    LexiconQueryRequest,
    UnknownLexicalObservation,
    create_or_update_lexicon_state,
    create_seed_lexicon_state,
    persist_lexicon_result_via_f01,
    query_lexical_entries,
    reconstruct_lexicon_state_from_snapshot,
    record_lexical_usage_episode,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _boot_runtime():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-lex-unknown-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-05T00:00:00+00:00",
            event_id="ev-lex-unknown-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _unknown_class_map(result) -> dict[str, set[LexicalUnknownClass]]:
    return {
        record.query_form: {state.unknown_class for state in record.unknown_states}
        for record in result.query_records
    }


def _hardness_map(result) -> dict[str, tuple[bool, bool, LexicalUnknownClass | None]]:
    return {
        record.query_form: (
            record.hard_unknown_or_capped,
            record.strong_lexical_claim_permitted,
            record.dominant_unknown_class,
        )
        for record in result.query_records
    }


def test_unknown_taxonomy_survives_roundtrip_and_continue_equivalence() -> None:
    seeded = create_seed_lexicon_state()
    with_unknown = create_or_update_lexicon_state(
        lexicon_state=seeded,
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="qzxv",
                occurrence_ref="occ-unknown-roundtrip-1",
                partial_pos_hint="noun",
                confidence=0.2,
                provenance="test.roundtrip",
            ),
        ),
    )
    with_partial_hypothesis = record_lexical_usage_episode(
        lexicon_state=with_unknown.updated_state,
        episodes=(
            LexicalUsageEpisode(
                episode_id="ep-roundtrip-partial-1",
                observed_surface_form="protox",
                observed_lemma_hint="protox",
                language_code="en",
                observed_context_keys=("turn",),
                source_kind="test",
                proposed_sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.protox",
                        sense_label="protox_entity",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.7,
                    ),
                ),
                proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
                usage_span="protox usage",
                confidence=0.7,
                evidence_quality=0.72,
                step_index=1,
                episode_status=LexicalEpisodeStatus.RECORDED,
                provenance="test.roundtrip",
            ),
        ),
    )
    requests = (
        LexiconQueryRequest(surface_form="qzxv", language_code="en"),
        LexiconQueryRequest(surface_form="protox", language_code="en"),
        LexiconQueryRequest(surface_form="slotx", language_code="en"),
        LexiconQueryRequest(surface_form="bank", language_code="en"),
    )
    context = LexiconQueryContext(syntax_known_lexical_gap_forms=("slotx",))
    uninterrupted = query_lexical_entries(
        lexicon_state=with_partial_hypothesis.updated_state,
        queries=requests,
        context=context,
    )

    runtime = _boot_runtime()
    persisted = persist_lexicon_result_via_f01(
        result=uninterrupted,
        runtime_state=runtime,
        transition_id="tr-lex-unknown-roundtrip-1",
        requested_at="2026-04-05T00:05:00+00:00",
    )
    snapshot = persisted.state.trace.events[-1].payload["lexicon_snapshot"]
    assert snapshot["query_records"]
    assert any(record["unknown_states"] for record in snapshot["query_records"])
    assert all("hard_unknown_or_capped" in record for record in snapshot["query_records"])
    assert all("strong_lexical_claim_permitted" in record for record in snapshot["query_records"])
    assert all("dominant_unknown_class" in record for record in snapshot["query_records"])
    reconstructed = reconstruct_lexicon_state_from_snapshot(snapshot)
    continued = query_lexical_entries(
        lexicon_state=reconstructed,
        queries=requests,
        context=context,
    )

    assert _unknown_class_map(uninterrupted) == _unknown_class_map(continued)
    assert _hardness_map(uninterrupted) == _hardness_map(continued)
    assert "known_lexeme_unknown_sense_in_context" in continued.downstream_gate.restrictions
    assert "partial_lexical_hypothesis" in continued.downstream_gate.restrictions
    assert "known_syntax_unknown_lexeme" in continued.downstream_gate.restrictions
    assert "unknown_word" in continued.downstream_gate.restrictions
    assert continued.downstream_gate.accepted is False
