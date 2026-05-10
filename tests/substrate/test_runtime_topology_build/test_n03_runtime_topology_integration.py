from __future__ import annotations

from substrate.n03_autobiographical_relevance import (
    N03AutobiographicalTraceKind,
    N03CurrentTarget,
    N03CurrentTargetKind,
    N03InputBundle,
    N03TraceCandidate,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _n03_input(case_id: str) -> N03InputBundle:
    return N03InputBundle(
        bundle_id=f"{case_id}:n03:bundle",
        trace_candidates=(
            N03TraceCandidate(
                source_trace_id=f"{case_id}:trace",
                trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE,
                semantic_topic_tags=("topic:regulation",),
                commitment_refs=("commitment:alpha",),
                capability_gap_refs=(),
                affordance_refs=(),
                internal_tool_refs=(),
                self_binding_refs=(),
                attribution_profile="self",
                failure_or_recovery_signature="sig:failure",
                identity_region_refs=("region:self",),
                temporal_validity_status="valid",
                recurrence_count=3,
                vividness_hint=0.3,
                recency_hint=0.4,
                confidence=0.84,
                provenance=("tests.n03.runtime", case_id),
            ),
        ),
        current_targets=(
            N03CurrentTarget(
                current_target_id=f"{case_id}:target",
                target_kind=N03CurrentTargetKind.COMMITMENT_UNDER_LOAD,
                active_commitment_refs=("commitment:alpha",),
                active_capability_gap_refs=(),
                active_affordance_refs=(),
                active_internal_tool_refs=(),
                active_self_binding_refs=(),
                active_identity_region_refs=("region:self",),
                active_drift_markers=(),
                semantic_topic_tags=("topic:regulation",),
                attribution_profile="self",
                regulation_or_planning_pressure=0.74,
                current_evidence_signature="sig:current",
                provenance=("tests.n03.runtime", case_id),
            ),
        ),
        source_lineage=("tests.n03.runtime", case_id),
        reason="n03 runtime integration fixture",
    )


def test_n03_runtime_topology_contains_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.n03_autobiographical_relevance_checkpoint" in graph.mandatory_checkpoint_ids
    assert "n03_autobiographical_relevance.autobiographical_relevance_result" in graph.source_of_truth_surfaces


def test_n03_is_after_n02_before_outcome_resolution() -> None:
    case_id = "runtime-topology-n03-order"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                n03_input_bundle=_n03_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    assert ids.index("rt01.n02_identity_drift_reflection_checkpoint") < ids.index(
        "rt01.n03_autobiographical_relevance_checkpoint"
    )
    assert ids.index("rt01.n03_autobiographical_relevance_checkpoint") < ids.index(
        "rt01.outcome_resolution_checkpoint"
    )


def test_n03_disable_flag_rejected_in_production_route() -> None:
    case_id = "runtime-topology-n03-disabled"
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                disable_n03_enforcement=True,
                n03_input_bundle=_n03_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert denied.decision.accepted is False
    assert denied.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in denied.decision.restrictions


def test_n03_source_of_truth_surface_not_telemetry_only() -> None:
    case_id = "runtime-topology-n03-surface"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                n03_input_bundle=_n03_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.n03_result.relevance_entries
