from __future__ import annotations

from substrate.regulation.models import (
    NeedAxis,
    NeedSignal,
    PressureState,
    RegulationBias,
    RegulationConfidence,
    RegulationState,
    RegulationTelemetry,
    TradeoffState,
)


def build_regulation_telemetry(
    *,
    state: RegulationState,
    deviations,
    pressures: tuple[PressureState, ...],
    tradeoff: TradeoffState,
    bias: RegulationBias,
    signals: tuple[NeedSignal, ...],
    source_lineage: tuple[str, ...],
    confidence: RegulationConfidence,
    causal_basis: str,
    attempted_paths: tuple[str, ...],
) -> RegulationTelemetry:
    return RegulationTelemetry(
        tracked_axes=tuple(need.axis for need in state.needs),
        source_lineage=source_lineage,
        signal_refs=tuple(signal.source_ref or "unspecified" for signal in signals),
        used_preferred_ranges=tuple(
            (need.axis, need.preferred_range) for need in state.needs
        ),
        deviations=deviations,
        pressures=pressures,
        tradeoff=tradeoff,
        downstream_bias=bias,
        confidence=confidence,
        partial_known_reason=state.partial_known.reason if state.partial_known else None,
        abstain_reason=state.abstention.reason if state.abstention else None,
        causal_basis=causal_basis,
        attempted_paths=attempted_paths,
    )


def pressure_table(state: RegulationState) -> tuple[tuple[NeedAxis, float], ...]:
    return tuple((need.axis, need.pressure) for need in state.needs)
