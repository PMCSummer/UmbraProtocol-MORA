from __future__ import annotations

from dataclasses import dataclass

from substrate.runtime_topology.models import RuntimeDispatchResult


@dataclass(frozen=True, slots=True)
class RuntimeDispatchContractView:
    accepted: bool
    lawful_production_route: bool
    route_binding_consequence: str
    route_class: str
    production_consumer_ready: bool
    contour_id: str
    execution_spine_phase: str
    source_of_truth_surfaces: tuple[str, ...]
    mandatory_checkpoints: tuple[str, ...]
    restrictions: tuple[str, ...]
    final_execution_outcome: str | None
    downstream_obedience_status: str | None
    world_link_status: str | None
    world_grounded_transition_allowed: bool | None
    world_effect_feedback_correlated: bool | None
    world_entry_episode_id: str | None
    world_entry_w01_admission_ready: bool | None
    world_entry_forbidden_claim_classes: tuple[str, ...] | None
    world_entry_scope: str | None
    world_entry_scope_admission_layer_only: bool | None
    world_entry_scope_w01_implemented: bool | None
    world_entry_scope_w_line_implemented: bool | None
    world_entry_scope_repo_wide_adoption: bool | None
    s_boundary_state_id: str | None
    s_attribution_class: str | None
    s_underconstrained: bool | None
    s_no_safe_self_claim: bool | None
    s_no_safe_world_claim: bool | None
    s_forbidden_shortcuts: tuple[str, ...] | None
    s_s01_admission_ready: bool | None
    s_readiness_blockers: tuple[str, ...] | None
    s_scope: str | None
    s_scope_rt01_contour_only: bool | None
    s_scope_s_minimal_only: bool | None
    s_scope_s01_implemented: bool | None
    s_scope_s_line_implemented: bool | None
    s_scope_minimal_contour_only: bool | None
    s_scope_s01_s05_implemented: bool | None
    s_scope_full_self_model_implemented: bool | None
    s_scope_repo_wide_adoption: bool | None
    a_capability_id: str | None
    a_capability_status: str | None
    a_underconstrained: bool | None
    a_no_safe_capability_claim: bool | None
    a_policy_conditioned_capability_present: bool | None
    a_forbidden_shortcuts: tuple[str, ...] | None
    a_a04_admission_ready: bool | None
    a_a04_blockers: tuple[str, ...] | None
    a_a04_structurally_present_but_not_ready: bool | None
    a_a04_capability_basis_missing: bool | None
    a_a04_world_dependency_unmet: bool | None
    a_a04_self_dependency_unmet: bool | None
    a_a04_policy_legitimacy_unmet: bool | None
    a_a04_underconstrained_capability_surface: bool | None
    a_a04_external_means_not_justified: bool | None
    a_scope: str | None
    a_scope_rt01_contour_only: bool | None
    a_scope_a_line_normalization_only: bool | None
    a_scope_readiness_gate_only: bool | None
    a_scope_a04_implemented: bool | None
    a_scope_a05_touched: bool | None
    a_scope_full_agency_stack_implemented: bool | None
    a_scope_repo_wide_adoption: bool | None
    m_memory_item_id: str | None
    m_lifecycle_status: str | None
    m_retention_class: str | None
    m_review_required: bool | None
    m_stale_risk: str | None
    m_conflict_risk: str | None
    m_no_safe_memory_claim: bool | None
    m_forbidden_shortcuts: tuple[str, ...] | None
    m_m01_admission_ready: bool | None
    m_m01_blockers: tuple[str, ...] | None
    m_m01_structurally_present_but_not_ready: bool | None
    m_m01_stale_risk_unacceptable: bool | None
    m_m01_conflict_risk_unacceptable: bool | None
    m_m01_reactivation_requires_review: bool | None
    m_m01_temporary_carry_not_stable_enough: bool | None
    m_m01_no_safe_memory_basis: bool | None
    m_m01_provenance_insufficient: bool | None
    m_m01_lifecycle_underconstrained: bool | None
    m_scope: str | None
    m_scope_rt01_contour_only: bool | None
    m_scope_m_minimal_only: bool | None
    m_scope_readiness_gate_only: bool | None
    m_scope_m01_implemented: bool | None
    m_scope_m02_implemented: bool | None
    m_scope_m03_implemented: bool | None
    m_scope_full_memory_stack_implemented: bool | None
    m_scope_repo_wide_adoption: bool | None
    n_narrative_commitment_id: str | None
    n_commitment_status: str | None
    n_safe_narrative_commitment_allowed: bool | None
    n_bounded_commitment_allowed: bool | None
    n_ambiguity_residue: bool | None
    n_contradiction_risk: str | None
    n_no_safe_narrative_claim: bool | None
    n_forbidden_shortcuts: tuple[str, ...] | None
    n_n01_admission_ready: bool | None
    n_n01_blockers: tuple[str, ...] | None
    n_scope: str | None
    n_scope_rt01_contour_only: bool | None
    n_scope_n_minimal_only: bool | None
    n_scope_readiness_gate_only: bool | None
    n_scope_n01_implemented: bool | None
    n_scope_n02_implemented: bool | None
    n_scope_n03_implemented: bool | None
    n_scope_n04_implemented: bool | None
    n_scope_full_narrative_line_implemented: bool | None
    n_scope_repo_wide_adoption: bool | None
    t01_scene_id: str | None
    t01_scene_status: str | None
    t01_stability_state: str | None
    t01_preverbal_consumer_ready: bool | None
    t01_scene_comparison_ready: bool | None
    t01_no_clean_scene_commit: bool | None
    t01_unresolved_slots_count: int | None
    t01_forbidden_shortcuts: tuple[str, ...] | None
    t01_require_scene_comparison_consumer: bool | None
    t01_scope: str | None
    t01_scope_rt01_contour_only: bool | None
    t01_scope_t01_first_slice_only: bool | None
    t01_scope_t02_implemented: bool | None
    t01_scope_t03_implemented: bool | None
    t01_scope_t04_implemented: bool | None
    t01_scope_o01_implemented: bool | None
    t01_scope_full_silent_thought_line_implemented: bool | None
    t01_scope_repo_wide_adoption: bool | None
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
    reason: str


