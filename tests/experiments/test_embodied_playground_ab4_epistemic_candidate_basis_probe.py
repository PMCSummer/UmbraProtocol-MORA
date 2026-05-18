from __future__ import annotations

from experiments.embodied_playground.ab4_epistemic_candidate_basis_probe import (
    run_ab4_probe_case,
)
from substrate.ab04_epistemic_candidate_basis import AB4CandidateKind


def test_ab4_probe_uses_ab3_open_frontier() -> None:
    run = run_ab4_probe_case("open_frontier_inspect")
    assert run.result.frontier_ref is not None
    assert run.result.bases


def test_ab4_probe_uses_ab3_ambiguous_frontier() -> None:
    run = run_ab4_probe_case("ambiguous_frontier_wait")
    kinds = {item.candidate_kind for item in run.result.bases}
    assert AB4CandidateKind.WAIT in kinds or AB4CandidateKind.REOBSERVE in kinds


def test_ab4_probe_no_hidden_eval_basis() -> None:
    run = run_ab4_probe_case("hidden_eval_only")
    assert run.result.bases == ()
    assert "hidden_eval_exclusion_required" in run.result.reason_codes


def test_ab4_probe_no_frontier_no_basis() -> None:
    run = run_ab4_probe_case("no_frontier")
    assert run.result.bases == ()
    assert "frontier_required" in run.result.reason_codes


def test_ab4_probe_basis_feeds_no_ap01_request_by_itself() -> None:
    run = run_ab4_probe_case("open_frontier_inspect")
    assert all(item.action_request_emitted is False for item in run.result.bases)
    assert all(item.ap01_request_ref is None for item in run.result.bases)


def test_ab4_probe_does_not_modify_world_or_subject_action() -> None:
    run = run_ab4_probe_case("open_frontier_inspect")
    assert run.route_supported is False
    assert run.routed_ap01_publication_count == 0
    assert run.routed_world_submission_count == 0


def test_ab4_probe_preserves_ab3_no_fact_boundary() -> None:
    run = run_ab4_probe_case("open_frontier_inspect")
    assert all(item.fact_claimed is False for item in run.result.bases)
    assert all(item.cause_confirmed is False for item in run.result.bases)


def test_ab4_probe_no_ap01_no_world_submission_if_routed() -> None:
    run = run_ab4_probe_case(
        "open_frontier_inspect",
        route_through_acp01=True,
        suppress_ap01=True,
    )
    assert run.routed_ap01_publication_count == 0
    assert run.routed_world_submission_count == 0
