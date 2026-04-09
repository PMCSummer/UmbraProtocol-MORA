from __future__ import annotations

from dataclasses import dataclass

from substrate.runtime_topology.models import RuntimeDispatchResult


@dataclass(frozen=True, slots=True)
class RuntimeDispatchContractView:
    accepted: bool
    lawful_production_route: bool
    route_binding_consequence: str
    route_class: str
    production_consumer_ready: bool
    contour_id: str
    execution_spine_phase: str
    source_of_truth_surfaces: tuple[str, ...]
    mandatory_checkpoints: tuple[str, ...]
    restrictions: tuple[str, ...]
    final_execution_outcome: str | None
    downstream_obedience_status: str | None
    world_link_status: str | None
    world_grounded_transition_allowed: bool | None
    world_effect_feedback_correlated: bool | None
    world_entry_episode_id: str | None
    world_entry_w01_admission_ready: bool | None
    world_entry_forbidden_claim_classes: tuple[str, ...] | None
    world_entry_scope: str | None
    world_entry_scope_admission_layer_only: bool | None
    world_entry_scope_w01_implemented: bool | None
    world_entry_scope_w_line_implemented: bool | None
    world_entry_scope_repo_wide_adoption: bool | None
    s_boundary_state_id: str | None
    s_attribution_class: str | None
    s_underconstrained: bool | None
    s_no_safe_self_claim: bool | None
    s_no_safe_world_claim: bool | None
    s_forbidden_shortcuts: tuple[str, ...] | None
    s_s01_admission_ready: bool | None
    s_readiness_blockers: tuple[str, ...] | None
    s_scope: str | None
    s_scope_rt01_contour_only: bool | None
    s_scope_s_minimal_only: bool | None
    s_scope_s01_implemented: bool | None
    s_scope_s_line_implemented: bool | None
    s_scope_minimal_contour_only: bool | None
    s_scope_s01_s05_implemented: bool | None
    s_scope_full_self_model_implemented: bool | None
    s_scope_repo_wide_adoption: bool | None
    a_capability_id: str | None
    a_capability_status: str | None
    a_underconstrained: bool | None
    a_no_safe_capability_claim: bool | None
    a_policy_conditioned_capability_present: bool | None
    a_forbidden_shortcuts: tuple[str, ...] | None
    a_a04_admission_ready: bool | None
    a_a04_blockers: tuple[str, ...] | None
    a_a04_structurally_present_but_not_ready: bool | None
    a_a04_capability_basis_missing: bool | None
    a_a04_world_dependency_unmet: bool | None
    a_a04_self_dependency_unmet: bool | None
    a_a04_policy_legitimacy_unmet: bool | None
    a_a04_underconstrained_capability_surface: bool | None
    a_a04_external_means_not_justified: bool | None
    a_scope: str | None
    a_scope_rt01_contour_only: bool | None
    a_scope_a_line_normalization_only: bool | None
    a_scope_readiness_gate_only: bool | None
    a_scope_a04_implemented: bool | None
    a_scope_a05_touched: bool | None
    a_scope_full_agency_stack_implemented: bool | None
    a_scope_repo_wide_adoption: bool | None
    reason: str


