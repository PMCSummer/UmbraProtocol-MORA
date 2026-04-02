from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEpisodeRecordContext,
    LexicalEpisodeStatus,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    LexiconQueryRequest,
    create_empty_lexicon_state,
    evaluate_lexical_learning_downstream_gate,
    query_lexical_entries,
    record_lexical_usage_episode,
)


def _episode(episode_id: str, *, surface: str) -> LexicalUsageEpisode:
    return LexicalUsageEpisode(
        episode_id=episode_id,
        observed_surface_form=surface,
        observed_lemma_hint=surface,
        language_code="en",
        observed_context_keys=("ctx",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family=f"entity.{surface}",
                sense_label=f"{surface}_sense",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.72,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span=f"{surface} sample",
        confidence=0.72,
        evidence_quality=0.72,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )


def test_learning_gate_distinguishes_provisional_vs_promotion_eligible() -> None:
    first = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-ds-1", surface="proto"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.65),
    )
    assert first.downstream_gate.accepted is False
    assert "single_episode_only" in first.downstream_gate.restrictions

    second = record_lexical_usage_episode(
        lexicon_state=first.updated_state,
        episodes=(_episode("ep-ds-2", surface="proto"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.65),
    )
    gate = evaluate_lexical_learning_downstream_gate(second.updated_state)
    assert gate.accepted is True
    assert gate.accepted_hypothesis_ids


def test_query_reflects_learning_provisionality_markers() -> None:
    learned = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-q-1", surface="qform"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=3, promotion_confidence_threshold=0.9),
    )
    queried = query_lexical_entries(
        lexicon_state=learned.updated_state,
        queries=(LexiconQueryRequest(surface_form="qform", language_code="en"),),
    )
    record = queried.query_records[0]
    assert "learning_hypotheses_present" in record.ambiguity_reasons
    assert "learning_hypothesis_provisional" in record.ambiguity_reasons
