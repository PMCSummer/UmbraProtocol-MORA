from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.ab01_event_digest import AB1EventDigest
from substrate.ab03_hypothesis_frontier import (
    AB3ExplanationFrontier,
    AB3FrontierHypothesisRecord,
    AB3SupportBucket,
)


class AB5DeltaKind(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    UNCHANGED = "unchanged"
    DISCONFIRM = "disconfirm"
    UNRESOLVED = "unresolved"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AB5HypothesisUpdateInput:
    tick_ref: str
    prior_frontier: AB3ExplanationFrontier | None
    source_refs: tuple[str, ...]
    source_effect_refs: tuple[str, ...] = ()
    source_event_digests: tuple[AB1EventDigest, ...] = ()
    source_request_refs: tuple[str, ...] = ()
    epistemic_basis_refs: tuple[str, ...] = ()
    source_observation_refs: tuple[str, ...] = ()
    supporting_hypothesis_refs: tuple[str, ...] = ()
    disconfirming_hypothesis_refs: tuple[str, ...] = ()
    ambiguous_evidence: bool = False
    effect_correlated: bool = False
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    source: str = "ab05_hypothesis_update_input"


@dataclass(frozen=True, slots=True)
class AB5UpdatedHypothesisRecord:
    hypothesis_ref: str
    hypothesis_kind: str
    previous_support_bucket: AB3SupportBucket
    support_bucket: AB3SupportBucket
    confidence: float
    confidence_policy: str
    evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    expected_observations: tuple[str, ...]
    possible_tests: tuple[str, ...]
    explains_what: tuple[str, ...]
    does_not_explain: tuple[str, ...]
    reason_codes: tuple[str, ...]
    fact_status: str = "not_fact"
    cause_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class AB5HypothesisSupportDelta:
    hypothesis_ref: str
    previous_support_bucket: AB3SupportBucket
    new_support_bucket: AB3SupportBucket
    delta_kind: AB5DeltaKind
    evidence_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    event_refs: tuple[str, ...]
    matched_expected_observations: tuple[str, ...]
    contradicted_expected_observations: tuple[str, ...]
    missing_expected_observations: tuple[str, ...]
    reason_codes: tuple[str, ...]
    confidence_delta: float
    confidence_policy: str = "evidence_bounded"
    fact_status: str = "not_fact"


@dataclass(frozen=True, slots=True)
class AB5ScopeMarker:
    scope: str
    hypothesis_support_update_only: bool
    no_hypothesis_generation_authority: bool
    no_epistemic_action_selection_authority: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_execution_authority: bool
    no_ownership_closure_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB5Telemetry:
    tick_ref: str
    hypothesis_count: int
    support_delta_count: int
    strengthened_count: int
    weakened_count: int
    disconfirmed_count: int
    unresolved_count: int
    blocked_count: int
    unchanged_count: int
    unsafe_basis_count: int
    no_update_count: int
    closure_allowed_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB5HypothesisUpdateResult:
    update_id: str
    prior_frontier_ref: str | None
    source_effect_refs: tuple[str, ...]
    source_event_digest_refs: tuple[str, ...]
    source_request_refs: tuple[str, ...]
    epistemic_basis_refs: tuple[str, ...]
    updated_hypothesis_records: tuple[AB5UpdatedHypothesisRecord, ...]
    support_deltas: tuple[AB5HypothesisSupportDelta, ...]
    disconfirmed_hypothesis_refs: tuple[str, ...]
    strengthened_hypothesis_refs: tuple[str, ...]
    weakened_hypothesis_refs: tuple[str, ...]
    unresolved_hypothesis_refs: tuple[str, ...]
    ambiguous_evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    closure_allowed: bool
    closure_blocked_reason: str | None
    closure_policy: str
    updated_frontier_snapshot: AB3ExplanationFrontier | None
    fact_claimed: bool = False
    cause_confirmed: bool = False
    selected_fact_hypothesis_id: str | None = None
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


@dataclass(frozen=True, slots=True)
class AB5UpdateEnvelope:
    tick_ref: str
    update: AB5HypothesisUpdateResult | None
    telemetry: AB5Telemetry
    scope_marker: AB5ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]


def as_ab3_record(updated: AB5UpdatedHypothesisRecord, *, seed_ref: str) -> AB3FrontierHypothesisRecord:
    return AB3FrontierHypothesisRecord(
        hypothesis_id=updated.hypothesis_ref,
        hypothesis_kind=updated.hypothesis_kind,
        seed_ref=seed_ref,
        support_score=round(max(0.0, min(0.95, updated.confidence)), 3),
        support_bucket=updated.support_bucket,
        evidence_refs=updated.evidence_refs,
        missing_evidence=updated.missing_evidence,
        expected_observations=updated.expected_observations,
        possible_tests=updated.possible_tests,
        explains_what=updated.explains_what,
        does_not_explain=updated.does_not_explain,
        conflicts_with=(),
        discriminated_by=updated.possible_tests,
        confidence=updated.confidence,
        confidence_basis_refs=updated.evidence_refs if updated.evidence_refs else ("insufficient_evidence_refs",),
        confidence_policy=updated.confidence_policy,
        fact_status="not_fact",
        cause_confirmed=False,
    )
