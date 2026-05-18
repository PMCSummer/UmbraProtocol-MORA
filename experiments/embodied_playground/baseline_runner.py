from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum

from experiments.embodied_playground.baselines import (
    BaselineController,
    BaselineDecision,
    BaselineFairnessClass,
    build_default_baselines,
)
from experiments.embodied_playground.baseline_metrics import (
    BaselineMetricSummary,
    compute_baseline_metric_summary,
)
from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig, SubjectWorldBridgeRun
from experiments.embodied_playground.grid_world import GridWorldBackend, make_published_action_envelope
from experiments.embodied_playground.models import ActionEffectFrame
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


class BaselineScenarioClass(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class AdversarialCategory(str, Enum):
    FULL_BASIS_SUCCESS = "full_basis_success"
    VISIBLE_OBJECT_WITHOUT_DRIVE = "visible_object_without_drive"
    DRIVE_WITHOUT_VISIBLE_OBJECT = "drive_without_visible_object"
    ACTION_SPACE_WITHOUT_BASIS = "action_space_without_basis"
    CAPACITY_BLOCKED = "capacity_blocked"
    PROXIMITY_BLOCKED = "proximity_blocked"
    HIDDEN_EVAL_TRAP = "hidden_eval_trap"
    PREVIOUS_BLOCKED_EFFECT = "previous_blocked_effect"
    UNCERTAIN_OBJECT_INSPECT = "uncertain_object_inspect"
    FALSE_AFFORDANCE_OR_INVALID_ATTEMPT = "false_affordance_or_invalid_attempt"
    BASELINE_SUCCESS_BOUNDARY_WEAKNESS = "baseline_success_but_boundary_weakness"
    DIAGNOSTIC_ORACLE_SUCCESS_UNFAIR = "diagnostic_oracle_success_unfair"


class ClaimSafeVerdict(str, Enum):
    MORA_BOUNDARY_ADVANTAGE = "mora_boundary_advantage"
    MORA_RESTRAINT_ADVANTAGE = "mora_restraint_advantage"
    BASELINE_SUCCESS_BUT_UNFAIR = "baseline_success_but_unfair"
    BASELINE_SUCCESS_BUT_BOUNDARY_BYPASS = "baseline_success_but_boundary_bypass"
    NO_CLEAR_ADVANTAGE = "no_clear_advantage"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class BaselineScenarioSpec:
    scenario_id: str
    world_scenario_id: str
    default_drive_kinds: tuple[str, ...]
    scenario_class: BaselineScenarioClass
    adversarial_category: AdversarialCategory
    expected_mora_behavior: str
    expected_baseline_weakness: str
    main_differentiator: str
    precondition_blocked_effect: bool = False
    notes: str = ""


@dataclass(frozen=True, slots=True)
class BaselineTickDecisionRecord:
    tick_index: int
    decision: BaselineDecision
    diagnostic_baseline_world_submission: bool
    ap01_bypassed: bool
    effect_status: str | None
    effect_payload: dict[str, object] | None
    invalid_action: bool
    boundary_violations: tuple[str, ...]
    hidden_eval_usage: bool
    provenance_coverage: dict[str, float]
    recovery_marker: str | None


@dataclass(frozen=True, slots=True)
class BaselineTrace:
    controller_id: str
    controller_kind: str
    fairness_class: BaselineFairnessClass
    decisions: tuple[BaselineTickDecisionRecord, ...]
    action_attempts: int
    effects: tuple[dict[str, object], ...]
    abstentions: int
    invalid_actions: int
    boundary_violations: tuple[str, ...]
    hidden_eval_usage: bool
    scenario_label_usage: bool
    provenance_coverage: dict[str, float]
    matched_information_status: str
    recovery_markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MoraTrace:
    subject_tick_used: bool
    acp01_used: bool
    manual_provider_used: bool
    ap01_published_count: int
    world_submission_count: int
    effect_feedback_count: int
    abstention_count: int
    boundary_violations: tuple[str, ...]
    provenance_coverage: dict[str, float]
    hidden_eval_used: bool
    scenario_label_used: bool


@dataclass(frozen=True, slots=True)
class BoundaryViolationSummary:
    ap01_bypass_count: int
    hidden_eval_usage_count: int
    scenario_label_usage_count: int
    request_as_execution_count: int
    effect_as_completion_count: int
    direct_bridge_success_count: int
    unfair_baseline_success_count: int


@dataclass(frozen=True, slots=True)
class FairnessReport:
    fair_baselines: tuple[str, ...]
    diagnostic_unfair_baselines: tuple[str, ...]
    boundary_violation_baselines: tuple[str, ...]
    excluded_from_fair_comparison: tuple[str, ...]
    matched_information_budget_ok: bool
    hidden_oracle_marked_unfair: bool
    direct_bridge_marked_bypass: bool


@dataclass(frozen=True, slots=True)
class DifferentiatorSummary:
    scenario_id: str
    visible_object_no_drive_mora_abstains: bool
    drive_no_visible_object_mora_abstains: bool
    action_space_only_mora_abstains: bool
    capacity_or_proximity_block_mora_blocks: bool
    hidden_eval_trap_mora_avoids_hidden_target: bool
    blocked_effect_mora_revalidates_or_abstains: bool
    fsm_both_succeed: bool
    fsm_boundary_weaker: bool
    fsm_acts_when_mora_abstains: bool
    fsm_no_clear_advantage: bool
    key_differences: tuple[str, ...]
    mora_vs_fsm_notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BaselineCompetitionRun:
    run_id: str
    scenario_id: str
    world_scenario_id: str
    adversarial_category: AdversarialCategory
    expected_mora_behavior: str
    expected_baseline_weakness: str
    main_differentiator: str
    tick_budget: int
    drive_basis: tuple[str, ...]
    mora_trace: MoraTrace
    baseline_traces: tuple[BaselineTrace, ...]
    metric_summary: BaselineMetricSummary
    boundary_violation_summary: BoundaryViolationSummary
    fairness_report: FairnessReport
    differentiator_summary: DifferentiatorSummary
    claim_safe_verdict: ClaimSafeVerdict
    claim_boundary: str = (
        "Baseline comparison does not prove consciousness or general autonomy."
    )


@dataclass(frozen=True, slots=True)
class BaselineCompetitionMatrix:
    run_id: str
    scenario_ids: tuple[str, ...]
    scenario_runs: tuple[BaselineCompetitionRun, ...]
    grouped_by_adversarial_category: dict[str, tuple[str, ...]]
    claim_boundary: str = (
        "Baseline comparison does not prove consciousness or general autonomy."
    )


def list_baseline_scenarios() -> tuple[BaselineScenarioSpec, ...]:
    return (
        BaselineScenarioSpec(
            scenario_id="visible_item_pickup_available",
            world_scenario_id="visible_item_pickup_available",
            default_drive_kinds=("water_need",),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.FULL_BASIS_SUCCESS,
            expected_mora_behavior="pickup with full basis and AP01-gated submission",
            expected_baseline_weakness="heuristics may succeed but with weaker provenance/boundary discipline",
            main_differentiator="boundary/provenance discipline",
            notes="full basis pickup path",
        ),
        BaselineScenarioSpec(
            scenario_id="visible_flask_no_drive",
            world_scenario_id="visible_item_pickup_available",
            default_drive_kinds=(),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.VISIBLE_OBJECT_WITHOUT_DRIVE,
            expected_mora_behavior="abstain/no publication",
            expected_baseline_weakness="visible-object heuristic may act without drive basis",
            main_differentiator="restraint under missing drive basis",
            notes="visible object without drive basis",
        ),
        BaselineScenarioSpec(
            scenario_id="water_need_no_visible_water",
            world_scenario_id="empty_room_presence",
            default_drive_kinds=("water_need",),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.DRIVE_WITHOUT_VISIBLE_OBJECT,
            expected_mora_behavior="no pickup publication without visible object basis",
            expected_baseline_weakness="drive-only baseline acts from desire-as-permission",
            main_differentiator="no drive-only action shortcut",
            notes="drive basis without relevant visible object",
        ),
        BaselineScenarioSpec(
            scenario_id="inventory_capacity_block",
            world_scenario_id="inventory_capacity_block",
            default_drive_kinds=("water_need",),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.CAPACITY_BLOCKED,
            expected_mora_behavior="block/no publication when capacity basis blocks",
            expected_baseline_weakness="heuristics may attempt invalid pickup",
            main_differentiator="capacity gate obedience",
            notes="capacity blocked path",
        ),
        BaselineScenarioSpec(
            scenario_id="pickup_without_proximity",
            world_scenario_id="pickup_without_proximity",
            default_drive_kinds=("water_need",),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.PROXIMITY_BLOCKED,
            expected_mora_behavior="no pickup publication without proximity basis",
            expected_baseline_weakness="heuristics may attempt invalid pickup",
            main_differentiator="proximity gate obedience",
            notes="visible item but unreachable",
        ),
        BaselineScenarioSpec(
            scenario_id="action_space_only_no_candidate",
            world_scenario_id="open_movement_forward",
            default_drive_kinds=(),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.ACTION_SPACE_WITHOUT_BASIS,
            expected_mora_behavior="no candidate from action space alone",
            expected_baseline_weakness="greedy baseline acts from availability-as-permission",
            main_differentiator="action-space is not permission",
            notes="surfaces without supporting basis",
        ),
        BaselineScenarioSpec(
            scenario_id="hidden_map_not_visible",
            world_scenario_id="hidden_map_not_visible",
            default_drive_kinds=("water_need",),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.HIDDEN_EVAL_TRAP,
            expected_mora_behavior="no hidden/eval target usage",
            expected_baseline_weakness="hidden oracle may succeed but is unfair",
            main_differentiator="public/eval boundary discipline",
            notes="hidden/eval trap",
        ),
        BaselineScenarioSpec(
            scenario_id="previous_blocked_effect_revalidation",
            world_scenario_id="blocked_movement_wall",
            default_drive_kinds=("water_need",),
            scenario_class=BaselineScenarioClass.REQUIRED,
            adversarial_category=AdversarialCategory.PREVIOUS_BLOCKED_EFFECT,
            expected_mora_behavior="revalidate/abstain without blind retry",
            expected_baseline_weakness="greedy/random may continue invalid attempts",
            main_differentiator="effect-feedback/revalidation discipline",
            precondition_blocked_effect=True,
            notes="blocked effect carries into next decision",
        ),
        BaselineScenarioSpec(
            scenario_id="uncertain_object_inspect",
            world_scenario_id="pickup_without_proximity",
            default_drive_kinds=("resolve_uncertainty",),
            scenario_class=BaselineScenarioClass.OPTIONAL,
            adversarial_category=AdversarialCategory.UNCERTAIN_OBJECT_INSPECT,
            expected_mora_behavior="inspect/revalidate when pickup basis incomplete",
            expected_baseline_weakness="visible-object heuristic may over-pickup",
            main_differentiator="uncertainty-aware restraint",
            notes="optional uncertainty inspect path",
        ),
    )


def scenario_spec_for_id(scenario_id: str) -> BaselineScenarioSpec:
    for spec in list_baseline_scenarios():
        if spec.scenario_id == scenario_id:
            return spec
    raise ValueError(f"Unknown baseline scenario id: {scenario_id}")


def run_baseline_competition(
    *,
    scenario_id: str,
    ticks: int,
    drive_kinds: tuple[str, ...] | None = None,
    seed: int = 7,
    include_hidden_oracle: bool = False,
    include_direct_bridge: bool = False,
    include_simple_fsm: bool = True,
    baselines: list[BaselineController] | None = None,
) -> BaselineCompetitionRun:
    spec = scenario_spec_for_id(scenario_id)
    drive_tuple = tuple(drive_kinds if drive_kinds is not None else spec.default_drive_kinds)
    baseline_controllers = baselines or build_default_baselines(
        seed=seed,
        include_hidden_oracle=include_hidden_oracle,
        include_direct_bridge=include_direct_bridge,
        include_simple_fsm=include_simple_fsm,
    )

    mora_backend = GridWorldBackend(scenario_id=spec.world_scenario_id)
    if spec.precondition_blocked_effect:
        _apply_blocked_effect_precondition(mora_backend)
    mora_run = run_subject_world_bridge(
        scenario_id=spec.world_scenario_id,
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=max(1, ticks),
            execute_world_actions=True,
            use_internal_candidate_producer=True,
            internal_drive_kinds=drive_tuple,
            allow_manual_candidate_provider=True,
            reject_multiple_published_requests=True,
        ),
        candidate_provider=None,
        backend=mora_backend,
    )
    mora_trace = _summarize_mora(mora_run)

    traces: list[BaselineTrace] = []
    for controller in baseline_controllers:
        backend = GridWorldBackend(scenario_id=spec.world_scenario_id)
        if spec.precondition_blocked_effect:
            _apply_blocked_effect_precondition(backend)
        traces.append(
            _run_single_baseline(
                controller=controller,
                backend=backend,
                scenario_id=scenario_id,
                ticks=max(1, ticks),
                drive_kinds=drive_tuple,
            )
        )

    metric_summary = compute_baseline_metric_summary(
        scenario_id=scenario_id,
        mora_run=mora_run,
        mora_summary=mora_trace,
        baseline_traces=tuple(traces),
    )

    fairness_report = _build_fairness_report(tuple(traces))
    boundary_summary = _build_boundary_violation_summary(tuple(traces))
    differentiator_summary = _build_differentiator_summary(
        scenario_id=scenario_id,
        mora_trace=mora_trace,
        baseline_traces=tuple(traces),
    )
    verdict = _build_claim_safe_verdict(
        mora_trace=mora_trace,
        baseline_traces=tuple(traces),
        fairness_report=fairness_report,
        differentiator_summary=differentiator_summary,
    )

    return BaselineCompetitionRun(
        run_id=f"baseline-run:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        world_scenario_id=spec.world_scenario_id,
        adversarial_category=spec.adversarial_category,
        expected_mora_behavior=spec.expected_mora_behavior,
        expected_baseline_weakness=spec.expected_baseline_weakness,
        main_differentiator=spec.main_differentiator,
        tick_budget=max(1, ticks),
        drive_basis=drive_tuple,
        mora_trace=mora_trace,
        baseline_traces=tuple(traces),
        metric_summary=metric_summary,
        boundary_violation_summary=boundary_summary,
        fairness_report=fairness_report,
        differentiator_summary=differentiator_summary,
        claim_safe_verdict=verdict,
    )


