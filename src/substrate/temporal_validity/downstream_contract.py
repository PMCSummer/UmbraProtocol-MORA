from __future__ import annotations

from dataclasses import dataclass

from substrate.temporal_validity.models import (
    C05RestrictionCode,
    TemporalCarryoverItemKind,
    TemporalValidityResult,
    TemporalValidityState,
    TemporalValidityStatus,
    TemporalValidityUsabilityClass,
)
from substrate.temporal_validity.policy import evaluate_temporal_validity_downstream_gate


@dataclass(frozen=True, slots=True)
class TemporalValidityContractView:
    validity_id: str
    stream_id: str
    reusable_item_ids: tuple[str, ...]
    provisional_item_ids: tuple[str, ...]
    revalidation_item_ids: tuple[str, ...]
    invalidated_item_ids: tuple[str, ...]
    expired_item_ids: tuple[str, ...]
    selective_scope_targets: tuple[str, ...]
    provisional_carry_only: bool
    dependency_graph_incomplete: bool
    insufficient_basis_for_revalidation: bool
    selective_scope_uncertain: bool
    gate_accepted: bool
    restrictions: tuple[C05RestrictionCode, ...]
    usability_class: TemporalValidityUsabilityClass
    requires_restrictions_read: bool
    reason: str


def derive_temporal_validity_contract_view(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
) -> TemporalValidityContractView:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "derive_temporal_validity_contract_view requires TemporalValidityState/TemporalValidityResult"
        )
    gate = evaluate_temporal_validity_downstream_gate(state)
    return TemporalValidityContractView(
        validity_id=state.validity_id,
        stream_id=state.stream_id,
        reusable_item_ids=state.reusable_item_ids,
        provisional_item_ids=state.provisional_item_ids,
        revalidation_item_ids=state.revalidation_item_ids,
        invalidated_item_ids=state.invalidated_item_ids,
        expired_item_ids=state.expired_item_ids,
        selective_scope_targets=state.selective_scope_targets,
        provisional_carry_only=state.provisional_carry_only,
        dependency_graph_incomplete=state.dependency_graph_incomplete,
        insufficient_basis_for_revalidation=state.insufficient_basis_for_revalidation,
        selective_scope_uncertain=state.selective_scope_uncertain,
        gate_accepted=gate.accepted,
        restrictions=gate.restrictions,
        usability_class=gate.usability_class,
        requires_restrictions_read=True,
        reason="contract requires typed c05 temporal validity surfaces to be read",
    )


def choose_temporal_reuse_execution_mode(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
) -> str:
    view = derive_temporal_validity_contract_view(temporal_validity_state_or_result)
    if not view.gate_accepted or view.usability_class == TemporalValidityUsabilityClass.BLOCKED:
        return "halt_reuse_and_rebuild_scope"
    if view.revalidation_item_ids:
        if view.selective_scope_targets and len(view.selective_scope_targets) < max(
            len(view.reusable_item_ids) + len(view.provisional_item_ids) + len(view.revalidation_item_ids),
            1,
        ):
            return "run_selective_revalidation"
        return "run_bounded_revalidation"
    if view.provisional_carry_only:
        return "reuse_with_provisional_limits"
    if view.provisional_item_ids and not view.reusable_item_ids:
        return "reuse_with_provisional_limits"
    if view.reusable_item_ids:
        return "reuse_valid_only"
    return "suspend_until_revalidation_basis"


def select_reusable_items(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
    *,
    include_provisional: bool = False,
) -> tuple[str, ...]:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "select_reusable_items requires TemporalValidityState/TemporalValidityResult"
        )
    gate = evaluate_temporal_validity_downstream_gate(state)
    if not gate.accepted:
        return ()
    if include_provisional:
        return tuple(dict.fromkeys((*state.reusable_item_ids, *state.provisional_item_ids)))
    return state.reusable_item_ids


def select_revalidation_targets(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
) -> tuple[str, ...]:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "select_revalidation_targets requires TemporalValidityState/TemporalValidityResult"
        )
    return state.selective_scope_targets


def can_reuse_item(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
    item_id: str,
    *,
    allow_provisional: bool = False,
) -> bool:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError("can_reuse_item requires TemporalValidityState/TemporalValidityResult")

    for item in state.items:
        if item.item_id != item_id:
            continue
        if item.current_validity_status == TemporalValidityStatus.STILL_VALID:
            return True
        if allow_provisional and item.current_validity_status == TemporalValidityStatus.CONDITIONALLY_CARRIED:
            return True
        return False
    return False


def can_continue_mode_hold(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
    *,
    allow_provisional: bool = False,
) -> bool:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "can_continue_mode_hold requires TemporalValidityState/TemporalValidityResult"
        )
    candidates = tuple(
        item.item_id
        for item in state.items
        if item.item_kind == TemporalCarryoverItemKind.MODE_HOLD_PERMISSION
    )
    return any(
        can_reuse_item(state, item_id, allow_provisional=allow_provisional)
        for item_id in candidates
    )


def can_revisit_with_basis(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
    *,
    allow_provisional: bool = False,
) -> bool:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "can_revisit_with_basis requires TemporalValidityState/TemporalValidityResult"
        )
    candidates = tuple(
        item.item_id
        for item in state.items
        if item.item_kind == TemporalCarryoverItemKind.REVISIT_BASIS
    )
    return any(
        can_reuse_item(state, item_id, allow_provisional=allow_provisional)
        for item_id in candidates
    )


def can_open_branch_access(
    temporal_validity_state_or_result: TemporalValidityState | TemporalValidityResult,
) -> bool:
    if isinstance(temporal_validity_state_or_result, TemporalValidityResult):
        state = temporal_validity_state_or_result.state
    elif isinstance(temporal_validity_state_or_result, TemporalValidityState):
        state = temporal_validity_state_or_result
    else:
        raise TypeError(
            "can_open_branch_access requires TemporalValidityState/TemporalValidityResult"
        )
    candidates = tuple(
        item.item_id
        for item in state.items
        if item.item_kind == TemporalCarryoverItemKind.BRANCH_ACCESS_GATE
    )
    return any(can_reuse_item(state, item_id, allow_provisional=False) for item_id in candidates)
