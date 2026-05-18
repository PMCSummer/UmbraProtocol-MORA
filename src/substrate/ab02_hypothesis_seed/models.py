from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.ab01_event_digest import AB1EventDigest


class AB2HypothesisKind(str, Enum):
    EFFECT_SOURCE_UNCERTAIN = "effect_source_uncertain"
    EXPECTED_EFFECT_MISSING = "expected_effect_missing"
    OBSERVATION_NOISE_OR_REPORTING_ERROR = "observation_noise_or_reporting_error"
    PRIOR_ACTION_DELAYED_EFFECT = "prior_action_delayed_effect"
    WORLD_STATE_CHANGED = "world_state_changed"
    CAPABILITY_OR_CONSTRAINT_BLOCK = "capability_or_constraint_block"
    INVENTORY_TRANSITION_UNACCOUNTED = "inventory_transition_unaccounted"
    UNKNOWN_EXTERNAL_CAUSE = "unknown_external_cause"
    MEASUREMENT_OR_PROJECTION_MISMATCH = "measurement_or_projection_mismatch"
    INSUFFICIENT_PUBLIC_EVIDENCE = "insufficient_public_evidence"
    INTENDED_EFFECT_OBSERVED = "intended_effect_observed"


class AB2SeedStatus(str, Enum):
    USABLE = "usable"
    BLOCKED = "blocked"


class AB2ClosureStatus(str, Enum):
    OPEN = "open"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AB2HypothesisSeedInput:
    tick_ref: str
    event_digests: tuple[AB1EventDigest, ...]
    source_refs: tuple[str, ...]
    observation_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    effect_refs: tuple[str, ...] = ()
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    prediction_error_signal: float | None = None
    efference_mismatch_present: bool = False
    source: str = "ab02_hypothesis_seed_input"


@dataclass(frozen=True, slots=True)
class AB2HypothesisSeed:
    hypothesis_id: str
    hypothesis_kind: AB2HypothesisKind
    explains_what: tuple[str, ...]
    does_not_explain: tuple[str, ...]
    expected_observations: tuple[str, ...]
    possible_tests: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    scope: str
    confidence_initial: float
    confidence_policy: str
    source_refs: tuple[str, ...]
    event_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    forbidden_fact_closure: bool = True
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    cause_confirmed: bool = False
    rank: int | None = None
    seed_status: AB2SeedStatus = AB2SeedStatus.USABLE


@dataclass(frozen=True, slots=True)
class AB2ScopeMarker:
    scope: str
    hypothesis_seed_only: bool
    no_fact_selection_authority: bool
    no_hypothesis_competition_authority: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_execution_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB2Telemetry:
    tick_ref: str
    seed_count: int
    usable_seed_count: int
    blocked_seed_count: int
    ambiguous_events_count: int
    unsafe_basis_count: int
    no_seed_count: int
    hidden_eval_excluded: bool
    scenario_label_excluded: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB2HypothesisSeedSet:
    seed_set_id: str
    source_event_refs: tuple[str, ...]
    source_residue_refs: tuple[str, ...]
    source_effect_refs: tuple[str, ...]
    source_observation_refs: tuple[str, ...]
    hypotheses: tuple[AB2HypothesisSeed, ...]
    seed_policy: str
    uncertainty_summary: str
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    fact_claimed: bool = False
    selected_fact_hypothesis_id: str | None = None
    closure_status: AB2ClosureStatus = AB2ClosureStatus.OPEN
    blocked_status: bool = False


@dataclass(frozen=True, slots=True)
class AB2HypothesisSeedResult:
    tick_ref: str
    seed_set: AB2HypothesisSeedSet | None
    telemetry: AB2Telemetry
    scope_marker: AB2ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]
