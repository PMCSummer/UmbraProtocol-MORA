from __future__ import annotations

from substrate.runtime_topology.models import RuntimeDispatchResult


def runtime_dispatch_snapshot(result: RuntimeDispatchResult) -> dict[str, object]:
    if not isinstance(result, RuntimeDispatchResult):
        raise TypeError("runtime_dispatch_snapshot requires RuntimeDispatchResult")
    state = None if result.subject_tick_result is None else result.subject_tick_result.state
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
                "s_scope": state.s_scope,
                "s_scope_minimal_contour_only": state.s_scope_minimal_contour_only,
                "s_scope_s01_s05_implemented": state.s_scope_s01_s05_implemented,
                "s_scope_full_self_model_implemented": state.s_scope_full_self_model_implemented,
                "s_scope_repo_wide_adoption": state.s_scope_repo_wide_adoption,
            }
        ),
        "persist_transition_accepted": (
            None if result.persist_transition is None else result.persist_transition.accepted
        ),
        "dispatch_lineage": result.dispatch_lineage,
    }
