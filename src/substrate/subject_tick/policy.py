from __future__ import annotations

from substrate.subject_tick.models import (
    SubjectTickGateDecision,
    SubjectTickOutcome,
    SubjectTickRestrictionCode,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickUsabilityClass,
)


def evaluate_subject_tick_downstream_gate(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult,
) -> SubjectTickGateDecision:
    if isinstance(subject_tick_state_or_result, SubjectTickResult):
        state = subject_tick_state_or_result.state
    elif isinstance(subject_tick_state_or_result, SubjectTickState):
        state = subject_tick_state_or_result
    else:
        raise TypeError(
            "evaluate_subject_tick_downstream_gate requires SubjectTickState/SubjectTickResult"
        )

    restrictions: list[SubjectTickRestrictionCode] = [
        SubjectTickRestrictionCode.FIXED_ORDER_MUST_BE_READ,
        SubjectTickRestrictionCode.R_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C01_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C02_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C03_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C04_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C05_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C04_MODE_SELECTION_MUST_BE_ENFORCED,
        SubjectTickRestrictionCode.C05_VALIDITY_ACTION_MUST_BE_ENFORCED,
        SubjectTickRestrictionCode.C05_RESTRICTIONS_MUST_NOT_BE_IGNORED,
        SubjectTickRestrictionCode.OUTCOME_MUST_BE_BOUNDED,
        SubjectTickRestrictionCode.EXECUTION_STANCE_MUST_BE_READ,
        SubjectTickRestrictionCode.CHECKPOINT_DECISIONS_MUST_BE_READ,
        SubjectTickRestrictionCode.C04_MODE_CLAIM_MUST_BE_READ,
        SubjectTickRestrictionCode.C05_ACTION_CLAIM_MUST_BE_READ,
        SubjectTickRestrictionCode.AUTHORITY_ROLES_MUST_BE_READ,
    ]
    usability = SubjectTickUsabilityClass.USABLE_BOUNDED
    accepted = True
    reason = "bounded subject tick contour enforces phase contracts in runtime order"

    if state.revalidation_needed or state.final_execution_outcome == SubjectTickOutcome.REVALIDATE:
        usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "runtime contour requires selective revalidation before unrestricted continuation"
    if state.repair_needed or state.final_execution_outcome == SubjectTickOutcome.REPAIR:
        usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "runtime contour requires repair path before strong continuation"
    if state.final_execution_outcome == SubjectTickOutcome.HALT:
        accepted = False
        usability = SubjectTickUsabilityClass.BLOCKED
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "runtime contour halted by upstream legality/contract restrictions"

    return SubjectTickGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.tick_id}@{state.tick_index}",
    )
