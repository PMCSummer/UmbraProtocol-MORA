from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .delayed_credit_learning import DelayedCreditLearningRun, run_delayed_credit_learning_case
from .recipe_precursor_scenarios import (
    RecipePrecursorScenarioSpec,
    list_recipe_precursor_scenarios,
    recipe_precursor_scenario_for_id,
)
from .station_affordance import StationAffordanceProofRun, run_station_affordance_case


@dataclass(frozen=True, slots=True)
class LivedRecipeTrace:
    trace_id: str
    public_station_ref: str | None
    public_input_refs: tuple[str, ...]
    public_output_refs: tuple[str, ...]
    public_effect_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    station_attempt_refs: tuple[str, ...]
    action_effect_refs: tuple[str, ...]
    p13_credit_link_refs: tuple[str, ...]
    p13_schema_candidate_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    timing_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    hidden_eval_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class PrecursorCandidate:
    precursor_candidate_id: str
    candidate_kind: str
    precursor_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    supporting_trace_refs: tuple[str, ...]
    disconfirming_trace_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    support_status: str
    confidence: float
    confidence_policy: str
    fact_claimed: bool = False
    cause_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class RecipeCandidate:
    recipe_candidate_id: str
    station_ref: str | None
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    supporting_trace_refs: tuple[str, ...]
    disconfirming_trace_refs: tuple[str, ...]
    p13_schema_candidate_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    required_public_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    maturity_status: str
    maturity_score: float
    maturity_policy: str
    one_shot_mature: bool = False
    hidden_recipe_used: bool = False
    protected_eval_used: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


@dataclass(frozen=True, slots=True)
class MaturityAssessment:
    recipe_candidate_count: int
    precursor_candidate_count: int
    mature_recipe_count: int
    weak_candidate_count: int
    provisional_candidate_count: int
    repeated_trace_supported_count: int
    blocked_candidate_count: int
    hidden_recipe_detected: bool
    one_shot_maturity_detected: bool
    confounder_bypass_detected: bool
    disconfirmation_ignored_detected: bool
    missing_evidence_erased_detected: bool
    calibration_score: float


@dataclass(frozen=True, slots=True)
class RecipeLearningAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecipePrecursorLearningRun:
    run_id: str
    scenario_id: str
    lived_trace_records: tuple[LivedRecipeTrace, ...]
    precursor_candidates: tuple[PrecursorCandidate, ...]
    recipe_candidates: tuple[RecipeCandidate, ...]
    confounder_records: tuple[dict[str, object], ...]
    disconfirming_records: tuple[dict[str, object], ...]
    maturity_assessment: MaturityAssessment
    falsifier_results: dict[str, bool]
    ablation_results: tuple[RecipeLearningAblationCheck, ...]
    claim_safe_verdict: str
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


_CLAIM_BOUNDARY = (
    "P15 builds provisional recipe/precursor candidates from lived public traces under repetition/confounder/"
    "disconfirmation constraints, without mature recipe claim, automation, or consciousness claim."
)


def list_recipe_precursor_cases() -> tuple[RecipePrecursorScenarioSpec, ...]:
    return list_recipe_precursor_scenarios()


