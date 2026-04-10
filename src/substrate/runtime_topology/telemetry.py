from __future__ import annotations

from substrate.runtime_topology.models import RuntimeDispatchResult


def runtime_dispatch_snapshot(result: RuntimeDispatchResult) -> dict[str, object]:
    if not isinstance(result, RuntimeDispatchResult):
        raise TypeError("runtime_dispatch_snapshot requires RuntimeDispatchResult")
    state = None if result.subject_tick_result is None else result.subject_tick_result.state
    t02_result = None if result.subject_tick_result is None else result.subject_tick_result.t02_result
    t03_result = None if result.subject_tick_result is None else result.subject_tick_result.t03_result
    t04_result = None if result.subject_tick_result is None else result.subject_tick_result.t04_result
    return {
        "decision": {
            "accepted": result.decision.accepted,
            "lawful_production_route": result.decision.lawful_production_route,
            "route_binding_consequence": result.decision.route_binding_consequence.value,
            "production_consumer_ready": (
                result.decision.accepted and result.decision.lawful_production_route
            ),
            "route_class": result.decision.route_class.value,
            "restrictions": tuple(item.value for item in result.decision.restrictions),
            "reason": result.decision.reason,
            "requires_dispatch_entry": result.decision.requires_dispatch_entry,
            "topology_ref": result.decision.topology_ref,
        },
        "bundle": {
            "bundle_id": result.bundle.bundle_id,
            "contour_id": result.bundle.contour_id,
            "runtime_entry": result.bundle.runtime_entry,
            "execution_spine_phase": result.bundle.execution_spine_phase,
            "downstream_obedience_phase": result.bundle.downstream_obedience_phase,
            "shared_domain_paths": result.bundle.shared_domain_paths,
            "enforcement_hooks": result.bundle.enforcement_hooks,
        },
        "tick_graph": {
            "graph_id": result.tick_graph.graph_id,
            "runtime_order": result.tick_graph.runtime_order,
            "mandatory_checkpoint_ids": result.tick_graph.mandatory_checkpoint_ids,
            "source_of_truth_surfaces": result.tick_graph.source_of_truth_surfaces,
        },
        "subject_tick_state": (
            None
            if state is None
            else {
                "tick_id": state.tick_id,
                "active_execution_mode": state.active_execution_mode,
                "execution_stance": state.execution_stance.value,
                "final_execution_outcome": state.final_execution_outcome.value,
                "downstream_obedience_status": state.downstream_obedience_status,
                "downstream_obedience_fallback": state.downstream_obedience_fallback,
                "world_link_status": state.world_link_status,
                "world_grounded_transition_allowed": state.world_grounded_transition_allowed,
                "world_effect_feedback_correlated": state.world_effect_feedback_correlated,
                "world_entry_episode_id": state.world_entry_episode_id,
                "world_entry_w01_admission_ready": state.world_entry_w01_admission_ready,
                "world_entry_forbidden_claim_classes": state.world_entry_forbidden_claim_classes,
                "world_entry_scope": state.world_entry_scope,
                "world_entry_scope_admission_layer_only": state.world_entry_scope_admission_layer_only,
                "world_entry_scope_w01_implemented": state.world_entry_scope_w01_implemented,
                "world_entry_scope_w_line_implemented": state.world_entry_scope_w_line_implemented,
                "world_entry_scope_repo_wide_adoption": state.world_entry_scope_repo_wide_adoption,
                "s_boundary_state_id": state.s_boundary_state_id,
                "s_attribution_class": state.s_attribution_class,
                "s_underconstrained": state.s_underconstrained,
                "s_no_safe_self_claim": state.s_no_safe_self_claim,
                "s_no_safe_world_claim": state.s_no_safe_world_claim,
                "s_forbidden_shortcuts": state.s_forbidden_shortcuts,
                "s_s01_admission_ready": state.s_s01_admission_ready,
                "s_readiness_blockers": state.s_readiness_blockers,
                "s_scope": state.s_scope,
                "s_scope_rt01_contour_only": state.s_scope_rt01_contour_only,
                "s_scope_s_minimal_only": state.s_scope_s_minimal_only,
                "s_scope_s01_implemented": state.s_scope_s01_implemented,
                "s_scope_s_line_implemented": state.s_scope_s_line_implemented,
                "s_scope_minimal_contour_only": state.s_scope_minimal_contour_only,
                "s_scope_s01_s05_implemented": state.s_scope_s01_s05_implemented,
                "s_scope_full_self_model_implemented": state.s_scope_full_self_model_implemented,
                "s_scope_repo_wide_adoption": state.s_scope_repo_wide_adoption,
                "a_capability_id": state.a_capability_id,
                "a_capability_status": state.a_capability_status,
                "a_underconstrained": state.a_underconstrained,
                "a_no_safe_capability_claim": state.a_no_safe_capability_claim,
                "a_policy_conditioned_capability_present": (
                    state.a_policy_conditioned_capability_present
                ),
                "a_forbidden_shortcuts": state.a_forbidden_shortcuts,
                "a_a04_admission_ready": state.a_a04_admission_ready,
                "a_a04_blockers": state.a_a04_blockers,
                "a_a04_structurally_present_but_not_ready": (
                    state.a_a04_structurally_present_but_not_ready
                ),
                "a_a04_capability_basis_missing": state.a_a04_capability_basis_missing,
                "a_a04_world_dependency_unmet": state.a_a04_world_dependency_unmet,
                "a_a04_self_dependency_unmet": state.a_a04_self_dependency_unmet,
                "a_a04_policy_legitimacy_unmet": (
                    state.a_a04_policy_legitimacy_unmet
                ),
                "a_a04_underconstrained_capability_surface": (
                    state.a_a04_underconstrained_capability_surface
                ),
                "a_a04_external_means_not_justified": (
                    state.a_a04_external_means_not_justified
                ),
                "a_scope": state.a_scope,
                "a_scope_rt01_contour_only": state.a_scope_rt01_contour_only,
                "a_scope_a_line_normalization_only": (
                    state.a_scope_a_line_normalization_only
                ),
                "a_scope_readiness_gate_only": state.a_scope_readiness_gate_only,
                "a_scope_a04_implemented": state.a_scope_a04_implemented,
                "a_scope_a05_touched": state.a_scope_a05_touched,
                "a_scope_full_agency_stack_implemented": (
                    state.a_scope_full_agency_stack_implemented
                ),
                "a_scope_repo_wide_adoption": state.a_scope_repo_wide_adoption,
                "m_memory_item_id": state.m_memory_item_id,
                "m_lifecycle_status": state.m_lifecycle_status,
                "m_retention_class": state.m_retention_class,
                "m_review_required": state.m_review_required,
                "m_stale_risk": state.m_stale_risk,
                "m_conflict_risk": state.m_conflict_risk,
                "m_no_safe_memory_claim": state.m_no_safe_memory_claim,
                "m_forbidden_shortcuts": state.m_forbidden_shortcuts,
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
                "n_narrative_commitment_id": state.n_narrative_commitment_id,
                "n_commitment_status": state.n_commitment_status,
                "n_safe_narrative_commitment_allowed": (
                    state.n_safe_narrative_commitment_allowed
                ),
                "n_bounded_commitment_allowed": state.n_bounded_commitment_allowed,
                "n_ambiguity_residue": state.n_ambiguity_residue,
                "n_contradiction_risk": state.n_contradiction_risk,
                "n_no_safe_narrative_claim": state.n_no_safe_narrative_claim,
                "n_forbidden_shortcuts": state.n_forbidden_shortcuts,
                "n_n01_admission_ready": state.n_n01_admission_ready,
                "n_n01_blockers": state.n_n01_blockers,
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
                "t01_scene_id": state.t01_scene_id,
                "t01_scene_status": state.t01_scene_status,
                "t01_stability_state": state.t01_stability_state,
                "t01_preverbal_consumer_ready": state.t01_preverbal_consumer_ready,
                "t01_scene_comparison_ready": state.t01_scene_comparison_ready,
                "t01_no_clean_scene_commit": state.t01_no_clean_scene_commit,
                "t01_unresolved_slots_count": state.t01_unresolved_slots_count,
                "t01_forbidden_shortcuts": state.t01_forbidden_shortcuts,
                "t01_require_scene_comparison_consumer": (
                    state.t01_require_scene_comparison_consumer
                ),
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
                "t02_constrained_scene_id": (
                    None if t02_result is None else t02_result.state.constrained_scene_id
                ),
                "t02_scene_status": (
                    None if t02_result is None else t02_result.state.scene_status.value
                ),
                "t02_preverbal_constraint_consumer_ready": (
                    None
                    if t02_result is None
                    else t02_result.gate.pre_verbal_constraint_consumer_ready
                ),
                "t02_no_clean_binding_commit": (
                    None if t02_result is None else t02_result.gate.no_clean_binding_commit
                ),
                "t02_confirmed_bindings_count": (
                    None
                    if t02_result is None
                    else sum(
                        1
                        for item in t02_result.state.relation_bindings
                        if item.status.value == "confirmed"
                    )
                ),
                "t02_provisional_bindings_count": (
                    None
                    if t02_result is None
                    else sum(
                        1
                        for item in t02_result.state.relation_bindings
                        if item.status.value == "provisional"
                    )
                ),
                "t02_blocked_bindings_count": (
                    None
                    if t02_result is None
                    else sum(
                        1
                        for item in t02_result.state.relation_bindings
                        if item.status.value == "blocked"
                    )
                ),
                "t02_conflicted_bindings_count": (
                    None
                    if t02_result is None
                    else sum(
                        1
                        for item in t02_result.state.relation_bindings
                        if item.status.value in {"conflicted", "incompatible"}
                    )
                ),
                "t02_propagated_consequences_count": (
                    None
                    if t02_result is None
                    else sum(
                        1
                        for item in t02_result.state.propagation_records
                        if item.effect_type.value != "no_effect" and item.status.value == "active"
                    )
                ),
                "t02_blocked_or_conflicted_consequences_count": (
                    None
                    if t02_result is None
                    else sum(
                        1
                        for item in t02_result.state.propagation_records
                        if item.status.value in {"blocked", "stopped"}
                    )
                ),
                "t02_forbidden_shortcuts": (
                    None if t02_result is None else t02_result.gate.forbidden_shortcuts
                ),
                "t02_scope": (
                    None if t02_result is None else t02_result.scope_marker.scope
                ),
                "t02_scope_rt01_contour_only": (
                    None if t02_result is None else t02_result.scope_marker.rt01_contour_only
                ),
                "t02_scope_t02_first_slice_only": (
                    None if t02_result is None else t02_result.scope_marker.t02_first_slice_only
                ),
                "t02_scope_t03_implemented": (
                    None if t02_result is None else t02_result.scope_marker.t03_implemented
                ),
                "t02_scope_t04_implemented": (
                    None if t02_result is None else t02_result.scope_marker.t04_implemented
                ),
                "t02_scope_o01_implemented": (
                    None if t02_result is None else t02_result.scope_marker.o01_implemented
                ),
                "t02_scope_full_silent_thought_line_implemented": (
                    None
                    if t02_result is None
                    else t02_result.scope_marker.full_silent_thought_line_implemented
                ),
                "t02_scope_repo_wide_adoption": (
                    None if t02_result is None else t02_result.scope_marker.repo_wide_adoption
                ),
                "t02_require_constrained_scene_consumer": (
                    state.t02_require_constrained_scene_consumer
                ),
                "t02_require_raw_vs_propagated_distinction": (
                    state.t02_require_raw_vs_propagated_distinction
                ),
                "t02_raw_vs_propagated_distinct": (
                    state.t02_raw_vs_propagated_distinct
                ),
                "t03_competition_id": (
                    None if t03_result is None else t03_result.state.competition_id
                ),
                "t03_convergence_status": (
                    None if t03_result is None else t03_result.state.convergence_status.value
                ),
                "t03_current_leader_hypothesis_id": (
                    None if t03_result is None else t03_result.state.current_leader_hypothesis_id
                ),
                "t03_provisional_frontrunner_hypothesis_id": (
                    None
                    if t03_result is None
                    else t03_result.state.provisional_frontrunner_hypothesis_id
                ),
                "t03_tied_competitor_count": (
                    None if t03_result is None else len(t03_result.state.tied_competitor_ids)
                ),
                "t03_blocked_hypothesis_count": (
                    None if t03_result is None else len(t03_result.state.blocked_hypothesis_ids)
                ),
                "t03_eliminated_hypothesis_count": (
                    None if t03_result is None else len(t03_result.state.eliminated_hypothesis_ids)
                ),
                "t03_reactivated_hypothesis_count": (
                    None if t03_result is None else len(t03_result.state.reactivated_hypothesis_ids)
                ),
                "t03_honest_nonconvergence": (
                    None if t03_result is None else t03_result.state.honest_nonconvergence
                ),
                "t03_bounded_plurality": (
                    None if t03_result is None else t03_result.state.bounded_plurality
                ),
                "t03_convergence_consumer_ready": (
                    None if t03_result is None else t03_result.gate.convergence_consumer_ready
                ),
                "t03_frontier_consumer_ready": (
                    None if t03_result is None else t03_result.gate.frontier_consumer_ready
                ),
                "t03_nonconvergence_preserved": (
                    None if t03_result is None else t03_result.gate.nonconvergence_preserved
                ),
                "t03_forbidden_shortcuts": (
                    None if t03_result is None else t03_result.gate.forbidden_shortcuts
                ),
                "t03_restrictions": (
                    None if t03_result is None else t03_result.gate.restrictions
                ),
                "t03_publication_current_leader": (
                    None if t03_result is None else t03_result.state.publication_frontier.current_leader
                ),
                "t03_publication_competitive_neighborhood": (
                    None
                    if t03_result is None
                    else t03_result.state.publication_frontier.competitive_neighborhood
                ),
                "t03_publication_unresolved_conflicts": (
                    None
                    if t03_result is None
                    else t03_result.state.publication_frontier.unresolved_conflicts
                ),
                "t03_publication_open_slots": (
                    None if t03_result is None else t03_result.state.publication_frontier.open_slots
                ),
                "t03_publication_stability_status": (
                    None
                    if t03_result is None
                    else t03_result.state.publication_frontier.stability_status
                ),
                "t03_scope": (
                    None if t03_result is None else t03_result.scope_marker.scope
                ),
                "t03_scope_rt01_contour_only": (
                    None if t03_result is None else t03_result.scope_marker.rt01_contour_only
                ),
                "t03_scope_t03_first_slice_only": (
                    None if t03_result is None else t03_result.scope_marker.t03_first_slice_only
                ),
                "t03_scope_t04_implemented": (
                    None if t03_result is None else t03_result.scope_marker.t04_implemented
                ),
                "t03_scope_o01_implemented": (
                    None if t03_result is None else t03_result.scope_marker.o01_implemented
                ),
                "t03_scope_o02_implemented": (
                    None if t03_result is None else t03_result.scope_marker.o02_implemented
                ),
                "t03_scope_o03_implemented": (
                    None if t03_result is None else t03_result.scope_marker.o03_implemented
                ),
                "t03_scope_full_silent_thought_line_implemented": (
                    None
                    if t03_result is None
                    else t03_result.scope_marker.full_silent_thought_line_implemented
                ),
                "t03_scope_repo_wide_adoption": (
                    None if t03_result is None else t03_result.scope_marker.repo_wide_adoption
                ),
                "t03_require_convergence_consumer": state.t03_require_convergence_consumer,
                "t03_require_frontier_consumer": state.t03_require_frontier_consumer,
                "t03_require_nonconvergence_preservation": (
                    state.t03_require_nonconvergence_preservation
                ),
                "t04_schema_id": (
                    None if t04_result is None else t04_result.state.schema_id
                ),
                "t04_focus_targets_count": (
                    None if t04_result is None else len(t04_result.state.focus_targets)
                ),
                "t04_peripheral_targets_count": (
                    None if t04_result is None else len(t04_result.state.peripheral_targets)
                ),
                "t04_attention_owner": (
                    None if t04_result is None else t04_result.state.attention_owner.value
                ),
                "t04_focus_mode": (
                    None if t04_result is None else t04_result.state.focus_mode.value
                ),
                "t04_control_estimate": (
                    None if t04_result is None else t04_result.state.control_estimate
                ),
                "t04_stability_estimate": (
                    None if t04_result is None else t04_result.state.stability_estimate
                ),
                "t04_redirect_cost": (
                    None if t04_result is None else t04_result.state.redirect_cost
                ),
                "t04_reportability_status": (
                    None
                    if t04_result is None
                    else t04_result.state.reportability_status.value
                ),
                "t04_focus_ownership_consumer_ready": (
                    None if t04_result is None else t04_result.gate.focus_ownership_consumer_ready
                ),
                "t04_reportable_focus_consumer_ready": (
                    None if t04_result is None else t04_result.gate.reportable_focus_consumer_ready
                ),
                "t04_peripheral_preservation_ready": (
                    None if t04_result is None else t04_result.gate.peripheral_preservation_ready
                ),
                "t04_forbidden_shortcuts": (
                    None if t04_result is None else t04_result.gate.forbidden_shortcuts
                ),
                "t04_restrictions": (
                    None if t04_result is None else t04_result.gate.restrictions
                ),
                "t04_scope": (
                    None if t04_result is None else t04_result.scope_marker.scope
                ),
                "t04_scope_rt01_contour_only": (
                    None if t04_result is None else t04_result.scope_marker.rt01_contour_only
                ),
                "t04_scope_t04_first_slice_only": (
                    None if t04_result is None else t04_result.scope_marker.t04_first_slice_only
                ),
                "t04_scope_o01_implemented": (
                    None if t04_result is None else t04_result.scope_marker.o01_implemented
                ),
                "t04_scope_o02_implemented": (
                    None if t04_result is None else t04_result.scope_marker.o02_implemented
                ),
                "t04_scope_o03_implemented": (
                    None if t04_result is None else t04_result.scope_marker.o03_implemented
                ),
                "t04_scope_full_attention_line_implemented": (
                    None
                    if t04_result is None
                    else t04_result.scope_marker.full_attention_line_implemented
                ),
                "t04_scope_repo_wide_adoption": (
                    None if t04_result is None else t04_result.scope_marker.repo_wide_adoption
                ),
            }
        ),
        "persist_transition_accepted": (
            None if result.persist_transition is None else result.persist_transition.accepted
        ),
        "dispatch_lineage": result.dispatch_lineage,
    }
