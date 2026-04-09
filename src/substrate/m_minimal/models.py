from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class MemoryLifecycleStatus(str, Enum):
    TEMPORARY_CARRY = "temporary_carry"
    BOUNDED_RETAINED = "bounded_retained"
    REVIEW_REQUIRED = "review_required"
    REACTIVATION_CANDIDATE = "reactivation_candidate"
    STALE_MEMORY_SURFACE = "stale_memory_surface"
    CONFLICT_MARKED_MEMORY = "conflict_marked_memory"
    DECAY_CANDIDATE = "decay_candidate"
    PRUNING_CANDIDATE = "pruning_candidate"
    NO_SAFE_MEMORY_CLAIM = "no_safe_memory_claim"


class MemoryRetentionClass(str, Enum):
    TRANSIENT = "transient"
    BOUNDED = "bounded"
    REVIEW = "review"
    REACTIVATION = "reactivation"
    DECAY = "decay"
    PRUNING = "pruning"
    UNSAFE = "unsafe"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ForbiddenMemoryShortcut(str, Enum):
    TEMPORARY_MEMORY_REFRAMED_AS_STABLE_FACT = (
        "temporary_memory_reframed_as_stable_fact"
    )
    STALE_MEMORY_REFRAMED_AS_CURRENT_TRUTH = "stale_memory_reframed_as_current_truth"
    CONFLICT_MARKED_MEMORY_SILENTLY_MERGED = (
        "conflict_marked_memory_silently_merged"
    )
    NO_PROVENANCE_MEMORY_CLAIM = "no_provenance_memory_claim"
    UNREVIEWED_MEMORY_REUSED_AS_SAFE_BASIS = (
        "unreviewed_memory_reused_as_safe_basis"
    )
    RETAINED_MEMORY_REFRAMED_AS_IDENTITY_WITHOUT_BASIS = (
        "retained_memory_reframed_as_identity_without_basis"
    )
    MEMORY_SURFACE_INFERRED_FROM_TESTKIT_ONLY = "memory_surface_inferred_from_testkit_only"


@dataclass(frozen=True, slots=True)
class MMinimalLifecycleState:
    memory_item_id: str
    memory_packet_id: str
    lifecycle_status: MemoryLifecycleStatus
    retention_class: MemoryRetentionClass
    bounded_persistence_allowed: bool
    temporary_carry_allowed: bool
    review_required: bool
    reactivation_eligible: bool
    decay_eligible: bool
    pruning_eligible: bool
    stale_risk: RiskLevel
    conflict_risk: RiskLevel
    confidence: float
    reliability: str
    degraded: bool
    underconstrained: bool
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class MMinimalGateDecision:
    safe_memory_claim_allowed: bool
    bounded_retained_claim_allowed: bool
    no_safe_memory_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class MLineAdmissionCriteria:
    typed_memory_lifecycle_surface_exists: bool
    lifecycle_states_machine_readable: bool
    safe_lifecycle_discipline_materialized: bool
    machine_readable_forbidden_shortcuts: bool
    rt01_path_affecting_consumption_ready: bool
    structurally_present_but_not_ready: bool
    stale_risk_unacceptable: bool
    conflict_risk_unacceptable: bool
    reactivation_requires_review: bool
    temporary_carry_not_stable_enough: bool
    no_safe_memory_basis: bool
    provenance_insufficient: bool
    lifecycle_underconstrained: bool
    m01_implemented: bool
    m02_implemented: bool
    m03_implemented: bool
    admission_ready_for_m01: bool
    blockers: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class MMinimalScopeMarker:
    scope: str
    rt01_contour_only: bool
    m_minimal_only: bool
    readiness_gate_only: bool
    m01_implemented: bool
    m02_implemented: bool
    m03_implemented: bool
    full_memory_stack_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class MMinimalTelemetry:
    memory_item_id: str
    lifecycle_status: MemoryLifecycleStatus
    retention_class: MemoryRetentionClass
    stale_risk: RiskLevel
    conflict_risk: RiskLevel
    confidence: float
    reliability: str
    degraded: bool
    underconstrained: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    m01_admission_ready: bool
    reason: str
    emitted_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


@dataclass(frozen=True, slots=True)
class MMinimalResult:
    state: MMinimalLifecycleState
    gate: MMinimalGateDecision
    admission: MLineAdmissionCriteria
    scope_marker: MMinimalScopeMarker
    telemetry: MMinimalTelemetry
    reason: str
