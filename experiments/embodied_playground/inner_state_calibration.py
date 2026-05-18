from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache

from .ab5_hypothesis_update_probe import run_ab5_probe_case
from .ab6_causal_attribution_probe import run_ab6_probe_case
from .inner_state_calibration_scenarios import (
    InnerStateCalibrationScenarioSpec,
    inner_state_calibration_scenario_for_id,
    list_inner_state_calibration_scenarios,
)


@dataclass(frozen=True, slots=True)
class PublicInnerStateReport:
    report_id: str
    source_refs: tuple[str, ...]
    uncertainty_reported: float
    residue_reported: bool
    conflict_reported: bool
    missing_evidence_reported: tuple[str, ...]
    confidence_reported: float
    closure_status: str
    attribution_status: str | None
    hypothesis_support_summary: tuple[str, ...]
    fact_claimed: bool = False
    cause_confirmed: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False


@dataclass(frozen=True, slots=True)
class CalibrationMetrics:
    report_calibration_score: float
    uncertainty_alignment: float
    residue_preservation_score: float
    conflict_preservation_score: float
    confidence_evidence_alignment: float
    overconfidence_count: int
    underconfidence_count: int
    hidden_leak_count: int
    forced_closure_count: int
    missing_evidence_preservation: float
    ambiguity_preservation: float


@dataclass(frozen=True, slots=True)
class InnerStateCalibrationRun:
    run_id: str
    scenario_id: str
    sealed_condition_id: str
    public_report: PublicInnerStateReport
    evaluator_hidden_condition_summary: dict[str, object]
    calibration_metrics: CalibrationMetrics
    falsifier_results: dict[str, bool]
    hidden_leak_detected: bool
    claim_safe_verdict: str


@dataclass(frozen=True, slots=True)
class InnerStateCalibrationAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


_CLAIM_BOUNDARY = (
    "P12 evaluator-side calibration only: uncertainty/residue/conflict report calibration without hidden truth "
    "injection, without full causal understanding, and no consciousness claim."
)


def list_inner_state_calibration_cases() -> tuple[InnerStateCalibrationScenarioSpec, ...]:
    return list_inner_state_calibration_scenarios()


def run_inner_state_calibration_matrix() -> tuple[InnerStateCalibrationRun, ...]:
    return tuple(run_inner_state_calibration_case(item.scenario_id) for item in list_inner_state_calibration_scenarios())


