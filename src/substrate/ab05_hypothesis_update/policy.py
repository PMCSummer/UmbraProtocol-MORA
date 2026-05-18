from __future__ import annotations

from dataclasses import replace

from substrate.ab03_hypothesis_frontier import AB3ClosureStatus, AB3SupportBucket

from .models import (
    AB5DeltaKind,
    AB5HypothesisSupportDelta,
    AB5HypothesisUpdateInput,
    AB5HypothesisUpdateResult,
    AB5ScopeMarker,
    AB5UpdateEnvelope,
    AB5UpdatedHypothesisRecord,
    as_ab3_record,
)
from .telemetry import build_ab5_telemetry

_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "test_label",
    "hidden",
    "eval",
    "private",
)
_WORLD_SPECIFIC_TOKENS: tuple[str, ...] = (
    "water",
    "flask",
    "ore",
    "filter",
    "station",
    "recipe",
    "minecraft",
)


def build_ab5_hypothesis_update(candidate_input: AB5HypothesisUpdateInput) -> AB5UpdateEnvelope:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    update: AB5HypothesisUpdateResult | None = None
    support_deltas: tuple[AB5HypothesisSupportDelta, ...] = ()
    closure_allowed = False
    if not unsafe_reasons:
        update, support_deltas, closure_allowed = _build_update(candidate_input)
    telemetry = build_ab5_telemetry(
        candidate_input=candidate_input,
        support_deltas=support_deltas,
        unsafe_basis_count=len(unsafe_reasons),
        closure_allowed=closure_allowed,
    )
    scope_marker = AB5ScopeMarker(
        scope="ab05_hypothesis_update_from_effects",
        hypothesis_support_update_only=True,
        no_hypothesis_generation_authority=True,
        no_epistemic_action_selection_authority=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_execution_authority=True,
        no_ownership_closure_authority=True,
        reason="ab5 updates bounded hypothesis support from correlated public effects only; no fact/action closure",
    )
    if unsafe_reasons:
        reason_codes = tuple(unsafe_reasons)
    elif update is None:
        reason_codes = ("no_support_update_emitted",)
    else:
        reason_codes = ("support_update_emitted",)
    return AB5UpdateEnvelope(
        tick_ref=candidate_input.tick_ref,
        update=update,
        telemetry=telemetry,
        scope_marker=scope_marker,
        reason_codes=reason_codes,
        source_lineage=("ab05_hypothesis_update.policy",),
    )


