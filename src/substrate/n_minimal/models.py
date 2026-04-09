from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class NarrativeCommitmentStatus(str, Enum):
    BOUNDED_NARRATIVE_COMMITMENT = "bounded_narrative_commitment"
    TENTATIVE_NARRATIVE_CLAIM = "tentative_narrative_claim"
    AMBIGUITY_PRESERVING_NARRATIVE = "ambiguity_preserving_narrative"
    CONTRADICTION_MARKED_NARRATIVE = "contradiction_marked_narrative"
    UNDERCONSTRAINED_NARRATIVE_SURFACE = "underconstrained_narrative_surface"
    NO_SAFE_NARRATIVE_CLAIM = "no_safe_narrative_claim"


class NarrativeRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ForbiddenNarrativeShortcut(str, Enum):
    PROSE_WITHOUT_COMMITMENT_BASIS = "prose_without_commitment_basis"
    NARRATIVE_REFRAMED_AS_SELF_TRUTH_WITHOUT_BASIS = (
        "narrative_reframed_as_self_truth_without_basis"
    )
    NARRATIVE_REFRAMED_AS_WORLD_TRUTH_WITHOUT_BASIS = (
        "narrative_reframed_as_world_truth_without_basis"
    )
    NARRATIVE_REFRAMED_AS_MEMORY_TRUTH_WITHOUT_BASIS = (
        "narrative_reframed_as_memory_truth_without_basis"
    )
    NARRATIVE_REFRAMED_AS_CAPABILITY_TRUTH_WITHOUT_BASIS = (
        "narrative_reframed_as_capability_truth_without_basis"
    )
    AMBIGUITY_ERASED_FROM_NARRATIVE_CLAIM = "ambiguity_erased_from_narrative_claim"
    CONTRADICTION_HIDDEN_BY_FLUENT_WORDING = "contradiction_hidden_by_fluent_wording"
    NARRATIVE_SURFACE_INFERRED_FROM_TESTKIT_ONLY = (
        "narrative_surface_inferred_from_testkit_only"
    )


@dataclass(frozen=True, slots=True)
class NMinimalCommitmentState:
    narrative_commitment_id: str
    commitment_status: NarrativeCommitmentStatus
    commitment_scope: str
    narrative_basis_present: bool
    self_basis_present: bool
    world_basis_present: bool
    memory_basis_present: bool
    capability_basis_present: bool
    ambiguity_residue: bool
    contradiction_risk: NarrativeRiskLevel
    confidence: float
    degraded: bool
    underconstrained: bool
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class NMinimalGateDecision:
    safe_narrative_commitment_allowed: bool
    bounded_commitment_allowed: bool
    no_safe_narrative_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class NLineAdmissionCriteria:
    typed_narrative_commitment_surface_exists: bool
    commitment_states_machine_readable: bool
    machine_readable_forbidden_shortcuts: bool
    rt01_path_affecting_consumption_ready: bool
    n01_implemented: bool
    n02_implemented: bool
    n03_implemented: bool
    n04_implemented: bool
    admission_ready_for_n01: bool
    blockers: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class NMinimalScopeMarker:
    scope: str
    rt01_contour_only: bool
    n_minimal_only: bool
    readiness_gate_only: bool
    n01_implemented: bool
    n02_implemented: bool
    n03_implemented: bool
    n04_implemented: bool
    full_narrative_line_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class NMinimalTelemetry:
    narrative_commitment_id: str
    commitment_status: NarrativeCommitmentStatus
    commitment_scope: str
    ambiguity_residue: bool
    contradiction_risk: NarrativeRiskLevel
    confidence: float
    degraded: bool
    underconstrained: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    n01_admission_ready: bool
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class NMinimalResult:
    state: NMinimalCommitmentState
    gate: NMinimalGateDecision
    admission: NLineAdmissionCriteria
    scope_marker: NMinimalScopeMarker
    telemetry: NMinimalTelemetry
    reason: str
