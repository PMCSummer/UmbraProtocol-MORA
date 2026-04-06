from __future__ import annotations

from substrate.temporal_validity.models import (
    C05RestrictionCode,
    TemporalValidityGateDecision,
    TemporalValidityResult,
    TemporalValidityState,
    TemporalValidityStatus,
    TemporalValidityUsabilityClass,
)


def evaluate_temporal_validity_downstream_gate(
    temporal_validity_state_or_result: object,
) -> TemporalValidityGateDecision:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "evaluate_temporal_validity_downstream_gate requires TemporalValidityState/TemporalValidityResult"
        )

    restrictions: list[C05RestrictionCode] = [
        C05RestrictionCode.TEMPORAL_VALIDITY_STATE_MUST_BE_READ,
        C05RestrictionCode.ITEM_VALIDITY_STATUS_MUST_BE_READ,
        C05RestrictionCode.ITEM_DEPENDENCY_SET_MUST_BE_READ,
        C05RestrictionCode.ITEM_REVALIDATION_SCOPE_MUST_BE_READ,
        C05RestrictionCode.ITEM_INVALIDATION_TRIGGERS_MUST_BE_READ,
        C05RestrictionCode.SELECTIVE_REVALIDATION_TARGETS_MUST_BE_READ,
        C05RestrictionCode.PROVISIONAL_CARRY_MUST_BE_READ,
        C05RestrictionCode.DEPENDENCY_PROPAGATION_MUST_BE_READ,
        C05RestrictionCode.NO_TTL_ONLY_SHORTCUT,
        C05RestrictionCode.NO_BLANKET_RESET_SHORTCUT,
        C05RestrictionCode.NO_BLANKET_REUSE_SHORTCUT,
        C05RestrictionCode.NO_GLOBAL_RECOMPUTE_SHORTCUT,
    ]
    accepted = bool(state.items)
    usability = TemporalValidityUsabilityClass.USABLE_BOUNDED
    reason = "typed c05 temporal validity state available for bounded selective revalidation"

    degraded = False
    blocked = False

    if state.insufficient_basis_for_revalidation:
        restrictions.append(
            C05RestrictionCode.INSUFFICIENT_BASIS_FOR_REVALIDATION_PRESENT
        )
        degraded = True
    if state.provisional_carry_only:
        restrictions.append(C05RestrictionCode.PROVISIONAL_CARRY_ONLY_PRESENT)
        degraded = True
    if state.dependency_graph_incomplete:
        restrictions.append(C05RestrictionCode.DEPENDENCY_GRAPH_INCOMPLETE_PRESENT)
        degraded = True
    if state.invalidation_possible_but_unproven:
        restrictions.append(
            C05RestrictionCode.INVALIDATION_POSSIBLE_BUT_UNPROVEN_PRESENT
        )
        degraded = True
    if state.selective_scope_uncertain:
        restrictions.append(C05RestrictionCode.SELECTIVE_SCOPE_UNCERTAIN_PRESENT)
        degraded = True
    if state.no_safe_reuse_item_ids:
        restrictions.append(C05RestrictionCode.NO_SAFE_REUSE_CLAIM_PRESENT)
        degraded = True

    any_invalidating = any(
        item.current_validity_status
        in {
            TemporalValidityStatus.INVALIDATED,
            TemporalValidityStatus.EXPIRED,
            TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
            TemporalValidityStatus.NO_SAFE_REUSE_CLAIM,
        }
        for item in state.items
    )
    if any_invalidating:
        degraded = True

    if not state.reusable_item_ids and not state.provisional_item_ids and state.items:
        blocked = True

    if blocked:
        accepted = False
        usability = TemporalValidityUsabilityClass.BLOCKED
        restrictions.append(C05RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "no reusable temporal items remain; downstream must halt strong reuse"
    elif degraded:
        usability = TemporalValidityUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(C05RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "temporal validity is degraded and requires bounded selective revalidation"

    if not state.items:
        accepted = False
        usability = TemporalValidityUsabilityClass.BLOCKED
        restrictions.append(C05RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "no typed temporal validity items available"

    return TemporalValidityGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.validity_id}@{state.source_stream_sequence_index}",
    )