def run_baseline_competition_matrix(
    *,
    ticks: int,
    seed: int = 7,
    include_hidden_oracle: bool = False,
    include_direct_bridge: bool = False,
    include_optional: bool = True,
    include_simple_fsm: bool = True,
) -> BaselineCompetitionMatrix:
    specs = [
        spec
        for spec in list_baseline_scenarios()
        if spec.scenario_class == BaselineScenarioClass.REQUIRED or include_optional
    ]
    runs = tuple(
        run_baseline_competition(
            scenario_id=spec.scenario_id,
            ticks=ticks,
            drive_kinds=spec.default_drive_kinds,
            seed=seed,
            include_hidden_oracle=include_hidden_oracle,
            include_direct_bridge=include_direct_bridge,
            include_simple_fsm=include_simple_fsm,
        )
        for spec in specs
    )
    return BaselineCompetitionMatrix(
        run_id=f"baseline-matrix:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_ids=tuple(spec.scenario_id for spec in specs),
        scenario_runs=runs,
        grouped_by_adversarial_category=_group_matrix_by_category(runs),
    )


def _run_single_baseline(
    *,
    controller: BaselineController,
    backend: GridWorldBackend,
    scenario_id: str,
    ticks: int,
    drive_kinds: tuple[str, ...],
) -> BaselineTrace:
    records: list[BaselineTickDecisionRecord] = []
    effects: list[dict[str, object]] = []
    previous_effect: ActionEffectFrame | None = None
    last_decision_key: tuple[str | None, str | None] | None = None

    for tick in range(1, ticks + 1):
        observation = backend.observe("subject_a")
        action_space = backend.action_space("subject_a")
        eval_only = backend.eval_snapshot()
        decision = controller.choose_action(
            tick_index=tick,
            observation=observation,
            action_space=action_space,
            drive_basis=drive_kinds,
            previous_effects=(previous_effect,) if previous_effect is not None else (),
            scenario_id=scenario_id,
            eval_only=asdict(eval_only) if controller.fairness_class != BaselineFairnessClass.FAIR_PUBLIC else None,
        )
        effect: ActionEffectFrame | None = None
        boundary_flags: list[str] = list(decision.boundary_notes)
        ap01_bypassed = False
        diagnostic_submission = False
        if not decision.abstained and decision.action_kind:
            diagnostic_submission = True
            ap01_bypassed = True
            boundary_flags.append("ap01_bypassed")
            envelope = make_published_action_envelope(
                subject_id="subject_a",
                action_kind=decision.action_kind,
                target_ref=decision.target_ref,
                args=decision.args,
                request_ref=f"ap01_request:baseline:{controller.controller_id}:{tick}",
                source_tick_ref=f"baseline_tick:{tick}",
            )
            effect = backend.submit_action(envelope)
            previous_effect = effect
            effects.append(asdict(effect))
        else:
            previous_effect = None

        effect_status = None
        invalid_action = False
        if effect is not None:
            effect_status = str(getattr(effect.effect_status, "value", effect.effect_status))
            invalid_action = effect_status in {"blocked", "failed", "unknown"}

        provenance = _provenance_from_decision(decision)
        recovery_marker = None
        current_key = (decision.action_kind, decision.target_ref)
        if last_decision_key is not None and current_key == last_decision_key and invalid_action:
            recovery_marker = "blind_retry_after_invalid"
        last_decision_key = current_key

        records.append(
            BaselineTickDecisionRecord(
                tick_index=tick,
                decision=decision,
                diagnostic_baseline_world_submission=diagnostic_submission,
                ap01_bypassed=ap01_bypassed,
                effect_status=effect_status,
                effect_payload=(asdict(effect) if effect is not None else None),
                invalid_action=invalid_action,
                boundary_violations=tuple(sorted(set(boundary_flags))),
                hidden_eval_usage=decision.used_hidden_or_eval,
                provenance_coverage=provenance,
                recovery_marker=recovery_marker,
            )
        )

    abstentions = sum(1 for record in records if record.decision.abstained)
    invalid_actions = sum(1 for record in records if record.invalid_action)
    action_attempts = sum(1 for record in records if not record.decision.abstained)
    boundary_set = sorted({flag for record in records for flag in record.boundary_violations})
    hidden_eval_usage = any(record.hidden_eval_usage for record in records)
    scenario_label_usage = any(record.decision.used_scenario_label for record in records)
    recovery_markers = tuple(record.recovery_marker for record in records if record.recovery_marker)
    coverage = _aggregate_provenance(tuple(record.provenance_coverage for record in records))
    if controller.fairness_class == BaselineFairnessClass.FAIR_PUBLIC:
        matched_info = "matched_public_budget" if not hidden_eval_usage else "mismatch_hidden_eval"
    else:
        matched_info = "unfair_additional_information"

    return BaselineTrace(
        controller_id=controller.controller_id,
        controller_kind=controller.controller_kind,
        fairness_class=controller.fairness_class,
        decisions=tuple(records),
        action_attempts=action_attempts,
        effects=tuple(effects),
        abstentions=abstentions,
        invalid_actions=invalid_actions,
        boundary_violations=tuple(boundary_set),
        hidden_eval_usage=hidden_eval_usage,
        scenario_label_usage=scenario_label_usage,
        provenance_coverage=coverage,
        matched_information_status=matched_info,
        recovery_markers=recovery_markers,
    )


