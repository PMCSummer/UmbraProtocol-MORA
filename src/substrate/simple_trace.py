from __future__ import annotations

from pathlib import Path

from substrate.runtime_tap_trace import deactivate_tick_trace, derive_tick_id, finish_tick_trace, start_tick_trace
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.subject_tick import SubjectTickInput


def run_tick_and_write_simple_trace(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool,
    output_root: str | Path,
    route_class: str = "production_contour",
) -> dict[str, object]:
    tick_id = derive_tick_id(case_id, prior_tick_index=None)
    token = start_tick_trace(tick_id=tick_id, output_root=output_root)
    try:
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=SubjectTickInput(
                    case_id=case_id,
                    energy=energy,
                    cognitive=cognitive,
                    safety=safety,
                    unresolved_preference=unresolved_preference,
                ),
                route_class=RuntimeRouteClass(route_class),
            )
        )
    finally:
        deactivate_tick_trace(token)
    return finish_tick_trace(tick_id=tick_id)
