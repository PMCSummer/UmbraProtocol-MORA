from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalSenseHypothesis,
    LexicalUnknownClass,
    LexicalEpisodeRecordContext,
    LexicalEpisodeStatus,
    LexicalUsageEpisode,
    create_empty_lexicon_state,
    query_lexical_entries,
    LexiconQueryRequest,
    record_lexical_usage_episode,
)


def test_weak_episode_yields_insufficient_evidence_path() -> None:
    weak_episode = LexicalUsageEpisode(
        episode_id="ep-weak-1",
        observed_surface_form="",
        observed_lemma_hint=None,
        language_code="en",
        observed_context_keys=(),
        source_kind="test",
        proposed_sense_hypotheses=(),
        proposed_role_hints=(LexicalCompositionRole.UNKNOWN,),
        usage_span=None,
        confidence=0.1,
        evidence_quality=0.1,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )
    result = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(weak_episode,),
        context=LexicalEpisodeRecordContext(min_episode_confidence=0.35, min_episode_evidence_quality=0.35),
    )
    assert not result.recorded_episode_ids
    assert result.blocked_episode_ids == ("ep-weak-1",)
    assert result.updated_state.usage_episodes[-1].episode_status == LexicalEpisodeStatus.INSUFFICIENT_EVIDENCE
    assert result.telemetry.insufficient_episode_count == 1
    assert result.downstream_gate.accepted is False


def test_partial_hypothesis_exposed_as_unknown_class_not_stable_lexical_claim() -> None:
    episode = LexicalUsageEpisode(
        episode_id="ep-partial-unknowns-1",
        observed_surface_form="protoz",
        observed_lemma_hint="protoz",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.protoz",
                sense_label="protoz_entity",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.66,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.UNKNOWN,),
        usage_span="protoz usage",
        confidence=0.66,
        evidence_quality=0.67,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )
    recorded = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(episode,),
    )
    queried = query_lexical_entries(
        lexicon_state=recorded.updated_state,
        queries=(LexiconQueryRequest(surface_form="protoz", language_code="en"),),
    )
    record = queried.query_records[0]
    assert {state.unknown_class for state in record.unknown_states} == {
        LexicalUnknownClass.PARTIAL_LEXICAL_HYPOTHESIS
    }
    assert queried.downstream_gate.accepted is False
