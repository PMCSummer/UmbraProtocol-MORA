from __future__ import annotations

from dataclasses import dataclass

from substrate.contracts import RuntimeState
from substrate.subject_tick.models import (
    SubjectTickOutcome,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickUsabilityClass,
)
from substrate.subject_tick.policy import evaluate_subject_tick_downstream_gate


@dataclass(frozen=True, slots=True)
class SubjectTickContractView:
    tick_id: str
    tick_index: int
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
    t02_constrained_scene_id: str | None
    t02_scene_status: str | None
    t02_preverbal_constraint_consumer_ready: bool | None
    t02_no_clean_binding_commit: bool | None
    t02_confirmed_bindings_count: int | None
    t02_provisional_bindings_count: int | None
    t02_blocked_bindings_count: int | None
    t02_conflicted_bindings_count: int | None
    t02_propagated_consequences_count: int | None
    t02_blocked_or_conflicted_consequences_count: int | None
    t02_forbidden_shortcuts: tuple[str, ...] | None
    t02_scope: str | None
    t02_scope_rt01_contour_only: bool | None
    t02_scope_t02_first_slice_only: bool | None
    t02_scope_t03_implemented: bool | None
    t02_scope_t04_implemented: bool | None
    t02_scope_o01_implemented: bool | None
    t02_scope_full_silent_thought_line_implemented: bool | None
    t02_scope_repo_wide_adoption: bool | None
    t02_require_constrained_scene_consumer: bool | None
    t02_require_raw_vs_propagated_distinction: bool | None
    t02_raw_vs_propagated_distinct: bool | None
    t03_competition_id: str | None
    t03_convergence_status: str | None
    t03_current_leader_hypothesis_id: str | None
    t03_provisional_frontrunner_hypothesis_id: str | None
    t03_tied_competitor_count: int | None
    t03_blocked_hypothesis_count: int | None
    t03_eliminated_hypothesis_count: int | None
    t03_reactivated_hypothesis_count: int | None
    t03_honest_nonconvergence: bool | None
    t03_bounded_plurality: bool | None
    t03_convergence_consumer_ready: bool | None
    t03_frontier_consumer_ready: bool | None
    t03_nonconvergence_preserved: bool | None
    t03_forbidden_shortcuts: tuple[str, ...] | None
    t03_restrictions: tuple[str, ...] | None
    t03_publication_current_leader: str | None
    t03_publication_competitive_neighborhood: tuple[str, ...] | None
    t03_publication_unresolved_conflicts: tuple[str, ...] | None
    t03_publication_open_slots: tuple[str, ...] | None
    t03_publication_stability_status: str | None
    t03_scope: str | None
    t03_scope_rt01_contour_only: bool | None
    t03_scope_t03_first_slice_only: bool | None
    t03_scope_t04_implemented: bool | None
    t03_scope_o01_implemented: bool | None
    t03_scope_o02_implemented: bool | None
    t03_scope_o03_implemented: bool | None
    t03_scope_full_silent_thought_line_implemented: bool | None
    t03_scope_repo_wide_adoption: bool | None
    t03_require_convergence_consumer: bool | None
    t03_require_frontier_consumer: bool | None
    t03_require_nonconvergence_preservation: bool | None
    t04_schema_id: str | None
    t04_focus_targets_count: int | None
    t04_peripheral_targets_count: int | None
    t04_attention_owner: str | None
    t04_focus_mode: str | None
    t04_control_estimate: float | None
    t04_stability_estimate: float | None
    t04_redirect_cost: float | None
    t04_reportability_status: str | None
    t04_focus_ownership_consumer_ready: bool | None
    t04_reportable_focus_consumer_ready: bool | None
    t04_peripheral_preservation_ready: bool | None
    t04_forbidden_shortcuts: tuple[str, ...] | None
    t04_restrictions: tuple[str, ...] | None
    t04_scope: str | None
    t04_scope_rt01_contour_only: bool | None
    t04_scope_t04_first_slice_only: bool | None
    t04_scope_o01_implemented: bool | None
    t04_scope_o02_implemented: bool | None
    t04_scope_o03_implemented: bool | None
    t04_scope_full_attention_line_implemented: bool | None
    t04_scope_repo_wide_adoption: bool | None
    t04_require_focus_ownership_consumer: bool | None
    t04_require_reportable_focus_consumer: bool | None
    t04_require_peripheral_preservation: bool | None
    execution_stance: str
    execution_checkpoints: tuple[str, ...]
    final_execution_outcome: SubjectTickOutcome
    repair_needed: bool
    revalidation_needed: bool
    halt_reason: str | None
    gate_accepted: bool
    restrictions: tuple[str, ...]
    usability_class: SubjectTickUsabilityClass
    requires_restrictions_read: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SubjectTickRuntimeDomainContractView:
    regulation_pressure_level: float | None
    regulation_override_scope: str | None
    continuity_mode_claim: str | None
    continuity_mode_legitimacy: bool
    validity_action_claim: str | None
    validity_legality_reuse_allowed: bool
    validity_revalidation_required: bool
    validity_no_safe_reuse: bool
    recommended_outcome: str
    source_of_truth_surface: str
    packet_snapshot_precedence_blocked: bool
    reason: str


