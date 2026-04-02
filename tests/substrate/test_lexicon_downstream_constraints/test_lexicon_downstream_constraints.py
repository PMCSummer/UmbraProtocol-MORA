from dataclasses import fields

import pytest

from substrate.lexicon import (
    LexiconQueryContext,
    LexiconQueryRequest,
    create_seed_lexicon_state,
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
