from __future__ import annotations

from dataclasses import dataclass

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
    active_execution_mode: str
    c04_selected_mode: str
    c05_validity_action: str
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
        active_execution_mode=state.active_execution_mode,
        c04_selected_mode=state.c04_selected_mode,
        c05_validity_action=state.c05_validity_action,
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