def _build_update(
    candidate_input: AB5HypothesisUpdateInput,
) -> tuple[AB5HypothesisUpdateResult | None, tuple[AB5HypothesisSupportDelta, ...], bool]:
    prior = candidate_input.prior_frontier
    if prior is None or not prior.hypotheses:
        return None, (), False

    source_effect_refs = tuple(candidate_input.source_effect_refs)
    source_event_refs = tuple(item.event_id for item in candidate_input.source_event_digests)
    evidence_refs = tuple(
        dict.fromkeys(
            (
                *candidate_input.source_refs,
                *candidate_input.source_observation_refs,
                *candidate_input.epistemic_basis_refs,
                *candidate_input.source_request_refs,
                *source_effect_refs,
                *source_event_refs,
            )
        )
    )
    if not source_effect_refs and not source_event_refs:
        reason = "request_without_effect_not_confirmation" if candidate_input.source_request_refs else "no_effect_evidence"
        update = AB5HypothesisUpdateResult(
            update_id=f"ab5:{candidate_input.tick_ref}:blocked",
            prior_frontier_ref=prior.frontier_id,
            source_effect_refs=source_effect_refs,
            source_event_digest_refs=source_event_refs,
            source_request_refs=tuple(candidate_input.source_request_refs),
            epistemic_basis_refs=tuple(candidate_input.epistemic_basis_refs),
            updated_hypothesis_records=(),
            support_deltas=(),
            disconfirmed_hypothesis_refs=(),
            strengthened_hypothesis_refs=(),
            weakened_hypothesis_refs=(),
            unresolved_hypothesis_refs=tuple(item.hypothesis_id for item in prior.hypotheses),
            ambiguous_evidence_refs=(),
            missing_evidence=tuple(prior.missing_evidence),
            closure_allowed=False,
            closure_blocked_reason=reason,
            closure_policy="ab5_non_fact_effect_update_v1",
            updated_frontier_snapshot=None,
            fact_claimed=False,
            cause_confirmed=False,
            selected_fact_hypothesis_id=None,
            hidden_eval_used=False,
            scenario_label_used=False,
            action_request_emitted=False,
            world_submission_emitted=False,
        )
        return update, (), False

    support_refs = set(candidate_input.supporting_hypothesis_refs)
    disconfirm_refs = set(candidate_input.disconfirming_hypothesis_refs)
    deltas: list[AB5HypothesisSupportDelta] = []
    updated_records: list[AB5UpdatedHypothesisRecord] = []
    strengthened: list[str] = []
    weakened: list[str] = []
    disconfirmed: list[str] = []
    unresolved: list[str] = []

    strong_update_allowed = candidate_input.effect_correlated and bool(source_effect_refs or source_event_refs)
    for hypothesis in prior.hypotheses:
        delta = _delta_for_hypothesis(
            hypothesis=hypothesis,
            support_refs=support_refs,
            disconfirm_refs=disconfirm_refs,
            strong_update_allowed=strong_update_allowed,
            ambiguous=candidate_input.ambiguous_evidence,
            has_support_signal=bool(support_refs),
            evidence_refs=evidence_refs,
            effect_refs=source_effect_refs,
            event_refs=source_event_refs,
        )
        deltas.append(delta)
        updated_records.append(
            AB5UpdatedHypothesisRecord(
                hypothesis_ref=hypothesis.hypothesis_id,
                hypothesis_kind=hypothesis.hypothesis_kind,
                previous_support_bucket=hypothesis.support_bucket,
                support_bucket=delta.new_support_bucket,
                confidence=_updated_confidence(hypothesis.confidence, delta.delta_kind),
                confidence_policy="evidence_bounded",
                evidence_refs=delta.evidence_refs,
                missing_evidence=tuple(hypothesis.missing_evidence),
                expected_observations=tuple(hypothesis.expected_observations),
                possible_tests=tuple(hypothesis.possible_tests),
                explains_what=tuple(hypothesis.explains_what),
                does_not_explain=tuple(hypothesis.does_not_explain),
                reason_codes=delta.reason_codes,
                fact_status="not_fact",
                cause_confirmed=False,
            )
        )
        if delta.delta_kind is AB5DeltaKind.INCREASE:
            strengthened.append(hypothesis.hypothesis_id)
        elif delta.delta_kind is AB5DeltaKind.DISCONFIRM:
            disconfirmed.append(hypothesis.hypothesis_id)
        elif delta.delta_kind is AB5DeltaKind.DECREASE:
            weakened.append(hypothesis.hypothesis_id)
        if delta.delta_kind in {AB5DeltaKind.UNRESOLVED, AB5DeltaKind.BLOCKED, AB5DeltaKind.UNCHANGED}:
            unresolved.append(hypothesis.hypothesis_id)

    ambiguous_refs = tuple(prior.unresolved_conflicts) if candidate_input.ambiguous_evidence else ()
    closure_allowed = _closure_allowed(
        prior_hypothesis_count=len(prior.hypotheses),
        strengthened=tuple(strengthened),
        disconfirmed=tuple(disconfirmed),
        ambiguous=bool(ambiguous_refs),
        effect_correlated=candidate_input.effect_correlated,
        missing_evidence=tuple(prior.missing_evidence),
    )
    closure_blocked_reason = None if closure_allowed else _closure_blocked_reason(
        candidate_input=candidate_input,
        ambiguous=bool(ambiguous_refs),
    )

    updated_frontier = _updated_frontier_snapshot(
        prior=prior,
        updated_records=tuple(updated_records),
        closure_allowed=closure_allowed,
        ambiguous=bool(ambiguous_refs),
    )
    update = AB5HypothesisUpdateResult(
        update_id=f"ab5:{candidate_input.tick_ref}:update",
        prior_frontier_ref=prior.frontier_id,
        source_effect_refs=source_effect_refs,
        source_event_digest_refs=source_event_refs,
        source_request_refs=tuple(candidate_input.source_request_refs),
        epistemic_basis_refs=tuple(candidate_input.epistemic_basis_refs),
        updated_hypothesis_records=tuple(updated_records),
        support_deltas=tuple(deltas),
        disconfirmed_hypothesis_refs=tuple(disconfirmed),
        strengthened_hypothesis_refs=tuple(strengthened),
        weakened_hypothesis_refs=tuple(weakened),
        unresolved_hypothesis_refs=tuple(dict.fromkeys(unresolved)),
        ambiguous_evidence_refs=ambiguous_refs,
        missing_evidence=tuple(prior.missing_evidence),
        closure_allowed=closure_allowed,
        closure_blocked_reason=closure_blocked_reason,
        closure_policy="ab5_non_fact_effect_update_v1",
        updated_frontier_snapshot=updated_frontier,
        fact_claimed=False,
        cause_confirmed=False,
        selected_fact_hypothesis_id=None,
        hidden_eval_used=False,
        scenario_label_used=False,
        action_request_emitted=False,
        world_submission_emitted=False,
    )
    return update, tuple(deltas), closure_allowed


