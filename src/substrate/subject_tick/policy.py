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
        SubjectTickRestrictionCode.DOWNSTREAM_OBEDIENCE_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.DOWNSTREAM_OBEDIENCE_RESTRICTIONS_MUST_BE_ENFORCED,
        SubjectTickRestrictionCode.WORLD_SEAM_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.W_ENTRY_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.W_ENTRY_FORBIDDEN_CLAIMS_MUST_BE_READ,
        SubjectTickRestrictionCode.W_ENTRY_ADMISSION_CRITERIA_MUST_BE_READ,
        SubjectTickRestrictionCode.S_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.A_LINE_NORMALIZATION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.A_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
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
    if state.downstream_obedience_status in {
        "insufficient_authority_basis",
        "invalidated_upstream_surface",
        "blocked_by_survival_override",
    }:
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "downstream obedience contract rejected continue path despite local helper surfaces"
    if (
        state.world_require_grounded_transition
        and not state.world_entry_world_grounded_transition_admissible
    ):
        restrictions.append(
            SubjectTickRestrictionCode.WORLD_GROUNDED_TRANSITION_REQUIRES_WORLD_PRESENCE
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "world grounded transition requested but world seam grounding is unavailable"
    if (
        state.world_require_effect_feedback_for_success_claim
        and not state.world_entry_world_effect_success_admissible
    ):
        restrictions.append(
            SubjectTickRestrictionCode.WORLD_EFFECT_FEEDBACK_REQUIRED_FOR_SUCCESS_CLAIM
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "world effect feedback required for externally effected claim but effect observation is absent"
    if state.s_require_self_side_claim and not state.s_no_safe_self_claim:
        restrictions.append(SubjectTickRestrictionCode.S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS)
    if state.s_require_self_controlled_transition_claim:
        restrictions.append(SubjectTickRestrictionCode.S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED)
    if state.s_require_self_side_claim and state.s_no_safe_self_claim:
        restrictions.append(SubjectTickRestrictionCode.S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "self-side claim requested but s-minimal contour has no safe self attribution basis"
    if state.s_require_world_side_claim and state.s_no_safe_world_claim:
        restrictions.append(SubjectTickRestrictionCode.S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "world-side claim requested but s-minimal contour has no safe world attribution basis"
    if (
        state.s_require_self_controlled_transition_claim
        and state.s_attribution_class != "self_controlled_transition_claim"
    ):
        restrictions.append(SubjectTickRestrictionCode.S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "self-controlled transition requested but s-minimal contour lacks lawful controllability basis"
    if (
        state.s_strict_mixed_attribution_guard
        and "mixed_attribution_without_uncertainty_marking" in state.s_forbidden_shortcuts
        and (
            state.s_require_self_side_claim
            or state.s_require_world_side_claim
            or state.s_require_self_controlled_transition_claim
            or state.world_require_grounded_transition
            or state.world_require_effect_feedback_for_success_claim
        )
    ):
        restrictions.append(SubjectTickRestrictionCode.S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "mixed self/world attribution requires explicit uncertainty marking before continue"
    if state.a_require_capability_claim and not state.a_available_capability_claim_allowed:
        restrictions.append(SubjectTickRestrictionCode.A_CAPABILITY_CLAIM_REQUIRES_BASIS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "capability claim requested but a-line normalization marks basis as unavailable"
    if state.a_require_capability_claim and state.a_policy_conditioned_capability_present:
        restrictions.append(
            SubjectTickRestrictionCode.A_POLICY_GATED_CAPABILITY_REQUIRES_GATE
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "policy-conditioned capability cannot be consumed as free available capability"
    if state.a_require_capability_claim and state.a_underconstrained:
        restrictions.append(SubjectTickRestrictionCode.A_CAPABILITY_CLAIM_REQUIRES_BASIS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "capability claim requested while a-line substrate remains underconstrained"

    return SubjectTickGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.tick_id}@{state.tick_index}",
    )