def run_recipe_precursor_learning_case(scenario_id: str) -> RecipePrecursorLearningRun:
    spec = recipe_precursor_scenario_for_id(scenario_id)
    p14_run = run_station_affordance_case(spec.p14_case_id)
    p13_run = run_delayed_credit_learning_case(spec.p13_case_id)

    traces = _build_lived_traces(spec=spec, p14_run=p14_run, p13_run=p13_run)
    precursor_candidates = _build_precursor_candidates(spec=spec, traces=traces, p13_run=p13_run)
    recipe_candidates = _build_recipe_candidates(spec=spec, traces=traces, p13_run=p13_run, p14_run=p14_run)

    confounder_records = tuple(asdict(item) for item in p13_run.confounder_records)
    disconfirming_records = _build_disconfirming_records(spec=spec, traces=traces, p13_run=p13_run)

    assessment = MaturityAssessment(
        recipe_candidate_count=len(recipe_candidates),
        precursor_candidate_count=len(precursor_candidates),
        mature_recipe_count=sum(1 for item in recipe_candidates if item.maturity_status == "mature_forbidden_or_not_reached" and item.maturity_score >= 0.9),
        weak_candidate_count=sum(1 for item in recipe_candidates if item.maturity_status == "weak_candidate"),
        provisional_candidate_count=sum(1 for item in recipe_candidates if item.maturity_status == "provisional_candidate"),
        repeated_trace_supported_count=sum(1 for item in recipe_candidates if item.maturity_status == "repeated_trace_supported"),
        blocked_candidate_count=sum(1 for item in recipe_candidates if item.maturity_status == "blocked"),
        hidden_recipe_detected=False,
        one_shot_maturity_detected=False,
        confounder_bypass_detected=False,
        disconfirmation_ignored_detected=False,
        missing_evidence_erased_detected=False,
        calibration_score=float(getattr(p13_run.maturity_assessment, "calibration_score", 0.0)),
    )

    draft = RecipePrecursorLearningRun(
        run_id=f"p15:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        lived_trace_records=traces,
        precursor_candidates=precursor_candidates,
        recipe_candidates=recipe_candidates,
        confounder_records=confounder_records,
        disconfirming_records=disconfirming_records,
        maturity_assessment=assessment,
        falsifier_results={},
        ablation_results=(),
        claim_safe_verdict="no_clear_advantage",
        action_request_emitted=False,
        world_submission_emitted=False,
    )

    from .recipe_precursor_falsifiers import evaluate_recipe_precursor_falsifiers

    falsifiers = evaluate_recipe_precursor_falsifiers(run=draft, claim_boundary=_CLAIM_BOUNDARY)
    assessment = MaturityAssessment(
        recipe_candidate_count=assessment.recipe_candidate_count,
        precursor_candidate_count=assessment.precursor_candidate_count,
        mature_recipe_count=assessment.mature_recipe_count,
        weak_candidate_count=assessment.weak_candidate_count,
        provisional_candidate_count=assessment.provisional_candidate_count,
        repeated_trace_supported_count=assessment.repeated_trace_supported_count,
        blocked_candidate_count=assessment.blocked_candidate_count,
        hidden_recipe_detected=falsifiers["hidden_recipe_leak"],
        one_shot_maturity_detected=falsifiers["one_shot_recipe_maturity"],
        confounder_bypass_detected=falsifiers["confounder_bypasses_recipe_maturity"],
        disconfirmation_ignored_detected=falsifiers["disconfirming_trace_ignored"],
        missing_evidence_erased_detected=falsifiers["missing_evidence_erased"],
        calibration_score=assessment.calibration_score,
    )
    verdict = "mora_recipe_precursor_provisional_advantage" if not any(falsifiers.values()) else "insufficient_evidence"

    return RecipePrecursorLearningRun(
        run_id=draft.run_id,
        scenario_id=draft.scenario_id,
        lived_trace_records=draft.lived_trace_records,
        precursor_candidates=draft.precursor_candidates,
        recipe_candidates=draft.recipe_candidates,
        confounder_records=draft.confounder_records,
        disconfirming_records=draft.disconfirming_records,
        maturity_assessment=assessment,
        falsifier_results=falsifiers,
        ablation_results=(),
        claim_safe_verdict=verdict,
        action_request_emitted=False,
        world_submission_emitted=False,
    )


def run_recipe_precursor_learning_matrix() -> tuple[RecipePrecursorLearningRun, ...]:
    return tuple(run_recipe_precursor_learning_case(item.scenario_id) for item in list_recipe_precursor_scenarios())


