from __future__ import annotations

from dataclasses import dataclass

from substrate.a04_external_affordance_binding.models import (
    A04ExternalAffordanceBindingResult,
)


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceContractView:
    a04_binding_count: int
    a04_contested_count: int
    a04_blocked_count: int
    a04_revoked_count: int
    a04_authority_missing_count: int
    a04_object_overclaim_blocked_count: int
    a04_consumer_ready: bool
    binding_packet_consumer_ready: bool
    authority_path_consumer_ready: bool
    downstream_readiness_status: str
    required_restrictions: tuple[str, ...]
    scope: str
    scope_frontier_only: bool
    scope_narrow_slice_only: bool
    scope_staged_scaffold_only: bool
    scope_entity_binding_not_object_perception: bool
    scope_no_map_wide_claim: bool
    scope_no_execution_claim: bool
    scope_no_policy_selection_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class A04ExternalAffordanceConsumerView:
    a04_binding_count: int
    a04_contested_count: int
    a04_blocked_count: int
    a04_revoked_count: int
    a04_authority_missing_count: int
    a04_object_overclaim_blocked_count: int
    a04_consumer_ready: bool
    binding_packet_consumer_ready: bool
    authority_path_consumer_ready: bool
    downstream_readiness_status: str
    required_restrictions: tuple[str, ...]
    reason: str


def derive_a04_external_affordance_contract_view(
    result: A04ExternalAffordanceBindingResult,
) -> A04ExternalAffordanceContractView:
    if not isinstance(result, A04ExternalAffordanceBindingResult):
        raise TypeError(
            "derive_a04_external_affordance_contract_view requires A04ExternalAffordanceBindingResult"
        )
    scope = result.scope_marker
    gate = result.gate
    telemetry = result.telemetry
    return A04ExternalAffordanceContractView(
        a04_binding_count=telemetry.a04_binding_count,
        a04_contested_count=telemetry.a04_contested_count,
        a04_blocked_count=telemetry.a04_blocked_count,
        a04_revoked_count=telemetry.a04_revoked_count,
        a04_authority_missing_count=telemetry.a04_authority_missing_count,
        a04_object_overclaim_blocked_count=telemetry.a04_object_overclaim_blocked_count,
        a04_consumer_ready=telemetry.a04_consumer_ready,
        binding_packet_consumer_ready=gate.binding_packet_consumer_ready,
        authority_path_consumer_ready=gate.authority_path_consumer_ready,
        downstream_readiness_status=gate.downstream_readiness_status.value,
        required_restrictions=gate.required_restrictions,
        scope=scope.scope,
        scope_frontier_only=scope.frontier_only,
        scope_narrow_slice_only=scope.narrow_slice_only,
        scope_staged_scaffold_only=scope.staged_scaffold_only,
        scope_entity_binding_not_object_perception=scope.entity_binding_not_object_perception,
        scope_no_map_wide_claim=scope.no_map_wide_claim,
        scope_no_execution_claim=scope.no_execution_claim,
        scope_no_policy_selection_claim=scope.no_policy_selection_claim,
        scope_reason=scope.reason,
        reason=result.reason,
    )


def derive_a04_external_affordance_consumer_view(
    result_or_view: A04ExternalAffordanceBindingResult | A04ExternalAffordanceContractView,
) -> A04ExternalAffordanceConsumerView:
    view = (
        derive_a04_external_affordance_contract_view(result_or_view)
        if isinstance(result_or_view, A04ExternalAffordanceBindingResult)
        else result_or_view
    )
    if not isinstance(view, A04ExternalAffordanceContractView):
        raise TypeError(
            "derive_a04_external_affordance_consumer_view requires A04ExternalAffordanceBindingResult/A04ExternalAffordanceContractView"
        )
    return A04ExternalAffordanceConsumerView(
        a04_binding_count=view.a04_binding_count,
        a04_contested_count=view.a04_contested_count,
        a04_blocked_count=view.a04_blocked_count,
        a04_revoked_count=view.a04_revoked_count,
        a04_authority_missing_count=view.a04_authority_missing_count,
        a04_object_overclaim_blocked_count=view.a04_object_overclaim_blocked_count,
        a04_consumer_ready=view.a04_consumer_ready,
        binding_packet_consumer_ready=view.binding_packet_consumer_ready,
        authority_path_consumer_ready=view.authority_path_consumer_ready,
        downstream_readiness_status=view.downstream_readiness_status,
        required_restrictions=view.required_restrictions,
        reason="a04 external-affordance consumer view",
    )


def require_a04_binding_packet_consumer(
    result_or_view: A04ExternalAffordanceBindingResult | A04ExternalAffordanceContractView,
) -> A04ExternalAffordanceConsumerView:
    view = derive_a04_external_affordance_consumer_view(result_or_view)
    if not view.binding_packet_consumer_ready:
        raise PermissionError("a04 binding-packet consumer requires admitted/provisional bindings")
    return view


def require_a04_authority_path_consumer(
    result_or_view: A04ExternalAffordanceBindingResult | A04ExternalAffordanceContractView,
) -> A04ExternalAffordanceConsumerView:
    view = derive_a04_external_affordance_consumer_view(result_or_view)
    if not view.authority_path_consumer_ready:
        raise PermissionError("a04 authority-path consumer requires preserved authority-tagged source path")
    return view
