from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from experiments.embodied_playground.ablation_runner import run_causal_necessity_case
from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig, SubjectWorldBridgeRun
from experiments.embodied_playground.body_action_scenarios import (
    BodyActionScenarioSpec,
    body_action_scenario_for_id,
    list_body_action_scenarios,
)
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


@dataclass(frozen=True, slots=True)
class BodyActionStepSummary:
    bridge_tick_index: int
    ap01_published_count: int
    world_submission_count: int
    effect_status: str | None
    body_delta: dict[str, object]
    inventory_delta: dict[str, object]
    world_delta_public: dict[str, object]
    ap01_request_ref: str | None
    envelope_ref: str | None
    world_effect_id: str | None
    effect_correlated_to_request: bool
    next_observation_id: str | None
    previous_effect_refs_in_next_tick: tuple[str, ...]
    manual_provider_used: bool


@dataclass(frozen=True, slots=True)
class BodyActionProofRun:
    run_id: str
    scenario_id: str
    world_scenario_id: str
    ticks: int
    drive_kinds: tuple[str, ...]
    subject_tick_used: bool
    acp01_used: bool
    manual_provider_used: bool
    ap01_published_count: int
    world_submission_count: int
    effect_feedback_count: int
    repeated_body_action_policy: str
    repeated_publish_expected: bool
    stale_candidate_detected: bool
    step_summaries: tuple[BodyActionStepSummary, ...]
    bridge_run: SubjectWorldBridgeRun
    claim_boundary: str = (
        "P10 body-action proof only: subject_tick -> ACP01 -> AP01 -> world effect -> next observation."
    )


@dataclass(frozen=True, slots=True)
class P10AblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_degradation: tuple[str, ...]
    hard_ablation_no_effect: bool
    non_informative_ablation: bool


def list_p10_scenarios() -> tuple[BodyActionScenarioSpec, ...]:
    return list_body_action_scenarios()


def run_body_action_proof_case(
    *,
    scenario_id: str,
    ticks: int | None = None,
    drive_kinds: tuple[str, ...] | None = None,
    strict_internal_mode: bool = True,
) -> BodyActionProofRun:
    spec = body_action_scenario_for_id(scenario_id)
    tick_budget = max(1, int(ticks if ticks is not None else spec.ticks))
    drives = tuple(drive_kinds if drive_kinds is not None else spec.drive_kinds)

    bridge_run = run_subject_world_bridge(
        scenario_id=spec.world_scenario_id,
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=tick_budget,
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            allow_manual_override_in_internal_mode=False,
            allow_manual_candidate_provider=not strict_internal_mode,
            internal_drive_kinds=drives,
            reject_multiple_published_requests=True,
        ),
        candidate_provider=None,
    )

    step_summaries = _build_step_summaries(bridge_run)
    repeated_policy = "basis_persistent_repeat_allowed"
    repeated_expected = tick_budget > 1 and any(
        kind in {"move_forward_intent", "turn_left_intent", "turn_right_intent"}
        for kind in drives
    )
    stale_candidate_detected = _detect_stale_repeated_action(step_summaries)
    return BodyActionProofRun(
        run_id=f"p10:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        world_scenario_id=spec.world_scenario_id,
        ticks=tick_budget,
        drive_kinds=drives,
        subject_tick_used=bridge_run.subject_tick_used_any,
        acp01_used=bridge_run.internal_candidate_producer_used_any,
        manual_provider_used=any(step.manual_candidate_input for step in bridge_run.steps),
        ap01_published_count=sum(step.ap01_published_request_count for step in bridge_run.steps),
        world_submission_count=bridge_run.world_submissions_count,
        effect_feedback_count=sum(1 for step in bridge_run.steps if step.observation_previous_effect_refs),
        repeated_body_action_policy=repeated_policy,
        repeated_publish_expected=repeated_expected,
        stale_candidate_detected=stale_candidate_detected,
        step_summaries=step_summaries,
        bridge_run=bridge_run,
    )


def run_body_action_proof_matrix() -> tuple[BodyActionProofRun, ...]:
    return tuple(
        run_body_action_proof_case(scenario_id=spec.scenario_id)
        for spec in list_body_action_scenarios()
    )


