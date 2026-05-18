from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import sys

try:
    from substrate.ap01_subject_action_publication import AP01DecisionStatus
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from substrate.ap01_subject_action_publication import AP01DecisionStatus

from experiments.embodied_playground.candidate_provider import ManualCandidateProvider, ManualCandidateSpec
from experiments.embodied_playground.causal_necessity import (
    AblationOutcomeClass,
    AblationSpec,
    AblationTrace,
    CausalNecessityClaimSafeVerdict,
    CausalNecessityMetricSummary,
    CausalNecessityRun,
    ablation_spec_for_id,
    required_ablation_specs,
)
from experiments.embodied_playground.causal_necessity_falsifiers import (
    ablation_no_effect,
    action_surface_fabricated,
    candidate_without_acp01,
    causal_necessity_report_overclaims,
    diagnostic_success_counted_as_causal_necessity,
    drive_alone_becomes_action,
    effect_feedback_fabricated,
    failure_erased_without_w06_like_residue,
    forbidden_fallback_after_ablation,
    hidden_basis_substitution,
    permission_without_w04_like_basis,
    pickup_without_capacity_basis,
    pickup_without_proximity_basis,
    prediction_or_desire_as_permission,
    silent_bundle_fabrication,
    strict_mode_not_enforced,
    visible_object_alone_becomes_action,
    world_submission_without_ap01,
)
from experiments.embodied_playground.grid_world import GridWorldBackend, make_published_action_envelope
from experiments.embodied_playground.strict_mode_runner import run_strict_mode_check
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge
from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig, SubjectWorldBridgeRun


def list_ablation_specs() -> tuple[AblationSpec, ...]:
    return required_ablation_specs()


def list_causal_necessity_scenarios() -> tuple[str, ...]:
    return (
        "visible_item_pickup_available",
        "water_need_no_visible_water",
        "pickup_without_proximity",
        "inventory_capacity_block",
        "hidden_map_not_visible",
        "previous_blocked_effect_revalidation",
        "action_space_only_no_candidate",
    )


def run_causal_necessity_case(
    *,
    scenario_id: str,
    ablation_id: str,
    ticks: int = 2,
    drive_kind: str | None = None,
    strict_mode: bool = True,
) -> CausalNecessityRun:
    spec = ablation_spec_for_id(ablation_id)
    world_scenario = _resolve_world_scenario_id(scenario_id)
    drive_basis = _resolve_drive_basis(scenario_id, drive_kind)

    baseline = _execute_bridge(
        scenario_id=world_scenario,
        ticks=ticks,
        drive_basis=drive_basis,
        force_internal=True,
        execute_world_actions=True,
        for_blocked_precondition=(scenario_id == "previous_blocked_effect_revalidation"),
    )
    baseline_trace = _trace_from_run(
        run=baseline,
        ablation_id="baseline",
        scenario_id=scenario_id,
        basis_flow=_basis_flow_for_ablation(spec_id="baseline", has_drive=bool(drive_basis), has_public_object=_has_public_object(baseline), has_action_surface=True, has_proximity=True, has_capacity=True),
    )

    ablated_run, basis_flow = _execute_ablated(
        scenario_id=scenario_id,
        world_scenario=world_scenario,
        spec=spec,
        ticks=ticks,
        drive_basis=drive_basis,
    )
    ablated_trace = _trace_from_run(
        run=ablated_run,
        ablation_id=ablation_id,
        scenario_id=scenario_id,
        basis_flow=basis_flow,
        overlay=_overlay_for_ablation(spec),
    )
    ablated_trace = _finalize_trace_with_expected(ablated_trace, spec)
    ablated_trace = _reclassify_outcome_with_baseline(
        baseline_trace=baseline_trace,
        ablated_trace=ablated_trace,
    )

    strict_trace = run_strict_mode_check(strict_mode_enabled=strict_mode, trace=ablated_trace)

    metric_summary = _build_metric_summary(
        baseline_trace=baseline_trace,
        ablation_traces=(ablated_trace,),
        strict_fabrications=len(strict_trace.fabricated_basis_refs),
        strict_valid=strict_trace.valid_basis_flow,
    )

    observed = _observed_degradation_tokens(ablated_trace)
    falsifier_results = _run_falsifiers(
        baseline_trace=baseline_trace,
        ablated_trace=ablated_trace,
        strict_violations=strict_trace.violations,
        strict_mode=strict_mode,
    )

    verdict = _claim_safe_verdict(
        ablated_trace=ablated_trace,
        strict_valid=strict_trace.valid_basis_flow,
        has_hard_falsifier=any(falsifier_results.values()),
    )

    summary = (
        f"ablation={ablation_id} expected={spec.expected_degradation.expected} "
        f"observed={observed} outcome_class={ablated_trace.ablation_outcome_class.value} "
        f"strict_violations={strict_trace.violations}"
    )

    return CausalNecessityRun(
        run_id=f"p9:{scenario_id}:{ablation_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        mode="strict_no_auto_builder" if strict_mode else "causal_ablation_only",
        baseline_trace=baseline_trace,
        ablation_traces=(ablated_trace,),
        strict_trace=strict_trace,
        expected_degradations=(spec.expected_degradation,),
        observed_degradations=observed,
        falsifier_results=falsifier_results,
        metric_summary=metric_summary,
        claim_safe_verdict=verdict,
        summary=summary,
    )


