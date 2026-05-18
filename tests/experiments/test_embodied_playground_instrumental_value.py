from __future__ import annotations

from experiments.embodied_playground.instrumental_value import (
    list_instrumental_value_cases,
    run_instrumental_value_ablations,
    run_instrumental_value_case,
)


def test_p16_resource_with_need_and_recipe_chain_gets_bounded_value() -> None:
    run = run_instrumental_value_case("resource_with_need_and_recipe_chain")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"provisional_instrumental", "repeated_trace_supported", "weak_instrumental"}
    assert run.instrumental_value_frames[0].intrinsic_value_claimed is False


def test_p16_resource_without_need_no_value() -> None:
    run = run_instrumental_value_case("resource_without_need_no_value")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"no_value", "blocked"}


def test_p16_iron_magic_value_guard() -> None:
    run = run_instrumental_value_case("iron_magic_value_guard")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"no_value", "blocked"}
    assert run.falsifier_results["iron_magic_value"] is False


def test_p16_filter_without_water_problem() -> None:
    run = run_instrumental_value_case("filter_without_water_problem")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"no_value", "blocked"}
    assert run.falsifier_results["filter_without_water_problem"] is False


def test_p16_recipe_candidate_missing_effect_chain_blocks_value() -> None:
    run = run_instrumental_value_case("resource_with_recipe_candidate_but_missing_effect_chain")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"blocked", "weak_instrumental", "no_value"}


def test_p16_station_affordance_missing_blocks_station_linked_value() -> None:
    run = run_instrumental_value_case("resource_with_station_affordance_missing")
    assert run.instrumental_value_frames
    assert "p14_station_affordance_refs_required" in run.blocked_reasons
    assert run.instrumental_value_frames[0].value_status == "blocked"


def test_p16_confounded_resource_value_is_weak_or_blocked() -> None:
    run = run_instrumental_value_case("confounded_resource_value")
    assert run.confounder_refs
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"weak_instrumental", "blocked"}


def test_p16_disconfirming_trace_blocks_value() -> None:
    run = run_instrumental_value_case("disconfirmed_resource_value")
    assert run.disconfirmation_refs
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"disconfirmed", "blocked"}


def test_p16_repeated_trace_strengthens_instrumental_value_without_automation() -> None:
    run = run_instrumental_value_case("repeated_trace_strengthens_instrumental_value")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status in {"repeated_trace_supported", "provisional_instrumental"}
    assert run.mature_automation_claimed is False


def test_p16_ab7_blocks_automation_readiness() -> None:
    run = run_instrumental_value_case("AB7_blocks_automation_readiness")
    assert run.means_candidates
    assert all(item.readiness_status in {"blocked", "provisional", "weak", "evidence_required", "not_ready"} for item in run.means_candidates)
    assert run.mature_automation_claimed is False


def test_p16_hidden_eval_value_rule_rejected() -> None:
    run = run_instrumental_value_case("hidden_eval_value_rule_rejected")
    assert run.instrumental_value_frames
    assert run.instrumental_value_frames[0].value_status == "blocked"
    assert run.hidden_eval_used is False


def test_p16_value_candidate_does_not_emit_action() -> None:
    run = run_instrumental_value_case("value_candidate_does_not_emit_action")
    assert run.action_request_emitted is False
    assert run.world_submission_emitted is False
    assert all(item.action_request_emitted is False for item in run.means_candidates)
    assert all(item.world_submission_emitted is False for item in run.means_candidates)


def test_p16_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_instrumental_value_cases()}
    required = {
        "resource_with_need_and_recipe_chain",
        "resource_without_need_no_value",
        "iron_magic_value_guard",
        "filter_without_water_problem",
        "resource_with_recipe_candidate_but_missing_effect_chain",
        "resource_with_station_affordance_missing",
        "confounded_resource_value",
        "disconfirmed_resource_value",
        "repeated_trace_strengthens_instrumental_value",
        "AB7_blocks_automation_readiness",
        "hidden_eval_value_rule_rejected",
        "value_candidate_does_not_emit_action",
    }
    assert required.issubset(ids)


def test_p16_ablation_checks_present() -> None:
    checks = run_instrumental_value_ablations()
    names = {item.ablation_id for item in checks}
    required = {
        "remove_need_refs",
        "remove_resource_refs",
        "remove_effect_chain_refs",
        "remove_recipe_candidate_refs",
        "remove_AB7_constraint_refs",
        "remove_P13_gate_refs",
        "remove_P14_affordance_refs",
        "active_confounder",
        "disconfirming_trace",
        "hidden_eval_only_value_rule",
        "name_only_resource",
    }
    assert required.issubset(names)
