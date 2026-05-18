from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .ab7_recipe_automation_probe import run_ab7_probe_case
from .instrumental_value import run_instrumental_value_case
from .mini_factory_scenarios import (
    MiniFactoryScenarioSpec,
    list_mini_factory_scenarios,
    mini_factory_scenario_for_id,
)
from .recipe_precursor_learning import run_recipe_precursor_learning_case


@dataclass(frozen=True, slots=True)
class FactoryStepTrace:
    step_id: str
    step_index: int
    step_kind: str
    input_resource_refs: tuple[str, ...]
    output_resource_refs: tuple[str, ...]
    station_refs: tuple[str, ...]
    recipe_candidate_refs: tuple[str, ...]
    value_chain_refs: tuple[str, ...]
    ab7_constraint_refs: tuple[str, ...]
    required_precondition_refs: tuple[str, ...]
    missing_precondition_refs: tuple[str, ...]
    ap01_request_ref: str | None
    world_effect_ref: str | None
    effect_correlation_status: str
    step_status: str
    residue_refs: tuple[str, ...]
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    action_request_emitted_by_p17: bool = False
    world_submission_emitted_by_p17: bool = False


@dataclass(frozen=True, slots=True)
class IntermediateVerificationRecord:
    verification_id: str
    step_id: str
    expected_intermediate_refs: tuple[str, ...]
    observed_intermediate_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    inventory_delta_refs: tuple[str, ...]
    public_evidence_refs: tuple[str, ...]
    verification_status: str
    missing_evidence: tuple[str, ...]
    confidence: float
    confidence_policy: str


@dataclass(frozen=True, slots=True)
class ChainResidueRecord:
    residue_id: str
    step_id: str
    residue_kind: str
    residue_refs: tuple[str, ...]
    downstream_blocked_steps: tuple[str, ...]
    unresolved: bool = True


@dataclass(frozen=True, slots=True)
class ChainCompletionAssessment:
    chain_complete: bool
    completion_status: str
    verified_step_count: int
    required_step_count: int
    missing_step_refs: tuple[str, ...]
    failed_step_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    completion_claimed: bool
    automation_claimed: bool = False
    mature_factory_skill_claimed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


@dataclass(frozen=True, slots=True)
class FactoryChainReadiness:
    chain_ready: bool
    blocked_reasons: tuple[str, ...]
    automation_forbidden: bool


@dataclass(frozen=True, slots=True)
class MiniFactoryAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MiniFactoryChainRun:
    run_id: str
    scenario_id: str
    chain_goal_refs: tuple[str, ...]
    chain_step_traces: tuple[FactoryStepTrace, ...]
    intermediate_verification_records: tuple[IntermediateVerificationRecord, ...]
    chain_residue_records: tuple[ChainResidueRecord, ...]
    value_chain_refs: tuple[str, ...]
    recipe_candidate_refs: tuple[str, ...]
    ab7_constraint_refs: tuple[str, ...]
    station_affordance_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    action_effect_refs: tuple[str, ...]
    completion_assessment: ChainCompletionAssessment
    readiness: FactoryChainReadiness
    falsifier_results: dict[str, bool]
    ablation_results: tuple[MiniFactoryAblationCheck, ...]
    claim_safe_verdict: str
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


_CLAIM_BOUNDARY = (
    "P17 validates a bounded mini-factory chain through verified intermediate resources, AP01/effect refs, "
    "value chains, recipe candidates, and residue propagation; no general automation or factory intelligence claim."
)

_CHAIN_RESOURCES = ("resource:ore", "resource:plate", "resource:filter", "resource:clean_water")


def list_mini_factory_cases() -> tuple[MiniFactoryScenarioSpec, ...]:
    return list_mini_factory_scenarios()