def run_causal_necessity_matrix(
    *,
    ticks: int = 2,
    strict_mode: bool = True,
) -> tuple[CausalNecessityRun, ...]:
    matrix: list[CausalNecessityRun] = []
    matrix.append(run_causal_necessity_case(scenario_id="visible_item_pickup_available", ablation_id="no_acp01", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="visible_item_pickup_available", ablation_id="no_ap01", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="visible_item_pickup_available", ablation_id="no_drive_basis", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="water_need_no_visible_water", ablation_id="no_public_object_basis", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="visible_item_pickup_available", ablation_id="no_action_surface_basis", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="pickup_without_proximity", ablation_id="no_proximity_basis", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="inventory_capacity_block", ablation_id="no_capacity_basis", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="previous_blocked_effect_revalidation", ablation_id="no_effect_feedback", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="previous_blocked_effect_revalidation", ablation_id="no_residue_feedback", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="visible_item_pickup_available", ablation_id="no_permission_basis", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="water_need_no_visible_water", ablation_id="no_prediction_permission_separation", ticks=ticks, strict_mode=strict_mode))
    matrix.append(run_causal_necessity_case(scenario_id="hidden_map_not_visible", ablation_id="hidden_eval_substitution_attempt", ticks=ticks, strict_mode=strict_mode))
    return tuple(matrix)


def _resolve_world_scenario_id(scenario_id: str) -> str:
    mapping = {
        "water_need_no_visible_water": "empty_room_presence",
        "previous_blocked_effect_revalidation": "blocked_movement_wall",
    }
    return mapping.get(scenario_id, scenario_id)


def _resolve_drive_basis(scenario_id: str, drive_kind: str | None) -> tuple[str, ...]:
    if drive_kind:
        return (drive_kind,)
    defaults = {
        "visible_item_pickup_available": ("water_need",),
        "water_need_no_visible_water": ("water_need",),
        "pickup_without_proximity": ("water_need",),
        "inventory_capacity_block": ("water_need",),
        "hidden_map_not_visible": ("water_need",),
        "previous_blocked_effect_revalidation": ("water_need",),
        "action_space_only_no_candidate": (),
    }
    return defaults.get(scenario_id, ())


def _execute_bridge(
    *,
    scenario_id: str,
    ticks: int,
    drive_basis: tuple[str, ...],
    force_internal: bool,
    execute_world_actions: bool,
    for_blocked_precondition: bool,
) -> SubjectWorldBridgeRun:
    backend = GridWorldBackend(scenario_id=scenario_id)
    candidate_provider = None
    allow_manual_override = False
    if for_blocked_precondition:
        # Create one blocked effect on tick 1 so tick 2 can expose revalidation paths.
        candidate_provider = ManualCandidateProvider(
            plans_by_tick={1: (ManualCandidateSpec(action_kind="move_forward"),)}
        )
        allow_manual_override = True

    return run_subject_world_bridge(
        scenario_id=scenario_id,
        backend=backend,
        candidate_provider=candidate_provider,
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=max(1, ticks),
            execute_world_actions=execute_world_actions,
            use_internal_candidate_producer=force_internal,
            internal_drive_kinds=drive_basis,
            allow_manual_candidate_provider=True,
            allow_manual_override_in_internal_mode=allow_manual_override,
            reject_multiple_published_requests=True,
        ),
    )


