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
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    dispatch_runtime_tick,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommunicativeActCandidate,
)
from tests.substrate.p02_intervention_episode_layer_licensed_action_trace_testkit import (
    p02_episode_input,
    p02_execution_event,
    p02_license_snapshot,
    p02_outcome_evidence,
)
from tests.substrate.p03_long_horizon_credit_assignment_intervention_learning_testkit import (
    p03_confounder_signal,
    p03_credit_assignment_input,
    p03_outcome_observation,
    p03_outcome_window,
)
from substrate.p03_long_horizon_credit_assignment_intervention_learning import (
    P03ConfounderKind,
    P03WindowEvidenceStatus,
)
from substrate.p04_interpersonal_counterfactual_policy_simulation import (
    P04BeliefStateMode,
    P04PolicyClass,
)
from tests.substrate.p04_interpersonal_counterfactual_policy_simulation_testkit import (
    p04_assumption,
    p04_candidate,
    p04_candidate_set,
    p04_simulation_input,
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
        provenance=f"tests.p03.runtime_topology:{signal_id}",
        target_claim=None,
    )


def _grounded_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="rt-p03-g1",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="rt-p03-g2",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="rt-p03-g3",
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
        provenance=f"tests.p03.runtime_topology:{case_id}:project",
    )


def _candidate(*, act_id: str) -> V01CommunicativeActCandidate:
    return V01CommunicativeActCandidate(
        act_id=act_id,
        act_type=V01ActType.ASSERTION,
        proposition_ref="prop:p03-runtime-topology",
        evidence_strength=0.97,
        authority_basis_present=True,
        commitment_target_ref=None,
        provenance=f"tests.p03.runtime_topology:{act_id}",
    )


def _episode_ref(case_id: str) -> str:
    return f"p02:subject-tick-{case_id}-1:episode:1"


def _verified_p02_episode_input(case_id: str, action_id: str):
    license_snapshot = p02_license_snapshot(
        action_id=action_id,
        source_license_ref=f"v01:licensed:{action_id}",
        license_scope_ref="assertion",
    )
    return p02_episode_input(
        input_id=f"p02:{case_id}",
        licensed_actions=(license_snapshot,),
        execution_events=(
            p02_execution_event(
                event_id=f"ev:{case_id}:1",
                action_ref=action_id,
                event_kind="executed",
                order_index=1,
                source_license_ref=license_snapshot.source_license_ref,
            ),
        ),
        outcome_evidence=(
            p02_outcome_evidence(
                evidence_id=f"e:{case_id}:verified",
                action_ref=action_id,
                evidence_kind="verified_success",
                verified=True,
            ),
        ),
    )


def _safe_p03_input(case_id: str):
    episode_ref = _episode_ref(case_id)
    return p03_credit_assignment_input(
        input_id=f"p03:{case_id}:safe",
        outcome_observations=(
            p03_outcome_observation(
                observation_id=f"obs:{case_id}:safe",
                episode_ref=episode_ref,
                horizon_class="delayed",
                target_dimension="primary",
                effect_polarity="improved",
                magnitude=0.8,
                verified=True,
            ),
        ),
        outcome_windows=(
            p03_outcome_window(
                window_id=f"win:{case_id}:safe",
                episode_ref=episode_ref,
                status=P03WindowEvidenceStatus.WITHIN_WINDOW,
            ),
        ),
    )


def _risky_p03_input(case_id: str):
    episode_ref = _episode_ref(case_id)
    return p03_credit_assignment_input(
        input_id=f"p03:{case_id}:risky",
        outcome_observations=(
            p03_outcome_observation(
                observation_id=f"obs:{case_id}:risky",
                episode_ref=episode_ref,
                horizon_class="delayed",
                target_dimension="primary",
                effect_polarity="improved",
                magnitude=0.8,
                verified=True,
            ),
        ),
        confounder_signals=(
            p03_confounder_signal(
                confounder_id=f"conf:{case_id}:parallel",
                episode_ref=episode_ref,
                kind=P03ConfounderKind.PARALLEL_INTERVENTION,
                strength=0.95,
            ),
        ),
        outcome_windows=(
            p03_outcome_window(
                window_id=f"win:{case_id}:risky",
                episode_ref=episode_ref,
                status=P03WindowEvidenceStatus.WITHIN_WINDOW,
            ),
        ),
    )


def _base_context(case_id: str) -> SubjectTickContext:
    action_id = f"act:{case_id}:p03"
    return SubjectTickContext(
        o01_entity_signals=_grounded_signals(),
        o03_candidate_strategy=_transparent_candidate(case_id),
        p01_project_signals=(_project_signal(case_id),),
        v01_act_candidates=(_candidate(act_id=action_id),),
        p02_episode_input=_verified_p02_episode_input(case_id, action_id),
        p03_credit_assignment_input=_safe_p03_input(case_id),
        p04_simulation_input=_stable_p04_input(case_id),
    )


