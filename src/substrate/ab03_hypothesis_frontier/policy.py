from __future__ import annotations

from substrate.ab02_hypothesis_seed import AB2SeedStatus

from .models import (
    AB3ClosureStatus,
    AB3ExplanationFrontier,
    AB3FrontierHypothesisRecord,
    AB3FrontierInput,
    AB3FrontierResult,
    AB3ScopeMarker,
    AB3SupportBucket,
)
from .telemetry import build_ab3_telemetry

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


def build_ab3_hypothesis_frontier(candidate_input: AB3FrontierInput) -> AB3FrontierResult:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    frontier: AB3ExplanationFrontier | None = None
    hypotheses: tuple[AB3FrontierHypothesisRecord, ...] = ()
    if not unsafe_reasons:
        frontier, hypotheses = _build_frontier(candidate_input)

    telemetry = build_ab3_telemetry(
        candidate_input=candidate_input,
        hypotheses=hypotheses,
        unsafe_basis_count=len(unsafe_reasons),
    )
    scope = AB3ScopeMarker(
        scope="ab03_hypothesis_frontier_competition",
        local_explanation_frontier_only=True,
        no_fact_selection_authority=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_execution_authority=True,
        no_epistemic_action_selection_authority=True,
        reason="ab3 maintains local abductive explanation frontier over ab2 seeds without fact/action closure",
    )
    if unsafe_reasons:
        reason_codes = tuple(unsafe_reasons)
    elif frontier is None:
        reason_codes = ("no_frontier_emitted",)
    else:
        reason_codes = ("frontier_emitted",)
    return AB3FrontierResult(
        tick_ref=candidate_input.tick_ref,
        frontier=frontier,
        telemetry=telemetry,
        scope_marker=scope,
        reason_codes=reason_codes,
        source_lineage=("ab03_hypothesis_frontier.policy",),
    )


def _build_frontier(
    candidate_input: AB3FrontierInput,
) -> tuple[AB3ExplanationFrontier | None, tuple[AB3FrontierHypothesisRecord, ...]]:
    seed_set = candidate_input.seed_set
    if seed_set is None:
        return None, ()
    if seed_set.fact_claimed or seed_set.selected_fact_hypothesis_id is not None:
        return None, ()

    records = _records_from_seed_set(candidate_input)
    if not records:
        return None, ()

    usable = tuple(item for item in records if item.support_bucket is not AB3SupportBucket.UNSUPPORTED)
    conflicting = tuple(item for item in usable if item.conflicts_with)
    unresolved = _unresolved_conflicts(usable)
    missing_evidence = tuple(dict.fromkeys(code for item in records for code in item.missing_evidence))
    tests = tuple(dict.fromkeys(test for item in usable for test in item.discriminated_by))
    confidence_distribution = _confidence_distribution(records)

    must_block = False
    closure_status = AB3ClosureStatus.OPEN
    if candidate_input.require_competing_hypotheses and len(usable) <= 1:
        must_block = True
        closure_status = AB3ClosureStatus.BLOCKED
    elif missing_evidence:
        closure_status = AB3ClosureStatus.OPEN
    else:
        closure_status = AB3ClosureStatus.PROVISIONALLY_RANKED

    if candidate_input.ambiguous_evidence and not must_block:
        closure_status = AB3ClosureStatus.OPEN

    leader_id = _leader_hypothesis_id(usable, ambiguous_evidence=candidate_input.ambiguous_evidence)
    if must_block:
        leader_id = None

    if usable and not tests:
        # competing hypotheses without discriminating tests must remain blocked for AB4 readiness.
        closure_status = AB3ClosureStatus.BLOCKED
        must_block = True
        leader_id = None

    frontier = AB3ExplanationFrontier(
        frontier_id=f"ab3:{candidate_input.tick_ref}:frontier",
        source_seed_set_refs=(seed_set.seed_set_id,),
        source_event_refs=tuple(seed_set.source_event_refs),
        source_residue_refs=tuple(seed_set.source_residue_refs),
        source_effect_refs=tuple(seed_set.source_effect_refs),
        hypotheses=records,
        leader_hypothesis_id=leader_id,
        competitive_neighborhood=tuple(item.hypothesis_id for item in sorted(usable, key=lambda it: it.confidence, reverse=True)[:3]),
        unresolved_conflicts=unresolved,
        missing_evidence=missing_evidence,
        discriminating_tests=tests,
        confidence_distribution=confidence_distribution,
        closure_status=closure_status,
        fact_claimed=False,
        selected_fact_hypothesis_id=None,
        cause_confirmed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
        frontier_policy="ab3_evidence_bounded_local_frontier_v1",
        uncertainty_summary=_uncertainty_summary(
            usable_count=len(usable),
            unresolved_count=len(unresolved),
            ambiguous=candidate_input.ambiguous_evidence,
            blocked=must_block,
        ),
    )
    return frontier, records


