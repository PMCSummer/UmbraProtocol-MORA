from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AttributionSourceStatus(str, Enum):
    INTERNAL_DOMINANT = "internal_dominant"
    EXTERNAL_DOMINANT = "external_dominant"
    MIXED = "mixed"
    UNDERCONSTRAINED = "underconstrained"


class BoundaryBreachRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AttributionClass(str, Enum):
    SELF_OWNED_STATE_CLAIM = "self_owned_state_claim"
    SELF_CAUSED_CHANGE_CLAIM = "self_caused_change_claim"
    SELF_CONTROLLED_TRANSITION_CLAIM = "self_controlled_transition_claim"
    EXTERNALLY_CAUSED_CHANGE_CLAIM = "externally_caused_change_claim"
    WORLD_CAUSED_PERTURBATION_CLAIM = "world_caused_perturbation_claim"
    MIXED_OR_UNDERCONSTRAINED_ATTRIBUTION = "mixed_or_underconstrained_attribution"
    NO_SAFE_SELF_CLAIM = "no_safe_self_claim"
    NO_SAFE_WORLD_CLAIM = "no_safe_world_claim"


class ForbiddenSelfWorldShortcut(str, Enum):
    SELF_CLAIM_WITHOUT_SELF_BASIS = "self_claim_without_self_basis"
    OWNERSHIP_CLAIM_WITHOUT_ACTION_OR_BOUNDARY_BASIS = (
        "ownership_claim_without_action_or_boundary_basis"
    )
    CONTROL_CLAIM_WITHOUT_CONTROLLABILITY_BASIS = (
        "control_claim_without_controllability_basis"
    )
    EXTERNAL_EVENT_REFRAMED_AS_SELF_OWNED = "external_event_reframed_as_self_owned"
    SELF_STATE_REFRAMED_AS_WORLD_FACT = "self_state_reframed_as_world_fact"
    MIXED_ATTRIBUTION_WITHOUT_UNCERTAINTY_MARKING = (
        "mixed_attribution_without_uncertainty_marking"
    )


@dataclass(frozen=True, slots=True)
class SMinimalBoundaryState:
    boundary_state_id: str
    self_attribution_basis_present: bool
    world_attribution_basis_present: bool
    controllability_estimate: float
    ownership_estimate: float
    attribution_confidence: float
    internal_vs_external_source_status: AttributionSourceStatus
    boundary_breach_risk: BoundaryBreachRisk
    attribution_class: AttributionClass
    no_safe_self_claim: bool
    no_safe_world_claim: bool
    degraded: bool
    underconstrained: bool
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class SMinimalGateDecision:
    self_owned_state_claim_allowed: bool
    self_caused_change_claim_allowed: bool
    self_controlled_transition_claim_allowed: bool
    externally_caused_change_claim_allowed: bool
    world_caused_perturbation_claim_allowed: bool
    mixed_or_underconstrained_attribution: bool
    no_safe_self_claim: bool
    no_safe_world_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class SLineAdmissionCriteria:
    s_minimal_contour_materialized: bool
    typed_boundary_surface_exists: bool
    ownership_controllability_discipline_exists: bool
    forbidden_shortcuts_machine_readable: bool
    rt01_path_affecting_consumption_ready: bool
    future_s01_s05_remain_open: bool
    full_self_model_implemented: bool
    admission_ready_for_s01: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class SMinimalScopeMarker:
    scope: str
    minimal_contour_only: bool
    s01_s05_implemented: bool
    full_self_model_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SMinimalTelemetry:
    boundary_state_id: str
    attribution_class: AttributionClass
    source_status: AttributionSourceStatus
    boundary_breach_risk: BoundaryBreachRisk
    controllability_estimate: float
    ownership_estimate: float
    attribution_confidence: float
    degraded: bool
    underconstrained: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class SMinimalContourResult:
    state: SMinimalBoundaryState
    gate: SMinimalGateDecision
    admission: SLineAdmissionCriteria
    scope_marker: SMinimalScopeMarker
    telemetry: SMinimalTelemetry
    reason: str
