from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.station_affordance import (
    StationAffordanceProofRun,
    StationAffordanceRecord,
    StationUseAttemptRecord,
    run_station_affordance_case,
)
from experiments.embodied_playground.station_falsifiers import (
    action_space_as_station_permission,
    blocked_station_claimed_success,
    evaluate_station_falsifiers,
    inventory_delta_without_station_effect,
    missing_input_erased,
    one_shot_station_schema_maturity,
    protected_eval_rule_used_by_subject,
    recipe_or_mature_rule_result_in_p14,
    scenario_label_station_use,
    station_affordance_report_overclaims,
    station_effect_without_ap01,
    station_request_as_success,
    station_use_crosses_acp01_boundary,
    station_use_crosses_ap01_boundary,
    station_use_without_affordance,
    station_use_without_input,
    station_use_without_proximity,
    station_visible_as_usable,
    world_delta_without_station_effect,
)


def _base_run() -> StationAffordanceProofRun:
    return run_station_affordance_case("station_proximate_with_input")


def test_p14_falsifier_station_use_without_affordance_negative_control() -> None:
    run = _base_run()
    run = replace(run, station_use_candidate_status="published", affordance_status="insufficient_public_basis")
    assert station_use_without_affordance(run=run)


def test_p14_falsifier_station_visible_as_usable_negative_control() -> None:
    run = _base_run()
    run = replace(run, proximity_status="not_proximate", input_status="missing_input")
    assert station_visible_as_usable(run=run)


def test_p14_falsifier_station_use_without_proximity_negative_control() -> None:
    run = _base_run()
    run = replace(run, proximity_status="not_proximate", effect_status="succeeded")
    assert station_use_without_proximity(run=run)


def test_p14_falsifier_station_use_without_input_negative_control() -> None:
    run = _base_run()
    run = replace(run, input_status="missing_input", effect_status="succeeded")
    assert station_use_without_input(run=run)


def test_p14_falsifier_protected_eval_rule_used_by_subject_negative_control() -> None:
    run = _base_run()
    run = replace(run, protected_evaluator_only_rule_present=True, ap01_publication_status="published")
    assert protected_eval_rule_used_by_subject(run=run)


def test_p14_falsifier_scenario_label_station_use_negative_control() -> None:
    run = _base_run()
    basis = replace(run.public_station_basis, scenario_label_used=True)
    run = replace(run, public_station_basis=basis)
    assert scenario_label_station_use(run=run)


def test_p14_falsifier_action_space_as_station_permission_negative_control() -> None:
    run = _base_run()
    basis = replace(run.public_station_basis, visible=False, action_surface_supports_use_station=True)
    run = replace(run, public_station_basis=basis, station_use_candidate_status="published")
    assert action_space_as_station_permission(run=run)


def test_p14_falsifier_station_effect_without_ap01_negative_control() -> None:
    run = _base_run()
    run = replace(run, ap01_publication_status="not_attempted", station_use_candidate_status="published", world_submission_status="submitted")
    assert station_effect_without_ap01(run=run)


def test_p14_falsifier_station_request_as_success_negative_control() -> None:
    run = _base_run()
    run = replace(run, effect_status="not_attempted", ap01_publication_status="published")
    assert station_request_as_success(run=run)


def test_p14_falsifier_blocked_station_claimed_success_negative_control() -> None:
    run = _base_run()
    run = replace(run, blocked_status="blocked", effect_status="succeeded")
    assert blocked_station_claimed_success(run=run)


def test_p14_falsifier_missing_input_erased_negative_control() -> None:
    run = _base_run()
    run = replace(run, input_status="missing_input", missing_input_refs=())
    assert missing_input_erased(run=run)


def test_p14_falsifier_inventory_delta_without_station_effect_negative_control() -> None:
    run = _base_run()
    run = replace(run, effect_refs=(), inventory_delta_refs=("effect:1:inventory",))
    assert inventory_delta_without_station_effect(run=run)


def test_p14_falsifier_world_delta_without_station_effect_negative_control() -> None:
    run = _base_run()
    run = replace(run, effect_refs=(), world_delta_refs=("effect:1:world",))
    assert world_delta_without_station_effect(run=run)


def test_p14_falsifier_recipe_or_mature_rule_result_in_p14_negative_control() -> None:
    run = _base_run()
    run = replace(run, mature_schema_created=True)
    assert recipe_or_mature_rule_result_in_p14(run=run)


def test_p14_falsifier_one_shot_station_schema_maturity_negative_control() -> None:
    run = _base_run()
    run = replace(run, mature_schema_created=True)
    assert one_shot_station_schema_maturity(run=run)


def test_p14_falsifier_station_affordance_report_overclaims_negative_control() -> None:
    assert station_affordance_report_overclaims(claim_boundary="This proves recipe learning, automation, and consciousness.")


def test_p14_falsifier_station_use_crosses_acp01_boundary_negative_control() -> None:
    run = _base_run()
    run = replace(run, acp01_involved=True, acp01_candidate_status="not_proposed", station_use_candidate_status="published")
    assert station_use_crosses_acp01_boundary(run=run)


def test_p14_falsifier_station_use_crosses_ap01_boundary_negative_control() -> None:
    run = _base_run()
    run = replace(run, ap01_publication_status="not_attempted", world_submission_status="submitted")
    assert station_use_crosses_ap01_boundary(run=run)


def test_p14_falsifier_suite_smoke_negative_control() -> None:
    run = _base_run()
    basis = StationAffordanceRecord(
        station_ref="station:alpha",
        visible=False,
        reachable=False,
        proximate=False,
        required_input_refs=("item:ore",),
        available_input_refs=(),
        missing_input_refs=(),
        blocked_reasons=(),
        usable_status="insufficient_public_basis",
        affordance_basis_refs=(),
        action_surface_supports_use_station=True,
        hidden_recipe_used=True,
        scenario_label_used=True,
    )
    attempt = StationUseAttemptRecord(
        attempt_id="bad:attempt",
        ap01_request_ref=None,
        station_ref="station:alpha",
        input_refs=(),
        effect_ref=None,
        correlation_status="ambiguous",
        outcome="not_attempted",
        inventory_delta={},
        world_delta={},
        recipe_claimed=False,
        mature_schema_created=False,
        hidden_recipe_used=False,
    )
    bad = replace(
        run,
        public_station_basis=basis,
        affordance_status="insufficient_public_basis",
        station_use_candidate_status="published",
        ap01_publication_status="not_attempted",
        world_submission_status="submitted",
        effect_status="succeeded",
        effect_refs=(),
        inventory_delta_refs=("x",),
        world_delta_refs=("y",),
        missing_input_refs=(),
        blocked_status="blocked",
        protected_evaluator_only_rule_present=True,
        mature_schema_created=True,
        acp01_involved=True,
        acp01_candidate_status="not_proposed",
        attempt_record=attempt,
    )
    result = evaluate_station_falsifiers(run=bad, claim_boundary="recipe learning and consciousness")
    assert result["station_use_without_affordance"] is True
    assert result["station_effect_without_ap01"] is False
    assert result["station_affordance_report_overclaims"] is True
