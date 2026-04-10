from __future__ import annotations

from dataclasses import dataclass

from substrate.s02_prediction_boundary.models import S02PredictionBoundaryResult


@dataclass(frozen=True, slots=True)
class S02BoundaryContractView:
    boundary_id: str
    tick_index: int
    active_boundary_status: str
    seam_entries: tuple[tuple[str, str, float, float, float, float, float], ...]
    boundary_uncertain: bool
    insufficient_coverage: bool
    no_clean_seam_claim: bool
    boundary_consumer_ready: bool
    controllability_consumer_ready: bool
    mixed_source_consumer_ready: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_s02_first_slice_only: bool
    scope_s03_implemented: bool
    scope_s04_implemented: bool
    scope_s05_implemented: bool
    scope_full_self_model_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class S02BoundaryConsumerView:
    boundary_id: str
    can_consume_boundary: bool
    can_consume_controllability: bool
    can_consume_mixed_source: bool
    active_boundary_status: str
    restrictions: tuple[str, ...]
    reason: str


def derive_s02_boundary_contract_view(
    result: S02PredictionBoundaryResult,
) -> S02BoundaryContractView:
    if not isinstance(result, S02PredictionBoundaryResult):
        raise TypeError("derive_s02_boundary_contract_view requires S02PredictionBoundaryResult")
    return S02BoundaryContractView(
        boundary_id=result.state.boundary_id,
        tick_index=result.state.tick_index,
        active_boundary_status=result.state.active_boundary_status.value,
        seam_entries=tuple(
            (
                item.seam_entry_id,
                item.channel_or_effect_class,
                item.controllability_estimate,
                item.prediction_reliability_estimate,
                item.external_dominance_estimate,
                item.mixed_source_score,
                item.boundary_confidence,
            )
            for item in result.state.seam_entries
        ),
        boundary_uncertain=result.state.boundary_uncertain,
        insufficient_coverage=result.state.insufficient_coverage,
        no_clean_seam_claim=result.state.no_clean_seam_claim,
        boundary_consumer_ready=result.gate.boundary_consumer_ready,
        controllability_consumer_ready=result.gate.controllability_consumer_ready,
        mixed_source_consumer_ready=result.gate.mixed_source_consumer_ready,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_s02_first_slice_only=result.scope_marker.s02_first_slice_only,
        scope_s03_implemented=result.scope_marker.s03_implemented,
        scope_s04_implemented=result.scope_marker.s04_implemented,
        scope_s05_implemented=result.scope_marker.s05_implemented,
        scope_full_self_model_implemented=result.scope_marker.full_self_model_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_s02_boundary_consumer_view(
    result_or_view: S02PredictionBoundaryResult | S02BoundaryContractView,
) -> S02BoundaryConsumerView:
    view = (
        derive_s02_boundary_contract_view(result_or_view)
        if isinstance(result_or_view, S02PredictionBoundaryResult)
        else result_or_view
    )
    if not isinstance(view, S02BoundaryContractView):
        raise TypeError(
            "derive_s02_boundary_consumer_view requires S02PredictionBoundaryResult/S02BoundaryContractView"
        )
    return S02BoundaryConsumerView(
        boundary_id=view.boundary_id,
        can_consume_boundary=view.boundary_consumer_ready,
        can_consume_controllability=view.controllability_consumer_ready,
        can_consume_mixed_source=view.mixed_source_consumer_ready,
        active_boundary_status=view.active_boundary_status,
        restrictions=view.restrictions,
        reason="s02 pre-rt01 consumer view over bounded prediction boundary seam",
    )


def require_s02_boundary_consumer_ready(
    result_or_view: S02PredictionBoundaryResult | S02BoundaryContractView,
) -> S02BoundaryConsumerView:
    view = derive_s02_boundary_consumer_view(result_or_view)
    if not view.can_consume_boundary:
        raise PermissionError(
            "s02 boundary consumer requires clean non-stale prediction boundary seam"
        )
    return view


def require_s02_controllability_consumer_ready(
    result_or_view: S02PredictionBoundaryResult | S02BoundaryContractView,
) -> S02BoundaryConsumerView:
    view = derive_s02_boundary_consumer_view(result_or_view)
    if not view.can_consume_controllability:
        raise PermissionError(
            "s02 controllability consumer requires controllability basis distinct from mere predictability"
        )
    return view


def require_s02_mixed_source_consumer_ready(
    result_or_view: S02PredictionBoundaryResult | S02BoundaryContractView,
) -> S02BoundaryConsumerView:
    view = derive_s02_boundary_consumer_view(result_or_view)
    if not view.can_consume_mixed_source:
        raise PermissionError(
            "s02 mixed-source consumer requires explicit mixed-source boundary preservation"
        )
    return view