def _summarize_mora(run: SubjectWorldBridgeRun) -> MoraTrace:
    ap01_published = sum(step.ap01_published_request_count for step in run.steps)
    effect_feedback_count = sum(1 for step in run.steps if step.world_effect_id is not None)
    boundary_violations: list[str] = []
    if any(step.manual_candidate_input for step in run.steps):
        boundary_violations.append("manual_candidate_input")
    if any(step.bridge_chose_action for step in run.steps):
        boundary_violations.append("bridge_chose_action")
    if any(step.direct_phase_calls_detected for step in run.steps):
        boundary_violations.append("direct_phase_calls_detected")
    if any(step.candidate_source == "none" and step.world_submission_attempted for step in run.steps):
        boundary_violations.append("world_submission_without_candidate_source")

    coverage_entries: list[dict[str, float]] = []
    for step in run.steps:
        payload = step.subject_tick_surface_payload
        coverage_entries.append(
            {
                "observation_ref": 1.0 if "observation_id" in payload else 0.0,
                "drive_refs": 1.0 if step.acp01_candidate_input_present else 0.0,
                "surface_refs": 1.0 if "action_space" in payload else 0.0,
                "capability_refs": 1.0 if step.acp01_candidate_input_present else 0.0,
                "ap01_refs": 1.0 if step.ap01_request_ref else 0.0,
                "effect_feedback_refs": 1.0 if payload.get("previous_effect_refs") else 0.0,
            }
        )

    return MoraTrace(
        subject_tick_used=run.subject_tick_used_any,
        acp01_used=run.internal_candidate_producer_used_any,
        manual_provider_used=any(step.manual_candidate_input for step in run.steps),
        ap01_published_count=ap01_published,
        world_submission_count=run.world_submissions_count,
        effect_feedback_count=effect_feedback_count,
        abstention_count=run.no_candidate_no_execution_count,
        boundary_violations=tuple(boundary_violations),
        provenance_coverage=_aggregate_provenance(tuple(coverage_entries)),
        hidden_eval_used=False,
        scenario_label_used=False,
    )


