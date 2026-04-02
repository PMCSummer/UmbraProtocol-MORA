from dataclasses import fields

import pytest

from substrate.lexicon import (
    LexicalEntry,
    LexicalSenseRecord,
    LexiconQueryContext,
    LexiconQueryRequest,
    create_or_update_lexicon_state,
    create_seed_lexicon_state,
    query_lexical_entries,
)


def test_raw_bypass_rejected_on_update_and_query_paths() -> None:
    with pytest.raises(TypeError):
        create_or_update_lexicon_state(entry_proposals=("raw",))
    with pytest.raises(TypeError):
        query_lexical_entries(lexicon_state="raw", queries=(LexiconQueryRequest(surface_form="x"),))


def test_query_schema_version_incompatibility_is_honest_abstain() -> None:
    state = create_seed_lexicon_state()
    result = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
        context=LexiconQueryContext(expected_schema_version="lexicon.schema.v999"),
    )
    assert result.abstain is True
    assert result.downstream_gate.accepted is False
    assert "compatibility_mismatch" in result.downstream_gate.restrictions
    assert "schema_version_mismatch" in result.telemetry.compatibility_markers


def test_lexicon_public_models_do_not_claim_dictum_or_illocution() -> None:
    forbidden = {
        "dictum",
        "proposition",
        "parse_tree",
        "syntax_winner",
        "illocution",
        "commitment",
        "accepted_fact",
        "world_truth",
    }
    field_names = {field_info.name for field_info in fields(LexicalEntry)}
    assert forbidden.isdisjoint(field_names)
    sense_field_names = {field_info.name for field_info in fields(LexicalSenseRecord)}
    assert forbidden.isdisjoint(sense_field_names)
