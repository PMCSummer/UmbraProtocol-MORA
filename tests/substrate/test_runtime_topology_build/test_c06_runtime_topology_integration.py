from __future__ import annotations

from dataclasses import replace

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.p01_project_formation import P01AuthoritySourceKind, P01ProjectSignalInput
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommunicativeActCandidate,
)
from substrate.c06_surfacing_candidates import C06SurfacingInput


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
        provenance=f"tests.c06.runtime_topology:{signal_id}",
        target_claim=None,
    )


def _grounded_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="rt-c06-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="rt-c06-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="rt-c06-g3",
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


def _project_signal(case_id: str) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=f"{case_id}:project",
        signal_kind="directive",
        authority_source_kind=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
        target_summary="stabilize bounded runtime response path",
        grounded_basis_present=True,
        provenance=f"tests.c06.runtime_topology:{case_id}:project",
    )


def _candidate(
    *,
    act_id: str,
    act_type: V01ActType,
    evidence_strength: float,
    authority_basis_present: bool = True,
) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=act_type,
        proposition_ref="prop:c06-runtime-topology",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        commitment_target_ref="target:c06" if act_type is V01ActType.PROMISE else None,
        provenance=f"tests.c06.runtime_topology:{act_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_signals(),
        o03_candidate_strategy=_transparent_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def test_runtime_topology_graph_includes_c06_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "C06" in graph.runtime_order
    assert graph.runtime_order.index("V03") < graph.runtime_order.index("C06")
    assert graph.runtime_order.index("C06") < graph.runtime_order.index("RT01")
    assert "rt01.c06_surfacing_candidates_checkpoint" in graph.mandatory_checkpoint_ids
    assert "c06_surfacing_candidates.surfaced_candidate_set" in graph.source_of_truth_surfaces
    assert any(
        edge.source_phase == "V03" and edge.target_phase == "C06" for edge in graph.edges
    )


def test_dispatch_c06_require_paths_are_enforced() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-c06-require"),
            context=replace(
                _base_context("runtime-topology-c06-require"),
                require_c06_candidate_set_consumer=True,
                require_c06_suppression_report_consumer=True,
                require_c06_identity_merge_consumer=True,
                v01_act_candidates=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.c06_surfacing_candidates_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_c06_candidate_set_consumer" in checkpoint.required_action
    assert "require_c06_suppression_report_consumer" in checkpoint.required_action
    assert "require_c06_identity_merge_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_c06_default_ambiguity_detour_is_strict_and_basis_gated() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-c06-default"),
            context=replace(
                _base_context("runtime-topology-c06-default"),
                v01_act_candidates=(
                    _candidate(
                        act_id="assertion-c06-topology-1",
                        act_type=V01ActType.ASSERTION,
                        evidence_strength=0.97,
                    ),
                ),
                c06_surfacing_input=C06SurfacingInput(
                    input_id="c06-topology-ambiguity",
                    prior_unresolved_question_present=True,
                    unresolved_ambiguity_tokens=("ambiguity:1",),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.c06_surfacing_candidates_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "default_c06_candidate_ambiguity_detour" in checkpoint.required_action


def test_dispatch_c06_no_candidate_no_default_friction() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-c06-no-candidate"),
            context=replace(
                _base_context("runtime-topology-c06-no-candidate"),
                v01_act_candidates=(),
                c06_surfacing_input=None,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.c06_surfacing_candidates_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "c06_optional"
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE

