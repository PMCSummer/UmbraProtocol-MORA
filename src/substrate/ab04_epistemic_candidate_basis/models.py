from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.ab03_hypothesis_frontier import AB3ExplanationFrontier


class AB4CandidateKind(str, Enum):
    INSPECT = "inspect"
    WAIT = "wait"
    COMPARE = "compare"
    SAMPLE = "sample"
    REMEASURE = "remeasure"
    REOBSERVE = "reobserve"
    CHECK_CONSISTENCY = "check_consistency"
    ISOLATE_UNCERTAINTY = "isolate_uncertainty"
    REQUEST_MORE_PUBLIC_EVIDENCE = "request_more_public_evidence"


class AB4EIGLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AB4BasisStatus(str, Enum):
    USABLE = "usable"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AB4EpistemicBasisInput:
    tick_ref: str
    frontier: AB3ExplanationFrontier | None
    source_refs: tuple[str, ...]
    observation_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    effect_refs: tuple[str, ...] = ()
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    allow_numeric_eig: bool = False
    source: str = "ab04_epistemic_candidate_basis_input"


@dataclass(frozen=True, slots=True)
class AB4ExpectedInformationGain:
    level: AB4EIGLevel
    numeric: float | None
    scoring_refs: tuple[str, ...]
    scoring_policy: str


@dataclass(frozen=True, slots=True)
class AB4EpistemicCandidateBasis:
    basis_id: str
    frontier_ref: str
    hypothesis_refs: tuple[str, ...]
    candidate_kind: AB4CandidateKind
    discriminates_between: tuple[str, ...]
    expected_information_gain: AB4ExpectedInformationGain
    expected_information_gain_policy: str
    uncertainty_basis_refs: tuple[str, ...]
    missing_evidence_refs: tuple[str, ...]
    discriminating_test_refs: tuple[str, ...]
    public_basis_refs: tuple[str, ...]
    allowed_action_kinds: tuple[str, ...]
    target_refs: tuple[str, ...] = ()
    risk: float = 0.0
    cost: float = 0.0
    confidence: float = 0.0
    confidence_policy: str = "bounded"
    forbidden_execution: bool = True
    no_publication_authority: bool = True
    no_world_submission_authority: bool = True
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    action_request_emitted: bool = False
    ap01_request_ref: str | None = None
    fact_claimed: bool = False
    cause_confirmed: bool = False
    basis_status: AB4BasisStatus = AB4BasisStatus.USABLE


@dataclass(frozen=True, slots=True)
class AB4ScopeMarker:
    scope: str
    epistemic_basis_only: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_execution_authority: bool
    no_world_submission_authority: bool
    no_hypothesis_update_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB4Telemetry:
    tick_ref: str
    basis_count: int
    usable_basis_count: int
    blocked_basis_count: int
    inspect_basis_count: int
    wait_or_reobserve_basis_count: int
    high_eig_count: int
    low_or_none_eig_count: int
    unsafe_basis_count: int
    no_basis_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB4EpistemicBasisResult:
    tick_ref: str
    frontier_ref: str | None
    bases: tuple[AB4EpistemicCandidateBasis, ...]
    telemetry: AB4Telemetry
    scope_marker: AB4ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]