def derive_runtime_dispatch_contract_view(
    result: RuntimeDispatchResult,
) -> RuntimeDispatchContractView:
    if not isinstance(result, RuntimeDispatchResult):
        raise TypeError("derive_runtime_dispatch_contract_view requires RuntimeDispatchResult")
    state = None if result.subject_tick_result is None else result.subject_tick_result.state
    return RuntimeDispatchContractView(
        accepted=result.decision.accepted,
        lawful_production_route=result.decision.lawful_production_route,
        route_binding_consequence=result.decision.route_binding_consequence.value,
        route_class=result.decision.route_class.value,
        production_consumer_ready=(
            result.decision.accepted and result.decision.lawful_production_route
        ),
        contour_id=result.bundle.contour_id,
        execution_spine_phase=result.bundle.execution_spine_phase,
        source_of_truth_surfaces=result.tick_graph.source_of_truth_surfaces,
        mandatory_checkpoints=result.tick_graph.mandatory_checkpoint_ids,
        restrictions=tuple(item.value for item in result.decision.restrictions),
        final_execution_outcome=(
            None if state is None else state.final_execution_outcome.value
        ),
        downstream_obedience_status=(
            None if state is None else state.downstream_obedience_status
        ),
        world_link_status=(None if state is None else state.world_link_status),
        world_grounded_transition_allowed=(
            None if state is None else state.world_grounded_transition_allowed
        ),
        world_effect_feedback_correlated=(
            None if state is None else state.world_effect_feedback_correlated
        ),
        world_entry_episode_id=(None if state is None else state.world_entry_episode_id),
        world_entry_w01_admission_ready=(
            None if state is None else state.world_entry_w01_admission_ready
        ),
        world_entry_forbidden_claim_classes=(
            None if state is None else state.world_entry_forbidden_claim_classes
        ),
        world_entry_scope=(None if state is None else state.world_entry_scope),
        world_entry_scope_admission_layer_only=(
            None if state is None else state.world_entry_scope_admission_layer_only
        ),
        world_entry_scope_w01_implemented=(
            None if state is None else state.world_entry_scope_w01_implemented
        ),
        world_entry_scope_w_line_implemented=(
            None if state is None else state.world_entry_scope_w_line_implemented
        ),
        world_entry_scope_repo_wide_adoption=(
            None if state is None else state.world_entry_scope_repo_wide_adoption
        ),
        s_boundary_state_id=(None if state is None else state.s_boundary_state_id),
        s_attribution_class=(None if state is None else state.s_attribution_class),
        s_underconstrained=(None if state is None else state.s_underconstrained),
        s_no_safe_self_claim=(None if state is None else state.s_no_safe_self_claim),
        s_no_safe_world_claim=(None if state is None else state.s_no_safe_world_claim),
        s_forbidden_shortcuts=(None if state is None else state.s_forbidden_shortcuts),
        s_s01_admission_ready=(None if state is None else state.s_s01_admission_ready),
        s_readiness_blockers=(None if state is None else state.s_readiness_blockers),
        s_scope=(None if state is None else state.s_scope),
        s_scope_rt01_contour_only=(
            None if state is None else state.s_scope_rt01_contour_only
        ),
        s_scope_s_minimal_only=(None if state is None else state.s_scope_s_minimal_only),
        s_scope_s01_implemented=(None if state is None else state.s_scope_s01_implemented),
        s_scope_s_line_implemented=(
            None if state is None else state.s_scope_s_line_implemented
        ),
        s_scope_minimal_contour_only=(
            None if state is None else state.s_scope_minimal_contour_only
        ),
        s_scope_s01_s05_implemented=(
            None if state is None else state.s_scope_s01_s05_implemented
        ),
        s_scope_full_self_model_implemented=(
            None if state is None else state.s_scope_full_self_model_implemented
        ),
        s_scope_repo_wide_adoption=(
            None if state is None else state.s_scope_repo_wide_adoption
        ),
        a_capability_id=(None if state is None else state.a_capability_id),
        a_capability_status=(None if state is None else state.a_capability_status),
        a_underconstrained=(None if state is None else state.a_underconstrained),
        a_no_safe_capability_claim=(
            None if state is None else state.a_no_safe_capability_claim
        ),
        a_policy_conditioned_capability_present=(
            None if state is None else state.a_policy_conditioned_capability_present
        ),
        a_forbidden_shortcuts=(None if state is None else state.a_forbidden_shortcuts),
        a_a04_admission_ready=(None if state is None else state.a_a04_admission_ready),
        a_a04_blockers=(None if state is None else state.a_a04_blockers),
        a_a04_structurally_present_but_not_ready=(
            None if state is None else state.a_a04_structurally_present_but_not_ready
        ),
        a_a04_capability_basis_missing=(
            None if state is None else state.a_a04_capability_basis_missing
        ),
        a_a04_world_dependency_unmet=(
            None if state is None else state.a_a04_world_dependency_unmet
        ),
        a_a04_self_dependency_unmet=(
            None if state is None else state.a_a04_self_dependency_unmet
        ),
        a_a04_policy_legitimacy_unmet=(
            None if state is None else state.a_a04_policy_legitimacy_unmet
        ),
        a_a04_underconstrained_capability_surface=(
            None if state is None else state.a_a04_underconstrained_capability_surface
        ),
        a_a04_external_means_not_justified=(
            None if state is None else state.a_a04_external_means_not_justified
        ),
        a_scope=(None if state is None else state.a_scope),
        a_scope_rt01_contour_only=(
            None if state is None else state.a_scope_rt01_contour_only
        ),
        a_scope_a_line_normalization_only=(
            None if state is None else state.a_scope_a_line_normalization_only
        ),
        a_scope_readiness_gate_only=(
            None if state is None else state.a_scope_readiness_gate_only
        ),
        a_scope_a04_implemented=(
            None if state is None else state.a_scope_a04_implemented
        ),
        a_scope_a05_touched=(None if state is None else state.a_scope_a05_touched),
        a_scope_full_agency_stack_implemented=(
            None if state is None else state.a_scope_full_agency_stack_implemented
        ),
        a_scope_repo_wide_adoption=(
            None if state is None else state.a_scope_repo_wide_adoption
        ),
        reason=result.decision.reason,
    )


def require_lawful_production_dispatch(result: RuntimeDispatchResult) -> None:
    view = derive_runtime_dispatch_contract_view(result)
    if not view.accepted:
        raise PermissionError("runtime dispatch rejected; contour path is not lawful")
    if not view.lawful_production_route:
        raise PermissionError("runtime dispatch path is not lawful production contour")
