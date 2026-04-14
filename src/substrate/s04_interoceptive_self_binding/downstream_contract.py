from __future__ import annotations

from dataclasses import dataclass

from substrate.s04_interoceptive_self_binding.models import (
    S04BindingStatus,
    S04InteroceptiveSelfBindingResult,
)


@dataclass(frozen=True, slots=True)
class S04SelfBindingContractView:
    binding_id: str
    tick_index: int
    strong_core_channels: tuple[str, ...]
    weak_or_peripheral_channels: tuple[str, ...]
    contested_channels: tuple[str, ...]
    recently_unbound_channels: tuple[str, ...]
    no_stable_self_core_claim: bool
    strongest_binding_strength: float
    contamination_detected: bool
    rebinding_event: bool
    stale_binding_drop_count: int
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_s04_first_slice_only: bool
    scope_s05_implemented: bool
    scope_full_self_model_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class S04SelfBindingConsumerView:
    binding_id: str
    can_consume_stable_core: bool
    can_consume_contested: bool
    can_consume_no_stable_core: bool
    strong_core_channels: tuple[str, ...]
    weak_or_peripheral_channels: tuple[str, ...]
    contested_channels: tuple[str, ...]
    no_stable_self_core_claim: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_s04_interoceptive_self_binding_contract_view(
    result: S04InteroceptiveSelfBindingResult,
) -> S04SelfBindingContractView:
    if not isinstance(result, S04InteroceptiveSelfBindingResult):
        raise TypeError(
            "derive_s04_interoceptive_self_binding_contract_view requires S04InteroceptiveSelfBindingResult"
        )
    return S04SelfBindingContractView(
        binding_id=result.state.binding_id,
        tick_index=result.state.tick_index,
        strong_core_channels=result.state.core_bound_channels,
        weak_or_peripheral_channels=result.state.peripheral_or_weakly_bound_channels,
        contested_channels=result.state.contested_channels,
        recently_unbound_channels=result.state.recently_unbound_channels,
        no_stable_self_core_claim=result.state.no_stable_self_core_claim,
        strongest_binding_strength=result.state.strongest_binding_strength,
        contamination_detected=result.state.contamination_detected,
        rebinding_event=result.state.rebinding_event,
        stale_binding_drop_count=result.state.stale_binding_drop_count,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_s04_first_slice_only=result.scope_marker.s04_first_slice_only,
        scope_s05_implemented=result.scope_marker.s05_implemented,
        scope_full_self_model_implemented=result.scope_marker.full_self_model_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_s04_interoceptive_self_binding_consumer_view(
    result_or_view: S04InteroceptiveSelfBindingResult | S04SelfBindingContractView,
) -> S04SelfBindingConsumerView:
    view = (
        derive_s04_interoceptive_self_binding_contract_view(result_or_view)
        if isinstance(result_or_view, S04InteroceptiveSelfBindingResult)
        else result_or_view
    )
    if not isinstance(view, S04SelfBindingContractView):
        raise TypeError(
            "derive_s04_interoceptive_self_binding_consumer_view requires S04InteroceptiveSelfBindingResult/S04SelfBindingContractView"
        )
    return S04SelfBindingConsumerView(
        binding_id=view.binding_id,
        can_consume_stable_core=(
            len(view.strong_core_channels) > 0 and not view.no_stable_self_core_claim
        ),
        can_consume_contested=len(view.contested_channels) > 0,
        can_consume_no_stable_core=view.no_stable_self_core_claim,
        strong_core_channels=view.strong_core_channels,
        weak_or_peripheral_channels=view.weak_or_peripheral_channels,
        contested_channels=view.contested_channels,
        no_stable_self_core_claim=view.no_stable_self_core_claim,
        restrictions=view.restrictions,
        reason="s04 bounded self-binding consumer view",
    )


def require_s04_stable_core_consumer_ready(
    result_or_view: S04InteroceptiveSelfBindingResult | S04SelfBindingContractView,
) -> S04SelfBindingConsumerView:
    view = derive_s04_interoceptive_self_binding_consumer_view(result_or_view)
    if not view.can_consume_stable_core:
        raise PermissionError(
            "s04 stable-core consumer requires convergent privileged self-binding core"
        )
    return view


def require_s04_contested_consumer_ready(
    result_or_view: S04InteroceptiveSelfBindingResult | S04SelfBindingContractView,
) -> S04SelfBindingConsumerView:
    view = derive_s04_interoceptive_self_binding_consumer_view(result_or_view)
    if not view.can_consume_contested:
        raise PermissionError(
            "s04 contested-consumer requires explicit contested/mixed binding channels"
        )
    return view


def require_s04_no_stable_core_consumer_ready(
    result_or_view: S04InteroceptiveSelfBindingResult | S04SelfBindingContractView,
) -> S04SelfBindingConsumerView:
    view = derive_s04_interoceptive_self_binding_consumer_view(result_or_view)
    if not view.can_consume_no_stable_core:
        raise PermissionError(
            "s04 no-stable-core consumer requires explicit no_stable_self_core_claim status"
        )
    return view


def s04_binding_status_histogram(
    result_or_view: S04InteroceptiveSelfBindingResult | S04SelfBindingContractView,
) -> dict[str, int]:
    if isinstance(result_or_view, S04InteroceptiveSelfBindingResult):
        entries = result_or_view.state.entries
    else:
        raise TypeError(
            "s04_binding_status_histogram requires S04InteroceptiveSelfBindingResult for entry-level histogram"
        )
    histogram: dict[str, int] = {item.value: 0 for item in S04BindingStatus}
    for entry in entries:
        histogram[entry.binding_status.value] = histogram.get(entry.binding_status.value, 0) + 1
    return histogram