def _delta_for_hypothesis(
    *,
    hypothesis,
    support_refs: set[str],
    disconfirm_refs: set[str],
    strong_update_allowed: bool,
    ambiguous: bool,
    has_support_signal: bool,
    evidence_refs: tuple[str, ...],
    effect_refs: tuple[str, ...],
    event_refs: tuple[str, ...],
) -> AB5HypothesisSupportDelta:
    prev_bucket = hypothesis.support_bucket
    matched_expected: tuple[str, ...] = ()
    contradicted_expected: tuple[str, ...] = ()
    missing_expected: tuple[str, ...] = tuple(hypothesis.expected_observations)
    reason_codes: list[str] = []

    if ambiguous:
        delta_kind = AB5DeltaKind.UNRESOLVED
        new_bucket = prev_bucket
        reason_codes.append("ambiguous_evidence_keeps_open")
    elif hypothesis.hypothesis_id in disconfirm_refs and strong_update_allowed:
        delta_kind = AB5DeltaKind.DISCONFIRM
        new_bucket = AB3SupportBucket.CONTRADICTED
        contradicted_expected = tuple(hypothesis.expected_observations)
        missing_expected = ()
        reason_codes.append("disconfirming_effect_observed")
    elif hypothesis.hypothesis_id in support_refs and strong_update_allowed:
        delta_kind = AB5DeltaKind.INCREASE
        new_bucket = _increase_bucket(prev_bucket)
        matched_expected = tuple(hypothesis.expected_observations)
        missing_expected = ()
        reason_codes.append("correlated_effect_matches_expected_observation")
    elif hypothesis.hypothesis_id in support_refs and not strong_update_allowed:
        delta_kind = AB5DeltaKind.BLOCKED
        new_bucket = prev_bucket
        reason_codes.append("uncorrelated_or_missing_effect_blocks_support_increase")
    elif has_support_signal and strong_update_allowed:
        delta_kind = AB5DeltaKind.DECREASE
        new_bucket = _decrease_bucket(prev_bucket)
        reason_codes.append("alternative_hypothesis_supported")
    else:
        delta_kind = AB5DeltaKind.UNCHANGED
        new_bucket = prev_bucket
        reason_codes.append("no_discriminating_effect_for_hypothesis")

    confidence_delta = _confidence_delta(prev_bucket=prev_bucket, new_bucket=new_bucket, delta_kind=delta_kind)
    return AB5HypothesisSupportDelta(
        hypothesis_ref=hypothesis.hypothesis_id,
        previous_support_bucket=prev_bucket,
        new_support_bucket=new_bucket,
        delta_kind=delta_kind,
        evidence_refs=evidence_refs if evidence_refs else ("insufficient_evidence_refs",),
        effect_refs=effect_refs,
        event_refs=event_refs,
        matched_expected_observations=matched_expected,
        contradicted_expected_observations=contradicted_expected,
        missing_expected_observations=missing_expected,
        reason_codes=tuple(reason_codes),
        confidence_delta=confidence_delta,
        confidence_policy="evidence_bounded",
        fact_status="not_fact",
    )


def _increase_bucket(bucket: AB3SupportBucket) -> AB3SupportBucket:
    order = (
        AB3SupportBucket.UNSUPPORTED,
        AB3SupportBucket.WEAK,
        AB3SupportBucket.PROVISIONAL,
        AB3SupportBucket.SUPPORTED,
    )
    if bucket is AB3SupportBucket.CONTRADICTED:
        return AB3SupportBucket.WEAK
    idx = min(len(order) - 1, order.index(bucket) + 1 if bucket in order else 1)
    return order[idx]


def _decrease_bucket(bucket: AB3SupportBucket) -> AB3SupportBucket:
    order = (
        AB3SupportBucket.UNSUPPORTED,
        AB3SupportBucket.WEAK,
        AB3SupportBucket.PROVISIONAL,
        AB3SupportBucket.SUPPORTED,
    )
    if bucket is AB3SupportBucket.CONTRADICTED:
        return AB3SupportBucket.CONTRADICTED
    idx = max(0, order.index(bucket) - 1 if bucket in order else 0)
    return order[idx]


def _confidence_delta(*, prev_bucket: AB3SupportBucket, new_bucket: AB3SupportBucket, delta_kind: AB5DeltaKind) -> float:
    if delta_kind is AB5DeltaKind.DISCONFIRM:
        return -0.4
    score = {
        AB3SupportBucket.CONTRADICTED: -0.8,
        AB3SupportBucket.UNSUPPORTED: 0.1,
        AB3SupportBucket.WEAK: 0.3,
        AB3SupportBucket.PROVISIONAL: 0.55,
        AB3SupportBucket.SUPPORTED: 0.75,
    }
    return round(score[new_bucket] - score[prev_bucket], 3)


