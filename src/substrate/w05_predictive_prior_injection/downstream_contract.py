from __future__ import annotations

from dataclasses import dataclass

from substrate.w05_predictive_prior_injection.models import (
    W05DownstreamRoutingPermissionPacket,
    W05ResultBundle,
)


@dataclass(frozen=True, slots=True)
class W05ContractView:
    signal_stack_count: int
    prediction_use_count: int
    mismatch_count: int
    ambiguous_mismatch_count: int
    revalidate_route_count: int
    escalate_route_count: int
    abstain_count: int
    constitutional_guard_count: int
    protected_target_block_count: int
    must_not_execute_update_count: int
    permitted_channel_block_count: int
    channel_collapse_block_count: int
    consumer_ready: bool
    no_clean_routing: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class W05ConsumerPacket:
    routing_id: str
    may_consider_update: bool
    may_request_learning: bool
    may_adjust_interpretation: bool
    may_adjust_policy_hint: bool
    must_revalidate: bool
    must_escalate: bool
    must_abstain: bool
    must_not_execute_update: bool
    must_preserve_desired_predicted_observed_permitted_separation: bool
    must_preserve_guardrails: bool
    protected_target_blocked: bool
    prohibited_uses: tuple[str, ...]
    preserved_guardrails: tuple[str, ...]
    execution_authorization_granted: bool


def derive_w05_contract_view(result: W05ResultBundle) -> W05ContractView:
    if not isinstance(result, W05ResultBundle):
        raise TypeError("derive_w05_contract_view requires W05ResultBundle")
    return W05ContractView(
        signal_stack_count=result.telemetry.signal_stack_count,
        prediction_use_count=result.telemetry.prediction_use_count,
        mismatch_count=result.telemetry.mismatch_count,
        ambiguous_mismatch_count=result.telemetry.ambiguous_mismatch_count,
        revalidate_route_count=result.telemetry.revalidate_route_count,
        escalate_route_count=result.telemetry.escalate_route_count,
        abstain_count=result.telemetry.abstain_count,
        constitutional_guard_count=result.telemetry.constitutional_guard_count,
        protected_target_block_count=result.telemetry.protected_target_block_count,
        must_not_execute_update_count=result.telemetry.must_not_execute_update_count,
        permitted_channel_block_count=result.telemetry.permitted_channel_block_count,
        channel_collapse_block_count=result.telemetry.channel_collapse_block_count,
        consumer_ready=result.gate.consumer_ready,
        no_clean_routing=result.gate.no_clean_routing,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        reason=result.reason,
    )


def derive_w05_consumer_packets(result: W05ResultBundle) -> tuple[W05ConsumerPacket, ...]:
    if not isinstance(result, W05ResultBundle):
        raise TypeError("derive_w05_consumer_packets requires W05ResultBundle")
    return tuple(_to_consumer(item) for item in result.downstream_routing_packets)


def require_w05_routing_consumer(result_or_view: W05ResultBundle | W05ContractView) -> W05ContractView:
    view = derive_w05_contract_view(result_or_view) if isinstance(result_or_view, W05ResultBundle) else result_or_view
    if not isinstance(view, W05ContractView):
        raise TypeError("require_w05_routing_consumer requires W05ResultBundle/W05ContractView")
    if not view.consumer_ready:
        raise PermissionError("w05 routing consumer requires clean routing state")
    return view


def require_w05_execution_seam_consumer(result_or_view: W05ResultBundle | W05ContractView) -> W05ContractView:
    view = derive_w05_contract_view(result_or_view) if isinstance(result_or_view, W05ResultBundle) else result_or_view
    if not isinstance(view, W05ContractView):
        raise TypeError("require_w05_execution_seam_consumer requires W05ResultBundle/W05ContractView")
    if view.must_not_execute_update_count <= 0:
        raise PermissionError("w05 execution seam consumer requires must-not-execute guarantees")
    return view


def _to_consumer(packet: W05DownstreamRoutingPermissionPacket) -> W05ConsumerPacket:
    return W05ConsumerPacket(
        routing_id=packet.routing_id,
        may_consider_update=packet.may_consider_update,
        may_request_learning=packet.may_request_learning,
        may_adjust_interpretation=packet.may_adjust_interpretation,
        may_adjust_policy_hint=packet.may_adjust_policy_hint,
        must_revalidate=packet.must_revalidate,
        must_escalate=packet.must_escalate,
        must_abstain=packet.must_abstain,
        must_not_execute_update=packet.must_not_execute_update,
        must_preserve_desired_predicted_observed_permitted_separation=(
            packet.must_preserve_desired_predicted_observed_permitted_separation
        ),
        must_preserve_guardrails=packet.must_preserve_guardrails,
        protected_target_blocked=packet.protected_target_blocked,
        prohibited_uses=packet.prohibited_uses,
        preserved_guardrails=packet.preserved_guardrails,
        execution_authorization_granted=packet.execution_authorization_granted,
    )
