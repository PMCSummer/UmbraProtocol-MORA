from __future__ import annotations

from experiments.embodied_playground.recipe_precursor_learning import (
    list_recipe_precursor_cases,
    run_recipe_precursor_ablations,
    run_recipe_precursor_learning_case,
)


def test_p15_one_success_trace_provisional_only() -> None:
    run = run_recipe_precursor_learning_case("one_success_trace_provisional_only")
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status in {"weak_candidate", "provisional_candidate"}
    assert run.maturity_assessment.mature_recipe_count == 0


def test_p15_repeated_consistent_traces_strengthen_candidate_without_final_truth() -> None:
    run = run_recipe_precursor_learning_case("repeated_consistent_traces_candidate_strengthens")
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status in {"repeated_trace_supported", "provisional_candidate"}
    assert run.recipe_candidates[0].fact_claimed is False
    assert run.recipe_candidates[0].cause_confirmed is False


def test_p15_hidden_recipe_only_no_candidate() -> None:
    run = run_recipe_precursor_learning_case("hidden_recipe_only_no_candidate")
    assert run.falsifier_results["hidden_recipe_leak"] is False
    assert (not run.recipe_candidates) or all(item.maturity_status == "blocked" for item in run.recipe_candidates)


def test_p15_visible_station_no_trace_no_recipe() -> None:
    run = run_recipe_precursor_learning_case("visible_station_no_trace_no_recipe")
    assert run.lived_trace_records == ()
    assert run.recipe_candidates == ()


def test_p15_station_success_without_input_refs_blocked() -> None:
    run = run_recipe_precursor_learning_case("station_success_without_input_refs_blocked")
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status == "blocked"
    assert "public_input_refs" in run.recipe_candidates[0].missing_evidence


def test_p15_station_success_without_effect_refs_blocked() -> None:
    run = run_recipe_precursor_learning_case("station_success_without_effect_refs_blocked")
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status == "blocked"
    assert "public_effect_refs" in run.recipe_candidates[0].missing_evidence


def test_p15_confounded_station_effect_blocks_clean_maturity() -> None:
    run = run_recipe_precursor_learning_case("confounded_station_effect")
    assert run.confounder_records
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status in {"weak_candidate", "blocked"}
    assert run.maturity_assessment.mature_recipe_count == 0


def test_p15_confounder_disconfirmed_by_repetition_strengthens_but_not_mature() -> None:
    run = run_recipe_precursor_learning_case("confounder_disconfirmed_by_repetition")
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status in {"provisional_candidate", "repeated_trace_supported"}
    assert run.maturity_assessment.mature_recipe_count == 0


def test_p15_disconfirming_trace_blocks_maturity() -> None:
    run = run_recipe_precursor_learning_case("disconfirming_trace_blocks_maturity")
    assert run.disconfirming_records
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status == "blocked"


def test_p15_delayed_station_effect_preserves_delay() -> None:
    run = run_recipe_precursor_learning_case("delayed_station_effect")
    assert run.lived_trace_records
    assert any(item.timing_refs for item in run.lived_trace_records)
    assert run.falsifier_results["delayed_effect_as_immediate_recipe"] is False


def test_p15_ambiguous_output_preserves_uncertainty() -> None:
    run = run_recipe_precursor_learning_case("ambiguous_output_effect")
    assert run.recipe_candidates
    assert run.recipe_candidates[0].maturity_status in {"weak_candidate", "blocked"}
    assert run.maturity_assessment.mature_recipe_count == 0


def test_p15_recipe_candidate_does_not_emit_action() -> None:
    run = run_recipe_precursor_learning_case("recipe_candidate_does_not_emit_action")
    assert run.action_request_emitted is False
    assert run.world_submission_emitted is False
    assert all(item.action_request_emitted is False for item in run.recipe_candidates)
    assert all(item.world_submission_emitted is False for item in run.recipe_candidates)


def test_p15_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_recipe_precursor_cases()}
    required = {
        "one_success_trace_provisional_only",
        "repeated_consistent_traces_candidate_strengthens",
        "hidden_recipe_only_no_candidate",
        "visible_station_no_trace_no_recipe",
        "station_success_without_input_refs_blocked",
        "station_success_without_effect_refs_blocked",
        "confounded_station_effect",
        "confounder_disconfirmed_by_repetition",
        "disconfirming_trace_blocks_maturity",
        "delayed_station_effect",
        "ambiguous_output_effect",
        "recipe_candidate_does_not_emit_action",
    }
    assert required.issubset(ids)


def test_p15_ablation_checks_present() -> None:
    checks = run_recipe_precursor_ablations()
    names = {item.ablation_id for item in checks}
    required = {
        "no_lived_trace",
        "no_effect_refs",
        "no_input_refs",
        "one_trace_only",
        "remove_repetition",
        "remove_confounder_records",
        "disconfirming_trace",
        "hidden_eval_only_recipe",
        "remove_P13_gate_refs",
        "ambiguous_output",
    }
    assert required.issubset(names)
