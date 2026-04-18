from __future__ import annotations

from dataclasses import replace

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.p01_project_formation import P01AuthoritySourceKind, P01ProjectSignalInput
from substrate.r05_appraisal_sovereign_protective_regulation import R05ProtectiveTriggerInput
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
        provenance=f"tests.r05.runtime_topology:{signal_id}",
        target_claim=None,
    )


def _grounded_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="rt-r05-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="rt-r05-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="rt-r05-g3",
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
        provenance=f"tests.r05.runtime_topology:{case_id}:project",
    )


def _r05_trigger(
    *,
    trigger_id: str,
    threat_structure_score: float,
    o04_coercive_structure_present: bool = False,
    load_pressure_score: float = 0.0,
    project_continuation_requested: bool = True,
    p01_project_continuation_active: bool = True,
    release_signal_present: bool = False,
    counterevidence_present: bool = False,
) -> R05ProtectiveTriggerInput:
    return R05ProtectiveTriggerInput(
        trigger_id=trigger_id,
        threat_structure_score=threat_structure_score,
        o04_coercive_structure_present=o04_coercive_structure_present,
        load_pressure_score=load_pressure_score,
        project_continuation_requested=project_continuation_requested,
        p01_project_continuation_active=p01_project_continuation_active,
        release_signal_present=release_signal_present,
        counterevidence_present=counterevidence_present,
        provenance=f"tests.r05.runtime_topology:{trigger_id}",
    )


def _base_context(case_id: str) -> SubjectTickContext:
    return SubjectTickContext(
        o04_interaction_events=(),
        o01_entity_signals=_grounded_signals(),
        o03_candidate_strategy=_transparent_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
    )


def test_runtime_topology_graph_includes_r05_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "R05" in graph.runtime_order
    assert graph.runtime_order.index("O04") < graph.runtime_order.index("R05")
    assert graph.runtime_order.index("R05") < graph.runtime_order.index("RT01")
    assert "rt01.r05_protective_regulation_checkpoint" in graph.mandatory_checkpoint_ids
    assert (
        "r05_appraisal_sovereign_protective_regulation.protective_state"
        in graph.source_of_truth_surfaces
    )


def test_dispatch_r05_explicit_require_path_detour_is_load_bearing() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-r05-required"),
            context=replace(
                _base_context("runtime-topology-r05-required"),
                require_r05_protective_state_consumer=True,
                require_r05_surface_inhibition_consumer=True,
                require_r05_release_contract_consumer=True,
                r05_protective_triggers=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_r05_protective_state_consumer" in checkpoint.required_action
    assert "require_r05_surface_inhibition_consumer" in checkpoint.required_action
    assert "require_r05_release_contract_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_r05_default_protective_override_detour_is_strict() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-r05-default-baseline"),
            context=replace(
                _base_context("runtime-topology-r05-default-baseline"),
                r05_protective_triggers=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    risky = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-r05-default-risky"),
            context=replace(
                _base_context("runtime-topology-r05-default-risky"),
                r05_protective_triggers=(
                    _r05_trigger(
                        trigger_id="runtime-default-risky-1",
                        threat_structure_score=0.8,
                        o04_coercive_structure_present=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert risky.subject_tick_result is not None
    baseline_checkpoint = next(
        item
        for item in baseline.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    risky_checkpoint = next(
        item
        for item in risky.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "enforced_detour"
    assert "default_r05_protective_override_detour" in risky_checkpoint.required_action
    assert risky.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_dispatch_r05_no_trigger_no_default_friction() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-r05-no-trigger"),
            context=replace(
                _base_context("runtime-topology-r05-no-trigger"),
                r05_protective_triggers=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert checkpoint.status.value == "allowed"
    assert "default_r05_protective_override_detour" not in checkpoint.required_action
    assert "default_r05_surface_throttle_detour" not in checkpoint.required_action
    assert "default_r05_release_recheck_detour" not in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_dispatch_r05_release_recheck_detour_is_strict() -> None:
    seed = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-r05-release-seed"),
            context=replace(
                _base_context("runtime-topology-r05-release-seed"),
                require_r05_protective_state_consumer=True,
                r05_protective_triggers=(
                    _r05_trigger(
                        trigger_id="runtime-release-seed-1",
                        threat_structure_score=0.8,
                        o04_coercive_structure_present=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert seed.subject_tick_result is not None
    released = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-r05-release-follow-up"),
            context=replace(
                _base_context("runtime-topology-r05-release-follow-up"),
                prior_r05_state=seed.subject_tick_result.r05_result.state,
                r05_protective_triggers=(
                    _r05_trigger(
                        trigger_id="runtime-release-follow-up-1",
                        threat_structure_score=0.5,
                        p01_project_continuation_active=False,
                        release_signal_present=True,
                        counterevidence_present=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert released.subject_tick_result is not None
    checkpoint = next(
        item
        for item in released.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
    )
    assert released.subject_tick_result.r05_result.state.protective_mode.value == "recovery_in_progress"
    assert checkpoint.status.value == "enforced_detour"
    assert "default_r05_release_recheck_detour" in checkpoint.required_action
    assert released.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