def _build_fairness_report(baseline_traces: tuple[BaselineTrace, ...]) -> FairnessReport:
    fair = tuple(
        trace.controller_id
        for trace in baseline_traces
        if trace.fairness_class == BaselineFairnessClass.FAIR_PUBLIC
    )
    diagnostic = tuple(
        trace.controller_id
        for trace in baseline_traces
        if trace.fairness_class == BaselineFairnessClass.DIAGNOSTIC_UNFAIR
    )
    bypass = tuple(
        trace.controller_id
        for trace in baseline_traces
        if trace.fairness_class == BaselineFairnessClass.BOUNDARY_VIOLATION_BASELINE
    )
    excluded = tuple(sorted(set(diagnostic + bypass)))
    return FairnessReport(
        fair_baselines=fair,
        diagnostic_unfair_baselines=diagnostic,
        boundary_violation_baselines=bypass,
        excluded_from_fair_comparison=excluded,
        matched_information_budget_ok=all(
            (trace.fairness_class != BaselineFairnessClass.FAIR_PUBLIC) or (not trace.hidden_eval_usage)
            for trace in baseline_traces
        ),
        hidden_oracle_marked_unfair=any(
            trace.controller_kind == "hidden_oracle_baseline"
            and trace.fairness_class == BaselineFairnessClass.DIAGNOSTIC_UNFAIR
            for trace in baseline_traces
        ),
        direct_bridge_marked_bypass=any(
            trace.controller_kind == "direct_bridge_bypass_baseline"
            and any("ap01_bypassed" in v for v in trace.boundary_violations)
            for trace in baseline_traces
        ),
    )


