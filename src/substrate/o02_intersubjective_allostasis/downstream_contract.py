from __future__ import annotations

from dataclasses import dataclass

from substrate.o02_intersubjective_allostasis.models import (
    O02IntersubjectiveAllostasisResult,
    O02InteractionMode,
    O02RepairPressureBand,
)


@dataclass(frozen=True, slots=True)
class O02AllostasisContractView:
    regulation_id: str
    tick_index: int
    interaction_mode: O02InteractionMode
    repair_pressure: O02RepairPressureBand
    clarification_threshold: float
    no_safe_regulation_claim: bool
    other_load_underconstrained: bool
    self_other_constraint_conflict: bool
    repair_sensitive_consumer_ready: bool
    boundary_preserving_consumer_ready: bool
    clarification_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_o02_first_slice_only: bool
    scope_o03_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class O02AllostasisConsumerView:
    regulation_id: str
    conservative_mode_only: bool
    repair_sensitive_detour_recommended: bool
    boundary_preservation_required: bool
    clarification_required: bool
    do_not_collapse_to_politeness: bool
    repair_sensitive_consumer_ready: bool
    boundary_preserving_consumer_ready: bool
    downstream_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_o02_intersubjective_allostasis_contract_view(
    result: O02IntersubjectiveAllostasisResult,
) -> O02AllostasisContractView:
    if not isinstance(result, O02IntersubjectiveAllostasisResult):
        raise TypeError(
            "derive_o02_intersubjective_allostasis_contract_view requires O02IntersubjectiveAllostasisResult"
        )
    return O02AllostasisContractView(
        regulation_id=result.state.regulation_id,
        tick_index=result.state.tick_index,
        interaction_mode=result.state.interaction_mode,
        repair_pressure=result.state.repair_pressure,
        clarification_threshold=result.state.clarification_threshold,
        no_safe_regulation_claim=result.state.no_safe_regulation_claim,
        other_load_underconstrained=result.state.other_load_underconstrained,
        self_other_constraint_conflict=result.state.self_other_constraint_conflict,
        repair_sensitive_consumer_ready=result.gate.repair_sensitive_consumer_ready,
        boundary_preserving_consumer_ready=result.gate.boundary_preserving_consumer_ready,
        clarification_ready=result.gate.clarification_ready,
        downstream_consumer_ready=result.gate.downstream_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_o02_first_slice_only=result.scope_marker.o02_first_slice_only,
        scope_o03_not_implemented=result.scope_marker.o03_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_o02_intersubjective_allostasis_consumer_view(
    result_or_view: O02IntersubjectiveAllostasisResult | O02AllostasisContractView,
) -> O02AllostasisConsumerView:
    view = (
        derive_o02_intersubjective_allostasis_contract_view(result_or_view)
        if isinstance(result_or_view, O02IntersubjectiveAllostasisResult)
        else result_or_view
    )
    if not isinstance(view, O02AllostasisContractView):
        raise TypeError(
            "derive_o02_intersubjective_allostasis_consumer_view requires O02IntersubjectiveAllostasisResult/O02AllostasisContractView"
        )
    conservative_mode_only = view.interaction_mode is O02InteractionMode.CONSERVATIVE_MODE_ONLY
    repair_sensitive_detour = (
        view.interaction_mode is O02InteractionMode.REPAIR_HEAVY
        and view.repair_pressure is O02RepairPressureBand.HIGH
    )
    boundary_required = (
        view.interaction_mode is O02InteractionMode.BOUNDARY_PROTECTIVE_MODE
        or view.self_other_constraint_conflict
    )
    clarification_required = (
        conservative_mode_only
        or repair_sensitive_detour
        or view.no_safe_regulation_claim
        or view.other_load_underconstrained
        or not view.clarification_ready
    )
    do_not_collapse_to_politeness = bool(
        view.self_other_constraint_conflict
        or view.no_safe_regulation_claim
        or view.other_load_underconstrained
        or "preserve_explicit_uncertainty" in view.restrictions
    )
    return O02AllostasisConsumerView(
        regulation_id=view.regulation_id,
        conservative_mode_only=conservative_mode_only,
        repair_sensitive_detour_recommended=repair_sensitive_detour,
        boundary_preservation_required=boundary_required,
        clarification_required=clarification_required,
        do_not_collapse_to_politeness=do_not_collapse_to_politeness,
        repair_sensitive_consumer_ready=view.repair_sensitive_consumer_ready,
        boundary_preserving_consumer_ready=view.boundary_preserving_consumer_ready,
        downstream_consumer_ready=view.downstream_consumer_ready,
        restrictions=view.restrictions,
        reason="o02 intersubjective allostasis consumer view",
    )


def require_o02_repair_sensitive_consumer_ready(
    result_or_view: O02IntersubjectiveAllostasisResult | O02AllostasisContractView,
) -> O02AllostasisConsumerView:
    view = derive_o02_intersubjective_allostasis_consumer_view(result_or_view)
    if not view.repair_sensitive_consumer_ready:
        raise PermissionError(
            "o02 repair-sensitive consumer requires lawful repair posture under bounded uncertainty"
        )
    return view


def require_o02_boundary_preserving_consumer_ready(
    result_or_view: O02IntersubjectiveAllostasisResult | O02AllostasisContractView,
) -> O02AllostasisConsumerView:
    view = derive_o02_intersubjective_allostasis_consumer_view(result_or_view)
    if not view.boundary_preserving_consumer_ready:
        raise PermissionError(
            "o02 boundary-preserving consumer requires preserved boundary posture"
        )
    return view