def _updated_confidence(current: float, delta_kind: AB5DeltaKind) -> float:
    delta = {
        AB5DeltaKind.INCREASE: 0.12,
        AB5DeltaKind.DECREASE: -0.12,
        AB5DeltaKind.DISCONFIRM: -0.35,
        AB5DeltaKind.UNCHANGED: 0.0,
        AB5DeltaKind.UNRESOLVED: -0.05,
        AB5DeltaKind.BLOCKED: -0.08,
    }[delta_kind]
    return round(max(0.05, min(0.9, current + delta)), 3)


def _closure_allowed(
    *,
    prior_hypothesis_count: int,
    strengthened: tuple[str, ...],
    disconfirmed: tuple[str, ...],
    ambiguous: bool,
    effect_correlated: bool,
    missing_evidence: tuple[str, ...],
) -> bool:
    if ambiguous or not effect_correlated or missing_evidence:
        return False
    if len(strengthened) != 1:
        return False
    return len(disconfirmed) >= max(1, prior_hypothesis_count - 1)


def _closure_blocked_reason(*, candidate_input: AB5HypothesisUpdateInput, ambiguous: bool) -> str:
    if ambiguous:
        return "ambiguous_evidence_requires_open_frontier"
    if candidate_input.source_request_refs and not candidate_input.source_effect_refs and not candidate_input.source_event_digests:
        return "request_without_effect_not_confirmation"
    if not candidate_input.effect_correlated:
        return "uncorrelated_effect_blocks_strong_update"
    return "non_fact_update_policy_requires_downstream_resolution"


def _updated_frontier_snapshot(
    *,
    prior,
    updated_records: tuple[AB5UpdatedHypothesisRecord, ...],
    closure_allowed: bool,
    ambiguous: bool,
):
    converted = tuple(as_ab3_record(record, seed_ref=record.hypothesis_ref) for record in updated_records)
    if not converted:
        return None
    closure_status = AB3ClosureStatus.PROVISIONALLY_RANKED if closure_allowed else AB3ClosureStatus.OPEN
    if ambiguous:
        closure_status = AB3ClosureStatus.OPEN
    confidence_distribution = {
        "supported": round(sum(1 for item in converted if item.support_bucket is AB3SupportBucket.SUPPORTED) / len(converted), 3),
        "provisional": round(sum(1 for item in converted if item.support_bucket is AB3SupportBucket.PROVISIONAL) / len(converted), 3),
        "weak": round(sum(1 for item in converted if item.support_bucket is AB3SupportBucket.WEAK) / len(converted), 3),
        "unsupported": round(sum(1 for item in converted if item.support_bucket is AB3SupportBucket.UNSUPPORTED) / len(converted), 3),
        "contradicted": round(sum(1 for item in converted if item.support_bucket is AB3SupportBucket.CONTRADICTED) / len(converted), 3),
    }
    return replace(
        prior,
        frontier_id=f"{prior.frontier_id}:ab5_update",
        hypotheses=converted,
        closure_status=closure_status,
        confidence_distribution=confidence_distribution,
        fact_claimed=False,
        selected_fact_hypothesis_id=None,
        cause_confirmed=False,
        uncertainty_summary="updated_from_correlated_effects_no_fact_closure",
    )


def _unsafe_basis_reasons(candidate_input: AB5HypothesisUpdateInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if not candidate_input.source_refs:
        reasons.append("source_refs_required")
    prior = candidate_input.prior_frontier
    if prior is None:
        reasons.append("prior_frontier_required")
    else:
        if prior.fact_claimed or prior.cause_confirmed or prior.selected_fact_hypothesis_id is not None:
            reasons.append("fact_claiming_prior_frontier_forbidden")
        if prior.hidden_eval_used:
            reasons.append("prior_frontier_hidden_eval_forbidden")
        if prior.scenario_label_used:
            reasons.append("prior_frontier_scenario_label_forbidden")

    for digest in candidate_input.source_event_digests:
        if digest.hidden_eval_used:
            reasons.append("event_digest_hidden_eval_forbidden")
        if digest.scenario_label_used:
            reasons.append("event_digest_scenario_label_forbidden")
        if digest.cause_claimed or not digest.explicit_non_causal_closure:
            reasons.append("event_digest_cause_claim_forbidden")

    values = (
        tuple(candidate_input.source_refs)
        + tuple(candidate_input.source_effect_refs)
        + tuple(candidate_input.source_request_refs)
        + tuple(candidate_input.epistemic_basis_refs)
        + tuple(candidate_input.source_observation_refs)
    )
    lowered = " ".join(str(item).lower() for item in values)
    for marker in _FORBIDDEN_MARKERS:
        if marker in lowered:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_update_basis")
            else:
                reasons.append("scenario_marker_in_update_basis")
            break
    for token in _WORLD_SPECIFIC_TOKENS:
        if token in lowered:
            reasons.append("world_specific_marker_forbidden_in_ab5_substrate")
            break
    return list(dict.fromkeys(reasons))
