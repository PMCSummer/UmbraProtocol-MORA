from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .station_affordance import StationAffordanceProofRun

_OVERCLAIM_MARKERS: tuple[str, ...] = (
    "learned recipe",
    "recipe learning",
    "automation",
    "general tool use",
    "consciousness",
    "general intelligence",
)
_OVERCLAIM_GUARDS: tuple[str, ...] = (
    "not recipe learning",
    "no recipe learning",
    "bounded station affordance",
    "no automation",
    "no consciousness",
)


def station_use_without_affordance(*, run: StationAffordanceProofRun) -> bool:
    attempted = run.station_use_candidate_status in {"proposed", "published"}
    return attempted and run.affordance_status not in {"usable", "missing_input", "blocked", "not_proximate"}


def station_visible_as_usable(*, run: StationAffordanceProofRun) -> bool:
    return (
        run.public_station_basis.visible
        and run.station_use_candidate_status in {"proposed", "published"}
        and run.affordance_status == "usable"
        and (run.proximity_status != "proximate" or run.input_status not in {"input_available", "input_not_required"})
    )


def station_use_without_proximity(*, run: StationAffordanceProofRun) -> bool:
    return run.effect_status == "succeeded" and run.proximity_status != "proximate"


def station_use_without_input(*, run: StationAffordanceProofRun) -> bool:
    return run.effect_status == "succeeded" and run.input_status == "missing_input"


def protected_eval_rule_used_by_subject(*, run: StationAffordanceProofRun) -> bool:
    if run.protected_evaluator_only_rule_present and run.ap01_publication_status == "published":
        return True
    return run.public_station_basis.hidden_recipe_used


def scenario_label_station_use(*, run: StationAffordanceProofRun) -> bool:
    return run.public_station_basis.scenario_label_used


def action_space_as_station_permission(*, run: StationAffordanceProofRun) -> bool:
    return (
        run.public_station_basis.action_surface_supports_use_station
        and not run.public_station_basis.visible
        and run.station_use_candidate_status in {"proposed", "published"}
    )


def station_effect_without_ap01(*, run: StationAffordanceProofRun) -> bool:
    effect_counted_as_subject_use = (
        run.station_use_candidate_status == "published"
        or run.world_submission_status == "submitted"
        or (run.attempt_record is not None and run.attempt_record.outcome == "succeeded")
    )
    return bool(run.effect_refs) and effect_counted_as_subject_use and run.ap01_publication_status != "published"


def station_request_as_success(*, run: StationAffordanceProofRun) -> bool:
    return run.ap01_publication_status == "published" and run.effect_status == "not_attempted"


def blocked_station_claimed_success(*, run: StationAffordanceProofRun) -> bool:
    return run.blocked_status == "blocked" and run.effect_status == "succeeded"


def missing_input_erased(*, run: StationAffordanceProofRun) -> bool:
    return run.input_status == "missing_input" and not run.missing_input_refs


def inventory_delta_without_station_effect(*, run: StationAffordanceProofRun) -> bool:
    return bool(run.inventory_delta_refs) and not run.effect_refs


def world_delta_without_station_effect(*, run: StationAffordanceProofRun) -> bool:
    return bool(run.world_delta_refs) and not run.effect_refs


def recipe_or_mature_rule_result_in_p14(*, run: StationAffordanceProofRun) -> bool:
    if run.mature_schema_created:
        return True
    return any("recipe_output" in ref.lower() or "crafted" in ref.lower() for ref in run.effect_refs)


def one_shot_station_schema_maturity(*, run: StationAffordanceProofRun) -> bool:
    return run.mature_schema_created


def station_affordance_report_overclaims(*, claim_boundary: str) -> bool:
    lowered = claim_boundary.lower()
    if any(guard in lowered for guard in _OVERCLAIM_GUARDS):
        return False
    return any(marker in lowered for marker in _OVERCLAIM_MARKERS)


def station_use_crosses_acp01_boundary(*, run: StationAffordanceProofRun) -> bool:
    if not run.acp01_involved:
        return False
    return run.station_use_candidate_status == "published" and run.acp01_candidate_status != "proposed"


def station_use_crosses_ap01_boundary(*, run: StationAffordanceProofRun) -> bool:
    return run.world_submission_status == "submitted" and run.ap01_publication_status != "published"


def evaluate_station_falsifiers(*, run: StationAffordanceProofRun, claim_boundary: str) -> dict[str, bool]:
    return {
        "station_use_without_affordance": station_use_without_affordance(run=run),
        "station_visible_as_usable": station_visible_as_usable(run=run),
        "station_use_without_proximity": station_use_without_proximity(run=run),
        "station_use_without_input": station_use_without_input(run=run),
        "protected_eval_rule_used_by_subject": protected_eval_rule_used_by_subject(run=run),
        "scenario_label_station_use": scenario_label_station_use(run=run),
        "action_space_as_station_permission": action_space_as_station_permission(run=run),
        "station_effect_without_ap01": station_effect_without_ap01(run=run),
        "station_request_as_success": station_request_as_success(run=run),
        "blocked_station_claimed_success": blocked_station_claimed_success(run=run),
        "missing_input_erased": missing_input_erased(run=run),
        "inventory_delta_without_station_effect": inventory_delta_without_station_effect(run=run),
        "world_delta_without_station_effect": world_delta_without_station_effect(run=run),
        "recipe_or_mature_rule_result_in_p14": recipe_or_mature_rule_result_in_p14(run=run),
        "one_shot_station_schema_maturity": one_shot_station_schema_maturity(run=run),
        "station_affordance_report_overclaims": station_affordance_report_overclaims(claim_boundary=claim_boundary),
        "station_use_crosses_acp01_boundary": station_use_crosses_acp01_boundary(run=run),
        "station_use_crosses_ap01_boundary": station_use_crosses_ap01_boundary(run=run),
    }
