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
            }
        ),
        "persist_transition_accepted": (
            None if result.persist_transition is None else result.persist_transition.accepted
        ),
        "dispatch_lineage": result.dispatch_lineage,
    }
