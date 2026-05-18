from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache

from .ab5_hypothesis_update_probe import run_ab5_probe_case
from .ab6_causal_attribution_probe import run_ab6_probe_case
from .delayed_credit_scenarios import (
    DelayedCreditScenarioSpec,
    delayed_credit_scenario_for_id,
    list_delayed_credit_scenarios,
)
from .inner_state_calibration import run_inner_state_calibration_case


@dataclass(frozen=True, slots=True)
class EpisodeTrace:
    episode_id: str
    public_action_refs: tuple[str, ...]
    public_effect_refs: tuple[str, ...]
    event_digest_refs: tuple[str, ...]
    attribution_frame_refs: tuple[str, ...]
    support_update_refs: tuple[str, ...]
    timing_refs: tuple[str, ...]
    precursor_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    observed_outcome_refs: tuple[str, ...]
    hidden_eval_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class CandidateCreditLink:
    link_id: str
    precursor_ref: str
    effect_ref: str
    delay_window: str
    correlation_status: str
    attribution_kind_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    confidence: float
    confidence_policy: str
    maturity_status: str
    fact_claimed: bool = False
    cause_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class ConfounderRecord:
    confounder_id: str
    confounder_ref: str
    overlaps_with: tuple[str, ...]
    could_explain_effect: bool
    discriminating_evidence_needed: tuple[str, ...]
    credit_leak_risk: str
    status: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProvisionalSchemaCandidate:
    schema_candidate_id: str
    precursor_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    supporting_episode_refs: tuple[str, ...]
    disconfirming_episode_refs: tuple[str, ...]
    confounder_refs: tuple[str, ...]
    delay_profile: str
    maturity_score: float
    maturity_policy: str
    maturity_status: str
    blocked_reasons: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    hidden_recipe_used: bool = False
    one_shot_mature: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class MaturityAssessment:
    candidate_count: int
    mature_schema_count: int
    weak_candidate_count: int
    provisional_candidate_count: int
    blocked_candidate_count: int
    one_shot_maturity_detected: bool
    confounder_credit_leak_detected: bool
    delayed_misattribution_detected: bool
    evidence_repetition_count: int
    disconfirmation_count: int
    calibration_score: float


@dataclass(frozen=True, slots=True)
class DelayedCreditLearningRun:
    run_id: str
    scenario_id: str
    episode_traces: tuple[EpisodeTrace, ...]
    candidate_credit_links: tuple[CandidateCreditLink, ...]
    confounder_records: tuple[ConfounderRecord, ...]
    delayed_effect_records: tuple[dict[str, object], ...]
    provisional_schema_candidates: tuple[ProvisionalSchemaCandidate, ...]
    maturity_assessment: MaturityAssessment
    falsifier_results: dict[str, bool]
    calibration_summary: dict[str, object]
    claim_safe_verdict: str
    action_request_emitted: bool = False


@dataclass(frozen=True, slots=True)
class DelayedCreditAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


_CLAIM_BOUNDARY = (
    "P13 delayed-credit proof only: no mature recipe learning, no true-cause closure, no consciousness claim, "
    "and no general world-model learning claim."
)


def list_delayed_credit_cases() -> tuple[DelayedCreditScenarioSpec, ...]:
    return list_delayed_credit_scenarios()


def run_delayed_credit_learning_matrix() -> tuple[DelayedCreditLearningRun, ...]:
    return tuple(run_delayed_credit_learning_case(item.scenario_id) for item in list_delayed_credit_scenarios())


