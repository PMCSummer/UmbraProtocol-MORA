from __future__ import annotations

import json

from experiments.symbolic_trade.runner import list_scenarios, run_stage3_response, stage3_result_to_dict


STAGE3_SCENARIOS = (
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
)


def test_stage3_scenarios_are_registered() -> None:
    available = set(list_scenarios())
    assert set(STAGE3_SCENARIOS).issubset(available)


def test_stage3_all_scenarios_run_with_falsifiers_and_claim_boundary() -> None:
    for scenario in STAGE3_SCENARIOS:
        run = run_stage3_response(scenario, include_falsifiers=True)
        assert run.execution_level
        assert run.claim_boundary
        assert run.falsifier_summary
        assert all(item["passed"] for item in run.falsifier_summary), scenario


def test_stage3_control_scenarios_do_not_emit_offer_or_transfer_candidates() -> None:
    control = ("presence_only", "a_deficit_only", "b_surplus_claim_only", "blocked_aperture")
    for scenario in control:
        run = run_stage3_response(scenario, include_falsifiers=False)
        kinds = {item.response_kind.value for item in run.response_candidates}
        assert "offer_candidate" not in kinds
        assert "transfer_attempt_candidate" not in kinds


def test_stage3_mirrored_scenario_is_differentiated_from_controls() -> None:
    mirrored = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    assert mirrored.selected_response_kind.value in {
        "offer_candidate",
        "request_clarification",
        "revalidate_before_response",
    }
    assert any(
        token in " ".join(item.reason_codes)
        for item in mirrored.response_candidates
        for token in ("resource_asymmetry_candidate", "visible_claim_relation_present", "revalidate")
    )


def test_stage3_blocked_and_false_and_noisy_boundaries_hold() -> None:
    blocked = run_stage3_response("blocked_aperture", include_falsifiers=False)
    assert blocked.selected_response_kind.value != "transfer_attempt_candidate"

    false_claim = run_stage3_response("false_counterpart_claim", include_falsifiers=False)
    false_blob = " ".join(" ".join(item.reason_codes) for item in false_claim.response_candidates).lower()
    assert "counterpart_claim_as_fact" not in false_blob

    noisy = run_stage3_response("noisy_signal", include_falsifiers=False)
    noisy_kinds = {item.response_kind.value for item in noisy.response_candidates}
    assert "transfer_attempt_candidate" not in noisy_kinds


def test_stage3_phase_evidence_includes_w01_to_w06_for_offer_or_transfer_candidates() -> None:
    run = run_stage3_response("claim_then_confirmed_transfer", include_falsifiers=False)
    candidate = next((item for item in run.response_candidates if item.response_kind.value in {"offer_candidate", "transfer_attempt_candidate"}), None)
    if candidate is not None:
        assert {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(candidate.source_phase_coverage))
        evidence_phases = {
            item.split(":", 1)[0]
            for item in candidate.phase_evidence_refs
            if ":" in item
        }
        assert {"W01", "W04", "W05", "W06"}.issubset(evidence_phases)


def test_stage3_candidate_specific_evidence_differs_between_mirrored_and_controls() -> None:
    mirrored = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=False)
    deficit = run_stage3_response("a_deficit_only", include_falsifiers=False)
    surplus = run_stage3_response("b_surplus_claim_only", include_falsifiers=False)

    mirrored_candidate = next((c for c in mirrored.response_candidates if c.response_kind.value == "offer_candidate"), None)
    assert mirrored_candidate is not None
    mirrored_basis = " ".join(mirrored_candidate.response_basis_summary).lower()
    assert "visible_counterpart_claim_relation_present" in mirrored_basis
    assert "bounded_complementarity_candidate_without_oracle" in mirrored_basis

    deficit_blob = " ".join(" ".join(c.response_basis_summary).lower() for c in deficit.response_candidates)
    surplus_blob = " ".join(" ".join(c.response_basis_summary).lower() for c in surplus.response_candidates)
    assert "bounded_complementarity_candidate_without_oracle" not in deficit_blob
    assert "bounded_complementarity_candidate_without_oracle" not in surplus_blob


def test_stage3_candidate_specific_evidence_differs_between_confirmed_and_failed_transfer() -> None:
    confirmed = run_stage3_response("claim_then_confirmed_transfer", include_falsifiers=False)
    failed = run_stage3_response("claim_then_failed_transfer", include_falsifiers=False)

    confirmed_candidate = next((c for c in confirmed.response_candidates if c.response_kind.value == "offer_candidate"), None)
    assert confirmed_candidate is not None
    confirmed_basis = " ".join(confirmed_candidate.response_basis_summary).lower()
    assert "transfer_confirmation_visible_as_observation_not_hidden_truth" in confirmed_basis

    failed_blob = " ".join(" ".join(c.response_basis_summary).lower() for c in failed.response_candidates)
    assert "transfer_confirmation_visible_as_observation_not_hidden_truth" not in failed_blob


def test_stage3_false_claim_vs_resource_claim_contact_have_different_basis_profiles() -> None:
    false_claim = run_stage3_response("false_counterpart_claim", include_falsifiers=False)
    regular_claim = run_stage3_response("resource_claim_contact", include_falsifiers=False)

    false_blob = " ".join(" ".join(c.reason_codes).lower() for c in false_claim.response_candidates)
    regular_blob = " ".join(" ".join(c.reason_codes).lower() for c in regular_claim.response_candidates)
    assert "counterpart_claim_visible" in false_blob
    assert "counterpart_claim_visible" in regular_blob
    # false claim path should retain stronger revalidation/residue pressure from stage25
    false_uncertainty = sum(len(c.residual_uncertainty_refs) for c in false_claim.response_candidates)
    regular_uncertainty = sum(len(c.residual_uncertainty_refs) for c in regular_claim.response_candidates)
    assert false_uncertainty >= regular_uncertainty


def test_stage3_json_default_excludes_eval_only_and_include_eval_only_scoped() -> None:
    run = run_stage3_response("mirrored_resource_asymmetry", include_falsifiers=True)
    payload_default = stage3_result_to_dict(run, include_eval_only=False, include_response_candidates=True)
    assert "eval_only" not in payload_default

    payload_eval = stage3_result_to_dict(run, include_eval_only=True, include_response_candidates=True)
    assert "eval_only" in payload_eval
    blob = json.dumps(payload_eval.get("response_candidates", []), sort_keys=True)
    assert "harness_truth" not in blob
    assert "mutually_beneficial_trade_possible_eval_only" not in blob
