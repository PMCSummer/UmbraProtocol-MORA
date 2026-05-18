from __future__ import annotations

from experiments.embodied_playground.delayed_credit_learning import (
    list_delayed_credit_cases,
    run_delayed_credit_ablation_checks,
    run_delayed_credit_learning_case,
)


def test_p13_immediate_clear_effect_only_provisional_not_mature() -> None:
    run = run_delayed_credit_learning_case("immediate_clear_effect")
    assert run.candidate_credit_links
    assert all(item.maturity_status in {"provisional_candidate", "weak_candidate"} for item in run.candidate_credit_links)
    assert run.maturity_assessment.mature_schema_count == 0


def test_p13_delayed_effect_uses_delay_window() -> None:
    run = run_delayed_credit_learning_case("delayed_effect_correct_window")
    assert run.delayed_effect_records
    assert run.candidate_credit_links[0].correlation_status in {"delayed_possible", "ambiguous"}
    assert run.candidate_credit_links[0].delay_window


def test_p13_wrong_delay_window_blocks_credit() -> None:
    run = run_delayed_credit_learning_case("delayed_effect_wrong_window")
    assert run.candidate_credit_links
    assert run.candidate_credit_links[0].correlation_status in {"insufficient_evidence", "disconfirmed"}
    assert run.candidate_credit_links[0].maturity_status == "blocked"


def test_p13_confounded_effect_keeps_confounder_active() -> None:
    run = run_delayed_credit_learning_case("confounded_effect_two_precursors")
    assert run.confounder_records
    assert run.confounder_records[0].status in {"active", "unresolved"}
    assert run.falsifier_results["confounder_credit_leak"] is False


def test_p13_repetition_can_weaken_confounder_without_maturing_schema() -> None:
    run = run_delayed_credit_learning_case("confounder_disconfirmed_by_repetition")
    assert len(run.episode_traces) >= 2
    assert run.confounder_records
    assert run.confounder_records[0].status == "disconfirmed"
    assert run.maturity_assessment.mature_schema_count == 0


def test_p13_one_shot_correlation_not_mature_schema() -> None:
    run = run_delayed_credit_learning_case("spurious_one_shot_correlation")
    assert run.maturity_assessment.mature_schema_count == 0
    assert run.falsifier_results["one_shot_mature_schema"] is False


def test_p13_disconfirming_episode_lowers_credit() -> None:
    run = run_delayed_credit_learning_case("disconfirming_episode")
    assert any(item.correlation_status in {"disconfirmed", "insufficient_evidence"} for item in run.candidate_credit_links)
    assert run.falsifier_results["disconfirming_trace_ignored"] is False


def test_p13_hidden_recipe_only_no_learning() -> None:
    run = run_delayed_credit_learning_case("hidden_recipe_only")
    assert run.candidate_credit_links == ()
    assert run.falsifier_results["hidden_recipe_leak"] is False


def test_p13_ambiguous_public_evidence_preserves_uncertainty() -> None:
    run = run_delayed_credit_learning_case("ambiguous_public_evidence")
    assert any(item.correlation_status == "ambiguous" for item in run.candidate_credit_links)
    assert run.maturity_assessment.mature_schema_count == 0


def test_p13_delayed_and_confounded_mixed_preserves_both() -> None:
    run = run_delayed_credit_learning_case("delayed_and_confounded_mixed")
    assert run.delayed_effect_records
    assert run.confounder_records
    assert run.falsifier_results["delayed_effect_misattribution"] is False
    assert run.falsifier_results["confounder_credit_leak"] is False


def test_p13_scenario_registry_contains_required_cases() -> None:
    ids = {item.scenario_id for item in list_delayed_credit_cases()}
    required = {
        "immediate_clear_effect",
        "delayed_effect_correct_window",
        "delayed_effect_wrong_window",
        "confounded_effect_two_precursors",
        "confounder_disconfirmed_by_repetition",
        "spurious_one_shot_correlation",
        "disconfirming_episode",
        "hidden_recipe_only",
        "ambiguous_public_evidence",
        "delayed_and_confounded_mixed",
    }
    assert required.issubset(ids)


def test_p13_ablation_checks_present() -> None:
    checks = run_delayed_credit_ablation_checks()
    names = {item.ablation_id for item in checks}
    required = {
        "no_effect_refs",
        "no_precursor_refs",
        "no_timing_refs",
        "remove_repetition",
        "remove_confounder_record",
        "disconfirming_episode",
        "hidden_eval_only",
        "request_without_effect",
        "ambiguous_public_evidence",
    }
    assert required.issubset(names)
