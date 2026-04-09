from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.contracts import (
    TransitionKind,
    TransitionRequest,
    WriterIdentity,
)
from substrate.runtime_topology import (
    RuntimeDispatchRequest,
    RuntimeDispatchRestriction,
    RuntimeRouteBindingConsequence,
    RuntimeRouteClass,
    build_minimal_runtime_tick_graph,
    build_minimal_runtime_topology_bundle,
    derive_runtime_dispatch_contract_view,
    dispatch_runtime_tick,
    require_dispatch_bounded_n_scope,
    require_dispatch_strong_narrative_commitment,
    require_lawful_production_dispatch,
    runtime_dispatch_snapshot,
)
from substrate.state import create_empty_state
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    build_subject_tick_runtime_domain_update,
    build_subject_tick_runtime_route_auth_context,
    execute_subject_tick,
)
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-runtime-topology-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-08T19:00:00+00:00",
            event_id="ev-runtime-topology-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _tick_input(case_id: str, *, unresolved: bool = False) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=14.0 if unresolved else 66.0,
        cognitive=95.0 if unresolved else 44.0,
        safety=34.0 if unresolved else 74.0,
        unresolved_preference=unresolved,
    )


def _persist_domain_update(runtime_state, seed_result, domain_update, transition_id: str):
    route_auth = build_subject_tick_runtime_route_auth_context(
        result=seed_result,
        domain_update=domain_update,
    )
    result = execute_transition(
        TransitionRequest(
            transition_id=transition_id,
            transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
            writer=WriterIdentity.TRANSITION_ENGINE,
            cause_chain=("runtime-topology-build", transition_id),
            requested_at="2026-04-08T19:01:00+00:00",
            event_id=f"ev-{transition_id}",
            event_payload={
                "turn_id": f"turn-{transition_id}",
                "runtime_domain_update": domain_update,
                "runtime_route_auth": route_auth,
            },
        ),
        runtime_state,
    )
    assert result.accepted is True
    return result.state


def test_runtime_topology_bundle_and_graph_are_materialized() -> None:
    bundle = build_minimal_runtime_topology_bundle()
    graph = build_minimal_runtime_tick_graph()
    assert bundle.execution_spine_phase == "RT01"
    assert bundle.runtime_entry == "runtime_topology.dispatch_runtime_tick"
    assert bundle.shared_domain_paths == (
        "domains.regulation",
        "domains.continuity",
        "domains.validity",
    )
    assert graph.runtime_order == ("R", "C01", "C02", "C03", "C04", "C05", "RT01")
    assert "rt01.downstream_obedience_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.world_seam_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.world_entry_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s_minimal_contour_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.a_line_normalization_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.m_minimal_contour_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.n_minimal_contour_checkpoint" in graph.mandatory_checkpoint_ids
    assert "world_adapter.state" in graph.source_of_truth_surfaces
    assert "world_entry_contract.episode" in graph.source_of_truth_surfaces
    assert "s_minimal_contour.boundary_state" in graph.source_of_truth_surfaces
    assert "a_line_normalization.capability_state" in graph.source_of_truth_surfaces
    assert "m_minimal.lifecycle_state" in graph.source_of_truth_surfaces
    assert "n_minimal.commitment_state" in graph.source_of_truth_surfaces


def test_dispatch_happy_path_runs_lawful_production_contour() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-happy"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.decision.accepted is True
    assert result.decision.lawful_production_route is True
    assert result.decision.route_binding_consequence == RuntimeRouteBindingConsequence.LAWFUL_PRODUCTION_CONTOUR
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.state.rt01_authority_role == "gating"
    assert result.bundle.execution_spine_phase == "RT01"


def test_dispatch_rejects_helper_route_without_explicit_allow() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-helper-denied"),
            route_class=RuntimeRouteClass.HELPER_PATH,
        )
    )
    assert result.decision.accepted is False
    assert result.subject_tick_result is None
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_REQUIRED in result.decision.restrictions


