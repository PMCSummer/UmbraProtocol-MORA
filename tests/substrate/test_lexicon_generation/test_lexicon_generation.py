from substrate.lexicon import (
    LexicalAcquisitionStatus,
    LexicalCoarseSemanticType,
    LexicalCompositionProfile,
    LexicalCompositionRole,
    LexicalEntryProposal,
    LexicalSenseHypothesis,
    LexiconUpdateContext,
    LexiconUpdateKind,
    create_empty_lexicon_state,
    create_or_update_lexicon_state,
    create_seed_lexicon_state,
)


def _proposal(surface: str, evidence_ref: str) -> LexicalEntryProposal:
    return LexicalEntryProposal(
        surface_form=surface,
        canonical_form=surface,
        language_code="en",
        part_of_speech_candidates=("noun",),
        sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.test",
                sense_label=f"{surface}_sense",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.82,
                provisional=True,
            ),
        ),
        composition_profile=LexicalCompositionProfile(
            role_hints=(LexicalCompositionRole.PARTICIPANT,),
            argument_structure_hints=(),
            can_introduce_predicate_frame=False,
            behaves_as_modifier=False,
            behaves_as_operator=False,
            behaves_as_participant=True,
            behaves_as_referential_carrier=False,
            scope_sensitive=False,
            negation_sensitive=False,
            remains_underspecified=True,
        ),
        confidence=0.82,
        evidence_ref=evidence_ref,
    )


def test_entry_creation_and_stable_transition_from_repeated_evidence() -> None:
    state = create_empty_lexicon_state()
    context = LexiconUpdateContext(min_evidence_for_stable=2, stable_confidence_threshold=0.7)

    first = create_or_update_lexicon_state(
        lexicon_state=state,
        entry_proposals=(_proposal("glim", "ev-1"),),
        context=context,
    )
    assert len(first.updated_state.entries) == 1
    created = first.updated_state.entries[0]
    assert created.acquisition_state.status == LexicalAcquisitionStatus.PROVISIONAL
    assert first.no_final_meaning_resolution_performed is True
    assert first.telemetry.new_entry_count == 1

    second = create_or_update_lexicon_state(
        lexicon_state=first.updated_state,
        entry_proposals=(_proposal("glim", "ev-2"),),
        context=context,
    )
    updated = second.updated_state.entries[0]
    assert updated.acquisition_state.evidence_count >= 2
    assert updated.acquisition_state.status == LexicalAcquisitionStatus.STABLE
    assert second.telemetry.updated_entry_count >= 1


def test_incompatible_version_blocks_update_with_frozen_path() -> None:
    state = create_empty_lexicon_state()
    result = create_or_update_lexicon_state(
        lexicon_state=state,
        entry_proposals=(_proposal("drim", "ev-x"),),
        context=LexiconUpdateContext(expected_schema_version="lexicon.schema.v999"),
    )
    assert result.abstain is True
    assert result.blocked_updates
    assert any(block.frozen for block in result.blocked_updates)
    assert "compatibility_mismatch" in result.downstream_gate.restrictions
    assert "schema_version_mismatch" in result.telemetry.compatibility_markers


def test_multi_match_update_freezes_instead_of_forced_winner_selection() -> None:
    state = create_seed_lexicon_state()
    ambiguous = LexicalEntryProposal(
        surface_form="can",
        canonical_form="can",
        language_code="en",
        part_of_speech_candidates=("noun", "modal"),
        sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="ambiguous.can",
                sense_label="ambiguous_can",
                coarse_semantic_type=LexicalCoarseSemanticType.UNKNOWN,
                confidence=0.6,
            ),
        ),
        confidence=0.6,
        evidence_ref="ev-ambiguous-can",
    )
    result = create_or_update_lexicon_state(
        lexicon_state=state,
        entry_proposals=(ambiguous,),
    )
    assert any("ambiguous update target blocked" in block.reason for block in result.blocked_updates)
    assert any(block.frozen for block in result.blocked_updates)
    assert any(event.update_kind == LexiconUpdateKind.FREEZE_UPDATE for event in result.update_events)
    assert result.telemetry.updated_entry_count == 0
    assert result.telemetry.new_entry_count == 0
