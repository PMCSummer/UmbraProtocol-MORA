from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEpisodeRecordContext,
    LexicalEpisodeStatus,
    LexicalHypothesisStatus,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    consolidate_lexical_hypotheses,
    create_empty_lexicon_state,
    record_lexical_usage_episode,
)


def _episode(episode_id: str, *, label: str, anti: tuple[str, ...] = ()) -> LexicalUsageEpisode:
    return LexicalUsageEpisode(
        episode_id=episode_id,
        observed_surface_form="drift",
        observed_lemma_hint="drift",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.drift",
                sense_label=label,
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                compatibility_cues=("cue_a",),
                anti_cues=anti,
                confidence=0.72,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span="drift usage",
        confidence=0.72,
        evidence_quality=0.72,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )


def test_conflicting_episode_keeps_hypothesis_conflicted_or_frozen_not_silently_promoted() -> None:
    first = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-c1", label="drift_primary"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    second = record_lexical_usage_episode(
        lexicon_state=first.updated_state,
        episodes=(_episode("ep-c2", label="drift_alt", anti=("cue_a",)),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    hypothesis = second.updated_state.provisional_hypotheses[0]
    assert hypothesis.conflict_count >= 1
    assert hypothesis.status in {LexicalHypothesisStatus.CONFLICTED, LexicalHypothesisStatus.FROZEN}
    assert not hypothesis.promotion_eligibility
    assert "conflicting_episode" in hypothesis.blocked_reasons

    consolidated = consolidate_lexical_hypotheses(lexicon_state=second.updated_state)
    assert not consolidated.promoted_hypothesis_ids
    assert consolidated.downstream_gate.accepted is False


def test_role_hint_conflict_is_detected_without_cue_overlap() -> None:
    first = LexicalUsageEpisode(
        episode_id="ep-role-1",
        observed_surface_form="roleword",
        observed_lemma_hint="roleword",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.roleword",
                sense_label="roleword_sense",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.72,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span="role usage a",
        confidence=0.72,
        evidence_quality=0.72,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )
    second = LexicalUsageEpisode(
        episode_id="ep-role-2",
        observed_surface_form="roleword",
        observed_lemma_hint="roleword",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.roleword",
                sense_label="roleword_sense",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.72,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.OPERATOR,),
        usage_span="role usage b",
        confidence=0.72,
        evidence_quality=0.72,
        step_index=2,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )
    first_result = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(first,),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    second_result = record_lexical_usage_episode(
        lexicon_state=first_result.updated_state,
        episodes=(second,),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    hypothesis = second_result.updated_state.provisional_hypotheses[0]
    assert hypothesis.conflict_count >= 1
    assert hypothesis.status in {LexicalHypothesisStatus.CONFLICTED, LexicalHypothesisStatus.FROZEN}