def derive_runtime_dispatch_contract_view(
    result: RuntimeDispatchResult,
) -> RuntimeDispatchContractView:
    if not isinstance(result, RuntimeDispatchResult):
        raise TypeError("derive_runtime_dispatch_contract_view requires RuntimeDispatchResult")
    state = None if result.subject_tick_result is None else result.subject_tick_result.state
    t02_result = None if result.subject_tick_result is None else result.subject_tick_result.t02_result
    t03_result = None if result.subject_tick_result is None else result.subject_tick_result.t03_result
    t04_result = None if result.subject_tick_result is None else result.subject_tick_result.t04_result
    return RuntimeDispatchContractView(
        accepted=result.decision.accepted,
        lawful_production_route=result.decision.lawful_production_route,
        route_binding_consequence=result.decision.route_binding_consequence.value,
        route_class=result.decision.route_class.value,
        production_consumer_ready=(
            result.decision.accepted and result.decision.lawful_production_route
        ),
        contour_id=result.bundle.contour_id,
        execution_spine_phase=result.bundle.execution_spine_phase,
        source_of_truth_surfaces=result.tick_graph.source_of_truth_surfaces,
        mandatory_checkpoints=result.tick_graph.mandatory_checkpoint_ids,
        restrictions=tuple(item.value for item in result.decision.restrictions),
        final_execution_outcome=(
            None if state is None else state.final_execution_outcome.value
        ),
        downstream_obedience_status=(
            None if state is None else state.downstream_obedience_status
        ),
        world_link_status=(None if state is None else state.world_link_status),
        world_grounded_transition_allowed=(
            None if state is None else state.world_grounded_transition_allowed
        ),
        world_effect_feedback_correlated=(
            None if state is None else state.world_effect_feedback_correlated
        ),
        world_entry_episode_id=(None if state is None else state.world_entry_episode_id),
        world_entry_w01_admission_ready=(
            None if state is None else state.world_entry_w01_admission_ready
        ),
        world_entry_forbidden_claim_classes=(
            None if state is None else state.world_entry_forbidden_claim_classes
        ),
        world_entry_scope=(None if state is None else state.world_entry_scope),
        world_entry_scope_admission_layer_only=(
            None if state is None else state.world_entry_scope_admission_layer_only
        ),
        world_entry_scope_w01_implemented=(
            None if state is None else state.world_entry_scope_w01_implemented
        ),
        world_entry_scope_w_line_implemented=(
            None if state is None else state.world_entry_scope_w_line_implemented
        ),
        world_entry_scope_repo_wide_adoption=(
            None if state is None else state.world_entry_scope_repo_wide_adoption
        ),
        s_boundary_state_id=(None if state is None else state.s_boundary_state_id),
        s_attribution_class=(None if state is None else state.s_attribution_class),
        s_underconstrained=(None if state is None else state.s_underconstrained),
        s_no_safe_self_claim=(None if state is None else state.s_no_safe_self_claim),
        s_no_safe_world_claim=(None if state is None else state.s_no_safe_world_claim),
        s_forbidden_shortcuts=(None if state is None else state.s_forbidden_shortcuts),
        s_s01_admission_ready=(None if state is None else state.s_s01_admission_ready),
        s_readiness_blockers=(None if state is None else state.s_readiness_blockers),
        s_scope=(None if state is None else state.s_scope),
        s_scope_rt01_contour_only=(
            None if state is None else state.s_scope_rt01_contour_only
        ),
        s_scope_s_minimal_only=(None if state is None else state.s_scope_s_minimal_only),
        s_scope_s01_implemented=(None if state is None else state.s_scope_s01_implemented),
        s_scope_s_line_implemented=(
            None if state is None else state.s_scope_s_line_implemented
        ),
        s_scope_minimal_contour_only=(
            None if state is None else state.s_scope_minimal_contour_only
        ),
        s_scope_s01_s05_implemented=(
            None if state is None else state.s_scope_s01_s05_implemented
        ),
        s_scope_full_self_model_implemented=(
            None if state is None else state.s_scope_full_self_model_implemented
        ),
        s_scope_repo_wide_adoption=(
            None if state is None else state.s_scope_repo_wide_adoption
        ),
        a_capability_id=(None if state is None else state.a_capability_id),
        a_capability_status=(None if state is None else state.a_capability_status),
        a_underconstrained=(None if state is None else state.a_underconstrained),
        a_no_safe_capability_claim=(
            None if state is None else state.a_no_safe_capability_claim
        ),
        a_policy_conditioned_capability_present=(
            None if state is None else state.a_policy_conditioned_capability_present
        ),
        a_forbidden_shortcuts=(None if state is None else state.a_forbidden_shortcuts),
        a_a04_admission_ready=(None if state is None else state.a_a04_admission_ready),
        a_a04_blockers=(None if state is None else state.a_a04_blockers),
        a_a04_structurally_present_but_not_ready=(
            None if state is None else state.a_a04_structurally_present_but_not_ready
        ),
        a_a04_capability_basis_missing=(
            None if state is None else state.a_a04_capability_basis_missing
        ),
        a_a04_world_dependency_unmet=(
            None if state is None else state.a_a04_world_dependency_unmet
        ),
        a_a04_self_dependency_unmet=(
            None if state is None else state.a_a04_self_dependency_unmet
        ),
        a_a04_policy_legitimacy_unmet=(
            None if state is None else state.a_a04_policy_legitimacy_unmet
        ),
        a_a04_underconstrained_capability_surface=(
            None if state is None else state.a_a04_underconstrained_capability_surface
        ),
        a_a04_external_means_not_justified=(
            None if state is None else state.a_a04_external_means_not_justified
        ),
        a_scope=(None if state is None else state.a_scope),
        a_scope_rt01_contour_only=(
            None if state is None else state.a_scope_rt01_contour_only
        ),
        a_scope_a_line_normalization_only=(
            None if state is None else state.a_scope_a_line_normalization_only
        ),
        a_scope_readiness_gate_only=(
            None if state is None else state.a_scope_readiness_gate_only
        ),
        a_scope_a04_implemented=(
            None if state is None else state.a_scope_a04_implemented
        ),
        a_scope_a05_touched=(None if state is None else state.a_scope_a05_touched),
        a_scope_full_agency_stack_implemented=(
            None if state is None else state.a_scope_full_agency_stack_implemented
        ),
        a_scope_repo_wide_adoption=(
            None if state is None else state.a_scope_repo_wide_adoption
        ),
        m_memory_item_id=(None if state is None else state.m_memory_item_id),
        m_lifecycle_status=(None if state is None else state.m_lifecycle_status),
        m_retention_class=(None if state is None else state.m_retention_class),
        m_review_required=(None if state is None else state.m_review_required),
        m_stale_risk=(None if state is None else state.m_stale_risk),
        m_conflict_risk=(None if state is None else state.m_conflict_risk),
        m_no_safe_memory_claim=(None if state is None else state.m_no_safe_memory_claim),
        m_forbidden_shortcuts=(None if state is None else state.m_forbidden_shortcuts),
        m_m01_admission_ready=(None if state is None else state.m_m01_admission_ready),
        m_m01_blockers=(None if state is None else state.m_m01_blockers),
        m_m01_structurally_present_but_not_ready=(
            None if state is None else state.m_m01_structurally_present_but_not_ready
        ),
        m_m01_stale_risk_unacceptable=(
            None if state is None else state.m_m01_stale_risk_unacceptable
        ),
        m_m01_conflict_risk_unacceptable=(
            None if state is None else state.m_m01_conflict_risk_unacceptable
        ),
        m_m01_reactivation_requires_review=(
            None if state is None else state.m_m01_reactivation_requires_review
        ),
        m_m01_temporary_carry_not_stable_enough=(
            None if state is None else state.m_m01_temporary_carry_not_stable_enough
        ),
        m_m01_no_safe_memory_basis=(
            None if state is None else state.m_m01_no_safe_memory_basis
        ),
        m_m01_provenance_insufficient=(
            None if state is None else state.m_m01_provenance_insufficient
        ),
        m_m01_lifecycle_underconstrained=(
            None if state is None else state.m_m01_lifecycle_underconstrained
        ),
        m_scope=(None if state is None else state.m_scope),
        m_scope_rt01_contour_only=(
            None if state is None else state.m_scope_rt01_contour_only
        ),
        m_scope_m_minimal_only=(None if state is None else state.m_scope_m_minimal_only),
        m_scope_readiness_gate_only=(
            None if state is None else state.m_scope_readiness_gate_only
        ),
        m_scope_m01_implemented=(None if state is None else state.m_scope_m01_implemented),
        m_scope_m02_implemented=(None if state is None else state.m_scope_m02_implemented),
        m_scope_m03_implemented=(None if state is None else state.m_scope_m03_implemented),
        m_scope_full_memory_stack_implemented=(
            None if state is None else state.m_scope_full_memory_stack_implemented
        ),
        m_scope_repo_wide_adoption=(
            None if state is None else state.m_scope_repo_wide_adoption
        ),
        n_narrative_commitment_id=(
            None if state is None else state.n_narrative_commitment_id
        ),
        n_commitment_status=(None if state is None else state.n_commitment_status),
        n_safe_narrative_commitment_allowed=(
            None if state is None else state.n_safe_narrative_commitment_allowed
        ),
        n_bounded_commitment_allowed=(
            None if state is None else state.n_bounded_commitment_allowed
        ),
        n_ambiguity_residue=(None if state is None else state.n_ambiguity_residue),
        n_contradiction_risk=(None if state is None else state.n_contradiction_risk),
        n_no_safe_narrative_claim=(
            None if state is None else state.n_no_safe_narrative_claim
        ),
        n_forbidden_shortcuts=(None if state is None else state.n_forbidden_shortcuts),
        n_n01_admission_ready=(None if state is None else state.n_n01_admission_ready),
        n_n01_blockers=(None if state is None else state.n_n01_blockers),
        n_scope=(None if state is None else state.n_scope),
        n_scope_rt01_contour_only=(
            None if state is None else state.n_scope_rt01_contour_only
        ),
        n_scope_n_minimal_only=(None if state is None else state.n_scope_n_minimal_only),
        n_scope_readiness_gate_only=(
            None if state is None else state.n_scope_readiness_gate_only
        ),
        n_scope_n01_implemented=(None if state is None else state.n_scope_n01_implemented),
        n_scope_n02_implemented=(None if state is None else state.n_scope_n02_implemented),
        n_scope_n03_implemented=(None if state is None else state.n_scope_n03_implemented),
        n_scope_n04_implemented=(None if state is None else state.n_scope_n04_implemented),
        n_scope_full_narrative_line_implemented=(
            None if state is None else state.n_scope_full_narrative_line_implemented
        ),
        n_scope_repo_wide_adoption=(
            None if state is None else state.n_scope_repo_wide_adoption
        ),
        t01_scene_id=(None if state is None else state.t01_scene_id),
        t01_scene_status=(None if state is None else state.t01_scene_status),
        t01_stability_state=(None if state is None else state.t01_stability_state),
        t01_preverbal_consumer_ready=(
            None if state is None else state.t01_preverbal_consumer_ready
        ),
        t01_scene_comparison_ready=(
            None if state is None else state.t01_scene_comparison_ready
        ),
        t01_no_clean_scene_commit=(
            None if state is None else state.t01_no_clean_scene_commit
        ),
        t01_unresolved_slots_count=(
            None if state is None else state.t01_unresolved_slots_count
        ),
        t01_forbidden_shortcuts=(None if state is None else state.t01_forbidden_shortcuts),
        t01_require_scene_comparison_consumer=(
            None if state is None else state.t01_require_scene_comparison_consumer
        ),
        t01_scope=(None if state is None else state.t01_scope),
        t01_scope_rt01_contour_only=(
            None if state is None else state.t01_scope_rt01_contour_only
        ),
        t01_scope_t01_first_slice_only=(
            None if state is None else state.t01_scope_t01_first_slice_only
        ),
        t01_scope_t02_implemented=(
            None if state is None else state.t01_scope_t02_implemented
        ),
        t01_scope_t03_implemented=(
            None if state is None else state.t01_scope_t03_implemented
        ),
        t01_scope_t04_implemented=(
            None if state is None else state.t01_scope_t04_implemented
        ),
        t01_scope_o01_implemented=(
            None if state is None else state.t01_scope_o01_implemented
        ),
        t01_scope_full_silent_thought_line_implemented=(
            None
            if state is None
            else state.t01_scope_full_silent_thought_line_implemented
        ),
        t01_scope_repo_wide_adoption=(
            None if state is None else state.t01_scope_repo_wide_adoption
        ),
        t02_constrained_scene_id=(
            None if t02_result is None else t02_result.state.constrained_scene_id
        ),
        t02_scene_status=(
            None if t02_result is None else t02_result.state.scene_status.value
        ),
        t02_preverbal_constraint_consumer_ready=(
            None
            if t02_result is None
            else t02_result.gate.pre_verbal_constraint_consumer_ready
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
        t02_require_constrained_scene_consumer=(
            None if state is None else state.t02_require_constrained_scene_consumer
        ),
        t02_require_raw_vs_propagated_distinction=(
            None if state is None else state.t02_require_raw_vs_propagated_distinction
        ),
        t02_raw_vs_propagated_distinct=(
            None if state is None else state.t02_raw_vs_propagated_distinct
        ),
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
        t03_require_convergence_consumer=(
            None if state is None else state.t03_require_convergence_consumer
        ),
        t03_require_frontier_consumer=(
            None if state is None else state.t03_require_frontier_consumer
        ),
        t03_require_nonconvergence_preservation=(
            None if state is None else state.t03_require_nonconvergence_preservation
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
        t04_focus_mode=(None if t04_result is None else t04_result.state.focus_mode.value),
        t04_control_estimate=(
            None if t04_result is None else t04_result.state.control_estimate
        ),
        t04_stability_estimate=(
            None if t04_result is None else t04_result.state.stability_estimate
        ),
        t04_redirect_cost=(None if t04_result is None else t04_result.state.redirect_cost),
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
        t04_require_focus_ownership_consumer=None,
        t04_require_reportable_focus_consumer=None,
        t04_require_peripheral_preservation=None,
        reason=result.decision.reason,
    )


def require_lawful_production_dispatch(result: RuntimeDispatchResult) -> None:
    view = derive_runtime_dispatch_contract_view(result)
    if not view.accepted:
        raise PermissionError("runtime dispatch rejected; contour path is not lawful")
    if not view.lawful_production_route:
        raise PermissionError("runtime dispatch path is not lawful production contour")


def require_dispatch_bounded_n_scope(
    result: RuntimeDispatchResult | RuntimeDispatchContractView,
) -> RuntimeDispatchContractView:
    view = (
        result
        if isinstance(result, RuntimeDispatchContractView)
        else derive_runtime_dispatch_contract_view(result)
    )
    if not view.accepted:
        raise PermissionError("runtime dispatch rejected; contour path is not lawful")
    if view.n_scope is None:
        raise PermissionError("runtime dispatch does not expose n-minimal scope surface")
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
            "runtime dispatch n-surface violates bounded rt01 contour-only non-claim scope contract"
        )
    return view


def require_dispatch_strong_narrative_commitment(
    result: RuntimeDispatchResult | RuntimeDispatchContractView,
) -> RuntimeDispatchContractView:
    view = require_dispatch_bounded_n_scope(result)
    if not view.lawful_production_route:
        raise PermissionError(
            "strong narrative commitment consumer requires lawful production dispatch route"
        )
    if not view.n_safe_narrative_commitment_allowed or view.n_no_safe_narrative_claim:
        raise PermissionError(
            "strong narrative commitment requires safe bounded n-minimal basis in dispatched contour"
        )
    return view