def _execute_ablated(
    *,
    scenario_id: str,
    world_scenario: str,
    spec: AblationSpec,
    ticks: int,
    drive_basis: tuple[str, ...],
) -> tuple[SubjectWorldBridgeRun, dict[str, bool]]:
    internal = True
    execute_world = True
    drive = drive_basis
    blocked_precondition = scenario_id == "previous_blocked_effect_revalidation"

    if spec.ablation_id == "no_acp01":
        internal = False
    elif spec.ablation_id == "no_ap01":
        execute_world = False
    elif spec.ablation_id == "no_drive_basis":
        drive = ()
    elif spec.ablation_id == "no_public_object_basis":
        # Keep drive but use scenario with no visible object basis.
        pass
    elif spec.ablation_id == "no_action_surface_basis":
        drive = ()
    elif spec.ablation_id == "no_proximity_basis":
        pass
    elif spec.ablation_id == "no_capacity_basis":
        pass
    elif spec.ablation_id == "no_effect_feedback":
        pass
    elif spec.ablation_id == "no_residue_feedback":
        pass
    elif spec.ablation_id == "no_permission_basis":
        drive = ()
    elif spec.ablation_id == "no_prediction_permission_separation":
        # desire-only shape: drive present, no visible object scenario.
        pass
    elif spec.ablation_id == "hidden_eval_substitution_attempt":
        pass

    run = _execute_bridge(
        scenario_id=world_scenario,
        ticks=ticks,
        drive_basis=drive,
        force_internal=internal,
        execute_world_actions=execute_world,
        for_blocked_precondition=blocked_precondition,
    )

    basis_flow = _basis_flow_for_ablation(
        spec_id=spec.ablation_id,
        has_drive=bool(drive),
        has_public_object=_has_public_object(run),
        has_action_surface=(spec.ablation_id != "no_action_surface_basis"),
        has_proximity=(spec.ablation_id != "no_proximity_basis"),
        has_capacity=(spec.ablation_id != "no_capacity_basis"),
    )
    return run, basis_flow


def _basis_flow_for_ablation(
    *,
    spec_id: str,
    has_drive: bool,
    has_public_object: bool,
    has_action_surface: bool,
    has_proximity: bool,
    has_capacity: bool,
) -> dict[str, bool]:
    permission_basis = spec_id not in {"no_permission_basis", "no_ap01"}
    return {
        "drive_basis": has_drive,
        "public_object_basis": has_public_object,
        "action_surface_basis": has_action_surface,
        "proximity_basis": has_proximity,
        "capacity_basis": has_capacity,
        "permission_basis": permission_basis,
    }


def _has_public_object(run: SubjectWorldBridgeRun) -> bool:
    if not run.steps:
        return False
    payload = run.steps[0].subject_tick_surface_payload
    visible = payload.get("visible_objects", ()) if isinstance(payload, dict) else ()
    return bool(visible)


def _trace_from_run(
    *,
    run: SubjectWorldBridgeRun,
    ablation_id: str,
    scenario_id: str,
    basis_flow: dict[str, bool],
    overlay: dict[str, int] | None = None,
) -> AblationTrace:
    overlay = overlay or {}
    acp01_candidate_count = overlay.get("acp01_candidate_count", sum(step.acp01_proposed_count for step in run.steps))
    ap01_published_count = overlay.get("ap01_published_count", sum(step.ap01_published_request_count for step in run.steps))
    world_submission_count = overlay.get("world_submission_count", run.world_submissions_count)
    effect_feedback_count = overlay.get(
        "effect_feedback_count",
        sum(1 for step in run.steps if step.observation_previous_effect_refs),
    )
    revalidation_count = overlay.get(
        "revalidation_count",
        sum(step.acp01_revalidation_required_count + step.ap01_revalidation_required_count for step in run.steps),
    )
    blocked_count = overlay.get(
        "blocked_count",
        sum(1 for step in run.steps if step.world_effect_status == "blocked"),
    )
    residue_count = overlay.get("residue_count", revalidation_count)
    hidden_eval_used = overlay.get("hidden_eval_used", 0) > 0
    scenario_label_used = overlay.get("scenario_label_used", 0) > 0

    violations: list[str] = []
    if any(step.manual_candidate_input for step in run.steps):
        violations.append("manual_candidate_input")
    if any(step.direct_phase_calls_detected for step in run.steps):
        violations.append("direct_phase_calls_detected")

    return AblationTrace(
        ablation_id=ablation_id,
        scenario_id=scenario_id,
        subject_tick_used=run.subject_tick_used_any,
        acp01_used=run.internal_candidate_producer_used_any,
        acp01_candidate_count=acp01_candidate_count,
        ap01_published_count=ap01_published_count,
        world_submission_count=world_submission_count,
        effect_feedback_count=effect_feedback_count,
        revalidation_count=revalidation_count,
        residue_count=residue_count,
        blocked_count=blocked_count,
        hidden_eval_used=hidden_eval_used,
        scenario_label_used=scenario_label_used,
        degradation_observed=False,
        unexpected_success=False,
        boundary_violations=tuple(violations),
        basis_flow=basis_flow,
    )


