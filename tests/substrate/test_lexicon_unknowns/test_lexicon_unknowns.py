from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalEntryProposal,
    LexicalUnknownClass,
    LexicalSenseHypothesis,
    LexiconQueryRequest,
    UnknownLexicalObservation,
    create_or_update_lexicon_state,
    create_seed_lexicon_state,
    query_lexical_entries,
)


def test_unknown_lexical_item_kept_as_unknown_not_forced_match() -> None:
    seeded = create_seed_lexicon_state()
    updated = create_or_update_lexicon_state(
        lexicon_state=seeded,
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="qzxv",
                occurrence_ref="occ-unknown-1",
                partial_pos_hint="noun",
                confidence=0.15,
                provenance="test.unknown",
            ),
        ),
    )
    queried = query_lexical_entries(
        lexicon_state=updated.updated_state,
        queries=(LexiconQueryRequest(surface_form="qzxv", language_code="en"),),
    )
    record = queried.query_records[0]
    assert not record.matched_entry_ids
    assert record.unknown_item_ids
    assert "unknown_lexical_item" in record.ambiguity_reasons
    assert {state.unknown_class for state in record.unknown_states} == {
        LexicalUnknownClass.UNKNOWN_WORD
    }


def test_unknown_path_carries_partial_hint_but_no_strong_meaning_claim() -> None:
    seeded = create_seed_lexicon_state()
    updated = create_or_update_lexicon_state(
        lexicon_state=seeded,
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="zint",
                occurrence_ref="occ-unknown-2",
                partial_pos_hint="verb",
                confidence=0.22,
                provenance="test.unknown",
            ),
        ),
    )
    unknown = updated.updated_state.unknown_items[-1]
    assert unknown.surface_form == "zint"
    assert unknown.partial_pos_hint == "verb"
    assert unknown.no_strong_meaning_claim is True
    assert updated.no_final_meaning_resolution_performed is True


def test_negative_control_fake_match_changes_unknown_behavior() -> None:
    seeded = create_seed_lexicon_state()
    baseline = query_lexical_entries(
        lexicon_state=seeded,
        queries=(LexiconQueryRequest(surface_form="blarf", language_code="en"),),
    )
    assert not baseline.query_records[0].matched_entry_ids

    fabricated = create_or_update_lexicon_state(
        lexicon_state=seeded,
        entry_proposals=(
            LexicalEntryProposal(
                surface_form="blarf",
                canonical_form="blarf",
                language_code="en",
                part_of_speech_candidates=("noun",),
                sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.synthetic",
                        sense_label="fabricated",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.6,
                    ),
                ),
                confidence=0.6,
                evidence_ref="test.synthetic",
            ),
        ),
    )
    after = query_lexical_entries(
        lexicon_state=fabricated.updated_state,
        queries=(LexiconQueryRequest(surface_form="blarf", language_code="en"),),
    )
    assert after.query_records[0].matched_entry_ids
