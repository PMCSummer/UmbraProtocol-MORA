from __future__ import annotations

from substrate.mode_arbitration.models import (
    C04RestrictionCode,
    HoldSwitchDecision,
    ModeArbitrationGateDecision,
    ModeArbitrationResult,
    ModeArbitrationState,
    ModeArbitrationUsabilityClass,
)


def evaluate_mode_arbitration_downstream_gate(
    mode_arbitration_state_or_result: object,
) -> ModeArbitrationGateDecision:
    if isinstance(mode_arbitration_state_or_result, ModeArbitrationResult):
        state = mode_arbitration_state_or_result.state
    elif isinstance(mode_arbitration_state_or_result, ModeArbitrationState):
        state = mode_arbitration_state_or_result
    else:
        raise TypeError(
            "evaluate_mode_arbitration_downstream_gate requires ModeArbitrationState/ModeArbitrationResult"
        )

    restrictions: list[C04RestrictionCode] = [
        C04RestrictionCode.MODE_ARBITRATION_STATE_MUST_BE_READ,
        C04RestrictionCode.ENDOGENOUS_TICK_CONTRACT_MUST_BE_READ,
        C04RestrictionCode.ACTIVE_MODE_MUST_BE_READ,
        C04RestrictionCode.CANDIDATE_MODES_MUST_BE_READ,
        C04RestrictionCode.ARBITRATION_BASIS_MUST_BE_READ,
        C04RestrictionCode.MODE_PRIORITY_VECTOR_MUST_BE_READ,
        C04RestrictionCode.HOLD_SWITCH_DECISION_MUST_BE_READ,
        C04RestrictionCode.INTERRUPTIBILITY_MUST_BE_READ,
        C04RestrictionCode.DWELL_BUDGET_MUST_BE_READ,
        C04RestrictionCode.SAFE_IDLE_MUST_BE_READ,
        C04RestrictionCode.SURVIVAL_INTERRUPT_MUST_BE_READ,
        C04RestrictionCode.NO_PLANNER_MODE_BACKFILL,
        C04RestrictionCode.NO_BACKGROUND_LOOP_SHORTCUT,
        C04RestrictionCode.NO_EXTERNAL_TURN_SUBSTITUTION,
    ]

    accepted = True
    usability = ModeArbitrationUsabilityClass.USABLE_BOUNDED
    reason = "typed c04 mode arbitration is available for bounded endogenous governance"

    if state.hold_or_switch_decision == HoldSwitchDecision.NO_CLEAR_MODE_WINNER:
        restrictions.append(C04RestrictionCode.NO_CLEAR_MODE_WINNER_PRESENT)
    if state.hold_or_switch_decision == HoldSwitchDecision.ARBITRATION_CONFLICT:
        restrictions.append(C04RestrictionCode.ARBITRATION_CONFLICT_PRESENT)
    if state.hold_or_switch_decision == HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS:
        restrictions.append(C04RestrictionCode.INSUFFICIENT_INTERNAL_BASIS_PRESENT)

    degraded = bool(
        state.hold_or_switch_decision
        in {
            HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
            HoldSwitchDecision.ARBITRATION_CONFLICT,
            HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
            HoldSwitchDecision.SAFE_IDLE_ONLY,
            HoldSwitchDecision.FORCED_REARBITRATION,
        }
        or state.arbitration_confidence < 0.58
        or not state.endogenous_tick_allowed
    )

    blocked = bool(
        state.hold_or_switch_decision == HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS
        and state.endogenous_tick_allowed is False
        and state.external_turn_present is False
        and state.arbitration_confidence < 0.25
    )

    if blocked:
        accepted = False
        usability = ModeArbitrationUsabilityClass.BLOCKED
        restrictions.append(C04RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "insufficient internal basis for lawful c04 active mode claim"
    elif degraded:
        usability = ModeArbitrationUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(C04RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "c04 arbitration is bounded/degraded and requires cautious downstream use"

    return ModeArbitrationGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.arbitration_id}@{state.source_stream_sequence_index}",
    )
