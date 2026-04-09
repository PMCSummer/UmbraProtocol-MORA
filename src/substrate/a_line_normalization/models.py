from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class CapabilityClass(str, Enum):
    INTERNAL_AFFORDANCE = "internal_affordance"
    WORLD_CONDITIONED_AFFORDANCE = "world_conditioned_affordance"
    SELF_CONDITIONED_AFFORDANCE = "self_conditioned_affordance"
    POLICY_CONDITIONED_AFFORDANCE = "policy_conditioned_affordance"


class CapabilityStatus(str, Enum):
    AVAILABLE_CAPABILITY = "available_capability"
    UNAVAILABLE_CAPABILITY = "unavailable_capability"
    WORLD_CONDITIONED_CAPABILITY = "world_conditioned_capability"
    SELF_CONDITIONED_CAPABILITY = "self_conditioned_capability"
    POLICY_CONDITIONED_CAPABILITY = "policy_conditioned_capability"
    UNDERCONSTRAINED_CAPABILITY = "underconstrained_capability"
    NO_SAFE_CAPABILITY_CLAIM = "no_safe_capability_claim"


class ForbiddenCapabilityShortcut(str, Enum):
    CAPABILITY_CLAIM_WITHOUT_BASIS = "capability_claim_without_basis"
    AFFORDANCE_CLAIM_WITHOUT_WORLD_OR_SELF_BASIS = (
        "affordance_claim_without_world_or_self_basis"
    )
    UNAVAILABLE_CAPABILITY_REFRAMED_AS_AVAILABLE = (
        "unavailable_capability_reframed_as_available"
    )
    POLICY_GATED_CAPABILITY_REFRAMED_AS_FREE_ACTION = (
        "policy_gated_capability_reframed_as_free_action"
    )
    UNDERCONSTRAINED_CAPABILITY_PRESENTED_AS_READY = (
        "underconstrained_capability_presented_as_ready"
    )
    CAPABILITY_INFERRED_FROM_TESTKIT_ONLY = "capability_inferred_from_testkit_only"
    HIDDEN_EXTERNAL_MEANS_CLAIM = "hidden_external_means_claim"


@dataclass(frozen=True, slots=True)
class ALineCapabilityState:
    capability_id: str
    affordance_id: str
    capability_class: CapabilityClass
    capability_status: CapabilityStatus
    availability_basis_present: bool
    world_dependency_present: bool
    self_dependency_present: bool
    controllability_dependency_present: bool
    legitimacy_dependency_present: bool
    confidence: float
    degraded: bool
    underconstrained: bool
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class ALineGateDecision:
    available_capability_claim_allowed: bool
    world_conditioned_capability_claim_allowed: bool
    self_conditioned_capability_claim_allowed: bool
    policy_conditioned_capability_present: bool
    underconstrained_capability: bool
    no_safe_capability_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class A04ReadinessCriteria:
    typed_a01_a03_substrate_exists: bool
    capability_states_machine_readable: bool
    dependency_linkage_world_self_policy_inspectable: bool
    structurally_present_but_not_ready: bool
    capability_basis_missing: bool
    world_dependency_unmet: bool
    self_dependency_unmet: bool
    policy_legitimacy_unmet: bool
    underconstrained_capability_surface: bool
    external_means_not_justified: bool
    forbidden_shortcuts_machine_readable: bool
    rt01_path_affecting_consumption_ready: bool
    a04_implemented: bool
    a05_touched: bool
    admission_ready_for_a04: bool
    blockers: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class ALineScopeMarker:
    scope: str
    rt01_contour_only: bool
    a_line_normalization_only: bool
    readiness_gate_only: bool
    a04_implemented: bool
    a05_touched: bool
    full_agency_stack_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ALineTelemetry:
    capability_id: str
    capability_status: CapabilityStatus
    capability_class: CapabilityClass
    confidence: float
    degraded: bool
    underconstrained: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    a04_admission_ready: bool
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ALineNormalizationResult:
    state: ALineCapabilityState
    gate: ALineGateDecision
    a04_readiness: A04ReadinessCriteria
    scope_marker: ALineScopeMarker
    telemetry: ALineTelemetry
    reason: str
