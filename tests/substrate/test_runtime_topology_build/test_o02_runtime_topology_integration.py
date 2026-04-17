from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o02_intersubjective_allostasis import O02InteractionDiagnosticsInput
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome, SubjectTickInput


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _signal(
    *,
    signal_id: str,
    relation: str,
    claim: str,
    turn_index: int,
) -> O01EntitySignal:
    return O01EntitySignal(
        signal_id=signal_id,
        entity_id_hint=None,
        referent_label="user",
        source_authority="current_user_direct",
        relation_class=relation,
        claim_value=claim,
        confidence=0.82,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.o02.runtime_topology:{signal_id}",
        target_claim=None,
    )


def _grounded_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="rtg1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="rtg2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="rtg3",
            relation="knowledge_boundary",
            claim="knows_cli_basics",
            turn_index=3,
        ),
    )


def test_runtime_topology_graph_includes_o02_node_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "O02" in graph.runtime_order
    assert graph.runtime_order.index("O01") < graph.runtime_order.index("O02")
    assert graph.runtime_order.index("O02") < graph.runtime_order.index("RT01")
    assert "rt01.o02_intersubjective_allostasis_checkpoint" in graph.mandatory_checkpoint_ids
    assert "o02_intersubjective_allostasis.regulation_state" in graph.source_of_truth_surfaces


def test_dispatch_o02_default_repair_sensitive_detour_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o02-default-baseline"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o02_interaction_diagnostics=O02InteractionDiagnosticsInput(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    repair = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o02-default-repair"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                    recent_corrections_count=2,
                    recent_misunderstanding_count=2,
                    clarification_failures=1,
                    repetition_request_count=1,
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert repair.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    repair_checkpoint = next(
        checkpoint
        for checkpoint in repair.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert repair_checkpoint.status.value == "enforced_detour"
    assert "default_o02_repair_sensitive_clarification_detour" in repair_checkpoint.required_action
    assert repair.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_dispatch_o02_explicit_require_paths_are_load_bearing() -> None:
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o02-required"),
            context=SubjectTickContext(
                require_o02_repair_sensitive_consumer=True,
                require_o02_boundary_preserving_consumer=True,
                o01_entity_signals=_grounded_signals(),
                o02_interaction_diagnostics=O02InteractionDiagnosticsInput(
                    recent_corrections_count=1,
                    recent_misunderstanding_count=1,
                    impatience_or_compression_request=True,
                    self_side_caution_required=True,
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert required.subject_tick_result is not None
    checkpoint = next(
        item
        for item in required.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o02_repair_sensitive_consumer" in checkpoint.required_action
    assert "require_o02_boundary_preserving_consumer" in checkpoint.required_action
