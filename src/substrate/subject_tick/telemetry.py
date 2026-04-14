from __future__ import annotations

from substrate.subject_tick.models import (
    SubjectTickGateDecision,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickStepResult,
    SubjectTickTelemetry,
)


def build_subject_tick_telemetry(
    *,
    state: SubjectTickState,
    attempted_paths: tuple[str, ...],
    downstream_gate: SubjectTickGateDecision,
    causal_basis: str,
) -> SubjectTickTelemetry:
    return SubjectTickTelemetry(
        tick_id=state.tick_id,
        tick_index=state.tick_index,
        source_lineage=state.source_lineage,
        phase_order=tuple(step.phase_id for step in state.downstream_step_results),
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
        s_require_self_controlled_transition_claim=state.s_require_self_controlled_transition_claim,
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
        a_policy_conditioned_capability_present=state.a_policy_conditioned_capability_present,
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
        t02_require_constrained_scene_consumer=state.t02_require_constrained_scene_consumer,
        t02_require_raw_vs_propagated_distinction=(
            state.t02_require_raw_vs_propagated_distinction
        ),
        t02_raw_vs_propagated_distinct=state.t02_raw_vs_propagated_distinct,
        t03_competition_id=state.t03_competition_id,
        t03_convergence_status=state.t03_convergence_status,
        t03_current_leader_hypothesis_id=state.t03_current_leader_hypothesis_id,
        t03_provisional_frontrunner_hypothesis_id=(
            state.t03_provisional_frontrunner_hypothesis_id
        ),
        t03_tied_competitor_count=state.t03_tied_competitor_count,
        t03_blocked_hypothesis_count=state.t03_blocked_hypothesis_count,
        t03_eliminated_hypothesis_count=state.t03_eliminated_hypothesis_count,
        t03_reactivated_hypothesis_count=state.t03_reactivated_hypothesis_count,
        t03_honest_nonconvergence=state.t03_honest_nonconvergence,
        t03_bounded_plurality=state.t03_bounded_plurality,
        t03_convergence_consumer_ready=state.t03_convergence_consumer_ready,
        t03_frontier_consumer_ready=state.t03_frontier_consumer_ready,
        t03_nonconvergence_preserved=state.t03_nonconvergence_preserved,
        t03_forbidden_shortcuts=state.t03_forbidden_shortcuts,
        t03_restrictions=state.t03_restrictions,
        t03_publication_current_leader=state.t03_publication_current_leader,
        t03_publication_competitive_neighborhood=state.t03_publication_competitive_neighborhood,
        t03_publication_unresolved_conflicts=state.t03_publication_unresolved_conflicts,
        t03_publication_open_slots=state.t03_publication_open_slots,
        t03_publication_stability_status=state.t03_publication_stability_status,
        t03_scope=state.t03_scope,
        t03_scope_rt01_contour_only=state.t03_scope_rt01_contour_only,
        t03_scope_t03_first_slice_only=state.t03_scope_t03_first_slice_only,
        t03_scope_t04_implemented=state.t03_scope_t04_implemented,
        t03_scope_o01_implemented=state.t03_scope_o01_implemented,
        t03_scope_o02_implemented=state.t03_scope_o02_implemented,
        t03_scope_o03_implemented=state.t03_scope_o03_implemented,
        t03_scope_full_silent_thought_line_implemented=(
            state.t03_scope_full_silent_thought_line_implemented
        ),
        t03_scope_repo_wide_adoption=state.t03_scope_repo_wide_adoption,
        t03_scope_reason=state.t03_scope_reason,
        t03_reason=state.t03_reason,
        t03_require_convergence_consumer=state.t03_require_convergence_consumer,
        t03_require_frontier_consumer=state.t03_require_frontier_consumer,
        t03_require_nonconvergence_preservation=(
            state.t03_require_nonconvergence_preservation
        ),
        execution_stance=state.execution_stance,
        execution_checkpoints=state.execution_checkpoints,
        final_execution_outcome=state.final_execution_outcome,
        repair_needed=state.repair_needed,
        revalidation_needed=state.revalidation_needed,
        halt_reason=state.halt_reason,
        step_results=state.downstream_step_results,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def subject_tick_result_snapshot(result: SubjectTickResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_planner_orchestrator_dependency": result.no_planner_orchestrator_dependency,
        "no_phase_semantics_override_dependency": result.no_phase_semantics_override_dependency,
        "state": {
            "tick_id": state.tick_id,
            "tick_index": state.tick_index,
            "prior_runtime_status": (
                None if state.prior_runtime_status is None else state.prior_runtime_status.value
            ),
            "c04_execution_mode_claim": state.c04_execution_mode_claim,
            "c05_execution_action_claim": state.c05_execution_action_claim,
            "f01_authority_role": state.f01_authority_role,
            "r04_authority_role": state.r04_authority_role,
            "c04_authority_role": state.c04_authority_role,
            "c05_authority_role": state.c05_authority_role,
            "d01_authority_role": state.d01_authority_role,
            "rt01_authority_role": state.rt01_authority_role,
            "role_source_ref": state.role_source_ref,
            "role_frontier_only": state.role_frontier_only,
            "role_map_ready": state.role_map_ready,
            "role_frontier_typed": state.role_frontier_typed,
            "f01_computational_role": state.f01_computational_role,
            "r04_computational_role": state.r04_computational_role,
            "c04_computational_role": state.c04_computational_role,
            "c05_computational_role": state.c05_computational_role,
            "d01_computational_role": state.d01_computational_role,
            "rt01_computational_role": state.rt01_computational_role,
            "active_execution_mode": state.active_execution_mode,
            "c04_selected_mode": state.c04_selected_mode,
            "c05_validity_action": state.c05_validity_action,
            "downstream_obedience_status": state.downstream_obedience_status,
            "downstream_obedience_fallback": state.downstream_obedience_fallback,
            "downstream_obedience_source_of_truth_surface": (
                state.downstream_obedience_source_of_truth_surface
            ),
            "downstream_obedience_requires_restrictions_read": (
                state.downstream_obedience_requires_restrictions_read
            ),
            "downstream_obedience_reason": state.downstream_obedience_reason,
            "world_adapter_presence": state.world_adapter_presence,
            "world_adapter_available": state.world_adapter_available,
            "world_adapter_degraded": state.world_adapter_degraded,
            "world_link_status": state.world_link_status,
            "world_effect_status": state.world_effect_status,
            "world_grounded_transition_allowed": state.world_grounded_transition_allowed,
            "world_externally_effected_change_claim_allowed": (
                state.world_externally_effected_change_claim_allowed
            ),
            "world_action_success_claim_allowed": state.world_action_success_claim_allowed,
            "world_effect_feedback_correlated": state.world_effect_feedback_correlated,
            "world_grounding_confidence": state.world_grounding_confidence,
            "world_require_grounded_transition": state.world_require_grounded_transition,
            "world_require_effect_feedback_for_success_claim": (
                state.world_require_effect_feedback_for_success_claim
            ),
            "world_adapter_reason": state.world_adapter_reason,
            "world_entry_episode_id": state.world_entry_episode_id,
            "world_entry_presence_mode": state.world_entry_presence_mode,
            "world_entry_episode_scope": state.world_entry_episode_scope,
            "world_entry_observation_basis_present": state.world_entry_observation_basis_present,
            "world_entry_action_trace_present": state.world_entry_action_trace_present,
            "world_entry_effect_basis_present": state.world_entry_effect_basis_present,
            "world_entry_effect_feedback_correlated": state.world_entry_effect_feedback_correlated,
            "world_entry_confidence": state.world_entry_confidence,
            "world_entry_reliability": state.world_entry_reliability,
            "world_entry_degraded": state.world_entry_degraded,
            "world_entry_incomplete": state.world_entry_incomplete,
            "world_entry_forbidden_claim_classes": state.world_entry_forbidden_claim_classes,
            "world_entry_world_grounded_transition_admissible": (
                state.world_entry_world_grounded_transition_admissible
            ),
            "world_entry_world_effect_success_admissible": (
                state.world_entry_world_effect_success_admissible
            ),
            "world_entry_w01_admission_ready": state.world_entry_w01_admission_ready,
            "world_entry_w01_admission_restrictions": state.world_entry_w01_admission_restrictions,
            "world_entry_scope": state.world_entry_scope,
            "world_entry_scope_admission_layer_only": state.world_entry_scope_admission_layer_only,
            "world_entry_scope_w01_implemented": state.world_entry_scope_w01_implemented,
            "world_entry_scope_w_line_implemented": state.world_entry_scope_w_line_implemented,
            "world_entry_scope_repo_wide_adoption": state.world_entry_scope_repo_wide_adoption,
            "world_entry_scope_reason": state.world_entry_scope_reason,
            "world_entry_reason": state.world_entry_reason,
            "s_boundary_state_id": state.s_boundary_state_id,
            "s_self_attribution_basis_present": state.s_self_attribution_basis_present,
            "s_world_attribution_basis_present": state.s_world_attribution_basis_present,
            "s_controllability_estimate": state.s_controllability_estimate,
            "s_ownership_estimate": state.s_ownership_estimate,
            "s_attribution_confidence": state.s_attribution_confidence,
            "s_source_status": state.s_source_status,
            "s_boundary_breach_risk": state.s_boundary_breach_risk,
            "s_attribution_class": state.s_attribution_class,
            "s_no_safe_self_claim": state.s_no_safe_self_claim,
            "s_no_safe_world_claim": state.s_no_safe_world_claim,
            "s_degraded": state.s_degraded,
            "s_underconstrained": state.s_underconstrained,
            "s_forbidden_shortcuts": state.s_forbidden_shortcuts,
            "s_restrictions": state.s_restrictions,
            "s_s01_admission_ready": state.s_s01_admission_ready,
            "s_self_attribution_basis_sufficient": state.s_self_attribution_basis_sufficient,
            "s_controllability_basis_sufficient": state.s_controllability_basis_sufficient,
            "s_ownership_basis_sufficient": state.s_ownership_basis_sufficient,
            "s_attribution_underconstrained": state.s_attribution_underconstrained,
            "s_mixed_boundary_instability": state.s_mixed_boundary_instability,
            "s_no_safe_self_basis": state.s_no_safe_self_basis,
            "s_no_safe_world_basis": state.s_no_safe_world_basis,
            "s_readiness_blockers": state.s_readiness_blockers,
            "s_future_s01_s05_remain_open": state.s_future_s01_s05_remain_open,
            "s_full_self_model_implemented": state.s_full_self_model_implemented,
            "s_scope": state.s_scope,
            "s_scope_rt01_contour_only": state.s_scope_rt01_contour_only,
            "s_scope_s_minimal_only": state.s_scope_s_minimal_only,
            "s_scope_s01_implemented": state.s_scope_s01_implemented,
            "s_scope_s_line_implemented": state.s_scope_s_line_implemented,
            "s_scope_minimal_contour_only": state.s_scope_minimal_contour_only,
            "s_scope_s01_s05_implemented": state.s_scope_s01_s05_implemented,
            "s_scope_full_self_model_implemented": state.s_scope_full_self_model_implemented,
            "s_scope_repo_wide_adoption": state.s_scope_repo_wide_adoption,
            "s_scope_reason": state.s_scope_reason,
            "s_reason": state.s_reason,
            "s_require_self_side_claim": state.s_require_self_side_claim,
            "s_require_world_side_claim": state.s_require_world_side_claim,
            "s_require_self_controlled_transition_claim": (
                state.s_require_self_controlled_transition_claim
            ),
            "s_strict_mixed_attribution_guard": state.s_strict_mixed_attribution_guard,
            "a_capability_id": state.a_capability_id,
            "a_affordance_id": state.a_affordance_id,
            "a_capability_class": state.a_capability_class,
            "a_capability_status": state.a_capability_status,
            "a_availability_basis_present": state.a_availability_basis_present,
            "a_world_dependency_present": state.a_world_dependency_present,
            "a_self_dependency_present": state.a_self_dependency_present,
            "a_controllability_dependency_present": state.a_controllability_dependency_present,
            "a_legitimacy_dependency_present": state.a_legitimacy_dependency_present,
            "a_confidence": state.a_confidence,
            "a_degraded": state.a_degraded,
            "a_underconstrained": state.a_underconstrained,
            "a_available_capability_claim_allowed": state.a_available_capability_claim_allowed,
            "a_world_conditioned_capability_claim_allowed": (
                state.a_world_conditioned_capability_claim_allowed
            ),
            "a_self_conditioned_capability_claim_allowed": (
                state.a_self_conditioned_capability_claim_allowed
            ),
            "a_policy_conditioned_capability_present": (
                state.a_policy_conditioned_capability_present
            ),
            "a_no_safe_capability_claim": state.a_no_safe_capability_claim,
            "a_forbidden_shortcuts": state.a_forbidden_shortcuts,
            "a_restrictions": state.a_restrictions,
            "a_a04_admission_ready": state.a_a04_admission_ready,
            "a_a04_blockers": state.a_a04_blockers,
            "a_a04_structurally_present_but_not_ready": (
                state.a_a04_structurally_present_but_not_ready
            ),
            "a_a04_capability_basis_missing": state.a_a04_capability_basis_missing,
            "a_a04_world_dependency_unmet": state.a_a04_world_dependency_unmet,
            "a_a04_self_dependency_unmet": state.a_a04_self_dependency_unmet,
            "a_a04_policy_legitimacy_unmet": state.a_a04_policy_legitimacy_unmet,
            "a_a04_underconstrained_capability_surface": (
                state.a_a04_underconstrained_capability_surface
            ),
            "a_a04_external_means_not_justified": (
                state.a_a04_external_means_not_justified
            ),
            "a_a04_implemented": state.a_a04_implemented,
            "a_a05_touched": state.a_a05_touched,
            "a_scope": state.a_scope,
            "a_scope_rt01_contour_only": state.a_scope_rt01_contour_only,
            "a_scope_a_line_normalization_only": state.a_scope_a_line_normalization_only,
            "a_scope_readiness_gate_only": state.a_scope_readiness_gate_only,
            "a_scope_a04_implemented": state.a_scope_a04_implemented,
            "a_scope_a05_touched": state.a_scope_a05_touched,
            "a_scope_full_agency_stack_implemented": (
                state.a_scope_full_agency_stack_implemented
            ),
            "a_scope_repo_wide_adoption": state.a_scope_repo_wide_adoption,
            "a_scope_reason": state.a_scope_reason,
            "a_reason": state.a_reason,
            "a_require_capability_claim": state.a_require_capability_claim,
            "m_memory_item_id": state.m_memory_item_id,
            "m_memory_packet_id": state.m_memory_packet_id,
            "m_lifecycle_status": state.m_lifecycle_status,
            "m_retention_class": state.m_retention_class,
            "m_bounded_persistence_allowed": state.m_bounded_persistence_allowed,
            "m_temporary_carry_allowed": state.m_temporary_carry_allowed,
            "m_review_required": state.m_review_required,
            "m_reactivation_eligible": state.m_reactivation_eligible,
            "m_decay_eligible": state.m_decay_eligible,
            "m_pruning_eligible": state.m_pruning_eligible,
            "m_stale_risk": state.m_stale_risk,
            "m_conflict_risk": state.m_conflict_risk,
            "m_confidence": state.m_confidence,
            "m_reliability": state.m_reliability,
            "m_degraded": state.m_degraded,
            "m_underconstrained": state.m_underconstrained,
            "m_safe_memory_claim_allowed": state.m_safe_memory_claim_allowed,
            "m_bounded_retained_claim_allowed": state.m_bounded_retained_claim_allowed,
            "m_no_safe_memory_claim": state.m_no_safe_memory_claim,
            "m_forbidden_shortcuts": state.m_forbidden_shortcuts,
            "m_restrictions": state.m_restrictions,
            "m_m01_admission_ready": state.m_m01_admission_ready,
            "m_m01_blockers": state.m_m01_blockers,
            "m_m01_structurally_present_but_not_ready": (
                state.m_m01_structurally_present_but_not_ready
            ),
            "m_m01_stale_risk_unacceptable": state.m_m01_stale_risk_unacceptable,
            "m_m01_conflict_risk_unacceptable": state.m_m01_conflict_risk_unacceptable,
            "m_m01_reactivation_requires_review": (
                state.m_m01_reactivation_requires_review
            ),
            "m_m01_temporary_carry_not_stable_enough": (
                state.m_m01_temporary_carry_not_stable_enough
            ),
            "m_m01_no_safe_memory_basis": state.m_m01_no_safe_memory_basis,
            "m_m01_provenance_insufficient": state.m_m01_provenance_insufficient,
            "m_m01_lifecycle_underconstrained": (
                state.m_m01_lifecycle_underconstrained
            ),
            "m_m01_implemented": state.m_m01_implemented,
            "m_m02_implemented": state.m_m02_implemented,
            "m_m03_implemented": state.m_m03_implemented,
            "m_scope": state.m_scope,
            "m_scope_rt01_contour_only": state.m_scope_rt01_contour_only,
            "m_scope_m_minimal_only": state.m_scope_m_minimal_only,
            "m_scope_readiness_gate_only": state.m_scope_readiness_gate_only,
            "m_scope_m01_implemented": state.m_scope_m01_implemented,
            "m_scope_m02_implemented": state.m_scope_m02_implemented,
            "m_scope_m03_implemented": state.m_scope_m03_implemented,
            "m_scope_full_memory_stack_implemented": (
                state.m_scope_full_memory_stack_implemented
            ),
            "m_scope_repo_wide_adoption": state.m_scope_repo_wide_adoption,
            "m_scope_reason": state.m_scope_reason,
            "m_reason": state.m_reason,
            "m_require_memory_safe_claim": state.m_require_memory_safe_claim,
            "n_narrative_commitment_id": state.n_narrative_commitment_id,
            "n_commitment_status": state.n_commitment_status,
            "n_commitment_scope": state.n_commitment_scope,
            "n_narrative_basis_present": state.n_narrative_basis_present,
            "n_self_basis_present": state.n_self_basis_present,
            "n_world_basis_present": state.n_world_basis_present,
            "n_memory_basis_present": state.n_memory_basis_present,
            "n_capability_basis_present": state.n_capability_basis_present,
            "n_ambiguity_residue": state.n_ambiguity_residue,
            "n_contradiction_risk": state.n_contradiction_risk,
            "n_confidence": state.n_confidence,
            "n_degraded": state.n_degraded,
            "n_underconstrained": state.n_underconstrained,
            "n_safe_narrative_commitment_allowed": (
                state.n_safe_narrative_commitment_allowed
            ),
            "n_bounded_commitment_allowed": state.n_bounded_commitment_allowed,
            "n_no_safe_narrative_claim": state.n_no_safe_narrative_claim,
            "n_forbidden_shortcuts": state.n_forbidden_shortcuts,
            "n_restrictions": state.n_restrictions,
            "n_n01_admission_ready": state.n_n01_admission_ready,
            "n_n01_blockers": state.n_n01_blockers,
            "n_n01_implemented": state.n_n01_implemented,
            "n_n02_implemented": state.n_n02_implemented,
            "n_n03_implemented": state.n_n03_implemented,
            "n_n04_implemented": state.n_n04_implemented,
            "n_scope": state.n_scope,
            "n_scope_rt01_contour_only": state.n_scope_rt01_contour_only,
            "n_scope_n_minimal_only": state.n_scope_n_minimal_only,
            "n_scope_readiness_gate_only": state.n_scope_readiness_gate_only,
            "n_scope_n01_implemented": state.n_scope_n01_implemented,
            "n_scope_n02_implemented": state.n_scope_n02_implemented,
            "n_scope_n03_implemented": state.n_scope_n03_implemented,
            "n_scope_n04_implemented": state.n_scope_n04_implemented,
            "n_scope_full_narrative_line_implemented": (
                state.n_scope_full_narrative_line_implemented
            ),
            "n_scope_repo_wide_adoption": state.n_scope_repo_wide_adoption,
            "n_scope_reason": state.n_scope_reason,
            "n_reason": state.n_reason,
            "n_require_narrative_safe_claim": state.n_require_narrative_safe_claim,
            "t01_scene_id": state.t01_scene_id,
            "t01_scene_status": state.t01_scene_status,
            "t01_stability_state": state.t01_stability_state,
            "t01_active_entities_count": state.t01_active_entities_count,
            "t01_relation_edges_count": state.t01_relation_edges_count,
            "t01_role_bindings_count": state.t01_role_bindings_count,
            "t01_unresolved_slots_count": state.t01_unresolved_slots_count,
            "t01_contested_relations_count": state.t01_contested_relations_count,
            "t01_preverbal_consumer_ready": state.t01_preverbal_consumer_ready,
            "t01_scene_comparison_ready": state.t01_scene_comparison_ready,
            "t01_no_clean_scene_commit": state.t01_no_clean_scene_commit,
            "t01_forbidden_shortcuts": state.t01_forbidden_shortcuts,
            "t01_restrictions": state.t01_restrictions,
            "t01_scope": state.t01_scope,
            "t01_scope_rt01_contour_only": state.t01_scope_rt01_contour_only,
            "t01_scope_t01_first_slice_only": state.t01_scope_t01_first_slice_only,
            "t01_scope_t02_implemented": state.t01_scope_t02_implemented,
            "t01_scope_t03_implemented": state.t01_scope_t03_implemented,
            "t01_scope_t04_implemented": state.t01_scope_t04_implemented,
            "t01_scope_o01_implemented": state.t01_scope_o01_implemented,
            "t01_scope_full_silent_thought_line_implemented": (
                state.t01_scope_full_silent_thought_line_implemented
            ),
            "t01_scope_repo_wide_adoption": state.t01_scope_repo_wide_adoption,
            "t01_scope_reason": state.t01_scope_reason,
            "t01_reason": state.t01_reason,
            "t01_require_preverbal_scene_consumer": (
                state.t01_require_preverbal_scene_consumer
            ),
            "t01_require_scene_comparison_consumer": (
                state.t01_require_scene_comparison_consumer
            ),
            "t02_require_constrained_scene_consumer": (
                state.t02_require_constrained_scene_consumer
            ),
            "t02_require_raw_vs_propagated_distinction": (
                state.t02_require_raw_vs_propagated_distinction
            ),
            "t02_raw_vs_propagated_distinct": state.t02_raw_vs_propagated_distinct,
            "t03_competition_id": state.t03_competition_id,
            "t03_convergence_status": state.t03_convergence_status,
            "t03_current_leader_hypothesis_id": state.t03_current_leader_hypothesis_id,
            "t03_provisional_frontrunner_hypothesis_id": (
                state.t03_provisional_frontrunner_hypothesis_id
            ),
            "t03_tied_competitor_count": state.t03_tied_competitor_count,
            "t03_blocked_hypothesis_count": state.t03_blocked_hypothesis_count,
            "t03_eliminated_hypothesis_count": state.t03_eliminated_hypothesis_count,
            "t03_reactivated_hypothesis_count": state.t03_reactivated_hypothesis_count,
            "t03_honest_nonconvergence": state.t03_honest_nonconvergence,
            "t03_bounded_plurality": state.t03_bounded_plurality,
            "t03_convergence_consumer_ready": state.t03_convergence_consumer_ready,
            "t03_frontier_consumer_ready": state.t03_frontier_consumer_ready,
            "t03_nonconvergence_preserved": state.t03_nonconvergence_preserved,
            "t03_forbidden_shortcuts": state.t03_forbidden_shortcuts,
            "t03_restrictions": state.t03_restrictions,
            "t03_publication_current_leader": state.t03_publication_current_leader,
            "t03_publication_competitive_neighborhood": (
                state.t03_publication_competitive_neighborhood
            ),
            "t03_publication_unresolved_conflicts": (
                state.t03_publication_unresolved_conflicts
            ),
            "t03_publication_open_slots": state.t03_publication_open_slots,
            "t03_publication_stability_status": state.t03_publication_stability_status,
            "t03_scope": state.t03_scope,
            "t03_scope_rt01_contour_only": state.t03_scope_rt01_contour_only,
            "t03_scope_t03_first_slice_only": state.t03_scope_t03_first_slice_only,
            "t03_scope_t04_implemented": state.t03_scope_t04_implemented,
            "t03_scope_o01_implemented": state.t03_scope_o01_implemented,
            "t03_scope_o02_implemented": state.t03_scope_o02_implemented,
            "t03_scope_o03_implemented": state.t03_scope_o03_implemented,
            "t03_scope_full_silent_thought_line_implemented": (
                state.t03_scope_full_silent_thought_line_implemented
            ),
            "t03_scope_repo_wide_adoption": state.t03_scope_repo_wide_adoption,
            "t03_scope_reason": state.t03_scope_reason,
            "t03_reason": state.t03_reason,
            "t03_require_convergence_consumer": state.t03_require_convergence_consumer,
            "t03_require_frontier_consumer": state.t03_require_frontier_consumer,
            "t03_require_nonconvergence_preservation": (
                state.t03_require_nonconvergence_preservation
            ),
            "execution_stance": state.execution_stance.value,
            "execution_checkpoints": tuple(
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "source_contract": checkpoint.source_contract,
                    "status": checkpoint.status.value,
                    "required_action": checkpoint.required_action,
                    "applied_action": checkpoint.applied_action,
                    "reason": checkpoint.reason,
                }
                for checkpoint in state.execution_checkpoints
            ),
            "final_execution_outcome": state.final_execution_outcome.value,
            "repair_needed": state.repair_needed,
            "revalidation_needed": state.revalidation_needed,
            "halt_reason": state.halt_reason,
            "downstream_step_results": tuple(
                {
                    "phase_id": step.phase_id,
                    "status": step.status.value,
                    "gate_accepted": step.gate_accepted,
                    "usability_class": step.usability_class,
                    "execution_mode": step.execution_mode,
                    "restrictions": step.restrictions,
                    "reason": step.reason,
                }
                for step in state.downstream_step_results
            ),
            "source_stream_id": state.source_stream_id,
            "source_stream_sequence_index": state.source_stream_sequence_index,
            "source_c01_state_ref": state.source_c01_state_ref,
            "source_c02_state_ref": state.source_c02_state_ref,
            "source_c03_state_ref": state.source_c03_state_ref,
            "source_c04_state_ref": state.source_c04_state_ref,
            "source_c05_state_ref": state.source_c05_state_ref,
            "source_lineage": state.source_lineage,
            "last_update_provenance": state.last_update_provenance,
        },
        "world_adapter_result": {
            "world_link_status": result.world_adapter_result.state.world_link_status.value,
            "effect_status": result.world_adapter_result.state.effect_status.value,
            "adapter_presence": result.world_adapter_result.state.adapter_presence,
            "adapter_available": result.world_adapter_result.state.adapter_available,
            "adapter_degraded": result.world_adapter_result.state.adapter_degraded,
            "world_grounding_confidence": result.world_adapter_result.state.world_grounding_confidence,
            "world_grounded_transition_allowed": (
                result.world_adapter_result.gate.world_grounded_transition_allowed
            ),
            "externally_effected_change_claim_allowed": (
                result.world_adapter_result.gate.externally_effected_change_claim_allowed
            ),
            "world_action_success_claim_allowed": (
                result.world_adapter_result.gate.world_action_success_claim_allowed
            ),
            "effect_feedback_correlated": result.world_adapter_result.gate.effect_feedback_correlated,
            "restrictions": result.world_adapter_result.gate.restrictions,
            "reason": result.world_adapter_result.gate.reason,
        },
        "world_entry_result": {
            "episode_id": result.world_entry_result.episode.world_episode_id,
            "world_presence_mode": result.world_entry_result.episode.world_presence_mode.value,
            "observation_basis_present": result.world_entry_result.episode.observation_basis_present,
            "action_trace_present": result.world_entry_result.episode.action_trace_present,
            "effect_basis_present": result.world_entry_result.episode.effect_basis_present,
            "effect_feedback_correlated": result.world_entry_result.episode.effect_feedback_correlated,
            "forbidden_claim_classes": result.world_entry_result.forbidden_claim_classes,
            "world_grounded_transition_admissible": (
                result.world_entry_result.world_grounded_transition_admissible
            ),
            "world_effect_success_admissible": (
                result.world_entry_result.world_effect_success_admissible
            ),
            "w01_admission_ready": result.world_entry_result.w01_admission.admission_ready,
            "w01_admission_restrictions": result.world_entry_result.w01_admission.restrictions,
            "scope_marker": {
                "scope": result.world_entry_result.scope_marker.scope,
                "admission_layer_only": result.world_entry_result.scope_marker.admission_layer_only,
                "w01_implemented": result.world_entry_result.scope_marker.w01_implemented,
                "w_line_implemented": result.world_entry_result.scope_marker.w_line_implemented,
                "repo_wide_adoption": result.world_entry_result.scope_marker.repo_wide_adoption,
                "reason": result.world_entry_result.scope_marker.reason,
            },
            "reason": result.world_entry_result.reason,
        },
        "self_contour_result": {
            "boundary_state_id": result.self_contour_result.state.boundary_state_id,
            "self_attribution_basis_present": (
                result.self_contour_result.state.self_attribution_basis_present
            ),
            "world_attribution_basis_present": (
                result.self_contour_result.state.world_attribution_basis_present
            ),
            "controllability_estimate": result.self_contour_result.state.controllability_estimate,
            "ownership_estimate": result.self_contour_result.state.ownership_estimate,
            "attribution_confidence": result.self_contour_result.state.attribution_confidence,
            "source_status": (
                result.self_contour_result.state.internal_vs_external_source_status.value
            ),
            "boundary_breach_risk": result.self_contour_result.state.boundary_breach_risk.value,
            "attribution_class": result.self_contour_result.state.attribution_class.value,
            "no_safe_self_claim": result.self_contour_result.gate.no_safe_self_claim,
            "no_safe_world_claim": result.self_contour_result.gate.no_safe_world_claim,
            "forbidden_shortcuts": result.self_contour_result.gate.forbidden_shortcuts,
            "restrictions": result.self_contour_result.gate.restrictions,
            "s01_admission_ready": result.self_contour_result.admission.admission_ready_for_s01,
            "self_attribution_basis_sufficient": (
                result.self_contour_result.admission.self_attribution_basis_sufficient
            ),
            "controllability_basis_sufficient": (
                result.self_contour_result.admission.controllability_basis_sufficient
            ),
            "ownership_basis_sufficient": (
                result.self_contour_result.admission.ownership_basis_sufficient
            ),
            "attribution_underconstrained": (
                result.self_contour_result.admission.attribution_underconstrained
            ),
            "mixed_boundary_instability": (
                result.self_contour_result.admission.mixed_boundary_instability
            ),
            "no_safe_self_basis": result.self_contour_result.admission.no_safe_self_basis,
            "no_safe_world_basis": result.self_contour_result.admission.no_safe_world_basis,
            "readiness_blockers": result.self_contour_result.admission.readiness_blockers,
            "scope_marker": {
                "scope": result.self_contour_result.scope_marker.scope,
                "rt01_contour_only": result.self_contour_result.scope_marker.rt01_contour_only,
                "s_minimal_only": result.self_contour_result.scope_marker.s_minimal_only,
                "s01_implemented": result.self_contour_result.scope_marker.s01_implemented,
                "s_line_implemented": result.self_contour_result.scope_marker.s_line_implemented,
                "minimal_contour_only": result.self_contour_result.scope_marker.minimal_contour_only,
                "s01_s05_implemented": result.self_contour_result.scope_marker.s01_s05_implemented,
                "full_self_model_implemented": (
                    result.self_contour_result.scope_marker.full_self_model_implemented
                ),
                "repo_wide_adoption": result.self_contour_result.scope_marker.repo_wide_adoption,
                "reason": result.self_contour_result.scope_marker.reason,
            },
            "reason": result.self_contour_result.reason,
        },
        "s04_interoceptive_self_binding_result": {
            "binding_id": result.s04_result.state.binding_id,
            "tick_index": result.s04_result.state.tick_index,
            "strong_core_channels": result.s04_result.state.core_bound_channels,
            "weak_or_peripheral_channels": (
                result.s04_result.state.peripheral_or_weakly_bound_channels
            ),
            "contested_channels": result.s04_result.state.contested_channels,
            "recently_unbound_channels": result.s04_result.state.recently_unbound_channels,
            "no_stable_self_core_claim": result.s04_result.state.no_stable_self_core_claim,
            "strongest_binding_strength": result.s04_result.state.strongest_binding_strength,
            "contamination_detected": result.s04_result.state.contamination_detected,
            "rebinding_event": result.s04_result.state.rebinding_event,
            "stale_binding_drop_count": result.s04_result.state.stale_binding_drop_count,
            "candidate_channels": result.s04_result.state.candidate_channels,
            "excluded_channels": result.s04_result.state.excluded_channels,
            "gate": {
                "core_consumer_ready": result.s04_result.gate.core_consumer_ready,
                "contested_consumer_ready": result.s04_result.gate.contested_consumer_ready,
                "no_stable_core_consumer_ready": (
                    result.s04_result.gate.no_stable_core_consumer_ready
                ),
                "restrictions": result.s04_result.gate.restrictions,
                "reason": result.s04_result.gate.reason,
            },
            "scope_marker": {
                "scope": result.s04_result.scope_marker.scope,
                "rt01_contour_only": result.s04_result.scope_marker.rt01_contour_only,
                "s04_first_slice_only": result.s04_result.scope_marker.s04_first_slice_only,
                "s05_implemented": result.s04_result.scope_marker.s05_implemented,
                "full_self_model_implemented": (
                    result.s04_result.scope_marker.full_self_model_implemented
                ),
                "repo_wide_adoption": result.s04_result.scope_marker.repo_wide_adoption,
                "reason": result.s04_result.scope_marker.reason,
            },
            "reason": result.s04_result.reason,
        },
        "a_line_result": {
            "capability_id": result.a_line_result.state.capability_id,
            "affordance_id": result.a_line_result.state.affordance_id,
            "capability_class": result.a_line_result.state.capability_class.value,
            "capability_status": result.a_line_result.state.capability_status.value,
            "availability_basis_present": result.a_line_result.state.availability_basis_present,
            "world_dependency_present": result.a_line_result.state.world_dependency_present,
            "self_dependency_present": result.a_line_result.state.self_dependency_present,
            "controllability_dependency_present": (
                result.a_line_result.state.controllability_dependency_present
            ),
            "legitimacy_dependency_present": (
                result.a_line_result.state.legitimacy_dependency_present
            ),
            "confidence": result.a_line_result.state.confidence,
            "degraded": result.a_line_result.state.degraded,
            "underconstrained": result.a_line_result.state.underconstrained,
            "available_capability_claim_allowed": (
                result.a_line_result.gate.available_capability_claim_allowed
            ),
            "world_conditioned_capability_claim_allowed": (
                result.a_line_result.gate.world_conditioned_capability_claim_allowed
            ),
            "self_conditioned_capability_claim_allowed": (
                result.a_line_result.gate.self_conditioned_capability_claim_allowed
            ),
            "policy_conditioned_capability_present": (
                result.a_line_result.gate.policy_conditioned_capability_present
            ),
            "no_safe_capability_claim": result.a_line_result.gate.no_safe_capability_claim,
            "forbidden_shortcuts": result.a_line_result.gate.forbidden_shortcuts,
            "restrictions": result.a_line_result.gate.restrictions,
            "a04_readiness": {
                "admission_ready_for_a04": (
                    result.a_line_result.a04_readiness.admission_ready_for_a04
                ),
                "blockers": result.a_line_result.a04_readiness.blockers,
                "structurally_present_but_not_ready": (
                    result.a_line_result.a04_readiness.structurally_present_but_not_ready
                ),
                "capability_basis_missing": (
                    result.a_line_result.a04_readiness.capability_basis_missing
                ),
                "world_dependency_unmet": (
                    result.a_line_result.a04_readiness.world_dependency_unmet
                ),
                "self_dependency_unmet": (
                    result.a_line_result.a04_readiness.self_dependency_unmet
                ),
                "policy_legitimacy_unmet": (
                    result.a_line_result.a04_readiness.policy_legitimacy_unmet
                ),
                "underconstrained_capability_surface": (
                    result.a_line_result.a04_readiness.underconstrained_capability_surface
                ),
                "external_means_not_justified": (
                    result.a_line_result.a04_readiness.external_means_not_justified
                ),
                "a04_implemented": result.a_line_result.a04_readiness.a04_implemented,
                "a05_touched": result.a_line_result.a04_readiness.a05_touched,
                "restrictions": result.a_line_result.a04_readiness.restrictions,
                "reason": result.a_line_result.a04_readiness.reason,
            },
            "scope_marker": {
                "scope": result.a_line_result.scope_marker.scope,
                "rt01_contour_only": result.a_line_result.scope_marker.rt01_contour_only,
                "a_line_normalization_only": (
                    result.a_line_result.scope_marker.a_line_normalization_only
                ),
                "readiness_gate_only": result.a_line_result.scope_marker.readiness_gate_only,
                "a04_implemented": result.a_line_result.scope_marker.a04_implemented,
                "a05_touched": result.a_line_result.scope_marker.a05_touched,
                "full_agency_stack_implemented": (
                    result.a_line_result.scope_marker.full_agency_stack_implemented
                ),
                "repo_wide_adoption": result.a_line_result.scope_marker.repo_wide_adoption,
                "reason": result.a_line_result.scope_marker.reason,
            },
            "reason": result.a_line_result.reason,
        },
        "m_minimal_result": {
            "memory_item_id": result.m_minimal_result.state.memory_item_id,
            "memory_packet_id": result.m_minimal_result.state.memory_packet_id,
            "lifecycle_status": result.m_minimal_result.state.lifecycle_status.value,
            "retention_class": result.m_minimal_result.state.retention_class.value,
            "bounded_persistence_allowed": (
                result.m_minimal_result.state.bounded_persistence_allowed
            ),
            "temporary_carry_allowed": result.m_minimal_result.state.temporary_carry_allowed,
            "review_required": result.m_minimal_result.state.review_required,
            "reactivation_eligible": result.m_minimal_result.state.reactivation_eligible,
            "decay_eligible": result.m_minimal_result.state.decay_eligible,
            "pruning_eligible": result.m_minimal_result.state.pruning_eligible,
            "stale_risk": result.m_minimal_result.state.stale_risk.value,
            "conflict_risk": result.m_minimal_result.state.conflict_risk.value,
            "confidence": result.m_minimal_result.state.confidence,
            "reliability": result.m_minimal_result.state.reliability,
            "degraded": result.m_minimal_result.state.degraded,
            "underconstrained": result.m_minimal_result.state.underconstrained,
            "safe_memory_claim_allowed": (
                result.m_minimal_result.gate.safe_memory_claim_allowed
            ),
            "bounded_retained_claim_allowed": (
                result.m_minimal_result.gate.bounded_retained_claim_allowed
            ),
            "no_safe_memory_claim": result.m_minimal_result.gate.no_safe_memory_claim,
            "forbidden_shortcuts": result.m_minimal_result.gate.forbidden_shortcuts,
            "restrictions": result.m_minimal_result.gate.restrictions,
            "admission": {
                "admission_ready_for_m01": (
                    result.m_minimal_result.admission.admission_ready_for_m01
                ),
                "blockers": result.m_minimal_result.admission.blockers,
                "structurally_present_but_not_ready": (
                    result.m_minimal_result.admission.structurally_present_but_not_ready
                ),
                "stale_risk_unacceptable": (
                    result.m_minimal_result.admission.stale_risk_unacceptable
                ),
                "conflict_risk_unacceptable": (
                    result.m_minimal_result.admission.conflict_risk_unacceptable
                ),
                "reactivation_requires_review": (
                    result.m_minimal_result.admission.reactivation_requires_review
                ),
                "temporary_carry_not_stable_enough": (
                    result.m_minimal_result.admission.temporary_carry_not_stable_enough
                ),
                "no_safe_memory_basis": (
                    result.m_minimal_result.admission.no_safe_memory_basis
                ),
                "provenance_insufficient": (
                    result.m_minimal_result.admission.provenance_insufficient
                ),
                "lifecycle_underconstrained": (
                    result.m_minimal_result.admission.lifecycle_underconstrained
                ),
                "m01_implemented": result.m_minimal_result.admission.m01_implemented,
                "m02_implemented": result.m_minimal_result.admission.m02_implemented,
                "m03_implemented": result.m_minimal_result.admission.m03_implemented,
                "restrictions": result.m_minimal_result.admission.restrictions,
                "reason": result.m_minimal_result.admission.reason,
            },
            "scope_marker": {
                "scope": result.m_minimal_result.scope_marker.scope,
                "rt01_contour_only": result.m_minimal_result.scope_marker.rt01_contour_only,
                "m_minimal_only": result.m_minimal_result.scope_marker.m_minimal_only,
                "readiness_gate_only": result.m_minimal_result.scope_marker.readiness_gate_only,
                "m01_implemented": result.m_minimal_result.scope_marker.m01_implemented,
                "m02_implemented": result.m_minimal_result.scope_marker.m02_implemented,
                "m03_implemented": result.m_minimal_result.scope_marker.m03_implemented,
                "full_memory_stack_implemented": (
                    result.m_minimal_result.scope_marker.full_memory_stack_implemented
                ),
                "repo_wide_adoption": result.m_minimal_result.scope_marker.repo_wide_adoption,
                "reason": result.m_minimal_result.scope_marker.reason,
            },
            "reason": result.m_minimal_result.reason,
        },
        "n_minimal_result": {
            "narrative_commitment_id": result.n_minimal_result.state.narrative_commitment_id,
            "commitment_status": result.n_minimal_result.state.commitment_status.value,
            "commitment_scope": result.n_minimal_result.state.commitment_scope,
            "narrative_basis_present": result.n_minimal_result.state.narrative_basis_present,
            "self_basis_present": result.n_minimal_result.state.self_basis_present,
            "world_basis_present": result.n_minimal_result.state.world_basis_present,
            "memory_basis_present": result.n_minimal_result.state.memory_basis_present,
            "capability_basis_present": result.n_minimal_result.state.capability_basis_present,
            "ambiguity_residue": result.n_minimal_result.state.ambiguity_residue,
            "contradiction_risk": result.n_minimal_result.state.contradiction_risk.value,
            "confidence": result.n_minimal_result.state.confidence,
            "degraded": result.n_minimal_result.state.degraded,
            "underconstrained": result.n_minimal_result.state.underconstrained,
            "safe_narrative_commitment_allowed": (
                result.n_minimal_result.gate.safe_narrative_commitment_allowed
            ),
            "bounded_commitment_allowed": result.n_minimal_result.gate.bounded_commitment_allowed,
            "no_safe_narrative_claim": result.n_minimal_result.gate.no_safe_narrative_claim,
            "forbidden_shortcuts": result.n_minimal_result.gate.forbidden_shortcuts,
            "restrictions": result.n_minimal_result.gate.restrictions,
            "admission": {
                "admission_ready_for_n01": (
                    result.n_minimal_result.admission.admission_ready_for_n01
                ),
                "blockers": result.n_minimal_result.admission.blockers,
                "n01_implemented": result.n_minimal_result.admission.n01_implemented,
                "n02_implemented": result.n_minimal_result.admission.n02_implemented,
                "n03_implemented": result.n_minimal_result.admission.n03_implemented,
                "n04_implemented": result.n_minimal_result.admission.n04_implemented,
                "restrictions": result.n_minimal_result.admission.restrictions,
                "reason": result.n_minimal_result.admission.reason,
            },
            "scope_marker": {
                "scope": result.n_minimal_result.scope_marker.scope,
                "rt01_contour_only": result.n_minimal_result.scope_marker.rt01_contour_only,
                "n_minimal_only": result.n_minimal_result.scope_marker.n_minimal_only,
                "readiness_gate_only": result.n_minimal_result.scope_marker.readiness_gate_only,
                "n01_implemented": result.n_minimal_result.scope_marker.n01_implemented,
                "n02_implemented": result.n_minimal_result.scope_marker.n02_implemented,
                "n03_implemented": result.n_minimal_result.scope_marker.n03_implemented,
                "n04_implemented": result.n_minimal_result.scope_marker.n04_implemented,
                "full_narrative_line_implemented": (
                    result.n_minimal_result.scope_marker.full_narrative_line_implemented
                ),
                "repo_wide_adoption": result.n_minimal_result.scope_marker.repo_wide_adoption,
                "reason": result.n_minimal_result.scope_marker.reason,
            },
            "reason": result.n_minimal_result.reason,
        },
        "t01_semantic_field_result": {
            "scene_id": result.t01_result.state.scene_id,
            "scene_status": result.t01_result.state.scene_status.value,
            "stability_state": result.t01_result.state.stability_state.value,
            "active_entities_count": len(result.t01_result.state.active_entities),
            "relation_edges_count": len(result.t01_result.state.relation_edges),
            "role_bindings_count": len(result.t01_result.state.role_bindings),
            "unresolved_slots_count": len(result.t01_result.state.unresolved_slots),
            "contested_relations_count": sum(
                1 for edge in result.t01_result.state.relation_edges if edge.contested
            ),
            "active_predicates": result.t01_result.state.active_predicates,
            "source_authority_tags": result.t01_result.state.source_authority_tags,
            "pre_verbal_consumer_ready": result.t01_result.gate.pre_verbal_consumer_ready,
            "no_clean_scene_commit": result.t01_result.gate.no_clean_scene_commit,
            "forbidden_shortcuts": result.t01_result.gate.forbidden_shortcuts,
            "restrictions": result.t01_result.gate.restrictions,
            "scope_marker": {
                "scope": result.t01_result.scope_marker.scope,
                "rt01_contour_only": result.t01_result.scope_marker.rt01_contour_only,
                "t01_first_slice_only": result.t01_result.scope_marker.t01_first_slice_only,
                "t02_implemented": result.t01_result.scope_marker.t02_implemented,
                "t03_implemented": result.t01_result.scope_marker.t03_implemented,
                "t04_implemented": result.t01_result.scope_marker.t04_implemented,
                "o01_implemented": result.t01_result.scope_marker.o01_implemented,
                "full_silent_thought_line_implemented": (
                    result.t01_result.scope_marker.full_silent_thought_line_implemented
                ),
                "repo_wide_adoption": result.t01_result.scope_marker.repo_wide_adoption,
                "reason": result.t01_result.scope_marker.reason,
            },
            "reason": result.t01_result.reason,
        },
        "t02_relation_binding_result": {
            "constrained_scene_id": result.t02_result.state.constrained_scene_id,
            "source_t01_scene_id": result.t02_result.state.source_t01_scene_id,
            "source_t01_scene_status": result.t02_result.state.source_t01_scene_status,
            "scene_status": result.t02_result.state.scene_status.value,
            "raw_scene_nodes_count": len(result.t02_result.state.raw_scene_nodes),
            "raw_relation_candidates_count": len(result.t02_result.state.raw_relation_candidates),
            "confirmed_bindings_count": sum(
                1
                for item in result.t02_result.state.relation_bindings
                if item.status.value == "confirmed"
            ),
            "provisional_bindings_count": sum(
                1
                for item in result.t02_result.state.relation_bindings
                if item.status.value == "provisional"
            ),
            "blocked_bindings_count": sum(
                1
                for item in result.t02_result.state.relation_bindings
                if item.status.value == "blocked"
            ),
            "conflicted_bindings_count": sum(
                1
                for item in result.t02_result.state.relation_bindings
                if item.status.value in {"conflicted", "incompatible"}
            ),
            "constraint_objects_count": len(result.t02_result.state.constraint_objects),
            "propagation_records_count": len(result.t02_result.state.propagation_records),
            "stopped_propagation_count": sum(
                1
                for item in result.t02_result.state.propagation_records
                if item.status.value == "stopped"
            ),
            "conflict_records_count": len(result.t02_result.state.conflict_records),
            "narrowed_role_candidates": result.t02_result.state.narrowed_role_candidates,
            "operations_applied": result.t02_result.state.operations_applied,
            "pre_verbal_constraint_consumer_ready": (
                result.t02_result.gate.pre_verbal_constraint_consumer_ready
            ),
            "no_clean_binding_commit": result.t02_result.gate.no_clean_binding_commit,
            "forbidden_shortcuts": result.t02_result.gate.forbidden_shortcuts,
            "restrictions": result.t02_result.gate.restrictions,
            "scope_marker": {
                "scope": result.t02_result.scope_marker.scope,
                "rt01_contour_only": result.t02_result.scope_marker.rt01_contour_only,
                "t02_first_slice_only": result.t02_result.scope_marker.t02_first_slice_only,
                "t03_implemented": result.t02_result.scope_marker.t03_implemented,
                "t04_implemented": result.t02_result.scope_marker.t04_implemented,
                "o01_implemented": result.t02_result.scope_marker.o01_implemented,
                "full_silent_thought_line_implemented": (
                    result.t02_result.scope_marker.full_silent_thought_line_implemented
                ),
                "repo_wide_adoption": result.t02_result.scope_marker.repo_wide_adoption,
                "reason": result.t02_result.scope_marker.reason,
            },
            "reason": result.t02_result.reason,
        },
        "t03_hypothesis_competition_result": {
            "competition_id": result.t03_result.state.competition_id,
            "source_t01_scene_id": result.t03_result.state.source_t01_scene_id,
            "source_t02_constrained_scene_id": result.t03_result.state.source_t02_constrained_scene_id,
            "convergence_status": result.t03_result.state.convergence_status.value,
            "current_leader_hypothesis_id": result.t03_result.state.current_leader_hypothesis_id,
            "provisional_frontrunner_hypothesis_id": (
                result.t03_result.state.provisional_frontrunner_hypothesis_id
            ),
            "tied_competitor_ids": result.t03_result.state.tied_competitor_ids,
            "blocked_hypothesis_ids": result.t03_result.state.blocked_hypothesis_ids,
            "eliminated_hypothesis_ids": result.t03_result.state.eliminated_hypothesis_ids,
            "reactivated_hypothesis_ids": result.t03_result.state.reactivated_hypothesis_ids,
            "honest_nonconvergence": result.t03_result.state.honest_nonconvergence,
            "bounded_plurality": result.t03_result.state.bounded_plurality,
            "publication_frontier": {
                "current_leader": result.t03_result.state.publication_frontier.current_leader,
                "competitive_neighborhood": (
                    result.t03_result.state.publication_frontier.competitive_neighborhood
                ),
                "unresolved_conflicts": (
                    result.t03_result.state.publication_frontier.unresolved_conflicts
                ),
                "open_slots": result.t03_result.state.publication_frontier.open_slots,
                "authority_profile": result.t03_result.state.publication_frontier.authority_profile,
                "stability_status": result.t03_result.state.publication_frontier.stability_status,
            },
            "convergence_consumer_ready": result.t03_result.gate.convergence_consumer_ready,
            "frontier_consumer_ready": result.t03_result.gate.frontier_consumer_ready,
            "nonconvergence_preserved": result.t03_result.gate.nonconvergence_preserved,
            "forbidden_shortcuts": result.t03_result.gate.forbidden_shortcuts,
            "restrictions": result.t03_result.gate.restrictions,
            "scope_marker": {
                "scope": result.t03_result.scope_marker.scope,
                "rt01_contour_only": result.t03_result.scope_marker.rt01_contour_only,
                "t03_first_slice_only": result.t03_result.scope_marker.t03_first_slice_only,
                "t04_implemented": result.t03_result.scope_marker.t04_implemented,
                "o01_implemented": result.t03_result.scope_marker.o01_implemented,
                "o02_implemented": result.t03_result.scope_marker.o02_implemented,
                "o03_implemented": result.t03_result.scope_marker.o03_implemented,
                "full_silent_thought_line_implemented": (
                    result.t03_result.scope_marker.full_silent_thought_line_implemented
                ),
                "repo_wide_adoption": result.t03_result.scope_marker.repo_wide_adoption,
                "reason": result.t03_result.scope_marker.reason,
            },
            "reason": result.t03_result.reason,
        },
        "downstream_gate": {
            "accepted": result.downstream_gate.accepted,
            "usability_class": result.downstream_gate.usability_class.value,
            "restrictions": tuple(code.value for code in result.downstream_gate.restrictions),
            "reason": result.downstream_gate.reason,
            "state_ref": result.downstream_gate.state_ref,
        },
        "telemetry": {
            "tick_id": result.telemetry.tick_id,
            "tick_index": result.telemetry.tick_index,
            "source_lineage": result.telemetry.source_lineage,
            "phase_order": result.telemetry.phase_order,
            "c04_execution_mode_claim": result.telemetry.c04_execution_mode_claim,
            "c05_execution_action_claim": result.telemetry.c05_execution_action_claim,
            "f01_authority_role": result.telemetry.f01_authority_role,
            "r04_authority_role": result.telemetry.r04_authority_role,
            "c04_authority_role": result.telemetry.c04_authority_role,
            "c05_authority_role": result.telemetry.c05_authority_role,
            "d01_authority_role": result.telemetry.d01_authority_role,
            "rt01_authority_role": result.telemetry.rt01_authority_role,
            "role_source_ref": result.telemetry.role_source_ref,
            "role_frontier_only": result.telemetry.role_frontier_only,
            "role_map_ready": result.telemetry.role_map_ready,
            "role_frontier_typed": result.telemetry.role_frontier_typed,
            "active_execution_mode": result.telemetry.active_execution_mode,
            "c04_selected_mode": result.telemetry.c04_selected_mode,
            "c05_validity_action": result.telemetry.c05_validity_action,
            "downstream_obedience_status": result.telemetry.downstream_obedience_status,
            "downstream_obedience_fallback": result.telemetry.downstream_obedience_fallback,
            "downstream_obedience_source_of_truth_surface": (
                result.telemetry.downstream_obedience_source_of_truth_surface
            ),
            "downstream_obedience_requires_restrictions_read": (
                result.telemetry.downstream_obedience_requires_restrictions_read
            ),
            "downstream_obedience_reason": result.telemetry.downstream_obedience_reason,
            "world_adapter_presence": result.telemetry.world_adapter_presence,
            "world_adapter_available": result.telemetry.world_adapter_available,
            "world_adapter_degraded": result.telemetry.world_adapter_degraded,
            "world_link_status": result.telemetry.world_link_status,
            "world_effect_status": result.telemetry.world_effect_status,
            "world_grounded_transition_allowed": (
                result.telemetry.world_grounded_transition_allowed
            ),
            "world_externally_effected_change_claim_allowed": (
                result.telemetry.world_externally_effected_change_claim_allowed
            ),
            "world_action_success_claim_allowed": (
                result.telemetry.world_action_success_claim_allowed
            ),
            "world_effect_feedback_correlated": result.telemetry.world_effect_feedback_correlated,
            "world_grounding_confidence": result.telemetry.world_grounding_confidence,
            "world_require_grounded_transition": result.telemetry.world_require_grounded_transition,
            "world_require_effect_feedback_for_success_claim": (
                result.telemetry.world_require_effect_feedback_for_success_claim
            ),
            "world_adapter_reason": result.telemetry.world_adapter_reason,
            "world_entry_episode_id": result.telemetry.world_entry_episode_id,
            "world_entry_presence_mode": result.telemetry.world_entry_presence_mode,
            "world_entry_episode_scope": result.telemetry.world_entry_episode_scope,
            "world_entry_observation_basis_present": (
                result.telemetry.world_entry_observation_basis_present
            ),
            "world_entry_action_trace_present": result.telemetry.world_entry_action_trace_present,
            "world_entry_effect_basis_present": result.telemetry.world_entry_effect_basis_present,
            "world_entry_effect_feedback_correlated": (
                result.telemetry.world_entry_effect_feedback_correlated
            ),
            "world_entry_confidence": result.telemetry.world_entry_confidence,
            "world_entry_reliability": result.telemetry.world_entry_reliability,
            "world_entry_degraded": result.telemetry.world_entry_degraded,
            "world_entry_incomplete": result.telemetry.world_entry_incomplete,
            "world_entry_forbidden_claim_classes": (
                result.telemetry.world_entry_forbidden_claim_classes
            ),
            "world_entry_world_grounded_transition_admissible": (
                result.telemetry.world_entry_world_grounded_transition_admissible
            ),
            "world_entry_world_effect_success_admissible": (
                result.telemetry.world_entry_world_effect_success_admissible
            ),
            "world_entry_w01_admission_ready": result.telemetry.world_entry_w01_admission_ready,
            "world_entry_w01_admission_restrictions": (
                result.telemetry.world_entry_w01_admission_restrictions
            ),
            "world_entry_scope": result.telemetry.world_entry_scope,
            "world_entry_scope_admission_layer_only": (
                result.telemetry.world_entry_scope_admission_layer_only
            ),
            "world_entry_scope_w01_implemented": result.telemetry.world_entry_scope_w01_implemented,
            "world_entry_scope_w_line_implemented": (
                result.telemetry.world_entry_scope_w_line_implemented
            ),
            "world_entry_scope_repo_wide_adoption": (
                result.telemetry.world_entry_scope_repo_wide_adoption
            ),
            "world_entry_scope_reason": result.telemetry.world_entry_scope_reason,
            "world_entry_reason": result.telemetry.world_entry_reason,
            "s_boundary_state_id": result.telemetry.s_boundary_state_id,
            "s_self_attribution_basis_present": (
                result.telemetry.s_self_attribution_basis_present
            ),
            "s_world_attribution_basis_present": (
                result.telemetry.s_world_attribution_basis_present
            ),
            "s_controllability_estimate": result.telemetry.s_controllability_estimate,
            "s_ownership_estimate": result.telemetry.s_ownership_estimate,
            "s_attribution_confidence": result.telemetry.s_attribution_confidence,
            "s_source_status": result.telemetry.s_source_status,
            "s_boundary_breach_risk": result.telemetry.s_boundary_breach_risk,
            "s_attribution_class": result.telemetry.s_attribution_class,
            "s_no_safe_self_claim": result.telemetry.s_no_safe_self_claim,
            "s_no_safe_world_claim": result.telemetry.s_no_safe_world_claim,
            "s_degraded": result.telemetry.s_degraded,
            "s_underconstrained": result.telemetry.s_underconstrained,
            "s_forbidden_shortcuts": result.telemetry.s_forbidden_shortcuts,
            "s_restrictions": result.telemetry.s_restrictions,
            "s_s01_admission_ready": result.telemetry.s_s01_admission_ready,
            "s_self_attribution_basis_sufficient": (
                result.telemetry.s_self_attribution_basis_sufficient
            ),
            "s_controllability_basis_sufficient": (
                result.telemetry.s_controllability_basis_sufficient
            ),
            "s_ownership_basis_sufficient": result.telemetry.s_ownership_basis_sufficient,
            "s_attribution_underconstrained": result.telemetry.s_attribution_underconstrained,
            "s_mixed_boundary_instability": result.telemetry.s_mixed_boundary_instability,
            "s_no_safe_self_basis": result.telemetry.s_no_safe_self_basis,
            "s_no_safe_world_basis": result.telemetry.s_no_safe_world_basis,
            "s_readiness_blockers": result.telemetry.s_readiness_blockers,
            "s_future_s01_s05_remain_open": result.telemetry.s_future_s01_s05_remain_open,
            "s_full_self_model_implemented": result.telemetry.s_full_self_model_implemented,
            "s_scope": result.telemetry.s_scope,
            "s_scope_rt01_contour_only": result.telemetry.s_scope_rt01_contour_only,
            "s_scope_s_minimal_only": result.telemetry.s_scope_s_minimal_only,
            "s_scope_s01_implemented": result.telemetry.s_scope_s01_implemented,
            "s_scope_s_line_implemented": result.telemetry.s_scope_s_line_implemented,
            "s_scope_minimal_contour_only": result.telemetry.s_scope_minimal_contour_only,
            "s_scope_s01_s05_implemented": result.telemetry.s_scope_s01_s05_implemented,
            "s_scope_full_self_model_implemented": (
                result.telemetry.s_scope_full_self_model_implemented
            ),
            "s_scope_repo_wide_adoption": result.telemetry.s_scope_repo_wide_adoption,
            "s_scope_reason": result.telemetry.s_scope_reason,
            "s_reason": result.telemetry.s_reason,
            "s_require_self_side_claim": result.telemetry.s_require_self_side_claim,
            "s_require_world_side_claim": result.telemetry.s_require_world_side_claim,
            "s_require_self_controlled_transition_claim": (
                result.telemetry.s_require_self_controlled_transition_claim
            ),
            "s_strict_mixed_attribution_guard": result.telemetry.s_strict_mixed_attribution_guard,
            "a_capability_id": result.telemetry.a_capability_id,
            "a_affordance_id": result.telemetry.a_affordance_id,
            "a_capability_class": result.telemetry.a_capability_class,
            "a_capability_status": result.telemetry.a_capability_status,
            "a_availability_basis_present": result.telemetry.a_availability_basis_present,
            "a_world_dependency_present": result.telemetry.a_world_dependency_present,
            "a_self_dependency_present": result.telemetry.a_self_dependency_present,
            "a_controllability_dependency_present": (
                result.telemetry.a_controllability_dependency_present
            ),
            "a_legitimacy_dependency_present": (
                result.telemetry.a_legitimacy_dependency_present
            ),
            "a_confidence": result.telemetry.a_confidence,
            "a_degraded": result.telemetry.a_degraded,
            "a_underconstrained": result.telemetry.a_underconstrained,
            "a_available_capability_claim_allowed": (
                result.telemetry.a_available_capability_claim_allowed
            ),
            "a_world_conditioned_capability_claim_allowed": (
                result.telemetry.a_world_conditioned_capability_claim_allowed
            ),
            "a_self_conditioned_capability_claim_allowed": (
                result.telemetry.a_self_conditioned_capability_claim_allowed
            ),
            "a_policy_conditioned_capability_present": (
                result.telemetry.a_policy_conditioned_capability_present
            ),
            "a_no_safe_capability_claim": result.telemetry.a_no_safe_capability_claim,
            "a_forbidden_shortcuts": result.telemetry.a_forbidden_shortcuts,
            "a_restrictions": result.telemetry.a_restrictions,
            "a_a04_admission_ready": result.telemetry.a_a04_admission_ready,
            "a_a04_blockers": result.telemetry.a_a04_blockers,
            "a_a04_structurally_present_but_not_ready": (
                result.telemetry.a_a04_structurally_present_but_not_ready
            ),
            "a_a04_capability_basis_missing": (
                result.telemetry.a_a04_capability_basis_missing
            ),
            "a_a04_world_dependency_unmet": (
                result.telemetry.a_a04_world_dependency_unmet
            ),
            "a_a04_self_dependency_unmet": (
                result.telemetry.a_a04_self_dependency_unmet
            ),
            "a_a04_policy_legitimacy_unmet": (
                result.telemetry.a_a04_policy_legitimacy_unmet
            ),
            "a_a04_underconstrained_capability_surface": (
                result.telemetry.a_a04_underconstrained_capability_surface
            ),
            "a_a04_external_means_not_justified": (
                result.telemetry.a_a04_external_means_not_justified
            ),
            "a_a04_implemented": result.telemetry.a_a04_implemented,
            "a_a05_touched": result.telemetry.a_a05_touched,
            "a_scope": result.telemetry.a_scope,
            "a_scope_rt01_contour_only": result.telemetry.a_scope_rt01_contour_only,
            "a_scope_a_line_normalization_only": (
                result.telemetry.a_scope_a_line_normalization_only
            ),
            "a_scope_readiness_gate_only": result.telemetry.a_scope_readiness_gate_only,
            "a_scope_a04_implemented": result.telemetry.a_scope_a04_implemented,
            "a_scope_a05_touched": result.telemetry.a_scope_a05_touched,
            "a_scope_full_agency_stack_implemented": (
                result.telemetry.a_scope_full_agency_stack_implemented
            ),
            "a_scope_repo_wide_adoption": result.telemetry.a_scope_repo_wide_adoption,
            "a_scope_reason": result.telemetry.a_scope_reason,
            "a_reason": result.telemetry.a_reason,
            "a_require_capability_claim": result.telemetry.a_require_capability_claim,
            "m_memory_item_id": result.telemetry.m_memory_item_id,
            "m_memory_packet_id": result.telemetry.m_memory_packet_id,
            "m_lifecycle_status": result.telemetry.m_lifecycle_status,
            "m_retention_class": result.telemetry.m_retention_class,
            "m_bounded_persistence_allowed": (
                result.telemetry.m_bounded_persistence_allowed
            ),
            "m_temporary_carry_allowed": result.telemetry.m_temporary_carry_allowed,
            "m_review_required": result.telemetry.m_review_required,
            "m_reactivation_eligible": result.telemetry.m_reactivation_eligible,
            "m_decay_eligible": result.telemetry.m_decay_eligible,
            "m_pruning_eligible": result.telemetry.m_pruning_eligible,
            "m_stale_risk": result.telemetry.m_stale_risk,
            "m_conflict_risk": result.telemetry.m_conflict_risk,
            "m_confidence": result.telemetry.m_confidence,
            "m_reliability": result.telemetry.m_reliability,
            "m_degraded": result.telemetry.m_degraded,
            "m_underconstrained": result.telemetry.m_underconstrained,
            "m_safe_memory_claim_allowed": result.telemetry.m_safe_memory_claim_allowed,
            "m_bounded_retained_claim_allowed": (
                result.telemetry.m_bounded_retained_claim_allowed
            ),
            "m_no_safe_memory_claim": result.telemetry.m_no_safe_memory_claim,
            "m_forbidden_shortcuts": result.telemetry.m_forbidden_shortcuts,
            "m_restrictions": result.telemetry.m_restrictions,
            "m_m01_admission_ready": result.telemetry.m_m01_admission_ready,
            "m_m01_blockers": result.telemetry.m_m01_blockers,
            "m_m01_structurally_present_but_not_ready": (
                result.telemetry.m_m01_structurally_present_but_not_ready
            ),
            "m_m01_stale_risk_unacceptable": result.telemetry.m_m01_stale_risk_unacceptable,
            "m_m01_conflict_risk_unacceptable": (
                result.telemetry.m_m01_conflict_risk_unacceptable
            ),
            "m_m01_reactivation_requires_review": (
                result.telemetry.m_m01_reactivation_requires_review
            ),
            "m_m01_temporary_carry_not_stable_enough": (
                result.telemetry.m_m01_temporary_carry_not_stable_enough
            ),
            "m_m01_no_safe_memory_basis": result.telemetry.m_m01_no_safe_memory_basis,
            "m_m01_provenance_insufficient": (
                result.telemetry.m_m01_provenance_insufficient
            ),
            "m_m01_lifecycle_underconstrained": (
                result.telemetry.m_m01_lifecycle_underconstrained
            ),
            "m_m01_implemented": result.telemetry.m_m01_implemented,
            "m_m02_implemented": result.telemetry.m_m02_implemented,
            "m_m03_implemented": result.telemetry.m_m03_implemented,
            "m_scope": result.telemetry.m_scope,
            "m_scope_rt01_contour_only": result.telemetry.m_scope_rt01_contour_only,
            "m_scope_m_minimal_only": result.telemetry.m_scope_m_minimal_only,
            "m_scope_readiness_gate_only": result.telemetry.m_scope_readiness_gate_only,
            "m_scope_m01_implemented": result.telemetry.m_scope_m01_implemented,
            "m_scope_m02_implemented": result.telemetry.m_scope_m02_implemented,
            "m_scope_m03_implemented": result.telemetry.m_scope_m03_implemented,
            "m_scope_full_memory_stack_implemented": (
                result.telemetry.m_scope_full_memory_stack_implemented
            ),
            "m_scope_repo_wide_adoption": result.telemetry.m_scope_repo_wide_adoption,
            "m_scope_reason": result.telemetry.m_scope_reason,
            "m_reason": result.telemetry.m_reason,
            "m_require_memory_safe_claim": result.telemetry.m_require_memory_safe_claim,
            "n_narrative_commitment_id": result.telemetry.n_narrative_commitment_id,
            "n_commitment_status": result.telemetry.n_commitment_status,
            "n_commitment_scope": result.telemetry.n_commitment_scope,
            "n_narrative_basis_present": result.telemetry.n_narrative_basis_present,
            "n_self_basis_present": result.telemetry.n_self_basis_present,
            "n_world_basis_present": result.telemetry.n_world_basis_present,
            "n_memory_basis_present": result.telemetry.n_memory_basis_present,
            "n_capability_basis_present": result.telemetry.n_capability_basis_present,
            "n_ambiguity_residue": result.telemetry.n_ambiguity_residue,
            "n_contradiction_risk": result.telemetry.n_contradiction_risk,
            "n_confidence": result.telemetry.n_confidence,
            "n_degraded": result.telemetry.n_degraded,
            "n_underconstrained": result.telemetry.n_underconstrained,
            "n_safe_narrative_commitment_allowed": (
                result.telemetry.n_safe_narrative_commitment_allowed
            ),
            "n_bounded_commitment_allowed": result.telemetry.n_bounded_commitment_allowed,
            "n_no_safe_narrative_claim": result.telemetry.n_no_safe_narrative_claim,
            "n_forbidden_shortcuts": result.telemetry.n_forbidden_shortcuts,
            "n_restrictions": result.telemetry.n_restrictions,
            "n_n01_admission_ready": result.telemetry.n_n01_admission_ready,
            "n_n01_blockers": result.telemetry.n_n01_blockers,
            "n_n01_implemented": result.telemetry.n_n01_implemented,
            "n_n02_implemented": result.telemetry.n_n02_implemented,
            "n_n03_implemented": result.telemetry.n_n03_implemented,
            "n_n04_implemented": result.telemetry.n_n04_implemented,
            "n_scope": result.telemetry.n_scope,
            "n_scope_rt01_contour_only": result.telemetry.n_scope_rt01_contour_only,
            "n_scope_n_minimal_only": result.telemetry.n_scope_n_minimal_only,
            "n_scope_readiness_gate_only": result.telemetry.n_scope_readiness_gate_only,
            "n_scope_n01_implemented": result.telemetry.n_scope_n01_implemented,
            "n_scope_n02_implemented": result.telemetry.n_scope_n02_implemented,
            "n_scope_n03_implemented": result.telemetry.n_scope_n03_implemented,
            "n_scope_n04_implemented": result.telemetry.n_scope_n04_implemented,
            "n_scope_full_narrative_line_implemented": (
                result.telemetry.n_scope_full_narrative_line_implemented
            ),
            "n_scope_repo_wide_adoption": result.telemetry.n_scope_repo_wide_adoption,
            "n_scope_reason": result.telemetry.n_scope_reason,
            "n_reason": result.telemetry.n_reason,
            "n_require_narrative_safe_claim": result.telemetry.n_require_narrative_safe_claim,
            "t01_scene_id": result.telemetry.t01_scene_id,
            "t01_scene_status": result.telemetry.t01_scene_status,
            "t01_stability_state": result.telemetry.t01_stability_state,
            "t01_active_entities_count": result.telemetry.t01_active_entities_count,
            "t01_relation_edges_count": result.telemetry.t01_relation_edges_count,
            "t01_role_bindings_count": result.telemetry.t01_role_bindings_count,
            "t01_unresolved_slots_count": result.telemetry.t01_unresolved_slots_count,
            "t01_contested_relations_count": result.telemetry.t01_contested_relations_count,
            "t01_preverbal_consumer_ready": result.telemetry.t01_preverbal_consumer_ready,
            "t01_scene_comparison_ready": result.telemetry.t01_scene_comparison_ready,
            "t01_no_clean_scene_commit": result.telemetry.t01_no_clean_scene_commit,
            "t01_forbidden_shortcuts": result.telemetry.t01_forbidden_shortcuts,
            "t01_restrictions": result.telemetry.t01_restrictions,
            "t01_scope": result.telemetry.t01_scope,
            "t01_scope_rt01_contour_only": result.telemetry.t01_scope_rt01_contour_only,
            "t01_scope_t01_first_slice_only": result.telemetry.t01_scope_t01_first_slice_only,
            "t01_scope_t02_implemented": result.telemetry.t01_scope_t02_implemented,
            "t01_scope_t03_implemented": result.telemetry.t01_scope_t03_implemented,
            "t01_scope_t04_implemented": result.telemetry.t01_scope_t04_implemented,
            "t01_scope_o01_implemented": result.telemetry.t01_scope_o01_implemented,
            "t01_scope_full_silent_thought_line_implemented": (
                result.telemetry.t01_scope_full_silent_thought_line_implemented
            ),
            "t01_scope_repo_wide_adoption": result.telemetry.t01_scope_repo_wide_adoption,
            "t01_scope_reason": result.telemetry.t01_scope_reason,
            "t01_reason": result.telemetry.t01_reason,
            "t01_require_preverbal_scene_consumer": (
                result.telemetry.t01_require_preverbal_scene_consumer
            ),
            "t01_require_scene_comparison_consumer": (
                result.telemetry.t01_require_scene_comparison_consumer
            ),
            "t02_require_constrained_scene_consumer": (
                result.telemetry.t02_require_constrained_scene_consumer
            ),
            "t02_require_raw_vs_propagated_distinction": (
                result.telemetry.t02_require_raw_vs_propagated_distinction
            ),
            "t02_raw_vs_propagated_distinct": (
                result.telemetry.t02_raw_vs_propagated_distinct
            ),
            "t03_competition_id": result.telemetry.t03_competition_id,
            "t03_convergence_status": result.telemetry.t03_convergence_status,
            "t03_current_leader_hypothesis_id": (
                result.telemetry.t03_current_leader_hypothesis_id
            ),
            "t03_provisional_frontrunner_hypothesis_id": (
                result.telemetry.t03_provisional_frontrunner_hypothesis_id
            ),
            "t03_tied_competitor_count": result.telemetry.t03_tied_competitor_count,
            "t03_blocked_hypothesis_count": result.telemetry.t03_blocked_hypothesis_count,
            "t03_eliminated_hypothesis_count": result.telemetry.t03_eliminated_hypothesis_count,
            "t03_reactivated_hypothesis_count": result.telemetry.t03_reactivated_hypothesis_count,
            "t03_honest_nonconvergence": result.telemetry.t03_honest_nonconvergence,
            "t03_bounded_plurality": result.telemetry.t03_bounded_plurality,
            "t03_convergence_consumer_ready": result.telemetry.t03_convergence_consumer_ready,
            "t03_frontier_consumer_ready": result.telemetry.t03_frontier_consumer_ready,
            "t03_nonconvergence_preserved": result.telemetry.t03_nonconvergence_preserved,
            "t03_forbidden_shortcuts": result.telemetry.t03_forbidden_shortcuts,
            "t03_restrictions": result.telemetry.t03_restrictions,
            "t03_publication_current_leader": result.telemetry.t03_publication_current_leader,
            "t03_publication_competitive_neighborhood": (
                result.telemetry.t03_publication_competitive_neighborhood
            ),
            "t03_publication_unresolved_conflicts": (
                result.telemetry.t03_publication_unresolved_conflicts
            ),
            "t03_publication_open_slots": result.telemetry.t03_publication_open_slots,
            "t03_publication_stability_status": result.telemetry.t03_publication_stability_status,
            "t03_scope": result.telemetry.t03_scope,
            "t03_scope_rt01_contour_only": result.telemetry.t03_scope_rt01_contour_only,
            "t03_scope_t03_first_slice_only": result.telemetry.t03_scope_t03_first_slice_only,
            "t03_scope_t04_implemented": result.telemetry.t03_scope_t04_implemented,
            "t03_scope_o01_implemented": result.telemetry.t03_scope_o01_implemented,
            "t03_scope_o02_implemented": result.telemetry.t03_scope_o02_implemented,
            "t03_scope_o03_implemented": result.telemetry.t03_scope_o03_implemented,
            "t03_scope_full_silent_thought_line_implemented": (
                result.telemetry.t03_scope_full_silent_thought_line_implemented
            ),
            "t03_scope_repo_wide_adoption": result.telemetry.t03_scope_repo_wide_adoption,
            "t03_scope_reason": result.telemetry.t03_scope_reason,
            "t03_reason": result.telemetry.t03_reason,
            "t03_require_convergence_consumer": (
                result.telemetry.t03_require_convergence_consumer
            ),
            "t03_require_frontier_consumer": result.telemetry.t03_require_frontier_consumer,
            "t03_require_nonconvergence_preservation": (
                result.telemetry.t03_require_nonconvergence_preservation
            ),
            "execution_stance": result.telemetry.execution_stance.value,
            "execution_checkpoints": tuple(
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "source_contract": checkpoint.source_contract,
                    "status": checkpoint.status.value,
                    "required_action": checkpoint.required_action,
                    "applied_action": checkpoint.applied_action,
                    "reason": checkpoint.reason,
                }
                for checkpoint in result.telemetry.execution_checkpoints
            ),
            "final_execution_outcome": result.telemetry.final_execution_outcome.value,
            "repair_needed": result.telemetry.repair_needed,
            "revalidation_needed": result.telemetry.revalidation_needed,
            "halt_reason": result.telemetry.halt_reason,
            "step_results": tuple(_step_to_payload(step) for step in result.telemetry.step_results),
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": tuple(
                    code.value for code in result.telemetry.downstream_gate.restrictions
                ),
                "reason": result.telemetry.downstream_gate.reason,
                "state_ref": result.telemetry.downstream_gate.state_ref,
            },
            "causal_basis": result.telemetry.causal_basis,
            "emitted_at": result.telemetry.emitted_at,
        },
    }


def _step_to_payload(step: SubjectTickStepResult) -> dict[str, object]:
    return {
        "phase_id": step.phase_id,
        "status": step.status.value,
        "gate_accepted": step.gate_accepted,
        "usability_class": step.usability_class,
        "execution_mode": step.execution_mode,
        "restrictions": step.restrictions,
        "reason": step.reason,
    }
