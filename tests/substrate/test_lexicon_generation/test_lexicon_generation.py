from substrate.lexicon import (
    LexicalAcquisitionStatus,
    LexicalCoarseSemanticType,
    LexicalCompositionProfile,
    LexicalCompositionRole,
    LexicalEntryProposal,
    LexicalSenseHypothesis,
    LexicalSenseStatus,
    LexiconQueryRequest,
    LexiconUpdateContext,
    LexiconUpdateKind,
    create_empty_lexicon_state,
    create_or_update_lexicon_state,
    create_seed_lexicon_state,
    query_lexical_entries,
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


def test_typed_examples_are_attached_to_entry_and_sense() -> None:
    proposal = LexicalEntryProposal(
        surface_form="lumen",
        canonical_form="lumen",
        language_code="en",
        part_of_speech_candidates=("noun",),
        sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.light",
                sense_label="light_unit",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.74,
                example_texts=("the lumen value increased",),
            ),
        ),
        entry_example_texts=("lumen appears in specs",),
        confidence=0.74,
        evidence_ref="ev-examples-1",
    )
    result = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(proposal,),
    )
    assert result.updated_state.entries
    entry = result.updated_state.entries[0]
    assert entry.examples
    assert all(example.linked_entry_id == entry.entry_id for example in entry.examples)
    linked_sense_ids = {example.linked_sense_id for example in entry.examples if example.linked_sense_id}
    assert linked_sense_ids
    assert any(sense.example_ids for sense in entry.sense_records)


def test_examples_are_runtime_load_bearing_for_non_stable_entry_claim_strength() -> None:
    without_examples = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(
            LexicalEntryProposal(
                surface_form="kappa",
                canonical_form="kappa",
                language_code="en",
                part_of_speech_candidates=("noun",),
                sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.kappa",
                        sense_label="kappa_entity",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.71,
                        status_hint=LexicalSenseStatus.STABLE,
                    ),
                ),
                confidence=0.62,
                evidence_ref="ev-kappa-no-examples",
            ),
        ),
        context=LexiconUpdateContext(min_evidence_for_stable=3, stable_confidence_threshold=0.7),
    )
    with_examples = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(
            LexicalEntryProposal(
                surface_form="kappa",
                canonical_form="kappa",
                language_code="en",
                part_of_speech_candidates=("noun",),
                sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.kappa",
                        sense_label="kappa_entity",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.71,
                        status_hint=LexicalSenseStatus.STABLE,
                        example_texts=("kappa appears as a domain entity",),
                    ),
                ),
                entry_example_texts=("kappa entry usage sample",),
                confidence=0.62,
                evidence_ref="ev-kappa-with-examples",
            ),
        ),
        context=LexiconUpdateContext(min_evidence_for_stable=3, stable_confidence_threshold=0.7),
    )

    query_without = query_lexical_entries(
        lexicon_state=without_examples.updated_state,
        queries=(LexiconQueryRequest(surface_form="kappa", language_code="en"),),
    )
    query_with = query_lexical_entries(
        lexicon_state=with_examples.updated_state,
        queries=(LexiconQueryRequest(surface_form="kappa", language_code="en"),),
    )

    assert query_without.downstream_gate.accepted is False
    assert "non_stable_entry_without_example_support" in query_without.downstream_gate.restrictions
    assert query_with.downstream_gate.accepted is True
