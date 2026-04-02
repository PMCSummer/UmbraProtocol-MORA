from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEpisodeRecordContext,
    LexicalEpisodeStatus,
    LexicalHypothesisConsolidationContext,
    LexicalHypothesisStatus,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    consolidate_lexical_hypotheses,
    create_empty_lexicon_state,
    record_lexical_usage_episode,
)


def _episode(
    episode_id: str,
    *,
    surface: str,
    sense_label: str,
    confidence: float = 0.72,
    evidence_quality: float = 0.74,
) -> LexicalUsageEpisode:
    return LexicalUsageEpisode(
        episode_id=episode_id,
        observed_surface_form=surface,
        observed_lemma_hint=surface,
        language_code="en",
        observed_context_keys=("utterance",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family=f"entity.{surface}",
                sense_label=sense_label,
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=confidence,
                provisional=True,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span=f"... {surface} ...",
        confidence=confidence,
        evidence_quality=evidence_quality,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )


def test_single_episode_creates_provisional_hypothesis_not_stable_truth() -> None:
    state = create_empty_lexicon_state()
    recorded = record_lexical_usage_episode(
        lexicon_state=state,
        episodes=(_episode("ep-1", surface="glim", sense_label="glim_entity"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.65),
    )
    assert recorded.recorded_episode_ids == ("ep-1",)
    assert not recorded.blocked_episode_ids
    assert len(recorded.updated_state.provisional_hypotheses) == 1
    hypothesis = recorded.updated_state.provisional_hypotheses[0]
    assert hypothesis.status == LexicalHypothesisStatus.PROVISIONAL
    assert hypothesis.support_count == 1
    assert not hypothesis.promotion_eligibility
    assert not recorded.updated_state.entries
    assert recorded.no_final_meaning_resolution_performed is True


def test_single_episode_not_promotion_eligible_even_if_context_threshold_is_one() -> None:
    recorded = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-1b", surface="mono", sense_label="mono_entity"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=1, promotion_confidence_threshold=0.1),
    )
    hypothesis = recorded.updated_state.provisional_hypotheses[0]
    assert hypothesis.support_count == 1
    assert hypothesis.status == LexicalHypothesisStatus.PROVISIONAL
    assert hypothesis.promotion_eligibility is False


def test_repeated_compatible_episodes_enable_promotion_and_stable_entry_creation() -> None:
    first = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-a", surface="vex", sense_label="vex_entity"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.65),
    )
    second = record_lexical_usage_episode(
        lexicon_state=first.updated_state,
        episodes=(_episode("ep-b", surface="vex", sense_label="vex_entity"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.65),
    )
    hypothesis = second.updated_state.provisional_hypotheses[0]
    assert hypothesis.support_count >= 2
    assert hypothesis.status == LexicalHypothesisStatus.PROMOTION_ELIGIBLE
    assert hypothesis.promotion_eligibility is True

    consolidated = consolidate_lexical_hypotheses(
        lexicon_state=second.updated_state,
        context=LexicalHypothesisConsolidationContext(
            min_support_for_promotion=2,
            promotion_confidence_threshold=0.65,
        ),
    )
    assert consolidated.promoted_hypothesis_ids
    promoted = consolidated.updated_state.provisional_hypotheses[0]
    assert promoted.status == LexicalHypothesisStatus.STABLE_PROMOTED
    assert promoted.promoted_entry_id is not None
    assert consolidated.updated_state.entries
    assert any(entry.canonical_form == "vex" for entry in consolidated.updated_state.entries)