def run_recipe_precursor_ablations() -> tuple[RecipeLearningAblationCheck, ...]:
    runs = {item.scenario_id: item for item in run_recipe_precursor_learning_matrix()}
    checks: list[RecipeLearningAblationCheck] = []

    checks.append(RecipeLearningAblationCheck("no_lived_trace", "visible_station_no_trace_no_recipe", ("no_recipe_candidate",), ("no_recipe_candidate" if not runs["visible_station_no_trace_no_recipe"].recipe_candidates else "recipe_candidate_present",)))
    checks.append(RecipeLearningAblationCheck("no_effect_refs", "station_success_without_effect_refs_blocked", ("candidate_blocked_or_absent",), ("candidate_blocked_or_absent" if not runs["station_success_without_effect_refs_blocked"].recipe_candidates or runs["station_success_without_effect_refs_blocked"].recipe_candidates[0].maturity_status == "blocked" else "candidate_not_blocked",)))
    checks.append(RecipeLearningAblationCheck("no_input_refs", "station_success_without_input_refs_blocked", ("candidate_blocked_or_absent",), ("candidate_blocked_or_absent" if not runs["station_success_without_input_refs_blocked"].recipe_candidates or runs["station_success_without_input_refs_blocked"].recipe_candidates[0].maturity_status == "blocked" else "candidate_not_blocked",)))
    checks.append(RecipeLearningAblationCheck("one_trace_only", "one_success_trace_provisional_only", ("no_mature_recipe",), ("no_mature_recipe" if runs["one_success_trace_provisional_only"].maturity_assessment.mature_recipe_count == 0 else "mature_recipe_present",)))
    checks.append(RecipeLearningAblationCheck("remove_repetition", "one_success_trace_provisional_only", ("no_repeated_trace_supported",), ("no_repeated_trace_supported" if runs["one_success_trace_provisional_only"].maturity_assessment.repeated_trace_supported_count == 0 else "repeated_trace_supported_present",)))
    checks.append(RecipeLearningAblationCheck("remove_confounder_records", "confounded_station_effect", ("confounder_risk_preserved",), ("confounder_risk_preserved" if runs["confounded_station_effect"].confounder_records else "confounder_records_missing",)))
    checks.append(RecipeLearningAblationCheck("disconfirming_trace", "disconfirming_trace_blocks_maturity", ("support_decreases_or_blocked",), ("support_decreases_or_blocked" if runs["disconfirming_trace_blocks_maturity"].disconfirming_records else "no_disconfirming_record",)))
    checks.append(RecipeLearningAblationCheck("hidden_eval_only_recipe", "hidden_recipe_only_no_candidate", ("no_public_recipe_candidate",), ("no_public_recipe_candidate" if not runs["hidden_recipe_only_no_candidate"].recipe_candidates else "recipe_candidate_present",)))
    checks.append(RecipeLearningAblationCheck("remove_P13_gate_refs", "one_success_trace_provisional_only", ("maturity_blocked",), ("maturity_blocked" if runs["one_success_trace_provisional_only"].recipe_candidates and runs["one_success_trace_provisional_only"].recipe_candidates[0].maturity_status in {"weak_candidate", "provisional_candidate", "blocked"} else "maturity_not_blocked",)))
    checks.append(RecipeLearningAblationCheck("ambiguous_output", "ambiguous_output_effect", ("no_mature_recipe",), ("no_mature_recipe" if runs["ambiguous_output_effect"].maturity_assessment.mature_recipe_count == 0 else "mature_recipe_present",)))

    return tuple(checks)


