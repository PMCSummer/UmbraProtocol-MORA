from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidateSet,
)


class ACP01DecisionStatus(str, Enum):
    PROPOSED = "proposed"
    NO_CANDIDATE = "no_candidate"
    BLOCKED = "blocked"
    REVALIDATION_REQUIRED = "revalidation_required"
    INSUFFICIENT_BASIS = "insufficient_basis"
    UNSAFE_BASIS = "unsafe_basis"
    MULTIPLE_CANDIDATES_ABSTAINED = "multiple_candidates_abstained"


class ACP01CapabilityStatus(str, Enum):
    AVAILABLE = "available"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"
    INSUFFICIENT = "insufficient"


class ACP01ExecutionBoundary(str, Enum):
    CANDIDATE_ONLY = "candidate_only"


@dataclass(frozen=True, slots=True)
class ACP01ObservationBasis:
    observation_id: str
    body_ref: str
    location_ref: str
    orientation: str
    inventory_ref: str
    visible_object_refs: tuple[str, ...]
    action_surface_refs: tuple[str, ...]
    previous_effect_refs: tuple[str, ...]
    inventory_item_refs: tuple[str, ...] = ()
    inventory_item_counts: dict[str, int] = field(default_factory=dict)
    public_only: bool = True

    def __post_init__(self) -> None:
        if not self.observation_id or not self.body_ref or not self.location_ref or not self.inventory_ref:
            raise ValueError("ACP01ObservationBasis requires observation/body/location/inventory refs")
        if not self.public_only:
            raise ValueError("ACP01ObservationBasis must remain public_only")


@dataclass(frozen=True, slots=True)
class ACP01InternalDriveBasis:
    drive_ref: str
    drive_kind: str
    resource_or_goal_ref: str | None
    urgency_level: float
    source_ref: str
    drive_class: str | None = None
    target_object_refs: tuple[str, ...] = ()
    target_affordance_refs: tuple[str, ...] = ()
    target_resource_refs: tuple[str, ...] = ()
    allowed_action_kinds: tuple[str, ...] = ()
    required_capability_refs: tuple[str, ...] = ()
    relevance_basis_refs: tuple[str, ...] = ()
    is_permission: bool = False
    is_action: bool = False

    def __post_init__(self) -> None:
        if not self.drive_ref or not self.drive_kind or not self.source_ref:
            raise ValueError("ACP01InternalDriveBasis requires drive_ref/drive_kind/source_ref")
        if self.is_permission or self.is_action:
            raise ValueError("ACP01InternalDriveBasis cannot be permission/action by itself")


@dataclass(frozen=True, slots=True)
class ACP01VisibleObjectBasis:
    object_ref: str
    object_kind: str
    location_ref: str
    public_properties: dict[str, object]
    confidence: float
    claim_not_fact: bool = False
    public_only: bool = True

    def __post_init__(self) -> None:
        if not self.object_ref or not self.object_kind or not self.location_ref:
            raise ValueError("ACP01VisibleObjectBasis requires object_ref/object_kind/location_ref")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("ACP01VisibleObjectBasis.confidence must be between 0 and 1")
        if not self.public_only:
            raise ValueError("ACP01VisibleObjectBasis must remain public_only")


@dataclass(frozen=True, slots=True)
class ACP01ActionSurfaceBasis:
    surface_ref: str
    surface_kind: str
    target_ref: str | None
    action_kinds: tuple[str, ...]
    is_permission: bool = False
    is_selection: bool = False
    is_execution: bool = False

    def __post_init__(self) -> None:
        if not self.surface_ref or not self.surface_kind or not self.action_kinds:
            raise ValueError("ACP01ActionSurfaceBasis requires surface_ref/surface_kind/action_kinds")
        if self.is_permission or self.is_selection or self.is_execution:
            raise ValueError("ACP01ActionSurfaceBasis cannot encode permission/selection/execution")


@dataclass(frozen=True, slots=True)
class ACP01CapabilityBasis:
    capability_ref: str
    capability_kind: str
    target_ref: str | None
    status: ACP01CapabilityStatus
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.capability_ref or not self.capability_kind:
            raise ValueError("ACP01CapabilityBasis requires capability_ref/capability_kind")


