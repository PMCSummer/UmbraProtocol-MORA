from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BaselineMetricSummary:
    success_rate: float
    invalid_action_rate: float
    abstention_quality: float
    shortcut_violation_count: int
    provenance_coverage: dict[str, float]
    boundary_integrity: float
    recovery_after_failure: float
    effect_feedback_incorporation: float
    overclaim_rate: float
    matched_information_score: float
    differentiator_score: float
    fsm_equivalence_risk: float


def compute_baseline_metric_summary(
    *,
    scenario_id: str,
    mora_run: Any,
    mora_summary: Any,
    baseline_traces: tuple[Any, ...],
) -> BaselineMetricSummary:
    _ = scenario_id
    _ = mora_run
    effect_statuses: list[str] = []
    invalid_count = 0
    total_attempts = 0
    total_abstentions = 0
    abstentions_with_basis_gap = 0
    shortcut_violations = 0
    overclaim_count = 0
    provenance_keys: set[str] = set()
    provenance_accumulator: dict[str, float] = {}
    recovery_events = 0
    recovery_positive = 0
    feedback_events = 0
    feedback_positive = 0
    fair_baseline_count = 0
    fair_baseline_hidden_usage = 0
    differentiator_points = 0
    differentiator_total = 0
    fsm_similarity_points = 0
    fsm_total = 0

    mora_abstention_count = int(
        getattr(
            mora_summary,
            "abstention_count",
            getattr(mora_summary, "abstention_no_candidate_count", 0),
        )
    )
    mora_world_submissions = int(getattr(mora_summary, "world_submission_count", 0))
    mora_ap01_published = int(getattr(mora_summary, "ap01_published_count", 0))

    for trace in baseline_traces:
        is_fsm = str(getattr(trace, "controller_kind", "")) == "simple_fsm_baseline"
        if str(trace.fairness_class.value if hasattr(trace.fairness_class, "value") else trace.fairness_class) == "fair_public":
            fair_baseline_count += 1
            if trace.hidden_eval_usage:
                fair_baseline_hidden_usage += 1
        for decision_record in trace.decisions:
            total_attempts += 0 if decision_record.decision.abstained else 1
            total_abstentions += 1 if decision_record.decision.abstained else 0
            if decision_record.decision.abstained and any(
                token in decision_record.decision.reason_codes
                for token in ("no_drive_basis", "no_action_surface", "insufficient_basis")
            ):
                abstentions_with_basis_gap += 1
            if decision_record.effect_status is not None:
                effect_statuses.append(str(decision_record.effect_status))
            if decision_record.invalid_action:
                invalid_count += 1
            if decision_record.hidden_eval_usage or decision_record.ap01_bypassed:
                shortcut_violations += 1
            if decision_record.decision.expected_boundary_violation:
                overclaim_count += 1
            provenance = decision_record.provenance_coverage
            for key, value in provenance.items():
                provenance_keys.add(key)
                provenance_accumulator[key] = provenance_accumulator.get(key, 0.0) + float(value)
            if decision_record.recovery_marker is not None:
                recovery_events += 1
                if "blind_retry" not in decision_record.recovery_marker:
                    recovery_positive += 1
            if decision_record.decision.used_previous_effect:
                feedback_events += 1
                if not decision_record.decision.abstained:
                    feedback_positive += 1
            if is_fsm:
                fsm_total += 1
                fsm_acted = not decision_record.decision.abstained
                mora_acted = mora_world_submissions > 0 or mora_ap01_published > 0
                if fsm_acted == mora_acted:
                    fsm_similarity_points += 1

    success_count = sum(1 for status in effect_statuses if status == "succeeded")
    success_den = len(effect_statuses) if effect_statuses else max(1, total_attempts)
    success_rate = success_count / success_den
    invalid_action_rate = (invalid_count / max(1, total_attempts))
    abstention_quality = abstentions_with_basis_gap / max(1, total_abstentions)
    boundary_integrity = 1.0 - min(1.0, shortcut_violations / max(1, total_attempts + total_abstentions))
    recovery_after_failure = recovery_positive / max(1, recovery_events)
    effect_feedback_incorporation = feedback_positive / max(1, feedback_events)
    overclaim_rate = overclaim_count / max(1, total_attempts + total_abstentions)
    matched_information_score = 1.0 - (fair_baseline_hidden_usage / max(1, fair_baseline_count))

    if provenance_keys:
        count_records = max(1, sum(len(trace.decisions) for trace in baseline_traces))
        provenance_coverage = {
            key: provenance_accumulator.get(key, 0.0) / count_records for key in sorted(provenance_keys)
        }
    else:
        provenance_coverage = {}

    # Differentiator score rewards MORA restraint and provenance when baselines
    # take simplistic actions on basis-missing scenarios.
    for trace in baseline_traces:
        differentiator_total += 1
        baseline_acted = any(not rec.decision.abstained for rec in trace.decisions)
        if mora_abstention_count > 0 and baseline_acted:
            differentiator_points += 1
    differentiator_score = differentiator_points / max(1, differentiator_total)
    fsm_equivalence_risk = fsm_similarity_points / max(1, fsm_total)

    return BaselineMetricSummary(
        success_rate=success_rate,
        invalid_action_rate=invalid_action_rate,
        abstention_quality=abstention_quality,
        shortcut_violation_count=shortcut_violations,
        provenance_coverage=provenance_coverage,
        boundary_integrity=boundary_integrity,
        recovery_after_failure=recovery_after_failure,
        effect_feedback_incorporation=effect_feedback_incorporation,
        overclaim_rate=overclaim_rate,
        matched_information_score=matched_information_score,
        differentiator_score=differentiator_score,
        fsm_equivalence_risk=fsm_equivalence_risk,
    )
