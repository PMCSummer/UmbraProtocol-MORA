from __future__ import annotations

from tests.substrate.l05_testkit import build_l05_context


def test_quoted_speech_state_remains_first_class_and_separable() -> None:
    result = build_l05_context('no, i was quoting "you are wrong"', "l05-quoted").modus
    assert result.bundle.hypothesis_records
    assert any(record.quoted_speech_state.quote_or_echo_present for record in result.bundle.hypothesis_records)
    assert all(
        record.quoted_speech_state.commitment_transfer_forbidden
        for record in result.bundle.hypothesis_records
    )
    assert all(
        record.quoted_speech_state.quoted_force_not_current_commitment
        for record in result.bundle.hypothesis_records
        if record.quoted_speech_state.quote_or_echo_present
    )


def test_echoic_like_case_keeps_reported_force_as_alternative_not_commitment() -> None:
    result = build_l05_context('he said "you should leave"', "l05-echoic").modus
    assert any(
        (not record.quoted_speech_state.quote_or_echo_present)
        or ("quoted_force_not_current_commitment" in record.downstream_cautions)
        for record in result.bundle.hypothesis_records
    )
    assert all(len(record.illocution_hypotheses) >= 2 for record in result.bundle.hypothesis_records)
