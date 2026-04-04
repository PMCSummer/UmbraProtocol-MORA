from __future__ import annotations

from substrate.modus_hypotheses import IllocutionKind
from tests.substrate.l05_testkit import build_l05_context


def test_punctuation_variant_does_not_force_single_label_resolution() -> None:
    plain = build_l05_context("you are tired", "l05-meta-plain").modus
    punct = build_l05_context("you are tired?", "l05-meta-question").modus

    for result in (plain, punct):
        for record in result.bundle.hypothesis_records:
            kinds = {hypothesis.illocution_kind for hypothesis in record.illocution_hypotheses}
            assert len(kinds) >= 2
            assert IllocutionKind.UNKNOWN_FORCE_CANDIDATE in kinds
            assert record.uncertainty_entropy > 0.0


def test_quoted_vs_current_assertion_changes_force_signature() -> None:
    quoted = build_l05_context('he said "you are tired"', "l05-meta-quoted").modus
    direct = build_l05_context("you are tired", "l05-meta-direct").modus

    quoted_kinds = {
        hypothesis.illocution_kind
        for record in quoted.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    direct_kinds = {
        hypothesis.illocution_kind
        for record in direct.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    assert IllocutionKind.QUOTED_FORCE_CANDIDATE in quoted_kinds
    assert IllocutionKind.REPORTED_FORCE_CANDIDATE in quoted_kinds
    assert IllocutionKind.QUOTED_FORCE_CANDIDATE not in direct_kinds


def test_negation_shift_keeps_uncertainty_and_adds_corrective_force_option() -> None:
    affirm = build_l05_context("i said that", "l05-meta-affirm").modus
    negated = build_l05_context("i did not say that", "l05-meta-negated").modus

    negated_kinds = {
        hypothesis.illocution_kind
        for record in negated.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    assert IllocutionKind.EXPRESSIVE_CANDIDATE in negated_kinds
    assert all(record.uncertainty_entropy > 0.0 for record in affirm.bundle.hypothesis_records)
    assert all(record.uncertainty_entropy > 0.0 for record in negated.bundle.hypothesis_records)
