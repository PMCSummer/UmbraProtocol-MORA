from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MicroOperationKind(str, Enum):
    INSPECT = "inspect"
    MOVE_TOWARD = "move_toward"
    GATHER = "gather"
    PICKUP = "pickup"
    STORE = "store"
    USE_STATION = "use_station"
    PLACE_SEGMENT = "place_segment"
    REPAIR_CHECK = "repair_check"
    EAT = "eat"
    ATTACK_CANDIDATE = "attack_candidate"
    WAIT = "wait"
    COMPARE = "compare"
    SCAN = "scan"
    ASK = "ask"
    CONNECT_CANDIDATE = "connect_candidate"
    CUSTOM_PUBLIC_OPERATION = "custom_public_operation"


class MicroOperationStatus(str, Enum):
    PROPOSED = "proposed"
    BASIS_INCOMPLETE = "basis_incomplete"
    CANDIDATE_BASIS_READY = "candidate_basis_ready"
    BLOCKED = "blocked"
    REQUEST_PUBLISHED_ELSEWHERE = "request_published_elsewhere"
    EFFECT_OBSERVED = "effect_observed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNRESOLVED = "unresolved"
    RESIDUE_OPEN = "residue_open"


class MicroOperationBlockReason(str, Enum):
    MISSING_PUBLIC_PRESSURE_BASIS = "missing_public_pressure_basis"
    MISSING_TARGET_AFFORDANCE = "missing_target_affordance"
    MISSING_EXPECTED_EFFECT = "missing_expected_effect"
    MISSING_CAPABILITY_REF = "missing_capability_ref"
    MISSING_RESOURCE_REF = "missing_resource_ref"
    MISSING_RISK_REF = "missing_risk_ref"
    ACTION_SURFACE_IS_COMMAND = "action_surface_is_command"
    MACRO_ACTION_REQUIRES_DECOMPOSITION = "macro_action_requires_decomposition"
    HIDDEN_PRECONDITION_DETECTED = "hidden_precondition_detected"
    PROVIDER_HINT_AS_TRUTH_DETECTED = "provider_hint_as_truth_detected"
    QUEST_OBJECTIVE_AS_PERMISSION_DETECTED = "quest_objective_as_permission_detected"
    COST_WINNER_AS_PERMISSION_DETECTED = "cost_winner_as_permission_detected"
    RECIPE_CANDIDATE_AS_SCRIPT_DETECTED = "recipe_candidate_as_script_detected"
    EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER = "effect_without_request_or_passive_marker"
    SUCCESS_WITHOUT_EFFECT_REF = "success_without_effect_ref"
    RESIDUE_MISSING_AFTER_FAILURE = "residue_missing_after_failure"
    AP01_EMISSION_ATTEMPTED = "ap01_emission_attempted"
    WORLD_SUBMISSION_ATTEMPTED = "world_submission_attempted"


class MicroValidationStatus(str, Enum):
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    NOOP = "noop"


class MicroOperationGraphStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class Micro1AuthorityFlags:
    can_select_action: bool = False
    can_publish_ap01: bool = False
    can_execute_world_action: bool = False
    can_claim_fact: bool = False
    can_confirm_cause: bool = False
    can_assign_value: bool = False
    can_mature_recipe: bool = False
    can_mature_skill: bool = False
    can_claim_automation: bool = False
    can_claim_lived_evidence: bool = False
    can_select_goal: bool = False
    can_infer_hidden_precondition: bool = False

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
                self.can_claim_lived_evidence,
                self.can_select_goal,
                self.can_infer_hidden_precondition,
            )
        )


