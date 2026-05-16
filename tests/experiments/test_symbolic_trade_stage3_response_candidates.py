from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.symbolic_trade.response_candidates import AResponseCandidate, AResponseKind
from experiments.symbolic_trade.runner import run_stage3_response


def _candidate(kind: AResponseKind = AResponseKind.OBSERVE_ONLY) -> AResponseCandidate:
    return AResponseCandidate(
        response_id="r1",
        scenario_name="presence_only",
        source_step_id="step:1",
        source_step_ids=("step:1",),
        response_kind=kind,
        target_ref="counterpart_b",
        object_ref=None,
        requested_effect="observe",
        confidence=0.2,
        permitted_status="observe_only",
        evidence_refs=("packet:p1",),
        phase_evidence_refs=("W01:w01_result.gate", "W04:w04_result.gate", "W05:w05_result.gate", "W06:w06_result.gate"),
        prohibited_claims=(
            "no_autonomous_trade_claim",
            "no_hidden_truth_claim",
            "no_negotiation_claim",
            "no_executed_transfer_claim",
            "no_economic_agency_claim",
        ),
        reason_codes=("bounded_probe_only",),
        boundary_markers=("counterpart_claim_not_fact",),
        execution_prohibited=True,
        claim_boundary=("stage3_response_candidate_probe_only",),
        hidden_truth_used=False,
        eval_only_used=False,
        trade_shortcut_used=False,
        derived_from_real_subject_tick=True,
        extraction_method="test",
        source_phase_coverage=("W01", "W02", "W03", "W04", "W05", "W06"),
        residual_uncertainty_refs=(),
        response_basis_summary=("visible_only_packet_basis",),
        forbidden_basis_markers=(
            "hidden_truth_not_used",
            "eval_only_not_used",
            "scenario_label_not_used",
            "mirrored_oracle_not_used",
            "trade_shortcut_not_used",
            "desired_not_evidence",
            "predicted_not_permission",
        ),
    )


def test_response_candidate_construction_and_boundary_defaults() -> None:
    candidate = _candidate()
    assert candidate.execution_prohibited is True
    assert candidate.hidden_truth_used is False
    assert candidate.eval_only_used is False
    assert candidate.trade_shortcut_used is False


def test_offer_candidate_requires_execution_prohibited_and_claim_boundary() -> None:
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.OFFER_CANDIDATE),
            claim_boundary=(),
        )
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.OFFER_CANDIDATE),
            execution_prohibited=False,
        )
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.OFFER_CANDIDATE),
            hidden_truth_used=True,
        )
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.OFFER_CANDIDATE),
            eval_only_used=True,
        )
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.OFFER_CANDIDATE),
            trade_shortcut_used=True,
        )
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.OFFER_CANDIDATE),
            phase_evidence_refs=(),
        )
    with pytest.raises(ValueError):
        replace(
            _candidate(AResponseKind.TRANSFER_ATTEMPT_CANDIDATE),
            transfer_executed=True,
        )

    valid_offer = replace(
        _candidate(AResponseKind.OBSERVE_ONLY),
        response_kind=AResponseKind.OFFER_CANDIDATE,
        requested_effect="bounded_offer_candidate_not_executed",
        execution_prohibited=True,
        claim_boundary=("stage3_response_candidate_probe_only", "candidate_not_executed_trade"),
        phase_evidence_refs=(
            "W01:packet:p1:claim_not_fact_preserved:true",
            "W04:packet:p1:clean_applicability_allowed:true",
            "W05:packet:p1:desired_as_observed:false",
            "W06:packet:p1:execution_prohibited:true",
        ),
        evidence_refs=("packet:p1", "counterpart_claim:p1"),
    )
    assert valid_offer.response_kind is AResponseKind.OFFER_CANDIDATE


def test_candidate_allows_adversarial_mutation_for_falsifier_negative_controls() -> None:
    mutated = replace(_candidate(), hidden_truth_used=True, eval_only_used=True, trade_shortcut_used=True)
    assert mutated.hidden_truth_used is True
    assert mutated.eval_only_used is True
    assert mutated.trade_shortcut_used is True


def test_stage3_run_candidates_keep_non_execution_boundary() -> None:
    run = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    assert run.response_candidates
    for candidate in run.response_candidates:
        assert candidate.execution_prohibited is True
        assert candidate.hidden_truth_used is False
        assert candidate.eval_only_used is False
        assert candidate.trade_shortcut_used is False
