from __future__ import annotations

from dataclasses import dataclass

from substrate.m02_predictive_relevance import (
    M02InputBundle,
    M02PredictiveFeedback,
    M02PredictiveTrace,
    M02PredictionTarget,
    M02Result,
    M02TargetType,
    M02TraceKind,
    M02UtilityHorizon,
    build_m02_predictive_relevance,
)


@dataclass(frozen=True, slots=True)
class M02HarnessCase:
    case_id: str
    input_bundle: M02InputBundle | None
    relevance_enabled: bool = True


@dataclass(frozen=True, slots=True)
class M02HarnessRun:
    m02_result: M02Result


def m02_trace(
    *,
    trace_id: str,
    trace_kind: M02TraceKind = M02TraceKind.EVENT,
    semantic_label: str = "trace:predictive",
    boredom_level: float = 0.7,
    vividness_level: float = 0.2,
    novelty_level: float = 0.2,
    timestamp_or_sequence: str = "seq:1",
    context_scope: str = "runtime_scope",
    mode_context: str = "mode:analysis",
    tool_context: str | None = "tool:diagnostic",
    homeostatic_imprint_ref: str | None = None,
    homeostatic_strength_hint: float | None = None,
    provenance: tuple[str, ...] = ("tests.m02.trace",),
) -> M02PredictiveTrace:
    return M02PredictiveTrace(
        trace_id=trace_id,
        trace_kind=trace_kind,
        semantic_label=semantic_label,
        boredom_level=boredom_level,
        vividness_level=vividness_level,
        novelty_level=novelty_level,
        timestamp_or_sequence=timestamp_or_sequence,
        context_scope=context_scope,
        mode_context=mode_context,
        tool_context=tool_context,
        homeostatic_imprint_ref=homeostatic_imprint_ref,
        homeostatic_strength_hint=homeostatic_strength_hint,
        provenance=provenance,
    )


def m02_target(
    *,
    target_id: str,
    target_type: M02TargetType = M02TargetType.REGIME_DETECTION,
    utility_horizon: M02UtilityHorizon = M02UtilityHorizon.SHORT,
    context_scope: str = "runtime_scope",
    success_metric: str = "prediction_gain",
    provenance: tuple[str, ...] = ("tests.m02.target",),
) -> M02PredictionTarget:
    return M02PredictionTarget(
        target_id=target_id,
        target_type=target_type,
        utility_horizon=utility_horizon,
        context_scope=context_scope,
        success_metric=success_metric,
        provenance=provenance,
    )


def m02_feedback(
    *,
    feedback_id: str,
    trace_id: str,
    target_id: str,
    prediction_gain: float,
    error_delta: float = 0.0,
    corroboration_count: int = 2,
    failed_transfer_count: int = 0,
    spurious_risk_score: float = 0.1,
    context_locked: bool = False,
    attribution_noise_risk: bool = False,
    confidence: float = 0.8,
    provenance: tuple[str, ...] = ("tests.m02.feedback",),
) -> M02PredictiveFeedback:
    return M02PredictiveFeedback(
        feedback_id=feedback_id,
        trace_id=trace_id,
        target_id=target_id,
        prediction_gain=prediction_gain,
        error_delta=error_delta,
        corroboration_count=corroboration_count,
        failed_transfer_count=failed_transfer_count,
        spurious_risk_score=spurious_risk_score,
        context_locked=context_locked,
        attribution_noise_risk=attribution_noise_risk,
        confidence=confidence,
        provenance=provenance,
    )


def m02_bundle(
    *,
    bundle_id: str,
    traces: tuple[M02PredictiveTrace, ...],
    targets: tuple[M02PredictionTarget, ...],
    feedback: tuple[M02PredictiveFeedback, ...],
    source_lineage: tuple[str, ...] = (),
    reason: str = "tests.m02 bundle",
) -> M02InputBundle:
    return M02InputBundle(
        bundle_id=bundle_id,
        traces=traces,
        prediction_targets=targets,
        predictive_feedback=feedback,
        source_lineage=source_lineage,
        reason=reason,
    )


def build_m02_harness_case(case: M02HarnessCase) -> M02HarnessRun:
    result = build_m02_predictive_relevance(
        tick_id=f"tests.m02:{case.case_id}",
        tick_index=1,
        input_bundle=case.input_bundle,
        relevance_enabled=case.relevance_enabled,
    )
    return M02HarnessRun(m02_result=result)