@dataclass(frozen=True, slots=True)
class MicroOperationBasis:
    pressure_refs: tuple[str, ...] = ()
    need_refs: tuple[str, ...] = ()
    body_pressure_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    channel_refs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    knowledge_hint_refs: tuple[str, ...] = ()
    language_testimony_refs: tuple[str, ...] = ()
    sensory_candidate_refs: tuple[str, ...] = ()
    provider_hint_refs: tuple[str, ...] = ()
    public_observation_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MicroOperationConstraintSet:
    required_capability_refs: tuple[str, ...] = ()
    required_resource_refs: tuple[str, ...] = ()
    required_tool_refs: tuple[str, ...] = ()
    required_station_refs: tuple[str, ...] = ()
    required_position_or_range_refs: tuple[str, ...] = ()
    risk_refs: tuple[str, ...] = ()
    precondition_refs: tuple[str, ...] = ()
    missing_constraint_refs: tuple[str, ...] = ()
    constraint_uncertainty_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MicroOperationExpectedEffectSet:
    expected_effect_refs: tuple[str, ...] = ()
    success_criteria_refs: tuple[str, ...] = ()
    blocked_effect_refs: tuple[str, ...] = ()
    passive_event_allowed: bool = False
    request_correlation_required: bool = True
    uncertainty_refs: tuple[str, ...] = ()
    lossiness_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MicroOperationLineage:
    operation_id: str
    pressure_ref: str | None
    target_affordance_ref: str | None
    action_surface_ref: str | None
    acp01_candidate_ref: str | None = None
    ap01_request_ref: str | None = None
    world_effect_frame_ref: str | None = None
    observed_effect_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    update_refs: tuple[str, ...] = ()
    next_pressure_refs: tuple[str, ...] = ()
    trace_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MicroOperationResidueFrame:
    residue_id: str
    operation_ref: str
    failure_or_block_reason: str
    failed_precondition_refs: tuple[str, ...] = ()
    missing_evidence_refs: tuple[str, ...] = ()
    observed_mismatch_refs: tuple[str, ...] = ()
    next_pressure_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    conflict_refs: tuple[str, ...] = ()
    downstream_blocked_claim_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MicroOperationFrame:
    operation_id: str
    operation_kind: MicroOperationKind
    status: MicroOperationStatus
    basis: MicroOperationBasis
    target_affordance_refs: tuple[str, ...] = ()
    action_surface_refs: tuple[str, ...] = ()
    constraints: MicroOperationConstraintSet = field(default_factory=MicroOperationConstraintSet)
    expected_effects: MicroOperationExpectedEffectSet = field(default_factory=MicroOperationExpectedEffectSet)
    lineage: MicroOperationLineage | None = None
    residue_frame_refs: tuple[str, ...] = ()
    update_refs: tuple[str, ...] = ()
    composition_parent_ref: str | None = None
    composition_child_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    uncertainty_refs: tuple[str, ...] = ()
    blocked_reasons: tuple[MicroOperationBlockReason, ...] = ()
    authority_flags: Micro1AuthorityFlags = field(default_factory=Micro1AuthorityFlags)
    validation_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MicroOperationGraph:
    graph_id: str
    root_pressure_refs: tuple[str, ...]
    operation_refs: tuple[str, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    verified_intermediate_refs: tuple[str, ...] = ()
    blocked_edges: tuple[tuple[str, str], ...] = ()
    residue_refs: tuple[str, ...] = ()
    unresolved_refs: tuple[str, ...] = ()
    macro_task_ref: str | None = None
    macro_task_decomposed: bool = False
    graph_status: MicroOperationGraphStatus = MicroOperationGraphStatus.UNRESOLVED
    authority_flags: Micro1AuthorityFlags = field(default_factory=Micro1AuthorityFlags)


@dataclass(frozen=True, slots=True)
class MicroOperationCounters:
    operation_count: int = 0
    ready_operation_count: int = 0
    blocked_operation_count: int = 0
    residue_count: int = 0
    missing_public_basis_count: int = 0
    macro_action_block_count: int = 0
    ap01_emission_attempt_count: int = 0
    world_submission_attempt_count: int = 0
    effect_without_request_count: int = 0
    success_without_effect_count: int = 0
    hidden_precondition_block_count: int = 0
    provider_truth_block_count: int = 0
    quest_permission_block_count: int = 0
    cost_permission_block_count: int = 0
    recipe_script_block_count: int = 0
    residue_missing_after_failure_count: int = 0
    composition_edge_count: int = 0
    unverified_intermediate_count: int = 0


@dataclass(frozen=True, slots=True)
class MicroOperationValidationResult:
    status: MicroValidationStatus
    operation_status: MicroOperationStatus | None
    blocked_reasons: tuple[MicroOperationBlockReason, ...]
    warnings: tuple[str, ...]
    counters: MicroOperationCounters
    operation: MicroOperationFrame | None
    graph: MicroOperationGraph | None
    authority_flags: Micro1AuthorityFlags
    conformance_trace: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MicroOperationInput:
    operation_id: str
    operation_kind: MicroOperationKind
    basis: MicroOperationBasis = field(default_factory=MicroOperationBasis)
    target_affordance_refs: tuple[str, ...] = ()
    action_surface_refs: tuple[str, ...] = ()
    constraints: MicroOperationConstraintSet = field(default_factory=MicroOperationConstraintSet)
    expected_effects: MicroOperationExpectedEffectSet = field(default_factory=MicroOperationExpectedEffectSet)
    lineage: MicroOperationLineage | None = None
    residue_frames: tuple[MicroOperationResidueFrame, ...] = ()
    status_hint: MicroOperationStatus = MicroOperationStatus.PROPOSED
    composition_parent_ref: str | None = None
    composition_child_refs: tuple[str, ...] = ()
    macro_task_ref: str | None = None
    metadata_refs: tuple[str, ...] = ()
    ap01_emission_attempt: bool = False
    world_submission_attempt: bool = False


@dataclass(frozen=True, slots=True)
class MicroOperationGraphInput:
    graph_id: str
    root_pressure_refs: tuple[str, ...]
    operations: tuple[MicroOperationFrame, ...]
    dependency_edges: tuple[tuple[str, str], ...]
    verified_intermediate_refs: tuple[str, ...] = ()
    macro_task_ref: str | None = None
