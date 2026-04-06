from __future__ import annotations

from dataclasses import dataclass

from substrate.tension_scheduler import (
    TensionSchedulerContext,
    TensionSchedulerState,
    build_tension_scheduler,
)
from tests.substrate.c02_testkit import build_c02_upstream


@dataclass(frozen=True, slots=True)
class C03UpstreamBundle:
    stream: object
    scheduler: object
    regulation: object
    affordances: object
    preferences: object
    viability: object


def build_c03_upstream(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool = False,
    prior_stream_state: object | None = None,
    prior_scheduler_state: TensionSchedulerState | None = None,
    scheduler_context: TensionSchedulerContext | None = None,
) -> C03UpstreamBundle:
    upstream = build_c02_upstream(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
        prior_stream_state=prior_stream_state,
    )
    context = scheduler_context
    if context is None and prior_scheduler_state is not None:
        context = TensionSchedulerContext(prior_scheduler_state=prior_scheduler_state)
    scheduler = build_tension_scheduler(
        upstream.stream,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=context,
    )
    return C03UpstreamBundle(
        stream=upstream.stream,
        scheduler=scheduler,
        regulation=upstream.regulation,
        affordances=upstream.affordances,
        preferences=upstream.preferences,
        viability=upstream.viability,
    )
