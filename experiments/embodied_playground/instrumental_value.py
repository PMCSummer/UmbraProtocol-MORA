from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .ab7_recipe_automation_probe import run_ab7_probe_case
from .instrumental_value_scenarios import (
    InstrumentalValueScenarioSpec,
    instrumental_value_scenario_for_id,
    list_instrumental_value_scenarios,
)
from .recipe_precursor_learning import RecipePrecursorLearningRun, run_recipe_precursor_learning_case


@dataclass(frozen=True, slots=True)
class InstrumentalValueFrame:
    frame_id: str
    resource_ref: str
    need_refs: tuple[str, ...]
    recipe_candidate_refs: tuple[str, ...]
    precursor_candidate_refs: tuple[str, ...]
    value_chain_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    station_affordance_refs: tuple[str, ...]
    ab7_constraint_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    value_status: str
    value_kind: str
    confidence: float
    confidence_policy: str
    intrinsic_value_claimed: bool = False
    mature_automation_claimed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class ValueChain:
    chain_id: str
    chain_kind: str
    start_refs: tuple[str, ...]
    intermediate_refs: tuple[str, ...]
    terminal_refs: tuple[str, ...]
    required_refs: tuple[str, ...]
    missing_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeansCandidate:
    means_candidate_id: str
    resource_ref: str
    means_for_refs: tuple[str, ...]
    required_context_refs: tuple[str, ...]
    blocked_context_refs: tuple[str, ...]
    supporting_trace_refs: tuple[str, ...]
    disconfirming_trace_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    readiness_status: str
    fact_claimed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


@dataclass(frozen=True, slots=True)
class ResourceNeedBinding:
    binding_id: str
    resource_ref: str
    need_refs: tuple[str, ...]
    chain_refs: tuple[str, ...]
    status: str
    missing_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValueReadinessAssessment:
    value_candidate_count: int
    weak_value_count: int
    provisional_value_count: int
    blocked_value_count: int
    disconfirmed_value_count: int
    intrinsic_value_detected: bool
    magic_value_detected: bool
    missing_need_detected: bool
    missing_effect_chain_detected: bool
    automation_claimed: bool
    action_request_emitted: bool
    calibration_score: float


@dataclass(frozen=True, slots=True)
class InstrumentalValueAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InstrumentalValueRun:
    run_id: str
    scenario_id: str
    public_need_refs: tuple[str, ...]
    resource_refs: tuple[str, ...]
    instrumental_value_frames: tuple[InstrumentalValueFrame, ...]
    value_chains: tuple[ValueChain, ...]
    means_candidates: tuple[MeansCandidate, ...]
    resource_need_bindings: tuple[ResourceNeedBinding, ...]
    ab7_constraint_refs: tuple[str, ...]
    p15_candidate_refs: tuple[str, ...]
    p13_gate_refs: tuple[str, ...]
    p14_affordance_refs: tuple[str, ...]
    effect_chain_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    disconfirmation_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    value_readiness_assessment: ValueReadinessAssessment
    falsifier_results: dict[str, bool]
    ablation_results: tuple[InstrumentalValueAblationCheck, ...]
    claim_safe_verdict: str
    intrinsic_value_claimed: bool = False
    mature_automation_claimed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False


_CLAIM_BOUNDARY = (
    "P16 assigns bounded instrumental value to intermediate resources through public need/effect/recipe-candidate "
    "evidence chains while blocking magic value and automation overclaims."
)


def list_instrumental_value_cases() -> tuple[InstrumentalValueScenarioSpec, ...]:
    return list_instrumental_value_scenarios()


