from __future__ import annotations

from dataclasses import dataclass

from substrate.o01_other_entity_model.models import O01AttributionStatus, O01OtherEntityModelResult


@dataclass(frozen=True, slots=True)
class O01EntityModelContractView:
    model_id: str
    tick_index: int
    attribution_status: O01AttributionStatus
    current_user_entity_id: str | None
    current_user_model_ready: bool
    entity_individuation_ready: bool
    clarification_ready: bool
    downstream_consumer_ready: bool
    entity_count: int
    competing_entity_models: tuple[str, ...]
    no_safe_state_claim: bool
    perspective_underconstrained: bool
    temporary_only_not_stable: bool
    knowledge_boundary_unknown: bool
    projection_guard_triggered: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_o01_first_slice_only: bool
    scope_o02_o03_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class O01EntityModelConsumerView:
    model_id: str
    can_consume_current_user_model: bool
    clarification_required: bool
    expectation_management_ready: bool
    competing_entity_models_present: bool
    no_safe_state_claim: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_o01_other_entity_model_contract_view(
    result: O01OtherEntityModelResult,
) -> O01EntityModelContractView:
    if not isinstance(result, O01OtherEntityModelResult):
        raise TypeError(
            "derive_o01_other_entity_model_contract_view requires O01OtherEntityModelResult"
        )
    return O01EntityModelContractView(
        model_id=result.state.model_id,
        tick_index=result.state.tick_index,
        attribution_status=result.attribution_status,
        current_user_entity_id=result.state.current_user_entity_id,
        current_user_model_ready=result.gate.current_user_model_ready,
        entity_individuation_ready=result.gate.entity_individuation_ready,
        clarification_ready=result.gate.clarification_ready,
        downstream_consumer_ready=result.gate.downstream_consumer_ready,
        entity_count=len(result.state.entities),
        competing_entity_models=result.state.competing_entity_models,
        no_safe_state_claim=result.state.no_safe_state_claim,
        perspective_underconstrained=result.state.perspective_underconstrained,
        temporary_only_not_stable=result.state.temporary_only_not_stable,
        knowledge_boundary_unknown=result.state.knowledge_boundary_unknown,
        projection_guard_triggered=result.state.projection_guard_triggered,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_o01_first_slice_only=result.scope_marker.o01_first_slice_only,
        scope_o02_o03_not_implemented=result.scope_marker.o02_o03_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_o01_other_entity_model_consumer_view(
    result_or_view: O01OtherEntityModelResult | O01EntityModelContractView,
) -> O01EntityModelConsumerView:
    view = (
        derive_o01_other_entity_model_contract_view(result_or_view)
        if isinstance(result_or_view, O01OtherEntityModelResult)
        else result_or_view
    )
    if not isinstance(view, O01EntityModelContractView):
        raise TypeError(
            "derive_o01_other_entity_model_consumer_view requires O01OtherEntityModelResult/O01EntityModelContractView"
        )
    return O01EntityModelConsumerView(
        model_id=view.model_id,
        can_consume_current_user_model=(
            view.current_user_model_ready
            and view.entity_individuation_ready
            and not view.no_safe_state_claim
            and not view.competing_entity_models
        ),
        clarification_required=(
            not view.clarification_ready
            or view.perspective_underconstrained
            or view.no_safe_state_claim
            or bool(view.competing_entity_models)
        ),
        expectation_management_ready=(
            view.current_user_model_ready
            and not view.temporary_only_not_stable
            and not view.knowledge_boundary_unknown
        ),
        competing_entity_models_present=bool(view.competing_entity_models),
        no_safe_state_claim=view.no_safe_state_claim,
        restrictions=view.restrictions,
        reason="o01 other-entity consumer view",
    )


def require_o01_entity_consumer_ready(
    result_or_view: O01OtherEntityModelResult | O01EntityModelContractView,
) -> O01EntityModelConsumerView:
    view = derive_o01_other_entity_model_consumer_view(result_or_view)
    if not view.can_consume_current_user_model:
        raise PermissionError(
            "o01 entity consumer requires individuated current-user model with safe bounded claims"
        )
    return view


def require_o01_clarification_consumer_ready(
    result_or_view: O01OtherEntityModelResult | O01EntityModelContractView,
) -> O01EntityModelConsumerView:
    view = derive_o01_other_entity_model_consumer_view(result_or_view)
    if view.clarification_required:
        raise PermissionError(
            "o01 clarification consumer requires non-underconstrained perspective and no competing referent model"
        )
    return view