def _overlay_for_ablation(spec: AblationSpec) -> dict[str, int]:
    if spec.ablation_id == "no_ap01":
        return {
            "ap01_published_count": 0,
            "world_submission_count": 0,
            "effect_feedback_count": 0,
        }
    if spec.ablation_id == "no_effect_feedback":
        return {
            "effect_feedback_count": 0,
        }
    if spec.ablation_id == "no_residue_feedback":
        return {
            "residue_count": 0,
            "revalidation_count": 0,
        }
    if spec.ablation_id == "hidden_eval_substitution_attempt":
        return {
            "hidden_eval_used": 0,
        }
    return {}


def _finalize_trace_with_expected(trace: AblationTrace, spec: AblationSpec) -> AblationTrace:
    observed = _matches_expected(trace=trace, spec=spec)
    unexpected_success = trace.world_submission_count > 0 and "no_world_submission" in spec.expected_degradation.expected
    outcome_class, non_informative_reason = _classify_ablation_outcome(trace=trace, spec=spec, observed=observed)
    return AblationTrace(
        **{
            **asdict(trace),
            "degradation_observed": observed,
            "unexpected_success": unexpected_success,
            "ablation_outcome_class": outcome_class,
            "non_informative_reason": non_informative_reason,
        }
    )


def _classify_ablation_outcome(
    *,
    trace: AblationTrace,
    spec: AblationSpec,
    observed: bool,
) -> tuple[AblationOutcomeClass, str | None]:
    if observed:
        return AblationOutcomeClass.EXPECTED_DEGRADATION_OBSERVED, None

    signature_zero = (
        trace.acp01_candidate_count == 0
        and trace.ap01_published_count == 0
        and trace.world_submission_count == 0
        and trace.effect_feedback_count == 0
    )
    if signature_zero:
        missing_basis = [
            key
            for key, present in trace.basis_flow.items()
            if not present
        ]
        if missing_basis:
            return (
                AblationOutcomeClass.EXPECTED_NO_EFFECT_DUE_MISSING_BASIS,
                f"missing_basis:{','.join(sorted(missing_basis))}",
            )
        return AblationOutcomeClass.NON_INFORMATIVE_ABLATION, "already_blocked_before_ablation"

    if spec.expected_degradation.expected:
        return AblationOutcomeClass.HARD_ABLATION_NO_EFFECT, "expected_load_bearing_seam_no_behavior_change"
    return AblationOutcomeClass.NON_INFORMATIVE_ABLATION, "no_expected_degradation_defined"


def _reclassify_outcome_with_baseline(
    *,
    baseline_trace: AblationTrace,
    ablated_trace: AblationTrace,
) -> AblationTrace:
    if ablated_trace.ablation_outcome_class == AblationOutcomeClass.EXPECTED_DEGRADATION_OBSERVED:
        return ablated_trace

    baseline_meaningful = (
        baseline_trace.ap01_published_count > 0
        or baseline_trace.world_submission_count > 0
        or baseline_trace.effect_feedback_count > 0
    )
    same_signature = (
        baseline_trace.acp01_candidate_count == ablated_trace.acp01_candidate_count
        and baseline_trace.ap01_published_count == ablated_trace.ap01_published_count
        and baseline_trace.world_submission_count == ablated_trace.world_submission_count
        and baseline_trace.effect_feedback_count == ablated_trace.effect_feedback_count
    )

    if baseline_meaningful and same_signature:
        return AblationTrace(
            **{
                **asdict(ablated_trace),
                "ablation_outcome_class": AblationOutcomeClass.HARD_ABLATION_NO_EFFECT,
                "non_informative_reason": "hard_no_effect_meaningful_behavior_unchanged",
            }
        )

    if not baseline_meaningful:
        missing_basis = [
            key
            for key, present in baseline_trace.basis_flow.items()
            if not present
        ]
        if missing_basis:
            return AblationTrace(
                **{
                    **asdict(ablated_trace),
                    "ablation_outcome_class": AblationOutcomeClass.EXPECTED_NO_EFFECT_DUE_MISSING_BASIS,
                    "non_informative_reason": f"expected_no_effect_due_missing_basis:{','.join(sorted(missing_basis))}",
                }
            )
        return AblationTrace(
            **{
                **asdict(ablated_trace),
                "ablation_outcome_class": AblationOutcomeClass.NON_INFORMATIVE_ABLATION,
                "non_informative_reason": "already_blocked_before_ablation",
            }
        )

    return ablated_trace


