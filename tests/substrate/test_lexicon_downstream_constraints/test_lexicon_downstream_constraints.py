from dataclasses import fields

import pytest

from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalEntryProposal,
    LexicalSenseHypothesis,
    LexicalSenseStatus,
    LexicalUnknownClass,
    LexiconQueryContext,
    LexiconQueryRequest,
    UnknownLexicalObservation,
    create_seed_lexicon_state,
    create_or_update_lexicon_state,
    create_empty_lexicon_state,
    evaluate_lexicon_downstream_gate,
    query_lexical_entries,
)


def test_gate_rejects_raw_and_accepts_typed_artifacts() -> None:
    with pytest.raises(TypeError):
        evaluate_lexicon_downstream_gate("raw")
    with pytest.raises(TypeError):
        evaluate_lexicon_downstream_gate({"entries": "raw"})

    state = create_seed_lexicon_state()
    gate = evaluate_lexicon_downstream_gate(state)
    assert gate.accepted is True
    assert gate.restrictions


def test_no_final_semantic_claim_or_referent_resolution_fields() -> None:
    state = create_seed_lexicon_state()
    result = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
    )
    assert result.no_final_meaning_resolution_performed is True
    forbidden = {
        "accepted_discourse_fact",
        "final_referent",
        "dictum",
        "proposition",
        "illocution",
        "commitment",
        "world_truth",
    }
    field_names = {field_info.name for field_info in fields(type(result))}
    assert forbidden.isdisjoint(field_names)


def test_ablation_lite_without_typed_lexicon_input_contract_degrades() -> None:
    with pytest.raises(TypeError):
        query_lexical_entries(lexicon_state="raw", queries=(LexiconQueryRequest(surface_form="x"),))


def test_reference_profile_requires_context_is_runtime_load_bearing() -> None:
    state = create_seed_lexicon_state()
    without_context = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="you", language_code="en"),),
    )
    with_context = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="you", language_code="en"),),
        context=LexiconQueryContext(context_keys=("speaker", "addressee")),
    )

    no_ctx_record = without_context.query_records[0]
    assert no_ctx_record.context_blocked_entry_ids
    assert "context_required_for_reference_profile" in no_ctx_record.ambiguity_reasons
    assert without_context.downstream_gate.accepted is False
    assert "context_required_for_reference_profile" in without_context.downstream_gate.restrictions

    with_ctx_record = with_context.query_records[0]
    assert not with_ctx_record.context_blocked_entry_ids
    assert with_context.downstream_gate.accepted is True


def test_operator_role_hint_requires_scope_anchor_when_underspecified() -> None:
    state = create_seed_lexicon_state()
    without_scope = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="not", language_code="en"),),
    )
    with_scope = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="not", language_code="en"),),
        context=LexiconQueryContext(context_keys=("scope_anchor",)),
    )
    no_scope_record = without_scope.query_records[0]
    assert "operator_scope_context_required" in no_scope_record.ambiguity_reasons
    assert without_scope.downstream_gate.accepted is False
    assert "operator_scope_context_required" in without_scope.downstream_gate.restrictions

    with_scope_record = with_scope.query_records[0]
    assert "operator_scope_context_required" not in with_scope_record.ambiguity_reasons
    assert with_scope.downstream_gate.accepted is True


def test_query_gate_semantics_match_canonical_gate_for_context_blocked_case() -> None:
    state = create_seed_lexicon_state()
    result = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="you", language_code="en"),),
    )
    canonical = evaluate_lexicon_downstream_gate(result)
    assert result.downstream_gate == canonical
    assert result.downstream_gate.accepted is False
    assert "context_blocked_query_match_present" in result.downstream_gate.restrictions


def test_only_unstable_senses_block_strong_usable_lexical_claim() -> None:
    unstable = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(
            LexicalEntryProposal(
                surface_form="unstablex",
                canonical_form="unstablex",
                language_code="en",
                part_of_speech_candidates=("noun",),
                sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.unstablex",
                        sense_label="unstable_sense",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.65,
                        status_hint=LexicalSenseStatus.PROVISIONAL,
                    ),
                ),
                confidence=0.65,
                evidence_ref="ev-unstable-only",
            ),
        ),
    )
    result = query_lexical_entries(
        lexicon_state=unstable.updated_state,
        queries=(LexiconQueryRequest(surface_form="unstablex", language_code="en"),),
    )
    canonical = evaluate_lexicon_downstream_gate(result)
    assert result.downstream_gate == canonical
    assert result.downstream_gate.accepted is False
    assert "only_unstable_senses" in result.downstream_gate.restrictions


def test_unknown_word_and_unknown_sense_in_context_have_distinct_gate_semantics() -> None:
    seeded = create_seed_lexicon_state()
    with_unknown = create_or_update_lexicon_state(
        lexicon_state=seeded,
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="qzxv",
                occurrence_ref="occ-downstream-unknown",
                provenance="test.downstream",
            ),
        ),
    )
    unknown_result = query_lexical_entries(
        lexicon_state=with_unknown.updated_state,
        queries=(LexiconQueryRequest(surface_form="qzxv", language_code="en"),),
    )
    unknown_record = unknown_result.query_records[0]
    assert {state.unknown_class for state in unknown_record.unknown_states} == {
        LexicalUnknownClass.UNKNOWN_WORD
    }
    assert "unknown_word" in unknown_result.downstream_gate.restrictions
    assert unknown_result.downstream_gate.accepted is False

    unknown_sense_result = query_lexical_entries(
        lexicon_state=with_unknown.updated_state,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
    )
    unknown_sense_record = unknown_sense_result.query_records[0]
    assert {
        state.unknown_class for state in unknown_sense_record.unknown_states
    } == {LexicalUnknownClass.KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT}
    assert "known_lexeme_unknown_sense_in_context" in unknown_sense_result.downstream_gate.restrictions
    assert unknown_sense_result.downstream_gate.accepted is False
