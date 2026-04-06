from __future__ import annotations

from dataclasses import dataclass

from substrate.mode_arbitration import (
    ModeArbitrationContext,
    ModeArbitrationState,
    build_mode_arbitration,
)
from substrate.stream_diversification import (
    StreamDiversificationContext,
    StreamDiversificationState,
)
from substrate.tension_scheduler import TensionSchedulerContext, TensionSchedulerState
from tests.substrate.c04_testkit import build_c04_upstream


@dataclass(frozen=True, slots=True)
class C05UpstreamBundle:
    stream: object
    scheduler: object
    diversification: object
    mode_arbitration: object
    regulation: object
    affordances: object
    preferences: object
    viability: object


def build_c05_upstream(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool = False,
    prior_stream_state: object | None = None,
    prior_scheduler_state: TensionSchedulerState | None = None,
    prior_diversification_state: StreamDiversificationState | None = None,
    prior_mode_state: ModeArbitrationState | None = None,
    scheduler_context: TensionSchedulerContext | None = None,
    diversification_context: StreamDiversificationContext | None = None,
    mode_context: ModeArbitrationContext | None = None,
) -> C05UpstreamBundle:
    upstream = build_c04_upstream(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
        prior_stream_state=prior_stream_state,
        prior_scheduler_state=prior_scheduler_state,
        prior_diversification_state=prior_diversification_state,
        scheduler_context=scheduler_context,
        diversification_context=diversification_context,
    )
    context = mode_context
    if context is None and prior_mode_state is not None:
        context = ModeArbitrationContext(prior_mode_arbitration_state=prior_mode_state)
    mode_arbitration = build_mode_arbitration(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=context,
    )
    return C05UpstreamBundle(
        stream=upstream.stream,
        scheduler=upstream.scheduler,
        diversification=upstream.diversification,
        mode_arbitration=mode_arbitration,
        regulation=upstream.regulation,
        affordances=upstream.affordances,
        preferences=upstream.preferences,
        viability=upstream.viability,
    )
