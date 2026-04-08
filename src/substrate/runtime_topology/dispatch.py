from __future__ import annotations

from substrate.runtime_topology.models import (
    RuntimeDispatchRequest,
    RuntimeDispatchResult,
    RuntimeRouteClass,
)
from substrate.runtime_topology.policy import (
    build_minimal_runtime_topology_bundle,
    evaluate_runtime_dispatch_decision,
)
from substrate.subject_tick import execute_subject_tick, persist_subject_tick_result_via_f01


def dispatch_runtime_tick(request: RuntimeDispatchRequest) -> RuntimeDispatchResult:
    if not isinstance(request, RuntimeDispatchRequest):
        raise TypeError("dispatch_runtime_tick requires RuntimeDispatchRequest")

    bundle = build_minimal_runtime_topology_bundle()
    tick_graph = bundle.tick_graph
    decision = evaluate_runtime_dispatch_decision(request=request, bundle=bundle)
    if not decision.accepted:
        return RuntimeDispatchResult(
            decision=decision,
            bundle=bundle,
            tick_graph=tick_graph,
            request=request,
            subject_tick_result=None,
            persist_transition=None,
            dispatch_lineage=("runtime_topology.dispatch_runtime_tick",),
        )

    subject_tick_result = execute_subject_tick(
        tick_input=request.tick_input,
        context=request.context,
    )
    persist_transition = None
    if request.persist_via_f01:
        persist_transition = persist_subject_tick_result_via_f01(
            result=subject_tick_result,
            runtime_state=request.runtime_state,
            transition_id=request.transition_id,
            requested_at=request.requested_at,
            cause_chain=request.cause_chain,
        )

    return RuntimeDispatchResult(
        decision=decision,
        bundle=bundle,
        tick_graph=tick_graph,
        request=request,
        subject_tick_result=subject_tick_result,
        persist_transition=persist_transition,
        dispatch_lineage=(
            "runtime_topology.dispatch_runtime_tick",
            f"route:{request.route_class.value}",
            "execution_spine:RT01",
        ),
    )


def dispatch_rt01_production_tick(
    *,
    tick_input,
    context=None,
    persist_via_f01: bool = False,
    runtime_state=None,
    transition_id: str | None = None,
    requested_at: str | None = None,
    cause_chain: tuple[str, ...] = ("runtime-topology-dispatch",),
) -> RuntimeDispatchResult:
    return dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=tick_input,
            context=context,
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            allow_helper_route=False,
            allow_test_only_route=False,
            persist_via_f01=persist_via_f01,
            runtime_state=runtime_state,
            transition_id=transition_id,
            requested_at=requested_at,
            cause_chain=cause_chain,
        )
    )
