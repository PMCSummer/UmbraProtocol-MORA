from __future__ import annotations

from dataclasses import dataclass

from substrate.contracts import RuntimeState
from substrate.subject_tick.models import (
    SubjectTickOutcome,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickUsabilityClass,
)
from substrate.subject_tick.policy import evaluate_subject_tick_downstream_gate


@dataclass(frozen=True, slots=True)
class SubjectTickContractView:
    tick_id: str
    tick_index: int
    c04_execution_mode_claim: str
    c05_execution_action_claim: str
    f01_authority_role: str
    r04_authority_role: str
    c04_authority_role: str
    c05_authority_role: str
    d01_authority_role: str
    rt01_authority_role: str
    role_source_ref: str
    role_frontier_only: bool
    role_map_ready: bool
    role_frontier_typed: bool
    active_execution_mode: str
    c04_selected_mode: str
    c05_validity_action: str
    downstream_obedience_status: str
    downstream_obedience_fallback: str
    downstream_obedience_source_of_truth_surface: str
    downstream_obedience_requires_restrictions_read: bool
    downstream_obedience_reason: str
    world_adapter_presence: bool
    world_adapter_available: bool
    world_adapter_degraded: bool
    world_link_status: str
    world_effect_status: str
    world_grounded_transition_allowed: bool
    world_externally_effected_change_claim_allowed: bool
    world_action_success_claim_allowed: bool
    world_effect_feedback_correlated: bool
    world_grounding_confidence: float
    world_require_grounded_transition: bool
    world_require_effect_feedback_for_success_claim: bool
    world_adapter_reason: str
    world_entry_episode_id: str
    world_entry_presence_mode: str
    world_entry_episode_scope: str
    world_entry_observation_basis_present: bool
    world_entry_action_trace_present: bool
    world_entry_effect_basis_present: bool
    world_entry_effect_feedback_correlated: bool
    world_entry_confidence: float
    world_entry_reliability: str
    world_entry_degraded: bool
    world_entry_incomplete: bool
    world_entry_forbidden_claim_classes: tuple[str, ...]
    world_entry_world_grounded_transition_admissible: bool
    world_entry_world_effect_success_admissible: bool
    world_entry_w01_admission_ready: bool
    world_entry_w01_admission_restrictions: tuple[str, ...]
    world_entry_scope: str
    world_entry_scope_admission_layer_only: bool
    world_entry_scope_w01_implemented: bool
    world_entry_scope_w_line_implemented: bool
    world_entry_scope_repo_wide_adoption: bool
    world_entry_scope_reason: str
    world_entry_reason: str
    s_boundary_state_id: str
    s_self_attribution_basis_present: bool
    s_world_attribution_basis_present: bool
    s_controllability_estimate: float
    s_ownership_estimate: float
    s_attribution_confidence: float
    s_source_status: str
    s_boundary_breach_risk: str
    s_attribution_class: str
    s_no_safe_self_claim: bool
    s_no_safe_world_claim: bool
    s_degraded: bool
    s_underconstrained: bool
    s_forbidden_shortcuts: tuple[str, ...]
    s_restrictions: tuple[str, ...]
    s_s01_admission_ready: bool
    s_self_attribution_basis_sufficient: bool
    s_controllability_basis_sufficient: bool
    s_ownership_basis_sufficient: bool
    s_attribution_underconstrained: bool
    s_mixed_boundary_instability: bool
    s_no_safe_self_basis: bool
    s_no_safe_world_basis: bool
    s_readiness_blockers: tuple[str, ...]
    s_future_s01_s05_remain_open: bool
    s_full_self_model_implemented: bool
    s_scope: str
    s_scope_rt01_contour_only: bool
    s_scope_s_minimal_only: bool
    s_scope_s01_implemented: bool
    s_scope_s_line_implemented: bool
    s_scope_minimal_contour_only: bool
    s_scope_s01_s05_implemented: bool
    s_scope_full_self_model_implemented: bool
    s_scope_repo_wide_adoption: bool
    s_scope_reason: str
    s_reason: str
    s_require_self_side_claim: bool
    s_require_world_side_claim: bool
    s_require_self_controlled_transition_claim: bool
    s_strict_mixed_attribution_guard: bool
    a_capability_id: str
    a_affordance_id: str
    a_capability_class: str
    a_capability_status: str
    a_availability_basis_present: bool
    a_world_dependency_present: bool
    a_self_dependency_present: bool
    a_controllability_dependency_present: bool
    a_legitimacy_dependency_present: bool
    a_confidence: float
    a_degraded: bool
    a_underconstrained: bool
    a_available_capability_claim_allowed: bool
    a_world_conditioned_capability_claim_allowed: bool
    a_self_conditioned_capability_claim_allowed: bool
    a_policy_conditioned_capability_present: bool
    a_no_safe_capability_claim: bool
    a_forbidden_shortcuts: tuple[str, ...]
    a_restrictions: tuple[str, ...]
    a_a04_admission_ready: bool
    a_a04_blockers: tuple[str, ...]
    a_a04_structurally_present_but_not_ready: bool
    a_a04_capability_basis_missing: bool
    a_a04_world_dependency_unmet: bool
    a_a04_self_dependency_unmet: bool
    a_a04_policy_legitimacy_unmet: bool
    a_a04_underconstrained_capability_surface: bool
    a_a04_external_means_not_justified: bool
    a_a04_implemented: bool
    a_a05_touched: bool
    a_scope: str
    a_scope_rt01_contour_only: bool
    a_scope_a_line_normalization_only: bool
    a_scope_readiness_gate_only: bool
    a_scope_a04_implemented: bool
    a_scope_a05_touched: bool
    a_scope_full_agency_stack_implemented: bool
    a_scope_repo_wide_adoption: bool
    a_scope_reason: str
    a_reason: str
    a_require_capability_claim: bool
    execution_stance: str
    execution_checkpoints: tuple[str, ...]
    final_execution_outcome: SubjectTickOutcome
    repair_needed: bool
    revalidation_needed: bool
    halt_reason: str | None
    gate_accepted: bool
    restrictions: tuple[str, ...]
    usability_class: SubjectTickUsabilityClass
    requires_restrictions_read: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SubjectTickRuntimeDomainContractView:
    regulation_pressure_level: float | None
    regulation_override_scope: str | None
    continuity_mode_claim: str | None
    continuity_mode_legitimacy: bool
    validity_action_claim: str | None
    validity_legality_reuse_allowed: bool
    validity_revalidation_required: bool
    validity_no_safe_reuse: bool
    recommended_outcome: str
    source_of_truth_surface: str
    packet_snapshot_precedence_blocked: bool
    reason: str