def _records_from_seed_set(candidate_input: AB3FrontierInput) -> tuple[AB3FrontierHypothesisRecord, ...]:
    assert candidate_input.seed_set is not None
    seeds = tuple(seed for seed in candidate_input.seed_set.hypotheses if seed.seed_status is AB2SeedStatus.USABLE)
    if not seeds:
        return ()

    ids = tuple(seed.hypothesis_id for seed in seeds)
    records: list[AB3FrontierHypothesisRecord] = []
    for seed in seeds:
        evidence_refs = tuple(dict.fromkeys((*seed.event_refs, *seed.residue_refs, *seed.effect_refs, *seed.source_refs)))
        disconfirmed = bool(set(evidence_refs).intersection(set(candidate_input.disconfirming_evidence_refs)))
        missing = tuple(seed.missing_evidence)
        score = _support_score(seed_confidence=seed.confidence_initial, evidence_count=len(evidence_refs), missing_count=len(missing))
        if not evidence_refs:
            score = None
        bucket = _support_bucket(score=score, disconfirmed=disconfirmed, missing_count=len(missing))
        confidence = _frontier_confidence(score=score, missing_count=len(missing), evidence_count=len(evidence_refs))
        conflicts = tuple(other_id for other_id in ids if other_id != seed.hypothesis_id)
        discriminated_by = tuple(seed.possible_tests)
        if candidate_input.ambiguous_evidence and len(conflicts) > 0:
            discriminated_by = tuple(dict.fromkeys((*discriminated_by, "collect_more_public_discriminating_evidence")))
        records.append(
            AB3FrontierHypothesisRecord(
                hypothesis_id=seed.hypothesis_id,
                hypothesis_kind=seed.hypothesis_kind.value,
                seed_ref=seed.hypothesis_id,
                support_score=score,
                support_bucket=bucket,
                evidence_refs=evidence_refs,
                missing_evidence=missing,
                expected_observations=tuple(seed.expected_observations),
                possible_tests=tuple(seed.possible_tests),
                explains_what=tuple(seed.explains_what),
                does_not_explain=tuple(seed.does_not_explain),
                conflicts_with=conflicts,
                discriminated_by=discriminated_by,
                confidence=confidence,
                confidence_basis_refs=evidence_refs if evidence_refs else ("insufficient_evidence_refs",),
                confidence_policy="evidence_bounded",
                fact_status="not_fact",
                cause_confirmed=False,
            )
        )
    return tuple(records)


def _support_score(*, seed_confidence: float, evidence_count: int, missing_count: int) -> float:
    score = float(seed_confidence)
    score += min(float(evidence_count), 4.0) * 0.05
    score -= min(float(missing_count), 3.0) * 0.2
    return round(max(0.0, min(0.95, score)), 3)


