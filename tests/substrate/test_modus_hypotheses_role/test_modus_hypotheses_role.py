from __future__ import annotations

from substrate.modus_hypotheses import AddressivityKind, IllocutionKind
from tests.substrate.l05_testkit import build_l05_context


def test_quoted_force_not_bound_as_current_commitment() -> None:
    quoted = build_l05_context('he said "you are tired"', "l05-role-quoted").modus
    plain = build_l05_context("you are tired", "l05-role-plain").modus

    quoted_kinds = {
        hypothesis.illocution_kind
        for record in quoted.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    plain_kinds = {
        hypothesis.illocution_kind
        for record in plain.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    assert IllocutionKind.QUOTED_FORCE_CANDIDATE in quoted_kinds
    assert IllocutionKind.REPORTED_FORCE_CANDIDATE in quoted_kinds
    assert IllocutionKind.QUOTED_FORCE_CANDIDATE not in plain_kinds
    assert all(
        record.quoted_speech_state.quoted_force_not_current_commitment
        for record in quoted.bundle.hypothesis_records
        if record.quoted_speech_state.quote_or_echo_present
    )


def test_addressivity_is_inspectable_separately_from_force() -> None:
    result = build_l05_context("if we are tired", "l05-role-addressivity").modus
    for record in result.bundle.hypothesis_records:
        assert record.illocution_hypotheses
        assert record.addressivity_hypotheses
        assert any(
            hypothesis.addressivity_kind in {AddressivityKind.UNSPECIFIED_AUDIENCE, AddressivityKind.UNKNOWN_TARGET}
            for hypothesis in record.addressivity_hypotheses
        )