def derive_subject_tick_contract_view(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult,
) -> SubjectTickContractView:
    if isinstance(subject_tick_state_or_result, SubjectTickResult):
        state = subject_tick_state_or_result.state
    elif isinstance(subject_tick_state_or_result, SubjectTickState):
        state = subject_tick_state_or_result
    else:
        raise TypeError(
            "derive_subject_tick_contract_view requires SubjectTickState/SubjectTickResult"
        )
    gate = evaluate_subject_tick_downstream_gate(state)
    return SubjectTickContractView(
        tick_id=state.tick_id,
        tick_index=state.tick_index,
        c04_execution_mode_claim=state.c04_execution_mode_claim,
        c05_execution_action_claim=state.c05_execution_action_claim,
        f01_authority_role=state.f01_authority_role,
        r04_authority_role=state.r04_authority_role,
        c04_authority_role=state.c04_authority_role,
        c05_authority_role=state.c05_authority_role,
        d01_authority_role=state.d01_authority_role,
        rt01_authority_role=state.rt01_authority_role,
        role_source_ref=state.role_source_ref,
        role_frontier_only=state.role_frontier_only,
        role_map_ready=state.role_map_ready,
        role_frontier_typed=state.role_frontier_typed,
        active_execution_mode=state.active_execution_mode,
        c04_selected_mode=state.c04_selected_mode,
        c05_validity_action=state.c05_validity_action,
        downstream_obedience_status=state.downstream_obedience_status,
        downstream_obedience_fallback=state.downstream_obedience_fallback,
        downstream_obedience_source_of_truth_surface=state.downstream_obedience_source_of_truth_surface,
        downstream_obedience_requires_restrictions_read=(
            state.downstream_obedience_requires_restrictions_read
        ),
        downstream_obedience_reason=state.downstream_obedience_reason,
        world_adapter_presence=state.world_adapter_presence,
        world_adapter_available=state.world_adapter_available,
        world_adapter_degraded=state.world_adapter_degraded,
        world_link_status=state.world_link_status,
        world_effect_status=state.world_effect_status,
        world_grounded_transition_allowed=state.world_grounded_transition_allowed,
        world_externally_effected_change_claim_allowed=(
            state.world_externally_effected_change_claim_allowed
        ),
        world_action_success_claim_allowed=state.world_action_success_claim_allowed,
        world_effect_feedback_correlated=state.world_effect_feedback_correlated,
        world_grounding_confidence=state.world_grounding_confidence,
        world_require_grounded_transition=state.world_require_grounded_transition,
        world_require_effect_feedback_for_success_claim=(
            state.world_require_effect_feedback_for_success_claim
        ),
        world_adapter_reason=state.world_adapter_reason,
        world_entry_episode_id=state.world_entry_episode_id,
        world_entry_presence_mode=state.world_entry_presence_mode,
        world_entry_episode_scope=state.world_entry_episode_scope,
        world_entry_observation_basis_present=state.world_entry_observation_basis_present,
        world_entry_action_trace_present=state.world_entry_action_trace_present,
        world_entry_effect_basis_present=state.world_entry_effect_basis_present,
        world_entry_effect_feedback_correlated=state.world_entry_effect_feedback_correlated,
        world_entry_confidence=state.world_entry_confidence,
        world_entry_reliability=state.world_entry_reliability,
        world_entry_degraded=state.world_entry_degraded,
        world_entry_incomplete=state.world_entry_incomplete,
        world_entry_forbidden_claim_classes=state.world_entry_forbidden_claim_classes,
        world_entry_world_grounded_transition_admissible=(
            state.world_entry_world_grounded_transition_admissible
        ),
        world_entry_world_effect_success_admissible=(
            state.world_entry_world_effect_success_admissible
        ),
        world_entry_w01_admission_ready=state.world_entry_w01_admission_ready,
        world_entry_w01_admission_restrictions=state.world_entry_w01_admission_restrictions,
        world_entry_scope=state.world_entry_scope,
        world_entry_scope_admission_layer_only=state.world_entry_scope_admission_layer_only,
        world_entry_scope_w01_implemented=state.world_entry_scope_w01_implemented,
        world_entry_scope_w_line_implemented=state.world_entry_scope_w_line_implemented,
        world_entry_scope_repo_wide_adoption=state.world_entry_scope_repo_wide_adoption,
        world_entry_scope_reason=state.world_entry_scope_reason,
        world_entry_reason=state.world_entry_reason,
        s_boundary_state_id=state.s_boundary_state_id,
        s_self_attribution_basis_present=state.s_self_attribution_basis_present,
        s_world_attribution_basis_present=state.s_world_attribution_basis_present,
        s_controllability_estimate=state.s_controllability_estimate,
        s_ownership_estimate=state.s_ownership_estimate,
        s_attribution_confidence=state.s_attribution_confidence,
        s_source_status=state.s_source_status,
        s_boundary_breach_risk=state.s_boundary_breach_risk,
        s_attribution_class=state.s_attribution_class,
        s_no_safe_self_claim=state.s_no_safe_self_claim,
        s_no_safe_world_claim=state.s_no_safe_world_claim,
        s_degraded=state.s_degraded,
        s_underconstrained=state.s_underconstrained,
        s_forbidden_shortcuts=state.s_forbidden_shortcuts,
        s_restrictions=state.s_restrictions,
        s_s01_admission_ready=state.s_s01_admission_ready,
        s_self_attribution_basis_sufficient=state.s_self_attribution_basis_sufficient,
        s_controllability_basis_sufficient=state.s_controllability_basis_sufficient,
        s_ownership_basis_sufficient=state.s_ownership_basis_sufficient,
        s_attribution_underconstrained=state.s_attribution_underconstrained,
        s_mixed_boundary_instability=state.s_mixed_boundary_instability,
        s_no_safe_self_basis=state.s_no_safe_self_basis,
        s_no_safe_world_basis=state.s_no_safe_world_basis,
        s_readiness_blockers=state.s_readiness_blockers,
        s_future_s01_s05_remain_open=state.s_future_s01_s05_remain_open,
        s_full_self_model_implemented=state.s_full_self_model_implemented,
        s_scope=state.s_scope,
        s_scope_rt01_contour_only=state.s_scope_rt01_contour_only,
        s_scope_s_minimal_only=state.s_scope_s_minimal_only,
        s_scope_s01_implemented=state.s_scope_s01_implemented,
        s_scope_s_line_implemented=state.s_scope_s_line_implemented,
        s_scope_minimal_contour_only=state.s_scope_minimal_contour_only,
        s_scope_s01_s05_implemented=state.s_scope_s01_s05_implemented,
        s_scope_full_self_model_implemented=state.s_scope_full_self_model_implemented,
        s_scope_repo_wide_adoption=state.s_scope_repo_wide_adoption,
        s_scope_reason=state.s_scope_reason,
        s_reason=state.s_reason,
        s_require_self_side_claim=state.s_require_self_side_claim,
        s_require_world_side_claim=state.s_require_world_side_claim,
        s_require_self_controlled_transition_claim=(
            state.s_require_self_controlled_transition_claim
        ),
        s_strict_mixed_attribution_guard=state.s_strict_mixed_attribution_guard,
        a_capability_id=state.a_capability_id,
        a_affordance_id=state.a_affordance_id,
        a_capability_class=state.a_capability_class,
        a_capability_status=state.a_capability_status,
        a_availability_basis_present=state.a_availability_basis_present,
        a_world_dependency_present=state.a_world_dependency_present,
        a_self_dependency_present=state.a_self_dependency_present,
        a_controllability_dependency_present=state.a_controllability_dependency_present,
        a_legitimacy_dependency_present=state.a_legitimacy_dependency_present,
        a_confidence=state.a_confidence,
        a_degraded=state.a_degraded,
        a_underconstrained=state.a_underconstrained,
        a_available_capability_claim_allowed=state.a_available_capability_claim_allowed,
        a_world_conditioned_capability_claim_allowed=(
            state.a_world_conditioned_capability_claim_allowed
        ),
        a_self_conditioned_capability_claim_allowed=(
            state.a_self_conditioned_capability_claim_allowed
        ),
        a_policy_conditioned_capability_present=(
            state.a_policy_conditioned_capability_present
        ),
        a_no_safe_capability_claim=state.a_no_safe_capability_claim,
        a_forbidden_shortcuts=state.a_forbidden_shortcuts,
        a_restrictions=state.a_restrictions,
        a_a04_admission_ready=state.a_a04_admission_ready,
        a_a04_blockers=state.a_a04_blockers,
        a_a04_structurally_present_but_not_ready=(
            state.a_a04_structurally_present_but_not_ready
        ),
        a_a04_capability_basis_missing=state.a_a04_capability_basis_missing,
        a_a04_world_dependency_unmet=state.a_a04_world_dependency_unmet,
        a_a04_self_dependency_unmet=state.a_a04_self_dependency_unmet,
        a_a04_policy_legitimacy_unmet=state.a_a04_policy_legitimacy_unmet,
        a_a04_underconstrained_capability_surface=(
            state.a_a04_underconstrained_capability_surface
        ),
        a_a04_external_means_not_justified=(
            state.a_a04_external_means_not_justified
        ),
        a_a04_implemented=state.a_a04_implemented,
        a_a05_touched=state.a_a05_touched,
        a_scope=state.a_scope,
        a_scope_rt01_contour_only=state.a_scope_rt01_contour_only,
        a_scope_a_line_normalization_only=state.a_scope_a_line_normalization_only,
        a_scope_readiness_gate_only=state.a_scope_readiness_gate_only,
        a_scope_a04_implemented=state.a_scope_a04_implemented,
        a_scope_a05_touched=state.a_scope_a05_touched,
        a_scope_full_agency_stack_implemented=state.a_scope_full_agency_stack_implemented,
        a_scope_repo_wide_adoption=state.a_scope_repo_wide_adoption,
        a_scope_reason=state.a_scope_reason,
        a_reason=state.a_reason,
        a_require_capability_claim=state.a_require_capability_claim,
        execution_stance=state.execution_stance.value,
        execution_checkpoints=tuple(
            f"{checkpoint.checkpoint_id}:{checkpoint.status.value}"
            for checkpoint in state.execution_checkpoints
        ),
        final_execution_outcome=state.final_execution_outcome,
        repair_needed=state.repair_needed,
        revalidation_needed=state.revalidation_needed,
        halt_reason=state.halt_reason,
        gate_accepted=gate.accepted,
        restrictions=tuple(code.value for code in gate.restrictions),
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason=(
            "runtime contour contract requires C04/C05 claims, world-entry basis, s-minimal "
            "self/world boundary and a-line normalization checkpoint surfaces to be read"
        ),
    )


