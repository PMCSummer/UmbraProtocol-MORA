from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.targeted_clarification import TargetedClarificationResult


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    CaseSpec("g07-01", "i am tired"),
    CaseSpec("g07-02", "you are tired?"),
    CaseSpec("g07-03", 'he said "you are tired"'),
    CaseSpec("g07-04", "no, i did not say that"),
    CaseSpec("g07-05", "you should stop"),
    CaseSpec("g07-06", "this is dangerous"),
    CaseSpec("g07-07", "if he said i am dangerous"),
    CaseSpec("g07-08", "we are tired"),
    CaseSpec("g07-09", "are you sure this is true"),
    CaseSpec("g07-10", "it is cold"),
    CaseSpec("g07-11", "you must comply"),
    CaseSpec("g07-12", "i think he said you are wrong"),
)


def test_case_matrix_contains_12_inputs() -> None:
    assert len(_CASES) == 12


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g07_builds_typed_targeted_clarification_layer(case: CaseSpec, g07_factory) -> None:
    result = g07_factory(case.text, case.case_id).intervention
    assert isinstance(result, TargetedClarificationResult)
    assert result.bundle.intervention_records
    assert result.bundle.no_final_semantic_closure is True
    assert result.bundle.l06_upstream_bound_here is True
    assert result.bundle.l06_update_proposal_absent is False
    assert result.bundle.l06_continuation_topology_present is True
    assert result.bundle.response_realization_contract_absent is True
    assert result.bundle.answer_binding_consumer_absent is True
    assert result.telemetry.attempted_paths
    assert all(record.uncertainty_target_id for record in result.bundle.intervention_records)
    assert all(record.minimal_question_spec.preferred_answer_forbidden for record in result.bundle.intervention_records)
    assert all(record.downstream_lockouts for record in result.bundle.intervention_records)