def derive_subject_tick_contract_view(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult,
) -> SubjectTickContractView:
    if isinstance(subject_tick_state_or_result, SubjectTickResult):
        state = subject_tick_state_or_result.state
        t02_result = subject_tick_state_or_result.t02_result
        t03_result = subject_tick_state_or_result.t03_result
        t04_result = subject_tick_state_or_result.t04_result
    elif isinstance(subject_tick_state_or_result, SubjectTickState):
        state = subject_tick_state_or_result
        t02_result = None
        t03_result = None
        t04_result = None
    else:
        raise TypeError(
            "derive_subject_tick_contract_view requires SubjectTickState/SubjectTickResult"
        )
    gate = evaluate_subject_tick_downstream_gate(state)
    return SubjectTickContractView(
        tick_id=state.tick_id,
        tick_index=state.tick_index,
        c04_execution_mode_claim=state.c04_execution_mode_claim,
        c05_execution_action_claim=state.c05_execution_action_claim,
        f01_authority_role=state.f01_authority_role,
        r04_authority_role=state.r04_authority_role,
        c04_authority_role=state.c04_authority_role,
        c05_authority_role=state.c05_authority_role,
        d01_authority_role=state.d01_authority_role,
        rt01_authority_role=state.rt01_authority_role,
        role_source_ref=state.role_source_ref,
        role_frontier_only=state.role_frontier_only,
        role_map_ready=state.role_map_ready,
        role_frontier_typed=state.role_frontier_typed,
        active_execution_mode=state.active_execution_mode,
        c04_selected_mode=state.c04_selected_mode,
        c05_validity_action=state.c05_validity_action,
        downstream_obedience_status=state.downstream_obedience_status,
        downstream_obedience_fallback=state.downstream_obedience_fallback,
        downstream_obedience_source_of_truth_surface=state.downstream_obedience_source_of_truth_surface,
        downstream_obedience_requires_restrictions_read=(
            state.downstream_obedience_requires_restrictions_read
        ),
        downstream_obedience_reason=state.downstream_obedience_reason,
        world_adapter_presence=state.world_adapter_presence,
        world_adapter_available=state.world_adapter_available,
        world_adapter_degraded=state.world_adapter_degraded,
        world_link_status=state.world_link_status,
        world_effect_status=state.world_effect_status,
        world_grounded_transition_allowed=state.world_grounded_transition_allowed,
        world_externally_effected_change_claim_allowed=(
            state.world_externally_effected_change_claim_allowed
        ),
        world_action_success_claim_allowed=state.world_action_success_claim_allowed,
        world_effect_feedback_correlated=state.world_effect_feedback_correlated,
        world_grounding_confidence=state.world_grounding_confidence,
        world_require_grounded_transition=state.world_require_grounded_transition,
        world_require_effect_feedback_for_success_claim=(
            state.world_require_effect_feedback_for_success_claim
        ),
        world_adapter_reason=state.world_adapter_reason,
        world_entry_episode_id=state.world_entry_episode_id,
        world_entry_presence_mode=state.world_entry_presence_mode,
        world_entry_episode_scope=state.world_entry_episode_scope,
        world_entry_observation_basis_present=state.world_entry_observation_basis_present,
        world_entry_action_trace_present=state.world_entry_action_trace_present,
        world_entry_effect_basis_present=state.world_entry_effect_basis_present,
        world_entry_effect_feedback_correlated=state.world_entry_effect_feedback_correlated,
        world_entry_confidence=state.world_entry_confidence,
        world_entry_reliability=state.world_entry_reliability,
        world_entry_degraded=state.world_entry_degraded,
        world_entry_incomplete=state.world_entry_incomplete,
        world_entry_forbidden_claim_classes=state.world_entry_forbidden_claim_classes,
        world_entry_world_grounded_transition_admissible=(
            state.world_entry_world_grounded_transition_admissible
        ),
        world_entry_world_effect_success_admissible=(
            state.world_entry_world_effect_success_admissible
        ),
        world_entry_w01_admission_ready=state.world_entry_w01_admission_ready,
        world_entry_w01_admission_restrictions=state.world_entry_w01_admission_restrictions,
        world_entry_scope=state.world_entry_scope,
        world_entry_scope_admission_layer_only=state.world_entry_scope_admission_layer_only,
        world_entry_scope_w01_implemented=state.world_entry_scope_w01_implemented,
        world_entry_scope_w_line_implemented=state.world_entry_scope_w_line_implemented,
        world_entry_scope_repo_wide_adoption=state.world_entry_scope_repo_wide_adoption,
        world_entry_scope_reason=state.world_entry_scope_reason,
        world_entry_reason=state.world_entry_reason,
        s_boundary_state_id=state.s_boundary_state_id,
        s_self_attribution_basis_present=state.s_self_attribution_basis_present,
        s_world_attribution_basis_present=state.s_world_attribution_basis_present,
        s_controllability_estimate=state.s_controllability_estimate,
        s_ownership_estimate=state.s_ownership_estimate,
        s_attribution_confidence=state.s_attribution_confidence,
        s_source_status=state.s_source_status,
        s_boundary_breach_risk=state.s_boundary_breach_risk,
        s_attribution_class=state.s_attribution_class,
        s_no_safe_self_claim=state.s_no_safe_self_claim,
        s_no_safe_world_claim=state.s_no_safe_world_claim,
        s_degraded=state.s_degraded,
        s_underconstrained=state.s_underconstrained,
        s_forbidden_shortcuts=state.s_forbidden_shortcuts,
        s_restrictions=state.s_restrictions,
        s_s01_admission_ready=state.s_s01_admission_ready,
        s_self_attribution_basis_sufficient=state.s_self_attribution_basis_sufficient,
        s_controllability_basis_sufficient=state.s_controllability_basis_sufficient,
        s_ownership_basis_sufficient=state.s_ownership_basis_sufficient,
        s_attribution_underconstrained=state.s_attribution_underconstrained,
        s_mixed_boundary_instability=state.s_mixed_boundary_instability,
        s_no_safe_self_basis=state.s_no_safe_self_basis,
        s_no_safe_world_basis=state.s_no_safe_world_basis,
        s_readiness_blockers=state.s_readiness_blockers,
        s_future_s01_s05_remain_open=state.s_future_s01_s05_remain_open,
        s_full_self_model_implemented=state.s_full_self_model_implemented,
        s_scope=state.s_scope,
        s_scope_rt01_contour_only=state.s_scope_rt01_contour_only,
        s_scope_s_minimal_only=state.s_scope_s_minimal_only,
        s_scope_s01_implemented=state.s_scope_s01_implemented,
        s_scope_s_line_implemented=state.s_scope_s_line_implemented,
        s_scope_minimal_contour_only=state.s_scope_minimal_contour_only,
        s_scope_s01_s05_implemented=state.s_scope_s01_s05_implemented,
        s_scope_full_self_model_implemented=state.s_scope_full_self_model_implemented,
        s_scope_repo_wide_adoption=state.s_scope_repo_wide_adoption,
        s_scope_reason=state.s_scope_reason,
        s_reason=state.s_reason,
        s_require_self_side_claim=state.s_require_self_side_claim,
        s_require_world_side_claim=state.s_require_world_side_claim,
        s_require_self_controlled_transition_claim=(
            state.s_require_self_controlled_transition_claim
        ),
        s_strict_mixed_attribution_guard=state.s_strict_mixed_attribution_guard,
        a_capability_id=state.a_capability_id,
        a_affordance_id=state.a_affordance_id,
        a_capability_class=state.a_capability_class,
        a_capability_status=state.a_capability_status,
        a_availability_basis_present=state.a_availability_basis_present,
        a_world_dependency_present=state.a_world_dependency_present,
        a_self_dependency_present=state.a_self_dependency_present,
        a_controllability_dependency_present=state.a_controllability_dependency_present,
        a_legitimacy_dependency_present=state.a_legitimacy_dependency_present,
        a_confidence=state.a_confidence,
        a_degraded=state.a_degraded,
        a_underconstrained=state.a_underconstrained,
        a_available_capability_claim_allowed=state.a_available_capability_claim_allowed,
        a_world_conditioned_capability_claim_allowed=(
            state.a_world_conditioned_capability_claim_allowed
        ),
        a_self_conditioned_capability_claim_allowed=(
            state.a_self_conditioned_capability_claim_allowed
        ),
        a_policy_conditioned_capability_present=(
            state.a_policy_conditioned_capability_present
        ),
        a_no_safe_capability_claim=state.a_no_safe_capability_claim,
        a_forbidden_shortcuts=state.a_forbidden_shortcuts,
        a_restrictions=state.a_restrictions,
        a_a04_admission_ready=state.a_a04_admission_ready,
        a_a04_blockers=state.a_a04_blockers,
        a_a04_structurally_present_but_not_ready=(
            state.a_a04_structurally_present_but_not_ready
        ),
        a_a04_capability_basis_missing=state.a_a04_capability_basis_missing,
        a_a04_world_dependency_unmet=state.a_a04_world_dependency_unmet,
        a_a04_self_dependency_unmet=state.a_a04_self_dependency_unmet,
        a_a04_policy_legitimacy_unmet=state.a_a04_policy_legitimacy_unmet,
        a_a04_underconstrained_capability_surface=(
            state.a_a04_underconstrained_capability_surface
        ),
        a_a04_external_means_not_justified=(
            state.a_a04_external_means_not_justified
        ),
        a_a04_implemented=state.a_a04_implemented,
        a_a05_touched=state.a_a05_touched,
        a_scope=state.a_scope,
        a_scope_rt01_contour_only=state.a_scope_rt01_contour_only,
        a_scope_a_line_normalization_only=state.a_scope_a_line_normalization_only,
        a_scope_readiness_gate_only=state.a_scope_readiness_gate_only,
        a_scope_a04_implemented=state.a_scope_a04_implemented,
        a_scope_a05_touched=state.a_scope_a05_touched,
        a_scope_full_agency_stack_implemented=state.a_scope_full_agency_stack_implemented,
        a_scope_repo_wide_adoption=state.a_scope_repo_wide_adoption,
        a_scope_reason=state.a_scope_reason,
        a_reason=state.a_reason,
        a_require_capability_claim=state.a_require_capability_claim,
        m_memory_item_id=state.m_memory_item_id,
        m_memory_packet_id=state.m_memory_packet_id,
        m_lifecycle_status=state.m_lifecycle_status,
        m_retention_class=state.m_retention_class,
        m_bounded_persistence_allowed=state.m_bounded_persistence_allowed,
        m_temporary_carry_allowed=state.m_temporary_carry_allowed,
        m_review_required=state.m_review_required,
        m_reactivation_eligible=state.m_reactivation_eligible,
        m_decay_eligible=state.m_decay_eligible,
        m_pruning_eligible=state.m_pruning_eligible,
        m_stale_risk=state.m_stale_risk,
        m_conflict_risk=state.m_conflict_risk,
        m_confidence=state.m_confidence,
        m_reliability=state.m_reliability,
        m_degraded=state.m_degraded,
        m_underconstrained=state.m_underconstrained,
        m_safe_memory_claim_allowed=state.m_safe_memory_claim_allowed,
        m_bounded_retained_claim_allowed=state.m_bounded_retained_claim_allowed,
        m_no_safe_memory_claim=state.m_no_safe_memory_claim,
        m_forbidden_shortcuts=state.m_forbidden_shortcuts,
        m_restrictions=state.m_restrictions,
        m_m01_admission_ready=state.m_m01_admission_ready,
        m_m01_blockers=state.m_m01_blockers,
        m_m01_structurally_present_but_not_ready=(
            state.m_m01_structurally_present_but_not_ready
        ),
        m_m01_stale_risk_unacceptable=state.m_m01_stale_risk_unacceptable,
        m_m01_conflict_risk_unacceptable=state.m_m01_conflict_risk_unacceptable,
        m_m01_reactivation_requires_review=state.m_m01_reactivation_requires_review,
        m_m01_temporary_carry_not_stable_enough=(
            state.m_m01_temporary_carry_not_stable_enough
        ),
        m_m01_no_safe_memory_basis=state.m_m01_no_safe_memory_basis,
        m_m01_provenance_insufficient=state.m_m01_provenance_insufficient,
        m_m01_lifecycle_underconstrained=state.m_m01_lifecycle_underconstrained,
        m_m01_implemented=state.m_m01_implemented,
        m_m02_implemented=state.m_m02_implemented,
        m_m03_implemented=state.m_m03_implemented,
        m_scope=state.m_scope,
        m_scope_rt01_contour_only=state.m_scope_rt01_contour_only,
        m_scope_m_minimal_only=state.m_scope_m_minimal_only,
        m_scope_readiness_gate_only=state.m_scope_readiness_gate_only,
        m_scope_m01_implemented=state.m_scope_m01_implemented,
        m_scope_m02_implemented=state.m_scope_m02_implemented,
        m_scope_m03_implemented=state.m_scope_m03_implemented,
        m_scope_full_memory_stack_implemented=state.m_scope_full_memory_stack_implemented,
        m_scope_repo_wide_adoption=state.m_scope_repo_wide_adoption,
        m_scope_reason=state.m_scope_reason,
        m_reason=state.m_reason,
        m_require_memory_safe_claim=state.m_require_memory_safe_claim,
        n_narrative_commitment_id=state.n_narrative_commitment_id,
        n_commitment_status=state.n_commitment_status,
        n_commitment_scope=state.n_commitment_scope,
        n_narrative_basis_present=state.n_narrative_basis_present,
        n_self_basis_present=state.n_self_basis_present,
        n_world_basis_present=state.n_world_basis_present,
        n_memory_basis_present=state.n_memory_basis_present,
        n_capability_basis_present=state.n_capability_basis_present,
        n_ambiguity_residue=state.n_ambiguity_residue,
        n_contradiction_risk=state.n_contradiction_risk,
        n_confidence=state.n_confidence,
        n_degraded=state.n_degraded,
        n_underconstrained=state.n_underconstrained,
        n_safe_narrative_commitment_allowed=state.n_safe_narrative_commitment_allowed,
        n_bounded_commitment_allowed=state.n_bounded_commitment_allowed,
        n_no_safe_narrative_claim=state.n_no_safe_narrative_claim,
        n_forbidden_shortcuts=state.n_forbidden_shortcuts,
        n_restrictions=state.n_restrictions,
        n_n01_admission_ready=state.n_n01_admission_ready,
        n_n01_blockers=state.n_n01_blockers,
        n_n01_implemented=state.n_n01_implemented,
        n_n02_implemented=state.n_n02_implemented,
        n_n03_implemented=state.n_n03_implemented,
        n_n04_implemented=state.n_n04_implemented,
        n_scope=state.n_scope,
        n_scope_rt01_contour_only=state.n_scope_rt01_contour_only,
        n_scope_n_minimal_only=state.n_scope_n_minimal_only,
        n_scope_readiness_gate_only=state.n_scope_readiness_gate_only,
        n_scope_n01_implemented=state.n_scope_n01_implemented,
        n_scope_n02_implemented=state.n_scope_n02_implemented,
        n_scope_n03_implemented=state.n_scope_n03_implemented,
        n_scope_n04_implemented=state.n_scope_n04_implemented,
        n_scope_full_narrative_line_implemented=(
            state.n_scope_full_narrative_line_implemented
        ),
        n_scope_repo_wide_adoption=state.n_scope_repo_wide_adoption,
        n_scope_reason=state.n_scope_reason,
        n_reason=state.n_reason,
        n_require_narrative_safe_claim=state.n_require_narrative_safe_claim,
        t01_scene_id=state.t01_scene_id,
        t01_scene_status=state.t01_scene_status,
        t01_stability_state=state.t01_stability_state,
        t01_active_entities_count=state.t01_active_entities_count,
        t01_relation_edges_count=state.t01_relation_edges_count,
        t01_role_bindings_count=state.t01_role_bindings_count,
        t01_unresolved_slots_count=state.t01_unresolved_slots_count,
        t01_contested_relations_count=state.t01_contested_relations_count,
        t01_preverbal_consumer_ready=state.t01_preverbal_consumer_ready,
        t01_scene_comparison_ready=state.t01_scene_comparison_ready,
        t01_no_clean_scene_commit=state.t01_no_clean_scene_commit,
        t01_forbidden_shortcuts=state.t01_forbidden_shortcuts,
        t01_restrictions=state.t01_restrictions,
        t01_scope=state.t01_scope,
        t01_scope_rt01_contour_only=state.t01_scope_rt01_contour_only,
        t01_scope_t01_first_slice_only=state.t01_scope_t01_first_slice_only,
        t01_scope_t02_implemented=state.t01_scope_t02_implemented,
        t01_scope_t03_implemented=state.t01_scope_t03_implemented,
        t01_scope_t04_implemented=state.t01_scope_t04_implemented,
        t01_scope_o01_implemented=state.t01_scope_o01_implemented,
        t01_scope_full_silent_thought_line_implemented=(
            state.t01_scope_full_silent_thought_line_implemented
        ),
        t01_scope_repo_wide_adoption=state.t01_scope_repo_wide_adoption,
        t01_scope_reason=state.t01_scope_reason,
        t01_reason=state.t01_reason,
        t01_require_preverbal_scene_consumer=(
            state.t01_require_preverbal_scene_consumer
        ),
        t01_require_scene_comparison_consumer=(
            state.t01_require_scene_comparison_consumer
        ),
        s01_latest_comparison_status=state.s01_latest_comparison_status,
        s01_comparison_ready=state.s01_comparison_ready,
        s01_unexpected_change_detected=state.s01_unexpected_change_detected,
        s01_prediction_validity_ready=state.s01_prediction_validity_ready,
        s01_comparison_blocked_by_contamination=(
            state.s01_comparison_blocked_by_contamination
        ),
        s01_stale_prediction_detected=state.s01_stale_prediction_detected,
        s01_pending_predictions_count=state.s01_pending_predictions_count,
        s01_comparisons_count=state.s01_comparisons_count,
        s01_require_comparison_consumer=state.s01_require_comparison_consumer,
        s01_require_unexpected_change_consumer=(
            state.s01_require_unexpected_change_consumer
        ),
        s01_require_prediction_validity_consumer=(
            state.s01_require_prediction_validity_consumer
        ),
        s02_boundary_id=state.s02_boundary_id,
        s02_active_boundary_status=state.s02_active_boundary_status,
        s02_boundary_uncertain=state.s02_boundary_uncertain,
        s02_insufficient_coverage=state.s02_insufficient_coverage,
        s02_no_clean_seam_claim=state.s02_no_clean_seam_claim,
        s02_controllability_estimate=state.s02_controllability_estimate,
        s02_prediction_reliability_estimate=state.s02_prediction_reliability_estimate,
        s02_external_dominance_estimate=state.s02_external_dominance_estimate,
        s02_mixed_source_score=state.s02_mixed_source_score,
        s02_boundary_confidence=state.s02_boundary_confidence,
        s02_boundary_consumer_ready=state.s02_boundary_consumer_ready,
        s02_controllability_consumer_ready=state.s02_controllability_consumer_ready,
        s02_mixed_source_consumer_ready=state.s02_mixed_source_consumer_ready,
        s02_forbidden_shortcuts=state.s02_forbidden_shortcuts,
        s02_restrictions=state.s02_restrictions,
        s02_scope=state.s02_scope,
        s02_scope_rt01_contour_only=state.s02_scope_rt01_contour_only,
        s02_scope_s02_first_slice_only=state.s02_scope_s02_first_slice_only,
        s02_scope_s03_implemented=state.s02_scope_s03_implemented,
        s02_scope_s04_implemented=state.s02_scope_s04_implemented,
        s02_scope_s05_implemented=state.s02_scope_s05_implemented,
        s02_scope_full_self_model_implemented=state.s02_scope_full_self_model_implemented,
        s02_scope_repo_wide_adoption=state.s02_scope_repo_wide_adoption,
        s02_scope_reason=state.s02_scope_reason,
        s02_reason=state.s02_reason,
        s02_require_boundary_consumer=state.s02_require_boundary_consumer,
        s02_require_controllability_consumer=state.s02_require_controllability_consumer,
        s02_require_mixed_source_consumer=state.s02_require_mixed_source_consumer,
        t02_constrained_scene_id=(
            None if t02_result is None else t02_result.state.constrained_scene_id
        ),
        t02_scene_status=(
            None if t02_result is None else t02_result.state.scene_status.value
        ),
        t02_preverbal_constraint_consumer_ready=(
            None if t02_result is None else t02_result.gate.pre_verbal_constraint_consumer_ready
        ),
        t02_no_clean_binding_commit=(
            None if t02_result is None else t02_result.gate.no_clean_binding_commit
        ),
        t02_confirmed_bindings_count=(
            None
            if t02_result is None
            else sum(
                1
                for item in t02_result.state.relation_bindings
                if item.status.value == "confirmed"
            )
        ),
        t02_provisional_bindings_count=(
            None
            if t02_result is None
            else sum(
                1
                for item in t02_result.state.relation_bindings
                if item.status.value == "provisional"
            )
        ),
        t02_blocked_bindings_count=(
            None
            if t02_result is None
            else sum(
                1
                for item in t02_result.state.relation_bindings
                if item.status.value == "blocked"
            )
        ),
        t02_conflicted_bindings_count=(
            None
            if t02_result is None
            else sum(
                1
                for item in t02_result.state.relation_bindings
                if item.status.value in {"conflicted", "incompatible"}
            )
        ),
        t02_propagated_consequences_count=(
            None
            if t02_result is None
            else sum(
                1
                for item in t02_result.state.propagation_records
                if item.effect_type.value != "no_effect" and item.status.value == "active"
            )
        ),
        t02_blocked_or_conflicted_consequences_count=(
            None
            if t02_result is None
            else sum(
                1
                for item in t02_result.state.propagation_records
                if item.status.value in {"blocked", "stopped"}
            )
        ),
        t02_forbidden_shortcuts=(
            None if t02_result is None else t02_result.gate.forbidden_shortcuts
        ),
        t02_scope=(None if t02_result is None else t02_result.scope_marker.scope),
        t02_scope_rt01_contour_only=(
            None if t02_result is None else t02_result.scope_marker.rt01_contour_only
        ),
        t02_scope_t02_first_slice_only=(
            None if t02_result is None else t02_result.scope_marker.t02_first_slice_only
        ),
        t02_scope_t03_implemented=(
            None if t02_result is None else t02_result.scope_marker.t03_implemented
        ),
        t02_scope_t04_implemented=(
            None if t02_result is None else t02_result.scope_marker.t04_implemented
        ),
        t02_scope_o01_implemented=(
            None if t02_result is None else t02_result.scope_marker.o01_implemented
        ),
        t02_scope_full_silent_thought_line_implemented=(
            None
            if t02_result is None
            else t02_result.scope_marker.full_silent_thought_line_implemented
        ),
        t02_scope_repo_wide_adoption=(
            None if t02_result is None else t02_result.scope_marker.repo_wide_adoption
        ),
        t02_require_constrained_scene_consumer=state.t02_require_constrained_scene_consumer,
        t02_require_raw_vs_propagated_distinction=(
            state.t02_require_raw_vs_propagated_distinction
        ),
        t02_raw_vs_propagated_distinct=state.t02_raw_vs_propagated_distinct,
        t03_competition_id=(
            None if t03_result is None else t03_result.state.competition_id
        ),
        t03_convergence_status=(
            None if t03_result is None else t03_result.state.convergence_status.value
        ),
        t03_current_leader_hypothesis_id=(
            None if t03_result is None else t03_result.state.current_leader_hypothesis_id
        ),
        t03_provisional_frontrunner_hypothesis_id=(
            None
            if t03_result is None
            else t03_result.state.provisional_frontrunner_hypothesis_id
        ),
        t03_tied_competitor_count=(
            None if t03_result is None else len(t03_result.state.tied_competitor_ids)
        ),
        t03_blocked_hypothesis_count=(
            None if t03_result is None else len(t03_result.state.blocked_hypothesis_ids)
        ),
        t03_eliminated_hypothesis_count=(
            None if t03_result is None else len(t03_result.state.eliminated_hypothesis_ids)
        ),
        t03_reactivated_hypothesis_count=(
            None if t03_result is None else len(t03_result.state.reactivated_hypothesis_ids)
        ),
        t03_honest_nonconvergence=(
            None if t03_result is None else t03_result.state.honest_nonconvergence
        ),
        t03_bounded_plurality=(
            None if t03_result is None else t03_result.state.bounded_plurality
        ),
        t03_convergence_consumer_ready=(
            None if t03_result is None else t03_result.gate.convergence_consumer_ready
        ),
        t03_frontier_consumer_ready=(
            None if t03_result is None else t03_result.gate.frontier_consumer_ready
        ),
        t03_nonconvergence_preserved=(
            None if t03_result is None else t03_result.gate.nonconvergence_preserved
        ),
        t03_forbidden_shortcuts=(
            None if t03_result is None else t03_result.gate.forbidden_shortcuts
        ),
        t03_restrictions=(
            None if t03_result is None else t03_result.gate.restrictions
        ),
        t03_publication_current_leader=(
            None if t03_result is None else t03_result.state.publication_frontier.current_leader
        ),
        t03_publication_competitive_neighborhood=(
            None
            if t03_result is None
            else t03_result.state.publication_frontier.competitive_neighborhood
        ),
        t03_publication_unresolved_conflicts=(
            None
            if t03_result is None
            else t03_result.state.publication_frontier.unresolved_conflicts
        ),
        t03_publication_open_slots=(
            None if t03_result is None else t03_result.state.publication_frontier.open_slots
        ),
        t03_publication_stability_status=(
            None
            if t03_result is None
            else t03_result.state.publication_frontier.stability_status
        ),
        t03_scope=(None if t03_result is None else t03_result.scope_marker.scope),
        t03_scope_rt01_contour_only=(
            None if t03_result is None else t03_result.scope_marker.rt01_contour_only
        ),
        t03_scope_t03_first_slice_only=(
            None if t03_result is None else t03_result.scope_marker.t03_first_slice_only
        ),
        t03_scope_t04_implemented=(
            None if t03_result is None else t03_result.scope_marker.t04_implemented
        ),
        t03_scope_o01_implemented=(
            None if t03_result is None else t03_result.scope_marker.o01_implemented
        ),
        t03_scope_o02_implemented=(
            None if t03_result is None else t03_result.scope_marker.o02_implemented
        ),
        t03_scope_o03_implemented=(
            None if t03_result is None else t03_result.scope_marker.o03_implemented
        ),
        t03_scope_full_silent_thought_line_implemented=(
            None
            if t03_result is None
            else t03_result.scope_marker.full_silent_thought_line_implemented
        ),
        t03_scope_repo_wide_adoption=(
            None if t03_result is None else t03_result.scope_marker.repo_wide_adoption
        ),
        t03_require_convergence_consumer=state.t03_require_convergence_consumer,
        t03_require_frontier_consumer=state.t03_require_frontier_consumer,
        t03_require_nonconvergence_preservation=(
            state.t03_require_nonconvergence_preservation
        ),
        t04_schema_id=(None if t04_result is None else t04_result.state.schema_id),
        t04_focus_targets_count=(
            None if t04_result is None else len(t04_result.state.focus_targets)
        ),
        t04_peripheral_targets_count=(
            None if t04_result is None else len(t04_result.state.peripheral_targets)
        ),
        t04_attention_owner=(
            None if t04_result is None else t04_result.state.attention_owner.value
        ),
        t04_focus_mode=(
            None if t04_result is None else t04_result.state.focus_mode.value
        ),
        t04_control_estimate=(
            None if t04_result is None else t04_result.state.control_estimate
        ),
        t04_stability_estimate=(
            None if t04_result is None else t04_result.state.stability_estimate
        ),
        t04_redirect_cost=(
            None if t04_result is None else t04_result.state.redirect_cost
        ),
        t04_reportability_status=(
            None if t04_result is None else t04_result.state.reportability_status.value
        ),
        t04_focus_ownership_consumer_ready=(
            None if t04_result is None else t04_result.gate.focus_ownership_consumer_ready
        ),
        t04_reportable_focus_consumer_ready=(
            None if t04_result is None else t04_result.gate.reportable_focus_consumer_ready
        ),
        t04_peripheral_preservation_ready=(
            None if t04_result is None else t04_result.gate.peripheral_preservation_ready
        ),
        t04_forbidden_shortcuts=(
            None if t04_result is None else t04_result.gate.forbidden_shortcuts
        ),
        t04_restrictions=(None if t04_result is None else t04_result.gate.restrictions),
        t04_scope=(None if t04_result is None else t04_result.scope_marker.scope),
        t04_scope_rt01_contour_only=(
            None if t04_result is None else t04_result.scope_marker.rt01_contour_only
        ),
        t04_scope_t04_first_slice_only=(
            None if t04_result is None else t04_result.scope_marker.t04_first_slice_only
        ),
        t04_scope_o01_implemented=(
            None if t04_result is None else t04_result.scope_marker.o01_implemented
        ),
        t04_scope_o02_implemented=(
            None if t04_result is None else t04_result.scope_marker.o02_implemented
        ),
        t04_scope_o03_implemented=(
            None if t04_result is None else t04_result.scope_marker.o03_implemented
        ),
        t04_scope_full_attention_line_implemented=(
            None
            if t04_result is None
            else t04_result.scope_marker.full_attention_line_implemented
        ),
        t04_scope_repo_wide_adoption=(
            None if t04_result is None else t04_result.scope_marker.repo_wide_adoption
        ),
        t04_require_focus_ownership_consumer=(
            state.t04_require_focus_ownership_consumer
        ),
        t04_require_reportable_focus_consumer=(
            state.t04_require_reportable_focus_consumer
        ),
        t04_require_peripheral_preservation=(
            state.t04_require_peripheral_preservation
        ),
        execution_stance=state.execution_stance.value,
        execution_checkpoints=tuple(
            f"{checkpoint.checkpoint_id}:{checkpoint.status.value}"
            for checkpoint in state.execution_checkpoints
        ),
        final_execution_outcome=state.final_execution_outcome,
        repair_needed=state.repair_needed,
        revalidation_needed=state.revalidation_needed,
        halt_reason=state.halt_reason,
        gate_accepted=gate.accepted,
        restrictions=tuple(code.value for code in gate.restrictions),
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason=(
            "runtime contour contract requires C04/C05 claims, world-entry basis, s-minimal "
            "self/world boundary, s01 comparator and s02 prediction-boundary seam, a-line "
            "normalization, m-minimal lifecycle, n-minimal narrative commitment, t01 semantic "
            "field checkpoints, t02 raw-vs-propagated distinction, t03 hypothesis competition "
            "frontier, and t04 attention schema focus-ownership surfaces to be read"
        ),
    )