def test_dispatch_helper_route_can_run_only_as_non_production() -> None:
    denied_without_non_production_opt_in = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-helper-no-opt-in"),
            route_class=RuntimeRouteClass.HELPER_PATH,
            allow_helper_route=True,
        )
    )
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-helper-allowed"),
            route_class=RuntimeRouteClass.HELPER_PATH,
            allow_helper_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert denied_without_non_production_opt_in.decision.accepted is False
    assert (
        RuntimeDispatchRestriction.NON_PRODUCTION_ROUTE_REQUIRES_EXPLICIT_CONSUMER_OPT_IN
        in denied_without_non_production_opt_in.decision.restrictions
    )
    assert result.decision.accepted is True
    assert result.decision.lawful_production_route is False
    assert result.decision.route_binding_consequence == RuntimeRouteBindingConsequence.NON_LAWFUL_HELPER_ROUTE
    assert result.subject_tick_result is not None
    assert RuntimeDispatchRestriction.HELPER_ROUTE_NOT_LAWFUL_PRODUCTION in result.decision.restrictions
    with pytest.raises(PermissionError):
        require_lawful_production_dispatch(result)


def test_dispatch_rejects_production_route_with_test_ablation_flags() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-ablation-denied", unresolved=True),
            context=SubjectTickContext(disable_downstream_obedience_enforcement=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.decision.accepted is False
    assert RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS in result.decision.restrictions


def test_dispatch_test_only_route_requires_explicit_allow_and_ablation_basis() -> None:
    denied_no_allow = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-test-no-allow", unresolved=True),
            context=SubjectTickContext(disable_downstream_obedience_enforcement=True),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
        )
    )
    denied_no_ablation = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-test-no-ablation"),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
        )
    )
    denied_no_opt_in = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-test-no-opt-in", unresolved=True),
            context=SubjectTickContext(disable_downstream_obedience_enforcement=True),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
        )
    )
    allowed = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-test-allowed", unresolved=True),
            context=SubjectTickContext(disable_downstream_obedience_enforcement=True),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert denied_no_allow.decision.accepted is False
    assert RuntimeDispatchRestriction.TEST_ONLY_ROUTE_REQUIRES_EXPLICIT_ALLOW in denied_no_allow.decision.restrictions
    assert denied_no_ablation.decision.accepted is False
    assert RuntimeDispatchRestriction.TEST_ONLY_ROUTE_REQUIRES_ABLATION_BASIS in denied_no_ablation.decision.restrictions
    assert denied_no_opt_in.decision.accepted is False
    assert (
        RuntimeDispatchRestriction.NON_PRODUCTION_ROUTE_REQUIRES_EXPLICIT_CONSUMER_OPT_IN
        in denied_no_opt_in.decision.restrictions
    )
    assert allowed.decision.accepted is True
    assert allowed.decision.lawful_production_route is False
    assert allowed.decision.route_binding_consequence == RuntimeRouteBindingConsequence.TEST_ONLY_ABLATION_ROUTE


def test_dispatch_persistence_requires_f01_transition_inputs() -> None:
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-persist-denied"),
            persist_via_f01=True,
        )
    )
    assert denied.decision.accepted is False
    assert RuntimeDispatchRestriction.PERSISTENCE_REQUIRES_F01_INPUTS in denied.decision.restrictions


def test_dispatch_non_production_route_forbids_f01_persistence() -> None:
    denied = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-helper-no-persist"),
            route_class=RuntimeRouteClass.HELPER_PATH,
            allow_helper_route=True,
            allow_non_production_consumer_opt_in=True,
            persist_via_f01=True,
            runtime_state=_bootstrapped_state(),
            transition_id="tr-runtime-topology-helper-persist",
            requested_at="2026-04-08T19:02:30+00:00",
            cause_chain=("runtime-topology-dispatch", "helper-persist"),
        )
    )
    assert denied.decision.accepted is False
    assert (
        RuntimeDispatchRestriction.NON_PRODUCTION_ROUTE_FORBIDS_F01_PERSISTENCE
        in denied.decision.restrictions
    )