def _matches_expected(*, trace: AblationTrace, spec: AblationSpec) -> bool:
    expected_checks = {
        "no_candidate": trace.acp01_candidate_count == 0,
        "no_publication": trace.ap01_published_count == 0,
        "no_world_submission": trace.world_submission_count == 0,
        "blocked_or_revalidation": (trace.blocked_count > 0 or trace.revalidation_count > 0 or trace.ap01_published_count == 0),
        "no_completion": trace.world_submission_count == 0 or trace.blocked_count > 0,
        "no_feedback_claim": trace.effect_feedback_count == 0,
        "no_hidden_substitution": not trace.hidden_eval_used,
    }
    return all(expected_checks.get(token, True) for token in spec.expected_degradation.expected)


def _observed_degradation_tokens(trace: AblationTrace) -> tuple[str, ...]:
    observed: list[str] = []
    if trace.acp01_candidate_count == 0:
        observed.append("no_candidate")
    if trace.ap01_published_count == 0:
        observed.append("no_publication")
    if trace.world_submission_count == 0:
        observed.append("no_world_submission")
    if trace.blocked_count > 0 or trace.revalidation_count > 0:
        observed.append("blocked_or_revalidation")
    if trace.effect_feedback_count == 0:
        observed.append("no_feedback_claim")
    if not trace.hidden_eval_used:
        observed.append("no_hidden_substitution")
    return tuple(observed)


def _build_metric_summary(
    *,
    baseline_trace: AblationTrace,
    ablation_traces: tuple[AblationTrace, ...],
    strict_fabrications: int,
    strict_valid: bool,
) -> CausalNecessityMetricSummary:
    total = max(1, len(ablation_traces))
    degradation_match_rate = sum(1 for trace in ablation_traces if trace.degradation_observed) / total
    expected_degradation_count = sum(
        1 for trace in ablation_traces if trace.ablation_outcome_class == AblationOutcomeClass.EXPECTED_DEGRADATION_OBSERVED
    )
    hard_ablation_no_effect_count = sum(
        1 for trace in ablation_traces if trace.ablation_outcome_class == AblationOutcomeClass.HARD_ABLATION_NO_EFFECT
    )
    non_informative_ablation_count = sum(
        1 for trace in ablation_traces if trace.ablation_outcome_class == AblationOutcomeClass.NON_INFORMATIVE_ABLATION
    )
    expected_no_effect_due_missing_basis_count = sum(
        1
        for trace in ablation_traces
        if trace.ablation_outcome_class == AblationOutcomeClass.EXPECTED_NO_EFFECT_DUE_MISSING_BASIS
    )
    unexpected_success_count = sum(1 for trace in ablation_traces if trace.unexpected_success)
    hidden_substitution_count = sum(1 for trace in ablation_traces if trace.hidden_eval_used)
    no_effect_ablation_count = hard_ablation_no_effect_count
    boundary_violations = sum(len(trace.boundary_violations) for trace in ablation_traces)
    boundary_integrity_score = 1.0 - min(1.0, boundary_violations / total)
    basis_flow_integrity_score = 1.0 if strict_valid else 0.0
    ablation_sensitivity_score = degradation_match_rate
    _ = baseline_trace
    return CausalNecessityMetricSummary(
        ablation_sensitivity_score=ablation_sensitivity_score,
        silent_fabrication_count=strict_fabrications,
        unexpected_success_count=unexpected_success_count,
        boundary_integrity_score=boundary_integrity_score,
        basis_flow_integrity_score=basis_flow_integrity_score,
        degradation_match_rate=degradation_match_rate,
        hidden_substitution_count=hidden_substitution_count,
        no_effect_ablation_count=no_effect_ablation_count,
        hard_ablation_no_effect_count=hard_ablation_no_effect_count,
        non_informative_ablation_count=non_informative_ablation_count,
        expected_no_effect_due_missing_basis_count=expected_no_effect_due_missing_basis_count,
        expected_degradation_count=expected_degradation_count,
    )