def run_instrumental_value_case(scenario_id: str) -> InstrumentalValueRun:
    spec = instrumental_value_scenario_for_id(scenario_id)
    p15_run = run_recipe_precursor_learning_case(spec.p15_case_id)
    ab7_run = run_ab7_probe_case(spec.ab7_case_id)

    recipe_candidate_refs = tuple(item.recipe_candidate_id for item in p15_run.recipe_candidates)
    precursor_candidate_refs = tuple(item.precursor_candidate_id for item in p15_run.precursor_candidates)
    p13_gate_refs = tuple(
        dict.fromkeys(ref for trace in p15_run.lived_trace_records for ref in trace.p13_schema_candidate_refs)
    )
    p14_affordance_refs = tuple(ab7_run.frame.p14_station_affordance_refs) if ab7_run.frame is not None else ()
    ab7_constraint_refs = tuple(
        item.constraint_id for item in (ab7_run.frame.abductive_constraints if ab7_run.frame is not None else ())
    )

    effect_chain_refs = tuple(dict.fromkeys(ref for trace in p15_run.lived_trace_records for ref in trace.public_effect_refs))
    confounder_refs = tuple(
        dict.fromkeys(
            str(item.get("confounder_ref"))
            for item in p15_run.confounder_records
            if str(item.get("status")) in {"active", "unresolved"}
        )
    )
    disconfirmation_refs = tuple(dict.fromkeys(str(item.get("trace_ref")) for item in p15_run.disconfirming_records))

    frames, value_chains, means_candidates, bindings, blocked_reasons = _build_value_objects(
        spec=spec,
        p15_run=p15_run,
        ab7_run=ab7_run,
        effect_chain_refs=effect_chain_refs,
        confounder_refs=confounder_refs,
        disconfirmation_refs=disconfirmation_refs,
        recipe_candidate_refs=recipe_candidate_refs,
        precursor_candidate_refs=precursor_candidate_refs,
        p14_affordance_refs=p14_affordance_refs,
        ab7_constraint_refs=ab7_constraint_refs,
    )

    readiness = _build_readiness_assessment(
        frames=frames,
        means_candidates=means_candidates,
        spec=spec,
        has_effect_chain=bool(effect_chain_refs),
    )

    draft = InstrumentalValueRun(
        run_id=f"p16:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        public_need_refs=spec.need_refs,
        resource_refs=spec.resource_refs,
        instrumental_value_frames=frames,
        value_chains=value_chains,
        means_candidates=means_candidates,
        resource_need_bindings=bindings,
        ab7_constraint_refs=ab7_constraint_refs,
        p15_candidate_refs=recipe_candidate_refs,
        p13_gate_refs=p13_gate_refs,
        p14_affordance_refs=p14_affordance_refs,
        effect_chain_refs=effect_chain_refs,
        confounder_refs=confounder_refs,
        disconfirmation_refs=disconfirmation_refs,
        blocked_reasons=blocked_reasons,
        value_readiness_assessment=readiness,
        falsifier_results={},
        ablation_results=(),
        claim_safe_verdict="no_clear_advantage",
        intrinsic_value_claimed=False,
        mature_automation_claimed=False,
        action_request_emitted=False,
        world_submission_emitted=False,
        hidden_eval_used=False,
        scenario_label_used=False,
    )

    from .instrumental_value_falsifiers import evaluate_instrumental_value_falsifiers

    falsifiers = evaluate_instrumental_value_falsifiers(run=draft, claim_boundary=_CLAIM_BOUNDARY)
    verdict = "mora_instrumental_value_advantage" if not any(falsifiers.values()) else "insufficient_evidence"

    return InstrumentalValueRun(
        run_id=draft.run_id,
        scenario_id=draft.scenario_id,
        public_need_refs=draft.public_need_refs,
        resource_refs=draft.resource_refs,
        instrumental_value_frames=draft.instrumental_value_frames,
        value_chains=draft.value_chains,
        means_candidates=draft.means_candidates,
        resource_need_bindings=draft.resource_need_bindings,
        ab7_constraint_refs=draft.ab7_constraint_refs,
        p15_candidate_refs=draft.p15_candidate_refs,
        p13_gate_refs=draft.p13_gate_refs,
        p14_affordance_refs=draft.p14_affordance_refs,
        effect_chain_refs=draft.effect_chain_refs,
        confounder_refs=draft.confounder_refs,
        disconfirmation_refs=draft.disconfirmation_refs,
        blocked_reasons=draft.blocked_reasons,
        value_readiness_assessment=draft.value_readiness_assessment,
        falsifier_results=falsifiers,
        ablation_results=(),
        claim_safe_verdict=verdict,
        intrinsic_value_claimed=False,
        mature_automation_claimed=False,
        action_request_emitted=False,
        world_submission_emitted=False,
        hidden_eval_used=False,
        scenario_label_used=False,
    )


