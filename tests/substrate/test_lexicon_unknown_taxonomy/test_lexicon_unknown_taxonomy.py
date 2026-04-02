from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEntryProposal,
    LexicalEpisodeStatus,
    LexicalSenseHypothesis,
    LexicalSenseStatus,
    LexicalUnknownClass,
    LexicalUsageEpisode,
    LexiconQueryContext,
    LexiconQueryRequest,
    UnknownLexicalObservation,
    create_empty_lexicon_state,
    create_or_update_lexicon_state,
    create_seed_lexicon_state,
    evaluate_lexicon_downstream_gate,
    query_lexical_entries,
    record_lexical_usage_episode,
)


def _unknown_classes_for(record) -> set[LexicalUnknownClass]:
    return {state.unknown_class for state in record.unknown_states}


def _record_by_form(result, form: str):
    return next(record for record in result.query_records if record.query_form == form)


def test_plain_no_match_defaults_to_unknown_word() -> None:
    result = query_lexical_entries(
        lexicon_state=create_empty_lexicon_state(),
        queries=(LexiconQueryRequest(surface_form="never-seen-lexeme", language_code="en"),),
    )
    record = result.query_records[0]
    assert record.matched_entry_ids == ()
    assert _unknown_classes_for(record) == {LexicalUnknownClass.UNKNOWN_WORD}
    assert record.dominant_unknown_class == LexicalUnknownClass.UNKNOWN_WORD
    assert record.hard_unknown_or_capped is True
    assert record.strong_lexical_claim_permitted is False
    assert "unknown_word" in result.downstream_gate.restrictions
    assert result.downstream_gate.accepted is False


def test_unknown_word_is_first_class_and_not_partial_hypothesis() -> None:
    updated = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="qzxv",
                occurrence_ref="occ-unknown-tax-1",
                partial_pos_hint="noun",
                confidence=0.2,
                provenance="test.unknown.taxonomy",
            ),
        ),
    )
    result = query_lexical_entries(
        lexicon_state=updated.updated_state,
        queries=(LexiconQueryRequest(surface_form="qzxv", language_code="en"),),
    )
    record = result.query_records[0]
    assert _unknown_classes_for(record) == {LexicalUnknownClass.UNKNOWN_WORD}
    assert record.dominant_unknown_class == LexicalUnknownClass.UNKNOWN_WORD
    assert record.hard_unknown_or_capped is True
    assert record.strong_lexical_claim_permitted is False
    assert "unknown_word" in result.downstream_gate.restrictions
    assert result.downstream_gate.accepted is False


def test_partial_lexical_hypothesis_is_distinct_from_unknown_word() -> None:
    episode = LexicalUsageEpisode(
        episode_id="ep-partial-tax-1",
        observed_surface_form="novum",
        observed_lemma_hint="novum",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.novum",
                sense_label="novum_entity",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.72,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span="novum usage",
        confidence=0.72,
        evidence_quality=0.74,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode.taxonomy",
    )
    recorded = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(episode,),
    )
    result = query_lexical_entries(
        lexicon_state=recorded.updated_state,
        queries=(LexiconQueryRequest(surface_form="novum", language_code="en"),),
    )
    record = result.query_records[0]
    assert _unknown_classes_for(record) == {LexicalUnknownClass.PARTIAL_LEXICAL_HYPOTHESIS}
    assert record.dominant_unknown_class == LexicalUnknownClass.PARTIAL_LEXICAL_HYPOTHESIS
    assert record.hard_unknown_or_capped is True
    assert record.strong_lexical_claim_permitted is False
    assert "partial_lexical_hypothesis" in result.downstream_gate.restrictions
    assert result.downstream_gate.accepted is False


def test_known_syntax_unknown_lexeme_is_distinct_from_generic_no_match() -> None:
    result = query_lexical_entries(
        lexicon_state=create_empty_lexicon_state(),
        queries=(LexiconQueryRequest(surface_form="slotx", language_code="en"),),
        context=LexiconQueryContext(syntax_known_lexical_gap_forms=("slotx",)),
    )
    record = result.query_records[0]
    assert _unknown_classes_for(record) == {LexicalUnknownClass.KNOWN_SYNTAX_UNKNOWN_LEXEME}
    assert record.dominant_unknown_class == LexicalUnknownClass.KNOWN_SYNTAX_UNKNOWN_LEXEME
    assert record.hard_unknown_or_capped is True
    assert record.strong_lexical_claim_permitted is False
    assert "known_syntax_unknown_lexeme" in result.downstream_gate.restrictions
    assert result.downstream_gate.accepted is False


def test_unknown_precedence_policy_is_explicit_and_dominant() -> None:
    base = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="slotz",
                occurrence_ref="occ-slotz-unknown",
                provenance="test.unknown.precedence",
            ),
        ),
    )
    with_partial = record_lexical_usage_episode(
        lexicon_state=base.updated_state,
        episodes=(
            LexicalUsageEpisode(
                episode_id="ep-slotz-partial",
                observed_surface_form="slotz",
                observed_lemma_hint="slotz",
                language_code="en",
                observed_context_keys=("turn",),
                source_kind="test",
                proposed_sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.slotz",
                        sense_label="slotz_entity",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.66,
                    ),
                ),
                proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
                usage_span="slotz usage",
                confidence=0.66,
                evidence_quality=0.7,
                step_index=1,
                episode_status=LexicalEpisodeStatus.RECORDED,
                provenance="test.unknown.precedence",
            ),
        ),
    )
    result = query_lexical_entries(
        lexicon_state=with_partial.updated_state,
        queries=(LexiconQueryRequest(surface_form="slotz", language_code="en"),),
        context=LexiconQueryContext(syntax_known_lexical_gap_forms=("slotz",)),
    )
    record = result.query_records[0]
    assert _unknown_classes_for(record) == {
        LexicalUnknownClass.KNOWN_SYNTAX_UNKNOWN_LEXEME,
        LexicalUnknownClass.PARTIAL_LEXICAL_HYPOTHESIS,
    }
    assert record.dominant_unknown_class == LexicalUnknownClass.KNOWN_SYNTAX_UNKNOWN_LEXEME
    assert record.hard_unknown_or_capped is True
    assert record.strong_lexical_claim_permitted is False


