from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from substrate.world_adapter import WorldAdapterInput, WorldAdapterResult
    from substrate.world_entry_contract import WorldEntryContractResult


class SubjectTickOutcome(str, Enum):
    CONTINUE = "continue"
    REPAIR = "repair"
    REVALIDATE = "revalidate"
    HALT = "halt"


class SubjectTickStepStatus(str, Enum):
    EXECUTED = "executed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class SubjectTickUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class SubjectTickExecutionStance(str, Enum):
    CONTINUE_PATH = "continue_path"
    REPAIR_PATH = "repair_path"
    REVALIDATE_PATH = "revalidate_path"
    HALT_PATH = "halt_path"


class SubjectTickCheckpointStatus(str, Enum):
    ALLOWED = "allowed"
    ENFORCED_DETOUR = "enforced_detour"
    BLOCKED = "blocked"


class SubjectTickRestrictionCode(StrEnum):
    FIXED_ORDER_MUST_BE_READ = "fixed_order_must_be_read"
    R_GATE_MUST_BE_READ = "r_gate_must_be_read"
    C01_GATE_MUST_BE_READ = "c01_gate_must_be_read"
    C02_GATE_MUST_BE_READ = "c02_gate_must_be_read"
    C03_GATE_MUST_BE_READ = "c03_gate_must_be_read"
    C04_GATE_MUST_BE_READ = "c04_gate_must_be_read"
    C05_GATE_MUST_BE_READ = "c05_gate_must_be_read"
    C04_MODE_SELECTION_MUST_BE_ENFORCED = "c04_mode_selection_must_be_enforced"
    C05_VALIDITY_ACTION_MUST_BE_ENFORCED = "c05_validity_action_must_be_enforced"
    C05_RESTRICTIONS_MUST_NOT_BE_IGNORED = "c05_restrictions_must_not_be_ignored"
    OUTCOME_MUST_BE_BOUNDED = "outcome_must_be_bounded"
    EXECUTION_STANCE_MUST_BE_READ = "execution_stance_must_be_read"
    CHECKPOINT_DECISIONS_MUST_BE_READ = "checkpoint_decisions_must_be_read"
    C04_MODE_CLAIM_MUST_BE_READ = "c04_mode_claim_must_be_read"
    C05_ACTION_CLAIM_MUST_BE_READ = "c05_action_claim_must_be_read"
    AUTHORITY_ROLES_MUST_BE_READ = "authority_roles_must_be_read"
    DOWNSTREAM_OBEDIENCE_CONTRACT_MUST_BE_READ = "downstream_obedience_contract_must_be_read"
    DOWNSTREAM_OBEDIENCE_RESTRICTIONS_MUST_BE_ENFORCED = (
        "downstream_obedience_restrictions_must_be_enforced"
    )
    WORLD_SEAM_CONTRACT_MUST_BE_READ = "world_seam_contract_must_be_read"
    WORLD_GROUNDED_TRANSITION_REQUIRES_WORLD_PRESENCE = (
        "world_grounded_transition_requires_world_presence"
    )
    WORLD_EFFECT_FEEDBACK_REQUIRED_FOR_SUCCESS_CLAIM = (
        "world_effect_feedback_required_for_success_claim"
    )
    W_ENTRY_CONTRACT_MUST_BE_READ = "w_entry_contract_must_be_read"
    W_ENTRY_FORBIDDEN_CLAIMS_MUST_BE_READ = "w_entry_forbidden_claims_must_be_read"
    W_ENTRY_ADMISSION_CRITERIA_MUST_BE_READ = "w_entry_admission_criteria_must_be_read"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


class SubjectTickAuthorityRole(StrEnum):
    GATING = "gating"
    INVALIDATION = "invalidation"
    ARBITRATION = "arbitration"
    MODULATORY_ONLY = "modulatory_only"
    OBSERVABILITY_ONLY = "observability_only"
    COMPUTATIONAL = "computational"
    UNKNOWN = "unknown"


class SubjectTickComputationalRole(StrEnum):
    STATE_UPDATE = "state_update"
    SCHEDULER = "scheduler"
    EVALUATOR = "evaluator"
    OBSERVABILITY = "observability"
    EXECUTION_SPINE = "execution_spine"
    BRIDGE_CONTRACT = "bridge_contract"
    REGISTRY = "registry"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SubjectTickRoleMapSource:
    source_ref: str = "rt01.default_frontier_role_map"
    phase_authority_roles: dict[str, str] = field(default_factory=dict)
    phase_computational_roles: dict[str, str] = field(default_factory=dict)
    frontier_role_typed: bool = True
    map_wide_role_ready: bool = False
    role_frontier_only: bool = True


