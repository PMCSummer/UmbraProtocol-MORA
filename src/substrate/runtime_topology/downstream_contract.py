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
    reason: str


def derive_runtime_dispatch_contract_view(
    result: RuntimeDispatchResult,
) -> RuntimeDispatchContractView:
    if not isinstance(result, RuntimeDispatchResult):
        raise TypeError("derive_runtime_dispatch_contract_view requires RuntimeDispatchResult")
    state = None if result.subject_tick_result is None else result.subject_tick_result.state
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
        reason=result.decision.reason,
    )


def require_lawful_production_dispatch(result: RuntimeDispatchResult) -> None:
    view = derive_runtime_dispatch_contract_view(result)
    if not view.accepted:
        raise PermissionError("runtime dispatch rejected; contour path is not lawful")
    if not view.lawful_production_route:
        raise PermissionError("runtime dispatch path is not lawful production contour")
