from __future__ import annotations

from substrate.subject_tick.models import (
    SubjectTickGateDecision,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickStepResult,
    SubjectTickTelemetry,
)


def build_subject_tick_telemetry(
    *,
    state: SubjectTickState,
    attempted_paths: tuple[str, ...],
    downstream_gate: SubjectTickGateDecision,
    causal_basis: str,
) -> SubjectTickTelemetry:
    return SubjectTickTelemetry(
        tick_id=state.tick_id,
        tick_index=state.tick_index,
        source_lineage=state.source_lineage,
        phase_order=tuple(step.phase_id for step in state.downstream_step_results),
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
        execution_stance=state.execution_stance,
        execution_checkpoints=state.execution_checkpoints,
        final_execution_outcome=state.final_execution_outcome,
        repair_needed=state.repair_needed,
        revalidation_needed=state.revalidation_needed,
        halt_reason=state.halt_reason,
        step_results=state.downstream_step_results,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def subject_tick_result_snapshot(result: SubjectTickResult) -> dict[str, object]:
    state = result.state
    return {
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_planner_orchestrator_dependency": result.no_planner_orchestrator_dependency,
        "no_phase_semantics_override_dependency": result.no_phase_semantics_override_dependency,
        "state": {
            "tick_id": state.tick_id,
            "tick_index": state.tick_index,
            "prior_runtime_status": (
                None if state.prior_runtime_status is None else state.prior_runtime_status.value
            ),
            "c04_execution_mode_claim": state.c04_execution_mode_claim,
            "c05_execution_action_claim": state.c05_execution_action_claim,
            "f01_authority_role": state.f01_authority_role,
            "r04_authority_role": state.r04_authority_role,
            "c04_authority_role": state.c04_authority_role,
            "c05_authority_role": state.c05_authority_role,
            "d01_authority_role": state.d01_authority_role,
            "rt01_authority_role": state.rt01_authority_role,
            "role_source_ref": state.role_source_ref,
            "role_frontier_only": state.role_frontier_only,
            "role_map_ready": state.role_map_ready,
            "role_frontier_typed": state.role_frontier_typed,
            "f01_computational_role": state.f01_computational_role,
            "r04_computational_role": state.r04_computational_role,
            "c04_computational_role": state.c04_computational_role,
            "c05_computational_role": state.c05_computational_role,
            "d01_computational_role": state.d01_computational_role,
            "rt01_computational_role": state.rt01_computational_role,
            "active_execution_mode": state.active_execution_mode,
            "c04_selected_mode": state.c04_selected_mode,
            "c05_validity_action": state.c05_validity_action,
            "downstream_obedience_status": state.downstream_obedience_status,
            "downstream_obedience_fallback": state.downstream_obedience_fallback,
            "downstream_obedience_source_of_truth_surface": (
                state.downstream_obedience_source_of_truth_surface
            ),
            "downstream_obedience_requires_restrictions_read": (
                state.downstream_obedience_requires_restrictions_read
            ),
            "downstream_obedience_reason": state.downstream_obedience_reason,
            "world_adapter_presence": state.world_adapter_presence,
            "world_adapter_available": state.world_adapter_available,
            "world_adapter_degraded": state.world_adapter_degraded,
            "world_link_status": state.world_link_status,
            "world_effect_status": state.world_effect_status,
            "world_grounded_transition_allowed": state.world_grounded_transition_allowed,
            "world_externally_effected_change_claim_allowed": (
                state.world_externally_effected_change_claim_allowed
            ),
            "world_action_success_claim_allowed": state.world_action_success_claim_allowed,
            "world_effect_feedback_correlated": state.world_effect_feedback_correlated,
            "world_grounding_confidence": state.world_grounding_confidence,
            "world_require_grounded_transition": state.world_require_grounded_transition,
            "world_require_effect_feedback_for_success_claim": (
                state.world_require_effect_feedback_for_success_claim
            ),
            "world_adapter_reason": state.world_adapter_reason,
            "world_entry_episode_id": state.world_entry_episode_id,
            "world_entry_presence_mode": state.world_entry_presence_mode,
            "world_entry_episode_scope": state.world_entry_episode_scope,
            "world_entry_observation_basis_present": state.world_entry_observation_basis_present,
            "world_entry_action_trace_present": state.world_entry_action_trace_present,
            "world_entry_effect_basis_present": state.world_entry_effect_basis_present,
            "world_entry_effect_feedback_correlated": state.world_entry_effect_feedback_correlated,
            "world_entry_confidence": state.world_entry_confidence,
            "world_entry_reliability": state.world_entry_reliability,
            "world_entry_degraded": state.world_entry_degraded,
            "world_entry_incomplete": state.world_entry_incomplete,
            "world_entry_forbidden_claim_classes": state.world_entry_forbidden_claim_classes,
            "world_entry_world_grounded_transition_admissible": (
                state.world_entry_world_grounded_transition_admissible
            ),
            "world_entry_world_effect_success_admissible": (
                state.world_entry_world_effect_success_admissible
            ),
            "world_entry_w01_admission_ready": state.world_entry_w01_admission_ready,
            "world_entry_w01_admission_restrictions": state.world_entry_w01_admission_restrictions,
            "world_entry_scope": state.world_entry_scope,
            "world_entry_scope_admission_layer_only": state.world_entry_scope_admission_layer_only,
            "world_entry_scope_w01_implemented": state.world_entry_scope_w01_implemented,
            "world_entry_scope_w_line_implemented": state.world_entry_scope_w_line_implemented,
            "world_entry_scope_repo_wide_adoption": state.world_entry_scope_repo_wide_adoption,
            "world_entry_scope_reason": state.world_entry_scope_reason,
            "world_entry_reason": state.world_entry_reason,
            "execution_stance": state.execution_stance.value,
            "execution_checkpoints": tuple(
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "source_contract": checkpoint.source_contract,
                    "status": checkpoint.status.value,
                    "required_action": checkpoint.required_action,
                    "applied_action": checkpoint.applied_action,
                    "reason": checkpoint.reason,
                }
                for checkpoint in state.execution_checkpoints
            ),
            "final_execution_outcome": state.final_execution_outcome.value,
            "repair_needed": state.repair_needed,
            "revalidation_needed": state.revalidation_needed,
            "halt_reason": state.halt_reason,
            "downstream_step_results": tuple(
                {
                    "phase_id": step.phase_id,
                    "status": step.status.value,
                    "gate_accepted": step.gate_accepted,
                    "usability_class": step.usability_class,
                    "execution_mode": step.execution_mode,
                    "restrictions": step.restrictions,
                    "reason": step.reason,
                }
                for step in state.downstream_step_results
            ),
            "source_stream_id": state.source_stream_id,
            "source_stream_sequence_index": state.source_stream_sequence_index,
            "source_c01_state_ref": state.source_c01_state_ref,
            "source_c02_state_ref": state.source_c02_state_ref,
            "source_c03_state_ref": state.source_c03_state_ref,
            "source_c04_state_ref": state.source_c04_state_ref,
            "source_c05_state_ref": state.source_c05_state_ref,
            "source_lineage": state.source_lineage,
            "last_update_provenance": state.last_update_provenance,
        },
        "world_adapter_result": {
            "world_link_status": result.world_adapter_result.state.world_link_status.value,
            "effect_status": result.world_adapter_result.state.effect_status.value,
            "adapter_presence": result.world_adapter_result.state.adapter_presence,
            "adapter_available": result.world_adapter_result.state.adapter_available,
            "adapter_degraded": result.world_adapter_result.state.adapter_degraded,
            "world_grounding_confidence": result.world_adapter_result.state.world_grounding_confidence,
            "world_grounded_transition_allowed": (
                result.world_adapter_result.gate.world_grounded_transition_allowed
            ),
            "externally_effected_change_claim_allowed": (
                result.world_adapter_result.gate.externally_effected_change_claim_allowed
            ),
            "world_action_success_claim_allowed": (
                result.world_adapter_result.gate.world_action_success_claim_allowed
            ),
            "effect_feedback_correlated": result.world_adapter_result.gate.effect_feedback_correlated,
            "restrictions": result.world_adapter_result.gate.restrictions,
            "reason": result.world_adapter_result.gate.reason,
        },
        "world_entry_result": {
            "episode_id": result.world_entry_result.episode.world_episode_id,
            "world_presence_mode": result.world_entry_result.episode.world_presence_mode.value,
            "observation_basis_present": result.world_entry_result.episode.observation_basis_present,
            "action_trace_present": result.world_entry_result.episode.action_trace_present,
            "effect_basis_present": result.world_entry_result.episode.effect_basis_present,
            "effect_feedback_correlated": result.world_entry_result.episode.effect_feedback_correlated,
            "forbidden_claim_classes": result.world_entry_result.forbidden_claim_classes,
            "world_grounded_transition_admissible": (
                result.world_entry_result.world_grounded_transition_admissible
            ),
            "world_effect_success_admissible": (
                result.world_entry_result.world_effect_success_admissible
            ),
            "w01_admission_ready": result.world_entry_result.w01_admission.admission_ready,
            "w01_admission_restrictions": result.world_entry_result.w01_admission.restrictions,
            "scope_marker": {
                "scope": result.world_entry_result.scope_marker.scope,
                "admission_layer_only": result.world_entry_result.scope_marker.admission_layer_only,
                "w01_implemented": result.world_entry_result.scope_marker.w01_implemented,
                "w_line_implemented": result.world_entry_result.scope_marker.w_line_implemented,
                "repo_wide_adoption": result.world_entry_result.scope_marker.repo_wide_adoption,
                "reason": result.world_entry_result.scope_marker.reason,
            },
            "reason": result.world_entry_result.reason,
        },
        "downstream_gate": {
            "accepted": result.downstream_gate.accepted,
            "usability_class": result.downstream_gate.usability_class.value,
            "restrictions": tuple(code.value for code in result.downstream_gate.restrictions),
            "reason": result.downstream_gate.reason,
            "state_ref": result.downstream_gate.state_ref,
        },
        "telemetry": {
            "tick_id": result.telemetry.tick_id,
            "tick_index": result.telemetry.tick_index,
            "source_lineage": result.telemetry.source_lineage,
            "phase_order": result.telemetry.phase_order,
            "c04_execution_mode_claim": result.telemetry.c04_execution_mode_claim,
            "c05_execution_action_claim": result.telemetry.c05_execution_action_claim,
            "f01_authority_role": result.telemetry.f01_authority_role,
            "r04_authority_role": result.telemetry.r04_authority_role,
            "c04_authority_role": result.telemetry.c04_authority_role,
            "c05_authority_role": result.telemetry.c05_authority_role,
            "d01_authority_role": result.telemetry.d01_authority_role,
            "rt01_authority_role": result.telemetry.rt01_authority_role,
            "role_source_ref": result.telemetry.role_source_ref,
            "role_frontier_only": result.telemetry.role_frontier_only,
            "role_map_ready": result.telemetry.role_map_ready,
            "role_frontier_typed": result.telemetry.role_frontier_typed,
            "active_execution_mode": result.telemetry.active_execution_mode,
            "c04_selected_mode": result.telemetry.c04_selected_mode,
            "c05_validity_action": result.telemetry.c05_validity_action,
            "downstream_obedience_status": result.telemetry.downstream_obedience_status,
            "downstream_obedience_fallback": result.telemetry.downstream_obedience_fallback,
            "downstream_obedience_source_of_truth_surface": (
                result.telemetry.downstream_obedience_source_of_truth_surface
            ),
            "downstream_obedience_requires_restrictions_read": (
                result.telemetry.downstream_obedience_requires_restrictions_read
            ),
            "downstream_obedience_reason": result.telemetry.downstream_obedience_reason,
            "world_adapter_presence": result.telemetry.world_adapter_presence,
            "world_adapter_available": result.telemetry.world_adapter_available,
            "world_adapter_degraded": result.telemetry.world_adapter_degraded,
            "world_link_status": result.telemetry.world_link_status,
            "world_effect_status": result.telemetry.world_effect_status,
            "world_grounded_transition_allowed": (
                result.telemetry.world_grounded_transition_allowed
            ),
            "world_externally_effected_change_claim_allowed": (
                result.telemetry.world_externally_effected_change_claim_allowed
            ),
            "world_action_success_claim_allowed": (
                result.telemetry.world_action_success_claim_allowed
            ),
            "world_effect_feedback_correlated": result.telemetry.world_effect_feedback_correlated,
            "world_grounding_confidence": result.telemetry.world_grounding_confidence,
            "world_require_grounded_transition": result.telemetry.world_require_grounded_transition,
            "world_require_effect_feedback_for_success_claim": (
                result.telemetry.world_require_effect_feedback_for_success_claim
            ),
            "world_adapter_reason": result.telemetry.world_adapter_reason,
            "world_entry_episode_id": result.telemetry.world_entry_episode_id,
            "world_entry_presence_mode": result.telemetry.world_entry_presence_mode,
            "world_entry_episode_scope": result.telemetry.world_entry_episode_scope,
            "world_entry_observation_basis_present": (
                result.telemetry.world_entry_observation_basis_present
            ),
            "world_entry_action_trace_present": result.telemetry.world_entry_action_trace_present,
            "world_entry_effect_basis_present": result.telemetry.world_entry_effect_basis_present,
            "world_entry_effect_feedback_correlated": (
                result.telemetry.world_entry_effect_feedback_correlated
            ),
            "world_entry_confidence": result.telemetry.world_entry_confidence,
            "world_entry_reliability": result.telemetry.world_entry_reliability,
            "world_entry_degraded": result.telemetry.world_entry_degraded,
            "world_entry_incomplete": result.telemetry.world_entry_incomplete,
            "world_entry_forbidden_claim_classes": (
                result.telemetry.world_entry_forbidden_claim_classes
            ),
            "world_entry_world_grounded_transition_admissible": (
                result.telemetry.world_entry_world_grounded_transition_admissible
            ),
            "world_entry_world_effect_success_admissible": (
                result.telemetry.world_entry_world_effect_success_admissible
            ),
            "world_entry_w01_admission_ready": result.telemetry.world_entry_w01_admission_ready,
            "world_entry_w01_admission_restrictions": (
                result.telemetry.world_entry_w01_admission_restrictions
            ),
            "world_entry_scope": result.telemetry.world_entry_scope,
            "world_entry_scope_admission_layer_only": (
                result.telemetry.world_entry_scope_admission_layer_only
            ),
            "world_entry_scope_w01_implemented": result.telemetry.world_entry_scope_w01_implemented,
            "world_entry_scope_w_line_implemented": (
                result.telemetry.world_entry_scope_w_line_implemented
            ),
            "world_entry_scope_repo_wide_adoption": (
                result.telemetry.world_entry_scope_repo_wide_adoption
            ),
            "world_entry_scope_reason": result.telemetry.world_entry_scope_reason,
            "world_entry_reason": result.telemetry.world_entry_reason,
            "execution_stance": result.telemetry.execution_stance.value,
            "execution_checkpoints": tuple(
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "source_contract": checkpoint.source_contract,
                    "status": checkpoint.status.value,
                    "required_action": checkpoint.required_action,
                    "applied_action": checkpoint.applied_action,
                    "reason": checkpoint.reason,
                }
                for checkpoint in result.telemetry.execution_checkpoints
            ),
            "final_execution_outcome": result.telemetry.final_execution_outcome.value,
            "repair_needed": result.telemetry.repair_needed,
            "revalidation_needed": result.telemetry.revalidation_needed,
            "halt_reason": result.telemetry.halt_reason,
            "step_results": tuple(_step_to_payload(step) for step in result.telemetry.step_results),
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": tuple(
                    code.value for code in result.telemetry.downstream_gate.restrictions
                ),
                "reason": result.telemetry.downstream_gate.reason,
                "state_ref": result.telemetry.downstream_gate.state_ref,
            },
            "causal_basis": result.telemetry.causal_basis,
            "emitted_at": result.telemetry.emitted_at,
        },
    }


def _step_to_payload(step: SubjectTickStepResult) -> dict[str, object]:
    return {
        "phase_id": step.phase_id,
        "status": step.status.value,
        "gate_accepted": step.gate_accepted,
        "usability_class": step.usability_class,
        "execution_mode": step.execution_mode,
        "restrictions": step.restrictions,
        "reason": step.reason,
    }