def test_dispatch_persistence_materializes_domains_via_f01() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-persist-ok", unresolved=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            persist_via_f01=True,
            runtime_state=_bootstrapped_state(),
            transition_id="tr-runtime-topology-persist",
            requested_at="2026-04-08T19:02:00+00:00",
            cause_chain=("runtime-topology-dispatch", "persist"),
        )
    )
    assert result.decision.accepted is True
    assert result.persist_transition is not None
    assert result.persist_transition.accepted is True
    assert result.persist_transition.state.domains.regulation.updated_by_phase == "R04"
    assert result.persist_transition.state.domains.continuity.updated_by_phase == "C04"
    assert result.persist_transition.state.domains.validity.updated_by_phase == "C05"


def test_dispatch_keeps_c05_shared_domain_binding_load_bearing() -> None:
    seed = execute_subject_tick(_tick_input("runtime-topology-c05-seed"))
    update = build_subject_tick_runtime_domain_update(seed)
    update = replace(
        update,
        validity=replace(
            update.validity,
            legality_reuse_allowed=False,
            revalidation_required=False,
            no_safe_reuse=False,
            selective_scope_targets=(),
        ),
    )
    prior_state = _persist_domain_update(
        _bootstrapped_state(),
        seed,
        update,
        "tr-runtime-topology-c05-shared",
    )
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-c05-follow"),
            context=SubjectTickContext(prior_runtime_state=prior_state),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.decision.accepted is True
    assert result.subject_tick_result is not None
    assert result.subject_tick_result.state.downstream_obedience_status == "must_revalidate"
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_preserves_rt01_behavior_for_same_input() -> None:
    context = SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",))
    direct = execute_subject_tick(_tick_input("runtime-topology-direct", unresolved=True), context=context)
    dispatched = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-direct", unresolved=True),
            context=context,
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert dispatched.subject_tick_result is not None
    assert dispatched.subject_tick_result.state.final_execution_outcome == direct.state.final_execution_outcome
    assert dispatched.subject_tick_result.state.c04_execution_mode_claim == direct.state.c04_execution_mode_claim
    assert dispatched.subject_tick_result.state.c05_execution_action_claim == direct.state.c05_execution_action_claim


