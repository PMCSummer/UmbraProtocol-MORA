from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.ab02_hypothesis_seed import AB2HypothesisSeedSet


class AB3SupportBucket(str, Enum):
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    PROVISIONAL = "provisional"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"


class AB3ClosureStatus(str, Enum):
    OPEN = "open"
    BLOCKED = "blocked"
    PROVISIONALLY_RANKED = "provisionally_ranked"
    RESOLVED_ALLOWED_BUT_NOT_CLAIMED = "resolved_allowed_but_not_claimed"


@dataclass(frozen=True, slots=True)
class AB3FrontierInput:
    tick_ref: str
    seed_set: AB2HypothesisSeedSet | None
    source_refs: tuple[str, ...]
    observation_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    effect_refs: tuple[str, ...] = ()
    disconfirming_evidence_refs: tuple[str, ...] = ()
    ambiguous_evidence: bool = False
    require_competing_hypotheses: bool = True
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    source: str = "ab03_hypothesis_frontier_input"


@dataclass(frozen=True, slots=True)
class AB3FrontierHypothesisRecord:
    hypothesis_id: str
    hypothesis_kind: str
    seed_ref: str
    support_score: float | None
    support_bucket: AB3SupportBucket
    evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    expected_observations: tuple[str, ...]
    possible_tests: tuple[str, ...]
    explains_what: tuple[str, ...]
    does_not_explain: tuple[str, ...]
    conflicts_with: tuple[str, ...]
    discriminated_by: tuple[str, ...]
    confidence: float
    confidence_basis_refs: tuple[str, ...]
    confidence_policy: str
    fact_status: str = "not_fact"
    cause_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class AB3ExplanationFrontier:
    frontier_id: str
    source_seed_set_refs: tuple[str, ...]
    source_event_refs: tuple[str, ...]
    source_residue_refs: tuple[str, ...]
    source_effect_refs: tuple[str, ...]
    hypotheses: tuple[AB3FrontierHypothesisRecord, ...]
    leader_hypothesis_id: str | None
    competitive_neighborhood: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    discriminating_tests: tuple[str, ...]
    confidence_distribution: dict[str, float]
    closure_status: AB3ClosureStatus
    fact_claimed: bool = False
    selected_fact_hypothesis_id: str | None = None
    cause_confirmed: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    frontier_policy: str = "ab3_explanation_frontier_competition_v1"
    uncertainty_summary: str = "open_frontier"


@dataclass(frozen=True, slots=True)
class AB3ScopeMarker:
    scope: str
    local_explanation_frontier_only: bool
    no_fact_selection_authority: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_execution_authority: bool
    no_epistemic_action_selection_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB3Telemetry:
    tick_ref: str
    hypothesis_count: int
    unresolved_conflict_count: int
    missing_evidence_count: int
    discriminating_test_count: int
    supported_count: int
    provisional_count: int
    weak_count: int
    contradicted_count: int
    blocked_count: int
    unsafe_basis_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB3FrontierResult:
    tick_ref: str
    frontier: AB3ExplanationFrontier | None
    telemetry: AB3Telemetry
    scope_marker: AB3ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]
