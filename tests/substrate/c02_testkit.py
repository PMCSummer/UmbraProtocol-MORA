from __future__ import annotations

from dataclasses import dataclass

from substrate.stream_kernel import StreamKernelContext, StreamKernelState, build_stream_kernel
from tests.substrate.c01_testkit import build_c01_upstream


@dataclass(frozen=True, slots=True)
class C02UpstreamBundle:
    stream: object
    regulation: object
    affordances: object
    preferences: object
    viability: object


def build_c02_upstream(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool = False,
    prior_stream_state: StreamKernelState | None = None,
    stream_context: StreamKernelContext | None = None,
) -> C02UpstreamBundle:
    upstream = build_c01_upstream(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
    )
    context = stream_context
    if context is None and prior_stream_state is not None:
        context = StreamKernelContext(prior_stream_state=prior_stream_state)
    stream = build_stream_kernel(
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=context,
    )
    return C02UpstreamBundle(
        stream=stream,
        regulation=upstream.regulation,
        affordances=upstream.affordances,
        preferences=upstream.preferences,
        viability=upstream.viability,
    )
