from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.a03_internal_tool_affordances import (
    A03InternalOperationCandidate,
    A03InternalOperationCandidateSet,
    A03InvocationContract,
    A03ObservationHook,
    A03OperationBoundaryKind,
    A03OperationSourceProfile,
    A03ToolClass,
    A03ToolCostProfile,
    A03ToolFailureSignature,
    A03ToolInputSpec,
    A03ToolOutputSpec,
    A03ToolSideEffectProfile,
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
        reason="runtime topology a03",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.a03.runtime:{case_id}:c1",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:internal_diagnostic_scan",
            ),
        ),
    )


def _incomplete_a03_candidate_set(case_id: str) -> A03InternalOperationCandidateSet:
    return A03InternalOperationCandidateSet(
        candidate_set_id=f"{case_id}:a03:set",
        candidates=(
            A03InternalOperationCandidate(
                operation_ref=f"{case_id}:op",
                local_label="internal_diagnostic_scan",
                tool_class=A03ToolClass.DIAGNOSTIC,
                source_profile=A03OperationSourceProfile(
                    source_module="tests.a03.runtime",
                    source_surface="tests.surface",
                    provenance_refs=("tests.a03.runtime",),
                    source_lineage=("tests.a03.runtime", case_id),
                ),
                boundary_kind=A03OperationBoundaryKind.REUSABLE_TOOL,
                invocation_contract=A03InvocationContract(
                    accepted_input_types=(A03ToolInputSpec(type_name="state_packet", required=True),),
                    produced_output_types=(),
                    required_context=("mode:continue_stream",),
                    preconditions=("requires_observation:internal_state",),
                    abort_conditions=(),
                    completion_criteria=(),
                ),
                observation_hooks=(
                    A03ObservationHook(
                        hook_id=f"{case_id}:obs",
                        signal_ref="internal_state",
                        verification_required=True,
                    ),
                ),
                failure_signatures=(),
                cost_profile=A03ToolCostProfile(latency_class="bounded_tick", cost_band="low"),
                side_effect_profile=A03ToolSideEffectProfile(side_effect_refs=(), risk_band="bounded"),
                controllability_hint=0.8,
                reliability_hint=0.8,
                reuse_scope="frontier_narrow",
                required_context=("mode:continue_stream",),
                canonical_tool_id_hint=f"a01:{case_id}:internal_diagnostic_scan",
            ),
        ),
        source_lineage=("tests.a03.runtime", case_id),
        active_mode="continue_stream",
        resource_pressure=False,
        available_observation_channels=("internal_state",),
        reason="incomplete contract fixture",
    )


def test_runtime_topology_graph_includes_a03_checkpoint_and_surface() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "rt01.a03_internal_tool_affordances_checkpoint" in graph.mandatory_checkpoint_ids
    assert "a03_internal_tool_affordances.tool_affordance_result" in graph.source_of_truth_surfaces
    a_line_node = next(item for item in graph.nodes if item.node_id == "node.a_line")
    assert "rt01.a02_capability_gap_detection_checkpoint" in a_line_node.checkpoint_ids
    assert "rt01.a03_internal_tool_affordances_checkpoint" in a_line_node.checkpoint_ids
    assert "rt01.a_line_normalization_checkpoint" in a_line_node.checkpoint_ids
    assert a_line_node.checkpoint_ids.index("rt01.a02_capability_gap_detection_checkpoint") < a_line_node.checkpoint_ids.index(
        "rt01.a03_internal_tool_affordances_checkpoint"
    )
    assert a_line_node.checkpoint_ids.index("rt01.a03_internal_tool_affordances_checkpoint") < a_line_node.checkpoint_ids.index(
        "rt01.a_line_normalization_checkpoint"
    )


def test_dispatch_a03_require_path_is_enforced() -> None:
    case_id = "runtime-topology-a03-require"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=_candidate_set(case_id),
                a03_operation_candidate_set=_incomplete_a03_candidate_set(case_id),
                require_a03_tool_contract_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a03_internal_tool_affordances_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_a03_tool_contract_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_a03_integration_indispensability_rejects_gate_disabled_fixture_on_production_route() -> None:
    case_id = "runtime-topology-a03-integration-indispensability"
    enabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=SubjectTickContext(
                a01_raw_affordance_candidate_set=_candidate_set(case_id),
                a03_operation_candidate_set=_incomplete_a03_candidate_set(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert enabled.decision.accepted is True
    assert enabled.subject_tick_result is not None
    enabled_checkpoint = next(
        item
        for item in enabled.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a03_internal_tool_affordances_checkpoint"
    )
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a03_contract_incomplete_detour" in enabled_checkpoint.required_action

    disabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(f"{case_id}-disabled"),
            context=SubjectTickContext(
                disable_a03_enforcement=True,
                a01_raw_affordance_candidate_set=_candidate_set(f"{case_id}-disabled"),
                a03_operation_candidate_set=_incomplete_a03_candidate_set(f"{case_id}-disabled"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert disabled.decision.accepted is False
    assert disabled.subject_tick_result is None
    assert (
        RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS
        in disabled.decision.restrictions
    )

