from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from substrate.umwelts_symbolic_contact import ProviderSurfaceSpec


class ProviderKind(str, Enum):
    JEI_INDEX = "jei_index"
    ENCYCLOPEDIA = "encyclopedia"
    QUESTBOOK = "questbook"
    MANUAL = "manual"
    TOOLTIP = "tooltip"
    MACHINE_UI = "machine_ui"
    SCANNER = "scanner"
    STATUS_PANEL = "status_panel"
    LANGUAGE_MANUAL = "language_manual"
    EXTERNAL_ACTOR_TESTIMONY = "external_actor_testimony"
    SYSTEM_PROVIDER = "system_provider"
    UNKNOWN_PROVIDER = "unknown_provider"


class ProviderAuthorityClass(str, Enum):
    HINT = "hint"
    TESTIMONY = "testimony"
    INDEX = "index"
    UI_STATUS = "ui_status"
    QUEST_OBJECTIVE = "quest_objective"
    MACHINE_STATUS = "machine_status"
    SCANNER_CANDIDATE = "scanner_candidate"
    MANUAL_CLAIM = "manual_claim"
    CONFLICT_SOURCE = "conflict_source"
    UNKNOWN_SOURCE = "unknown_source"


class KnowledgeSlotState(str, Enum):
    LOCKED = "locked"
    UNKNOWN = "unknown"
    PARTIAL = "partial"
    VISIBLE_HINT = "visible_hint"
    PROVIDER_DECLARED = "provider_declared"
    CONFLICT = "conflict"
    BLOCKED = "blocked"
    STALE = "stale"
    INVALID = "invalid"


class KnowledgeAffordanceKind(str, Enum):
    TRANSFORMATION_HINT = "transformation_hint"
    STATION_CAPABILITY_HINT = "station_capability_hint"
    OBJECTIVE_HINT = "objective_hint"
    MACHINE_STATUS_HINT = "machine_status_hint"
    SCANNER_CANDIDATE_HINT = "scanner_candidate_hint"
    MANUAL_CLAIM_HINT = "manual_claim_hint"
    RECIPE_SLOT_HINT = "recipe_slot_hint"
    PROVIDER_INDEX_HINT = "provider_index_hint"
    LANGUAGE_TESTIMONY_HINT = "language_testimony_hint"
    CONFLICT_MARKER = "conflict_marker"


class KnowledgeSurfaceValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    NOOP = "noop"


@dataclass(frozen=True, slots=True)
class KSurfAuthorityFlags:
    can_select_action: bool = False
    can_publish_ap01: bool = False
    can_execute_world_action: bool = False
    can_claim_fact: bool = False
    can_confirm_cause: bool = False
    can_assign_value: bool = False
    can_mature_recipe: bool = False
    can_mature_transformation: bool = False
    can_mature_skill: bool = False
    can_claim_automation: bool = False
    can_claim_lived_evidence: bool = False
    can_select_goal: bool = False
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
                self.can_mature_transformation,
                self.can_mature_skill,
                self.can_claim_automation,
                self.can_claim_lived_evidence,
                self.can_select_goal,
                self.can_expose_hidden_truth,
            )
        )


@dataclass(frozen=True, slots=True)
class KnowledgeProviderRef:
    provider_id: str
    provider_kind: ProviderKind
    authority_class: ProviderAuthorityClass
    channel_ref: str
    source_refs: tuple[str, ...]
    public: bool = True
    protected_eval: bool = False
    scenario_label: bool = False
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    authority_flags: KSurfAuthorityFlags = field(default_factory=KSurfAuthorityFlags)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderClaimRef:
    claim_id: str
    provider_ref: str
    claim_kind: KnowledgeAffordanceKind
    subject_ref: str | None = None
    target_ref: str | None = None
    claim_text_ref: str | None = None
    slot_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    stale_marker: str | None = None
    authority_marker: str = "hint_only"
    blocked_reason: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LockedSlotRef:
    slot_id: str
    slot_kind: str
    provider_ref: str
    visible_basis_refs: tuple[str, ...]
    unlock_basis_refs: tuple[str, ...]
    slot_state: KnowledgeSlotState
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    blocked_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PartialSlotRef:
    slot_id: str
    slot_kind: str
    known_part_refs: tuple[str, ...]
    unknown_part_refs: tuple[str, ...]
    missing_evidence_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TransformationHintRef:
    hint_id: str
    provider_ref: str
    input_candidate_refs: tuple[str, ...]
    output_candidate_refs: tuple[str, ...]
    station_candidate_refs: tuple[str, ...]
    condition_candidate_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    maturity: bool = False
    observed_trace_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StationCapabilityHintRef:
    hint_id: str
    station_ref: str
    capability_candidate_refs: tuple[str, ...]
    required_input_candidate_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObjectiveHintRef:
    hint_id: str
    provider_ref: str
    objective_text_ref: str | None
    target_candidate_refs: tuple[str, ...]
    reward_hint_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    goal_authority: bool = False