def run_p10_ablation_checks() -> tuple[P10AblationCheck, ...]:
    ablation_plan = (
        ("no_drive_basis", "visible_item_pickup_available"),
        ("no_public_object_basis", "water_need_no_visible_water"),
        ("no_proximity_basis", "pickup_without_proximity"),
        ("no_capacity_basis", "inventory_capacity_block"),
        ("no_action_surface_basis", "visible_item_pickup_available"),
        ("no_acp01", "visible_item_pickup_available"),
        ("no_ap01", "visible_item_pickup_available"),
        ("no_effect_feedback", "previous_blocked_effect_revalidation"),
    )
    checks: list[P10AblationCheck] = []
    for ablation_id, scenario_id in ablation_plan:
        run = run_causal_necessity_case(
            scenario_id=scenario_id,
            ablation_id=ablation_id,
            strict_mode=True,
            ticks=2,
        )
        ablated = run.ablation_traces[0]
        checks.append(
            P10AblationCheck(
                ablation_id=ablation_id,
                scenario_id=scenario_id,
                expected_degradation=run.expected_degradations[0].expected,
                observed_degradation=run.observed_degradations,
                hard_ablation_no_effect=(
                    ablated.ablation_outcome_class.value == "hard_ablation_no_effect"
                ),
                non_informative_ablation=(
                    ablated.ablation_outcome_class.value == "non_informative_ablation"
                ),
            )
        )
    # P10-specific explicit no-inventory-item basis gate for drop.
    drop_no_inventory = run_body_action_proof_case(
        scenario_id="internal_drop_without_inventory_no_publish",
        strict_internal_mode=True,
    )
    drop_observed = []
    if drop_no_inventory.ap01_published_count == 0:
        drop_observed.append("no_publication")
    if drop_no_inventory.world_submission_count == 0:
        drop_observed.append("no_world_submission")
    if not any(step.effect_status for step in drop_no_inventory.step_summaries):
        drop_observed.append("no_effect")
    checks.append(
        P10AblationCheck(
            ablation_id="remove_inventory_item_basis",
            scenario_id="internal_drop_without_inventory_no_publish",
            expected_degradation=("no_candidate", "no_publication", "no_world_submission"),
            observed_degradation=tuple(drop_observed),
            hard_ablation_no_effect=False,
            non_informative_ablation=False,
        )
    )
    # Alias existing no-action-surface ablation under P10 wording.
    body_surface = run_causal_necessity_case(
        scenario_id="visible_item_pickup_available",
        ablation_id="no_action_surface_basis",
        strict_mode=True,
        ticks=2,
    )
    body_surface_trace = body_surface.ablation_traces[0]
    checks.append(
        P10AblationCheck(
            ablation_id="remove_body_action_surface",
            scenario_id="visible_item_pickup_available",
            expected_degradation=("no_candidate", "no_publication"),
            observed_degradation=body_surface.observed_degradations,
            hard_ablation_no_effect=(
                body_surface_trace.ablation_outcome_class.value == "hard_ablation_no_effect"
            ),
            non_informative_ablation=(
                body_surface_trace.ablation_outcome_class.value == "non_informative_ablation"
            ),
        )
    )
    return tuple(checks)


def _build_step_summaries(run: SubjectWorldBridgeRun) -> tuple[BodyActionStepSummary, ...]:
    summaries: list[BodyActionStepSummary] = []
    steps = tuple(run.steps)
    for index, step in enumerate(steps):
        payload = step.world_effect_payload or {}
        next_prev_refs = ()
        if index + 1 < len(steps):
            next_prev_refs = tuple(steps[index + 1].observation_previous_effect_refs)
        summaries.append(
            BodyActionStepSummary(
                bridge_tick_index=step.bridge_tick_index,
                ap01_published_count=step.ap01_published_request_count,
                world_submission_count=1 if step.world_submission_attempted else 0,
                effect_status=step.world_effect_status,
                body_delta=dict(payload.get("body_delta", {}) if isinstance(payload, dict) else {}),
                inventory_delta=dict(payload.get("inventory_delta", {}) if isinstance(payload, dict) else {}),
                world_delta_public=dict(payload.get("world_delta_public", {}) if isinstance(payload, dict) else {}),
                ap01_request_ref=step.ap01_request_ref,
                envelope_ref=step.envelope_ref,
                world_effect_id=step.world_effect_id,
                effect_correlated_to_request=(
                    not step.world_submission_attempted
                    or (
                        bool(step.ap01_request_ref)
                        and bool(step.envelope_ref)
                        and bool(step.world_effect_id)
                    )
                ),
                next_observation_id=step.next_observation_id,
                previous_effect_refs_in_next_tick=next_prev_refs,
                manual_provider_used=step.manual_candidate_input,
            )
        )
    return tuple(summaries)


def _detect_stale_repeated_action(step_summaries: tuple[BodyActionStepSummary, ...]) -> bool:
    submitted = tuple(step for step in step_summaries if step.world_submission_count > 0)
    if len(submitted) <= 1:
        return False
    request_refs = [step.ap01_request_ref for step in submitted]
    if any(not ref for ref in request_refs):
        return True
    if len(set(request_refs)) != len(request_refs):
        return True
    return any(not step.effect_correlated_to_request for step in submitted)
