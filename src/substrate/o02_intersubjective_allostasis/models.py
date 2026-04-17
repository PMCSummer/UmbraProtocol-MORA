from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class O02InteractionMode(str, Enum):
    REPAIR_HEAVY = "repair_heavy"
    CONSERVATIVE_MODE_ONLY = "conservative_mode_only"
    COMPRESSED_TASK_MODE = "compressed_task_mode"
    HIGH_PRECISION_MODE = "high_precision_mode"
    BOUNDARY_PROTECTIVE_MODE = "boundary_protective_mode"
    LOW_FRICTION_MODE = "low_friction_mode"


class O02PredictedLoadBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O02RepairPressureBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class O02BudgetBand(str, Enum):
    NARROW = "narrow"
    BALANCED = "balanced"
    EXPANDED = "expanded"


class O02RegulationLeverPreference(str, Enum):
    SLOW_DOWN = "slow_down"
    INCREASE_STRUCTURE = "increase_structure"
    ASK_TARGETED_CHECK = "ask_targeted_check"
    REDUCE_DETAIL = "reduce_detail"
    PRESERVE_EXPLICIT_UNCERTAINTY = "preserve_explicit_uncertainty"
    POSTPONE_STRONG_COMMIT = "postpone_strong_commit"
    PRESERVE_BOUNDARY = "preserve_boundary"
    KEEP_DIRECTNESS = "keep_directness"


class O02BoundaryProtectionStatus(str, Enum):
    PRESERVED = "preserved"
    CONFLICTED = "conflicted"
    NOT_REQUIRED = "not_required"


class O02OtherModelRelianceStatus(str, Enum):
    GROUNDED = "grounded"
    BOUNDED_UNCERTAIN = "bounded_uncertain"
    UNDERCONSTRAINED = "underconstrained"


@dataclass(frozen=True, slots=True)
class O02InteractionDiagnosticsInput:
    recent_corrections_count: int = 0
    recent_misunderstanding_count: int = 0
    clarification_failures: int = 0
    repetition_request_count: int = 0
    impatience_or_compression_request: bool = False
    precision_request: bool = False
    strong_disagreement_risk: bool = False
    self_side_caution_required: bool = False


@dataclass(frozen=True, slots=True)
class O02IntersubjectiveAllostasisState:
    regulation_id: str
    tick_index: int
    interaction_mode: O02InteractionMode
    predicted_other_load: O02PredictedLoadBand
    predicted_self_load: O02PredictedLoadBand
    repair_pressure: O02RepairPressureBand
    detail_budget: O02BudgetBand
    pace_budget: O02BudgetBand
    clarification_threshold: float
    initiative_posture: str
    uncertainty_notice_policy: str
    boundary_protection_status: O02BoundaryProtectionStatus
    other_model_reliance_status: O02OtherModelRelianceStatus
    lever_preferences: tuple[O02RegulationLeverPreference, ...]
    justification_links: tuple[str, ...]
    no_safe_regulation_claim: bool
    other_load_underconstrained: bool
    self_other_constraint_conflict: bool
    s05_shape_modulation_applied: bool
    prior_mode_carry_applied: bool
    strong_disagreement_guard_applied: bool
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class O02IntersubjectiveAllostasisGateDecision:
    repair_sensitive_consumer_ready: bool
    boundary_preserving_consumer_ready: bool
    clarification_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class O02ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    o02_first_slice_only: bool
    o03_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class O02Telemetry:
    regulation_id: str
    tick_index: int
    interaction_mode: O02InteractionMode
    predicted_other_load: O02PredictedLoadBand
    predicted_self_load: O02PredictedLoadBand
    repair_pressure: O02RepairPressureBand
    detail_budget: O02BudgetBand
    pace_budget: O02BudgetBand
    boundary_protection_status: O02BoundaryProtectionStatus
    other_model_reliance_status: O02OtherModelRelianceStatus
    no_safe_regulation_claim: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class O02IntersubjectiveAllostasisResult:
    state: O02IntersubjectiveAllostasisState
    gate: O02IntersubjectiveAllostasisGateDecision
    scope_marker: O02ScopeMarker
    telemetry: O02Telemetry
    reason: str