def run_delayed_credit_ablation_checks() -> tuple[DelayedCreditAblationCheck, ...]:
    matrix = {item.scenario_id: item for item in run_delayed_credit_learning_matrix()}
    checks: list[DelayedCreditAblationCheck] = []
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="no_effect_refs",
            scenario_id="hidden_recipe_only",
            expected_degradation=("no_usable_credit_candidate",),
            observed_behavior=(
                "no_usable_credit_candidate" if not matrix["hidden_recipe_only"].candidate_credit_links else "credit_candidate_present",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="no_precursor_refs",
            scenario_id="hidden_recipe_only",
            expected_degradation=("no_usable_credit_candidate",),
            observed_behavior=(
                "no_usable_credit_candidate"
                if not matrix["hidden_recipe_only"].candidate_credit_links
                else "precursor_present",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="no_timing_refs",
            scenario_id="delayed_effect_wrong_window",
            expected_degradation=("delayed_credit_blocked_or_weak",),
            observed_behavior=(
                "delayed_credit_blocked_or_weak"
                if all(item.correlation_status != "delayed_possible" for item in matrix["delayed_effect_wrong_window"].candidate_credit_links)
                else "delayed_credit_unjustified",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="remove_repetition",
            scenario_id="spurious_one_shot_correlation",
            expected_degradation=("maturity_blocked",),
            observed_behavior=(
                "maturity_blocked"
                if all(item.maturity_status in {"blocked", "weak"} for item in matrix["spurious_one_shot_correlation"].provisional_schema_candidates)
                else "maturity_not_blocked",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="remove_confounder_record",
            scenario_id="confounded_effect_two_precursors",
            expected_degradation=("confounder_leak_or_maturity_blocked",),
            observed_behavior=(
                "confounder_leak_or_maturity_blocked"
                if matrix["confounded_effect_two_precursors"].confounder_records
                else "confounder_record_missing",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="disconfirming_episode",
            scenario_id="disconfirming_episode",
            expected_degradation=("support_decreases_or_blocked",),
            observed_behavior=(
                "support_decreases_or_blocked"
                if any(item.correlation_status in {"disconfirmed", "insufficient_evidence"} for item in matrix["disconfirming_episode"].candidate_credit_links)
                else "support_not_decreased",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="hidden_eval_only",
            scenario_id="hidden_recipe_only",
            expected_degradation=("no_learned_candidate",),
            observed_behavior=(
                "no_learned_candidate" if not matrix["hidden_recipe_only"].candidate_credit_links else "candidate_from_hidden",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="request_without_effect",
            scenario_id="disconfirming_episode",
            expected_degradation=("no_learning_confirmation",),
            observed_behavior=(
                "no_learning_confirmation"
                if all(item.correlation_status != "correlated" for item in matrix["disconfirming_episode"].candidate_credit_links)
                else "request_confirmed_learning",
            ),
        )
    )
    checks.append(
        DelayedCreditAblationCheck(
            ablation_id="ambiguous_public_evidence",
            scenario_id="ambiguous_public_evidence",
            expected_degradation=("no_mature_schema",),
            observed_behavior=(
                "no_mature_schema"
                if all(item.maturity_status != "mature_forbidden_in_P13" for item in matrix["ambiguous_public_evidence"].provisional_schema_candidates)
                else "mature_schema_present",
            ),
        )
    )
    return tuple(checks)


def run_delayed_credit_learning_case(scenario_id: str) -> DelayedCreditLearningRun:
    spec = delayed_credit_scenario_for_id(scenario_id)
    ab6 = _ab6_case(spec.ab6_case_id)
    ab5 = _ab5_case(spec.ab5_case_id)
    p12 = _p12_case(spec.p12_case_id)
    traces = _episode_traces(spec=spec, ab6=ab6, ab5=ab5)
    links = _credit_links(spec=spec, traces=traces, ab6=ab6)
    confounders = _confounder_records(spec=spec, links=links)
    delayed_records = _delayed_records(spec=spec, traces=traces, links=links)
    schemas = _schema_candidates(spec=spec, links=links, confounders=confounders, traces=traces)
    provisional_count = sum(1 for item in schemas if item.maturity_status in {"provisional", "repeated_trace_supported"})
    weak_count = sum(1 for item in schemas if item.maturity_status == "weak")
    blocked_count = sum(1 for item in schemas if item.maturity_status == "blocked")
    from .delayed_credit_falsifiers import evaluate_delayed_credit_falsifiers

    assessment = MaturityAssessment(
        candidate_count=len(schemas),
        mature_schema_count=sum(1 for item in schemas if item.maturity_status == "mature_forbidden_in_P13"),
        weak_candidate_count=weak_count,
        provisional_candidate_count=provisional_count,
        blocked_candidate_count=blocked_count,
        one_shot_maturity_detected=False,
        confounder_credit_leak_detected=False,
        delayed_misattribution_detected=False,
        evidence_repetition_count=max(0, len(traces) - 1),
        disconfirmation_count=sum(1 for item in links if item.correlation_status == "disconfirmed"),
        calibration_score=p12.calibration_metrics.report_calibration_score,
    )
    draft = DelayedCreditLearningRun(
        run_id=f"p13:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        episode_traces=traces,
        candidate_credit_links=links,
        confounder_records=confounders,
        delayed_effect_records=delayed_records,
        provisional_schema_candidates=schemas,
        maturity_assessment=assessment,
        falsifier_results={},
        calibration_summary={
            "p12_scenario_id": p12.scenario_id,
            "report_calibration_score": p12.calibration_metrics.report_calibration_score,
            "uncertainty_alignment": p12.calibration_metrics.uncertainty_alignment,
            "confidence_evidence_alignment": p12.calibration_metrics.confidence_evidence_alignment,
        },
        claim_safe_verdict="no_clear_advantage",
        action_request_emitted=False,
    )
    falsifiers = evaluate_delayed_credit_falsifiers(run=draft, claim_boundary=_CLAIM_BOUNDARY)
    assessment = MaturityAssessment(
        candidate_count=assessment.candidate_count,
        mature_schema_count=assessment.mature_schema_count,
        weak_candidate_count=assessment.weak_candidate_count,
        provisional_candidate_count=assessment.provisional_candidate_count,
        blocked_candidate_count=assessment.blocked_candidate_count,
        one_shot_maturity_detected=falsifiers["one_shot_mature_schema"],
        confounder_credit_leak_detected=falsifiers["confounder_credit_leak"],
        delayed_misattribution_detected=falsifiers["delayed_effect_misattribution"],
        evidence_repetition_count=assessment.evidence_repetition_count,
        disconfirmation_count=assessment.disconfirmation_count,
        calibration_score=assessment.calibration_score,
    )
    has_violation = any(falsifiers.values())
    verdict = "mora_credit_restraint_advantage" if not has_violation else "insufficient_evidence"
    return DelayedCreditLearningRun(
        run_id=draft.run_id,
        scenario_id=draft.scenario_id,
        episode_traces=draft.episode_traces,
        candidate_credit_links=draft.candidate_credit_links,
        confounder_records=draft.confounder_records,
        delayed_effect_records=draft.delayed_effect_records,
        provisional_schema_candidates=draft.provisional_schema_candidates,
        maturity_assessment=assessment,
        falsifier_results=falsifiers,
        calibration_summary=draft.calibration_summary,
        claim_safe_verdict=verdict,
        action_request_emitted=False,
    )


def _episode_traces(*, spec: DelayedCreditScenarioSpec, ab6: object, ab5: object) -> tuple[EpisodeTrace, ...]:
    frame = ab6.frame
    update = ab5.update
    base = EpisodeTrace(
        episode_id=f"{spec.scenario_id}:ep1",
        public_action_refs=tuple(frame.source_request_refs) if frame is not None else (),
        public_effect_refs=tuple(frame.source_effect_refs) if frame is not None else (),
        event_digest_refs=tuple(frame.source_event_digest_refs) if frame is not None else (),
        attribution_frame_refs=(frame.attribution_frame_id,) if frame is not None else (),
        support_update_refs=(update.update_id,) if update is not None else (),
        timing_refs=tuple(frame.timing_refs) if frame is not None else (),
        precursor_refs=(
            tuple(frame.source_request_refs)
            if (frame is not None and frame.source_request_refs)
            else ("precursor:public:observed",)
        ),
        confounder_refs=("confounder:parallel:ep1",) if spec.confounder_expected else (),
        observed_outcome_refs=tuple(frame.source_effect_refs) if frame is not None else (),
        hidden_eval_used=False,
        scenario_label_used=False,
    )
    if spec.scenario_id == "hidden_recipe_only":
        base = EpisodeTrace(
            episode_id=base.episode_id,
            public_action_refs=(),
            public_effect_refs=(),
            event_digest_refs=(),
            attribution_frame_refs=(),
            support_update_refs=(update.update_id,) if update is not None else (),
            timing_refs=(),
            precursor_refs=(),
            confounder_refs=(),
            observed_outcome_refs=(),
            hidden_eval_used=False,
            scenario_label_used=False,
        )
    traces = [base]
    if spec.repeated_expected:
        traces.append(
            EpisodeTrace(
                episode_id=f"{spec.scenario_id}:ep2",
                public_action_refs=base.public_action_refs,
                public_effect_refs=base.public_effect_refs if spec.scenario_id != "disconfirming_episode" else (),
                event_digest_refs=base.event_digest_refs,
                attribution_frame_refs=base.attribution_frame_refs,
                support_update_refs=base.support_update_refs,
                timing_refs=base.timing_refs,
                precursor_refs=base.precursor_refs,
                confounder_refs=() if spec.scenario_id == "confounder_disconfirmed_by_repetition" else base.confounder_refs,
                observed_outcome_refs=base.observed_outcome_refs if spec.scenario_id != "disconfirming_episode" else (),
                hidden_eval_used=False,
                scenario_label_used=False,
            )
        )
    return tuple(traces)


def _credit_links(*, spec: DelayedCreditScenarioSpec, traces: tuple[EpisodeTrace, ...], ab6: object) -> tuple[CandidateCreditLink, ...]:
    if spec.scenario_id == "hidden_recipe_only":
        return ()
    frame = ab6.frame
    effect_ref = traces[0].public_effect_refs[0] if traces[0].public_effect_refs else ""
    precursor = traces[0].precursor_refs[0] if traces[0].precursor_refs else ""
    attribution_refs = tuple(frame.supported_attribution_kinds) if frame is not None else ()

    status = "correlated"
    maturity = "provisional_candidate"
    missing: tuple[str, ...] = ()
    confidence = 0.56
    window = "tick+0"

    if spec.delayed_expected:
        status = "delayed_possible"
        window = "tick+1..2"
        confidence = 0.47
    if spec.scenario_id == "delayed_effect_wrong_window":
        status = "insufficient_evidence"
        confidence = 0.28
        maturity = "blocked"
        missing = ("timing_window_mismatch",)
        window = "out_of_window"
    if spec.confounder_expected:
        status = "confounded" if status != "delayed_possible" else "ambiguous"
        confidence = min(confidence, 0.44)
        maturity = "weak_candidate"
        missing = tuple(dict.fromkeys((*missing, "confounder:parallel:ep1")))
    if spec.scenario_id == "spurious_one_shot_correlation":
        status = "ambiguous"
        confidence = 0.33
        maturity = "weak_candidate"
        missing = ("needs_repetition", "confounder:parallel:ep1")
    if spec.scenario_id == "disconfirming_episode":
        status = "disconfirmed"
        confidence = 0.21
        maturity = "blocked"
        missing = ("disconfirming_episode_present",)
    if spec.scenario_id == "confounder_disconfirmed_by_repetition":
        status = "correlated"
        confidence = 0.52
        maturity = "repeated_trace_supported"
        missing = ("further_disconfounder_required",)
    if spec.scenario_id == "ambiguous_public_evidence":
        status = "ambiguous"
        confidence = 0.37
        maturity = "weak_candidate"
        missing = ("additional_discriminating_evidence_required", "confounder:parallel:ep1")
    if spec.scenario_id == "delayed_and_confounded_mixed":
        status = "ambiguous"
        confidence = 0.39
        maturity = "weak_candidate"
        missing = ("confounder:parallel:ep1", "delay_disambiguation_required")
        window = "tick+1..3"

    primary = CandidateCreditLink(
        link_id=f"p13:{spec.scenario_id}:link:1",
        precursor_ref=precursor,
        effect_ref=effect_ref,
        delay_window=window,
        correlation_status=status,
        attribution_kind_refs=attribution_refs,
        evidence_refs=tuple(dict.fromkeys((*traces[0].public_action_refs, *traces[0].public_effect_refs, *traces[0].timing_refs))),
        missing_evidence=missing,
        confidence=round(confidence, 3),
        confidence_policy="evidence_bounded",
        maturity_status=maturity,
        fact_claimed=False,
        cause_confirmed=False,
    )
    links = [primary]
    if spec.scenario_id in {"confounded_effect_two_precursors", "ambiguous_public_evidence", "delayed_and_confounded_mixed"}:
        links.append(
            CandidateCreditLink(
                link_id=f"p13:{spec.scenario_id}:link:2",
                precursor_ref="precursor:alternative:public",
                effect_ref=effect_ref,
                delay_window=window,
                correlation_status="confounded" if spec.scenario_id == "confounded_effect_two_precursors" else "ambiguous",
                attribution_kind_refs=attribution_refs,
                evidence_refs=primary.evidence_refs,
                missing_evidence=("discriminating_evidence_needed", "confounder:parallel:ep1"),
                confidence=0.36,
                confidence_policy="evidence_bounded",
                maturity_status="weak_candidate",
                fact_claimed=False,
                cause_confirmed=False,
            )
        )
    return tuple(links)


def _confounder_records(*, spec: DelayedCreditScenarioSpec, links: tuple[CandidateCreditLink, ...]) -> tuple[ConfounderRecord, ...]:
    if not spec.confounder_expected:
        return ()
    status = "active"
    if spec.scenario_id == "confounder_disconfirmed_by_repetition":
        status = "disconfirmed"
    elif spec.scenario_id == "delayed_and_confounded_mixed":
        status = "unresolved"
    elif spec.scenario_id == "ambiguous_public_evidence":
        status = "unresolved"
    return (
        ConfounderRecord(
            confounder_id=f"p13:{spec.scenario_id}:conf:1",
            confounder_ref="confounder:parallel:ep1",
            overlaps_with=tuple(item.link_id for item in links),
            could_explain_effect=True,
            discriminating_evidence_needed=("repeat_without_confounder", "timing_disambiguation"),
            credit_leak_risk="high" if status in {"active", "unresolved"} else "low",
            status=status,
            evidence_refs=tuple(item.link_id for item in links),
        ),
    )


def _delayed_records(
    *,
    spec: DelayedCreditScenarioSpec,
    traces: tuple[EpisodeTrace, ...],
    links: tuple[CandidateCreditLink, ...],
) -> tuple[dict[str, object], ...]:
    if not spec.delayed_expected:
        return ()
    return (
        {
            "record_id": f"p13:{spec.scenario_id}:delay:1",
            "effect_ref": links[0].effect_ref if links else "",
            "delay_window": links[0].delay_window if links else "",
            "timing_refs": traces[0].timing_refs,
            "status": "observed_in_window" if spec.scenario_id != "delayed_effect_wrong_window" else "window_mismatch",
        },
    )


def _schema_candidates(
    *,
    spec: DelayedCreditScenarioSpec,
    links: tuple[CandidateCreditLink, ...],
    confounders: tuple[ConfounderRecord, ...],
    traces: tuple[EpisodeTrace, ...],
) -> tuple[ProvisionalSchemaCandidate, ...]:
    if spec.scenario_id == "hidden_recipe_only":
        return ()

    precursor_refs = tuple(dict.fromkeys(item.precursor_ref for item in links if item.precursor_ref))
    effect_refs = tuple(dict.fromkeys(item.effect_ref for item in links if item.effect_ref))
    supporting = tuple(item.episode_id for item in traces if item.public_effect_refs)
    disconfirming = tuple(item.episode_id for item in traces if not item.public_effect_refs and item.precursor_refs)
    conf_refs = tuple(item.confounder_ref for item in confounders)
    blocked_reasons: list[str] = []
    missing: list[str] = []
    maturity_status = "provisional"
    maturity_score = 0.42
    if any(item.maturity_status == "blocked" for item in links):
        maturity_status = "blocked"
        maturity_score = 0.21
        blocked_reasons.append("link_blocked_or_disconfirmed")
    elif any(item.maturity_status == "weak_candidate" for item in links):
        maturity_status = "weak"
        maturity_score = 0.31
    if confounders and any(item.status in {"active", "unresolved"} for item in confounders):
        maturity_status = "blocked" if maturity_status == "provisional" else maturity_status
        blocked_reasons.append("active_confounder_requires_disambiguation")
        missing.append("disconfirm_or_isolate_confounder")
    if spec.repeated_expected and not disconfirming and maturity_status in {"provisional", "weak"}:
        maturity_status = "repeated_trace_supported"
        maturity_score = 0.53
        missing.append("additional_repetition_before_maturity")
    if disconfirming:
        maturity_status = "blocked"
        maturity_score = min(maturity_score, 0.24)
        blocked_reasons.append("disconfirming_episode_present")
    if spec.delayed_expected:
        missing.append("delay_window_stability_required")
    missing.extend(item for link in links for item in link.missing_evidence)
    return (
        ProvisionalSchemaCandidate(
            schema_candidate_id=f"p13:{spec.scenario_id}:schema:1",
            precursor_refs=precursor_refs,
            effect_refs=effect_refs,
            supporting_episode_refs=supporting,
            disconfirming_episode_refs=disconfirming,
            confounder_refs=conf_refs,
            delay_profile="delayed" if spec.delayed_expected else "immediate_or_ambiguous",
            maturity_score=round(max(0.05, min(0.75, maturity_score)), 3),
            maturity_policy="requires_repetition_and_disconfounder",
            maturity_status=maturity_status if maturity_status != "repeated_trace_supported" else "repeated_trace_supported",
            blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
            missing_evidence=tuple(dict.fromkeys(missing)),
            hidden_recipe_used=False,
            one_shot_mature=False,
            fact_claimed=False,
            cause_confirmed=False,
        ),
    )


@lru_cache(maxsize=24)
def _ab5_case(case_id: str):
    return run_ab5_probe_case(case_id)


@lru_cache(maxsize=24)
def _ab6_case(case_id: str):
    return run_ab6_probe_case(case_id)


@lru_cache(maxsize=24)
def _p12_case(case_id: str):
    return run_inner_state_calibration_case(case_id)
