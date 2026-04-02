from substrate.lexicon import create_seed_lexicon_state


def test_seed_lexicon_size_and_typed_records_are_load_bearing() -> None:
    state = create_seed_lexicon_state()
    assert 20 <= len(state.entries) <= 60
    assert all(entry.sense_records for entry in state.entries)
    assert all(entry.composition_profile.role_hints for entry in state.entries)
    assert all(entry.reference_profile.can_remain_unresolved in (True, False) for entry in state.entries)


def test_seed_contains_pronoun_deixis_negation_temporal_quantifier_and_ambiguity() -> None:
    state = create_seed_lexicon_state()
    forms = {entry.canonical_form for entry in state.entries}
    assert {"i", "you", "я", "ты"}.issubset(forms)
    assert {"here", "now", "здесь", "это"}.issubset(forms)
    assert {"not", "не"}.issubset(forms)
    assert {"yesterday", "tomorrow"}.issubset(forms)
    assert {"all", "some", "many"}.issubset(forms)
    bank_entries = [entry for entry in state.entries if entry.canonical_form == "bank"]
    assert bank_entries and len(bank_entries[0].sense_records) >= 2
    can_entries = [entry for entry in state.entries if entry.canonical_form == "can"]
    assert len(can_entries) >= 2
