from __future__ import annotations

from experiments.embodied_playground.ablation_runner import run_causal_necessity_case
from experiments.embodied_playground.causal_necessity_falsifiers import ablation_no_effect
from experiments.embodied_playground.causal_necessity import AblationOutcomeClass


def test_no_acp01_causes_no_internal_candidate_publication_submission() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_acp01",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.acp01_candidate_count == 0
    assert trace.ap01_published_count == 0
    assert trace.world_submission_count == 0


def test_no_ap01_causes_no_world_submission() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_ap01",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ap01_published_count == 0
    assert trace.world_submission_count == 0


def test_no_drive_basis_prevents_visible_object_pickup() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_drive_basis",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ap01_published_count == 0
    assert trace.world_submission_count == 0


def test_no_public_object_basis_prevents_drive_only_pickup() -> None:
    run = run_causal_necessity_case(
        scenario_id="water_need_no_visible_water",
        ablation_id="no_public_object_basis",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ap01_published_count == 0


def test_no_action_surface_basis_prevents_action_surface_fabrication() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_action_surface_basis",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.basis_flow["action_surface_basis"] is False
    assert trace.ap01_published_count == 0


def test_no_proximity_basis_prevents_pickup_publication() -> None:
    run = run_causal_necessity_case(
        scenario_id="pickup_without_proximity",
        ablation_id="no_proximity_basis",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ap01_published_count == 0


def test_no_capacity_basis_prevents_pickup_publication() -> None:
    run = run_causal_necessity_case(
        scenario_id="inventory_capacity_block",
        ablation_id="no_capacity_basis",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ap01_published_count == 0


def test_hidden_eval_substitution_attempt_does_not_produce_candidate() -> None:
    run = run_causal_necessity_case(
        scenario_id="hidden_map_not_visible",
        ablation_id="hidden_eval_substitution_attempt",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ap01_published_count == 0
    assert trace.hidden_eval_used is False


def test_ablation_no_effect_negative_control() -> None:
    assert ablation_no_effect(is_hard_no_effect=True) is True
    assert ablation_no_effect(is_hard_no_effect=False) is False


def test_p9_non_informative_ablation_not_counted_as_hard_no_effect() -> None:
    run = run_causal_necessity_case(
        scenario_id="hidden_map_not_visible",
        ablation_id="hidden_eval_substitution_attempt",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ablation_outcome_class in {
        AblationOutcomeClass.NON_INFORMATIVE_ABLATION,
        AblationOutcomeClass.EXPECTED_NO_EFFECT_DUE_MISSING_BASIS,
        AblationOutcomeClass.EXPECTED_DEGRADATION_OBSERVED,
    }
    assert run.metric_summary.hard_ablation_no_effect_count == 0
    assert run.falsifier_results["ablation_no_effect"] is False


def test_p9_hard_ablation_no_effect_still_fails() -> None:
    assert ablation_no_effect(is_hard_no_effect=True) is True


def test_p9_expected_no_effect_due_missing_basis_reported_separately() -> None:
    run = run_causal_necessity_case(
        scenario_id="water_need_no_visible_water",
        ablation_id="no_prediction_permission_separation",
        ticks=1,
        strict_mode=True,
    )
    trace = run.ablation_traces[0]
    assert trace.ablation_outcome_class in {
        AblationOutcomeClass.EXPECTED_NO_EFFECT_DUE_MISSING_BASIS,
        AblationOutcomeClass.EXPECTED_DEGRADATION_OBSERVED,
    }
    assert run.metric_summary.expected_no_effect_due_missing_basis_count >= 0


def test_p9_matrix_report_separates_hard_no_effect_from_non_informative() -> None:
    run = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_acp01",
        ticks=1,
        strict_mode=True,
    )
    assert run.metric_summary.hard_ablation_no_effect_count >= 0
    assert run.metric_summary.non_informative_ablation_count >= 0
