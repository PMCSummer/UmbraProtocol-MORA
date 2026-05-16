from __future__ import annotations

from dataclasses import replace

import experiments.symbolic_trade.falsifiers as falsifier_module
from experiments.symbolic_trade.response_candidates import AResponseKind
from experiments.symbolic_trade.runner import run_stage3_response


def _outcome_map(items) -> dict[str, bool]:
    return {item.name: item.passed for item in items}


def test_stage3_falsifiers_pass_on_clean_scenarios() -> None:
    for scenario in (
        "presence_only",
        "resource_claim_contact",
        "mirrored_resource_asymmetry",
        "false_counterpart_claim",
        "blocked_aperture",
        "noisy_signal",
        "transfer_seen_without_trade_token",
        "eval_label_leak_attack",
        "a_deficit_only",
        "b_surplus_claim_only",
        "claim_then_confirmed_transfer",
        "claim_then_failed_transfer",
    ):
        run = run_stage3_response(scenario, include_falsifiers=True)
        assert all(item["passed"] for item in run.falsifier_summary), scenario


def test_stage3_hidden_truth_and_eval_label_negative_controls_fail() -> None:
    run = run_stage3_response("resource_claim_contact", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(c, hidden_truth_used=True, eval_only_used=True)
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_hidden_truth_used_for_response"] is False
    assert outcomes["stage3_eval_label_used_for_response"] is False


def test_stage3_deficit_permission_and_surplus_offer_shortcuts_fail() -> None:
    run = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    c = run.response_candidates[0]
    bad_offer = replace(
        c,
        response_kind=AResponseKind.OFFER_CANDIDATE,
        evidence_refs=("packet:only_self_state",),
        reason_codes=c.reason_codes + ("surplus_shortcut_offer", "deficit_as_permission"),
    )
    mutated = replace(run, response_candidates=(bad_offer,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_deficit_as_permission"] is False
    assert outcomes["stage3_surplus_as_offer_shortcut"] is False


def test_stage3_b_claim_fact_oracle_and_trade_shortcut_negative_controls_fail() -> None:
    run = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        evidence_refs=c.evidence_refs + ("counterpart_fact:water_surplus",),
        reason_codes=c.reason_codes + ("true_need_surplus_pairing", "trade_intent"),
    )
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_b_claim_as_fact"] is False
    assert outcomes["stage3_mirrored_complementarity_oracle"] is False
    assert outcomes["stage3_trade_specific_response_kind"] is False


def test_stage3_permission_and_execution_boundary_negative_controls_fail() -> None:
    run = run_stage3_response("claim_then_confirmed_transfer", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        permitted_status="permission_granted_by_usefulness",
        requested_effect="executed_transfer",
        reason_codes=c.reason_codes + ("predicted_as_permitted", "w05_route_as_permission", "w06_correction_executed"),
    )
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_usefulness_as_permission"] is False
    assert outcomes["stage3_predicted_as_permitted"] is False
    assert outcomes["stage3_candidate_executes_transfer"] is False
    assert outcomes["stage3_w05_routing_as_execution_permission"] is False
    assert outcomes["stage3_w06_correction_as_executed"] is False


def test_stage3_phase_causality_and_coverage_negative_controls_fail() -> None:
    run = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        response_kind=AResponseKind.OFFER_CANDIDATE,
        source_phase_coverage=("W01", "W02"),
        phase_evidence_refs=(
            "W01:w01_result.gate",
            "W02:w02_result.gate",
        ),
        reason_codes=c.reason_codes + ("one_shot_promoted_to_schema",),
    )
    mutated = replace(
        run,
        response_candidates=(bad,) + run.response_candidates[1:],
        phase_coverage_verified=True,
        phase_coverage_evidence=("W01:w01_result.gate",),
    )
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_response_without_phase_causality"] is False
    assert outcomes["stage3_one_shot_exchange_schema"] is False
    assert outcomes["stage3_phase_coverage_fake"] is False


def test_stage3_falsifier_detects_blocked_aperture_structural_bypass_without_scenario_name_dependency() -> None:
    run = run_stage3_response("blocked_aperture", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        response_kind=AResponseKind.TRANSFER_ATTEMPT_CANDIDATE,
        response_basis_summary=(
            "blocked_aperture_event_visible",
            "w04_constraint_prevents_clean_applicability",
        ),
        reason_codes=c.reason_codes + ("blocked_aperture_visible",),
    )
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_blocked_aperture_transfer_candidate"] is False


def test_stage3_falsifier_detects_noisy_signal_clean_offer_structurally() -> None:
    run = run_stage3_response("noisy_signal", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        response_kind=AResponseKind.OFFER_CANDIDATE,
        response_basis_summary=("contradiction_or_noise_visible",),
        reason_codes=("contradiction_visible",),
        phase_evidence_refs=(
            "W01:packet:p:claim_not_fact_preserved:true",
            "W04:packet:p:clean_applicability_allowed:true",
            "W05:packet:p:desired_as_observed:false",
            "W06:packet:p:residual_uncertainty_present:false",
        ),
    )
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_noisy_claim_cleaned_into_fact"] is False


def test_stage3_falsifier_detects_false_claim_clean_offer_structurally() -> None:
    run = run_stage3_response("false_counterpart_claim", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        response_kind=AResponseKind.OFFER_CANDIDATE,
        response_basis_summary=("claim_not_fact_boundary_preserved",),
        reason_codes=("visible_claim_relation_present",),
        residual_uncertainty_refs=(),
        phase_evidence_refs=(
            "W01:packet:p:claim_not_fact_preserved:true",
            "W04:packet:p:clean_applicability_allowed:true",
            "W05:packet:p:desired_as_observed:false",
            "W06:packet:p:residual_uncertainty_present:false",
        ),
    )
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_false_claim_clean_offer"] is False


def test_stage3_falsifier_detects_structured_json_leak_paths() -> None:
    run = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        response_basis_summary=c.response_basis_summary + ("hidden_truth:water_surplus", "mutual_benefit_oracle"),
    )
    mutated = replace(run, response_candidates=(bad,) + run.response_candidates[1:])
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_hidden_truth_used_for_response"] is False
    assert outcomes["stage3_mirrored_complementarity_oracle"] is False