def run_instrumental_value_matrix() -> tuple[InstrumentalValueRun, ...]:
    return tuple(run_instrumental_value_case(item.scenario_id) for item in list_instrumental_value_scenarios())


def run_instrumental_value_ablations() -> tuple[InstrumentalValueAblationCheck, ...]:
    runs = {item.scenario_id: item for item in run_instrumental_value_matrix()}
    checks: list[InstrumentalValueAblationCheck] = []

    checks.append(InstrumentalValueAblationCheck("remove_need_refs", "resource_without_need_no_value", ("no_value_or_blocked",), (_status_ok(runs["resource_without_need_no_value"], {"no_value", "blocked"}),)))
    checks.append(InstrumentalValueAblationCheck("remove_resource_refs", "iron_magic_value_guard", ("no_value",), (_frame_absent_or_no_value(runs["iron_magic_value_guard"]),)))
    checks.append(InstrumentalValueAblationCheck("remove_effect_chain_refs", "resource_with_recipe_candidate_but_missing_effect_chain", ("blocked_or_weak",), (_status_ok(runs["resource_with_recipe_candidate_but_missing_effect_chain"], {"blocked", "weak_instrumental", "no_value"}),)))
    checks.append(InstrumentalValueAblationCheck("remove_recipe_candidate_refs", "hidden_eval_value_rule_rejected", ("no_recipe_derived_value",), ("no_recipe_derived_value" if not runs["hidden_eval_value_rule_rejected"].p15_candidate_refs else "recipe_refs_present",)))
    checks.append(InstrumentalValueAblationCheck("remove_AB7_constraint_refs", "hidden_eval_value_rule_rejected", ("blocked",), (_frame_absent_or_no_value(runs["hidden_eval_value_rule_rejected"]),)))
    checks.append(InstrumentalValueAblationCheck("remove_P13_gate_refs", "resource_without_need_no_value", ("weak_or_blocked",), (_status_ok(runs["resource_without_need_no_value"], {"no_value", "blocked", "weak_instrumental"}),)))
    checks.append(InstrumentalValueAblationCheck("remove_P14_affordance_refs", "resource_with_station_affordance_missing", ("blocked",), (_status_ok(runs["resource_with_station_affordance_missing"], {"blocked"}),)))
    checks.append(InstrumentalValueAblationCheck("active_confounder", "confounded_resource_value", ("weak_or_blocked",), (_status_ok(runs["confounded_resource_value"], {"weak_instrumental", "blocked"}),)))
    checks.append(InstrumentalValueAblationCheck("disconfirming_trace", "disconfirmed_resource_value", ("disconfirmed_or_blocked",), (_status_ok(runs["disconfirmed_resource_value"], {"disconfirmed", "blocked"}),)))
    checks.append(InstrumentalValueAblationCheck("hidden_eval_only_value_rule", "hidden_eval_value_rule_rejected", ("no_value_or_blocked",), (_frame_absent_or_no_value(runs["hidden_eval_value_rule_rejected"]),)))
    checks.append(InstrumentalValueAblationCheck("name_only_resource", "iron_magic_value_guard", ("no_value",), (_status_ok(runs["iron_magic_value_guard"], {"no_value", "blocked"}),)))

    return tuple(checks)