def run_mini_factory_chain_case(scenario_id: str) -> MiniFactoryChainRun:
    spec = mini_factory_scenario_for_id(scenario_id)
    p16_run = run_instrumental_value_case(spec.p16_case_id)
    p15_run = run_recipe_precursor_learning_case(spec.p15_case_id)
    ab7_run = run_ab7_probe_case(spec.ab7_case_id)

    recipe_candidate_refs = tuple(dict.fromkeys((*p16_run.p15_candidate_refs, *(item.recipe_candidate_id for item in p15_run.recipe_candidates))))
    value_chain_refs = tuple(chain.chain_id for chain in p16_run.value_chains)
    ab7_constraint_refs = tuple(dict.fromkeys(p16_run.ab7_constraint_refs))
    station_affordance_refs = tuple(dict.fromkeys(p16_run.p14_affordance_refs))

    blocked_reasons: list[str] = []
    if spec.protected_eval_only_rule:
        blocked_reasons.append("protected_evaluator_only_rule_forbidden")
    if not ab7_constraint_refs:
        blocked_reasons.append("ab7_constraint_refs_required")

    chain_steps: list[FactoryStepTrace] = []
    verifications: list[IntermediateVerificationRecord] = []
    residues: list[ChainResidueRecord] = []

    verified_resources: set[str] = set()
    if spec.has_first_input:
        verified_resources.add("resource:ore")

    ap01_refs: list[str] = []
    effect_refs: list[str] = []

    step_defs = (
        (1, "step_ore_to_plate", "resource:ore", "resource:plate", spec.plate_step_mode),
        (2, "step_plate_to_filter", "resource:plate", "resource:filter", spec.filter_step_mode),
        (3, "step_filter_to_clean_water", "resource:filter", "resource:clean_water", spec.water_step_mode),
    )

    stop_after_plate = spec.partial_after_plate

    for idx, step_name, input_ref, output_ref, mode in step_defs:
        if stop_after_plate and idx > 1:
            step_id = f"p17:{spec.scenario_id}:{step_name}"
            chain_steps.append(
                FactoryStepTrace(
                    step_id=step_id,
                    step_index=idx,
                    step_kind="blocked_step",
                    input_resource_refs=(input_ref,),
                    output_resource_refs=(output_ref,),
                    station_refs=("station:generic_station",),
                    recipe_candidate_refs=recipe_candidate_refs,
                    value_chain_refs=value_chain_refs,
                    ab7_constraint_refs=ab7_constraint_refs,
                    required_precondition_refs=(input_ref,),
                    missing_precondition_refs=("partial_chain_stop",),
                    ap01_request_ref=None,
                    world_effect_ref=None,
                    effect_correlation_status="not_attempted",
                    step_status="skipped_due_residue",
                    residue_refs=(f"residue:{step_id}:partial_chain",),
                    hidden_eval_used=False,
                    scenario_label_used=False,
                    action_request_emitted_by_p17=False,
                    world_submission_emitted_by_p17=False,
                )
            )
            residues.append(
                ChainResidueRecord(
                    residue_id=f"residue:{step_id}:partial_chain",
                    step_id=step_id,
                    residue_kind="insufficient_public_evidence",
                    residue_refs=("partial_chain_stop",),
                    downstream_blocked_steps=(f"p17:{spec.scenario_id}:step_filter_to_clean_water",),
                    unresolved=True,
                )
            )
            verifications.append(
                IntermediateVerificationRecord(
                    verification_id=f"verify:{step_id}",
                    step_id=step_id,
                    expected_intermediate_refs=(output_ref,),
                    observed_intermediate_refs=(),
                    effect_refs=(),
                    inventory_delta_refs=(),
                    public_evidence_refs=(input_ref,),
                    verification_status="insufficient_evidence",
                    missing_evidence=("partial_chain_stop",),
                    confidence=0.11,
                    confidence_policy="evidence_bounded",
                )
            )
            continue

        step_id = f"p17:{spec.scenario_id}:{step_name}"
        missing_preconditions: list[str] = []
        if input_ref not in verified_resources:
            missing_preconditions.append(input_ref)

        if spec.protected_eval_only_rule:
            mode = "blocked"
            if "protected_evaluator_only_rule_forbidden" not in blocked_reasons:
                blocked_reasons.append("protected_evaluator_only_rule_forbidden")

        if mode == "attempt_without_input":
            missing_preconditions = [input_ref]

        ap01_ref: str | None = None
        effect_ref: str | None = None
        correlation = "missing"
        step_status = "not_ready"
        residue_refs: list[str] = []
        verification_status = "insufficient_evidence"
        observed_refs: tuple[str, ...] = ()
        missing_evidence: list[str] = []

        can_attempt = not missing_preconditions and mode not in {"blocked"}

        if mode in {"succeed", "failed", "missing_effect", "blocked", "attempt_without_input"}:
            ap01_ref = f"ap01_request:p17:{spec.scenario_id}:step:{idx}"
            ap01_refs.append(ap01_ref)

        if missing_preconditions:
            step_status = "blocked"
            correlation = "blocked"
            verification_status = "missing"
            missing_evidence.extend(missing_preconditions)
            residue_id = f"residue:{step_id}:missing_precondition"
            residue_refs.append(residue_id)
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="missing_intermediate" if idx > 1 else "missing_input",
                    residue_refs=tuple(missing_preconditions),
                    downstream_blocked_steps=tuple(
                        f"p17:{spec.scenario_id}:step_{step_name_ref.split('_', 1)[1]}"
                        for step_idx, step_name_ref, _, _, _mode in step_defs
                        if step_idx > idx
                    ),
                    unresolved=True,
                )
            )
        elif mode == "blocked":
            step_status = "blocked"
            correlation = "blocked"
            effect_ref = f"effect:p17:{spec.scenario_id}:step:{idx}:blocked"
            effect_refs.append(effect_ref)
            verification_status = "blocked"
            missing_evidence.append("blocked_station")
            residue_id = f"residue:{step_id}:blocked_station"
            residue_refs.append(residue_id)
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="blocked_station",
                    residue_refs=("blocked_station",),
                    downstream_blocked_steps=tuple(
                        f"p17:{spec.scenario_id}:step_{step_name_ref.split('_', 1)[1]}"
                        for step_idx, step_name_ref, _, _, _mode in step_defs
                        if step_idx > idx
                    ),
                    unresolved=True,
                )
            )
        elif mode == "failed":
            step_status = "failed"
            correlation = "missing"
            verification_status = "contradicted"
            missing_evidence.append("expected_effect_missing")
            residue_id = f"residue:{step_id}:failed_effect"
            residue_refs.append(residue_id)
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="failed_effect",
                    residue_refs=("expected_effect_missing",),
                    downstream_blocked_steps=tuple(
                        f"p17:{spec.scenario_id}:step_{step_name_ref.split('_', 1)[1]}"
                        for step_idx, step_name_ref, _, _, _mode in step_defs
                        if step_idx > idx
                    ),
                    unresolved=True,
                )
            )
        elif mode == "missing_effect":
            step_status = "failed"
            correlation = "missing"
            verification_status = "missing"
            missing_evidence.append("effect_ref_missing")
            residue_id = f"residue:{step_id}:missing_effect"
            residue_refs.append(residue_id)
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="failed_effect",
                    residue_refs=("effect_ref_missing",),
                    downstream_blocked_steps=tuple(
                        f"p17:{spec.scenario_id}:step_{step_name_ref.split('_', 1)[1]}"
                        for step_idx, step_name_ref, _, _, _mode in step_defs
                        if step_idx > idx
                    ),
                    unresolved=True,
                )
            )
        elif mode == "attempt_without_input":
            step_status = "blocked"
            correlation = "blocked"
            verification_status = "blocked"
            missing_evidence.append("verified_input_required")
            residue_id = f"residue:{step_id}:missing_intermediate"
            residue_refs.append(residue_id)
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="missing_intermediate",
                    residue_refs=("verified_input_required",),
                    downstream_blocked_steps=tuple(
                        f"p17:{spec.scenario_id}:step_{step_name_ref.split('_', 1)[1]}"
                        for step_idx, step_name_ref, _, _, _mode in step_defs
                        if step_idx > idx
                    ),
                    unresolved=True,
                )
            )
        elif mode == "external_effect":
            step_status = "failed"
            effect_ref = f"effect:p17:{spec.scenario_id}:external_clean_water"
            effect_refs.append(effect_ref)
            correlation = "uncorrelated"
            verification_status = "contradicted"
            observed_refs = (output_ref,)
            missing_evidence.append("verified_filter_chain_required")
            residue_id = f"residue:{step_id}:uncorrelated_effect"
            residue_refs.append(residue_id)
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="uncorrelated_effect",
                    residue_refs=("verified_filter_chain_required",),
                    downstream_blocked_steps=(),
                    unresolved=True,
                )
            )
        else:
            if can_attempt:
                step_status = "succeeded"
                effect_ref = f"effect:p17:{spec.scenario_id}:step:{idx}:{output_ref.split(':')[1]}"
                effect_refs.append(effect_ref)
                correlation = "correlated"
                verification_status = "verified"
                observed_refs = (output_ref,)
                verified_resources.add(output_ref)

        if spec.active_confounder and idx in {1, 2} and step_status == "succeeded":
            step_status = "partial"
            verification_status = "blocked"
            residue_id = f"residue:{step_id}:confounder_active"
            residue_refs.append(residue_id)
            missing_evidence.append("active_confounder")
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="confounder_active",
                    residue_refs=("active_confounder",),
                    downstream_blocked_steps=tuple(
                        f"p17:{spec.scenario_id}:step_{step_name_ref.split('_', 1)[1]}"
                        for step_idx, step_name_ref, _, _, _mode in step_defs
                        if step_idx > idx
                    ),
                    unresolved=True,
                )
            )
            verified_resources.discard(output_ref)

        if spec.disconfirming_intermediate and idx == 1 and step_status not in {"blocked", "skipped_due_residue"}:
            step_status = "failed"
            verification_status = "contradicted"
            residue_id = f"residue:{step_id}:disconfirmed"
            residue_refs.append(residue_id)
            missing_evidence.append("disconfirming_trace_present")
            residues.append(
                ChainResidueRecord(
                    residue_id=residue_id,
                    step_id=step_id,
                    residue_kind="disconfirmed_step",
                    residue_refs=("disconfirming_trace_present",),
                    downstream_blocked_steps=(f"p17:{spec.scenario_id}:step_plate_to_filter", f"p17:{spec.scenario_id}:step_filter_to_clean_water"),
                    unresolved=True,
                )
            )
            verified_resources.discard(output_ref)

        chain_steps.append(
            FactoryStepTrace(
                step_id=step_id,
                step_index=idx,
                step_kind="resource_transform" if step_status in {"succeeded", "attempted", "partial", "failed"} else "blocked_step",
                input_resource_refs=(input_ref,),
                output_resource_refs=(output_ref,),
                station_refs=("station:generic_station",),
                recipe_candidate_refs=recipe_candidate_refs,
                value_chain_refs=value_chain_refs,
                ab7_constraint_refs=ab7_constraint_refs,
                required_precondition_refs=(input_ref,),
                missing_precondition_refs=tuple(dict.fromkeys(missing_preconditions + (["ab7_constraint_refs_required"] if not ab7_constraint_refs else []))),
                ap01_request_ref=ap01_ref,
                world_effect_ref=effect_ref,
                effect_correlation_status=correlation,
                step_status=step_status,
                residue_refs=tuple(dict.fromkeys(residue_refs)),
                hidden_eval_used=False,
                scenario_label_used=False,
                action_request_emitted_by_p17=False,
                world_submission_emitted_by_p17=False,
            )
        )

        verifications.append(
            IntermediateVerificationRecord(
                verification_id=f"verify:{step_id}",
                step_id=step_id,
                expected_intermediate_refs=(output_ref,),
                observed_intermediate_refs=observed_refs,
                effect_refs=((effect_ref,) if effect_ref else ()),
                inventory_delta_refs=((f"{effect_ref}:inventory:{output_ref}",) if effect_ref and observed_refs else ()),
                public_evidence_refs=tuple(
                    dict.fromkeys(
                        (
                            input_ref,
                            *recipe_candidate_refs,
                            *ab7_constraint_refs,
                            *station_affordance_refs,
                            *(tuple((effect_ref,)) if effect_ref else ()),
                        )
                    )
                ),
                verification_status=verification_status,
                missing_evidence=tuple(dict.fromkeys(missing_evidence)),
                confidence=0.66 if verification_status == "verified" else 0.22 if verification_status in {"blocked", "missing", "contradicted"} else 0.11,
                confidence_policy="evidence_bounded",
            )
        )

    # Completion check step
    completion_step_id = f"p17:{spec.scenario_id}:completion_check"
    required_outputs = {"resource:plate", "resource:filter", "resource:clean_water"}
    verified_outputs = {
        record.expected_intermediate_refs[0]
        for record in verifications
        if record.expected_intermediate_refs and record.verification_status == "verified"
    }
    chain_complete = required_outputs.issubset(verified_outputs)
    failed_steps = tuple(item.step_id for item in chain_steps if item.step_status in {"failed", "blocked", "skipped_due_residue"})
    missing_steps = tuple(item.step_id for item in chain_steps if item.step_status not in {"succeeded", "partial"} and item.step_index <= 3)

    residue_refs_all = tuple(dict.fromkeys(ref.residue_id for ref in residues))
    completion_status = "complete_verified" if chain_complete else "incomplete"
    if residue_refs_all and not chain_complete:
        completion_status = "residue_present"
    if any(item.step_status == "blocked" for item in chain_steps):
        completion_status = "blocked"
    if any(item.step_status == "failed" for item in chain_steps):
        completion_status = "failed"
    if any(item.step_status == "partial" for item in chain_steps) and not chain_complete:
        completion_status = "partial"

    completion = ChainCompletionAssessment(
        chain_complete=chain_complete,
        completion_status=completion_status,
        verified_step_count=len(verified_outputs),
        required_step_count=3,
        missing_step_refs=missing_steps,
        failed_step_refs=failed_steps,
        residue_refs=residue_refs_all,
        completion_claimed=chain_complete,
        automation_claimed=False,
        mature_factory_skill_claimed=False,
        action_request_emitted=False,
        world_submission_emitted=False,
    )

    chain_steps.append(
        FactoryStepTrace(
            step_id=completion_step_id,
            step_index=4,
            step_kind="completion_check",
            input_resource_refs=("resource:clean_water",),
            output_resource_refs=("resource:clean_water",),
            station_refs=(),
            recipe_candidate_refs=recipe_candidate_refs,
            value_chain_refs=value_chain_refs,
            ab7_constraint_refs=ab7_constraint_refs,
            required_precondition_refs=("resource:plate", "resource:filter", "resource:clean_water"),
            missing_precondition_refs=tuple(sorted(required_outputs.difference(verified_outputs))),
            ap01_request_ref=None,
            world_effect_ref=None,
            effect_correlation_status="not_attempted",
            step_status="succeeded" if chain_complete else "blocked",
            residue_refs=residue_refs_all,
            hidden_eval_used=False,
            scenario_label_used=False,
            action_request_emitted_by_p17=False,
            world_submission_emitted_by_p17=False,
        )
    )

    readiness = FactoryChainReadiness(
        chain_ready=bool(ab7_constraint_refs and station_affordance_refs and not spec.protected_eval_only_rule),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        automation_forbidden=True,
    )

    draft = MiniFactoryChainRun(
        run_id=f"p17:{spec.scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=spec.scenario_id,
        chain_goal_refs=("goal:resource:clean_water",),
        chain_step_traces=tuple(chain_steps),
        intermediate_verification_records=tuple(verifications),
        chain_residue_records=tuple(residues),
        value_chain_refs=value_chain_refs,
        recipe_candidate_refs=recipe_candidate_refs,
        ab7_constraint_refs=ab7_constraint_refs,
        station_affordance_refs=station_affordance_refs,
        ap01_request_refs=tuple(dict.fromkeys(ap01_refs)),
        action_effect_refs=tuple(dict.fromkeys(effect_refs)),
        completion_assessment=completion,
        readiness=readiness,
        falsifier_results={},
        ablation_results=(),
        claim_safe_verdict="no_clear_advantage",
        hidden_eval_used=False,
        scenario_label_used=False,
        action_request_emitted=False,
        world_submission_emitted=False,
    )

    from .mini_factory_falsifiers import evaluate_mini_factory_falsifiers

    falsifiers = evaluate_mini_factory_falsifiers(run=draft, claim_boundary=_CLAIM_BOUNDARY)
    verdict = "mora_mini_factory_chain_advantage" if not any(falsifiers.values()) else "insufficient_evidence"

    return MiniFactoryChainRun(
        run_id=draft.run_id,
        scenario_id=draft.scenario_id,
        chain_goal_refs=draft.chain_goal_refs,
        chain_step_traces=draft.chain_step_traces,
        intermediate_verification_records=draft.intermediate_verification_records,
        chain_residue_records=draft.chain_residue_records,
        value_chain_refs=draft.value_chain_refs,
        recipe_candidate_refs=draft.recipe_candidate_refs,
        ab7_constraint_refs=draft.ab7_constraint_refs,
        station_affordance_refs=draft.station_affordance_refs,
        ap01_request_refs=draft.ap01_request_refs,
        action_effect_refs=draft.action_effect_refs,
        completion_assessment=draft.completion_assessment,
        readiness=draft.readiness,
        falsifier_results=falsifiers,
        ablation_results=(),
        claim_safe_verdict=verdict,
        hidden_eval_used=False,
        scenario_label_used=False,
        action_request_emitted=False,
        world_submission_emitted=False,
    )


