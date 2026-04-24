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
        provenance=f"tests.v01.runtime_topology:{signal_id}",
        target_claim=None,
    )


def _grounded_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="rt-v01-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="rt-v01-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="rt-v01-g3",
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
        provenance=f"tests.v01.runtime_topology:{case_id}:project",
    )


def _candidate(
    *,
    act_id: str,
    act_type: V01ActType,
    evidence_strength: float,
    authority_basis_present: bool = True,
    explicit_uncertainty_present: bool = False,
    commitment_target_ref: str | None = None,
) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=act_type,
        proposition_ref="prop:v01-runtime-topology",
        evidence_strength=evidence_strength,
        authority_basis_present=authority_basis_present,
        explicit_uncertainty_present=explicit_uncertainty_present,
        commitment_target_ref=commitment_target_ref,
        provenance=f"tests.v01.runtime_topology:{act_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o01_entity_signals=_grounded_signals(),
        o03_candidate_strategy=_transparent_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def test_runtime_topology_graph_includes_v01_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "V01" in graph.runtime_order
    assert graph.runtime_order.index("R05") < graph.runtime_order.index("V01")
    assert graph.runtime_order.index("V01") < graph.runtime_order.index("RT01")
    assert "rt01.v01_normative_permission_commitment_licensing_checkpoint" in graph.mandatory_checkpoint_ids
    assert (
        "v01_normative_permission_commitment_licensing.communicative_license_state"
        in graph.source_of_truth_surfaces
    )


def test_dispatch_v01_require_paths_are_enforced() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-v01-require"),
            context=replace(
                _base_context("runtime-topology-v01-require"),
                require_v01_license_consumer=True,
                require_v01_commitment_delta_consumer=True,
                require_v01_qualifier_binding_consumer=True,
                v01_act_candidates=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v01_normative_permission_commitment_licensing_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_v01_license_consumer" in checkpoint.required_action
    assert "require_v01_commitment_delta_consumer" in checkpoint.required_action
    assert "require_v01_qualifier_binding_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_v01_default_commitment_denied_detour_is_strict() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-v01-baseline"),
            context=replace(
                _base_context("runtime-topology-v01-baseline"),
                v01_act_candidates=(
                    _candidate(
                        act_id="assertion-baseline",
                        act_type=V01ActType.ASSERTION,
                        evidence_strength=0.97,
                        authority_basis_present=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    denied_commitment = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-v01-commitment-denied"),
            context=replace(
                _base_context("runtime-topology-v01-commitment-denied"),
                v01_act_candidates=(
                    _candidate(
                        act_id="assertion-for-split",
                        act_type=V01ActType.ASSERTION,
                        evidence_strength=0.97,
                        authority_basis_present=True,
                    ),
                    _candidate(
                        act_id="promise-for-split",
                        act_type=V01ActType.PROMISE,
                        evidence_strength=0.62,
                        authority_basis_present=True,
                        commitment_target_ref="target:runtime",
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert denied_commitment.subject_tick_result is not None
    baseline_checkpoint = next(
        item
        for item in baseline.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v01_normative_permission_commitment_licensing_checkpoint"
    )
    denied_checkpoint = next(
        item
        for item in denied_commitment.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v01_normative_permission_commitment_licensing_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert denied_checkpoint.status.value == "enforced_detour"
    assert "default_v01_commitment_denied_detour" in denied_checkpoint.required_action
    assert denied_commitment.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_dispatch_v01_no_candidate_no_default_friction() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-v01-no-candidate"),
            context=replace(
                _base_context("runtime-topology-v01-no-candidate"),
                v01_act_candidates=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.v01_normative_permission_commitment_licensing_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "v01_optional"
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