@dataclass(frozen=True, slots=True)
class SubjectTickInput:
    case_id: str
    energy: float
    cognitive: float
    safety: float
    unresolved_preference: bool = False


@dataclass(frozen=True, slots=True)
class SubjectTickContext:
    prior_subject_tick_state: SubjectTickState | None = None
    prior_runtime_state: object | None = None
    prior_regulation_state: object | None = None
    prior_viability_state: object | None = None
    prior_stream_state: object | None = None
    prior_scheduler_state: object | None = None
    prior_diversification_state: object | None = None
    prior_mode_state: object | None = None
    prior_temporal_validity_state: object | None = None
    dependency_trigger_hits: tuple[str, ...] = ()
    context_shift_markers: tuple[str, ...] = ()
    contradicted_source_refs: tuple[str, ...] = ()
    withdrawn_source_refs: tuple[str, ...] = ()
    external_turn_present: bool = False
    allow_endogenous_tick: bool = True
    mode_resource_budget: float = 1.0
    mode_cooldown_active: bool = False
    allow_provisional_carry: bool = True
    require_available_affordance: bool = False
    require_strong_regulation_claim: bool = False
    disable_gate_application: bool = False
    disable_c04_mode_execution_binding: bool = False
    disable_c05_validity_enforcement: bool = False
    disable_downstream_obedience_enforcement: bool = False
    phase_authority_roles: dict[str, str] = field(default_factory=dict)
    phase_computational_roles: dict[str, str] = field(default_factory=dict)
    role_map_source: SubjectTickRoleMapSource | None = None
    world_adapter_input: WorldAdapterInput | None = None
    require_world_grounded_transition: bool = False
    require_world_effect_feedback_for_success_claim: bool = False
    emit_world_action_candidate: bool = False
    disable_world_seam_enforcement: bool = False
    source_lineage: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SubjectTickStepResult:
    phase_id: str
    status: SubjectTickStepStatus
    gate_accepted: bool
    usability_class: str
    execution_mode: str | None
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class SubjectTickCheckpointResult:
    checkpoint_id: str
    source_contract: str
    status: SubjectTickCheckpointStatus
    required_action: str
    applied_action: str
    reason: str


