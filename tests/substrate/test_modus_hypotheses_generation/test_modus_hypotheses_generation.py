from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.modus_hypotheses import ModusHypothesisResult
from tests.substrate.l05_testkit import build_l05_context


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    CaseSpec("l05-01", "i am tired"),
    CaseSpec("l05-02", "you are tired?"),
    CaseSpec("l05-03", 'he said "you are tired"'),
    CaseSpec("l05-04", "if you are tired"),
    CaseSpec("l05-05", "i did not say that"),
    CaseSpec("l05-06", "maybe this is true"),
    CaseSpec("l05-07", "we should stop now"),
    CaseSpec("l05-08", "no, i was quoting him"),
    CaseSpec("l05-09", "it is cold"),
    CaseSpec("l05-10", "they told us to leave"),
)


def test_case_matrix_contains_10_inputs() -> None:
    assert len(_CASES) == 10


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_l05_builds_typed_modus_hypothesis_layer(case: CaseSpec) -> None:
    result = build_l05_context(case.text, case.case_id).modus
    assert isinstance(result, ModusHypothesisResult)
    assert result.bundle.hypothesis_records
    assert result.bundle.no_final_intent_selection is True
    assert result.bundle.no_common_ground_update is True
    assert result.bundle.no_repair_planning is True
    assert result.bundle.l06_downstream_not_bound_here is True
    assert result.bundle.l06_update_consumer_not_wired_here is True
    assert result.bundle.l06_repair_consumer_not_wired_here is True
    assert result.bundle.legacy_l04_g01_shortcut_operational_debt is True
    assert result.bundle.legacy_shortcut_bypass_risk is True
    assert result.telemetry.attempted_paths
    assert all(len(record.illocution_hypotheses) >= 2 for record in result.bundle.hypothesis_records)
    assert all(record.uncertainty_entropy > 0.0 for record in result.bundle.hypothesis_records)
