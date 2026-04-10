from __future__ import annotations

from dataclasses import dataclass

from substrate.s01_efference_copy.models import S01EfferenceCopyResult


@dataclass(frozen=True, slots=True)
class S01ContractView:
    efference_id: str
    tick_index: int
    pending_predictions_count: int
    comparisons_count: int
    latest_comparison_status: str | None
    comparison_ready: bool
    prediction_validity_ready: bool
    unexpected_change_detected: bool
    comparison_blocked_by_contamination: bool
    stale_prediction_detected: bool
    strong_self_attribution_allowed: bool
    no_post_hoc_prediction_fabrication: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_s01_first_slice_only: bool
    scope_s02_implemented: bool
    scope_s03_implemented: bool
    scope_s04_implemented: bool
    scope_s05_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class S01ComparisonConsumerView:
    efference_id: str
    comparison_ready: bool
    prediction_validity_ready: bool
    unexpected_change_detected: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_s01_contract_view(result: S01EfferenceCopyResult) -> S01ContractView:
    if not isinstance(result, S01EfferenceCopyResult):
        raise TypeError("derive_s01_contract_view requires S01EfferenceCopyResult")
    return S01ContractView(
        efference_id=result.state.efference_id,
        tick_index=result.state.tick_index,
        pending_predictions_count=len(result.state.pending_predictions),
        comparisons_count=len(result.state.comparisons),
        latest_comparison_status=(
            None
            if result.state.latest_comparison_status is None
            else result.state.latest_comparison_status.value
        ),
        comparison_ready=result.gate.comparison_ready,
        prediction_validity_ready=result.gate.prediction_validity_ready,
        unexpected_change_detected=result.gate.unexpected_change_detected,
        comparison_blocked_by_contamination=result.state.comparison_blocked_by_contamination,
        stale_prediction_detected=result.state.stale_prediction_detected,
        strong_self_attribution_allowed=result.state.strong_self_attribution_allowed,
        no_post_hoc_prediction_fabrication=result.gate.no_post_hoc_prediction_fabrication,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_s01_first_slice_only=result.scope_marker.s01_first_slice_only,
        scope_s02_implemented=result.scope_marker.s02_implemented,
        scope_s03_implemented=result.scope_marker.s03_implemented,
        scope_s04_implemented=result.scope_marker.s04_implemented,
        scope_s05_implemented=result.scope_marker.s05_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_s01_comparison_consumer_view(
    result_or_view: S01EfferenceCopyResult | S01ContractView,
) -> S01ComparisonConsumerView:
    view = (
        derive_s01_contract_view(result_or_view)
        if isinstance(result_or_view, S01EfferenceCopyResult)
        else result_or_view
    )
    if not isinstance(view, S01ContractView):
        raise TypeError(
            "derive_s01_comparison_consumer_view requires S01EfferenceCopyResult/S01ContractView"
        )
    return S01ComparisonConsumerView(
        efference_id=view.efference_id,
        comparison_ready=view.comparison_ready,
        prediction_validity_ready=view.prediction_validity_ready,
        unexpected_change_detected=view.unexpected_change_detected,
        restrictions=view.restrictions,
        reason="s01 bounded consumer view for intended-vs-observed comparator",
    )


def require_s01_comparison_consumer_ready(
    result_or_view: S01EfferenceCopyResult | S01ContractView,
) -> S01ComparisonConsumerView:
    view = derive_s01_comparison_consumer_view(result_or_view)
    if not view.comparison_ready:
        raise PermissionError(
            "s01 comparison consumer requires at least one lawful intended-vs-observed comparison entry"
        )
    return view


def require_s01_prediction_validity_ready(
    result_or_view: S01EfferenceCopyResult | S01ContractView,
) -> S01ComparisonConsumerView:
    view = derive_s01_comparison_consumer_view(result_or_view)
    if not view.prediction_validity_ready:
        raise PermissionError(
            "s01 prediction validity consumer requires non-stale non-contaminated comparison surface"
        )
    return view
