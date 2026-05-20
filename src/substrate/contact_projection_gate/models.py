from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from substrate.ab_subject_tick_integration import ABLiveTickInput
from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    ContactAuthorityFlags,
    ContactConformanceResult,
    WorldEffectFrame,
)


class ContactChannelKind(str, Enum):
    SYMBOLIC_WORLD = "symbolic_world"
    KNOWLEDGE_AFFORDANCE = "knowledge_affordance"
    LANGUAGE_CONTACT = "language_contact"
    SENSORY_CANDIDATE = "sensory_candidate"
    BODY_INTERNAL = "body_internal"
    SOCIAL_EXTERNAL_ACTOR = "social_external_actor"
    SYSTEM_STATUS = "system_status"
    UNKNOWN_PUBLIC = "unknown_public"


@dataclass(frozen=True, slots=True)
class ContactProjectionConfig:
    enable_ab_projection: bool = True
    enable_acp01_projection: bool = True
    enable_ap01_lineage_projection: bool = True
    strict_public_basis_only: bool = True
    reject_hidden_or_scenario_basis: bool = True
    reject_action_policy: bool = True
    reject_truth_oracle: bool = True
    allow_unknown_public_channels: bool = True
    max_projected_refs_per_channel: int = 32
    max_action_surface_basis_items: int = 16
    no_action_authority: bool = True
    no_publication_authority: bool = True
    no_execution_authority: bool = True


@dataclass(frozen=True, slots=True)
class ProjectedABInput:
    public_observation_refs: tuple[str, ...] = ()
    public_effect_refs: tuple[str, ...] = ()
    passive_public_event_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    ap01_request_refs: tuple[str, ...] = ()
    action_effect_refs: tuple[str, ...] = ()
    public_basis_refs: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    channel_refs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ab_live_input_candidate: ABLiveTickInput | None = None


@dataclass(frozen=True, slots=True)
class ProjectedACP01Basis:
    action_surface_basis_refs: tuple[str, ...] = ()
    pressure_basis_refs: tuple[str, ...] = ()
    capability_basis_refs: tuple[str, ...] = ()
    target_context_refs: tuple[str, ...] = ()
    resource_context_refs: tuple[str, ...] = ()
    station_context_refs: tuple[str, ...] = ()
    entity_context_refs: tuple[str, ...] = ()
    map_context_refs: tuple[str, ...] = ()
    knowledge_hint_refs: tuple[str, ...] = ()
    language_hint_refs: tuple[str, ...] = ()
    sensory_candidate_refs: tuple[str, ...] = ()
    residue_constraint_refs: tuple[str, ...] = ()
    uncertainty_constraint_refs: tuple[str, ...] = ()
    public_basis_refs: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    channel_refs: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProjectedAP01Lineage:
    request_refs: tuple[str, ...] = ()
    effect_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    public_basis_refs: tuple[str, ...] = ()
    correlation_refs: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectionTrace:
    stage_name: str
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    channel_kind: ContactChannelKind | None
    decision: str
    blocked_reason: str | None
    authority_flags: ContactAuthorityFlags
    note: str = ""


@dataclass(frozen=True, slots=True)
class ProjectionCounters:
    contact_ref_count: int = 0
    projected_ab_ref_count: int = 0
    projected_acp01_basis_count: int = 0
    projected_ap01_lineage_count: int = 0
    blocked_ref_count: int = 0
    blocked_hidden_eval_count: int = 0
    blocked_scenario_label_count: int = 0
    blocked_action_policy_count: int = 0
    blocked_truth_oracle_count: int = 0
    unknown_channel_count: int = 0
    bounded_ref_limit_triggered_count: int = 0
    authority_violation_count: int = 0


@dataclass(frozen=True, slots=True)
class ProjectedSubjectTickInputs:
    projection_id: str
    source_contact_frame_ref: str
    projection_status: str
    projected_ab_input: ProjectedABInput
    projected_acp01_basis: ProjectedACP01Basis
    projected_ap01_lineage: ProjectedAP01Lineage
    public_basis_refs: tuple[str, ...]
    blocked_projection_reasons: tuple[str, ...]
    authority_flags: ContactAuthorityFlags
    counters: ProjectionCounters
    traces: tuple[ProjectionTrace, ...]
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    value_assigned: bool = False
    mature_recipe_claimed: bool = False
    mature_skill_claimed: bool = False
    automation_claimed: bool = False


@dataclass(frozen=True, slots=True)
class ContactProjectionInput:
    projection_id: str
    contact_result: ContactConformanceResult
    channel_overrides: dict[str, ContactChannelKind] = field(default_factory=dict)
    world_effect_frames: tuple[WorldEffectFrame, ...] = ()
    action_surface_declarations: tuple[ActionSurfaceDeclaration, ...] = ()
    prior_frontier_refs: tuple[str, ...] = ()
    prior_ab_state_refs: tuple[str, ...] = ()
    recipe_candidate_refs: tuple[str, ...] = ()
    precursor_candidate_refs: tuple[str, ...] = ()
    value_chain_refs: tuple[str, ...] = ()
    factory_chain_refs: tuple[str, ...] = ()
    p13_credit_refs: tuple[str, ...] = ()
    p14_station_affordance_refs: tuple[str, ...] = ()

