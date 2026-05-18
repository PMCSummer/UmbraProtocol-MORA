from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AB6AttributionKind(str, Enum):
    SELF_ACTION = "self_action"
    WORLD_PROCESS = "world_process"
    OTHER_ACTOR = "other_actor"
    DELAYED_SELF_EFFECT = "delayed_self_effect"
    MIXED_CAUSE = "mixed_cause"
    UNKNOWN_CAUSE = "unknown_cause"
    SENSOR_OR_PROJECTION_ERROR = "sensor_or_projection_error"


class AB6SupportStatus(str, Enum):
    SUPPORTED = "supported"
    WEAK = "weak"
    BLOCKED = "blocked"
    NOT_SUPPORTED = "not_supported"
    UNRESOLVED = "unresolved"


class AB6ClosureStatus(str, Enum):
    OPEN = "open"
    BLOCKED = "blocked"
    PROVISIONALLY_ATTRIBUTED = "provisionally_attributed"


@dataclass(frozen=True, slots=True)
class AB6CausalAttributionInput:
    tick_ref: str
    source_frontier_refs: tuple[str, ...]
    source_update_refs: tuple[str, ...] = ()
    source_event_digest_refs: tuple[str, ...] = ()
    source_effect_refs: tuple[str, ...] = ()
    source_request_refs: tuple[str, ...] = ()
    source_candidate_refs: tuple[str, ...] = ()
    source_observation_refs: tuple[str, ...] = ()
    timing_refs: tuple[str, ...] = ()
    external_event_refs: tuple[str, ...] = ()
    other_actor_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    missing_evidence_refs: tuple[str, ...] = ()
    effect_correlated: bool = False
    blocked_action: bool = False
    delayed_marker: bool = False
    mixed_marker: bool = False
    unknown_marker: bool = False
    sensor_mismatch_marker: bool = False
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    source: str = "ab06_causal_attribution_input"


@dataclass(frozen=True, slots=True)
class AB6AttributionCandidate:
    attribution_id: str
    attribution_kind: AB6AttributionKind
    supports: tuple[str, ...]
    does_not_explain: tuple[str, ...]
    required_evidence: tuple[str, ...]
    present_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    timing_refs: tuple[str, ...]
    confidence: float
    confidence_policy: str
    support_status: AB6SupportStatus
    forbidden_fact_closure: bool = True


@dataclass(frozen=True, slots=True)
class AB6CausalAttributionFrame:
    attribution_frame_id: str
    source_frontier_refs: tuple[str, ...]
    source_update_refs: tuple[str, ...]
    source_event_digest_refs: tuple[str, ...]
    source_effect_refs: tuple[str, ...]
    source_request_refs: tuple[str, ...]
    source_candidate_refs: tuple[str, ...]
    source_observation_refs: tuple[str, ...]
    timing_refs: tuple[str, ...]
    attribution_candidates: tuple[AB6AttributionCandidate, ...]
    supported_attribution_kinds: tuple[str, ...]
    blocked_attribution_kinds: tuple[str, ...]
    unresolved_attribution_kinds: tuple[str, ...]
    mixed_cause_preserved: bool
    unknown_preserved: bool
    uncertainty: float
    missing_evidence: tuple[str, ...]
    closure_status: AB6ClosureStatus
    fact_claimed: bool = False
    cause_confirmed: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False


@dataclass(frozen=True, slots=True)
class AB6ScopeMarker:
    scope: str
    causal_attribution_only: bool
    no_hypothesis_update_authority: bool
    no_epistemic_action_selection_authority: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_execution_authority: bool
    no_full_causal_truth_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB6Telemetry:
    tick_ref: str
    candidate_count: int
    supported_count: int
    weak_count: int
    blocked_count: int
    unresolved_count: int
    unsafe_basis_count: int
    no_frame_count: int
    mixed_preserved_count: int
    unknown_preserved_count: int
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB6CausalAttributionResult:
    tick_ref: str
    frame: AB6CausalAttributionFrame | None
    telemetry: AB6Telemetry
    scope_marker: AB6ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]