def derive_subject_tick_runtime_domain_contract_view(
    runtime_state: RuntimeState,
) -> SubjectTickRuntimeDomainContractView:
    if not isinstance(runtime_state, RuntimeState):
        raise TypeError("derive_subject_tick_runtime_domain_contract_view requires RuntimeState")

    regulation = runtime_state.domains.regulation
    continuity = runtime_state.domains.continuity
    validity = runtime_state.domains.validity
    if validity.no_safe_reuse:
        outcome = "halt"
        reason = "shared validity no_safe_reuse blocks continuation"
    elif validity.revalidation_required or not validity.legality_reuse_allowed:
        outcome = "revalidate"
        reason = "shared validity requires bounded revalidation before continuation"
    elif not continuity.mode_legitimacy:
        outcome = "repair"
        reason = "shared continuity marks mode legitimacy failure"
    else:
        outcome = "continue"
        reason = "shared runtime domains allow bounded continuation"

    return SubjectTickRuntimeDomainContractView(
        regulation_pressure_level=regulation.pressure_level,
        regulation_override_scope=regulation.override_scope,
        continuity_mode_claim=continuity.c04_mode_claim,
        continuity_mode_legitimacy=continuity.mode_legitimacy,
        validity_action_claim=validity.c05_action_claim,
        validity_legality_reuse_allowed=validity.legality_reuse_allowed,
        validity_revalidation_required=validity.revalidation_required,
        validity_no_safe_reuse=validity.no_safe_reuse,
        recommended_outcome=outcome,
        source_of_truth_surface="runtime_state.domains",
        packet_snapshot_precedence_blocked=True,
        reason=reason,
    )


def choose_runtime_execution_outcome(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult,
) -> str:
    view = derive_subject_tick_contract_view(subject_tick_state_or_result)
    if not view.gate_accepted or view.final_execution_outcome == SubjectTickOutcome.HALT:
        return "halt"
    if view.final_execution_outcome == SubjectTickOutcome.REVALIDATE:
        return "revalidate"
    if view.final_execution_outcome == SubjectTickOutcome.REPAIR:
        return "repair"
    return "continue"


def choose_runtime_execution_outcome_from_runtime_state(runtime_state: RuntimeState) -> str:
    view = derive_subject_tick_runtime_domain_contract_view(runtime_state)
    return view.recommended_outcome
