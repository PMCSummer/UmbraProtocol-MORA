from __future__ import annotations

from experiments.embodied_playground.ab5_hypothesis_update_probe import run_ab5_probe_case
from substrate.ab05_hypothesis_update import AB5DeltaKind


def test_ab5_probe_uses_ab3_frontier_and_ab4_basis() -> None:
    run = run_ab5_probe_case("correlated_effect_support_increase")
    assert run.update is not None
    assert run.update.prior_frontier_ref is not None
    assert run.update.epistemic_basis_refs


def test_ab5_probe_correlated_effect_updates_support() -> None:
    run = run_ab5_probe_case("correlated_effect_support_increase")
    assert run.update is not None
    assert any(item.delta_kind is AB5DeltaKind.INCREASE for item in run.update.support_deltas)


def test_ab5_probe_disconfirming_effect_lowers_support() -> None:
    run = run_ab5_probe_case("disconfirming_effect_support_decrease")
    assert run.update is not None
    assert any(item.delta_kind in {AB5DeltaKind.DISCONFIRM, AB5DeltaKind.DECREASE} for item in run.update.support_deltas)


def test_ab5_probe_ambiguous_effect_no_closure() -> None:
    run = run_ab5_probe_case("ambiguous_effect_no_closure")
    assert run.update is not None
    assert run.update.closure_allowed is False
    assert run.update.ambiguous_evidence_refs


def test_ab5_probe_request_alone_no_confirmation() -> None:
    run = run_ab5_probe_case("request_alone_no_confirmation")
    assert run.update is not None
    assert run.update.support_deltas == ()
    assert run.update.closure_blocked_reason == "request_without_effect_not_confirmation"


def test_ab5_probe_no_hidden_eval_update() -> None:
    run = run_ab5_probe_case("hidden_eval_effect_rejected")
    assert run.update is None
    assert "hidden_eval_exclusion_required" in run.reason_codes


def test_ab5_probe_no_ap01_request_emitted() -> None:
    run = run_ab5_probe_case("correlated_effect_support_increase")
    assert run.update is not None
    assert run.update.action_request_emitted is False
    assert run.update.world_submission_emitted is False


def test_ab5_probe_preserves_ab3_no_fact_boundary() -> None:
    run = run_ab5_probe_case("correlated_effect_support_increase")
    assert run.update is not None
    assert run.update.fact_claimed is False
    assert run.update.cause_confirmed is False
