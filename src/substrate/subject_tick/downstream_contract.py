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
        reason="runtime contour contract requires C04/C05 claims plus checkpointed execution stance surfaces to be read",
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
