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
        active_execution_mode=state.active_execution_mode,
        c04_selected_mode=state.c04_selected_mode,
        c05_validity_action=state.c05_validity_action,
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
            "active_execution_mode": state.active_execution_mode,
            "c04_selected_mode": state.c04_selected_mode,
            "c05_validity_action": state.c05_validity_action,
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
            "active_execution_mode": result.telemetry.active_execution_mode,
            "c04_selected_mode": result.telemetry.c04_selected_mode,
            "c05_validity_action": result.telemetry.c05_validity_action,
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
