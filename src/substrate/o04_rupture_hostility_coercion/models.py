from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class O04DynamicType(str, Enum):
    DISAGREEMENT_ONLY = "disagreement_only"
    HARD_BARGAINING = "hard_bargaining"
    BOUNDARY_ENFORCEMENT_BOUNDED = "boundary_enforcement_bounded"
    HOSTILITY_CANDIDATE = "hostility_candidate"
    RUPTURE_RISK = "rupture_risk"
    RUPTURE_ACTIVE = "rupture_active"
    COERCIVE_PRESSURE_CANDIDATE = "coercive_pressure_candidate"
    FORCED_COMPLIANCE_CANDIDATE = "forced_compliance_candidate"
    EXCLUSION_SEQUENCE_CANDIDATE = "exclusion_sequence_candidate"
    RETALIATORY_ESCALATION_CANDIDATE = "retaliatory_escalation_candidate"
    AMBIGUOUS_PRESSURE = "ambiguous_pressure"


class O04LeverageSurfaceKind(str, Enum):
    RESOURCE_CONTROL = "resource_control"
    PERMISSION_CONTROL = "permission_control"
    SANCTION_THREAT = "sanction_threat"
    ACCESS_WITHDRAWAL = "access_withdrawal"
    DEPENDENCY_WITHDRAWAL = "dependency_withdrawal"
    BLOCKED_OPTION = "blocked_option"
    COMMITMENT_LEVERAGE = "commitment_leverage"
    ROLE_AUTHORITY = "role_authority"
    EXCLUSION_CHANNEL = "exclusion_channel"
    NONE_DETECTED = "none_detected"


class O04DirectionalityKind(str, Enum):
    ONE_WAY = "one_way"
    MUTUAL = "mutual"
    ASYMMETRIC_MUTUAL = "asymmetric_mutual"
    CHAIN_LIKE = "chain_like"
    DIRECTIONALITY_AMBIGUOUS = "directionality_ambiguous"


class O04LegitimacyHintStatus(str, Enum):
    LEGITIMACY_SUPPORTED = "legitimacy_supported"
    LEGITIMACY_CONTESTED = "legitimacy_contested"
    LEGITIMACY_ABSENT = "legitimacy_absent"
    LEGITIMACY_UNKNOWN = "legitimacy_unknown"


class O04SeverityBand(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class O04CertaintyBand(str, Enum):
    WEAK = "weak"
    BOUNDED = "bounded"
    STRONG = "strong"


class O04RuptureStatus(str, Enum):
    NO_RUPTURE_BASIS = "no_rupture_basis"
    RUPTURE_RISK_ONLY = "rupture_risk_only"
    RUPTURE_ACTIVE_CANDIDATE = "rupture_active_candidate"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    DEESCALATED_BUT_NOT_CLOSED = "deescalated_but_not_closed"


@dataclass(frozen=True, slots=True)
class O04InteractionEventInput:
    event_id: str
    actor_ref: str | None = None
    target_ref: str | None = None
    event_kind: str = "interaction_event"
    speech_act_kind: str | None = None
    blocked_option_present: bool = False
    threatened_loss_present: bool = False
    resource_control_present: bool = False
    access_withdrawal_present: bool = False
    dependency_surface_present: bool = False
    sanction_power_present: bool = False
    consent_marker: bool = False
    refusal_marker: bool = False
    commitment_break_marker: bool = False
    exclusion_marker: bool = False
    repair_attempt_marker: bool = False
    escalation_shift_marker: bool = False
    legitimacy_hint_status: O04LegitimacyHintStatus = O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN
    project_link_ref: str | None = None
    history_depth_band: str = "single"
    evidence_ref: str | None = None
    counterevidence_ref: str | None = None
    provenance: str = "o04.interaction_event"


@dataclass(frozen=True, slots=True)
class O04DynamicLink:
    link_id: str
    actor_ref: str | None
    target_ref: str | None
    dynamic_type: O04DynamicType
    leverage_surface: O04LeverageSurfaceKind
    blocked_option_ref: str | None
    threatened_outcome_ref: str | None
    directionality_kind: O04DirectionalityKind
    legitimacy_hint_status: O04LegitimacyHintStatus
    severity_band: O04SeverityBand
    certainty_band: O04CertaintyBand
    evidence_refs: tuple[str, ...]
    counterevidence_refs: tuple[str, ...]
    temporal_scope: str
    status: str
    provenance: str


@dataclass(frozen=True, slots=True)
class O04DynamicModel:
    interaction_model_id: str
    agent_refs: tuple[str, ...]
    directional_links: tuple[O04DynamicLink, ...]
    rupture_status: O04RuptureStatus
    hostility_candidates: tuple[str, ...]
    coercion_candidates: tuple[str, ...]
    retaliation_candidates: tuple[str, ...]
    counterevidence_summary: tuple[str, ...]
    uncertainty_markers: tuple[str, ...]
    no_safe_dynamic_claim: bool
    dependency_model_underconstrained: bool
    tone_shortcut_forbidden_applied: bool
    legitimacy_boundary_underconstrained: bool
    justification_links: tuple[str, ...]
    provenance: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class O04DynamicGateDecision:
    dynamic_contract_consumer_ready: bool
    directionality_consumer_ready: bool
    protective_handoff_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class O04ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    o04_first_slice_only: bool
    r05_not_implemented: bool
    v_line_not_implemented: bool
    p04_not_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class O04Telemetry:
    interaction_model_id: str
    tick_index: int
    dynamic_type: O04DynamicType
    rupture_status: O04RuptureStatus
    severity_band: O04SeverityBand
    certainty_band: O04CertaintyBand
    directionality_kind: O04DirectionalityKind
    leverage_surface: O04LeverageSurfaceKind
    legitimacy_hint_status: O04LegitimacyHintStatus
    coercion_candidate_count: int
    hostility_candidate_count: int
    no_safe_dynamic_claim: bool
    dependency_model_underconstrained: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class O04DynamicResult:
    state: O04DynamicModel
    gate: O04DynamicGateDecision
    scope_marker: O04ScopeMarker
    telemetry: O04Telemetry
    reason: str
