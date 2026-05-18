from __future__ import annotations

from experiments.embodied_playground.mini_factory_chain import (
    list_mini_factory_cases,
    run_mini_factory_chain_ablations,
    run_mini_factory_chain_case,
)


def test_p17_full_chain_verified_only_after_all_steps() -> None:
    run = run_mini_factory_chain_case("full_chain_verified")
    assert run.completion_assessment.chain_complete is True
    assert run.completion_assessment.verified_step_count == run.completion_assessment.required_step_count


def test_p17_missing_first_input_blocks_chain() -> None:
    run = run_mini_factory_chain_case("missing_first_input_blocks_chain")
    assert run.completion_assessment.chain_complete is False
    assert run.chain_step_traces[0].step_status == "blocked"


def test_p17_failed_plate_step_blocks_filter() -> None:
    run = run_mini_factory_chain_case("failed_plate_step_blocks_filter")
    step2 = next(item for item in run.chain_step_traces if item.step_index == 2)
    assert step2.step_status in {"blocked", "skipped_due_residue"}


def test_p17_filter_step_without_plate_rejected() -> None:
    run = run_mini_factory_chain_case("filter_step_without_plate_rejected")
    step2 = next(item for item in run.chain_step_traces if item.step_index == 2)
    assert step2.step_status == "blocked"


def test_p17_clean_water_without_filter_chain_rejected() -> None:
    run = run_mini_factory_chain_case("clean_water_without_filter_chain_rejected")
    assert run.completion_assessment.chain_complete is False
    step3 = next(item for item in run.chain_step_traces if item.step_index == 3)
    assert step3.effect_correlation_status in {"uncorrelated", "blocked", "missing"}


def test_p17_partial_chain_no_completion() -> None:
    run = run_mini_factory_chain_case("partial_chain_no_completion")
    assert run.completion_assessment.chain_complete is False
    assert run.completion_assessment.completion_status in {"partial", "incomplete", "residue_present", "blocked"}


def test_p17_blocked_station_preserves_residue() -> None:
    run = run_mini_factory_chain_case("blocked_station_preserves_residue")
    assert run.chain_residue_records
    assert any(item.residue_kind == "blocked_station" for item in run.chain_residue_records)


def test_p17_confounder_blocks_intermediate_completion() -> None:
    run = run_mini_factory_chain_case("confounded_intermediate_blocks_completion")
    assert run.completion_assessment.chain_complete is False
    assert any(item.residue_kind == "confounder_active" for item in run.chain_residue_records)


def test_p17_disconfirming_intermediate_blocks_completion() -> None:
    run = run_mini_factory_chain_case("disconfirming_intermediate_blocks_completion")
    assert run.completion_assessment.chain_complete is False
    assert any(item.residue_kind == "disconfirmed_step" for item in run.chain_residue_records)


def test_p17_evaluator_only_chain_rule_rejected() -> None:
    run = run_mini_factory_chain_case("evaluator_only_chain_rule_rejected")
    assert run.completion_assessment.chain_complete is False
    assert "protected_evaluator_only_rule_forbidden" in run.readiness.blocked_reasons or "protected_evaluator_only_rule_forbidden" in run.falsifier_results


def test_p17_chain_candidate_does_not_become_mature_automation() -> None:
    run = run_mini_factory_chain_case("chain_candidate_does_not_become_mature_automation")
    assert run.completion_assessment.automation_claimed is False
    assert run.completion_assessment.mature_factory_skill_claimed is False


def test_p17_chain_effect_feedback_preserved() -> None:
    run = run_mini_factory_chain_case("chain_effect_feedback_preserved")
    assert run.action_effect_refs
    assert run.intermediate_verification_records
    assert any(item.effect_refs for item in run.intermediate_verification_records)


def test_p17_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_mini_factory_cases()}
    required = {
        "full_chain_verified",
        "missing_first_input_blocks_chain",
        "failed_plate_step_blocks_filter",
        "filter_step_without_plate_rejected",
        "clean_water_without_filter_chain_rejected",
        "partial_chain_no_completion",
        "blocked_station_preserves_residue",
        "confounded_intermediate_blocks_completion",
        "disconfirming_intermediate_blocks_completion",
        "evaluator_only_chain_rule_rejected",
        "chain_candidate_does_not_become_mature_automation",
        "chain_effect_feedback_preserved",
    }
    assert required.issubset(ids)


def test_p17_ablation_checks_present() -> None:
    checks = run_mini_factory_chain_ablations()
    names = {item.ablation_id for item in checks}
    required = {
        "remove_first_input",
        "remove_plate_effect_ref",
        "remove_filter_effect_ref",
        "remove_AP01_ref_for_step",
        "remove_AB7_constraint_refs",
        "remove_P16_value_chain_refs",
        "remove_P14_affordance_refs",
        "active_confounder_on_intermediate",
        "disconfirming_intermediate",
        "evaluator_only_chain_rule",
        "partial_chain_only",
    }
    assert required.issubset(names)
