from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class T03HypothesisStatus(str, Enum):
    CANDIDATE = "candidate"
    LEADING = "leading"
    PROVISIONAL_FRONTRUNNER = "provisional_frontrunner"
    TIED_COMPETITOR = "tied_competitor"
    BLOCKED = "blocked"
    ELIMINATED = "eliminated"
    REACTIVATED = "reactivated"


class T03ConvergenceStatus(str, Enum):
    CONTINUE_COMPETING = "continue_competing"
    PROVISIONAL_CONVERGENCE = "provisional_convergence"
    STABLE_LOCAL_CONVERGENCE = "stable_local_convergence"
    HONEST_NONCONVERGENCE = "honest_nonconvergence"


class T03StabilityState(str, Enum):
    STABLE = "stable"
    PROVISIONAL = "provisional"
    CONTESTED = "contested"
    BLOCKED = "blocked"
    DEGRADED = "degraded"


class T03CompetitionOperation(str, Enum):
    REGISTER_CANDIDATES = "register_candidates"
    WEIGHT_AUTHORITY_SUPPORT = "weight_authority_support"
    APPLY_CONSTRAINT_LOAD = "apply_constraint_load"
    APPLY_UNRESOLVED_BURDEN = "apply_unresolved_burden"
    RESOLVE_FRONTIER = "resolve_frontier"
    PRESERVE_NONCONVERGENCE = "preserve_nonconvergence"
    REACTIVATE_HYPOTHESIS = "reactivate_hypothesis"


class T03CompetitionMode(str, Enum):
    BOUNDED_COMPETITION = "bounded_competition"
    GREEDY_ARGMAX_ABLATION = "greedy_argmax_ablation"
    HIDDEN_TEXT_RERANKING_ABLATION = "hidden_text_reranking_ablation"
    NO_REVIVAL_ABLATION = "no_revival_ablation"
    CONVENIENCE_BIAS_ABLATION = "convenience_bias_ablation"
    FORCED_SINGLE_WINNER_ABLATION = "forced_single_winner_ablation"
    AUTHORITY_WEIGHT_DISABLE_ABLATION = "authority_weight_disable_ablation"


class ForbiddenT03Shortcut(str, Enum):
    GREEDY_WINNER_TAKE_ALL_ARGMAX = "greedy_winner_take_all_argmax"
    HIDDEN_TEXT_RERANKING = "hidden_text_reranking"
    CONVENIENCE_BIASED_CANDIDATE_SELECTION = "convenience_biased_candidate_selection"
    LOW_AUTHORITY_SMOOTH_DOMINATION = "low_authority_smooth_domination"
    NO_REVIVAL_COMPETITION = "no_revival_competition"
    FORCED_SINGLE_WINNER_UNDER_AMBIGUITY = "forced_single_winner_under_ambiguity"
    CONFIDENCE_INCREASE_WITHOUT_NEW_SUPPORT = "confidence_increase_without_new_support"
    AUTHORITY_WEIGHT_DISABLED = "authority_weight_disabled"


@dataclass(frozen=True, slots=True)
class T03HypothesisCandidate:
    hypothesis_id: str
    scene_variant_id: str
    support_sources: tuple[str, ...]
    violated_constraints: tuple[str, ...]
    satisfied_constraints: tuple[str, ...]
    unresolved_load: float
    authority_profile: tuple[str, ...]
    competition_score: float
    stability_state: T03StabilityState
    divergence_signature: str
    status: T03HypothesisStatus
    provenance: str


@dataclass(frozen=True, slots=True)
class T03PublicationFrontierSnapshot:
    current_leader: str | None
    competitive_neighborhood: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    open_slots: tuple[str, ...]
    authority_profile: tuple[str, ...]
    stability_status: str
    provenance: str


@dataclass(frozen=True, slots=True)
class T03CompetitionState:
    competition_id: str
    source_t01_scene_id: str
    source_t02_constrained_scene_id: str
    candidates: tuple[T03HypothesisCandidate, ...]
    convergence_status: T03ConvergenceStatus
    current_leader_hypothesis_id: str | None
    provisional_frontrunner_hypothesis_id: str | None
    tied_competitor_ids: tuple[str, ...]
    blocked_hypothesis_ids: tuple[str, ...]
    eliminated_hypothesis_ids: tuple[str, ...]
    reactivated_hypothesis_ids: tuple[str, ...]
    honest_nonconvergence: bool
    bounded_plurality: bool
    publication_frontier: T03PublicationFrontierSnapshot
    operations_applied: tuple[str, ...]
    source_authority_tags: tuple[str, ...]
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class T03GateDecision:
    convergence_consumer_ready: bool
    frontier_consumer_ready: bool
    nonconvergence_preserved: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class T03ScopeMarker:
    scope: str
    rt01_contour_only: bool
    t03_first_slice_only: bool
    t04_implemented: bool
    o01_implemented: bool
    o02_implemented: bool
    o03_implemented: bool
    full_silent_thought_line_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class T03Telemetry:
    competition_id: str
    source_t01_scene_id: str
    source_t02_constrained_scene_id: str
    convergence_status: T03ConvergenceStatus
    candidates_count: int
    blocked_hypothesis_count: int
    eliminated_hypothesis_count: int
    reactivated_hypothesis_count: int
    tied_competitor_count: int
    bounded_plurality: bool
    honest_nonconvergence: bool
    convergence_consumer_ready: bool
    frontier_consumer_ready: bool
    nonconvergence_preserved: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class T03CompetitionResult:
    state: T03CompetitionState
    gate: T03GateDecision
    scope_marker: T03ScopeMarker
    telemetry: T03Telemetry
    reason: str
