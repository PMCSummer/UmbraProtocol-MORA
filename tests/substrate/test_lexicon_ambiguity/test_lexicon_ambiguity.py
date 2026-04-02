from dataclasses import replace

from substrate.lexicon import (
    LexicalEntry,
    LexiconQueryRequest,
    create_seed_lexicon_state,
    query_lexical_entries,
)


def test_single_form_supports_multiple_senses_without_top1_collapse() -> None:
    state = create_seed_lexicon_state()
    result = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
    )
    record = result.query_records[0]
    assert len(record.matched_entry_ids) >= 1
    assert len(record.matched_sense_ids) >= 2
    assert "multiple_senses_for_surface_form" in record.ambiguity_reasons
    assert record.no_final_meaning_resolution_performed is True


def test_single_form_can_map_to_multiple_entries() -> None:
    state = create_seed_lexicon_state()
    result = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="can", language_code="en"),),
    )
    record = result.query_records[0]
    assert len(record.matched_entry_ids) >= 2
    assert "multiple_entries_for_surface_form" in record.ambiguity_reasons


def test_negative_control_ablation_of_ambiguity_changes_behavior() -> None:
    state = create_seed_lexicon_state()
    base = query_lexical_entries(
        lexicon_state=state,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
    )
    base_record = base.query_records[0]
    assert len(base_record.matched_sense_ids) >= 2

    single_sense_entries: list[LexicalEntry] = []
    for entry in state.entries:
        if entry.canonical_form == "bank":
            single_sense_entries.append(replace(entry, sense_records=(entry.sense_records[0],)))
        else:
            single_sense_entries.append(entry)
    ablated_state = replace(state, entries=tuple(single_sense_entries))
    ablated = query_lexical_entries(
        lexicon_state=ablated_state,
        queries=(LexiconQueryRequest(surface_form="bank", language_code="en"),),
    )
    ablated_record = ablated.query_records[0]
    assert len(ablated_record.matched_sense_ids) == 1
    assert "multiple_senses_for_surface_form" not in ablated_record.ambiguity_reasons
