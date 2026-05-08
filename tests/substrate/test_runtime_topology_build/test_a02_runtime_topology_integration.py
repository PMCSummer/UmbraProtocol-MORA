from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.a02_capability_gap_detection import (
    A02ControllabilityStatus,
    A02DemandClass,
    A02DemandLegitimacyStatus,
    A02DemandPacket,
    A02DemandSet,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    a01_candidate,
    a01_candidate_set,
)


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set",
        reason="runtime topology a02",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a02.runtime:{case_id}:c1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:pause_and_recover",
            ),
        ),
    )


def _missing_demand_set(case_id: str) -> A02DemandSet:
    return A02DemandSet(
        demand_set_id=f"{case_id}:a02:demand",
        demands=(
            A02DemandPacket(
                demand_id=f"{case_id}:d1",
                demanded_change_class=A02DemandClass.COMMUNICATION,
                demanded_scope=("update_sent",),
                target_channels=("world",),
                source_kind="tests",
                source_ref="tests.a02.runtime",
                urgency="normal",
                severity=2,
                allowed_latency="bounded_tick",
                legitimacy_status=A02DemandLegitimacyStatus.TYPED_LEGITIMATE,
                required_controllability=A02ControllabilityStatus.CONTROLLABLE_ONLY_CONDITIONALLY,
                world_side_requirement="optional",
                provenance=("tests.a02.runtime",),
            ),
        ),
        source_lineage=("tests.a02.runtime", case_id),
        reason="missing demand",
    )


def test_runtime_topology_graph_includes_a02_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.a02_capability_gap_detection_checkpoint" in graph.mandatory_checkpoint_ids
    assert "a02_capability_gap_detection.capability_gap_result" in graph.source_of_truth_surfaces
    a_line_node = next(item for item in graph.nodes if item.node_id == "node.a_line")
    assert "rt01.a02_capability_gap_detection_checkpoint" in a_line_node.checkpoint_ids
    assert "a02_capability_gap_detection.capability_gap_result" in a_line_node.surfaces


def test_dispatch_a02_require_path_is_enforced() -> None:
    case_id = "runtime-topology-a02-require"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
                context=SubjectTickContext(
                    a01_raw_affordance_candidate_set=_candidate_set(case_id),
                    a02_demand_set=None,
                    require_a02_partial_coverage_consumer=True,
                ),
                route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            )
        )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a02_capability_gap_detection_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_a02_partial_coverage_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_disable_a02_enforcement_is_rejected_on_production_route() -> None:
    case_id = "runtime-topology-a02-no-bypass"
    enabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=_candidate_set(case_id),
                a02_demand_set=_missing_demand_set(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert enabled.decision.accepted is True
    assert enabled.subject_tick_result is not None
    enabled_checkpoint = next(
        item
        for item in enabled.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a02_capability_gap_detection_checkpoint"
    )
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a02_missing_affordance_exploration_detour" in enabled_checkpoint.required_action

    disabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(f"{case_id}-disabled"),
            context=SubjectTickContext(
                disable_a02_enforcement=True,
                a01_raw_affordance_candidate_set=_candidate_set(f"{case_id}-disabled"),
                a02_demand_set=_missing_demand_set(f"{case_id}-disabled"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert disabled.decision.accepted is False
    assert disabled.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in disabled.decision.restrictions