def derive_subject_tick_runtime_domain_contract_view(
    runtime_state: RuntimeState,
) -> SubjectTickRuntimeDomainContractView:
    if not isinstance(runtime_state, RuntimeState):
        raise TypeError("derive_subject_tick_runtime_domain_contract_view requires RuntimeState")

    regulation = runtime_state.domains.regulation
    continuity = runtime_state.domains.continuity
    validity = runtime_state.domains.validity
    if validity.no_safe_reuse:
        outcome = "halt"
        reason = "shared validity no_safe_reuse blocks continuation"
    elif validity.revalidation_required or not validity.legality_reuse_allowed:
        outcome = "revalidate"
        reason = "shared validity requires bounded revalidation before continuation"
    elif not continuity.mode_legitimacy:
        outcome = "repair"
        reason = "shared continuity marks mode legitimacy failure"
    else:
        outcome = "continue"
        reason = "shared runtime domains allow bounded continuation"

    return SubjectTickRuntimeDomainContractView(
        regulation_pressure_level=regulation.pressure_level,
        regulation_override_scope=regulation.override_scope,
        continuity_mode_claim=continuity.c04_mode_claim,
        continuity_mode_legitimacy=continuity.mode_legitimacy,
        validity_action_claim=validity.c05_action_claim,
        validity_legality_reuse_allowed=validity.legality_reuse_allowed,
        validity_revalidation_required=validity.revalidation_required,
        validity_no_safe_reuse=validity.no_safe_reuse,
        recommended_outcome=outcome,
        source_of_truth_surface="runtime_state.domains",
        packet_snapshot_precedence_blocked=True,
        reason=reason,
    )