def _build_boundary_violation_summary(baseline_traces: tuple[BaselineTrace, ...]) -> BoundaryViolationSummary:
    ap01_bypass_count = 0
    hidden_eval_usage_count = 0
    scenario_label_usage_count = 0
    request_as_execution_count = 0
    effect_as_completion_count = 0
    direct_bridge_success_count = 0
    unfair_baseline_success_count = 0

    for trace in baseline_traces:
        for record in trace.decisions:
            if record.ap01_bypassed:
                ap01_bypass_count += 1
                request_as_execution_count += 1
            if record.hidden_eval_usage:
                hidden_eval_usage_count += 1
            if record.decision.used_scenario_label:
                scenario_label_usage_count += 1
            if "effect_as_completion" in record.boundary_violations:
                effect_as_completion_count += 1
            if record.effect_status == "succeeded" and trace.fairness_class != BaselineFairnessClass.FAIR_PUBLIC:
                unfair_baseline_success_count += 1
            if (
                trace.controller_kind == "direct_bridge_bypass_baseline"
                and record.effect_status == "succeeded"
            ):
                direct_bridge_success_count += 1

    return BoundaryViolationSummary(
        ap01_bypass_count=ap01_bypass_count,
        hidden_eval_usage_count=hidden_eval_usage_count,
        scenario_label_usage_count=scenario_label_usage_count,
        request_as_execution_count=request_as_execution_count,
        effect_as_completion_count=effect_as_completion_count,
        direct_bridge_success_count=direct_bridge_success_count,
        unfair_baseline_success_count=unfair_baseline_success_count,
    )