def test_stage3_falsifier_detects_control_profile_offer_without_structural_basis() -> None:
    run = run_stage3_response("a_deficit_only", include_falsifiers=False)
    c = run.response_candidates[0]
    bad = replace(
        c,
        response_kind=AResponseKind.OFFER_CANDIDATE,
        response_basis_summary=("generic_offer_without_basis",),
        forbidden_basis_markers=("hidden_truth_not_used",),
        boundary_markers=("counterpart_claim_not_fact",),
        phase_evidence_refs=(
            "W01:packet:p:claim_not_fact_preserved:true",
            "W04:packet:p:clean_applicability_allowed:true",
            "W05:packet:p:desired_as_observed:false",
            "W06:packet:p:execution_prohibited:true",
        ),
    )
    mutated = replace(
        run,
        response_candidates=(bad,),
        selected_response_kind=AResponseKind.OFFER_CANDIDATE,
        selected_response_id=bad.response_id,
    )
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(mutated))
    assert outcomes["stage3_control_scenario_same_as_mirrored"] is False


def test_stage3_core_contamination_detects_untracked_forbidden_path(monkeypatch) -> None:
    run = run_stage3_response("presence_only", include_falsifiers=False)
    monkeypatch.setattr(falsifier_module, "_modified_paths", lambda _repo_root: ())
    monkeypatch.setattr(
        falsifier_module,
        "_untracked_paths",
        lambda _repo_root: ("src/substrate/subject_tick/stage3_probe_leak.py",),
    )
    outcomes = _outcome_map(falsifier_module.run_stage3_response_falsifiers(run))
    assert outcomes["stage3_core_contamination"] is False