def test_dispatch_route_matrix_and_runtime_outcome_matrix() -> None:
    route_results = (
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=_tick_input("runtime-topology-route-production"),
                route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            )
        ),
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=_tick_input("runtime-topology-route-helper"),
                route_class=RuntimeRouteClass.HELPER_PATH,
                allow_helper_route=True,
                allow_non_production_consumer_opt_in=True,
            )
        ),
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=_tick_input("runtime-topology-route-test", unresolved=True),
                context=SubjectTickContext(disable_downstream_obedience_enforcement=True),
                route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
                allow_test_only_route=True,
                allow_non_production_consumer_opt_in=True,
            )
        ),
    )
    assert {item.decision.route_class for item in route_results} == {
        RuntimeRouteClass.PRODUCTION_CONTOUR,
        RuntimeRouteClass.HELPER_PATH,
        RuntimeRouteClass.TEST_ONLY_ABLATION,
    }
    assert route_results[0].decision.lawful_production_route is True
    assert route_results[1].decision.lawful_production_route is False
    assert route_results[2].decision.lawful_production_route is False
    assert {
        item.decision.route_binding_consequence
        for item in route_results
    } == {
        RuntimeRouteBindingConsequence.LAWFUL_PRODUCTION_CONTOUR,
        RuntimeRouteBindingConsequence.NON_LAWFUL_HELPER_ROUTE,
        RuntimeRouteBindingConsequence.TEST_ONLY_ABLATION_ROUTE,
    }

    continue_case = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-outcome-continue"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    repair_case = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-outcome-repair", unresolved=True),
            context=SubjectTickContext(allow_endogenous_tick=False, external_turn_present=False),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    revalidate_case = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-outcome-revalidate", unresolved=True),
            context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    halt_case = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-outcome-halt", unresolved=True),
            context=SubjectTickContext(
                withdrawn_source_refs=(
                    "c01.stream_kernel_from_r01_r02_r03_r04",
                    "c02.tension_scheduler_from_c01_r01_r02_r03_r04",
                    "c03.stream_diversification_from_c01_c02_r04",
                    "c04.mode_arbitration_from_c01_c02_c03_r04",
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    outcomes = {
        continue_case.subject_tick_result.state.final_execution_outcome,
        repair_case.subject_tick_result.state.final_execution_outcome,
        revalidate_case.subject_tick_result.state.final_execution_outcome,
        halt_case.subject_tick_result.state.final_execution_outcome,
    }
    assert outcomes == {
        SubjectTickOutcome.CONTINUE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.HALT,
    }


def test_dispatch_contract_view_and_snapshot_are_inspectable() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-contract-view"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    snapshot = runtime_dispatch_snapshot(result)
    assert view.contour_id == "rt01_subject_tick_contour"
    assert view.execution_spine_phase == "RT01"
    assert view.accepted is True
    assert view.production_consumer_ready is True
    assert view.route_binding_consequence == "lawful_production_contour"
    assert "rt01.downstream_obedience_checkpoint" in view.mandatory_checkpoints
    assert view.world_entry_episode_id is not None
    assert view.world_entry_w01_admission_ready is False
    assert view.world_entry_scope == "rt01_contour_only"
    assert view.world_entry_scope_admission_layer_only is True
    assert view.world_entry_scope_w01_implemented is False
    assert view.world_entry_scope_w_line_implemented is False
    assert view.world_entry_scope_repo_wide_adoption is False
    assert view.s_boundary_state_id is not None
    assert view.s_scope == "rt01_contour_only"
    assert view.s_scope_rt01_contour_only is True
    assert view.s_scope_s_minimal_only is True
    assert view.s_scope_s01_implemented is False
    assert view.s_scope_s_line_implemented is False
    assert view.s_scope_minimal_contour_only is True
    assert view.s_scope_s01_s05_implemented is False
    assert view.s_scope_full_self_model_implemented is False
    assert view.s_scope_repo_wide_adoption is False
    assert isinstance(view.s_readiness_blockers, tuple)
    assert view.a_capability_id is not None
    assert view.a_scope == "rt01_contour_only"
    assert view.a_scope_rt01_contour_only is True
    assert view.a_scope_a_line_normalization_only is True
    assert view.a_scope_readiness_gate_only is True
    assert view.a_scope_a04_implemented is False
    assert view.a_scope_a05_touched is False
    assert view.a_scope_full_agency_stack_implemented is False
    assert view.a_scope_repo_wide_adoption is False
    assert view.m_memory_item_id is not None
    assert view.m_scope == "rt01_contour_only"
    assert view.m_scope_rt01_contour_only is True
    assert view.m_scope_m_minimal_only is True
    assert view.m_scope_readiness_gate_only is True
    assert view.m_scope_m01_implemented is False
    assert view.m_scope_m02_implemented is False
    assert view.m_scope_m03_implemented is False
    assert view.m_scope_full_memory_stack_implemented is False
    assert view.m_scope_repo_wide_adoption is False
    assert view.n_narrative_commitment_id is not None
    assert view.n_scope == "rt01_contour_only"
    assert view.n_scope_rt01_contour_only is True
    assert view.n_scope_n_minimal_only is True
    assert view.n_scope_readiness_gate_only is True
    assert view.n_scope_n01_implemented is False
    assert view.n_scope_n02_implemented is False
    assert view.n_scope_n03_implemented is False
    assert view.n_scope_n04_implemented is False
    assert view.n_scope_full_narrative_line_implemented is False
    assert view.n_scope_repo_wide_adoption is False
    assert isinstance(view.n_n01_blockers, tuple)
    assert require_dispatch_bounded_n_scope(view) is view
    assert isinstance(view.m_m01_blockers, tuple)
    assert view.m_m01_structurally_present_but_not_ready in {True, False}
    assert view.m_m01_stale_risk_unacceptable in {True, False}
    assert view.m_m01_conflict_risk_unacceptable in {True, False}
    assert view.m_m01_reactivation_requires_review in {True, False}
    assert view.m_m01_temporary_carry_not_stable_enough in {True, False}
    assert view.m_m01_no_safe_memory_basis in {True, False}
    assert view.m_m01_provenance_insufficient in {True, False}
    assert view.m_m01_lifecycle_underconstrained in {True, False}
    assert view.a_a04_structurally_present_but_not_ready in {True, False}
    assert view.a_a04_capability_basis_missing in {True, False}
    assert view.a_a04_world_dependency_unmet in {True, False}
    assert view.a_a04_self_dependency_unmet in {True, False}
    assert view.a_a04_policy_legitimacy_unmet in {True, False}
    assert view.a_a04_underconstrained_capability_surface in {True, False}
    assert view.a_a04_external_means_not_justified in {True, False}
    assert isinstance(view.a_a04_blockers, tuple)
    assert snapshot["decision"]["route_class"] == "production_contour"
    assert snapshot["decision"]["production_consumer_ready"] is True
    assert snapshot["decision"]["route_binding_consequence"] == "lawful_production_contour"
    assert "world_link_status" in snapshot["subject_tick_state"]
    assert "world_grounded_transition_allowed" in snapshot["subject_tick_state"]
    assert "world_entry_episode_id" in snapshot["subject_tick_state"]
    assert snapshot["subject_tick_state"]["world_entry_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["world_entry_scope_admission_layer_only"] is True
    assert snapshot["subject_tick_state"]["world_entry_scope_w01_implemented"] is False
    assert snapshot["subject_tick_state"]["world_entry_scope_w_line_implemented"] is False
    assert snapshot["subject_tick_state"]["world_entry_scope_repo_wide_adoption"] is False
    assert snapshot["subject_tick_state"]["s_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["s_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["s_scope_s_minimal_only"] is True
    assert snapshot["subject_tick_state"]["s_scope_s01_implemented"] is False
    assert snapshot["subject_tick_state"]["s_scope_s_line_implemented"] is False
    assert snapshot["subject_tick_state"]["s_scope_minimal_contour_only"] is True
    assert snapshot["subject_tick_state"]["s_scope_s01_s05_implemented"] is False
    assert snapshot["subject_tick_state"]["s_scope_full_self_model_implemented"] is False
    assert snapshot["subject_tick_state"]["s_scope_repo_wide_adoption"] is False
    assert isinstance(snapshot["subject_tick_state"]["s_readiness_blockers"], tuple)
    assert snapshot["subject_tick_state"]["a_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["a_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["a_scope_a_line_normalization_only"] is True
    assert snapshot["subject_tick_state"]["a_scope_readiness_gate_only"] is True
    assert snapshot["subject_tick_state"]["a_scope_a04_implemented"] is False
    assert snapshot["subject_tick_state"]["a_scope_a05_touched"] is False
    assert snapshot["subject_tick_state"]["a_scope_full_agency_stack_implemented"] is False
    assert snapshot["subject_tick_state"]["a_scope_repo_wide_adoption"] is False
    assert snapshot["subject_tick_state"]["a_a04_structurally_present_but_not_ready"] in {True, False}
    assert snapshot["subject_tick_state"]["a_a04_capability_basis_missing"] in {True, False}
    assert snapshot["subject_tick_state"]["a_a04_world_dependency_unmet"] in {True, False}
    assert snapshot["subject_tick_state"]["a_a04_self_dependency_unmet"] in {True, False}
    assert snapshot["subject_tick_state"]["a_a04_policy_legitimacy_unmet"] in {True, False}
    assert snapshot["subject_tick_state"]["a_a04_underconstrained_capability_surface"] in {True, False}
    assert snapshot["subject_tick_state"]["a_a04_external_means_not_justified"] in {True, False}
    assert isinstance(snapshot["subject_tick_state"]["a_a04_blockers"], tuple)
    assert snapshot["subject_tick_state"]["m_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["m_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["m_scope_m_minimal_only"] is True
    assert snapshot["subject_tick_state"]["m_scope_readiness_gate_only"] is True
    assert snapshot["subject_tick_state"]["m_scope_m01_implemented"] is False
    assert snapshot["subject_tick_state"]["m_scope_m02_implemented"] is False
    assert snapshot["subject_tick_state"]["m_scope_m03_implemented"] is False
    assert snapshot["subject_tick_state"]["m_scope_full_memory_stack_implemented"] is False
    assert snapshot["subject_tick_state"]["m_scope_repo_wide_adoption"] is False
    assert snapshot["subject_tick_state"]["n_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["n_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["n_scope_n_minimal_only"] is True
    assert snapshot["subject_tick_state"]["n_scope_readiness_gate_only"] is True
    assert snapshot["subject_tick_state"]["n_scope_n01_implemented"] is False
    assert snapshot["subject_tick_state"]["n_scope_n02_implemented"] is False
    assert snapshot["subject_tick_state"]["n_scope_n03_implemented"] is False
    assert snapshot["subject_tick_state"]["n_scope_n04_implemented"] is False
    assert snapshot["subject_tick_state"]["n_scope_full_narrative_line_implemented"] is False
    assert snapshot["subject_tick_state"]["n_scope_repo_wide_adoption"] is False
    assert isinstance(snapshot["subject_tick_state"]["n_n01_blockers"], tuple)
    assert isinstance(snapshot["subject_tick_state"]["m_m01_blockers"], tuple)
    assert snapshot["subject_tick_state"]["m_m01_structurally_present_but_not_ready"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_stale_risk_unacceptable"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_conflict_risk_unacceptable"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_reactivation_requires_review"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_temporary_carry_not_stable_enough"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_no_safe_memory_basis"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_provenance_insufficient"] in {True, False}
    assert snapshot["subject_tick_state"]["m_m01_lifecycle_underconstrained"] in {True, False}
    assert snapshot["bundle"]["runtime_entry"] == "runtime_topology.dispatch_runtime_tick"


def test_runtime_dispatch_n_scope_validator_blocks_tampered_scope_and_unsafe_strong_claim() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-n-scope-validator"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    assert require_dispatch_bounded_n_scope(view) is view
    with pytest.raises(PermissionError):
        require_dispatch_strong_narrative_commitment(view)

    tampered = replace(view, n_scope_repo_wide_adoption=True)
    with pytest.raises(PermissionError):
        require_dispatch_bounded_n_scope(tampered)


def test_direct_subject_tick_result_cannot_be_used_as_lawful_dispatch_contract() -> None:
    direct = execute_subject_tick(_tick_input("runtime-topology-direct-bypass"))
    with pytest.raises(TypeError):
        require_lawful_production_dispatch(direct)  # type: ignore[arg-type]


def test_matched_input_route_class_change_changes_binding_contract_surface() -> None:
    production = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-route-contrast"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    helper = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-route-contrast"),
            route_class=RuntimeRouteClass.HELPER_PATH,
            allow_helper_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert production.subject_tick_result is not None
    assert helper.subject_tick_result is not None
    assert (
        production.subject_tick_result.state.final_execution_outcome
        == helper.subject_tick_result.state.final_execution_outcome
    )
    production_view = derive_runtime_dispatch_contract_view(production)
    helper_view = derive_runtime_dispatch_contract_view(helper)
    assert production_view.route_binding_consequence != helper_view.route_binding_consequence
    assert production_view.production_consumer_ready is True
    assert helper_view.production_consumer_ready is False