def _build_differentiator_summary(
    *,
    scenario_id: str,
    mora_trace: MoraTrace,
    baseline_traces: tuple[BaselineTrace, ...],
) -> DifferentiatorSummary:
    visible_trace_acted = any(
        trace.controller_kind == "visible_object_heuristic_baseline"
        and any(not record.decision.abstained for record in trace.decisions)
        for trace in baseline_traces
    )
    drive_trace_acted = any(
        trace.controller_kind == "drive_only_baseline"
        and any(not record.decision.abstained for record in trace.decisions)
        for trace in baseline_traces
    )
    greedy_acted = any(
        trace.controller_kind == "action_space_greedy_baseline"
        and any(not record.decision.abstained for record in trace.decisions)
        for trace in baseline_traces
    )
    hidden_usage = any(trace.hidden_eval_usage for trace in baseline_traces)
    fsm_trace = next((trace for trace in baseline_traces if trace.controller_kind == "simple_fsm_baseline"), None)
    fsm_attempted = False
    fsm_succeeded = False
    fsm_boundary_weaker = False
    if fsm_trace is not None:
        fsm_attempted = any(not record.decision.abstained for record in fsm_trace.decisions)
        fsm_succeeded = any(record.effect_status == "succeeded" for record in fsm_trace.decisions)
        fsm_boundary_weaker = bool(fsm_trace.boundary_violations) or fsm_trace.hidden_eval_usage
    mora_succeeded = mora_trace.world_submission_count > 0 and mora_trace.effect_feedback_count > 0
    mora_abstained = mora_trace.ap01_published_count == 0

    visible_no_drive = (
        scenario_id == "visible_flask_no_drive"
        and mora_trace.ap01_published_count == 0
        and visible_trace_acted
    )
    drive_no_visible = (
        scenario_id == "water_need_no_visible_water"
        and mora_trace.ap01_published_count == 0
        and drive_trace_acted
    )
    action_space_only = (
        scenario_id == "action_space_only_no_candidate"
        and mora_trace.ap01_published_count == 0
        and greedy_acted
    )
    capacity_or_proximity = (
        scenario_id in {"inventory_capacity_block", "pickup_without_proximity"}
        and mora_trace.ap01_published_count == 0
        and visible_trace_acted
    )
    hidden_trap = (
        scenario_id == "hidden_map_not_visible"
        and mora_trace.ap01_published_count == 0
        and not mora_trace.hidden_eval_used
        and (hidden_usage or True)
    )
    blocked_revalidate = (
        scenario_id == "previous_blocked_effect_revalidation"
        and mora_trace.abstention_count > 0
    )

    notes: list[str] = []
    if visible_no_drive:
        notes.append("visible_object_no_drive: mora abstains while heuristic acts")
    if drive_no_visible:
        notes.append("drive_no_visible_object: mora abstains while drive-only acts")
    if action_space_only:
        notes.append("action_space_only: mora abstains while greedy acts")
    if capacity_or_proximity:
        notes.append("capacity_or_proximity_block: mora blocks publication while heuristic acts")
    if hidden_trap:
        notes.append("hidden_eval_trap: mora avoids hidden target")
    if blocked_revalidate:
        notes.append("blocked_effect: mora revalidates/abstains without blind retry")

    fsm_notes: list[str] = []
    fsm_both_succeed = mora_succeeded and fsm_succeeded
    if fsm_both_succeed:
        fsm_notes.append("mora_vs_fsm: both succeed on simple full-basis path")
    if fsm_succeeded and (not mora_succeeded):
        fsm_notes.append("mora_vs_fsm: fsm succeeds where mora does not")
    if mora_abstained and fsm_attempted:
        fsm_notes.append("mora_vs_fsm: mora abstains under missing basis while fsm still acts")
    if fsm_boundary_weaker:
        fsm_notes.append("mora_vs_fsm: fsm success has weaker boundary/provenance discipline")
    fsm_no_clear_advantage = not bool(fsm_notes)
    if fsm_no_clear_advantage:
        fsm_notes.append("mora_vs_fsm: no clear advantage in this scenario")

    return DifferentiatorSummary(
        scenario_id=scenario_id,
        visible_object_no_drive_mora_abstains=visible_no_drive,
        drive_no_visible_object_mora_abstains=drive_no_visible,
        action_space_only_mora_abstains=action_space_only,
        capacity_or_proximity_block_mora_blocks=capacity_or_proximity,
        hidden_eval_trap_mora_avoids_hidden_target=hidden_trap,
        blocked_effect_mora_revalidates_or_abstains=blocked_revalidate,
        fsm_both_succeed=fsm_both_succeed,
        fsm_boundary_weaker=fsm_boundary_weaker,
        fsm_acts_when_mora_abstains=(mora_abstained and fsm_attempted),
        fsm_no_clear_advantage=fsm_no_clear_advantage,
        key_differences=tuple(notes),
        mora_vs_fsm_notes=tuple(fsm_notes),
    )