def _build_value_objects(
    *,
    spec: InstrumentalValueScenarioSpec,
    p15_run: RecipePrecursorLearningRun,
    ab7_run,
    effect_chain_refs: tuple[str, ...],
    confounder_refs: tuple[str, ...],
    disconfirmation_refs: tuple[str, ...],
    recipe_candidate_refs: tuple[str, ...],
    precursor_candidate_refs: tuple[str, ...],
    p14_affordance_refs: tuple[str, ...],
    ab7_constraint_refs: tuple[str, ...],
) -> tuple[
    tuple[InstrumentalValueFrame, ...],
    tuple[ValueChain, ...],
    tuple[MeansCandidate, ...],
    tuple[ResourceNeedBinding, ...],
    tuple[str, ...],
]:
    if not spec.resource_refs:
        return (), (), (), (), ("resource_refs_required",)

    has_need = bool(spec.need_refs)
    has_recipe_refs = bool(recipe_candidate_refs)
    has_effect_chain = bool(effect_chain_refs)
    has_affordance = bool(p14_affordance_refs)
    has_ab7 = bool(ab7_constraint_refs) and (ab7_run.frame is not None)
    protected_eval = bool(spec.protected_eval_only) or ("protected_evaluator_only_rule_forbidden" in tuple(getattr(ab7_run, "reason_codes", ())))

    readiness_statuses = tuple(
        str(getattr(item.readiness_status, "value", item.readiness_status))
        for item in (ab7_run.frame.automation_readiness if ab7_run.frame is not None else ())
    )
    automation_blocked = (not readiness_statuses) or all(
        status in {"blocked", "provisional_only", "not_ready", "evidence_required", "automation_forbidden_in_ab7"}
        for status in readiness_statuses
    )

    blocked_reasons: list[str] = []
    if protected_eval:
        blocked_reasons.append("protected_evaluator_only_rule_forbidden")
    if not has_need:
        blocked_reasons.append("need_refs_required")
    if not has_effect_chain:
        blocked_reasons.append("effect_chain_refs_required")
    if spec.station_linked and not has_affordance:
        blocked_reasons.append("p14_station_affordance_refs_required")
    if not has_ab7:
        blocked_reasons.append("ab7_constraint_refs_required")
    if spec.name_only_resource and (not has_need and not has_effect_chain):
        blocked_reasons.append("name_only_resource_forbidden")
    if confounder_refs:
        blocked_reasons.append("active_confounder_requires_resolution")
    if disconfirmation_refs:
        blocked_reasons.append("disconfirming_trace_present")

    value_status = "no_value"
    confidence = 0.0
    if protected_eval:
        value_status = "blocked"
        confidence = 0.12
    elif spec.name_only_resource and not has_need and not has_effect_chain:
        value_status = "no_value"
        confidence = 0.02
    elif not has_need:
        value_status = "no_value"
        confidence = 0.06
    elif not has_effect_chain or not has_ab7:
        value_status = "blocked"
        confidence = 0.18
    elif spec.station_linked and not has_affordance:
        value_status = "blocked"
        confidence = 0.18
    elif disconfirmation_refs:
        value_status = "disconfirmed"
        confidence = 0.17
    elif confounder_refs:
        value_status = "weak_instrumental"
        confidence = 0.31
    elif sum(1 for item in p15_run.lived_trace_records if item.public_effect_refs) >= 2:
        value_status = "repeated_trace_supported"
        confidence = 0.58
    elif has_recipe_refs:
        value_status = "provisional_instrumental"
        confidence = 0.44
    else:
        value_status = "weak_instrumental"
        confidence = 0.29

    value_kind = "unknown_or_unbound"
    if has_need and has_recipe_refs and has_effect_chain:
        value_kind = "means_to_recipe_candidate"
    elif has_need and has_effect_chain and spec.station_linked:
        value_kind = "means_to_station_effect"
    elif has_need and has_effect_chain:
        value_kind = "means_to_need"
    elif has_recipe_refs:
        value_kind = "means_to_precursor_chain"

    chains: list[ValueChain] = []
    chain_refs: list[str] = []
    for idx, resource_ref in enumerate(spec.resource_refs, start=1):
        chain_id = f"p16:{spec.scenario_id}:chain:{idx}"
        chain_refs.append(chain_id)
        chain_kind = "resource_to_effect"
        if not has_need:
            chain_kind = "need_to_resource"
        elif has_recipe_refs:
            chain_kind = "resource_to_recipe_candidate"
        elif spec.station_linked:
            chain_kind = "resource_to_station_input"
        if disconfirmation_refs:
            chain_kind = "resource_to_disconfirmed_candidate"
        if not has_effect_chain:
            chain_kind = "resource_to_blocked_missing_input"

        if value_status in {"repeated_trace_supported", "provisional_instrumental"}:
            chain_status = "complete_public_chain"
        elif value_status in {"weak_instrumental"}:
            chain_status = "confounded" if confounder_refs else "partial_chain"
        elif value_status == "disconfirmed":
            chain_status = "disconfirmed"
        elif value_status == "blocked":
            chain_status = "blocked"
        else:
            chain_status = "insufficient_evidence"

        missing_refs = tuple(
            ref
            for ref in (
                "need_refs" if not has_need else None,
                "effect_chain_refs" if not has_effect_chain else None,
                "ab7_constraint_refs" if not has_ab7 else None,
                "p14_affordance_refs" if (spec.station_linked and not has_affordance) else None,
            )
            if ref is not None
        )

        evidence_refs = tuple(
            dict.fromkeys(
                (
                    resource_ref,
                    *spec.need_refs,
                    *recipe_candidate_refs,
                    *ab7_constraint_refs,
                    *p14_affordance_refs,
                    *effect_chain_refs,
                    *confounder_refs,
                    *disconfirmation_refs,
                )
            )
        )
        chains.append(
            ValueChain(
                chain_id=chain_id,
                chain_kind=chain_kind,
                start_refs=(resource_ref,),
                intermediate_refs=tuple(dict.fromkeys((*recipe_candidate_refs, *precursor_candidate_refs, *p14_affordance_refs))),
                terminal_refs=tuple(dict.fromkeys((*spec.need_refs, *effect_chain_refs))),
                required_refs=("resource_ref", "need_ref", "effect_ref", "ab7_constraint_ref"),
                missing_refs=missing_refs,
                evidence_refs=evidence_refs,
                effect_refs=effect_chain_refs,
                status=chain_status,
                reason_codes=tuple(dict.fromkeys(blocked_reasons if blocked_reasons else ("public_chain_complete",))),
            )
        )

    frames: list[InstrumentalValueFrame] = []
    means: list[MeansCandidate] = []
    bindings: list[ResourceNeedBinding] = []

    for idx, resource_ref in enumerate(spec.resource_refs, start=1):
        frame_id = f"p16:{spec.scenario_id}:frame:{idx}"
        frame = InstrumentalValueFrame(
            frame_id=frame_id,
            resource_ref=resource_ref,
            need_refs=spec.need_refs,
            recipe_candidate_refs=recipe_candidate_refs,
            precursor_candidate_refs=precursor_candidate_refs,
            value_chain_refs=tuple(chain_refs),
            evidence_refs=tuple(
                dict.fromkeys(
                    (
                        resource_ref,
                        *spec.need_refs,
                        *recipe_candidate_refs,
                        *p14_affordance_refs,
                        *ab7_constraint_refs,
                        *effect_chain_refs,
                        *confounder_refs,
                        *disconfirmation_refs,
                    )
                )
            ),
            effect_refs=effect_chain_refs,
            station_affordance_refs=p14_affordance_refs,
            ab7_constraint_refs=ab7_constraint_refs,
            confounder_refs=confounder_refs,
            missing_evidence=tuple(dict.fromkeys(blocked_reasons)),
            value_status=value_status,
            value_kind=value_kind,
            confidence=round(confidence, 3),
            confidence_policy="evidence_bounded",
            intrinsic_value_claimed=False,
            mature_automation_claimed=False,
            action_request_emitted=False,
            world_submission_emitted=False,
            hidden_eval_used=False,
            scenario_label_used=False,
        )
        frames.append(frame)

        if value_status in {"repeated_trace_supported", "provisional_instrumental", "weak_instrumental", "blocked", "disconfirmed"}:
            if value_status in {"blocked", "no_value", "disconfirmed"}:
                readiness = "blocked" if value_status != "no_value" else "not_ready"
            elif value_status == "repeated_trace_supported":
                readiness = "evidence_required"
            elif value_status == "provisional_instrumental":
                readiness = "provisional"
            else:
                readiness = "weak"
            if not automation_blocked:
                readiness = "automation_forbidden_in_P16"

            means.append(
                MeansCandidate(
                    means_candidate_id=f"p16:{spec.scenario_id}:means:{idx}",
                    resource_ref=resource_ref,
                    means_for_refs=tuple(dict.fromkeys((*spec.need_refs, *recipe_candidate_refs))),
                    required_context_refs=("public_need_refs", "effect_chain_refs", "ab7_constraint_refs"),
                    blocked_context_refs=tuple(dict.fromkeys(blocked_reasons)),
                    supporting_trace_refs=tuple(trace.trace_id for trace in p15_run.lived_trace_records if trace.public_effect_refs),
                    disconfirming_trace_refs=disconfirmation_refs,
                    confounder_refs=confounder_refs,
                    readiness_status=readiness,
                    fact_claimed=False,
                    action_request_emitted=False,
                    world_submission_emitted=False,
                )
            )

        bindings.append(
            ResourceNeedBinding(
                binding_id=f"p16:{spec.scenario_id}:binding:{idx}",
                resource_ref=resource_ref,
                need_refs=spec.need_refs,
                chain_refs=tuple(chain_refs),
                status=("bound" if (has_need and value_status not in {"no_value"}) else "unbound"),
                missing_refs=tuple(dict.fromkeys(blocked_reasons)),
                reason_codes=tuple(dict.fromkeys(blocked_reasons if blocked_reasons else ("binding_supported",))),
            )
        )

    return tuple(frames), tuple(chains), tuple(means), tuple(bindings), tuple(dict.fromkeys(blocked_reasons))


