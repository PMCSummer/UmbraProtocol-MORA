from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome


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
        provenance=f"tests.o03.runtime_topology:{signal_id}",
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


def _transparent_candidate(case_id: str) -> O03CandidateStrategyInput:
    return O03CandidateStrategyInput(
        candidate_move_id=f"{case_id}:transparent",
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=True,
        material_uncertainty_omitted=False,
        selective_omission_risk_marker=False,
        reversibility_preserved=True,
        repairability_preserved=True,
    )


def _risky_candidate(case_id: str) -> O03CandidateStrategyInput:
    return O03CandidateStrategyInput(
        candidate_move_id=f"{case_id}:risky",
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=False,
        material_uncertainty_omitted=True,
        selective_omission_risk_marker=True,
        asymmetry_opportunity_marker=True,
        dependency_shaping_marker=True,
        autonomy_narrowing_marker=True,
        reversibility_preserved=False,
        repairability_preserved=False,
        strong_compliance_pull_marker=True,
    )


def test_runtime_topology_graph_includes_o03_node_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "O03" in graph.runtime_order
    assert graph.runtime_order.index("O02") < graph.runtime_order.index("O03")
    assert graph.runtime_order.index("O03") < graph.runtime_order.index("RT01")
    assert "rt01.o03_strategy_class_evaluation_checkpoint" in graph.mandatory_checkpoint_ids
    assert "o03_strategy_class_evaluation.strategy_state" in graph.source_of_truth_surfaces


def test_dispatch_o03_default_high_entropy_detour_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o03-default-baseline"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-o03-default-baseline"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    risky = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o03-default-risky"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_risky_candidate("runtime-topology-o03-default-risky"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert risky.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    risky_checkpoint = next(
        checkpoint
        for checkpoint in risky.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "enforced_detour"
    assert (
        "default_o03_transparency_clarification_detour" in risky_checkpoint.required_action
        or "default_o03_exploitative_candidate_block_detour" in risky_checkpoint.required_action
    )
    assert risky.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_dispatch_o03_explicit_require_paths_are_load_bearing() -> None:
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o03-required"),
            context=SubjectTickContext(
                require_o03_strategy_contract_consumer=True,
                require_o03_cooperative_selection_consumer=True,
                require_o03_transparency_preserving_consumer=True,
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_risky_candidate("runtime-topology-o03-required"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert required.subject_tick_result is not None
    checkpoint = next(
        item
        for item in required.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o03_strategy_contract_consumer" in checkpoint.required_action
    assert "require_o03_cooperative_selection_consumer" in checkpoint.required_action
    assert "require_o03_transparency_preserving_consumer" in checkpoint.required_action