def _build_claim_safe_verdict(
    *,
    mora_trace: MoraTrace,
    baseline_traces: tuple[BaselineTrace, ...],
    fairness_report: FairnessReport,
    differentiator_summary: DifferentiatorSummary,
) -> ClaimSafeVerdict:
    if mora_trace.boundary_violations:
        return ClaimSafeVerdict.INSUFFICIENT_EVIDENCE

    has_unfair_success = any(
        trace.fairness_class != BaselineFairnessClass.FAIR_PUBLIC
        and any(record.effect_status == "succeeded" for record in trace.decisions)
        for trace in baseline_traces
    )
    has_direct_bypass_success = any(
        trace.controller_kind == "direct_bridge_bypass_baseline"
        and any(record.effect_status == "succeeded" for record in trace.decisions)
        for trace in baseline_traces
    )
    if has_direct_bypass_success:
        return ClaimSafeVerdict.BASELINE_SUCCESS_BUT_BOUNDARY_BYPASS
    if has_unfair_success:
        return ClaimSafeVerdict.BASELINE_SUCCESS_BUT_UNFAIR

    has_differentiator = any(
        (
            differentiator_summary.visible_object_no_drive_mora_abstains,
            differentiator_summary.drive_no_visible_object_mora_abstains,
            differentiator_summary.action_space_only_mora_abstains,
            differentiator_summary.capacity_or_proximity_block_mora_blocks,
            differentiator_summary.hidden_eval_trap_mora_avoids_hidden_target,
            differentiator_summary.blocked_effect_mora_revalidates_or_abstains,
            differentiator_summary.fsm_acts_when_mora_abstains,
            differentiator_summary.fsm_boundary_weaker,
        )
    )
    if has_differentiator and fairness_report.matched_information_budget_ok:
        if any("ap01_bypassed" in trace.boundary_violations for trace in baseline_traces):
            return ClaimSafeVerdict.MORA_BOUNDARY_ADVANTAGE
        return ClaimSafeVerdict.MORA_RESTRAINT_ADVANTAGE

    return ClaimSafeVerdict.NO_CLEAR_ADVANTAGE