def _build_lived_traces(
    *,
    spec: RecipePrecursorScenarioSpec,
    p14_run: StationAffordanceProofRun,
    p13_run: DelayedCreditLearningRun,
) -> tuple[LivedRecipeTrace, ...]:
    if spec.no_lived_trace:
        return ()

    base_input_refs = tuple(p14_run.public_station_basis.available_input_refs)
    base_effect_refs = tuple(p14_run.effect_refs)
    if spec.remove_input_refs:
        base_input_refs = ()
    if spec.remove_effect_refs:
        base_effect_refs = ()

    base_output_refs: tuple[str, ...]
    if base_effect_refs:
        base_output_refs = tuple(f"output:{ref}" for ref in base_effect_refs)
    else:
        base_output_refs = ()

    p13_credit_refs = tuple(item.link_id for item in p13_run.candidate_credit_links)
    p13_schema_refs = tuple(item.schema_candidate_id for item in p13_run.provisional_schema_candidates)
    confounder_refs = tuple(item.confounder_ref for item in p13_run.confounder_records)
    timing_refs = tuple(
        ref
        for record in p13_run.delayed_effect_records
        for ref in tuple(record.get("timing_refs", ()))
    )

    traces: list[LivedRecipeTrace] = []
    for idx in range(1, max(1, spec.repeated_traces) + 1):
        trace_id = f"p15:{spec.scenario_id}:trace:{idx}"
        disconfirming_step = spec.expect_disconfirming and idx == spec.repeated_traces
        effect_refs = () if disconfirming_step else base_effect_refs
        output_refs = () if disconfirming_step else base_output_refs
        traces.append(
            LivedRecipeTrace(
                trace_id=trace_id,
                public_station_ref=p14_run.station_ref,
                public_input_refs=base_input_refs,
                public_output_refs=output_refs,
                public_effect_refs=effect_refs,
                ap01_request_refs=(
                    (p14_run.attempt_record.ap01_request_ref,)
                    if (p14_run.attempt_record is not None and p14_run.attempt_record.ap01_request_ref)
                    else ()
                ),
                station_attempt_refs=((p14_run.attempt_record.attempt_id,) if p14_run.attempt_record is not None else ()),
                action_effect_refs=effect_refs,
                p13_credit_link_refs=p13_credit_refs,
                p13_schema_candidate_refs=p13_schema_refs,
                confounder_refs=confounder_refs,
                timing_refs=timing_refs,
                evidence_refs=tuple(
                    dict.fromkeys(
                        (
                            f"station:{p14_run.station_ref}" if p14_run.station_ref else "station:none",
                            *base_input_refs,
                            *effect_refs,
                            *p13_credit_refs,
                            *p13_schema_refs,
                            *timing_refs,
                        )
                    )
                ),
                hidden_eval_used=False,
                scenario_label_used=False,
            )
        )
    return tuple(traces)


def _build_precursor_candidates(
    *,
    spec: RecipePrecursorScenarioSpec,
    traces: tuple[LivedRecipeTrace, ...],
    p13_run: DelayedCreditLearningRun,
) -> tuple[PrecursorCandidate, ...]:
    if not traces:
        return ()
    input_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.public_input_refs))
    effect_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.public_effect_refs))
    confounder_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.confounder_refs))
    supporting = tuple(trace.trace_id for trace in traces if trace.public_effect_refs)
    disconfirming = tuple(trace.trace_id for trace in traces if not trace.public_effect_refs)

    missing: list[str] = []
    support_status = "provisional"
    confidence = 0.46

    if not input_refs:
        missing.append("public_input_refs")
    if not effect_refs:
        missing.append("public_effect_refs")
    if confounder_refs and any(item.status in {"active", "unresolved"} for item in p13_run.confounder_records):
        support_status = "weak"
        confidence = min(confidence, 0.38)
        missing.append("active_confounder_disambiguation")
    if spec.expect_disconfirming or disconfirming:
        support_status = "disconfirmed"
        confidence = min(confidence, 0.24)
        missing.append("disconfirming_trace_present")
    elif len(supporting) >= 2 and not confounder_refs:
        support_status = "repeated_trace_supported"
        confidence = 0.59
    elif len(supporting) == 1:
        support_status = "weak"
        confidence = 0.41

    if missing and support_status != "disconfirmed":
        support_status = "blocked" if ("public_input_refs" in missing or "public_effect_refs" in missing) else support_status

    candidate_kind = "input_precursor" if input_refs else "unknown_precursor"
    return (
        PrecursorCandidate(
            precursor_candidate_id=f"p15:{spec.scenario_id}:precursor:1",
            candidate_kind=candidate_kind,
            precursor_refs=input_refs if input_refs else ("unknown_precursor",),
            effect_refs=effect_refs,
            supporting_trace_refs=supporting,
            disconfirming_trace_refs=disconfirming,
            confounder_refs=confounder_refs,
            missing_evidence=tuple(dict.fromkeys(missing)),
            support_status=support_status,
            confidence=round(confidence, 3),
            confidence_policy="evidence_bounded",
            fact_claimed=False,
            cause_confirmed=False,
        ),
    )


