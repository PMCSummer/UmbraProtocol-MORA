from __future__ import annotations

from dataclasses import dataclass

from substrate.n03_autobiographical_relevance import (
    N03AutobiographicalTraceKind,
    N03CurrentTarget,
    N03CurrentTargetKind,
    N03InputBundle,
    N03Result,
    N03TraceCandidate,
    build_n03_autobiographical_relevance,
)


@dataclass(frozen=True, slots=True)
class N03HarnessCase:
    case_id: str
    input_bundle: N03InputBundle | None
    relevance_enabled: bool = True


@dataclass(frozen=True, slots=True)
class N03HarnessRun:
    n03_result: N03Result


def n03_trace(
    *,
    source_trace_id: str,
    trace_kind: N03AutobiographicalTraceKind = N03AutobiographicalTraceKind.PRIOR_FAILURE,
    semantic_topic_tags: tuple[str, ...] = ("topic:regulation",),
    commitment_refs: tuple[str, ...] = ("commitment:a",),
    capability_gap_refs: tuple[str, ...] = (),
    affordance_refs: tuple[str, ...] = (),
    internal_tool_refs: tuple[str, ...] = (),
    self_binding_refs: tuple[str, ...] = (),
    attribution_profile: str = "self",
    failure_or_recovery_signature: str = "sig:failure",
    identity_region_refs: tuple[str, ...] = ("region:self",),
    temporal_validity_status: str = "valid",
    recurrence_count: int = 2,
    vividness_hint: float = 0.4,
    recency_hint: float = 0.4,
    confidence: float = 0.8,
    provenance: tuple[str, ...] = ("tests.n03.trace",),
) -> N03TraceCandidate:
    return N03TraceCandidate(
        source_trace_id=source_trace_id,
        trace_kind=trace_kind,
        semantic_topic_tags=semantic_topic_tags,
        commitment_refs=commitment_refs,
        capability_gap_refs=capability_gap_refs,
        affordance_refs=affordance_refs,
        internal_tool_refs=internal_tool_refs,
        self_binding_refs=self_binding_refs,
        attribution_profile=attribution_profile,
        failure_or_recovery_signature=failure_or_recovery_signature,
        identity_region_refs=identity_region_refs,
        temporal_validity_status=temporal_validity_status,
        recurrence_count=recurrence_count,
        vividness_hint=vividness_hint,
        recency_hint=recency_hint,
        confidence=confidence,
        provenance=provenance,
    )


def n03_target(
    *,
    current_target_id: str,
    target_kind: N03CurrentTargetKind = N03CurrentTargetKind.REGULATION_DEMAND,
    active_commitment_refs: tuple[str, ...] = ("commitment:a",),
    active_capability_gap_refs: tuple[str, ...] = (),
    active_affordance_refs: tuple[str, ...] = (),
    active_internal_tool_refs: tuple[str, ...] = (),
    active_self_binding_refs: tuple[str, ...] = (),
    active_identity_region_refs: tuple[str, ...] = ("region:self",),
    active_drift_markers: tuple[str, ...] = (),
    semantic_topic_tags: tuple[str, ...] = ("topic:regulation",),
    attribution_profile: str = "self",
    regulation_or_planning_pressure: float = 0.7,
    current_evidence_signature: str = "sig:current",
    provenance: tuple[str, ...] = ("tests.n03.target",),
) -> N03CurrentTarget:
    return N03CurrentTarget(
        current_target_id=current_target_id,
        target_kind=target_kind,
        active_commitment_refs=active_commitment_refs,
        active_capability_gap_refs=active_capability_gap_refs,
        active_affordance_refs=active_affordance_refs,
        active_internal_tool_refs=active_internal_tool_refs,
        active_self_binding_refs=active_self_binding_refs,
        active_identity_region_refs=active_identity_region_refs,
        active_drift_markers=active_drift_markers,
        semantic_topic_tags=semantic_topic_tags,
        attribution_profile=attribution_profile,
        regulation_or_planning_pressure=regulation_or_planning_pressure,
        current_evidence_signature=current_evidence_signature,
        provenance=provenance,
    )


def n03_bundle(
    *,
    bundle_id: str,
    traces: tuple[N03TraceCandidate, ...],
    targets: tuple[N03CurrentTarget, ...],
    source_lineage: tuple[str, ...] = (),
    reason: str = "tests.n03 bundle",
) -> N03InputBundle:
    return N03InputBundle(
        bundle_id=bundle_id,
        trace_candidates=traces,
        current_targets=targets,
        source_lineage=source_lineage,
        reason=reason,
    )


def build_n03_harness_case(case: N03HarnessCase) -> N03HarnessRun:
    result = build_n03_autobiographical_relevance(
        tick_id=f"tests.n03:{case.case_id}",
        tick_index=1,
        input_bundle=case.input_bundle,
        relevance_enabled=case.relevance_enabled,
    )
    return N03HarnessRun(n03_result=result)