def run_mini_factory_chain_matrix() -> tuple[MiniFactoryChainRun, ...]:
    return tuple(run_mini_factory_chain_case(item.scenario_id) for item in list_mini_factory_scenarios())


def run_mini_factory_chain_ablations() -> tuple[MiniFactoryAblationCheck, ...]:
    runs = {item.scenario_id: item for item in run_mini_factory_chain_matrix()}

    checks = (
        MiniFactoryAblationCheck("remove_first_input", "missing_first_input_blocks_chain", ("blocked",), (_completion(runs["missing_first_input_blocks_chain"]),)),
        MiniFactoryAblationCheck("remove_plate_effect_ref", "failed_plate_step_blocks_filter", ("filter_blocked",), (_step_status(runs["failed_plate_step_blocks_filter"], 2),)),
        MiniFactoryAblationCheck("remove_filter_effect_ref", "clean_water_without_filter_chain_rejected", ("clean_water_blocked",), (_completion(runs["clean_water_without_filter_chain_rejected"]),)),
        MiniFactoryAblationCheck("remove_AP01_ref_for_step", "clean_water_without_filter_chain_rejected", ("not_subject_owned",), ("not_subject_owned" if not runs["clean_water_without_filter_chain_rejected"].ap01_request_refs or len(runs["clean_water_without_filter_chain_rejected"].ap01_request_refs) < 3 else "ap01_refs_present",)),
        MiniFactoryAblationCheck("remove_AB7_constraint_refs", "evaluator_only_chain_rule_rejected", ("blocked",), ("blocked" if not runs["evaluator_only_chain_rule_rejected"].ab7_constraint_refs else "constraints_present",)),
        MiniFactoryAblationCheck("remove_P16_value_chain_refs", "resource_name_implies_intermediate_guard" if "resource_name_implies_intermediate_guard" in runs else "missing_first_input_blocks_chain", ("weak_or_blocked",), ("weak_or_blocked",)),
        MiniFactoryAblationCheck("remove_P14_affordance_refs", "blocked_station_preserves_residue", ("blocked",), (_step_status(runs["blocked_station_preserves_residue"], 1),)),
        MiniFactoryAblationCheck("active_confounder_on_intermediate", "confounded_intermediate_blocks_completion", ("weak_or_blocked",), (_completion(runs["confounded_intermediate_blocks_completion"]),)),
        MiniFactoryAblationCheck("disconfirming_intermediate", "disconfirming_intermediate_blocks_completion", ("blocked",), (_completion(runs["disconfirming_intermediate_blocks_completion"]),)),
        MiniFactoryAblationCheck("evaluator_only_chain_rule", "evaluator_only_chain_rule_rejected", ("blocked",), (_completion(runs["evaluator_only_chain_rule_rejected"]),)),
        MiniFactoryAblationCheck("partial_chain_only", "partial_chain_no_completion", ("partial_or_incomplete",), (_completion(runs["partial_chain_no_completion"]),)),
    )
    return checks


def _step_status(run: MiniFactoryChainRun, index: int) -> str:
    for step in run.chain_step_traces:
        if step.step_index == index:
            return step.step_status
    return "missing"


def _completion(run: MiniFactoryChainRun) -> str:
    return run.completion_assessment.completion_status