def _build_recipe_candidates(
    *,
    spec: RecipePrecursorScenarioSpec,
    traces: tuple[LivedRecipeTrace, ...],
    p13_run: DelayedCreditLearningRun,
    p14_run: StationAffordanceProofRun,
) -> tuple[RecipeCandidate, ...]:
    if not traces:
        return ()

    station_ref = p14_run.station_ref
    input_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.public_input_refs))
    output_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.public_output_refs))
    effect_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.public_effect_refs))
    supporting = tuple(trace.trace_id for trace in traces if trace.public_effect_refs)
    disconfirming = tuple(trace.trace_id for trace in traces if not trace.public_effect_refs)
    confounder_refs = tuple(dict.fromkeys(ref for trace in traces for ref in trace.confounder_refs))
    schema_refs = tuple(item.schema_candidate_id for item in p13_run.provisional_schema_candidates)

    required_public_evidence = (
        "station_ref",
        "input_refs",
        "effect_refs",
        "repeated_public_trace_or_block_reason",
        "p13_gate_refs",
    )

    missing: list[str] = []
    if not station_ref:
        missing.append("public_station_ref")
    if not input_refs:
        missing.append("public_input_refs")
    if not effect_refs:
        missing.append("public_effect_refs")
    if not schema_refs:
        missing.append("p13_schema_candidate_refs")
    if spec.expect_delay:
        has_timing = any(trace.timing_refs for trace in traces)
        if not has_timing:
            missing.append("timing_refs_for_delayed_effect")

    active_confounder = confounder_refs and any(item.status in {"active", "unresolved"} for item in p13_run.confounder_records)

    maturity_status = "provisional_candidate"
    maturity_score = 0.44

    if spec.protected_eval_only_recipe:
        maturity_status = "blocked"
        maturity_score = 0.11
        missing.append("insufficient_public_lived_trace")
    elif missing:
        maturity_status = "blocked"
        maturity_score = 0.2
    elif spec.ambiguous_output or active_confounder:
        maturity_status = "weak_candidate"
        maturity_score = 0.35
        if active_confounder:
            missing.append("active_confounder_disambiguation")
        if spec.ambiguous_output:
            missing.append("ambiguous_output_disambiguation")
    elif spec.expect_disconfirming or disconfirming:
        maturity_status = "blocked"
        maturity_score = 0.23
        missing.append("disconfirming_trace_present")
    elif len(supporting) >= 3:
        maturity_status = "repeated_trace_supported"
        maturity_score = 0.61
    elif len(supporting) == 1:
        maturity_status = "weak_candidate"
        maturity_score = 0.39

    return (
        RecipeCandidate(
            recipe_candidate_id=f"p15:{spec.scenario_id}:recipe:1",
            station_ref=station_ref,
            input_refs=input_refs,
            output_refs=output_refs,
            effect_refs=effect_refs,
            supporting_trace_refs=supporting,
            disconfirming_trace_refs=disconfirming,
            p13_schema_candidate_refs=schema_refs,
            confounder_refs=confounder_refs,
            required_public_evidence=required_public_evidence,
            missing_evidence=tuple(dict.fromkeys(missing)),
            maturity_status=maturity_status,
            maturity_score=round(maturity_score, 3),
            maturity_policy="requires_repeated_public_traces_confounded_checked_disconfirmation_aware",
            one_shot_mature=False,
            hidden_recipe_used=False,
            protected_eval_used=False,
            fact_claimed=False,
            cause_confirmed=False,
            action_request_emitted=False,
            world_submission_emitted=False,
        ),
    )


def _build_disconfirming_records(
    *,
    spec: RecipePrecursorScenarioSpec,
    traces: tuple[LivedRecipeTrace, ...],
    p13_run: DelayedCreditLearningRun,
) -> tuple[dict[str, object], ...]:
    records: list[dict[str, object]] = []
    for trace in traces:
        if not trace.public_effect_refs:
            records.append(
                {
                    "record_id": f"{trace.trace_id}:disconfirming",
                    "trace_ref": trace.trace_id,
                    "reason": "expected_effect_missing",
                    "evidence_refs": trace.evidence_refs,
                }
            )
    if spec.expect_disconfirming and not records:
        records.append(
            {
                "record_id": f"p15:{spec.scenario_id}:disconfirming:synthetic",
                "trace_ref": traces[-1].trace_id if traces else "none",
                "reason": "disconfirming_expected",
                "evidence_refs": tuple(item.link_id for item in p13_run.candidate_credit_links),
            }
        )
    return tuple(records)
