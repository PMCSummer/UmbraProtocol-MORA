from __future__ import annotations

from dataclasses import dataclass

from substrate.mode_arbitration.models import (
    C04RestrictionCode,
    ModeArbitrationResult,
    ModeArbitrationState,
    ModeArbitrationUsabilityClass,
    SubjectMode,
)
from substrate.mode_arbitration.policy import evaluate_mode_arbitration_downstream_gate


@dataclass(frozen=True, slots=True)
class ModeArbitrationContractView:
    arbitration_id: str
    tick_id: str
    stream_id: str
    active_mode: SubjectMode
    candidate_modes: tuple[SubjectMode, ...]
    endogenous_tick_allowed: bool
    endogenous_tick_kind: str
    hold_or_switch_decision: str
    interruptibility: str
    dwell_budget_remaining: int
    forced_rearbitration: bool
    arbitration_confidence: float
    safe_idle_active: bool
    gate_accepted: bool
    restrictions: tuple[C04RestrictionCode, ...]
    usability_class: ModeArbitrationUsabilityClass
    requires_restrictions_read: bool
    reason: str


def derive_mode_arbitration_contract_view(
    mode_arbitration_state_or_result: ModeArbitrationState | ModeArbitrationResult,
) -> ModeArbitrationContractView:
    if isinstance(mode_arbitration_state_or_result, ModeArbitrationResult):
        state = mode_arbitration_state_or_result.state
    elif isinstance(mode_arbitration_state_or_result, ModeArbitrationState):
        state = mode_arbitration_state_or_result
    else:
        raise TypeError(
            "derive_mode_arbitration_contract_view requires ModeArbitrationState/ModeArbitrationResult"
        )
    gate = evaluate_mode_arbitration_downstream_gate(state)
    return ModeArbitrationContractView(
        arbitration_id=state.arbitration_id,
        tick_id=state.tick_id,
        stream_id=state.stream_id,
        active_mode=state.active_mode,
        candidate_modes=state.candidate_modes,
        endogenous_tick_allowed=state.endogenous_tick_allowed,
        endogenous_tick_kind=state.endogenous_tick_kind.value,
        hold_or_switch_decision=state.hold_or_switch_decision.value,
        interruptibility=state.interruptibility.value,
        dwell_budget_remaining=state.dwell_budget_remaining,
        forced_rearbitration=state.forced_rearbitration,
        arbitration_confidence=state.arbitration_confidence,
        safe_idle_active=state.active_mode == SubjectMode.SAFE_IDLE,
        gate_accepted=gate.accepted,
        restrictions=gate.restrictions,
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason="contract requires typed c04 mode arbitration surfaces to be read",
    )


def choose_subject_execution_mode(
    mode_arbitration_state_or_result: ModeArbitrationState | ModeArbitrationResult,
) -> str:
    view = derive_mode_arbitration_contract_view(mode_arbitration_state_or_result)
    if not view.gate_accepted or view.usability_class == ModeArbitrationUsabilityClass.BLOCKED:
        return "hold_safe_idle"
    if view.safe_idle_active:
        return "idle"
    if view.active_mode == SubjectMode.RECOVERY_MODE:
        return "run_recovery"
    if view.active_mode == SubjectMode.REVISIT_UNRESOLVED_TENSION:
        return "run_revisit"
    if view.active_mode == SubjectMode.DIVERSIFICATION_PROBE:
        return "probe_alternatives"
    if view.active_mode == SubjectMode.OUTPUT_PREPARATION:
        return "prepare_output"
    if view.active_mode == SubjectMode.PASSIVE_MONITORING:
        return "monitor_only"
    if view.active_mode == SubjectMode.HOLD_CURRENT_STREAM:
        return "continue_stream"
    return "hold_safe_idle"


def eligible_mode_candidates(
    mode_arbitration_state_or_result: ModeArbitrationState | ModeArbitrationResult,
) -> tuple[str, ...]:
    if isinstance(mode_arbitration_state_or_result, ModeArbitrationResult):
        state = mode_arbitration_state_or_result.state
    elif isinstance(mode_arbitration_state_or_result, ModeArbitrationState):
        state = mode_arbitration_state_or_result
    else:
        raise TypeError(
            "eligible_mode_candidates requires ModeArbitrationState/ModeArbitrationResult"
        )
    gate = evaluate_mode_arbitration_downstream_gate(state)
    if not gate.accepted:
        return ()
    if state.active_mode == SubjectMode.SAFE_IDLE:
        return (SubjectMode.SAFE_IDLE.value,)
    return tuple(mode.value for mode in state.candidate_modes)


def can_run_mode_candidate(
    mode_arbitration_state_or_result: ModeArbitrationState | ModeArbitrationResult,
    candidate_mode: SubjectMode | str,
) -> bool:
    if isinstance(candidate_mode, str):
        try:
            candidate = SubjectMode(candidate_mode)
        except ValueError:
            return False
    elif isinstance(candidate_mode, SubjectMode):
        candidate = candidate_mode
    else:
        raise TypeError("candidate_mode must be SubjectMode or str")

    eligible = set(eligible_mode_candidates(mode_arbitration_state_or_result))
    return candidate.value in eligible