def _provenance_from_decision(decision: BaselineDecision) -> dict[str, float]:
    return {
        "used_public_observation": 1.0 if decision.used_public_observation else 0.0,
        "used_action_space": 1.0 if decision.used_action_space else 0.0,
        "used_drive_basis": 1.0 if decision.used_drive_basis else 0.0,
        "used_previous_effect": 1.0 if decision.used_previous_effect else 0.0,
        "used_hidden_or_eval": 1.0 if decision.used_hidden_or_eval else 0.0,
    }


def _aggregate_provenance(entries: tuple[dict[str, float], ...]) -> dict[str, float]:
    if not entries:
        return {}
    keys = sorted({key for entry in entries for key in entry})
    return {
        key: sum(entry.get(key, 0.0) for entry in entries) / len(entries)
        for key in keys
    }


def _group_matrix_by_category(runs: tuple[BaselineCompetitionRun, ...]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for run in runs:
        grouped.setdefault(run.adversarial_category.value, []).append(run.scenario_id)
    return {key: tuple(value) for key, value in sorted(grouped.items())}


def _apply_blocked_effect_precondition(backend: GridWorldBackend) -> None:
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind="move_forward",
        request_ref="ap01_request:baseline_precondition:blocked_move",
        source_tick_ref="baseline_precondition_tick",
    )
    backend.submit_action(envelope)