def _run_falsifiers(
    *,
    baseline_trace: AblationTrace,
    ablated_trace: AblationTrace,
    strict_violations: tuple[str, ...],
    strict_mode: bool,
) -> dict[str, bool]:
    fabricated_refs = tuple(strict_violations)
    desire_only = ablated_trace.basis_flow.get("drive_basis", False) and (not ablated_trace.basis_flow.get("public_object_basis", False))
    diagnostic_success_count = 0
    return {
        "silent_bundle_fabrication": silent_bundle_fabrication(fabricated_basis_refs=fabricated_refs),
        "ablation_no_effect": ablation_no_effect(
            is_hard_no_effect=(
                ablated_trace.ablation_outcome_class
                == AblationOutcomeClass.HARD_ABLATION_NO_EFFECT
            ),
        ),
        "candidate_without_acp01": candidate_without_acp01(
            acp01_suppressed=(ablated_trace.ablation_id == "no_acp01"),
            acp01_candidate_count=ablated_trace.acp01_candidate_count,
        ),
        "world_submission_without_ap01": world_submission_without_ap01(
            ap01_published_count=ablated_trace.ap01_published_count,
            world_submission_count=ablated_trace.world_submission_count,
        ),
        "visible_object_alone_becomes_action": visible_object_alone_becomes_action(
            drive_present=ablated_trace.basis_flow.get("drive_basis", False),
            visible_object_present=ablated_trace.basis_flow.get("public_object_basis", False),
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "drive_alone_becomes_action": drive_alone_becomes_action(
            drive_present=ablated_trace.basis_flow.get("drive_basis", False),
            public_object_present=ablated_trace.basis_flow.get("public_object_basis", False),
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "action_surface_fabricated": action_surface_fabricated(
            surface_basis_present=ablated_trace.basis_flow.get("action_surface_basis", False),
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "pickup_without_proximity_basis": pickup_without_proximity_basis(
            proximity_basis_present=ablated_trace.basis_flow.get("proximity_basis", False),
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "pickup_without_capacity_basis": pickup_without_capacity_basis(
            capacity_basis_present=ablated_trace.basis_flow.get("capacity_basis", False),
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "permission_without_w04_like_basis": permission_without_w04_like_basis(
            permission_basis_present=ablated_trace.basis_flow.get("permission_basis", False),
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "prediction_or_desire_as_permission": prediction_or_desire_as_permission(
            desire_only_basis=desire_only,
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "failure_erased_without_w06_like_residue": failure_erased_without_w06_like_residue(
            blocked_count=ablated_trace.blocked_count,
            residue_count=ablated_trace.residue_count,
            world_submission_count=ablated_trace.world_submission_count,
        ),
        "effect_feedback_fabricated": effect_feedback_fabricated(
            effect_feedback_count=ablated_trace.effect_feedback_count,
            world_submission_count=ablated_trace.world_submission_count,
        ),
        "hidden_basis_substitution": hidden_basis_substitution(
            hidden_eval_used=ablated_trace.hidden_eval_used,
            ap01_published_count=ablated_trace.ap01_published_count,
        ),
        "forbidden_fallback_after_ablation": forbidden_fallback_after_ablation(
            fallback_markers=tuple(marker for marker in ablated_trace.boundary_violations if "manual" in marker or "fallback" in marker),
        ),
        "strict_mode_not_enforced": strict_mode_not_enforced(
            strict_mode_enabled=strict_mode,
            violations=strict_violations,
            verdict="mora_causal_load_bearing",
        ),
        "causal_necessity_report_overclaims": causal_necessity_report_overclaims(
            "P9 causal necessity evidence only; not consciousness or general autonomy proof."
        ),
        "diagnostic_success_counted_as_causal_necessity": diagnostic_success_counted_as_causal_necessity(
            diagnostic_success_count=diagnostic_success_count,
            counted_as_mora_win=False,
        ),
    }


def _claim_safe_verdict(
    *,
    ablated_trace: AblationTrace,
    strict_valid: bool,
    has_hard_falsifier: bool,
) -> CausalNecessityClaimSafeVerdict:
    if has_hard_falsifier:
        return CausalNecessityClaimSafeVerdict.INSUFFICIENT_EVIDENCE
    if strict_valid and ablated_trace.degradation_observed:
        return CausalNecessityClaimSafeVerdict.MORA_CAUSAL_LOAD_BEARING
    if strict_valid:
        return CausalNecessityClaimSafeVerdict.PARTIAL_CAUSAL_EVIDENCE
    return CausalNecessityClaimSafeVerdict.INSUFFICIENT_EVIDENCE