def _stable_p04_input(case_id: str):
    return p04_simulation_input(
        input_id=f"p04:{case_id}:stable",
        candidate_set=p04_candidate_set(
            set_id=f"set:{case_id}:stable",
            candidates=(
                p04_candidate(
                    candidate_id=f"cand:{case_id}:stable",
                    policy_ref="policy.p03_isolation_stable",
                    policy_class=P04PolicyClass.COLLABORATIVE_CLARIFICATION,
                    action_class="dialogue",
                    sequencing_rule="clarify_before_boundary",
                    escalation_stance="calibrated",
                    de_escalation_stance="repair_first",
                    clarification_strategy="explicit",
                    boundary_posture="guarded",
                    boundary_timing="phased",
                    stopping_conditions=("verification",),
                    horizon_steps=2,
                ),
            ),
        ),
        assumptions=(
            p04_assumption(
                assumption_id=f"as:{case_id}:shared",
                mode=P04BeliefStateMode.SHARED_KNOWLEDGE,
                shared_knowledge_confidence=0.9,
            ),
        ),
        horizon_steps=3,
        use_p03_priors=True,
    )


def test_runtime_topology_graph_includes_p03_order_checkpoint_and_wiring() -> None:
    graph = build_minimal_runtime_tick_graph()
    assert "P03" in graph.runtime_order
    assert graph.runtime_order.index("P02") < graph.runtime_order.index("P03")
    assert graph.runtime_order.index("P03") < graph.runtime_order.index("RT01")
    assert "rt01.p03_credit_assignment_checkpoint" in graph.mandatory_checkpoint_ids
    assert (
        "p03_long_horizon_credit_assignment_intervention_learning.credit_record_set"
        in graph.source_of_truth_surfaces
    )
    assert any(
        edge.source_phase == "P02" and edge.target_phase == "P03" for edge in graph.edges
    )
    assert any(
        edge.source_phase == "P03" and edge.target_phase == "P04" for edge in graph.edges
    )
    assert any(
        edge.source_phase == "P04" and edge.target_phase == "RT01" for edge in graph.edges
    )


def test_dispatch_p03_require_paths_are_enforced() -> None:
    case_id = "runtime-topology-p03-require"
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=replace(
                _base_context(case_id),
                p03_credit_assignment_input=None,
                require_p03_credit_record_consumer=True,
                require_p03_no_update_consumer=True,
                require_p03_update_recommendation_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        item
        for item in result.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p03_credit_assignment_checkpoint"
    )
    assert checkpoint.status.value == "enforced_detour"
    assert "require_p03_credit_record_consumer" in checkpoint.required_action
    assert "require_p03_no_update_consumer" in checkpoint.required_action
    assert "require_p03_update_recommendation_consumer" in checkpoint.required_action
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_same_p03_checkpoint_envelope_can_diverge_by_typed_shape() -> None:
    safe_case = "runtime-topology-p03-envelope-safe"
    risky_case = "runtime-topology-p03-envelope-risky"
    safe = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(safe_case),
            context=replace(
                _base_context(safe_case),
                require_p03_credit_record_consumer=True,
                require_p03_update_recommendation_consumer=True,
                p03_credit_assignment_input=_safe_p03_input(safe_case),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    risky = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(risky_case),
            context=replace(
                _base_context(risky_case),
                require_p03_credit_record_consumer=True,
                require_p03_update_recommendation_consumer=True,
                p03_credit_assignment_input=_risky_p03_input(risky_case),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert safe.subject_tick_result is not None
    assert risky.subject_tick_result is not None
    safe_checkpoint = next(
        item
        for item in safe.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p03_credit_assignment_checkpoint"
    )
    risky_checkpoint = next(
        item
        for item in risky.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p03_credit_assignment_checkpoint"
    )
    assert safe_checkpoint.status.value == "allowed"
    assert risky_checkpoint.status.value == "allowed"
    assert (
        safe_checkpoint.required_action
        == "require_p03_credit_record_consumer;require_p03_update_recommendation_consumer"
    )
    assert safe_checkpoint.required_action == risky_checkpoint.required_action
    assert safe.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert risky.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert safe.subject_tick_result.downstream_gate.accepted is True
    assert risky.subject_tick_result.downstream_gate.accepted is False


def test_dispatch_disable_p03_enforcement_changes_downstream_behavior() -> None:
    case_id = "runtime-topology-p03-no-bypass"
    enabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(case_id),
            context=replace(
                _base_context(case_id),
                p03_credit_assignment_input=_risky_p03_input(case_id),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    disabled_case = f"{case_id}-disabled"
    disabled = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input(disabled_case),
            context=replace(
                _base_context(disabled_case),
                disable_p03_enforcement=True,
                p03_credit_assignment_input=_risky_p03_input(disabled_case),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert enabled.decision.accepted is True
    assert enabled.subject_tick_result is not None
    enabled_checkpoint = next(
        item
        for item in enabled.subject_tick_result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.p03_credit_assignment_checkpoint"
    )
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_p03_confounded_association_detour" in enabled_checkpoint.required_action
    assert disabled.decision.accepted is False
    assert disabled.subject_tick_result is None
    assert (
        RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS
        in disabled.decision.restrictions
    )