@dataclass(frozen=True, slots=True)
class SubjectTickState:
    tick_id: str
    tick_index: int
    prior_runtime_status: SubjectTickOutcome | None
    c04_execution_mode_claim: str
    c05_execution_action_claim: str
    f01_authority_role: str
    r04_authority_role: str
    c04_authority_role: str
    c05_authority_role: str
    d01_authority_role: str
    rt01_authority_role: str
    f01_computational_role: str
    r04_computational_role: str
    c04_computational_role: str
    c05_computational_role: str
    d01_computational_role: str
    rt01_computational_role: str
    role_source_ref: str
    role_frontier_only: bool
    role_map_ready: bool
    role_frontier_typed: bool
    active_execution_mode: str
    c04_selected_mode: str
    c05_validity_action: str
    downstream_obedience_status: str
    downstream_obedience_fallback: str
    downstream_obedience_source_of_truth_surface: str
    downstream_obedience_requires_restrictions_read: bool
    downstream_obedience_reason: str
    world_adapter_presence: bool
    world_adapter_available: bool
    world_adapter_degraded: bool
    world_link_status: str
    world_effect_status: str
    world_grounded_transition_allowed: bool
    world_externally_effected_change_claim_allowed: bool
    world_action_success_claim_allowed: bool
    world_effect_feedback_correlated: bool
    world_grounding_confidence: float
    world_require_grounded_transition: bool
    world_require_effect_feedback_for_success_claim: bool
    world_adapter_reason: str
    world_entry_episode_id: str
    world_entry_presence_mode: str
    world_entry_episode_scope: str
    world_entry_observation_basis_present: bool
    world_entry_action_trace_present: bool
    world_entry_effect_basis_present: bool
    world_entry_effect_feedback_correlated: bool
    world_entry_confidence: float
    world_entry_reliability: str
    world_entry_degraded: bool
    world_entry_incomplete: bool
    world_entry_forbidden_claim_classes: tuple[str, ...]
    world_entry_world_grounded_transition_admissible: bool
    world_entry_world_effect_success_admissible: bool
    world_entry_w01_admission_ready: bool
    world_entry_w01_admission_restrictions: tuple[str, ...]
    world_entry_scope: str
    world_entry_scope_admission_layer_only: bool
    world_entry_scope_w01_implemented: bool
    world_entry_scope_w_line_implemented: bool
    world_entry_scope_repo_wide_adoption: bool
    world_entry_scope_reason: str
    world_entry_reason: str
    execution_stance: SubjectTickExecutionStance
    execution_checkpoints: tuple[SubjectTickCheckpointResult, ...]
    downstream_step_results: tuple[SubjectTickStepResult, ...]
    final_execution_outcome: SubjectTickOutcome
    repair_needed: bool
    revalidation_needed: bool
    halt_reason: str | None
    source_stream_id: str
    source_stream_sequence_index: int
    source_c01_state_ref: str
    source_c02_state_ref: str
    source_c03_state_ref: str
    source_c04_state_ref: str
    source_c05_state_ref: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class SubjectTickGateDecision:
    accepted: bool
    usability_class: SubjectTickUsabilityClass
    restrictions: tuple[SubjectTickRestrictionCode, ...]
    reason: str
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class SubjectTickTelemetry:
    tick_id: str
    tick_index: int
    source_lineage: tuple[str, ...]
    phase_order: tuple[str, ...]
    c04_execution_mode_claim: str
    c05_execution_action_claim: str
    f01_authority_role: str
    r04_authority_role: str
    c04_authority_role: str
    c05_authority_role: str
    d01_authority_role: str
    rt01_authority_role: str
    role_source_ref: str
    role_frontier_only: bool
    role_map_ready: bool
    role_frontier_typed: bool
    active_execution_mode: str
    c04_selected_mode: str
    c05_validity_action: str
    downstream_obedience_status: str
    downstream_obedience_fallback: str
    downstream_obedience_source_of_truth_surface: str
    downstream_obedience_requires_restrictions_read: bool
    downstream_obedience_reason: str
    world_adapter_presence: bool
    world_adapter_available: bool
    world_adapter_degraded: bool
    world_link_status: str
    world_effect_status: str
    world_grounded_transition_allowed: bool
    world_externally_effected_change_claim_allowed: bool
    world_action_success_claim_allowed: bool
    world_effect_feedback_correlated: bool
    world_grounding_confidence: float
    world_require_grounded_transition: bool
    world_require_effect_feedback_for_success_claim: bool
    world_adapter_reason: str
    world_entry_episode_id: str
    world_entry_presence_mode: str
    world_entry_episode_scope: str
    world_entry_observation_basis_present: bool
    world_entry_action_trace_present: bool
    world_entry_effect_basis_present: bool
    world_entry_effect_feedback_correlated: bool
    world_entry_confidence: float
    world_entry_reliability: str
    world_entry_degraded: bool
    world_entry_incomplete: bool
    world_entry_forbidden_claim_classes: tuple[str, ...]
    world_entry_world_grounded_transition_admissible: bool
    world_entry_world_effect_success_admissible: bool
    world_entry_w01_admission_ready: bool
    world_entry_w01_admission_restrictions: tuple[str, ...]
    world_entry_scope: str
    world_entry_scope_admission_layer_only: bool
    world_entry_scope_w01_implemented: bool
    world_entry_scope_w_line_implemented: bool
    world_entry_scope_repo_wide_adoption: bool
    world_entry_scope_reason: str
    world_entry_reason: str
    execution_stance: SubjectTickExecutionStance
    execution_checkpoints: tuple[SubjectTickCheckpointResult, ...]
    final_execution_outcome: SubjectTickOutcome
    repair_needed: bool
    revalidation_needed: bool
    halt_reason: str | None
    step_results: tuple[SubjectTickStepResult, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: SubjectTickGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class SubjectTickResult:
    state: SubjectTickState
    downstream_gate: SubjectTickGateDecision
    telemetry: SubjectTickTelemetry
    regulation_result: object
    affordance_result: object
    preference_result: object
    viability_result: object
    c01_result: object
    c02_result: object
    c03_result: object
    c04_result: object
    c05_result: object
    world_adapter_result: WorldAdapterResult
    world_entry_result: WorldEntryContractResult
    abstain: bool
    abstain_reason: str | None
    no_planner_orchestrator_dependency: bool
    no_phase_semantics_override_dependency: bool