def choose_runtime_execution_outcome(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult,
) -> str:
    view = derive_subject_tick_contract_view(subject_tick_state_or_result)
    if not view.gate_accepted or view.final_execution_outcome == SubjectTickOutcome.HALT:
        return "halt"
    if view.final_execution_outcome == SubjectTickOutcome.REVALIDATE:
        return "revalidate"
    if view.final_execution_outcome == SubjectTickOutcome.REPAIR:
        return "repair"
    return "continue"


def choose_runtime_execution_outcome_from_runtime_state(runtime_state: RuntimeState) -> str:
    view = derive_subject_tick_runtime_domain_contract_view(runtime_state)
    return view.recommended_outcome


def require_subject_tick_bounded_n_scope(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult | SubjectTickContractView,
) -> SubjectTickContractView:
    view = (
        subject_tick_state_or_result
        if isinstance(subject_tick_state_or_result, SubjectTickContractView)
        else derive_subject_tick_contract_view(subject_tick_state_or_result)
    )
    if (
        view.n_scope != "rt01_contour_only"
        or not view.n_scope_rt01_contour_only
        or not view.n_scope_n_minimal_only
        or not view.n_scope_readiness_gate_only
        or view.n_scope_n01_implemented
        or view.n_scope_n02_implemented
        or view.n_scope_n03_implemented
        or view.n_scope_n04_implemented
        or view.n_scope_full_narrative_line_implemented
        or view.n_scope_repo_wide_adoption
    ):
        raise PermissionError(
            "subject_tick n-surface does not satisfy bounded rt01 contour-only non-claim scope contract"
        )
    return view


def require_subject_tick_strong_narrative_commitment(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult | SubjectTickContractView,
) -> SubjectTickContractView:
    view = require_subject_tick_bounded_n_scope(subject_tick_state_or_result)
    if not view.n_safe_narrative_commitment_allowed or view.n_no_safe_narrative_claim:
        raise PermissionError(
            "subject_tick strong narrative commitment requires safe bounded n-minimal basis"
        )
    return view
