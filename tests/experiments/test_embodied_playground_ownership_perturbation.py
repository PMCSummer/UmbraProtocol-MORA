from __future__ import annotations

from experiments.embodied_playground.ownership_perturbation import (
    list_ownership_perturbation_scenarios,
    run_ownership_ablation_checks,
    run_ownership_perturbation_case,
)


def test_p11_self_caused_move_requires_ap01_and_correlated_effect() -> None:
    run = run_ownership_perturbation_case("self_caused_move_effect")
    assert run.ap01_request_refs
    assert run.effect_refs
    assert run.ownership_assessment.self_cause_status == "supported"
    assert run.falsifier_results["self_action_without_ap01_ref"] is False
    assert run.falsifier_results["effect_without_correlation_claimed_self"] is False


def test_p11_self_caused_pickup_preserves_effect_boundary() -> None:
    run = run_ownership_perturbation_case("self_caused_pickup_effect")
    assert run.ap01_request_refs
    assert run.effect_refs
    assert run.falsifier_results["ap01_request_as_effect"] is False
    assert run.ownership_assessment.fact_claimed is False
    assert run.ownership_assessment.cause_confirmed is False


def test_p11_world_only_change_not_claimed_as_self_action() -> None:
    run = run_ownership_perturbation_case("world_only_object_change")
    assert run.ap01_request_refs == ()
    assert run.ownership_assessment.self_cause_status in {"blocked", "not_supported"}
    assert run.falsifier_results["world_change_claimed_as_self_action"] is False


def test_p11_other_actor_change_not_claimed_as_self_action() -> None:
    run = run_ownership_perturbation_case("other_actor_object_change")
    assert run.ap01_request_refs == ()
    assert run.ownership_assessment.other_cause_status == "supported"
    assert run.ownership_assessment.self_cause_status in {"blocked", "not_supported"}
    assert run.falsifier_results["other_action_claimed_as_self_action"] is False


def test_p11_mixed_cause_is_preserved() -> None:
    run = run_ownership_perturbation_case("mixed_self_and_world_effect")
    assert run.ownership_assessment.mixed_cause_status in {"supported", "weak"}
    assert run.ownership_assessment.mixed_cause_preserved is True
    assert run.falsifier_results["mixed_cause_erased"] is False


def test_p11_delayed_self_effect_not_misattributed_immediate() -> None:
    run = run_ownership_perturbation_case("delayed_self_effect")
    assert run.ownership_assessment.self_cause_status in {"weak", "blocked"}
    assert run.falsifier_results["delayed_effect_misattributed_immediate"] is False


def test_p11_unknown_effect_preserves_unknown_cause() -> None:
    run = run_ownership_perturbation_case("unknown_unexplained_effect")
    assert run.ownership_assessment.unknown_cause_status in {"supported", "weak"}
    assert run.ownership_assessment.unknown_preserved is True
    assert run.falsifier_results["unknown_cause_forced_closure"] is False


def test_p11_sensor_projection_mismatch_not_world_fact() -> None:
    run = run_ownership_perturbation_case("sensor_or_projection_mismatch")
    assert run.ownership_assessment.world_cause_status in {"blocked", "not_supported"}
    assert run.falsifier_results["sensor_mismatch_claimed_world_fact"] is False


def test_p11_blocked_action_not_claimed_success() -> None:
    run = run_ownership_perturbation_case("blocked_self_action_no_world_delta")
    assert run.ownership_assessment.self_cause_status in {"weak", "blocked"}
    assert run.falsifier_results["blocked_action_claimed_success"] is False


def test_p11_hidden_eval_only_no_public_attribution() -> None:
    run = run_ownership_perturbation_case("hidden_eval_only_cause")
    assert run.hidden_eval_used is False
    assert run.ownership_assessment.self_cause_status in {"blocked", "not_supported"}
    assert run.ownership_assessment.unknown_cause_status in {"supported", "weak"}
    assert run.falsifier_results["hidden_truth_attribution"] is False


def test_p11_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_ownership_perturbation_scenarios()}
    required = {
        "self_caused_move_effect",
        "self_caused_pickup_effect",
        "world_only_object_change",
        "other_actor_object_change",
        "mixed_self_and_world_effect",
        "delayed_self_effect",
        "unknown_unexplained_effect",
        "sensor_or_projection_mismatch",
        "blocked_self_action_no_world_delta",
        "hidden_eval_only_cause",
    }
    assert required.issubset(ids)


def test_p11_ablation_checks_present_and_bounded() -> None:
    checks = run_ownership_ablation_checks()
    names = {item.ablation_id for item in checks}
    required = {
        "remove_ap01_request_ref",
        "remove_effect_correlation",
        "remove_external_actor_marker",
        "remove_mixed_cause_marker",
        "remove_delay_marker",
        "hidden_eval_only",
        "remove_public_observation_refs",
        "blocked_effect_without_delta",
    }
    assert required.issubset(names)
