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
    m_memory_item_id: str | None
    m_lifecycle_status: str | None
    m_retention_class: str | None
    m_review_required: bool | None
    m_stale_risk: str | None
    m_conflict_risk: str | None
    m_no_safe_memory_claim: bool | None
    m_forbidden_shortcuts: tuple[str, ...] | None
    m_m01_admission_ready: bool | None
    m_m01_blockers: tuple[str, ...] | None
    m_m01_structurally_present_but_not_ready: bool | None
    m_m01_stale_risk_unacceptable: bool | None
    m_m01_conflict_risk_unacceptable: bool | None
    m_m01_reactivation_requires_review: bool | None
    m_m01_temporary_carry_not_stable_enough: bool | None
    m_m01_no_safe_memory_basis: bool | None
    m_m01_provenance_insufficient: bool | None
    m_m01_lifecycle_underconstrained: bool | None
    m_scope: str | None
    m_scope_rt01_contour_only: bool | None
    m_scope_m_minimal_only: bool | None
    m_scope_readiness_gate_only: bool | None
    m_scope_m01_implemented: bool | None
    m_scope_m02_implemented: bool | None
    m_scope_m03_implemented: bool | None
    m_scope_full_memory_stack_implemented: bool | None
    m_scope_repo_wide_adoption: bool | None
    n_narrative_commitment_id: str | None
    n_commitment_status: str | None
    n_safe_narrative_commitment_allowed: bool | None
    n_bounded_commitment_allowed: bool | None
    n_ambiguity_residue: bool | None
    n_contradiction_risk: str | None
    n_no_safe_narrative_claim: bool | None
    n_forbidden_shortcuts: tuple[str, ...] | None
    n_n01_admission_ready: bool | None
    n_n01_blockers: tuple[str, ...] | None
    n_scope: str | None
    n_scope_rt01_contour_only: bool | None
    n_scope_n_minimal_only: bool | None
    n_scope_readiness_gate_only: bool | None
    n_scope_n01_implemented: bool | None
    n_scope_n02_implemented: bool | None
    n_scope_n03_implemented: bool | None
    n_scope_n04_implemented: bool | None
    n_scope_full_narrative_line_implemented: bool | None
    n_scope_repo_wide_adoption: bool | None
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
        m_memory_item_id=(None if state is None else state.m_memory_item_id),
        m_lifecycle_status=(None if state is None else state.m_lifecycle_status),
        m_retention_class=(None if state is None else state.m_retention_class),
        m_review_required=(None if state is None else state.m_review_required),
        m_stale_risk=(None if state is None else state.m_stale_risk),
        m_conflict_risk=(None if state is None else state.m_conflict_risk),
        m_no_safe_memory_claim=(None if state is None else state.m_no_safe_memory_claim),
        m_forbidden_shortcuts=(None if state is None else state.m_forbidden_shortcuts),
        m_m01_admission_ready=(None if state is None else state.m_m01_admission_ready),
        m_m01_blockers=(None if state is None else state.m_m01_blockers),
        m_m01_structurally_present_but_not_ready=(
            None if state is None else state.m_m01_structurally_present_but_not_ready
        ),
        m_m01_stale_risk_unacceptable=(
            None if state is None else state.m_m01_stale_risk_unacceptable
        ),
        m_m01_conflict_risk_unacceptable=(
            None if state is None else state.m_m01_conflict_risk_unacceptable
        ),
        m_m01_reactivation_requires_review=(
            None if state is None else state.m_m01_reactivation_requires_review
        ),
        m_m01_temporary_carry_not_stable_enough=(
            None if state is None else state.m_m01_temporary_carry_not_stable_enough
        ),
        m_m01_no_safe_memory_basis=(
            None if state is None else state.m_m01_no_safe_memory_basis
        ),
        m_m01_provenance_insufficient=(
            None if state is None else state.m_m01_provenance_insufficient
        ),
        m_m01_lifecycle_underconstrained=(
            None if state is None else state.m_m01_lifecycle_underconstrained
        ),
        m_scope=(None if state is None else state.m_scope),
        m_scope_rt01_contour_only=(
            None if state is None else state.m_scope_rt01_contour_only
        ),
        m_scope_m_minimal_only=(None if state is None else state.m_scope_m_minimal_only),
        m_scope_readiness_gate_only=(
            None if state is None else state.m_scope_readiness_gate_only
        ),
        m_scope_m01_implemented=(None if state is None else state.m_scope_m01_implemented),
        m_scope_m02_implemented=(None if state is None else state.m_scope_m02_implemented),
        m_scope_m03_implemented=(None if state is None else state.m_scope_m03_implemented),
        m_scope_full_memory_stack_implemented=(
            None if state is None else state.m_scope_full_memory_stack_implemented
        ),
        m_scope_repo_wide_adoption=(
            None if state is None else state.m_scope_repo_wide_adoption
        ),
        n_narrative_commitment_id=(
            None if state is None else state.n_narrative_commitment_id
        ),
        n_commitment_status=(None if state is None else state.n_commitment_status),
        n_safe_narrative_commitment_allowed=(
            None if state is None else state.n_safe_narrative_commitment_allowed
        ),
        n_bounded_commitment_allowed=(
            None if state is None else state.n_bounded_commitment_allowed
        ),
        n_ambiguity_residue=(None if state is None else state.n_ambiguity_residue),
        n_contradiction_risk=(None if state is None else state.n_contradiction_risk),
        n_no_safe_narrative_claim=(
            None if state is None else state.n_no_safe_narrative_claim
        ),
        n_forbidden_shortcuts=(None if state is None else state.n_forbidden_shortcuts),
        n_n01_admission_ready=(None if state is None else state.n_n01_admission_ready),
        n_n01_blockers=(None if state is None else state.n_n01_blockers),
        n_scope=(None if state is None else state.n_scope),
        n_scope_rt01_contour_only=(
            None if state is None else state.n_scope_rt01_contour_only
        ),
        n_scope_n_minimal_only=(None if state is None else state.n_scope_n_minimal_only),
        n_scope_readiness_gate_only=(
            None if state is None else state.n_scope_readiness_gate_only
        ),
        n_scope_n01_implemented=(None if state is None else state.n_scope_n01_implemented),
        n_scope_n02_implemented=(None if state is None else state.n_scope_n02_implemented),
        n_scope_n03_implemented=(None if state is None else state.n_scope_n03_implemented),
        n_scope_n04_implemented=(None if state is None else state.n_scope_n04_implemented),
        n_scope_full_narrative_line_implemented=(
            None if state is None else state.n_scope_full_narrative_line_implemented
        ),
        n_scope_repo_wide_adoption=(
            None if state is None else state.n_scope_repo_wide_adoption
        ),
        reason=result.decision.reason,
    )


