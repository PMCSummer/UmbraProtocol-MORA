from __future__ import annotations

from dataclasses import dataclass

from substrate.s05_multi_cause_attribution_factorization.models import (
    S05AttributionStatus,
    S05CauseClass,
    S05DownstreamRouteClass,
    S05MultiCauseAttributionResult,
)


@dataclass(frozen=True, slots=True)
class S05AttributionContractView:
    factorization_id: str
    tick_index: int
    latest_packet_id: str
    attribution_status: S05AttributionStatus
    revision_status: str
    scope_validity: str
    downstream_route_class: S05DownstreamRouteClass
    dominant_cause_classes: tuple[S05CauseClass, ...]
    unexplained_residual: float
    residual_class: str
    confidence: float
    temporal_misalignment_present: bool
    contamination_present: bool
    underdetermined_split: bool
    factorization_consumer_ready: bool
    learning_route_ready: bool
    no_binary_recollapse_required: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_s05_first_slice_only: bool
    scope_downstream_rollout_minimal: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class S05AttributionConsumerView:
    factorization_id: str
    can_consume_factorization: bool
    can_route_learning_attribution: bool
    do_not_collapse_to_single_cause: bool
    high_residual_or_underdetermined: bool
    downstream_route_class: S05DownstreamRouteClass
    dominant_cause_classes: tuple[S05CauseClass, ...]
    unexplained_residual: float
    restrictions: tuple[str, ...]
    reason: str


def derive_s05_multi_cause_attribution_contract_view(
    result: S05MultiCauseAttributionResult,
) -> S05AttributionContractView:
    if not isinstance(result, S05MultiCauseAttributionResult):
        raise TypeError(
            "derive_s05_multi_cause_attribution_contract_view requires S05MultiCauseAttributionResult"
        )
    packet = result.state.packets[-1]
    return S05AttributionContractView(
        factorization_id=result.state.factorization_id,
        tick_index=result.state.tick_index,
        latest_packet_id=result.state.latest_packet_id,
        attribution_status=packet.attribution_status,
        revision_status=packet.revision_status.value,
        scope_validity=packet.scope_validity.value,
        downstream_route_class=packet.downstream_route_class,
        dominant_cause_classes=result.state.dominant_cause_classes,
        unexplained_residual=result.state.unexplained_residual,
        residual_class=result.state.residual_class.value,
        confidence=packet.confidence,
        temporal_misalignment_present=result.state.temporal_misalignment_present,
        contamination_present=result.state.contamination_present,
        underdetermined_split=result.state.underdetermined_split,
        factorization_consumer_ready=result.gate.factorization_consumer_ready,
        learning_route_ready=result.gate.learning_route_ready,
        no_binary_recollapse_required=result.gate.no_binary_recollapse_required,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_s05_first_slice_only=result.scope_marker.s05_first_slice_only,
        scope_downstream_rollout_minimal=result.scope_marker.downstream_rollout_minimal,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_s05_multi_cause_attribution_consumer_view(
    result_or_view: S05MultiCauseAttributionResult | S05AttributionContractView,
) -> S05AttributionConsumerView:
    view = (
        derive_s05_multi_cause_attribution_contract_view(result_or_view)
        if isinstance(result_or_view, S05MultiCauseAttributionResult)
        else result_or_view
    )
    if not isinstance(view, S05AttributionContractView):
        raise TypeError(
            "derive_s05_multi_cause_attribution_consumer_view requires S05MultiCauseAttributionResult/S05AttributionContractView"
        )
    high_residual_or_underdetermined = bool(
        view.unexplained_residual >= 0.55
        or view.underdetermined_split
        or view.attribution_status
        in {
            S05AttributionStatus.INSUFFICIENT_FACTOR_BASIS,
            S05AttributionStatus.INCOMPATIBLE_CAUSE_CANDIDATES,
            S05AttributionStatus.RESIDUAL_TOO_LARGE,
            S05AttributionStatus.NO_CLEAN_FACTORIZATION_CLAIM,
        }
    )
    return S05AttributionConsumerView(
        factorization_id=view.factorization_id,
        can_consume_factorization=view.factorization_consumer_ready,
        can_route_learning_attribution=(
            view.learning_route_ready and not high_residual_or_underdetermined
        ),
        do_not_collapse_to_single_cause=view.no_binary_recollapse_required,
        high_residual_or_underdetermined=high_residual_or_underdetermined,
        downstream_route_class=view.downstream_route_class,
        dominant_cause_classes=view.dominant_cause_classes,
        unexplained_residual=view.unexplained_residual,
        restrictions=view.restrictions,
        reason="s05 bounded multi-cause attribution consumer view",
    )


def require_s05_factorized_consumer_ready(
    result_or_view: S05MultiCauseAttributionResult | S05AttributionContractView,
) -> S05AttributionConsumerView:
    view = derive_s05_multi_cause_attribution_consumer_view(result_or_view)
    if not view.can_consume_factorization:
        raise PermissionError(
            "s05 factorized consumer requires non-insufficient compatible attribution packet"
        )
    return view


def require_s05_learning_route_consumer_ready(
    result_or_view: S05MultiCauseAttributionResult | S05AttributionContractView,
) -> S05AttributionConsumerView:
    view = derive_s05_multi_cause_attribution_consumer_view(result_or_view)
    if not view.can_route_learning_attribution:
        raise PermissionError(
            "s05 learning-route consumer requires low-residual compatible attribution split"
        )
    return view
