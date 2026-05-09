from __future__ import annotations

from dataclasses import dataclass

from substrate.m01_homeostatic_salience_imprint import (
    M01AttributionEvidence,
    M01AttributionStatus,
    M01ImprintPacket,
    M01InputBundle,
    M01RegulatoryAxisDelta,
    M01RegulatoryDirection,
    M01Result,
    M01TemporalCouplingEvidence,
    M01TemporalWindowStatus,
    M01TraceInput,
    M01TraceKind,
    build_m01_homeostatic_salience_imprint,
)


@dataclass(frozen=True, slots=True)
class M01HarnessCase:
    case_id: str
    input_bundle: M01InputBundle | None
    imprint_enabled: bool = True


@dataclass(frozen=True, slots=True)
class M01HarnessRun:
    m01_result: M01Result


def m01_trace(
    *,
    trace_id: str,
    trace_kind: M01TraceKind = M01TraceKind.EVENT,
    semantic_signature: str = "trace:generic",
    timestamp_or_sequence: str = "seq:1",
    scope: str = "runtime_tick_scope",
    novelty_hint: float | None = None,
    recency_hint: float | None = None,
    outcome_hint: str | None = None,
    provenance: tuple[str, ...] = ("tests.m01",),
) -> M01TraceInput:
    return M01TraceInput(
        trace_id=trace_id,
        trace_kind=trace_kind,
        semantic_signature=semantic_signature,
        timestamp_or_sequence=timestamp_or_sequence,
        scope=scope,
        novelty_hint=novelty_hint,
        recency_hint=recency_hint,
        outcome_hint=outcome_hint,
        provenance=provenance,
    )


def m01_delta(
    *,
    delta_id: str,
    axis_id: str,
    before_value: float = 0.5,
    after_value: float = 0.8,
    deviation_before: float = 0.2,
    deviation_after: float = 0.8,
    direction: M01RegulatoryDirection = M01RegulatoryDirection.WORSENING,
    intensity: float = 0.75,
    rate_hint: float = 0.4,
    measurement_confidence: float = 0.85,
    stabilization_marker: bool = False,
    recovery_marker: bool = False,
    provenance: tuple[str, ...] = ("tests.m01.delta",),
) -> M01RegulatoryAxisDelta:
    return M01RegulatoryAxisDelta(
        delta_id=delta_id,
        axis_id=axis_id,
        before_value=before_value,
        after_value=after_value,
        deviation_before=deviation_before,
        deviation_after=deviation_after,
        direction=direction,
        intensity=intensity,
        rate_hint=rate_hint,
        measurement_confidence=measurement_confidence,
        stabilization_marker=stabilization_marker,
        recovery_marker=recovery_marker,
        provenance=provenance,
    )


def m01_coupling(
    *,
    trace_id: str,
    delta_refs: tuple[str, ...],
    temporal_window_status: M01TemporalWindowStatus = M01TemporalWindowStatus.WITHIN_WINDOW,
    confidence: float = 0.82,
) -> M01TemporalCouplingEvidence:
    return M01TemporalCouplingEvidence(
        trace_id=trace_id,
        regulatory_delta_refs=delta_refs,
        temporal_window_status=temporal_window_status,
        confidence=confidence,
    )


def m01_attribution(
    *,
    trace_id: str,
    attribution_status: M01AttributionStatus = M01AttributionStatus.SELF_RELEVANT,
    self_side_share: float = 0.75,
    residual_uncertainty: float = 0.2,
    provenance: tuple[str, ...] = ("tests.m01.attr",),
) -> M01AttributionEvidence:
    return M01AttributionEvidence(
        trace_id=trace_id,
        attribution_status=attribution_status,
        self_side_share=self_side_share,
        residual_uncertainty=residual_uncertainty,
        provenance=provenance,
    )


def m01_bundle(
    *,
    bundle_id: str,
    traces: tuple[M01TraceInput, ...],
    deltas: tuple[M01RegulatoryAxisDelta, ...],
    coupling: tuple[M01TemporalCouplingEvidence, ...],
    attribution: tuple[M01AttributionEvidence, ...],
    prior_imprints: tuple[M01ImprintPacket, ...] = (),
    source_lineage: tuple[str, ...] = (),
    reason: str = "tests.m01 bundle",
) -> M01InputBundle:
    return M01InputBundle(
        bundle_id=bundle_id,
        traces=traces,
        regulatory_deltas=deltas,
        temporal_coupling=coupling,
        attribution=attribution,
        prior_imprints=prior_imprints,
        source_lineage=source_lineage,
        reason=reason,
    )


def build_m01_harness_case(case: M01HarnessCase) -> M01HarnessRun:
    result = build_m01_homeostatic_salience_imprint(
        tick_id=f"tests.m01:{case.case_id}",
        tick_index=1,
        input_bundle=case.input_bundle,
        imprint_enabled=case.imprint_enabled,
    )
    return M01HarnessRun(m01_result=result)