def _build_readiness_assessment(
    *,
    frames: tuple[InstrumentalValueFrame, ...],
    means_candidates: tuple[MeansCandidate, ...],
    spec: InstrumentalValueScenarioSpec,
    has_effect_chain: bool,
) -> ValueReadinessAssessment:
    statuses = [item.value_status for item in frames]
    intrinsic_detected = any(item.intrinsic_value_claimed for item in frames)
    magic_detected = bool(spec.name_only_resource and any(item.value_status not in {"no_value", "blocked"} for item in frames))

    return ValueReadinessAssessment(
        value_candidate_count=len(frames),
        weak_value_count=sum(1 for status in statuses if status == "weak_instrumental"),
        provisional_value_count=sum(1 for status in statuses if status in {"provisional_instrumental", "repeated_trace_supported"}),
        blocked_value_count=sum(1 for status in statuses if status == "blocked"),
        disconfirmed_value_count=sum(1 for status in statuses if status == "disconfirmed"),
        intrinsic_value_detected=intrinsic_detected,
        magic_value_detected=magic_detected,
        missing_need_detected=not bool(spec.need_refs),
        missing_effect_chain_detected=not has_effect_chain,
        automation_claimed=False,
        action_request_emitted=False,
        calibration_score=0.55 if frames else 0.0,
    )


def _status_ok(run: InstrumentalValueRun, allowed: set[str]) -> str:
    if not run.instrumental_value_frames:
        return "no_value_or_blocked"
    status = run.instrumental_value_frames[0].value_status
    return "ok" if status in allowed else f"unexpected:{status}"


def _frame_absent_or_no_value(run: InstrumentalValueRun) -> str:
    if not run.instrumental_value_frames:
        return "no_value_or_blocked"
    status = run.instrumental_value_frames[0].value_status
    return "no_value_or_blocked" if status in {"no_value", "blocked"} else f"unexpected:{status}"
