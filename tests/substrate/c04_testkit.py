from __future__ import annotations

from dataclasses import dataclass

from substrate.stream_diversification import (
    StreamDiversificationContext,
    StreamDiversificationState,
    build_stream_diversification,
)
from substrate.tension_scheduler import TensionSchedulerContext, TensionSchedulerState
from tests.substrate.c03_testkit import build_c03_upstream


@dataclass(frozen=True, slots=True)
class C04UpstreamBundle:
    stream: object
    scheduler: object
    diversification: object
    regulation: object
    affordances: object
    preferences: object
    viability: object


def build_c04_upstream(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool = False,
    prior_stream_state: object | None = None,
    prior_scheduler_state: TensionSchedulerState | None = None,
    prior_diversification_state: StreamDiversificationState | None = None,
    scheduler_context: TensionSchedulerContext | None = None,
    diversification_context: StreamDiversificationContext | None = None,
) -> C04UpstreamBundle:
    upstream = build_c03_upstream(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
        prior_stream_state=prior_stream_state,
        prior_scheduler_state=prior_scheduler_state,
        scheduler_context=scheduler_context,
    )
    context = diversification_context
    if context is None and prior_diversification_state is not None:
        context = StreamDiversificationContext(
            prior_diversification_state=prior_diversification_state
        )
    diversification = build_stream_diversification(
        upstream.stream,
        upstream.scheduler,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=context,
    )
    return C04UpstreamBundle(
        stream=upstream.stream,
        scheduler=upstream.scheduler,
        diversification=diversification,
        regulation=upstream.regulation,
        affordances=upstream.affordances,
        preferences=upstream.preferences,
        viability=upstream.viability,
    )
