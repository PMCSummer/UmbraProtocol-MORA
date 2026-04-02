from substrate.lexicon import (
    LexicalCompositionRole,
    LexicalEpisodeRecordContext,
    LexicalEpisodeStatus,
    LexicalUsageEpisode,
    create_empty_lexicon_state,
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
