from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class T04FocusTargetStatus(str, Enum):
    FOCUS = "focus"
    PERIPHERAL = "peripheral"
    MIXED = "mixed"
    PROVISIONAL = "provisional"


class T04AttentionOwner(str, Enum):
    SELF_GUIDED = "self_guided"
    VALIDITY_GUARDED = "validity_guarded"
    MIXED_OR_PROVISIONAL = "mixed_or_provisional"
    UNASSIGNED = "unassigned"


class T04FocusMode(str, Enum):
    SINGLE_FOCUS = "single_focus"
    GUARDED_SINGLE_FOCUS = "guarded_single_focus"
    SPLIT_FOCUS = "split_focus"
    PERIPHERAL_SCAN = "peripheral_scan"


class T04ReportabilityStatus(str, Enum):
    REPORTABLE_STABLE = "reportable_stable"
    REPORTABLE_PROVISIONAL = "reportable_provisional"
    NOT_REPORTABLE = "not_reportable"


class ForbiddenT04Shortcut(str, Enum):
    HIGHEST_SALIENCE_AS_ATTENTION_SCHEMA = "highest_salience_as_attention_schema"
    OWNERSHIP_DROPPED_FROM_EXPORT = "ownership_dropped_from_export"
    PERIPHERAL_UNCERTAINTY_COLLAPSED = "peripheral_uncertainty_collapsed"
    REPORTABILITY_OVERSTATED_WHEN_UNSTABLE = "reportability_overstated_when_unstable"


@dataclass(frozen=True, slots=True)
class T04AttentionTarget:
    target_id: str
    source_hypothesis_id: str | None
    prominence_score: float
    owner_confidence: float
    status: T04FocusTargetStatus
    provenance: str


@dataclass(frozen=True, slots=True)
class T04AttentionSchemaState:
    schema_id: str
    source_t03_competition_id: str
    focus_targets: tuple[T04AttentionTarget, ...]
    peripheral_targets: tuple[T04AttentionTarget, ...]
    attention_owner: T04AttentionOwner
    focus_mode: T04FocusMode
    control_estimate: float
    stability_estimate: float
    redirect_cost: float
    reportability_status: T04ReportabilityStatus
    source_authority_tags: tuple[str, ...]
    source_lineage: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class T04GateDecision:
    focus_ownership_consumer_ready: bool
    reportable_focus_consumer_ready: bool
    peripheral_preservation_ready: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class T04ScopeMarker:
    scope: str
    rt01_contour_only: bool
    t04_first_slice_only: bool
    o01_implemented: bool
    o02_implemented: bool
    o03_implemented: bool
    full_attention_line_implemented: bool
    repo_wide_adoption: bool
    reason: str


@dataclass(frozen=True, slots=True)
class T04Telemetry:
    schema_id: str
    source_t03_competition_id: str
    focus_targets_count: int
    peripheral_targets_count: int
    attention_owner: T04AttentionOwner
    focus_mode: T04FocusMode
    control_estimate: float
    stability_estimate: float
    redirect_cost: float
    reportability_status: T04ReportabilityStatus
    focus_ownership_consumer_ready: bool
    reportable_focus_consumer_ready: bool
    peripheral_preservation_ready: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class T04AttentionSchemaResult:
    state: T04AttentionSchemaState
    gate: T04GateDecision
    scope_marker: T04ScopeMarker
    telemetry: T04Telemetry
    reason: str