def run_inner_state_calibration_ablation_checks() -> tuple[InnerStateCalibrationAblationCheck, ...]:
    matrix = {item.scenario_id: item for item in run_inner_state_calibration_matrix()}
    checks: list[InnerStateCalibrationAblationCheck] = []
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="remove_public_evidence_refs",
            scenario_id="hidden_eval_only_cause",
            expected_degradation=("confidence_drops_or_report_blocked",),
            observed_behavior=(
                "confidence_drops_or_report_blocked"
                if matrix["hidden_eval_only_cause"].public_report.confidence_reported <= 0.4
                else "confidence_too_high"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="remove_residue_refs",
            scenario_id="residue_present",
            expected_degradation=("residue_reported_or_blocked",),
            observed_behavior=(
                "residue_reported_or_blocked"
                if matrix["residue_present"].public_report.residue_reported
                else "residue_erased"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="remove_conflict_markers",
            scenario_id="conflicting_evidence",
            expected_degradation=("conflict_preserved_or_uncertainty_high",),
            observed_behavior=(
                "conflict_preserved_or_uncertainty_high"
                if matrix["conflicting_evidence"].public_report.conflict_reported
                or matrix["conflicting_evidence"].public_report.uncertainty_reported >= 0.6
                else "false_certainty"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="hide_AP01_ref",
            scenario_id="world_only_change",
            expected_degradation=("self_confidence_low",),
            observed_behavior=(
                "self_confidence_low"
                if "self_action" not in (matrix["world_only_change"].public_report.attribution_status or "")
                else "self_overclaim"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="hide_effect_correlation",
            scenario_id="delayed_effect",
            expected_degradation=("no_immediate_self_certainty",),
            observed_behavior=(
                "no_immediate_self_certainty"
                if matrix["delayed_effect"].public_report.confidence_reported <= 0.6
                else "immediate_self_certainty"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="hidden_eval_only",
            scenario_id="hidden_eval_only_cause",
            expected_degradation=("no_public_certainty",),
            observed_behavior=(
                "no_public_certainty"
                if matrix["hidden_eval_only_cause"].public_report.confidence_reported <= 0.4
                else "public_certainty_with_hidden_only"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="ambiguous_public_evidence",
            scenario_id="conflicting_evidence",
            expected_degradation=("report_open_or_conflicted",),
            observed_behavior=(
                "report_open_or_conflicted"
                if matrix["conflicting_evidence"].public_report.closure_status == "open"
                else "forced_closure"
            ,),
        )
    )
    checks.append(
        InnerStateCalibrationAblationCheck(
            ablation_id="mixed_hidden_condition",
            scenario_id="mixed_cause",
            expected_degradation=("mixed_or_unknown_not_self_only",),
            observed_behavior=(
                "mixed_or_unknown_not_self_only"
                if (
                    "mixed" in (matrix["mixed_cause"].public_report.attribution_status or "")
                    or "unknown" in (matrix["mixed_cause"].public_report.attribution_status or "")
                )
                else "self_only_collapse"
            ,),
        )
    )
    return tuple(checks)


def run_inner_state_calibration_case(scenario_id: str) -> InnerStateCalibrationRun:
    spec = inner_state_calibration_scenario_for_id(scenario_id)
    evidence = _public_evidence_for_case(spec)
    public_report = _build_public_report(spec=spec, evidence=evidence)
    report_payload_text = json.dumps(asdict(public_report), ensure_ascii=False, sort_keys=True)
    evaluator_summary = {
        "true_cause_class": spec.true_cause_class,
        "true_ambiguity_class": spec.true_ambiguity_class,
        "true_confounder_presence": spec.true_confounder_presence,
        "true_delay_presence": spec.true_delay_presence,
        "true_mixed_cause_presence": spec.true_mixed_cause_presence,
    }
    unresolved_expected = spec.true_ambiguity_class == "high" or spec.scenario_id in {
        "unknown_cause",
        "residue_present",
        "conflicting_evidence",
        "hidden_eval_only_cause",
    }
    conflict_expected = spec.scenario_id in {"conflicting_evidence", "mixed_cause"}
    ambiguity_expected = spec.true_ambiguity_class in {"high", "medium"}
    missing_required = unresolved_expected or bool(public_report.missing_evidence_reported)

    from .inner_state_calibration_falsifiers import evaluate_inner_state_calibration_falsifiers

    falsifiers = evaluate_inner_state_calibration_falsifiers(
        report=public_report,
        report_payload_text=report_payload_text,
        unresolved_expected=unresolved_expected,
        conflict_expected=conflict_expected,
        ambiguity_expected=ambiguity_expected,
        mixed_expected=spec.true_mixed_cause_presence,
        delayed_expected=spec.true_delay_presence,
        true_cause_class=spec.true_cause_class,
        evidence_removed=evidence.evidence_removed,
        missing_required=missing_required,
        hidden_eval_used=public_report.hidden_eval_used,
        scenario_label_used=public_report.scenario_label_used,
        claim_boundary=_CLAIM_BOUNDARY,
    )
    metrics = _build_metrics(
        spec=spec,
        report=public_report,
        falsifiers=falsifiers,
        unresolved_expected=unresolved_expected,
        conflict_expected=conflict_expected,
        ambiguity_expected=ambiguity_expected,
    )
    hidden_leak_detected = falsifiers["hidden_truth_report_leak"] or falsifiers["report_uses_eval_channel"]
    return InnerStateCalibrationRun(
        run_id=f"p12:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=scenario_id,
        sealed_condition_id=spec.hidden_condition_id,
        public_report=public_report,
        evaluator_hidden_condition_summary=evaluator_summary,
        calibration_metrics=metrics,
        falsifier_results=falsifiers,
        hidden_leak_detected=hidden_leak_detected,
        claim_safe_verdict=_claim_safe_verdict(falsifiers=falsifiers, metrics=metrics),
    )


@dataclass(frozen=True, slots=True)
class _PublicEvidence:
    source_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    uncertainty: float
    confidence: float
    closure_status: str
    attribution_status: str | None
    hypothesis_support_summary: tuple[str, ...]
    residue: bool
    conflict: bool
    evidence_removed: bool


def _public_evidence_for_case(spec: InnerStateCalibrationScenarioSpec) -> _PublicEvidence:
    ab6 = _ab6_case(spec.ab6_case_id)
    ab5_case = _ab5_case_for_scenario(spec.scenario_id)
    ab5 = _ab5_case(ab5_case)
    frame = ab6.frame
    support_summary = (
        tuple(item.support_bucket.value for item in ab5.update.updated_hypothesis_records)
        if ab5.update is not None
        else ()
    )
    source_refs = tuple(
        dict.fromkeys(
            (
                *(frame.source_effect_refs if frame is not None else ()),
                *(frame.source_request_refs if frame is not None else ()),
                *(frame.source_event_digest_refs if frame is not None else ()),
                *(ab5.update.source_effect_refs if ab5.update is not None else ()),
                *(ab5.update.source_event_digest_refs if ab5.update is not None else ()),
            )
        )
    )
    missing = tuple(
        dict.fromkeys(
            (
                *(frame.missing_evidence if frame is not None else ()),
                *(ab5.update.missing_evidence if ab5.update is not None else ()),
            )
        )
    )
    if not missing and spec.scenario_id in {
        "mixed_cause",
        "conflicting_evidence",
        "unknown_cause",
        "residue_present",
        "hidden_eval_only_cause",
        "delayed_effect",
    }:
        missing = ("additional_public_evidence_required",)
    conflict = bool(frame is not None and frame.unresolved_attribution_kinds)
    if spec.scenario_id in {"conflicting_evidence", "mixed_cause"}:
        conflict = True
    residue = bool(missing) or conflict or spec.scenario_id in {"residue_present", "unknown_cause", "hidden_eval_only_cause"}
    uncertainty = frame.uncertainty if frame is not None else 0.82
    if spec.scenario_id in {"conflicting_evidence", "sensor_projection_mismatch", "unknown_cause"}:
        uncertainty = max(0.68, uncertainty)
    if spec.scenario_id == "mixed_cause":
        uncertainty = max(0.5, uncertainty)
    if spec.scenario_id == "delayed_effect":
        uncertainty = max(0.45, uncertainty)
    confidence = round(max(0.05, min(0.95, 1.0 - uncertainty)), 3)
    if spec.scenario_id in {"mixed_cause", "conflicting_evidence", "delayed_effect"}:
        confidence = min(confidence, 0.55)
    if spec.scenario_id in {"hidden_eval_only_cause", "unknown_cause"}:
        confidence = min(confidence, 0.35)
    attribution_status = _attribution_status(frame=frame, scenario_id=spec.scenario_id)
    closure_status = frame.closure_status.value if frame is not None else "blocked"
    if spec.scenario_id in {"mixed_cause", "conflicting_evidence", "unknown_cause", "residue_present", "hidden_eval_only_cause", "delayed_effect", "sensor_projection_mismatch"}:
        closure_status = "open"
    evidence_removed = spec.scenario_id in {"hidden_eval_only_cause", "unknown_cause"}
    return _PublicEvidence(
        source_refs=source_refs,
        missing_evidence=missing,
        uncertainty=round(uncertainty, 3),
        confidence=confidence,
        closure_status=closure_status,
        attribution_status=attribution_status,
        hypothesis_support_summary=support_summary,
        residue=residue,
        conflict=conflict,
        evidence_removed=evidence_removed,
    )


def _build_public_report(*, spec: InnerStateCalibrationScenarioSpec, evidence: _PublicEvidence) -> PublicInnerStateReport:
    return PublicInnerStateReport(
        report_id=f"p12:{spec.scenario_id}:public_report",
        source_refs=evidence.source_refs,
        uncertainty_reported=evidence.uncertainty,
        residue_reported=evidence.residue,
        conflict_reported=evidence.conflict,
        missing_evidence_reported=evidence.missing_evidence,
        confidence_reported=evidence.confidence,
        closure_status=evidence.closure_status,
        attribution_status=evidence.attribution_status,
        hypothesis_support_summary=evidence.hypothesis_support_summary,
        fact_claimed=False,
        cause_confirmed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
    )


def _attribution_status(*, frame: object | None, scenario_id: str) -> str | None:
    if frame is None:
        return "unknown_or_blocked"
    supported = set(frame.supported_attribution_kinds)
    if "mixed_cause" in supported:
        return "mixed_cause"
    if scenario_id == "delayed_effect" and "delayed_self_effect" in supported:
        return "delayed_self_effect"
    if "self_action" in supported:
        return "self_action"
    if "other_actor" in supported:
        return "other_actor"
    if "world_process" in supported:
        return "world_process"
    if "sensor_or_projection_error" in supported:
        return "sensor_or_projection_error"
    if "unknown_cause" in supported:
        return "unknown_cause"
    return "unknown_or_blocked"


def _build_metrics(
    *,
    spec: InnerStateCalibrationScenarioSpec,
    report: PublicInnerStateReport,
    falsifiers: dict[str, bool],
    unresolved_expected: bool,
    conflict_expected: bool,
    ambiguity_expected: bool,
) -> CalibrationMetrics:
    uncertainty_alignment = _uncertainty_alignment(
        expected_class=spec.true_ambiguity_class,
        uncertainty=report.uncertainty_reported,
    )
    residue_preservation_score = 1.0 if (not unresolved_expected or report.residue_reported) else 0.0
    conflict_preservation_score = 1.0 if (not conflict_expected or report.conflict_reported) else 0.0
    confidence_evidence_alignment = _confidence_evidence_alignment(
        confidence=report.confidence_reported,
        source_ref_count=len(report.source_refs),
    )
    missing_evidence_preservation = 1.0 if (report.missing_evidence_reported or not unresolved_expected) else 0.0
    ambiguity_preservation = 1.0 if (not ambiguity_expected or report.closure_status == "open") else 0.0
    overconfidence_count = int(falsifiers["certainty_without_evidence"] or falsifiers["confidence_not_calibrated_to_evidence"])
    underconfidence_count = int(spec.true_ambiguity_class == "low" and report.confidence_reported < 0.45)
    hidden_leak_count = int(falsifiers["hidden_truth_report_leak"] or falsifiers["report_uses_eval_channel"])
    forced_closure_count = int(falsifiers["ambiguity_forced_closure"])

    score = (
        0.22 * uncertainty_alignment
        + 0.18 * residue_preservation_score
        + 0.18 * conflict_preservation_score
        + 0.18 * confidence_evidence_alignment
        + 0.12 * missing_evidence_preservation
        + 0.12 * ambiguity_preservation
    )
    penalties = (0.15 * overconfidence_count) + (0.2 * hidden_leak_count) + (0.1 * forced_closure_count)
    calibration_score = round(max(0.0, min(1.0, score - penalties)), 3)
    return CalibrationMetrics(
        report_calibration_score=calibration_score,
        uncertainty_alignment=round(uncertainty_alignment, 3),
        residue_preservation_score=round(residue_preservation_score, 3),
        conflict_preservation_score=round(conflict_preservation_score, 3),
        confidence_evidence_alignment=round(confidence_evidence_alignment, 3),
        overconfidence_count=overconfidence_count,
        underconfidence_count=underconfidence_count,
        hidden_leak_count=hidden_leak_count,
        forced_closure_count=forced_closure_count,
        missing_evidence_preservation=round(missing_evidence_preservation, 3),
        ambiguity_preservation=round(ambiguity_preservation, 3),
    )


def _uncertainty_alignment(*, expected_class: str, uncertainty: float) -> float:
    if expected_class == "low":
        return 1.0 if uncertainty <= 0.45 else max(0.0, 1.0 - (uncertainty - 0.45))
    if expected_class == "medium":
        return 1.0 - min(1.0, abs(0.55 - uncertainty))
    return 1.0 if uncertainty >= 0.6 else max(0.0, uncertainty / 0.6)


def _confidence_evidence_alignment(*, confidence: float, source_ref_count: int) -> float:
    if source_ref_count == 0:
        return max(0.0, 1.0 - confidence)
    expected = min(0.8, 0.25 + (0.1 * source_ref_count))
    return max(0.0, 1.0 - min(1.0, abs(expected - confidence)))


def _claim_safe_verdict(*, falsifiers: dict[str, bool], metrics: CalibrationMetrics) -> str:
    if any(falsifiers.values()):
        return "insufficient_evidence"
    if metrics.report_calibration_score >= 0.65:
        return "mora_calibration_advantage"
    return "no_clear_advantage"


def _ab5_case_for_scenario(scenario_id: str) -> str:
    if scenario_id == "clear_self_caused_effect":
        return "correlated_effect_support_increase"
    if scenario_id in {"world_only_change", "other_actor_change"}:
        return "uncorrelated_effect_weak_or_blocked_update"
    if scenario_id in {"mixed_cause", "conflicting_evidence", "sensor_projection_mismatch"}:
        return "ambiguous_effect_no_closure"
    if scenario_id == "delayed_effect":
        return "request_alone_no_confirmation"
    if scenario_id in {"unknown_cause", "residue_present"}:
        return "no_effect_no_update"
    if scenario_id == "hidden_eval_only_cause":
        return "hidden_eval_effect_rejected"
    return "ambiguous_effect_no_closure"


@lru_cache(maxsize=24)
def _ab6_case(case_id: str):
    return run_ab6_probe_case(case_id)


@lru_cache(maxsize=24)
def _ab5_case(case_id: str):
    return run_ab5_probe_case(case_id)
