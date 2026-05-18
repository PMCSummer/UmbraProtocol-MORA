from __future__ import annotations

from experiments.embodied_playground.station_affordance import (
    list_station_affordance_cases,
    run_station_affordance_ablations,
    run_station_affordance_case,
)


def test_p14_station_visible_not_usable() -> None:
    run = run_station_affordance_case("station_visible_not_usable")
    assert run.public_station_basis.visible is True
    assert run.proximity_status == "not_proximate"
    assert run.station_use_candidate_status != "published"


def test_p14_station_proximate_no_input_blocks_use() -> None:
    run = run_station_affordance_case("station_proximate_no_input")
    assert run.proximity_status == "proximate"
    assert run.input_status == "missing_input"
    assert run.effect_status == "blocked"
    assert run.missing_input_refs


def test_p14_station_proximate_with_input_uses_ap01_effect_path() -> None:
    run = run_station_affordance_case("station_proximate_with_input")
    assert run.station_use_candidate_status == "published"
    assert run.ap01_publication_status == "published"
    assert run.world_submission_status == "submitted"
    assert run.effect_refs


def test_p14_station_blocked_not_success() -> None:
    run = run_station_affordance_case("station_blocked")
    assert run.blocked_status == "blocked"
    assert run.effect_status == "blocked"


def test_p14_protected_eval_only_rule_no_station_use() -> None:
    run = run_station_affordance_case("station_protected_eval_only_rule")
    assert run.protected_evaluator_only_rule_present is True
    assert run.ap01_publication_status != "published"
    assert run.effect_status != "succeeded"


def test_p14_action_space_only_no_station_use() -> None:
    run = run_station_affordance_case("station_action_surface_only")
    assert run.station_ref is None
    assert run.station_use_candidate_status != "published"


def test_p14_station_far_with_input_not_usable() -> None:
    run = run_station_affordance_case("station_far_with_input")
    assert run.input_status == "input_available"
    assert run.proximity_status == "not_proximate"
    assert run.effect_status != "succeeded"


def test_p14_missing_station_ref_no_use() -> None:
    run = run_station_affordance_case("station_missing_station_ref")
    assert run.station_ref is None
    assert run.station_use_candidate_status != "published"


def test_p14_station_effect_without_ap01_not_subject_success() -> None:
    run = run_station_affordance_case("station_effect_without_ap01_attempt")
    assert run.ap01_publication_status != "published"
    assert run.effect_status == "succeeded"
    assert run.falsifier_results["station_effect_without_ap01"] is False


def test_p14_station_use_effect_feedback_preserved() -> None:
    run = run_station_affordance_case("station_use_effect_feedback")
    assert run.effect_refs
    assert run.world_submission_status == "submitted"


def test_p14_station_use_does_not_create_mature_recipe_or_schema() -> None:
    run = run_station_affordance_case("station_proximate_with_input")
    assert run.mature_schema_created is False
    assert run.falsifier_results["recipe_or_mature_rule_result_in_p14"] is False


def test_p14_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_station_affordance_cases()}
    required = {
        "station_visible_not_usable",
        "station_proximate_no_input",
        "station_proximate_with_input",
        "station_blocked",
        "station_protected_eval_only_rule",
        "station_action_surface_only",
        "station_far_with_input",
        "station_missing_station_ref",
        "station_effect_without_ap01_attempt",
        "station_use_effect_feedback",
    }
    assert required.issubset(ids)


def test_p14_ablation_checks_present() -> None:
    checks = run_station_affordance_ablations()
    names = {item.ablation_id for item in checks}
    required = {
        "remove_station_ref",
        "remove_proximity",
        "remove_input_refs",
        "remove_action_surface",
        "hidden_eval_only_recipe",
        "remove_ap01_ref",
        "remove_effect_ref",
        "blocked_station",
        "one_shot_success",
    }
    assert required.issubset(names)