def _support_bucket(*, score: float | None, disconfirmed: bool, missing_count: int) -> AB3SupportBucket:
    if disconfirmed:
        return AB3SupportBucket.CONTRADICTED
    if score is None:
        return AB3SupportBucket.UNSUPPORTED
    if missing_count > 0 and score < 0.45:
        return AB3SupportBucket.WEAK
    if score >= 0.7 and missing_count == 0:
        return AB3SupportBucket.SUPPORTED
    if score >= 0.45:
        return AB3SupportBucket.PROVISIONAL
    if score >= 0.2:
        return AB3SupportBucket.WEAK
    return AB3SupportBucket.UNSUPPORTED


def _frontier_confidence(*, score: float | None, missing_count: int, evidence_count: int) -> float:
    if score is None:
        return 0.1
    confidence = score
    if evidence_count <= 1:
        confidence -= 0.15
    confidence -= 0.05 * float(missing_count)
    return round(max(0.05, min(0.85, confidence)), 3)


def _leader_hypothesis_id(
    usable: tuple[AB3FrontierHypothesisRecord, ...],
    *,
    ambiguous_evidence: bool,
) -> str | None:
    if not usable or ambiguous_evidence:
        return None
    ordered = sorted(usable, key=lambda item: item.confidence, reverse=True)
    top = ordered[0]
    if len(ordered) > 1 and abs(top.confidence - ordered[1].confidence) < 0.08:
        return None
    return top.hypothesis_id


def _confidence_distribution(hypotheses: tuple[AB3FrontierHypothesisRecord, ...]) -> dict[str, float]:
    if not hypotheses:
        return {}
    total = float(len(hypotheses))
    counts: dict[str, float] = {}
    for bucket in AB3SupportBucket:
        value = sum(1 for item in hypotheses if item.support_bucket is bucket) / total
        counts[bucket.value] = round(value, 3)
    return counts


def _unresolved_conflicts(hypotheses: tuple[AB3FrontierHypothesisRecord, ...]) -> tuple[str, ...]:
    conflicts: list[str] = []
    for item in hypotheses:
        for other in item.conflicts_with:
            conflicts.append(f"{item.hypothesis_id} vs {other}")
    return tuple(dict.fromkeys(conflicts))


def _uncertainty_summary(*, usable_count: int, unresolved_count: int, ambiguous: bool, blocked: bool) -> str:
    if blocked:
        return "blocked:insufficient_competing_frontier_basis"
    if ambiguous or unresolved_count > 0:
        return f"open:usable={usable_count};unresolved_conflicts={unresolved_count}"
    return f"provisionally_ranked:usable={usable_count};no_fact_closure"


def _unsafe_basis_reasons(candidate_input: AB3FrontierInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if not candidate_input.source_refs:
        reasons.append("source_refs_required")

    values = (
        tuple(candidate_input.source_refs)
        + tuple(candidate_input.observation_refs)
        + tuple(candidate_input.residue_refs)
        + tuple(candidate_input.effect_refs)
        + tuple(candidate_input.disconfirming_evidence_refs)
    )
    lowered = " ".join(str(item).lower() for item in values)
    for marker in _FORBIDDEN_MARKERS:
        if marker in lowered:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_frontier_basis")
            else:
                reasons.append("scenario_marker_in_frontier_basis")
            break

    for token in _WORLD_SPECIFIC_TOKENS:
        if token in lowered:
            reasons.append("world_specific_marker_forbidden_in_ab3_substrate")
            break

    seed_set = candidate_input.seed_set
    if seed_set is not None:
        if seed_set.hidden_eval_used:
            reasons.append("seed_set_hidden_eval_forbidden")
        if seed_set.scenario_label_used:
            reasons.append("seed_set_scenario_label_forbidden")
        if seed_set.fact_claimed or seed_set.selected_fact_hypothesis_id is not None:
            reasons.append("seed_set_fact_closure_forbidden")
    return list(dict.fromkeys(reasons))
