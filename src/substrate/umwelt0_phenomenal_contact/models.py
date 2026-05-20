from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    NOOP = "noop"


class BlockedContactReason(str, Enum):
    PROTECTED_EVAL_ONLY = "protected_eval_only"
    SCENARIO_LABEL_ONLY = "scenario_label_only"
    MISSING_SOURCE_REFS = "missing_source_refs"
    BACKEND_TRUTH_DETECTED = "backend_truth_detected"
    WORLDSTATE_DETECTED = "worldstate_detected"
    TRUE_RECIPE_DETECTED = "true_recipe_detected"
    FULL_MAP_DETECTED = "full_map_detected"
    HIDDEN_IDENTITY_DETECTED = "hidden_identity_detected"
    ACTION_POLICY_DETECTED = "action_policy_detected"
    EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER = "effect_without_request_or_passive_marker"
    LOSSINESS_REQUIRED_BUT_MISSING = "lossiness_required_but_missing"
    UNSUPPORTED_BACKEND_SPECIFIC_FIELD = "unsupported_backend_specific_field"
    EMPTY_CONTACT = "empty_contact"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SourceRef:
    source_id: str
    source_kind: str
    public: bool
    protected_eval: bool
    scenario_label: bool
    provider_ref: str | None = None
    raw_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id or not self.source_kind:
            raise ValueError("SourceRef requires source_id/source_kind")


@dataclass(frozen=True, slots=True)
class LossinessMarker:
    marker_id: str
    kind: str
    description: str
    severity: float | None = None

    def __post_init__(self) -> None:
        if not self.marker_id:
            raise ValueError("LossinessMarker.marker_id is required")


@dataclass(frozen=True, slots=True)
class UncertaintyMarker:
    marker_id: str
    kind: str
    description: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.marker_id:
            raise ValueError("UncertaintyMarker.marker_id is required")


@dataclass(frozen=True, slots=True)
class ContactAuthorityFlags:
    can_select_action: bool = False
    can_publish_ap01: bool = False
    can_execute_world_action: bool = False
    can_claim_fact: bool = False
    can_confirm_cause: bool = False
    can_assign_value: bool = False
    can_mature_recipe: bool = False
    can_mature_skill: bool = False
    can_claim_automation: bool = False
    can_expose_hidden_truth: bool = False

    def has_violation(self) -> bool:
        return any(
            (
                self.can_select_action,
                self.can_publish_ap01,
                self.can_execute_world_action,
                self.can_claim_fact,
                self.can_confirm_cause,
                self.can_assign_value,
                self.can_mature_recipe,
                self.can_mature_skill,
                self.can_claim_automation,
                self.can_expose_hidden_truth,
            )
        )


@dataclass(frozen=True, slots=True)
class ContactRef:
    ref_id: str
    ref_kind: str
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    blocked_reason: BlockedContactReason | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ref_id or not self.ref_kind:
            raise ValueError("ContactRef requires ref_id/ref_kind")


@dataclass(frozen=True, slots=True)
class ActionSurfaceDeclaration:
    surface_ref: str
    action_kind: str
    target_ref: str | None = None
    required_capability_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    provided_capability: str | None = None
    learned_by_subject: bool | None = None
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    selected_action_ref: str | None = None
    action_policy_ref: str | None = None
    preferred_route_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.surface_ref or not self.action_kind:
            raise ValueError("ActionSurfaceDeclaration requires surface_ref/action_kind")


@dataclass(frozen=True, slots=True)
class WorldEffectFrame:
    effect_ref: str
    effect_kind: str
    request_ref: str | None = None
    passive_event_ref: str | None = None
    public_delta_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    blocked_reason: BlockedContactReason | None = None
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    fact_claimed: bool = False
    cause_confirmed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False

    def __post_init__(self) -> None:
        if not self.effect_ref or not self.effect_kind:
            raise ValueError("WorldEffectFrame requires effect_ref/effect_kind")


@dataclass(frozen=True, slots=True)
class ContactConformanceCounters:
    accepted_ref_count: int = 0
    blocked_ref_count: int = 0
    missing_source_ref_count: int = 0
    hidden_eval_block_count: int = 0
    scenario_label_block_count: int = 0
    backend_truth_block_count: int = 0
    worldstate_block_count: int = 0
    true_recipe_block_count: int = 0
    full_map_block_count: int = 0
    action_policy_block_count: int = 0
    lossiness_missing_count: int = 0
    effect_without_request_or_passive_count: int = 0
    authority_violation_count: int = 0


@dataclass(frozen=True, slots=True)
class WorldContactFrame:
    frame_id: str
    tick_id: str | None
    provider_refs: tuple[str, ...]
    public_observation_refs: tuple[str, ...]
    public_effect_refs: tuple[str, ...]
    passive_event_refs: tuple[str, ...]
    action_surface_refs: tuple[str, ...]
    effect_surface_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    blocked_contact_reasons: tuple[BlockedContactReason, ...]
    authority_flags: ContactAuthorityFlags
    hidden_eval_used: bool
    scenario_label_used: bool
    backend_truth_excluded: bool
    validation_status: ValidationStatus
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    mature_recipe_claimed: bool = False
    automation_claimed: bool = False
    value_assigned: bool = False


@dataclass(frozen=True, slots=True)
class PhenomenalContactFrame:
    frame_id: str
    tick_id: str | None
    provider_refs: tuple[str, ...]
    public_observation_refs: tuple[str, ...]
    public_effect_refs: tuple[str, ...]
    passive_event_refs: tuple[str, ...]
    action_surface_refs: tuple[str, ...]
    effect_surface_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    blocked_contact_reasons: tuple[BlockedContactReason, ...]
    authority_flags: ContactAuthorityFlags
    hidden_eval_used: bool
    scenario_label_used: bool
    backend_truth_excluded: bool
    validation_status: ValidationStatus
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    mature_recipe_claimed: bool = False
    automation_claimed: bool = False
    value_assigned: bool = False


@dataclass(frozen=True, slots=True)
class ContactBuildInput:
    frame_id: str
    tick_id: str | None
    provider_refs: tuple[str, ...] = ()
    public_observation_refs: tuple[str, ...] = ()
    public_effect_refs: tuple[str, ...] = ()
    passive_event_refs: tuple[str, ...] = ()
    action_surfaces: tuple[ActionSurfaceDeclaration, ...] = ()
    effect_frames: tuple[WorldEffectFrame, ...] = ()
    residue_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    source_refs: tuple[SourceRef, ...] = ()
    lossiness_markers: tuple[LossinessMarker, ...] = ()
    uncertainty_markers: tuple[UncertaintyMarker, ...] = ()
    prior_contact_frame_refs: tuple[str, ...] = ()
    ap01_request_refs: tuple[str, ...] = ()
    backend_public_delta_refs: tuple[str, ...] = ()
    contact_refs: tuple[ContactRef, ...] = ()
    protected_eval_present: bool = False
    scenario_label_present: bool = False
    backend_truth_present: bool = False
    worldstate_payload_present: bool = False
    true_recipe_present: bool = False
    full_map_present: bool = False
    hidden_identity_present: bool = False
    backend_specific_fields: tuple[str, ...] = ()
    requires_lossiness_marker: bool = False
    disabled: bool = False


@dataclass(frozen=True, slots=True)
class ContactConformanceResult:
    phenomenal_contact_frame: PhenomenalContactFrame
    world_contact_frame: WorldContactFrame
    counters: ContactConformanceCounters
    blocked_reasons: tuple[BlockedContactReason, ...]
    accepted_refs: tuple[str, ...]
    blocked_refs: tuple[str, ...]

