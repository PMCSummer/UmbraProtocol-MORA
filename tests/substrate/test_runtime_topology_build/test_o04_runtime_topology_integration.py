from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
)
from substrate.o04_rupture_hostility_coercion import (
    O04InteractionEventInput,
    O04LegitimacyHintStatus,
)
from substrate.p01_project_formation import P01AuthoritySourceKind, P01ProjectSignalInput
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
        provenance=f"tests.o04.runtime_topology:{signal_id}",
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


def _project_signal(case_id: str) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=f"{case_id}:project",
        signal_kind="directive",
        authority_source_kind=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
        target_summary="stabilize bounded runtime response path",
        grounded_basis_present=True,
        provenance=f"tests.o04.runtime_topology:{case_id}:project",
    )


def _event(
    *,
    event_id: str,
    blocked_option_present: bool = False,
    threatened_loss_present: bool = False,
    dependency_surface_present: bool = False,
    sanction_power_present: bool = False,
    access_withdrawal_present: bool = False,
    speech_act_kind: str | None = None,
    legitimacy_hint_status: O04LegitimacyHintStatus = O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
) -> O04InteractionEventInput:
    return O04InteractionEventInput(
        event_id=event_id,
        actor_ref="agent_a",
        target_ref="agent_b",
        blocked_option_present=blocked_option_present,
        threatened_loss_present=threatened_loss_present,
        dependency_surface_present=dependency_surface_present,
        sanction_power_present=sanction_power_present,
        access_withdrawal_present=access_withdrawal_present,
        speech_act_kind=speech_act_kind,
        legitimacy_hint_status=legitimacy_hint_status,
        provenance=f"tests.o04.runtime_topology:{event_id}",
    )


def test_runtime_topology_graph_includes_o04_node_order_and_checkpoint() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "O04" in graph.runtime_order
    assert graph.runtime_order.index("P01") < graph.runtime_order.index("O04")
    assert graph.runtime_order.index("O04") < graph.runtime_order.index("RT01")
    assert "rt01.o04_rupture_hostility_coercion_checkpoint" in graph.mandatory_checkpoint_ids
    assert "o04_rupture_hostility_coercion.dynamic_model" in graph.source_of_truth_surfaces


def test_dispatch_o04_default_coercive_detour_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o04-default-baseline"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-o04-default-baseline"),
                p01_project_signals=(_project_signal("runtime-topology-o04-default-baseline"),),
                o04_interaction_events=(
                    _event(event_id="baseline-rude", speech_act_kind="harsh_statement"),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    risky = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o04-default-risky"),
            context=SubjectTickContext(
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-o04-default-risky"),
                p01_project_signals=(_project_signal("runtime-topology-o04-default-risky"),),
                o04_interaction_events=(
                    _event(
                        event_id="risky-coercive",
                        blocked_option_present=True,
                        threatened_loss_present=True,
                        dependency_surface_present=True,
                        sanction_power_present=True,
                        legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert risky.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    risky_checkpoint = next(
        checkpoint
        for checkpoint in risky.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "enforced_detour"
    assert "default_o04_coercive_structure_detour" in risky_checkpoint.required_action
    assert risky.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_dispatch_o04_explicit_require_paths_are_load_bearing() -> None:
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-o04-required"),
            context=SubjectTickContext(
                require_o04_dynamic_contract_consumer=True,
                require_o04_directionality_consumer=True,
                require_o04_protective_handoff_consumer=True,
                o01_entity_signals=_grounded_signals(),
                o03_candidate_strategy=_transparent_candidate("runtime-topology-o04-required"),
                p01_project_signals=(_project_signal("runtime-topology-o04-required"),),
                o04_interaction_events=(),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert required.subject_tick_result is not None
    checkpoint = next(
        item
        for item in required.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_o04_dynamic_contract_consumer" in checkpoint.required_action
    assert "require_o04_directionality_consumer" in checkpoint.required_action
    assert "require_o04_protective_handoff_consumer" in checkpoint.required_action
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
