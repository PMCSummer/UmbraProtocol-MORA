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
from tests.substrate.w03_schema_consolidation_testkit import w03_input_from_w02


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
                provenance_ref=("tests.w03.runtime", case_id),
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
                candidate_type=W02RegularityCandidateType.KIND,
            ),
            W02TraceRef(
                trace_id=f"{case_id}:trace:2",
                sequence_index=2,
                entity_id=f"{case_id}:entity",
                source_authority="weak_scaffold_provider",
                presence_mode=W02PresenceMode.PRESENT,
                admission_state="admitted",
                confidence_band="high",
                provenance_ref=("tests.w03.runtime", case_id),
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
                candidate_type=W02RegularityCandidateType.KIND,
            ),
        ),
        source_lineage=("tests.w03.runtime", case_id),
        reason="w03 runtime integration fixture",
    )


def test_w03_runtime_topology_contains_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.w03_schema_consolidation_checkpoint" in graph.mandatory_checkpoint_ids
    assert "w03_schema_consolidation.schema_consolidation_result" in graph.source_of_truth_surfaces


def test_w03_is_after_w02_before_m01() -> None:
    case_id = "runtime-topology-w03-order"
    w02_input = _w02_input(case_id)
    w03_input = w03_input_from_w02(case_id=case_id, w02_input=w02_input, source_lineage=("tests.w03.runtime", case_id))
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                w02_input_bundle=w02_input,
                w03_input_bundle=w03_input,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    assert ids.index("rt01.w02_regularity_extraction_checkpoint") < ids.index(
        "rt01.w03_schema_consolidation_checkpoint"
    )
    assert ids.index("rt01.w03_schema_consolidation_checkpoint") < ids.index(
        "rt01.m01_homeostatic_salience_imprint_checkpoint"
    )


def test_world_to_narrative_chain_order_remains_stable_after_w03_hardening() -> None:
    case_id = "runtime-topology-w03-chain-order"
    w02_input = _w02_input(case_id)
    w03_input = w03_input_from_w02(case_id=case_id, w02_input=w02_input, source_lineage=("tests.w03.runtime", case_id))
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                w02_input_bundle=w02_input,
                w03_input_bundle=w03_input,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    ids = [item.checkpoint_id for item in result.subject_tick_result.state.execution_checkpoints]
    chain = [
        "rt01.w01_bounded_world_loop_checkpoint",
        "rt01.w02_regularity_extraction_checkpoint",
        "rt01.w03_schema_consolidation_checkpoint",
        "rt01.m01_homeostatic_salience_imprint_checkpoint",
        "rt01.m02_predictive_relevance_checkpoint",
        "rt01.n01_narrative_commitments_checkpoint",
        "rt01.n02_identity_drift_reflection_checkpoint",
        "rt01.n03_autobiographical_relevance_checkpoint",
        "rt01.outcome_resolution_checkpoint",
    ]
    positions = [ids.index(item) for item in chain]
    assert positions == sorted(positions)


def test_w03_disable_flag_rejected_in_production_route() -> None:
    case_id = "runtime-topology-w03-disabled"
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                disable_w03_enforcement=True,
                w02_input_bundle=_w02_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert denied.decision.accepted is False
    assert denied.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in denied.decision.restrictions


def test_w03_source_of_truth_surface_not_telemetry_only() -> None:
    case_id = "runtime-topology-w03-surface"
    w02_input = _w02_input(case_id)
    w03_input = w03_input_from_w02(case_id=case_id, w02_input=w02_input, source_lineage=("tests.w03.runtime", case_id))
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                w02_input_bundle=w02_input,
                w03_input_bundle=w03_input,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.w03_result.schema_candidates
