from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from substrate.epistemics import EpistemicResult, EpistemicUnit
    from substrate.o01_other_entity_model import (
        O01EntitySignal,
        O01OtherEntityModelResult,
        O01OtherEntityModelState,
    )
    from substrate.o02_intersubjective_allostasis import (
        O02IntersubjectiveAllostasisResult,
        O02IntersubjectiveAllostasisState,
        O02InteractionDiagnosticsInput,
    )
    from substrate.s03_ownership_weighted_learning import (
        S03OwnershipWeightedLearningResult,
        S03OwnershipWeightedLearningState,
    )
    from substrate.s04_interoceptive_self_binding import (
        S04InteroceptiveSelfBindingResult,
        S04InteroceptiveSelfBindingState,
    )
    from substrate.s05_multi_cause_attribution_factorization import (
        S05MultiCauseAttributionResult,
        S05MultiCauseAttributionState,
    )
    from substrate.s02_prediction_boundary import (
        S02PredictionBoundaryResult,
        S02PredictionBoundaryState,
    )
    from substrate.s01_efference_copy import S01EfferenceCopyResult, S01EfferenceCopyState
    from substrate.a_line_normalization import ALineNormalizationResult
    from substrate.m_minimal import MMinimalResult
    from substrate.n_minimal import NMinimalResult
    from substrate.self_contour import SMinimalContourResult
    from substrate.t01_semantic_field import T01ActiveFieldResult
    from substrate.t02_relation_binding import T02ConstrainedSceneResult
    from substrate.t03_hypothesis_competition import T03CompetitionResult
    from substrate.t04_attention_schema import T04AttentionSchemaResult
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
    S_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ = "s_minimal_contour_contract_must_be_read"
    S_FORBIDDEN_SHORTCUTS_MUST_BE_READ = "s_forbidden_shortcuts_must_be_read"
    S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS = (
        "s_self_world_boundary_required_for_self_claims"
    )
    S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED = "s_ownership_control_discipline_required"
    A_LINE_NORMALIZATION_CONTRACT_MUST_BE_READ = "a_line_normalization_contract_must_be_read"
    A_FORBIDDEN_SHORTCUTS_MUST_BE_READ = "a_forbidden_shortcuts_must_be_read"
    A_CAPABILITY_CLAIM_REQUIRES_BASIS = "a_capability_claim_requires_basis"
    A_POLICY_GATED_CAPABILITY_REQUIRES_GATE = "a_policy_gated_capability_requires_gate"
    M_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ = "m_minimal_contour_contract_must_be_read"
    M_FORBIDDEN_SHORTCUTS_MUST_BE_READ = "m_forbidden_shortcuts_must_be_read"
    M_SAFE_MEMORY_CLAIM_REQUIRES_LIFECYCLE_BASIS = (
        "m_safe_memory_claim_requires_lifecycle_basis"
    )
    N_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ = "n_minimal_contour_contract_must_be_read"
    N_FORBIDDEN_SHORTCUTS_MUST_BE_READ = "n_forbidden_shortcuts_must_be_read"
    N_SAFE_NARRATIVE_CLAIM_REQUIRES_BASIS = "n_safe_narrative_claim_requires_basis"
    T01_SEMANTIC_FIELD_CONTRACT_MUST_BE_READ = "t01_semantic_field_contract_must_be_read"
    T01_FORBIDDEN_SHORTCUTS_MUST_BE_READ = "t01_forbidden_shortcuts_must_be_read"
    T01_PREVERBAL_SCENE_REQUIRED_FOR_CONSUMER = "t01_preverbal_scene_required_for_consumer"
    T01_SCENE_COMPARISON_REQUIRED_FOR_CONSUMER = "t01_scene_comparison_required_for_consumer"
    T02_RELATION_BINDING_CONTRACT_MUST_BE_READ = "t02_relation_binding_contract_must_be_read"
    T02_FORBIDDEN_SHORTCUTS_MUST_BE_READ = "t02_forbidden_shortcuts_must_be_read"
    T02_CONSTRAINED_SCENE_REQUIRED_FOR_CONSUMER = "t02_constrained_scene_required_for_consumer"
    T02_RAW_VS_PROPAGATED_DISTINCTION_REQUIRED = (
        "t02_raw_vs_propagated_distinction_required"
    )
    T03_HYPOTHESIS_COMPETITION_CONTRACT_MUST_BE_READ = (
        "t03_hypothesis_competition_contract_must_be_read"
    )
    T03_CONVERGENCE_CONSUMER_REQUIRED = "t03_convergence_consumer_required"
    T03_FRONTIER_CONSUMER_REQUIRED = "t03_frontier_consumer_required"
    T03_NONCONVERGENCE_PRESERVATION_REQUIRED = (
        "t03_nonconvergence_preservation_required"
    )
    T04_ATTENTION_SCHEMA_CONTRACT_MUST_BE_READ = "t04_attention_schema_contract_must_be_read"
    T04_FOCUS_OWNERSHIP_CONSUMER_REQUIRED = "t04_focus_ownership_consumer_required"
    T04_REPORTABLE_FOCUS_CONSUMER_REQUIRED = "t04_reportable_focus_consumer_required"
    T04_PERIPHERAL_PRESERVATION_REQUIRED = "t04_peripheral_preservation_required"
    S01_EFFERENCE_COPY_CONTRACT_MUST_BE_READ = "s01_efference_copy_contract_must_be_read"
    S01_COMPARISON_CONSUMER_REQUIRED = "s01_comparison_consumer_required"
    S01_UNEXPECTED_CHANGE_CONSUMER_REQUIRED = "s01_unexpected_change_consumer_required"
    S01_PREDICTION_VALIDITY_CONSUMER_REQUIRED = "s01_prediction_validity_consumer_required"
    S02_PREDICTION_BOUNDARY_CONTRACT_MUST_BE_READ = (
        "s02_prediction_boundary_contract_must_be_read"
    )
    S02_BOUNDARY_CONSUMER_REQUIRED = "s02_boundary_consumer_required"
    S02_CONTROLLABILITY_CONSUMER_REQUIRED = "s02_controllability_consumer_required"
    S02_MIXED_SOURCE_CONSUMER_REQUIRED = "s02_mixed_source_consumer_required"
    S03_OWNERSHIP_WEIGHTED_LEARNING_CONTRACT_MUST_BE_READ = (
        "s03_ownership_weighted_learning_contract_must_be_read"
    )
    S03_LEARNING_PACKET_CONSUMER_REQUIRED = "s03_learning_packet_consumer_required"
    S03_MIXED_UPDATE_CONSUMER_REQUIRED = "s03_mixed_update_consumer_required"
    S03_FREEZE_OBEDIENCE_CONSUMER_REQUIRED = (
        "s03_freeze_obedience_consumer_required"
    )
    S04_INTEROCEPTIVE_SELF_BINDING_CONTRACT_MUST_BE_READ = (
        "s04_interoceptive_self_binding_contract_must_be_read"
    )
    S04_STABLE_CORE_CONSUMER_REQUIRED = "s04_stable_core_consumer_required"
    S04_CONTESTED_CONSUMER_REQUIRED = "s04_contested_consumer_required"
    S04_NO_STABLE_CORE_CONSUMER_REQUIRED = (
        "s04_no_stable_core_consumer_required"
    )
    S05_MULTI_CAUSE_ATTRIBUTION_CONTRACT_MUST_BE_READ = (
        "s05_multi_cause_attribution_contract_must_be_read"
    )
    S05_FACTORIZED_CONSUMER_REQUIRED = "s05_factorized_consumer_required"
    S05_LOW_RESIDUAL_LEARNING_ROUTE_REQUIRED = (
        "s05_low_residual_learning_route_required"
    )
    S05_SINGLE_CAUSE_COLLAPSE_FORBIDDEN = "s05_single_cause_collapse_forbidden"
    O01_OTHER_ENTITY_MODEL_CONTRACT_MUST_BE_READ = (
        "o01_other_entity_model_contract_must_be_read"
    )
    O01_ENTITY_INDIVIDUATION_CONSUMER_REQUIRED = (
        "o01_entity_individuation_consumer_required"
    )
    O01_CLARIFICATION_READY_CONSUMER_REQUIRED = (
        "o01_clarification_ready_consumer_required"
    )
    O01_PROJECTION_GUARD_REQUIRED = "o01_projection_guard_required"
    O02_INTERSUBJECTIVE_ALLOSTASIS_CONTRACT_MUST_BE_READ = (
        "o02_intersubjective_allostasis_contract_must_be_read"
    )
    O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED = (
        "o02_repair_sensitive_consumer_required"
    )
    O02_BOUNDARY_PRESERVING_CONSUMER_REQUIRED = (
        "o02_boundary_preserving_consumer_required"
    )
    O02_POLITENESS_ONLY_COLLAPSE_FORBIDDEN = (
        "o02_politeness_only_collapse_forbidden"
    )
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
    epistemic_content: str | None = None
    epistemic_source_id: str | None = None
    epistemic_source_class: str | None = None
    epistemic_modality: str | None = None
    epistemic_confidence_hint: str | None = None
    epistemic_support_note: str | None = None
    epistemic_contestation_note: str | None = None
    epistemic_claim_key: str | None = None
    epistemic_claim_polarity: str | None = None


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
    prior_s01_state: S01EfferenceCopyState | None = None
    prior_s02_state: S02PredictionBoundaryState | None = None
    prior_s03_state: S03OwnershipWeightedLearningState | None = None
    prior_s04_state: S04InteroceptiveSelfBindingState | None = None
    prior_s05_state: S05MultiCauseAttributionState | None = None
    prior_o01_state: O01OtherEntityModelState | None = None
    prior_o02_state: O02IntersubjectiveAllostasisState | None = None
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
    prior_epistemic_units: tuple[EpistemicUnit, ...] = ()
    require_epistemic_observation: bool = False
    disable_epistemic_admission_enforcement: bool = False
    phase_authority_roles: dict[str, str] = field(default_factory=dict)
    phase_computational_roles: dict[str, str] = field(default_factory=dict)
    role_map_source: SubjectTickRoleMapSource | None = None
    world_adapter_input: WorldAdapterInput | None = None
    require_world_grounded_transition: bool = False
    require_world_effect_feedback_for_success_claim: bool = False
    emit_world_action_candidate: bool = False
    disable_world_seam_enforcement: bool = False
    require_self_side_claim: bool = False
    require_world_side_claim: bool = False
    require_self_controlled_transition_claim: bool = False
    strict_mixed_attribution_guard: bool = True
    disable_s_minimal_enforcement: bool = False
    require_a_line_capability_claim: bool = False
    disable_a_line_enforcement: bool = False
    require_memory_safe_claim: bool = False
    disable_m_minimal_enforcement: bool = False
    require_narrative_safe_claim: bool = False
    disable_n_minimal_enforcement: bool = False
    require_t01_preverbal_scene_consumer: bool = False
    require_t01_scene_comparison_consumer: bool = False
    disable_t01_unresolved_slot_maintenance: bool = False
    disable_t01_field_enforcement: bool = False
    require_t02_constrained_scene_consumer: bool = False
    require_t02_raw_vs_propagated_distinction: bool = False
    t02_assembly_mode: str | None = None
    disable_t02_enforcement: bool = False
    require_t03_convergence_consumer: bool = False
    require_t03_frontier_consumer: bool = False
    require_t03_nonconvergence_preservation: bool = False
    t03_competition_mode: str | None = None
    disable_t03_enforcement: bool = False
    require_t04_focus_ownership_consumer: bool = False
    require_t04_reportable_focus_consumer: bool = False
    require_t04_peripheral_preservation: bool = False
    disable_t04_enforcement: bool = False
    require_s01_comparison_consumer: bool = False
    require_s01_unexpected_change_consumer: bool = False
    require_s01_prediction_validity_consumer: bool = False
    disable_s01_enforcement: bool = False
    disable_s01_prediction_registration: bool = False
    require_s02_boundary_consumer: bool = False
    require_s02_controllability_consumer: bool = False
    require_s02_mixed_source_consumer: bool = False
    disable_s02_enforcement: bool = False
    require_s03_learning_packet_consumer: bool = False
    require_s03_mixed_update_consumer: bool = False
    require_s03_freeze_obedience_consumer: bool = False
    disable_s03_enforcement: bool = False
    require_s04_stable_core_consumer: bool = False
    require_s04_contested_consumer: bool = False
    require_s04_no_stable_core_consumer: bool = False
    disable_s04_enforcement: bool = False
    require_s05_factorized_consumer: bool = False
    require_s05_low_residual_learning_route: bool = False
    disable_s05_enforcement: bool = False
    require_o01_entity_individuation_consumer: bool = False
    require_o01_clarification_ready_consumer: bool = False
    disable_o01_enforcement: bool = False
    require_o02_repair_sensitive_consumer: bool = False
    require_o02_boundary_preserving_consumer: bool = False
    disable_o02_enforcement: bool = False
    o01_entity_signals: tuple[O01EntitySignal, ...] = ()
    o02_interaction_diagnostics: O02InteractionDiagnosticsInput | None = None
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
    epistemic_unit_id: str
    epistemic_status: str
    epistemic_confidence: str
    epistemic_source_class: str
    epistemic_modality: str
    epistemic_classification_basis: str
    epistemic_can_treat_as_observation: bool
    epistemic_should_abstain: bool
    epistemic_claim_strength: str
    epistemic_allowance_restrictions: tuple[str, ...]
    epistemic_allowance_reason: str
    epistemic_unknown_reason: str | None
    epistemic_conflict_reason: str | None
    epistemic_abstain_reason: str | None
    c04_selected_mode: str
    c05_validity_action: str
    regulation_pressure_level: float
    regulation_escalation_stage: str
    regulation_override_scope: str
    regulation_no_strong_override_claim: bool
    regulation_gate_accepted: bool
    regulation_source_state_ref: str
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
    s_boundary_state_id: str
    s_self_attribution_basis_present: bool
    s_world_attribution_basis_present: bool
    s_controllability_estimate: float
    s_ownership_estimate: float
    s_attribution_confidence: float
    s_source_status: str
    s_boundary_breach_risk: str
    s_attribution_class: str
    s_no_safe_self_claim: bool
    s_no_safe_world_claim: bool
    s_degraded: bool
    s_underconstrained: bool
    s_forbidden_shortcuts: tuple[str, ...]
    s_restrictions: tuple[str, ...]
    s_s01_admission_ready: bool
    s_self_attribution_basis_sufficient: bool
    s_controllability_basis_sufficient: bool
    s_ownership_basis_sufficient: bool
    s_attribution_underconstrained: bool
    s_mixed_boundary_instability: bool
    s_no_safe_self_basis: bool
    s_no_safe_world_basis: bool
    s_readiness_blockers: tuple[str, ...]
    s_future_s01_s05_remain_open: bool
    s_full_self_model_implemented: bool
    s_scope: str
    s_scope_rt01_contour_only: bool
    s_scope_s_minimal_only: bool
    s_scope_s01_implemented: bool
    s_scope_s_line_implemented: bool
    s_scope_minimal_contour_only: bool
    s_scope_s01_s05_implemented: bool
    s_scope_full_self_model_implemented: bool
    s_scope_repo_wide_adoption: bool
    s_scope_reason: str
    s_reason: str
    s_require_self_side_claim: bool
    s_require_world_side_claim: bool
    s_require_self_controlled_transition_claim: bool
    s_strict_mixed_attribution_guard: bool
    a_capability_id: str
    a_affordance_id: str
    a_capability_class: str
    a_capability_status: str
    a_availability_basis_present: bool
    a_world_dependency_present: bool
    a_self_dependency_present: bool
    a_controllability_dependency_present: bool
    a_legitimacy_dependency_present: bool
    a_confidence: float
    a_degraded: bool
    a_underconstrained: bool
    a_available_capability_claim_allowed: bool
    a_world_conditioned_capability_claim_allowed: bool
    a_self_conditioned_capability_claim_allowed: bool
    a_policy_conditioned_capability_present: bool
    a_no_safe_capability_claim: bool
    a_forbidden_shortcuts: tuple[str, ...]
    a_restrictions: tuple[str, ...]
    a_a04_admission_ready: bool
    a_a04_blockers: tuple[str, ...]
    a_a04_structurally_present_but_not_ready: bool
    a_a04_capability_basis_missing: bool
    a_a04_world_dependency_unmet: bool
    a_a04_self_dependency_unmet: bool
    a_a04_policy_legitimacy_unmet: bool
    a_a04_underconstrained_capability_surface: bool
    a_a04_external_means_not_justified: bool
    a_a04_implemented: bool
    a_a05_touched: bool
    a_scope: str
    a_scope_rt01_contour_only: bool
    a_scope_a_line_normalization_only: bool
    a_scope_readiness_gate_only: bool
    a_scope_a04_implemented: bool
    a_scope_a05_touched: bool
    a_scope_full_agency_stack_implemented: bool
    a_scope_repo_wide_adoption: bool
    a_scope_reason: str
    a_reason: str
    a_require_capability_claim: bool
    m_memory_item_id: str
    m_memory_packet_id: str
    m_lifecycle_status: str
    m_retention_class: str
    m_bounded_persistence_allowed: bool
    m_temporary_carry_allowed: bool
    m_review_required: bool
    m_reactivation_eligible: bool
    m_decay_eligible: bool
    m_pruning_eligible: bool
    m_stale_risk: str
    m_conflict_risk: str
    m_confidence: float
    m_reliability: str
    m_degraded: bool
    m_underconstrained: bool
    m_safe_memory_claim_allowed: bool
    m_bounded_retained_claim_allowed: bool
    m_no_safe_memory_claim: bool
    m_forbidden_shortcuts: tuple[str, ...]
    m_restrictions: tuple[str, ...]
    m_m01_admission_ready: bool
    m_m01_blockers: tuple[str, ...]
    m_m01_structurally_present_but_not_ready: bool
    m_m01_stale_risk_unacceptable: bool
    m_m01_conflict_risk_unacceptable: bool
    m_m01_reactivation_requires_review: bool
    m_m01_temporary_carry_not_stable_enough: bool
    m_m01_no_safe_memory_basis: bool
    m_m01_provenance_insufficient: bool
    m_m01_lifecycle_underconstrained: bool
    m_m01_implemented: bool
    m_m02_implemented: bool
    m_m03_implemented: bool
    m_scope: str
    m_scope_rt01_contour_only: bool
    m_scope_m_minimal_only: bool
    m_scope_readiness_gate_only: bool
    m_scope_m01_implemented: bool
    m_scope_m02_implemented: bool
    m_scope_m03_implemented: bool
    m_scope_full_memory_stack_implemented: bool
    m_scope_repo_wide_adoption: bool
    m_scope_reason: str
    m_reason: str
    m_require_memory_safe_claim: bool
    n_narrative_commitment_id: str
    n_commitment_status: str
    n_commitment_scope: str
    n_narrative_basis_present: bool
    n_self_basis_present: bool
    n_world_basis_present: bool
    n_memory_basis_present: bool
    n_capability_basis_present: bool
    n_ambiguity_residue: bool
    n_contradiction_risk: str
    n_confidence: float
    n_degraded: bool
    n_underconstrained: bool
    n_safe_narrative_commitment_allowed: bool
    n_bounded_commitment_allowed: bool
    n_no_safe_narrative_claim: bool
    n_forbidden_shortcuts: tuple[str, ...]
    n_restrictions: tuple[str, ...]
    n_n01_admission_ready: bool
    n_n01_blockers: tuple[str, ...]
    n_n01_implemented: bool
    n_n02_implemented: bool
    n_n03_implemented: bool
    n_n04_implemented: bool
    n_scope: str
    n_scope_rt01_contour_only: bool
    n_scope_n_minimal_only: bool
    n_scope_readiness_gate_only: bool
    n_scope_n01_implemented: bool
    n_scope_n02_implemented: bool
    n_scope_n03_implemented: bool
    n_scope_n04_implemented: bool
    n_scope_full_narrative_line_implemented: bool
    n_scope_repo_wide_adoption: bool
    n_scope_reason: str
    n_reason: str
    n_require_narrative_safe_claim: bool
    t01_scene_id: str
    t01_scene_status: str
    t01_stability_state: str
    t01_active_entities_count: int
    t01_relation_edges_count: int
    t01_role_bindings_count: int
    t01_unresolved_slots_count: int
    t01_contested_relations_count: int
    t01_preverbal_consumer_ready: bool
    t01_scene_comparison_ready: bool
    t01_no_clean_scene_commit: bool
    t01_forbidden_shortcuts: tuple[str, ...]
    t01_restrictions: tuple[str, ...]
    t01_scope: str
    t01_scope_rt01_contour_only: bool
    t01_scope_t01_first_slice_only: bool
    t01_scope_t02_implemented: bool
    t01_scope_t03_implemented: bool
    t01_scope_t04_implemented: bool
    t01_scope_o01_implemented: bool
    t01_scope_full_silent_thought_line_implemented: bool
    t01_scope_repo_wide_adoption: bool
    t01_scope_reason: str
    t01_reason: str
    t01_require_preverbal_scene_consumer: bool
    t01_require_scene_comparison_consumer: bool
    s01_latest_comparison_status: str | None
    s01_comparison_ready: bool
    s01_unexpected_change_detected: bool
    s01_prediction_validity_ready: bool
    s01_comparison_blocked_by_contamination: bool
    s01_stale_prediction_detected: bool
    s01_pending_predictions_count: int
    s01_comparisons_count: int
    s01_require_comparison_consumer: bool
    s01_require_unexpected_change_consumer: bool
    s01_require_prediction_validity_consumer: bool
    s02_boundary_id: str
    s02_active_boundary_status: str
    s02_boundary_uncertain: bool
    s02_insufficient_coverage: bool
    s02_no_clean_seam_claim: bool
    s02_controllability_estimate: float
    s02_prediction_reliability_estimate: float
    s02_external_dominance_estimate: float
    s02_mixed_source_score: float
    s02_boundary_confidence: float
    s02_boundary_consumer_ready: bool
    s02_controllability_consumer_ready: bool
    s02_mixed_source_consumer_ready: bool
    s02_forbidden_shortcuts: tuple[str, ...]
    s02_restrictions: tuple[str, ...]
    s02_scope: str
    s02_scope_rt01_contour_only: bool
    s02_scope_s02_first_slice_only: bool
    s02_scope_s03_implemented: bool
    s02_scope_s04_implemented: bool
    s02_scope_s05_implemented: bool
    s02_scope_full_self_model_implemented: bool
    s02_scope_repo_wide_adoption: bool
    s02_scope_reason: str
    s02_reason: str
    s02_require_boundary_consumer: bool
    s02_require_controllability_consumer: bool
    s02_require_mixed_source_consumer: bool
    s03_learning_id: str
    s03_latest_packet_id: str
    s03_latest_update_class: str
    s03_latest_commit_class: str
    s03_latest_ambiguity_class: str | None
    s03_freeze_or_defer_state: str
    s03_requested_revalidation: bool
    s03_self_update_weight: float
    s03_world_update_weight: float
    s03_observation_update_weight: float
    s03_anomaly_update_weight: float
    s03_learning_packet_consumer_ready: bool
    s03_mixed_update_consumer_ready: bool
    s03_freeze_obedience_consumer_ready: bool
    s03_scope: str
    s03_scope_rt01_contour_only: bool
    s03_scope_s03_first_slice_only: bool
    s03_scope_s04_implemented: bool
    s03_scope_s05_implemented: bool
    s03_scope_repo_wide_adoption: bool
    s03_scope_reason: str
    s03_reason: str
    s03_require_learning_packet_consumer: bool
    s03_require_mixed_update_consumer: bool
    s03_require_freeze_obedience_consumer: bool
    t02_require_constrained_scene_consumer: bool
    t02_require_raw_vs_propagated_distinction: bool
    t02_raw_vs_propagated_distinct: bool
    t03_competition_id: str
    t03_convergence_status: str
    t03_current_leader_hypothesis_id: str | None
    t03_provisional_frontrunner_hypothesis_id: str | None
    t03_tied_competitor_count: int
    t03_blocked_hypothesis_count: int
    t03_eliminated_hypothesis_count: int
    t03_reactivated_hypothesis_count: int
    t03_honest_nonconvergence: bool
    t03_bounded_plurality: bool
    t03_convergence_consumer_ready: bool
    t03_frontier_consumer_ready: bool
    t03_nonconvergence_preserved: bool
    t03_forbidden_shortcuts: tuple[str, ...]
    t03_restrictions: tuple[str, ...]
    t03_publication_current_leader: str | None
    t03_publication_competitive_neighborhood: tuple[str, ...]
    t03_publication_unresolved_conflicts: tuple[str, ...]
    t03_publication_open_slots: tuple[str, ...]
    t03_publication_stability_status: str
    t03_scope: str
    t03_scope_rt01_contour_only: bool
    t03_scope_t03_first_slice_only: bool
    t03_scope_t04_implemented: bool
    t03_scope_o01_implemented: bool
    t03_scope_o02_implemented: bool
    t03_scope_o03_implemented: bool
    t03_scope_full_silent_thought_line_implemented: bool
    t03_scope_repo_wide_adoption: bool
    t03_scope_reason: str
    t03_reason: str
    t03_require_convergence_consumer: bool
    t03_require_frontier_consumer: bool
    t03_require_nonconvergence_preservation: bool
    t04_require_focus_ownership_consumer: bool
    t04_require_reportable_focus_consumer: bool
    t04_require_peripheral_preservation: bool
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
    o02_interaction_mode: str = "conservative_mode_only"
    o02_boundary_protection_status: str = "not_required"
    o02_other_model_reliance_status: str = "underconstrained"
    o02_no_safe_regulation_claim: bool = True
    o02_s05_shape_modulation_applied: bool = False
    o02_prior_mode_carry_applied: bool = False
    o02_strong_disagreement_guard_applied: bool = False


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
    s_boundary_state_id: str
    s_self_attribution_basis_present: bool
    s_world_attribution_basis_present: bool
    s_controllability_estimate: float
    s_ownership_estimate: float
    s_attribution_confidence: float
    s_source_status: str
    s_boundary_breach_risk: str
    s_attribution_class: str
    s_no_safe_self_claim: bool
    s_no_safe_world_claim: bool
    s_degraded: bool
    s_underconstrained: bool
    s_forbidden_shortcuts: tuple[str, ...]
    s_restrictions: tuple[str, ...]
    s_s01_admission_ready: bool
    s_self_attribution_basis_sufficient: bool
    s_controllability_basis_sufficient: bool
    s_ownership_basis_sufficient: bool
    s_attribution_underconstrained: bool
    s_mixed_boundary_instability: bool
    s_no_safe_self_basis: bool
    s_no_safe_world_basis: bool
    s_readiness_blockers: tuple[str, ...]
    s_future_s01_s05_remain_open: bool
    s_full_self_model_implemented: bool
    s_scope: str
    s_scope_rt01_contour_only: bool
    s_scope_s_minimal_only: bool
    s_scope_s01_implemented: bool
    s_scope_s_line_implemented: bool
    s_scope_minimal_contour_only: bool
    s_scope_s01_s05_implemented: bool
    s_scope_full_self_model_implemented: bool
    s_scope_repo_wide_adoption: bool
    s_scope_reason: str
    s_reason: str
    s_require_self_side_claim: bool
    s_require_world_side_claim: bool
    s_require_self_controlled_transition_claim: bool
    s_strict_mixed_attribution_guard: bool
    a_capability_id: str
    a_affordance_id: str
    a_capability_class: str
    a_capability_status: str
    a_availability_basis_present: bool
    a_world_dependency_present: bool
    a_self_dependency_present: bool
    a_controllability_dependency_present: bool
    a_legitimacy_dependency_present: bool
    a_confidence: float
    a_degraded: bool
    a_underconstrained: bool
    a_available_capability_claim_allowed: bool
    a_world_conditioned_capability_claim_allowed: bool
    a_self_conditioned_capability_claim_allowed: bool
    a_policy_conditioned_capability_present: bool
    a_no_safe_capability_claim: bool
    a_forbidden_shortcuts: tuple[str, ...]
    a_restrictions: tuple[str, ...]
    a_a04_admission_ready: bool
    a_a04_blockers: tuple[str, ...]
    a_a04_structurally_present_but_not_ready: bool
    a_a04_capability_basis_missing: bool
    a_a04_world_dependency_unmet: bool
    a_a04_self_dependency_unmet: bool
    a_a04_policy_legitimacy_unmet: bool
    a_a04_underconstrained_capability_surface: bool
    a_a04_external_means_not_justified: bool
    a_a04_implemented: bool
    a_a05_touched: bool
    a_scope: str
    a_scope_rt01_contour_only: bool
    a_scope_a_line_normalization_only: bool
    a_scope_readiness_gate_only: bool
    a_scope_a04_implemented: bool
    a_scope_a05_touched: bool
    a_scope_full_agency_stack_implemented: bool
    a_scope_repo_wide_adoption: bool
    a_scope_reason: str
    a_reason: str
    a_require_capability_claim: bool
    m_memory_item_id: str
    m_memory_packet_id: str
    m_lifecycle_status: str
    m_retention_class: str
    m_bounded_persistence_allowed: bool
    m_temporary_carry_allowed: bool
    m_review_required: bool
    m_reactivation_eligible: bool
    m_decay_eligible: bool
    m_pruning_eligible: bool
    m_stale_risk: str
    m_conflict_risk: str
    m_confidence: float
    m_reliability: str
    m_degraded: bool
    m_underconstrained: bool
    m_safe_memory_claim_allowed: bool
    m_bounded_retained_claim_allowed: bool
    m_no_safe_memory_claim: bool
    m_forbidden_shortcuts: tuple[str, ...]
    m_restrictions: tuple[str, ...]
    m_m01_admission_ready: bool
    m_m01_blockers: tuple[str, ...]
    m_m01_structurally_present_but_not_ready: bool
    m_m01_stale_risk_unacceptable: bool
    m_m01_conflict_risk_unacceptable: bool
    m_m01_reactivation_requires_review: bool
    m_m01_temporary_carry_not_stable_enough: bool
    m_m01_no_safe_memory_basis: bool
    m_m01_provenance_insufficient: bool
    m_m01_lifecycle_underconstrained: bool
    m_m01_implemented: bool
    m_m02_implemented: bool
    m_m03_implemented: bool
    m_scope: str
    m_scope_rt01_contour_only: bool
    m_scope_m_minimal_only: bool
    m_scope_readiness_gate_only: bool
    m_scope_m01_implemented: bool
    m_scope_m02_implemented: bool
    m_scope_m03_implemented: bool
    m_scope_full_memory_stack_implemented: bool
    m_scope_repo_wide_adoption: bool
    m_scope_reason: str
    m_reason: str
    m_require_memory_safe_claim: bool
    n_narrative_commitment_id: str
    n_commitment_status: str
    n_commitment_scope: str
    n_narrative_basis_present: bool
    n_self_basis_present: bool
    n_world_basis_present: bool
    n_memory_basis_present: bool
    n_capability_basis_present: bool
    n_ambiguity_residue: bool
    n_contradiction_risk: str
    n_confidence: float
    n_degraded: bool
    n_underconstrained: bool
    n_safe_narrative_commitment_allowed: bool
    n_bounded_commitment_allowed: bool
    n_no_safe_narrative_claim: bool
    n_forbidden_shortcuts: tuple[str, ...]
    n_restrictions: tuple[str, ...]
    n_n01_admission_ready: bool
    n_n01_blockers: tuple[str, ...]
    n_n01_implemented: bool
    n_n02_implemented: bool
    n_n03_implemented: bool
    n_n04_implemented: bool
    n_scope: str
    n_scope_rt01_contour_only: bool
    n_scope_n_minimal_only: bool
    n_scope_readiness_gate_only: bool
    n_scope_n01_implemented: bool
    n_scope_n02_implemented: bool
    n_scope_n03_implemented: bool
    n_scope_n04_implemented: bool
    n_scope_full_narrative_line_implemented: bool
    n_scope_repo_wide_adoption: bool
    n_scope_reason: str
    n_reason: str
    n_require_narrative_safe_claim: bool
    t01_scene_id: str
    t01_scene_status: str
    t01_stability_state: str
    t01_active_entities_count: int
    t01_relation_edges_count: int
    t01_role_bindings_count: int
    t01_unresolved_slots_count: int
    t01_contested_relations_count: int
    t01_preverbal_consumer_ready: bool
    t01_scene_comparison_ready: bool
    t01_no_clean_scene_commit: bool
    t01_forbidden_shortcuts: tuple[str, ...]
    t01_restrictions: tuple[str, ...]
    t01_scope: str
    t01_scope_rt01_contour_only: bool
    t01_scope_t01_first_slice_only: bool
    t01_scope_t02_implemented: bool
    t01_scope_t03_implemented: bool
    t01_scope_t04_implemented: bool
    t01_scope_o01_implemented: bool
    t01_scope_full_silent_thought_line_implemented: bool
    t01_scope_repo_wide_adoption: bool
    t01_scope_reason: str
    t01_reason: str
    t01_require_preverbal_scene_consumer: bool
    t01_require_scene_comparison_consumer: bool
    t02_require_constrained_scene_consumer: bool
    t02_require_raw_vs_propagated_distinction: bool
    t02_raw_vs_propagated_distinct: bool
    t03_competition_id: str
    t03_convergence_status: str
    t03_current_leader_hypothesis_id: str | None
    t03_provisional_frontrunner_hypothesis_id: str | None
    t03_tied_competitor_count: int
    t03_blocked_hypothesis_count: int
    t03_eliminated_hypothesis_count: int
    t03_reactivated_hypothesis_count: int
    t03_honest_nonconvergence: bool
    t03_bounded_plurality: bool
    t03_convergence_consumer_ready: bool
    t03_frontier_consumer_ready: bool
    t03_nonconvergence_preserved: bool
    t03_forbidden_shortcuts: tuple[str, ...]
    t03_restrictions: tuple[str, ...]
    t03_publication_current_leader: str | None
    t03_publication_competitive_neighborhood: tuple[str, ...]
    t03_publication_unresolved_conflicts: tuple[str, ...]
    t03_publication_open_slots: tuple[str, ...]
    t03_publication_stability_status: str
    t03_scope: str
    t03_scope_rt01_contour_only: bool
    t03_scope_t03_first_slice_only: bool
    t03_scope_t04_implemented: bool
    t03_scope_o01_implemented: bool
    t03_scope_o02_implemented: bool
    t03_scope_o03_implemented: bool
    t03_scope_full_silent_thought_line_implemented: bool
    t03_scope_repo_wide_adoption: bool
    t03_scope_reason: str
    t03_reason: str
    t03_require_convergence_consumer: bool
    t03_require_frontier_consumer: bool
    t03_require_nonconvergence_preservation: bool
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
    epistemic_result: EpistemicResult
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
    self_contour_result: SMinimalContourResult
    a_line_result: ALineNormalizationResult
    m_minimal_result: MMinimalResult
    n_minimal_result: NMinimalResult
    s01_result: S01EfferenceCopyResult
    s02_result: S02PredictionBoundaryResult
    s03_result: S03OwnershipWeightedLearningResult
    s04_result: S04InteroceptiveSelfBindingResult
    s05_result: S05MultiCauseAttributionResult
    o01_result: O01OtherEntityModelResult
    o02_result: O02IntersubjectiveAllostasisResult
    t01_result: T01ActiveFieldResult
    t02_result: T02ConstrainedSceneResult
    t03_result: T03CompetitionResult
    t04_result: T04AttentionSchemaResult
    abstain: bool
    abstain_reason: str | None
    no_planner_orchestrator_dependency: bool
    no_phase_semantics_override_dependency: bool
