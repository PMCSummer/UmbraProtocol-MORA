from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from substrate.umwelt0_phenomenal_contact import ContactAuthorityFlags


class UMWELTSChannelKind(str, Enum):
    SYMBOLIC_WORLD = "symbolic_world"
    KNOWLEDGE_AFFORDANCE = "knowledge_affordance"
    LANGUAGE_CONTACT = "language_contact"
    SENSORY_CANDIDATE = "sensory_candidate"
    BODY_INTERNAL = "body_internal"
    SOCIAL_EXTERNAL_ACTOR = "social_external_actor"
    SYSTEM_STATUS = "system_status"
    UNKNOWN_PUBLIC = "unknown_public"


class UMWELTSRefKind(str, Enum):
    RESOURCE = "resource"
    STATION = "station"
    ENTITY = "entity"
    MAP_SITE = "map_site"
    INVENTORY = "inventory"
    ROUTE_SEGMENT = "route_segment"
    HAZARD = "hazard"
    EFFECT = "effect"
    ACTION_SURFACE = "action_surface"
    KNOWLEDGE_HINT = "knowledge_hint"
    LANGUAGE_UTTERANCE = "language_utterance"
    SPEECH_ACT_CANDIDATE = "speech_act_candidate"
    SENSORY_CANDIDATE = "sensory_candidate"
    BODY_PRESSURE = "body_pressure"
    SYSTEM_STATUS = "system_status"
    PROVIDER_CLAIM = "provider_claim"
    OBJECTIVE_HINT = "objective_hint"
    CONFLICT = "conflict"
    RESIDUE = "residue"
    UNCERTAINTY = "uncertainty"
    LOSSINESS = "lossiness"


class UMWELTSValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ContactSourceRequirement:
    required: bool = True
    source_refs: tuple[str, ...] = ()
    allow_transformed_public_ref: bool = True


@dataclass(frozen=True, slots=True)
class ContactLossinessRequirement:
    required_when_partial: bool = False
    lossiness_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ContactUncertaintyRequirement:
    required_when_ambiguous: bool = False
    uncertainty_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ContactChannelDeclaration:
    channel_id: str
    channel_kind: UMWELTSChannelKind
    public: bool
    requires_source_refs: bool
    requires_lossiness_when_partial: bool
    allows_unknown_refs: bool
    max_refs: int
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    provider_ref: str | None = None
    blocked_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PublicRefDeclaration:
    ref_id: str
    ref_kind: UMWELTSRefKind
    channel_id: str
    source_requirements: ContactSourceRequirement
    uncertainty_policy: ContactUncertaintyRequirement = field(default_factory=ContactUncertaintyRequirement)
    lossiness_policy: ContactLossinessRequirement = field(default_factory=ContactLossinessRequirement)
    allowed_metadata_keys: tuple[str, ...] = ()
    forbidden_markers: tuple[str, ...] = ()
    backend_ref: str | None = None
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)


@dataclass(frozen=True, slots=True)
class ActionSurfaceSpec:
    surface_id: str
    action_kind: str
    channel_id: str
    target_ref_kinds: tuple[UMWELTSRefKind, ...] = ()
    required_capability_ref_kinds: tuple[UMWELTSRefKind, ...] = ()
    required_resource_ref_kinds: tuple[UMWELTSRefKind, ...] = ()
    risk_ref_kinds: tuple[UMWELTSRefKind, ...] = ()
    source_requirements: ContactSourceRequirement = field(default_factory=ContactSourceRequirement)
    forbidden_policy_fields: tuple[str, ...] = ()
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EffectSurfaceSpec:
    effect_surface_id: str
    effect_kind: str
    channel_id: str
    request_correlated_allowed: bool
    passive_event_allowed: bool
    required_source_refs: tuple[str, ...] = ()
    required_delta_refs: tuple[str, ...] = ()
    residue_policy: tuple[str, ...] = ()
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderSurfaceSpec:
    provider_id: str
    provider_kind: str
    channel_id: str
    authority_class: str
    source_requirements: ContactSourceRequirement = field(default_factory=ContactSourceRequirement)
    hint_only: bool = True
    truth_authority: bool = False
    can_mature_recipe: bool = False
    can_assign_value: bool = False
    can_select_action: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ForbiddenPayloadRule:
    rule_id: str
    reason: str
    blocked_tokens: tuple[str, ...]
    applies_to: tuple[str, ...]
    severity: str = "blocker"


@dataclass(frozen=True, slots=True)
class ContactSpec:
    spec_id: str
    backend_family: str
    spec_version: str
    channel_declarations: tuple[ContactChannelDeclaration, ...]
    public_ref_declarations: tuple[PublicRefDeclaration, ...]
    action_surface_declarations: tuple[ActionSurfaceSpec, ...]
    effect_surface_declarations: tuple[EffectSurfaceSpec, ...]
    provider_declarations: tuple[ProviderSurfaceSpec, ...]
    source_requirements: ContactSourceRequirement
    lossiness_requirements: ContactLossinessRequirement
    uncertainty_requirements: ContactUncertaintyRequirement
    forbidden_payload_rules: tuple[ForbiddenPayloadRule, ...]
    authority_profile: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContactIR:
    ir_id: str
    source_spec_ref: str
    normalized_channels: tuple[ContactChannelDeclaration, ...]
    normalized_refs: tuple[PublicRefDeclaration, ...]
    normalized_action_surfaces: tuple[ActionSurfaceSpec, ...]
    normalized_effect_surfaces: tuple[EffectSurfaceSpec, ...]
    normalized_providers: tuple[ProviderSurfaceSpec, ...]
    blocked_items: tuple[str, ...]
    conformance_status: UMWELTSValidationStatus
    authority_flags: ContactAuthorityFlags
    counters: "ContactSpecCounters"
    traces: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UMWELT0ConstructionPlan:
    plan_id: str
    source_spec_ref: str
    source_ir_ref: str
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
    blocked_reasons: tuple[str, ...]
    authority_flags: ContactAuthorityFlags = field(default_factory=ContactAuthorityFlags)
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    backend_truth_excluded: bool = True
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    value_assigned: bool = False
    mature_recipe_claimed: bool = False
    mature_skill_claimed: bool = False
    automation_claimed: bool = False


@dataclass(frozen=True, slots=True)
class ContactSpecCounters:
    channel_count: int = 0
    ref_count: int = 0
    action_surface_count: int = 0
    effect_surface_count: int = 0
    provider_count: int = 0
    blocked_item_count: int = 0
    source_requirement_missing_count: int = 0
    lossiness_requirement_missing_count: int = 0
    forbidden_payload_count: int = 0
    backend_specific_leak_count: int = 0
    selected_action_block_count: int = 0
    true_recipe_block_count: int = 0
    full_map_block_count: int = 0
    hidden_label_block_count: int = 0
    worldstate_block_count: int = 0
    authority_violation_count: int = 0
    unknown_channel_count: int = 0
    bounded_limit_triggered_count: int = 0


@dataclass(frozen=True, slots=True)
class ContactSpecValidationResult:
    spec_id: str
    status: UMWELTSValidationStatus
    blocked_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    counters: ContactSpecCounters
    normalized_ir: ContactIR | None
    authority_flags: ContactAuthorityFlags
    conformance_trace: tuple[str, ...]
    umwelt0_construction_plan: UMWELT0ConstructionPlan | None = None
    action_request_emitted: bool = False
    world_action_emitted: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    value_assigned: bool = False
    mature_recipe_claimed: bool = False
    mature_skill_claimed: bool = False
    automation_claimed: bool = False

