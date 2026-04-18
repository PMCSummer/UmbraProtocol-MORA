from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.p01_project_formation import (
    P01AuthoritySourceKind,
    P01ProjectSignalInput,
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
        confidence=0.83,
        grounded=True,
        quoted=False,
        turn_index=turn_index,
        provenance=f"tests.p01.runtime_topology:{signal_id}",
        target_claim=None,
    )


def _grounded_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="rtp1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="rtp2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="rtp3",
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


def _project_signal(
    *,
    signal_id: str,
    authority: P01AuthoritySourceKind,
    target: str,
    missing_precondition_marker: bool = False,
    blocker_present: bool = False,
) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=signal_id,
        signal_kind="directive",
        authority_source_kind=authority,
        target_summary=target,
        grounded_basis_present=True,
        missing_precondition_marker=missing_precondition_marker,
        blocker_present=blocker_present,
        provenance=f"tests.p01.runtime_topology:{signal_id}",
    )


def test_runtime_topology_graph_includes_p01_node_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "P01" in graph.runtime_order
    assert graph.runtime_order.index("O03") < graph.runtime_order.index("P01")
    assert graph.runtime_order.index("P01") < graph.runtime_order.index("RT01")
    assert "rt01.p01_project_formation_checkpoint" in graph.mandatory_checkpoint_ids
    assert "p01_project_formation.intention_stack_state" in graph.source_of_truth_surfaces


def test_dispatch_p01_default_missing_precondition_detour_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-p01-default-baseline"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-p01-default-baseline"),
                p01_project_signals=(
                    _project_signal(
                        signal_id="rtp01-baseline",
                        authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                        target="prepare nightly reviewer run",
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    blocked = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-p01-default-blocked"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-p01-default-blocked"),
                p01_project_signals=(
                    _project_signal(
                        signal_id="rtp01-blocked",
                        authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                        target="prepare nightly reviewer run",
                        missing_precondition_marker=True,
                        blocker_present=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert blocked.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    blocked_checkpoint = next(
        checkpoint
        for checkpoint in blocked.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert blocked_checkpoint.status.value == "enforced_detour"
    assert "default_p01_missing_precondition_detour" in blocked_checkpoint.required_action
    assert blocked.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_p01_explicit_require_paths_are_load_bearing() -> None:
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-p01-required"),
            context=SubjectTickContext(
                require_p01_intention_stack_consumer=True,
                require_p01_authority_bound_consumer=True,
                require_p01_project_handoff_consumer=True,
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-p01-required"),
                p01_project_signals=(
                    _project_signal(
                        signal_id="rtp01-required",
                        authority=P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION,
                        target="prepare nightly reviewer run",
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert required.subject_tick_result is not None
    checkpoint = next(
        item
        for item in required.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p01_project_formation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_p01_intention_stack_consumer" in checkpoint.required_action
    assert "require_p01_authority_bound_consumer" in checkpoint.required_action
    assert "require_p01_project_handoff_consumer" in checkpoint.required_action
