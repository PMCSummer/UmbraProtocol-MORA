from __future__ import annotations

from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput
from substrate.w02_regularity_extraction import (
    W02InputBundle,
    W02PresenceMode,
    W02RegularityCandidateType,
    W02TraceRef,
)


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _w02_input(case_id: str) -> W02InputBundle:
    return W02InputBundle(
        bundle_id=f"{case_id}:w02:bundle",
        traces=(
            W02TraceRef(
                trace_id=f"{case_id}:trace:1",
                sequence_index=1,
                entity_id=f"{case_id}:entity",
                source_authority="trusted_world_provider",
                presence_mode=W02PresenceMode.PRESENT,
                admission_state="admitted",
                confidence_band="high",
                provenance_ref=("tests.w02.runtime", case_id),
                action_ref="action:a",
                effect_ref="effect:a",
                structural_signature="shape:cube",
                kind_label="kind:block",
                role_label="role:anchor",
                provider_label="provider:a",
                contradiction_markers=(),
                is_duplicate_packet=False,
                provider_bias_marker=False,
                text_artifact_marker=False,
                revoked=False,
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
            W02TraceRef(
                trace_id=f"{case_id}:trace:2",
                sequence_index=2,
                entity_id=f"{case_id}:entity",
                source_authority="weak_scaffold_provider",
                presence_mode=W02PresenceMode.PRESENT,
                admission_state="admitted",
                confidence_band="high",
                provenance_ref=("tests.w02.runtime", case_id),
                action_ref="action:b",
                effect_ref="effect:b",
                structural_signature="shape:cube",
                kind_label="kind:block",
                role_label="role:anchor",
                provider_label="provider:b",
                contradiction_markers=(),
                is_duplicate_packet=False,
                provider_bias_marker=False,
                text_artifact_marker=False,
                revoked=False,
                candidate_type=W02RegularityCandidateType.INSTANCE,
            ),
        ),
        source_lineage=("tests.w02.runtime", case_id),
        reason="w02 runtime integration fixture",
    )


def test_w02_runtime_topology_contains_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.w02_regularity_extraction_checkpoint" in graph.mandatory_checkpoint_ids
    assert "w02_regularity_extraction.regularity_extraction_result" in graph.source_of_truth_surfaces


def test_w02_is_after_w01_before_m01() -> None:
    case_id = "runtime-topology-w02-order"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                w02_input_bundle=_w02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    assert ids.index("rt01.w01_bounded_world_loop_checkpoint") < ids.index(
        "rt01.w02_regularity_extraction_checkpoint"
    )
    assert ids.index("rt01.w02_regularity_extraction_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_w02_disable_flag_rejected_in_production_route() -> None:
    case_id = "runtime-topology-w02-disabled"
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                disable_w02_enforcement=True,
                w02_input_bundle=_w02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert denied.decision.accepted is False
    assert denied.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in denied.decision.restrictions


def test_w02_source_of_truth_surface_not_telemetry_only() -> None:
    case_id = "runtime-topology-w02-surface"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                w02_input_bundle=_w02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.w02_result.regularity_records
