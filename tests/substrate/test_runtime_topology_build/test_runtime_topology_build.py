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
from substrate.s05_multi_cause_attribution_factorization import (
    S05CauseClass,
    S05DownstreamRouteClass,
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
from substrate.world_adapter import WorldAdapterInput, build_world_observation_packet
from substrate.world_adapter import build_world_action_candidate, build_world_effect_packet
from tests.substrate.s01_efference_copy_testkit import build_s01


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


def _force_s05_shape(
    result,
    *,
    route_class: S05DownstreamRouteClass,
    dominant: tuple[S05CauseClass, ...],
    residual: float,
    factorization_ready: bool,
    learning_ready: bool,
    no_binary_recollapse_required: bool,
):
    latest = result.state.packets[-1]
    latest = replace(
        latest,
        downstream_route_class=route_class,
        unexplained_residual=residual,
    )
    state = replace(
        result.state,
        packets=(*result.state.packets[:-1], latest),
        dominant_cause_classes=dominant,
        unexplained_residual=residual,
    )
    gate = replace(
        result.gate,
        factorization_consumer_ready=factorization_ready,
        learning_route_ready=learning_ready,
        no_binary_recollapse_required=no_binary_recollapse_required,
    )
    telemetry = replace(
        result.telemetry,
        downstream_route_class=route_class,
        dominant_slot_count=len(dominant),
        residual_share=residual,
        factorization_consumer_ready=factorization_ready,
        learning_route_ready=learning_ready,
    )
    return replace(
        result,
        state=state,
        gate=gate,
        telemetry=telemetry,
    )


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
    assert graph.runtime_order == (
        "EPISTEMICS",
        "R",
        "C01",
        "C02",
        "C03",
        "C04",
        "C05",
        "S01",
        "S02",
        "S03",
        "S04",
        "S05",
        "T01",
        "T02",
        "T03",
        "T04",
        "RT01",
    )
    assert "rt01.epistemic_admission_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.downstream_obedience_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.world_seam_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.world_entry_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s_minimal_contour_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.a_line_normalization_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.m_minimal_contour_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.n_minimal_contour_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s01_efference_copy_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s02_prediction_boundary_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s03_ownership_weighted_learning_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s04_interoceptive_self_binding_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.s05_multi_cause_attribution_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.t01_semantic_field_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.t02_relation_binding_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.t02_raw_vs_propagated_integrity_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.t03_hypothesis_competition_checkpoint" in graph.mandatory_checkpoint_ids
    assert "rt01.t04_attention_schema_checkpoint" in graph.mandatory_checkpoint_ids
    assert "epistemics.grounded_unit" in graph.source_of_truth_surfaces
    assert "epistemics.downstream_allowance" in graph.source_of_truth_surfaces
    assert "world_adapter.state" in graph.source_of_truth_surfaces
    assert "world_entry_contract.episode" in graph.source_of_truth_surfaces
    assert "s_minimal_contour.boundary_state" in graph.source_of_truth_surfaces
    assert "a_line_normalization.capability_state" in graph.source_of_truth_surfaces
    assert "m_minimal.lifecycle_state" in graph.source_of_truth_surfaces
    assert "n_minimal.commitment_state" in graph.source_of_truth_surfaces
    assert "s01_efference_copy.latest_comparison" in graph.source_of_truth_surfaces
    assert "s02_prediction_boundary.seam_ledger" in graph.source_of_truth_surfaces
    assert (
        "s02_prediction_boundary.controllability_vs_predictability"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s03_ownership_weighted_learning.learning_attribution_ledger"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s03_ownership_weighted_learning.target_update_routes"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s03_ownership_weighted_learning.freeze_or_defer_state"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s04_interoceptive_self_binding.binding_entries"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s04_interoceptive_self_binding.core_channels"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s05_multi_cause_attribution_factorization.factorization_packet"
        in graph.source_of_truth_surfaces
    )
    assert (
        "s05_multi_cause_attribution_factorization.compatibility_filtering"
        in graph.source_of_truth_surfaces
    )
    assert "t01_semantic_field.active_scene" in graph.source_of_truth_surfaces
    assert "t02_relation_binding.constrained_scene" in graph.source_of_truth_surfaces
    assert "t02_relation_binding.raw_vs_propagated_distinction" in graph.source_of_truth_surfaces
    assert "t03_hypothesis_competition.competition_ledger" in graph.source_of_truth_surfaces
    assert "t03_hypothesis_competition.publication_frontier" in graph.source_of_truth_surfaces
    assert "t04_attention_schema.focus_ownership" in graph.source_of_truth_surfaces
    assert "t04_attention_schema.focus_targets" in graph.source_of_truth_surfaces


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
    assert view.t01_scene_id is not None
    assert view.t01_scene_status is not None
    assert view.t01_stability_state is not None
    assert view.t01_preverbal_consumer_ready in {True, False}
    assert view.t01_scene_comparison_ready in {True, False}
    assert view.t01_no_clean_scene_commit in {True, False}
    assert view.t01_require_scene_comparison_consumer in {True, False}
    assert view.t02_constrained_scene_id is not None
    assert view.t02_scene_status is not None
    assert view.t02_preverbal_constraint_consumer_ready in {True, False}
    assert view.t02_no_clean_binding_commit in {True, False}
    assert view.t02_confirmed_bindings_count is not None
    assert view.t02_provisional_bindings_count is not None
    assert view.t02_blocked_bindings_count is not None
    assert view.t02_conflicted_bindings_count is not None
    assert view.t02_propagated_consequences_count is not None
    assert view.t02_blocked_or_conflicted_consequences_count is not None
    assert view.t02_scope == "rt01_contour_only"
    assert view.t02_scope_rt01_contour_only is True
    assert view.t02_scope_t02_first_slice_only is True
    assert view.t02_scope_t03_implemented is False
    assert view.t02_scope_t04_implemented is False
    assert view.t02_scope_o01_implemented is False
    assert view.t02_scope_full_silent_thought_line_implemented is False
    assert view.t02_scope_repo_wide_adoption is False
    assert view.t02_require_constrained_scene_consumer in {True, False}
    assert view.t02_require_raw_vs_propagated_distinction in {True, False}
    assert view.t02_raw_vs_propagated_distinct in {True, False}
    assert view.t03_competition_id is not None
    assert view.t03_convergence_status is not None
    assert view.t03_tied_competitor_count is not None
    assert view.t03_publication_competitive_neighborhood is not None
    assert view.t03_scope == "rt01_contour_only"
    assert view.t03_scope_rt01_contour_only is True
    assert view.t03_scope_t03_first_slice_only is True
    assert view.t03_scope_t04_implemented is False
    assert view.t03_scope_o01_implemented is False
    assert view.t03_scope_o02_implemented is False
    assert view.t03_scope_o03_implemented is False
    assert view.t03_scope_full_silent_thought_line_implemented is False
    assert view.t03_scope_repo_wide_adoption is False
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
    assert "t01_scene_id" in snapshot["subject_tick_state"]
    assert "t01_scene_status" in snapshot["subject_tick_state"]
    assert "t01_stability_state" in snapshot["subject_tick_state"]
    assert "t01_preverbal_consumer_ready" in snapshot["subject_tick_state"]
    assert "t01_scene_comparison_ready" in snapshot["subject_tick_state"]
    assert "t01_no_clean_scene_commit" in snapshot["subject_tick_state"]
    assert "t01_require_scene_comparison_consumer" in snapshot["subject_tick_state"]
    assert snapshot["subject_tick_state"]["t02_constrained_scene_id"] is not None
    assert snapshot["subject_tick_state"]["t02_scene_status"] is not None
    assert snapshot["subject_tick_state"]["t02_preverbal_constraint_consumer_ready"] in {True, False}
    assert snapshot["subject_tick_state"]["t02_no_clean_binding_commit"] in {True, False}
    assert snapshot["subject_tick_state"]["t02_confirmed_bindings_count"] is not None
    assert snapshot["subject_tick_state"]["t02_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["t02_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["t02_scope_t02_first_slice_only"] is True
    assert snapshot["subject_tick_state"]["t02_scope_t03_implemented"] is False
    assert snapshot["subject_tick_state"]["t02_scope_t04_implemented"] is False
    assert snapshot["subject_tick_state"]["t02_scope_o01_implemented"] is False
    assert (
        snapshot["subject_tick_state"]["t02_scope_full_silent_thought_line_implemented"]
        is False
    )
    assert snapshot["subject_tick_state"]["t02_scope_repo_wide_adoption"] is False
    assert snapshot["subject_tick_state"]["t02_require_constrained_scene_consumer"] in {True, False}
    assert (
        snapshot["subject_tick_state"]["t02_require_raw_vs_propagated_distinction"]
        in {True, False}
    )
    assert snapshot["subject_tick_state"]["t02_raw_vs_propagated_distinct"] in {True, False}
    assert snapshot["subject_tick_state"]["t03_competition_id"] is not None
    assert snapshot["subject_tick_state"]["t03_convergence_status"] is not None
    assert snapshot["subject_tick_state"]["t03_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["t03_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["t03_scope_t03_first_slice_only"] is True
    assert snapshot["subject_tick_state"]["t03_scope_t04_implemented"] is False
    assert snapshot["subject_tick_state"]["t03_scope_o01_implemented"] is False
    assert snapshot["subject_tick_state"]["t03_scope_o02_implemented"] is False
    assert snapshot["subject_tick_state"]["t03_scope_o03_implemented"] is False
    assert (
        snapshot["subject_tick_state"]["t03_scope_full_silent_thought_line_implemented"]
        is False
    )
    assert snapshot["subject_tick_state"]["t03_scope_repo_wide_adoption"] is False
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


def test_dispatch_t01_scene_comparison_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t01-comparison"),
            context=SubjectTickContext(
                emit_world_action_candidate=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t01-comparison"),
            context=SubjectTickContext(
                emit_world_action_candidate=True,
                require_t01_scene_comparison_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.t01_scene_comparison_ready is False
    assert required.subject_tick_result.state.t01_scene_comparison_ready is False
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.t01_semantic_field_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t02_constrained_scene_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t02-consumer"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t02-consumer"),
            context=SubjectTickContext(require_t02_constrained_scene_consumer=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.t02_relation_binding_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t02_raw_vs_propagated_integrity_requirement_is_load_bearing() -> None:
    enriched_context = SubjectTickContext(
        require_t02_raw_vs_propagated_distinction=True,
        emit_world_action_candidate=True,
        world_adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=build_world_observation_packet(
                observation_id="obs-runtime-topology-t02-raw-propagated",
                source_ref="world.sensor.runtime_topology_test",
                observed_at="2026-04-18T10:05:00+00:00",
                payload_ref="payload:runtime-topology-t02-raw-propagated",
            ),
        ),
    )
    required_distinct = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t02-raw-propagated"),
            context=enriched_context,
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    flattened = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t02-raw-propagated"),
            context=replace(
                enriched_context,
                t02_assembly_mode="raw_vs_propagated_flatten_ablation",
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert required_distinct.subject_tick_result is not None
    assert flattened.subject_tick_result is not None
    assert (
        required_distinct.subject_tick_result.state.final_execution_outcome
        == SubjectTickOutcome.CONTINUE
    )
    assert flattened.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.t02_raw_vs_propagated_integrity_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in flattened.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t03_convergence_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t03-consumer"),
            context=SubjectTickContext(
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=False,
                    adapter_available=False,
                )
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t03-consumer"),
            context=SubjectTickContext(
                require_t03_convergence_consumer=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=False,
                    adapter_available=False,
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.t03_hypothesis_competition_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t03_frontier_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t03-frontier"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t03-frontier"),
            context=SubjectTickContext(
                require_t03_frontier_consumer=True,
                t03_competition_mode="greedy_argmax_ablation",
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.t03_hypothesis_competition_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t03_nonconvergence_preservation_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t03-nonconv"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t03-nonconv"),
            context=SubjectTickContext(
                require_t03_nonconvergence_preservation=True,
                t03_competition_mode="greedy_argmax_ablation",
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.t03_hypothesis_competition_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t04_focus_ownership_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t04-focus"),
            context=SubjectTickContext(
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=False,
                    adapter_available=False,
                )
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t04-focus"),
            context=SubjectTickContext(
                require_t04_focus_ownership_consumer=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=False,
                    adapter_available=False,
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.t04_attention_schema_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_t04_peripheral_preservation_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t04-peripheral"),
            context=SubjectTickContext(
                t03_competition_mode="forced_single_winner_ablation",
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t04-peripheral"),
            context=SubjectTickContext(
                require_t04_peripheral_preservation=True,
                t03_competition_mode="forced_single_winner_ablation",
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.t04_attention_schema_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.t04_attention_schema_checkpoint"
    )
    assert baseline_checkpoint.status.value != "enforced_detour"
    assert required_checkpoint.status.value == "enforced_detour"
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_contract_view_exposes_t04_attention_schema_surface() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-t04-contract-view"),
            context=SubjectTickContext(
                require_t04_focus_ownership_consumer=True,
                require_t04_reportable_focus_consumer=True,
                require_t04_peripheral_preservation=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    snapshot = runtime_dispatch_snapshot(result)
    assert view.t04_schema_id is not None
    assert view.t04_focus_targets_count is not None
    assert view.t04_attention_owner is not None
    assert view.t04_focus_mode is not None
    assert view.t04_scope == "rt01_contour_only"
    assert view.t04_scope_rt01_contour_only is True
    assert view.t04_scope_t04_first_slice_only is True
    assert view.t04_scope_o01_implemented is False
    assert view.t04_scope_o02_implemented is False
    assert view.t04_scope_o03_implemented is False
    assert view.t04_scope_full_attention_line_implemented is False
    assert view.t04_scope_repo_wide_adoption is False
    assert view.t04_require_focus_ownership_consumer is True
    assert view.t04_require_reportable_focus_consumer is True
    assert view.t04_require_peripheral_preservation is True
    assert snapshot["subject_tick_state"]["t04_schema_id"] is not None
    assert snapshot["subject_tick_state"]["t04_scope"] == "rt01_contour_only"
    assert snapshot["subject_tick_state"]["t04_scope_rt01_contour_only"] is True
    assert snapshot["subject_tick_state"]["t04_scope_t04_first_slice_only"] is True
    assert snapshot["subject_tick_state"]["t04_scope_o01_implemented"] is False
    assert snapshot["subject_tick_state"]["t04_scope_o02_implemented"] is False
    assert snapshot["subject_tick_state"]["t04_scope_o03_implemented"] is False
    assert (
        snapshot["subject_tick_state"]["t04_scope_full_attention_line_implemented"]
        is False
    )
    assert snapshot["subject_tick_state"]["t04_scope_repo_wide_adoption"] is False


def test_dispatch_s01_comparison_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-comparison"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-comparison"),
            context=SubjectTickContext(require_s01_comparison_consumer=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.s01_efference_copy_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s01_unexpected_change_consumer_requirement_is_load_bearing() -> None:
    baseline_action = build_world_action_candidate(
        tick_id="runtime-topology-s01-unexpected-baseline",
        execution_mode="continue_stream",
    )
    required_action = build_world_action_candidate(
        tick_id="runtime-topology-s01-unexpected-required",
        execution_mode="continue_stream",
    )
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-unexpected"),
            context=SubjectTickContext(
                disable_s01_prediction_registration=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=build_world_observation_packet(
                        observation_id="obs-runtime-topology-s01-unexpected",
                        source_ref="world.sensor.runtime_topology_s01",
                        observed_at="2026-04-20T10:10:00+00:00",
                        payload_ref="payload:runtime-topology-s01-unexpected",
                    ),
                    action_packet=baseline_action,
                    effect_packet=build_world_effect_packet(
                        effect_id="eff-runtime-topology-s01-unexpected",
                        action_id=baseline_action.action_id,
                        observed_at="2026-04-20T10:10:00+00:00",
                        source_ref="world.sensor.runtime_topology_s01",
                        success=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-unexpected"),
            context=SubjectTickContext(
                disable_s01_prediction_registration=True,
                require_s01_unexpected_change_consumer=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=build_world_observation_packet(
                        observation_id="obs-runtime-topology-s01-unexpected-required",
                        source_ref="world.sensor.runtime_topology_s01",
                        observed_at="2026-04-20T10:10:01+00:00",
                        payload_ref="payload:runtime-topology-s01-unexpected-required",
                    ),
                    action_packet=required_action,
                    effect_packet=build_world_effect_packet(
                        effect_id="eff-runtime-topology-s01-unexpected-required",
                        action_id=required_action.action_id,
                        observed_at="2026-04-20T10:10:01+00:00",
                        source_ref="world.sensor.runtime_topology_s01",
                        success=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.TEST_ONLY_ABLATION,
            allow_test_only_route=True,
            allow_non_production_consumer_opt_in=True,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.s01_result.state.unexpected_change_detected is True
    assert required.subject_tick_result.s01_result.state.unexpected_change_detected is True
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_dispatch_s01_unexpected_change_consumer_requirement_is_load_bearing_without_ablation_registration_toggle() -> None:
    prior = build_s01(
        case_id="runtime-topology-s01-unexpected-prod-like-prior",
        tick_index=1,
        register_prediction=False,
        world_effect_feedback_correlated=False,
    )
    baseline_action = build_world_action_candidate(
        tick_id="runtime-topology-s01-unexpected-prod-like-baseline",
        execution_mode="continue_stream",
    )
    required_action = build_world_action_candidate(
        tick_id="runtime-topology-s01-unexpected-prod-like-required",
        execution_mode="continue_stream",
    )
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-unexpected-prod-like"),
            context=SubjectTickContext(
                prior_s01_state=prior.state,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=build_world_observation_packet(
                        observation_id="obs-runtime-topology-s01-unexpected-prod-like-baseline",
                        source_ref="world.sensor.runtime_topology_s01",
                        observed_at="2026-04-20T10:10:10+00:00",
                        payload_ref="payload:runtime-topology-s01-unexpected-prod-like-baseline",
                    ),
                    action_packet=baseline_action,
                    effect_packet=build_world_effect_packet(
                        effect_id="eff-runtime-topology-s01-unexpected-prod-like-baseline",
                        action_id=baseline_action.action_id,
                        observed_at="2026-04-20T10:10:10+00:00",
                        source_ref="world.sensor.runtime_topology_s01",
                        success=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-unexpected-prod-like"),
            context=SubjectTickContext(
                prior_s01_state=prior.state,
                require_s01_unexpected_change_consumer=True,
                world_adapter_input=WorldAdapterInput(
                    adapter_presence=True,
                    adapter_available=True,
                    observation_packet=build_world_observation_packet(
                        observation_id="obs-runtime-topology-s01-unexpected-prod-like-required",
                        source_ref="world.sensor.runtime_topology_s01",
                        observed_at="2026-04-20T10:10:11+00:00",
                        payload_ref="payload:runtime-topology-s01-unexpected-prod-like-required",
                    ),
                    action_packet=required_action,
                    effect_packet=build_world_effect_packet(
                        effect_id="eff-runtime-topology-s01-unexpected-prod-like-required",
                        action_id=required_action.action_id,
                        observed_at="2026-04-20T10:10:11+00:00",
                        source_ref="world.sensor.runtime_topology_s01",
                        success=True,
                    ),
                ),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.s01_result.state.unexpected_change_detected is True
    assert required.subject_tick_result.s01_result.state.unexpected_change_detected is True
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.s01_efference_copy_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s01_prediction_validity_consumer_requirement_is_load_bearing() -> None:
    seed = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-validity-seed"),
            context=SubjectTickContext(emit_world_action_candidate=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert seed.subject_tick_result is not None
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-validity-follow"),
            context=SubjectTickContext(
                prior_s01_state=seed.subject_tick_result.s01_result.state,
                dependency_trigger_hits=("trigger:mode_shift",),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-validity-follow"),
            context=SubjectTickContext(
                prior_s01_state=seed.subject_tick_result.s01_result.state,
                dependency_trigger_hits=("trigger:mode_shift",),
                require_s01_prediction_validity_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.s01_result.gate.prediction_validity_ready is False
    assert required.subject_tick_result.s01_result.gate.prediction_validity_ready is False
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_dispatch_contract_view_exposes_s01_efference_surface() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s01-contract-view"),
            context=SubjectTickContext(require_s01_prediction_validity_consumer=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    assert result.subject_tick_result is not None
    state = result.subject_tick_result.state
    assert view.s01_latest_comparison_status == state.s01_latest_comparison_status
    assert view.s01_comparison_ready in {True, False}
    assert view.s01_unexpected_change_detected in {True, False}
    assert view.s01_prediction_validity_ready in {True, False}
    assert view.s01_comparison_blocked_by_contamination in {True, False}
    assert view.s01_stale_prediction_detected in {True, False}
    assert view.s01_pending_predictions_count == state.s01_pending_predictions_count
    assert view.s01_comparisons_count == state.s01_comparisons_count
    assert view.s01_require_prediction_validity_consumer is True


def test_dispatch_s02_boundary_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-boundary"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-boundary"),
            context=SubjectTickContext(require_s02_boundary_consumer=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.s02_prediction_boundary_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s02_controllability_consumer_requirement_is_load_bearing() -> None:
    seed = build_s01(
        case_id="runtime-topology-s02-controllability-seed",
        tick_index=1,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-controllability"),
            context=SubjectTickContext(
                prior_s01_state=seed.state,
                emit_world_action_candidate=False,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-controllability"),
            context=SubjectTickContext(
                prior_s01_state=seed.state,
                emit_world_action_candidate=False,
                require_s02_controllability_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.s02_prediction_boundary_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s02_mixed_source_consumer_requirement_is_load_bearing() -> None:
    seed = build_s01(
        case_id="runtime-topology-s02-mixed-seed",
        tick_index=1,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-mixed"),
            context=SubjectTickContext(
                prior_s01_state=seed.state,
                emit_world_action_candidate=False,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-mixed"),
            context=SubjectTickContext(
                prior_s01_state=seed.state,
                emit_world_action_candidate=False,
                require_s02_mixed_source_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.s02_prediction_boundary_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s02_mixed_source_consumer_positive_path_is_load_bearing_without_detour() -> None:
    def _adapter(case_id: str) -> WorldAdapterInput:
        action = build_world_action_candidate(
            tick_id=f"{case_id}-action",
            execution_mode="continue_stream",
        )
        effect = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=action.action_id,
            observed_at="2026-04-20T10:30:00+00:00",
            source_ref="world.sensor.runtime_topology_s02_mixed_positive",
            success=True,
        )
        return WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=build_world_observation_packet(
                observation_id=f"obs-{case_id}",
                source_ref="world.sensor.runtime_topology_s02_mixed_positive",
                observed_at="2026-04-20T10:30:00+00:00",
                payload_ref=f"payload:{case_id}",
            ),
            action_packet=action,
            effect_packet=effect,
        )

    bootstrap = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-mixed-positive-bootstrap"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert bootstrap.subject_tick_result is not None
    controllable_seed = build_s01(
        case_id="runtime-topology-s02-mixed-positive-controllable-seed",
        tick_index=1,
        c04_selected_mode="continue_stream",
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
    )
    external_seed = build_s01(
        case_id="runtime-topology-s02-mixed-positive-external-seed",
        tick_index=1,
        c04_selected_mode="idle",
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    internal = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-mixed-positive-internal"),
            context=SubjectTickContext(
                prior_subject_tick_state=bootstrap.subject_tick_result.state,
                prior_s01_state=controllable_seed.state,
                emit_world_action_candidate=True,
                world_adapter_input=_adapter("runtime-topology-s02-mixed-positive-internal"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert internal.subject_tick_result is not None
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-mixed-positive-baseline"),
            context=SubjectTickContext(
                prior_subject_tick_state=internal.subject_tick_result.state,
                prior_s01_state=external_seed.state,
                prior_s02_state=internal.subject_tick_result.s02_result.state,
                emit_world_action_candidate=True,
                world_adapter_input=_adapter("runtime-topology-s02-mixed-positive-baseline"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-mixed-positive-required"),
            context=SubjectTickContext(
                prior_subject_tick_state=internal.subject_tick_result.state,
                prior_s01_state=external_seed.state,
                prior_s02_state=internal.subject_tick_result.s02_result.state,
                emit_world_action_candidate=True,
                require_s02_mixed_source_consumer=True,
                world_adapter_input=_adapter("runtime-topology-s02-mixed-positive-required"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s02_prediction_boundary_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s02_prediction_boundary_checkpoint"
    )
    assert (
        required.subject_tick_result.s02_result.state.active_boundary_status.value
        == "mixed_source_boundary"
    )
    assert required.subject_tick_result.s02_result.gate.mixed_source_consumer_ready is True
    assert baseline_checkpoint.status.value == "allowed"
    assert required_checkpoint.status.value == "allowed"
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_dispatch_contract_view_exposes_s02_prediction_boundary_surface() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s02-contract-view"),
            context=SubjectTickContext(
                require_s02_boundary_consumer=True,
                require_s02_controllability_consumer=True,
                require_s02_mixed_source_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    assert view.s02_boundary_id is not None
    assert view.s02_active_boundary_status is not None
    assert view.s02_scope == "rt01_contour_only"
    assert view.s02_scope_rt01_contour_only is True
    assert view.s02_scope_s02_first_slice_only is True
    assert view.s02_scope_s03_implemented is False
    assert view.s02_scope_s04_implemented is False
    assert view.s02_scope_s05_implemented is False
    assert view.s02_scope_full_self_model_implemented is False
    assert view.s02_scope_repo_wide_adoption is False
    assert view.s02_require_boundary_consumer is True
    assert view.s02_require_controllability_consumer is True
    assert view.s02_require_mixed_source_consumer is True


def test_dispatch_s03_learning_packet_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-learning-baseline"),
            context=SubjectTickContext(context_shift_markers=("shift:s03-local",)),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-learning-required"),
            context=SubjectTickContext(
                context_shift_markers=("shift:s03-local",),
                require_s03_learning_packet_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s03_mixed_update_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-mixed-baseline"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-mixed-required"),
            context=SubjectTickContext(require_s03_mixed_update_consumer=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s03_freeze_obedience_consumer_requirement_is_load_bearing() -> None:
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-freeze-baseline"),
            context=SubjectTickContext(context_shift_markers=("shift:s03-freeze",)),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-freeze-required"),
            context=SubjectTickContext(
                context_shift_markers=("shift:s03-freeze",),
                require_s03_freeze_obedience_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
    )


def test_dispatch_s03_positive_consumer_ready_path_has_no_detour() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-positive"),
            context=SubjectTickContext(require_s03_learning_packet_consumer=True),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert result.subject_tick_result is not None
    checkpoint = next(
        checkpoint
        for checkpoint in result.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
    )
    assert result.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert checkpoint.status.value == "allowed"


def test_dispatch_s03_mixed_update_consumer_positive_path_is_load_bearing_without_detour() -> None:
    def _adapter(case_id: str) -> WorldAdapterInput:
        action = build_world_action_candidate(
            tick_id=f"{case_id}-action",
            execution_mode="continue_stream",
        )
        effect = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=action.action_id,
            observed_at="2026-04-21T09:10:00+00:00",
            source_ref="world.sensor.runtime_topology_s03_mixed_positive",
            success=True,
        )
        return WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=build_world_observation_packet(
                observation_id=f"obs-{case_id}",
                source_ref="world.sensor.runtime_topology_s03_mixed_positive",
                observed_at="2026-04-21T09:10:00+00:00",
                payload_ref=f"payload:{case_id}",
            ),
            action_packet=action,
            effect_packet=effect,
        )

    bootstrap = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-mixed-positive-bootstrap"),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert bootstrap.subject_tick_result is not None
    controllable_seed = build_s01(
        case_id="runtime-topology-s03-mixed-positive-controllable-seed",
        tick_index=1,
        c04_selected_mode="continue_stream",
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
    )
    external_seed = build_s01(
        case_id="runtime-topology-s03-mixed-positive-external-seed",
        tick_index=1,
        c04_selected_mode="idle",
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    internal = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-mixed-positive-internal"),
            context=SubjectTickContext(
                prior_subject_tick_state=bootstrap.subject_tick_result.state,
                prior_s01_state=controllable_seed.state,
                emit_world_action_candidate=True,
                world_adapter_input=_adapter("runtime-topology-s03-mixed-positive-internal"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert internal.subject_tick_result is not None
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-mixed-positive-baseline"),
            context=SubjectTickContext(
                prior_subject_tick_state=internal.subject_tick_result.state,
                prior_s01_state=external_seed.state,
                prior_s02_state=internal.subject_tick_result.s02_result.state,
                emit_world_action_candidate=True,
                world_adapter_input=_adapter("runtime-topology-s03-mixed-positive-baseline"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-mixed-positive-required"),
            context=SubjectTickContext(
                prior_subject_tick_state=internal.subject_tick_result.state,
                prior_s01_state=external_seed.state,
                prior_s02_state=internal.subject_tick_result.s02_result.state,
                emit_world_action_candidate=True,
                require_s03_mixed_update_consumer=True,
                world_adapter_input=_adapter("runtime-topology-s03-mixed-positive-required"),
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
    )
    assert required.subject_tick_result.state.s03_latest_update_class == "mixed_split_update"
    assert required.subject_tick_result.state.s03_mixed_update_consumer_ready is True
    assert baseline_checkpoint.status.value == "allowed"
    assert required_checkpoint.status.value == "allowed"
    assert baseline.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.subject_tick_result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_dispatch_contract_view_exposes_s03_ownership_weighted_learning_surface() -> None:
    result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s03-contract-view"),
            context=SubjectTickContext(
                require_s03_learning_packet_consumer=True,
                require_s03_mixed_update_consumer=True,
                require_s03_freeze_obedience_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    view = derive_runtime_dispatch_contract_view(result)
    assert view.s03_learning_id is not None
    assert view.s03_latest_packet_id is not None
    assert view.s03_latest_update_class is not None
    assert view.s03_latest_commit_class is not None
    assert view.s03_learning_packet_consumer_ready in {True, False}
    assert view.s03_mixed_update_consumer_ready in {True, False}
    assert view.s03_freeze_obedience_consumer_ready in {True, False}
    assert view.s03_scope == "rt01_contour_only"
    assert view.s03_scope_rt01_contour_only is True
    assert view.s03_scope_s03_first_slice_only is True
    assert view.s03_scope_s04_implemented is False
    assert view.s03_scope_s05_implemented is False
    assert view.s03_scope_repo_wide_adoption is False
    assert view.s03_require_learning_packet_consumer is True
    assert view.s03_require_mixed_update_consumer is True
    assert view.s03_require_freeze_obedience_consumer is True


def test_dispatch_s05_factorized_consumer_requirement_is_load_bearing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import substrate.subject_tick.update as subject_tick_update

    original = subject_tick_update.build_s05_multi_cause_attribution_factorization

    def _patched_builder(*, tick_id: str, **kwargs):
        result = original(tick_id=tick_id, **kwargs)
        if "runtime-topology-s05-factorized-required" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
                dominant=(S05CauseClass.UNEXPLAINED_RESIDUAL,),
                residual=0.64,
                factorization_ready=False,
                learning_ready=False,
                no_binary_recollapse_required=True,
            )
        if "runtime-topology-s05-factorized-baseline" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.WORLD_HEAVY,
                dominant=(S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,),
                residual=0.34,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=False,
            )
        return result

    monkeypatch.setattr(
        subject_tick_update,
        "build_s05_multi_cause_attribution_factorization",
        _patched_builder,
    )
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s05-factorized-baseline"),
            context=SubjectTickContext(),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s05-factorized-required"),
            context=SubjectTickContext(
                context_shift_markers=("shift:s05",),
                dependency_trigger_hits=("trigger:mode_shift",),
                require_s05_factorized_consumer=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert required.subject_tick_result.s05_result.gate.factorization_consumer_ready is False
    assert required_checkpoint.status.value == "enforced_detour"
    assert required.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }


def test_dispatch_s05_low_residual_learning_route_requirement_is_load_bearing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import substrate.subject_tick.update as subject_tick_update

    original = subject_tick_update.build_s05_multi_cause_attribution_factorization

    def _patched_builder(*, tick_id: str, **kwargs):
        result = original(tick_id=tick_id, **kwargs)
        if "runtime-topology-s05-learning-required" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
                dominant=(S05CauseClass.UNEXPLAINED_RESIDUAL,),
                residual=0.63,
                factorization_ready=True,
                learning_ready=False,
                no_binary_recollapse_required=True,
            )
        if "runtime-topology-s05-learning-baseline" in tick_id:
            return _force_s05_shape(
                result,
                route_class=S05DownstreamRouteClass.WORLD_HEAVY,
                dominant=(S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,),
                residual=0.34,
                factorization_ready=True,
                learning_ready=True,
                no_binary_recollapse_required=False,
            )
        return result

    monkeypatch.setattr(
        subject_tick_update,
        "build_s05_multi_cause_attribution_factorization",
        _patched_builder,
    )
    baseline = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s05-learning-baseline", unresolved=False),
            context=SubjectTickContext(),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    required = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=_tick_input("runtime-topology-s05-learning-required", unresolved=False),
            context=SubjectTickContext(
                require_s05_low_residual_learning_route=True,
            ),
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
        )
    )
    assert baseline.subject_tick_result is not None
    assert required.subject_tick_result is not None
    baseline_checkpoint = next(
        checkpoint
        for checkpoint in baseline.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    required_checkpoint = next(
        checkpoint
        for checkpoint in required.subject_tick_result.state.execution_checkpoints
        if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
    )
    assert baseline_checkpoint.status.value == "allowed"
    assert required.subject_tick_result.s05_result.gate.learning_route_ready is False
    assert required_checkpoint.status.value == "enforced_detour"
    assert required.subject_tick_result.state.final_execution_outcome in {
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.HALT,
    }
