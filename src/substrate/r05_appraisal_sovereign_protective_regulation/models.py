from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class R05ProtectiveMode(str, Enum):
    VIGILANCE_WITHOUT_OVERRIDE = "vigilance_without_override"
    PROTECTIVE_CANDIDATE_ONLY = "protective_candidate_only"
    ACTIVE_PROTECTIVE_MODE = "active_protective_mode"
    DEGRADED_OPERATION_ONLY = "degraded_operation_only"
    RECOVERY_IN_PROGRESS = "recovery_in_progress"
    RELEASE_TO_NORMAL_OPERATION = "release_to_normal_operation"
    INSUFFICIENT_BASIS_FOR_OVERRIDE = "insufficient_basis_for_override"
    REGULATION_CONFLICT = "regulation_conflict"


class R05AuthorityLevel(str, Enum):
    NONE = "none"
    BOUNDED_MONITORING = "bounded_monitoring"
    BOUNDED_OVERRIDE = "bounded_override"


class R05InhibitedSurface(str, Enum):
    COMMUNICATION_EXPOSURE = "communication_exposure"
    INTERACTION_INTENSITY = "interaction_intensity"
    PROJECT_CONTINUATION = "project_continuation"
    PERMISSION_HARDENING = "permission_hardening"
    ESCALATION_ROUTING = "escalation_routing"


@dataclass(frozen=True, slots=True)
class R05ProtectiveTriggerInput:
    trigger_id: str
    trigger_kind: str = "protective_signal"
    threat_structure_score: float = 0.0
    load_pressure_score: float = 0.0
    o04_coercive_structure_present: bool = False
    o04_rupture_risk_present: bool = False
    o04_directionality_ambiguous: bool = False
    o04_legitimacy_underconstrained: bool = False
    p01_project_continuation_active: bool = False
    p01_blocked_or_conflicted: bool = False
    g08_appraisal_significance_hint: float | None = None
    communication_surface_exposed: bool = True
    project_continuation_requested: bool = True
    escalation_route_available: bool = False
    permission_hardening_available: bool = True
    tone_only_discomfort: bool = False
    counterevidence_present: bool = False
    release_signal_present: bool = False
    provenance: str = "r05.protective_trigger"


@dataclass(frozen=True, slots=True)
class R05ProtectiveDirective:
    directive_id: str
    protective_mode: R05ProtectiveMode
    authority_level: R05AuthorityLevel
    inhibited_surfaces: tuple[R05InhibitedSurface, ...]
    project_override_active: bool
    release_pending: bool
    release_conditions: tuple[str, ...]
    recheck_after_ticks: int
    reason: str


@dataclass(frozen=True, slots=True)
class R05ProtectiveRegulationState:
    regulation_id: str
    protective_mode: R05ProtectiveMode
    authority_level: R05AuthorityLevel
    trigger_ids: tuple[str, ...]
    trigger_count: int
    structural_basis_score: float
    inhibited_surfaces: tuple[R05InhibitedSurface, ...]
    project_override_active: bool
    override_scope: str
    release_pending: bool
    release_conditions: tuple[str, ...]
    release_satisfied: bool
    recovery_recheck_due: bool
    hysteresis_hold_ticks: int
    regulation_conflict: bool
    insufficient_basis_for_override: bool
    justification_links: tuple[str, ...]
    provenance: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class R05ProtectiveGateDecision:
    protective_state_consumer_ready: bool
    surface_inhibition_consumer_ready: bool
    release_contract_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class R05ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    r05_first_slice_only: bool
    a05_not_implemented: bool
    v_line_not_implemented: bool
    p04_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class R05Telemetry:
    regulation_id: str
    tick_index: int
    protective_mode: R05ProtectiveMode
    authority_level: R05AuthorityLevel
    trigger_count: int
    inhibited_surface_count: int
    override_active: bool
    release_pending: bool
    regulation_conflict: bool
    insufficient_basis_for_override: bool
    downstream_consumer_ready: bool
    project_override_active: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class R05ProtectiveResult:
    state: R05ProtectiveRegulationState
    gate: R05ProtectiveGateDecision
    scope_marker: R05ScopeMarker
    telemetry: R05Telemetry
    reason: str