def test_known_lexeme_unknown_sense_in_context_caps_strong_claim() -> None:
    seeded = create_seed_lexicon_state()
    no_context = query_lexical_entries(
        lexicon_state=seeded,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
    )
    with_context = query_lexical_entries(
        lexicon_state=seeded,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
        context=LexiconQueryContext(context_keys=("sense_anchor",)),
    )

    no_ctx_record = no_context.query_records[0]
    assert _unknown_classes_for(no_ctx_record) == {
        LexicalUnknownClass.KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT
    }
    assert no_ctx_record.dominant_unknown_class == LexicalUnknownClass.KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT
    assert no_ctx_record.hard_unknown_or_capped is True
    assert no_ctx_record.strong_lexical_claim_permitted is False
    assert "known_lexeme_unknown_sense_in_context" in no_context.downstream_gate.restrictions
    assert no_context.downstream_gate.accepted is False

    with_ctx_record = with_context.query_records[0]
    assert LexicalUnknownClass.KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT not in _unknown_classes_for(
        with_ctx_record
    )
    assert with_ctx_record.hard_unknown_or_capped is False
    assert with_ctx_record.strong_lexical_claim_permitted is True
    assert with_context.downstream_gate.accepted is True


def test_known_lexeme_unknown_sense_requires_unresolved_sense_basis() -> None:
    updated = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(
            LexicalEntryProposal(
                surface_form="polyx",
                canonical_form="polyx",
                language_code="en",
                part_of_speech_candidates=("noun",),
                sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.polyx.finance",
                        sense_label="finance_polyx",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        compatibility_cues=("finance",),
                        confidence=0.82,
                        status_hint=LexicalSenseStatus.STABLE,
                    ),
                    LexicalSenseHypothesis(
                        sense_family="entity.polyx.geography",
                        sense_label="geo_polyx",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        compatibility_cues=("river",),
                        confidence=0.6,
                        status_hint=LexicalSenseStatus.STABLE,
                    ),
                ),
                confidence=0.82,
                entry_example_texts=("polyx usage with finance cue",),
                evidence_ref="test.polyx",
            ),
        ),
    )
    with_cue = query_lexical_entries(
        lexicon_state=updated.updated_state,
        queries=(LexiconQueryRequest(surface_form="polyx", language_code="en"),),
        context=LexiconQueryContext(context_keys=("finance",)),
    )
    record = with_cue.query_records[0]
    assert LexicalUnknownClass.KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT not in _unknown_classes_for(record)
    assert record.strong_lexical_claim_permitted is True
    assert with_cue.downstream_gate.accepted is True


def test_batched_query_preserves_per_record_unknown_hardness() -> None:
    result = query_lexical_entries(
        lexicon_state=create_seed_lexicon_state(),
        queries=(
            LexiconQueryRequest(surface_form="thing", language_code="en"),
            LexiconQueryRequest(surface_form="never-seen-batch", language_code="en"),
        ),
    )
    known_record = _record_by_form(result, "thing")
    unknown_record = _record_by_form(result, "never-seen-batch")

    assert result.downstream_gate.accepted is True
    assert known_record.strong_lexical_claim_permitted is True
    assert known_record.hard_unknown_or_capped is False
    assert unknown_record.strong_lexical_claim_permitted is False
    assert unknown_record.hard_unknown_or_capped is True
    assert unknown_record.dominant_unknown_class == LexicalUnknownClass.UNKNOWN_WORD


def test_unknown_taxonomy_query_gate_parity_on_mixed_batch() -> None:
    state = create_seed_lexicon_state()
    state = create_or_update_lexicon_state(
        lexicon_state=state,
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="ux",
                occurrence_ref="occ-ux",
                provenance="test.unknown.parity",
            ),
        ),
    ).updated_state
    state = record_lexical_usage_episode(
        lexicon_state=state,
        episodes=(
            LexicalUsageEpisode(
                episode_id="ep-hx",
                observed_surface_form="hx",
                observed_lemma_hint="hx",
                language_code="en",
                observed_context_keys=("turn",),
                source_kind="test",
                proposed_sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.hx",
                        sense_label="hx_entity",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.68,
                    ),
                ),
                proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
                usage_span="hx usage",
                confidence=0.68,
                evidence_quality=0.69,
                step_index=1,
                episode_status=LexicalEpisodeStatus.RECORDED,
                provenance="test.unknown.parity",
            ),
        ),
    ).updated_state
    result = query_lexical_entries(
        lexicon_state=state,
        queries=(
            LexiconQueryRequest(surface_form="ux", language_code="en"),
            LexiconQueryRequest(surface_form="hx", language_code="en"),
            LexiconQueryRequest(surface_form="slotx", language_code="en"),
            LexiconQueryRequest(surface_form="bank", language_code="en"),
            LexiconQueryRequest(surface_form="thing", language_code="en"),
        ),
        context=LexiconQueryContext(
            syntax_known_lexical_gap_forms=("slotx",),
        ),
    )
    canonical = evaluate_lexicon_downstream_gate(result)
    assert result.downstream_gate == canonical
