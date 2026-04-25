from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class V03RealizationStatus(str, Enum):
    REALIZED_CONSTRAINED = "realized_constrained"
    PARTIAL_REALIZATION_ONLY = "partial_realization_only"
    CLARIFICATION_ONLY_REALIZATION = "clarification_only_realization"
    BOUNDARY_ONLY_REALIZATION = "boundary_only_realization"
    REALIZATION_FAILED = "realization_failed"
    INSUFFICIENT_REALIZATION_BASIS = "insufficient_realization_basis"


@dataclass(frozen=True, slots=True)
class V03RealizationInput:
    input_id: str
    surface_variant: str = "default"
    selected_branch_id: str | None = None
    tamper_qualifier_locality_segment_id: str | None = None
    inject_blocked_expansion_token: str | None = None
    inject_protected_omission_token: str | None = None
    force_boundary_after_explanation: bool = False
    force_commitment_phrase: bool = False
    prefer_fluency_over_hard_constraints: bool = False
    provenance: str = "v03.realization_input"


@dataclass(frozen=True, slots=True)
class V03RealizedUtteranceArtifact:
    realization_id: str
    surface_text: str
    segment_order: tuple[str, ...]
    realized_segment_ids: tuple[str, ...]
    omitted_segment_ids: tuple[str, ...]
    source_act_ids: tuple[str, ...]
    selected_branch_id: str
    blocked_expansion_ids: tuple[str, ...]
    protected_omission_ids: tuple[str, ...]
    partial_realization_only: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class V03SurfaceSpanAlignment:
    segment_id: str
    start_index: int
    end_index: int
    realized_text: str
    source_act_ref: str
    realized: bool
    qualifier_locality_pass: bool
    ordering_pass: bool


@dataclass(frozen=True, slots=True)
class V03RealizationAlignmentMap:
    alignments: tuple[V03SurfaceSpanAlignment, ...]
    aligned_segment_count: int
    unaligned_segment_ids: tuple[str, ...]
    branch_compliance_pass: bool
    ordering_pass: bool
    qualifier_locality_pass: bool


@dataclass(frozen=True, slots=True)
class V03ConstraintSatisfactionReport:
    hard_constraint_violation_count: int
    qualifier_locality_failures: int
    blocked_expansion_leak_detected: bool
    protected_omission_violation_detected: bool
    boundary_before_explanation_required: bool
    boundary_before_explanation_satisfied: bool
    clarification_before_assertion_required: bool
    clarification_before_assertion_satisfied: bool
    branch_compliance_pass: bool
    ordering_pass: bool
    implicit_commitment_leak_detected: bool
    violation_codes: tuple[str, ...]
    satisfied_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class V03RealizationFailureState:
    failed: bool
    failure_code: str | None
    partial_realization_only: bool
    replan_required: bool
    reason: str


@dataclass(frozen=True, slots=True)
class V03RealizationGateDecision:
    realization_consumer_ready: bool
    alignment_consumer_ready: bool
    constraint_report_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class V03ScopeMarker:
    scope: str
    rt01_hosted_only: bool
    v03_first_slice_only: bool
    v_line_not_map_wide_ready: bool
    p02_not_implemented: bool
    map_wide_realization_enforcement: bool
    reason: str


@dataclass(frozen=True, slots=True)
class V03Telemetry:
    realization_id: str
    tick_index: int
    realization_status: V03RealizationStatus
    segment_count: int
    aligned_segment_count: int
    hard_constraint_violation_count: int
    qualifier_locality_failures: int
    blocked_expansion_leak_detected: bool
    protected_omission_count: int
    boundary_before_explanation_required: bool
    boundary_before_explanation_satisfied: bool
    partial_realization_only: bool
    replan_required: bool
    downstream_consumer_ready: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class V03ConstrainedRealizationResult:
    realization_status: V03RealizationStatus
    artifact: V03RealizedUtteranceArtifact
    alignment_map: V03RealizationAlignmentMap
    constraint_report: V03ConstraintSatisfactionReport
    failure_state: V03RealizationFailureState
    gate: V03RealizationGateDecision
    scope_marker: V03ScopeMarker
    telemetry: V03Telemetry
    reason: str
