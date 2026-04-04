from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.discourse_update import DiscourseUpdateResult
from tests.substrate.l06_testkit import build_l06_context


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    CaseSpec("l06-01", "i am tired"),
    CaseSpec("l06-02", "you are tired?"),
    CaseSpec("l06-03", 'he said "you are tired"'),
    CaseSpec("l06-04", "if you are tired"),
    CaseSpec("l06-05", "i did not say that"),
    CaseSpec("l06-06", "this is true"),
    CaseSpec("l06-07", "we should stop"),
    CaseSpec("l06-08", "no, i was quoting him"),
    CaseSpec("l06-09", "it is cold"),
    CaseSpec("l06-10", "they told us to leave"),
)


def test_case_matrix_contains_10_inputs() -> None:
    assert len(_CASES) == 10


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_l06_builds_typed_update_and_repair_layer(case: CaseSpec) -> None:
    result = build_l06_context(case.text, case.case_id).discourse_update
    assert isinstance(result, DiscourseUpdateResult)
    assert result.bundle.update_proposals
    assert result.bundle.acceptance_required_count == len(result.bundle.update_proposals)
    assert all(proposal.acceptance_required for proposal in result.bundle.update_proposals)
    assert all(proposal.acceptance_status.value in {"acceptance_required", "not_accepted"} for proposal in result.bundle.update_proposals)
    assert result.bundle.interpretation_not_equal_accepted_update is True
    assert result.bundle.no_common_ground_mutation_performed is True
    assert result.bundle.no_self_state_mutation_performed is True
    assert result.bundle.no_final_acceptance_performed is True
    assert result.bundle.downstream_update_acceptor_absent is True
    assert result.bundle.repair_consumer_absent is True
    assert result.bundle.discourse_state_mutation_consumer_absent is True
    assert result.bundle.legacy_g01_bypass_risk_present is True