@dataclass(frozen=True, slots=True)
class ACP01EffectFeedbackBasis:
    effect_ref: str
    status: str
    correlation_status: str
    residue_refs: tuple[str, ...] = ()
    used_as_success_oracle: bool = False

    def __post_init__(self) -> None:
        if not self.effect_ref:
            raise ValueError("ACP01EffectFeedbackBasis.effect_ref is required")
        if self.used_as_success_oracle:
            raise ValueError("ACP01EffectFeedbackBasis cannot be used as success oracle")


@dataclass(frozen=True, slots=True)
class ACP01CandidateProductionInput:
    tick_ref: str
    observation_basis: ACP01ObservationBasis
    internal_drive_bases: tuple[ACP01InternalDriveBasis, ...]
    visible_object_bases: tuple[ACP01VisibleObjectBasis, ...]
    action_surface_bases: tuple[ACP01ActionSurfaceBasis, ...]
    capability_bases: tuple[ACP01CapabilityBasis, ...]
    effect_feedback_bases: tuple[ACP01EffectFeedbackBasis, ...]
    private_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    source: str = "acp01_subject_visible_basis"

    def __post_init__(self) -> None:
        if not self.tick_ref:
            raise ValueError("ACP01CandidateProductionInput.tick_ref is required")
        if not self.private_eval_excluded:
            raise ValueError("ACP01CandidateProductionInput requires private_eval_excluded=True")
        if not self.scenario_label_excluded:
            raise ValueError("ACP01CandidateProductionInput requires scenario_label_excluded=True")


@dataclass(frozen=True, slots=True)
class ACP01ActionCandidateProposal:
    candidate_id: str
    action_kind: str
    target_ref: str | None
    args: dict[str, object]
    intended_effect: str
    basis_refs: tuple[str, ...]
    missing_basis: tuple[str, ...]
    blocked_basis: tuple[str, ...]
    confidence: float
    revalidation_required: bool
    execution_boundary: ACP01ExecutionBoundary = ACP01ExecutionBoundary.CANDIDATE_ONLY
    no_scenario_label_used: bool = True
    no_eval_only_used: bool = True
    no_private_world_used: bool = True

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.action_kind or not self.intended_effect:
            raise ValueError("ACP01ActionCandidateProposal requires candidate_id/action_kind/intended_effect")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("ACP01ActionCandidateProposal.confidence must be between 0 and 1")
        if self.execution_boundary is not ACP01ExecutionBoundary.CANDIDATE_ONLY:
            raise ValueError("ACP01 proposals must remain candidate_only")
        if not self.no_scenario_label_used or not self.no_eval_only_used or not self.no_private_world_used:
            raise ValueError("ACP01 proposals must preserve no-scenario/no-eval/no-private boundaries")


@dataclass(frozen=True, slots=True)
class ACP01CandidateProductionDecision:
    decision_id: str
    status: ACP01DecisionStatus
    reason_codes: tuple[str, ...]
    proposal: ACP01ActionCandidateProposal | None
    missing_requirements: tuple[str, ...] = ()
    blocked_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ACP01CandidateProductionTelemetry:
    decision_count: int
    proposal_count: int
    proposed_count: int
    blocked_count: int
    revalidation_required_count: int
    unsafe_basis_count: int
    insufficient_basis_count: int
    no_candidate_count: int
    private_eval_excluded: bool
    scenario_label_excluded: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ACP01ScopeMarker:
    scope: str
    candidate_production_only: bool
    no_publication_authority: bool
    no_execution_authority: bool
    no_world_submission_authority: bool
    no_phase_override_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ACP01CandidateProductionResult:
    tick_ref: str
    decisions: tuple[ACP01CandidateProductionDecision, ...]
    proposal_count: int
    proposed_count: int
    blocked_count: int
    revalidation_required_count: int
    unsafe_basis_count: int
    candidate_set_for_ap01: AP01ActionPublicationCandidateSet | None
    telemetry: ACP01CandidateProductionTelemetry
    scope_marker: ACP01ScopeMarker
    reason: str