def require_lawful_production_dispatch(result: RuntimeDispatchResult) -> None:
    view = derive_runtime_dispatch_contract_view(result)
    if not view.accepted:
        raise PermissionError("runtime dispatch rejected; contour path is not lawful")
    if not view.lawful_production_route:
        raise PermissionError("runtime dispatch path is not lawful production contour")


def require_dispatch_bounded_n_scope(
    result: RuntimeDispatchResult | RuntimeDispatchContractView,
) -> RuntimeDispatchContractView:
    view = (
        result
        if isinstance(result, RuntimeDispatchContractView)
        else derive_runtime_dispatch_contract_view(result)
    )
    if not view.accepted:
        raise PermissionError("runtime dispatch rejected; contour path is not lawful")
    if view.n_scope is None:
        raise PermissionError("runtime dispatch does not expose n-minimal scope surface")
    if (
        view.n_scope != "rt01_contour_only"
        or not view.n_scope_rt01_contour_only
        or not view.n_scope_n_minimal_only
        or not view.n_scope_readiness_gate_only
        or view.n_scope_n01_implemented
        or view.n_scope_n02_implemented
        or view.n_scope_n03_implemented
        or view.n_scope_n04_implemented
        or view.n_scope_full_narrative_line_implemented
        or view.n_scope_repo_wide_adoption
    ):
        raise PermissionError(
            "runtime dispatch n-surface violates bounded rt01 contour-only non-claim scope contract"
        )
    return view


def require_dispatch_strong_narrative_commitment(
    result: RuntimeDispatchResult | RuntimeDispatchContractView,
) -> RuntimeDispatchContractView:
    view = require_dispatch_bounded_n_scope(result)
    if not view.lawful_production_route:
        raise PermissionError(
            "strong narrative commitment consumer requires lawful production dispatch route"
        )
    if not view.n_safe_narrative_commitment_allowed or view.n_no_safe_narrative_claim:
        raise PermissionError(
            "strong narrative commitment requires safe bounded n-minimal basis in dispatched contour"
        )
    return view