@dataclass(frozen=True, slots=True)
class MachineStatusHintRef:
    hint_id: str
    machine_or_station_ref: str
    status_candidate_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    diagnosis_authority: bool = False


@dataclass(frozen=True, slots=True)
class ScannerCandidateHintRef:
    hint_id: str
    scanned_ref: str
    identity_candidate_refs: tuple[str, ...]
    property_candidate_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()
    identity_truth: bool = False


@dataclass(frozen=True, slots=True)
class ProviderConflictFrame:
    conflict_id: str
    provider_refs: tuple[str, ...]
    conflicting_claim_refs: tuple[str, ...]
    conflict_kind: str
    affected_slot_refs: tuple[str, ...]
    affected_hint_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    resolution_status: str = "unresolved"
    chosen_winner: str | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeSurfaceCounters:
    provider_count: int = 0
    claim_count: int = 0
    hint_count: int = 0
    locked_slot_count: int = 0
    partial_slot_count: int = 0
    conflict_count: int = 0
    blocked_provider_count: int = 0
    missing_source_ref_count: int = 0
    hidden_eval_block_count: int = 0
    scenario_label_block_count: int = 0
    oracle_payload_block_count: int = 0
    selected_action_block_count: int = 0
    value_assignment_block_count: int = 0
    mature_recipe_block_count: int = 0
    lived_evidence_block_count: int = 0
    provider_conflict_count: int = 0
    stale_or_lossy_count: int = 0
    unlock_without_public_basis_count: int = 0


@dataclass(frozen=True, slots=True)
class KnowledgeAffordanceFrame:
    frame_id: str
    provider_refs: tuple[str, ...]
    provider_claim_refs: tuple[str, ...]
    knowledge_hint_refs: tuple[str, ...]
    locked_slot_refs: tuple[str, ...]
    partial_slot_refs: tuple[str, ...]
    transformation_hint_refs: tuple[str, ...]
    station_capability_hint_refs: tuple[str, ...]
    objective_hint_refs: tuple[str, ...]
    machine_status_hint_refs: tuple[str, ...]
    scanner_candidate_hint_refs: tuple[str, ...]
    provider_conflict_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    lossiness_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    blocked_provider_reasons: tuple[str, ...]
    authority_flags: KSurfAuthorityFlags
    validation_status: KnowledgeSurfaceValidationStatus
    counters: KnowledgeSurfaceCounters
    action_request_emitted: bool = False
    action_selected: bool = False
    goal_selected: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    value_assigned: bool = False
    mature_recipe_claimed: bool = False
    mature_skill_claimed: bool = False
    automation_claimed: bool = False


@dataclass(frozen=True, slots=True)
class KnowledgeSurfaceValidationResult:
    status: KnowledgeSurfaceValidationStatus
    blocked_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    counters: KnowledgeSurfaceCounters
    frame: KnowledgeAffordanceFrame | None
    authority_flags: KSurfAuthorityFlags
    conformance_trace: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeSurfaceInput:
    frame_id: str
    provider_refs: tuple[KnowledgeProviderRef, ...] = ()
    provider_claim_refs: tuple[ProviderClaimRef, ...] = ()
    locked_slot_refs: tuple[LockedSlotRef, ...] = ()
    partial_slot_refs: tuple[PartialSlotRef, ...] = ()
    transformation_hint_refs: tuple[TransformationHintRef, ...] = ()
    station_capability_hint_refs: tuple[StationCapabilityHintRef, ...] = ()
    objective_hint_refs: tuple[ObjectiveHintRef, ...] = ()
    machine_status_hint_refs: tuple[MachineStatusHintRef, ...] = ()
    scanner_candidate_hint_refs: tuple[ScannerCandidateHintRef, ...] = ()
    residue_refs: tuple[str, ...] = ()
    from_umwelts_provider_declarations: tuple[ProviderSurfaceSpec, ...] = ()

