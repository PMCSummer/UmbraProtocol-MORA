from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalEntryProposal,
    LexicalSenseHypothesis,
    LexiconQueryRequest,
    LexiconUpdateContext,
    LexiconUpdateKind,
    create_empty_lexicon_state,
    create_or_update_lexicon_state,
    evaluate_lexicon_downstream_gate,
    query_lexical_entries,
)


def _proposal(label: str, conflict_hint: bool, evidence_ref: str) -> LexicalEntryProposal:
    return LexicalEntryProposal(
        surface_form="delta",
        canonical_form="delta",
        language_code="en",
        part_of_speech_candidates=("noun",),
        sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.delta",
                sense_label=label,
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                compatibility_cues=("cue_a",),
                anti_cues=("cue_b",) if conflict_hint else (),
                confidence=0.7,
                provisional=True,
            ),
        ),
        confidence=0.7,
        conflict_hint=conflict_hint,
        evidence_ref=evidence_ref,
    )


def test_conflicting_evidence_is_explicit_and_can_freeze_update() -> None:
    state = create_empty_lexicon_state()
    first = create_or_update_lexicon_state(
        lexicon_state=state,
        entry_proposals=(_proposal("sense_a", False, "ev-c1"),),
    )
    second = create_or_update_lexicon_state(
        lexicon_state=first.updated_state,
        entry_proposals=(_proposal("sense_b", True, "ev-c2"),),
        context=LexiconUpdateContext(freeze_on_conflict=True),
    )
    assert second.updated_state.conflict_index
    assert second.blocked_updates
    assert any(update.frozen for update in second.blocked_updates)
    assert any(event.update_kind == LexiconUpdateKind.REGISTER_CONFLICT for event in second.update_events)
    assert "conflict_entries_present" in second.downstream_gate.restrictions


def test_conflicted_query_matches_do_not_stay_accepted() -> None:
    state = create_empty_lexicon_state()
    first = create_or_update_lexicon_state(
        lexicon_state=state,
        entry_proposals=(_proposal("sense_a", False, "ev-q1"),),
    )
    frozen = create_or_update_lexicon_state(
        lexicon_state=first.updated_state,
        entry_proposals=(_proposal("sense_b", True, "ev-q2"),),
        context=LexiconUpdateContext(freeze_on_conflict=True),
    )
    assert frozen.updated_state.entries

    query_result = query_lexical_entries(
        lexicon_state=frozen.updated_state,
        queries=(LexiconQueryRequest(surface_form="delta", language_code="en"),),
    )
    assert query_result.query_records
    assert query_result.downstream_gate.accepted is False
    assert query_result.downstream_gate.rejected_entry_ids
    assert "conflicted_or_frozen_entry_present" in query_result.downstream_gate.restrictions

    canonical_gate = evaluate_lexicon_downstream_gate(query_result)
    assert canonical_gate.accepted is False
    assert canonical_gate.rejected_entry_ids
