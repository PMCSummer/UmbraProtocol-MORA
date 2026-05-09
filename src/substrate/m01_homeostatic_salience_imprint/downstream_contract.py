from __future__ import annotations

from dataclasses import dataclass

from substrate.m01_homeostatic_salience_imprint.models import M01Result


@dataclass(frozen=True, slots=True)
class M01ContractView:
    trace_count: int
    imprint_count: int
    strong_imprint_count: int
    weak_or_no_claim_count: int
    attribution_limited_count: int
    recovery_imprint_count: int
    no_safe_imprint_count: int
    consumer_ready: bool
    imprint_packet_consumer_ready: bool
    axis_scope_consumer_ready: bool
    no_safe_imprint_claim: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    homeostatic_imprint_not_general_importance: bool
    not_reward_function: bool
    not_narrative_relevance: bool
    not_full_memory_system: bool
    no_policy_claim: bool
    no_global_value_claim: bool
    reason: str


@dataclass(frozen=True, slots=True)
class M01ConsumerView:
    source_trace_id: str
    affected_axes: tuple[str, ...]
    transfer_limits: tuple[str, ...]
    imprint_strength: float
    retention_bias: float
    replay_priority: float
    retrieval_bias: float
    may_bias_retention: bool
    may_bias_replay: bool
    may_bias_retrieval: bool
    must_preserve_axis_scope: bool
    must_preserve_transfer_limits: bool
    must_not_treat_as_general_importance: bool
    confidence: float
    reason_codes: tuple[str, ...]


def derive_m01_contract_view(result: M01Result) -> M01ContractView:
    if not isinstance(result, M01Result):
        raise TypeError("derive_m01_contract_view requires M01Result")
    return M01ContractView(
        trace_count=result.telemetry.trace_count,
        imprint_count=result.telemetry.imprint_count,
        strong_imprint_count=result.telemetry.strong_imprint_count,
        weak_or_no_claim_count=result.telemetry.weak_or_no_claim_count,
        attribution_limited_count=result.telemetry.attribution_limited_count,
        recovery_imprint_count=result.telemetry.recovery_imprint_count,
        no_safe_imprint_count=result.telemetry.no_safe_imprint_count,
        consumer_ready=result.gate.consumer_ready,
        imprint_packet_consumer_ready=result.gate.imprint_packet_consumer_ready,
        axis_scope_consumer_ready=result.gate.axis_scope_consumer_ready,
        no_safe_imprint_claim=result.gate.no_safe_imprint_claim,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        homeostatic_imprint_not_general_importance=result.scope_marker.homeostatic_imprint_not_general_importance,
        not_reward_function=result.scope_marker.not_reward_function,
        not_narrative_relevance=result.scope_marker.not_narrative_relevance,
        not_full_memory_system=result.scope_marker.not_full_memory_system,
        no_policy_claim=result.scope_marker.no_policy_claim,
        no_global_value_claim=result.scope_marker.no_global_value_claim,
        reason=result.reason,
    )


def derive_m01_consumer_packets(result: M01Result) -> tuple[M01ConsumerView, ...]:
    if not isinstance(result, M01Result):
        raise TypeError("derive_m01_consumer_packets requires M01Result")
    return tuple(
        M01ConsumerView(
            source_trace_id=item.source_trace_id,
            affected_axes=item.affected_axes,
            transfer_limits=item.transfer_limits,
            imprint_strength=item.imprint_strength,
            retention_bias=item.retention_bias,
            replay_priority=item.replay_priority,
            retrieval_bias=item.retrieval_bias,
            may_bias_retention=item.allowed_memory_use.may_bias_retention,
            may_bias_replay=item.allowed_memory_use.may_bias_replay,
            may_bias_retrieval=item.allowed_memory_use.may_bias_retrieval,
            must_preserve_axis_scope=item.allowed_memory_use.must_preserve_axis_scope,
            must_preserve_transfer_limits=item.allowed_memory_use.must_preserve_transfer_limits,
            must_not_treat_as_general_importance=item.allowed_memory_use.must_not_treat_as_general_importance,
            confidence=item.confidence,
            reason_codes=item.reason_codes,
        )
        for item in result.imprint_packets
    )


def require_m01_imprint_packet_consumer(result_or_view: M01Result | M01ContractView) -> M01ContractView:
    view = derive_m01_contract_view(result_or_view) if isinstance(result_or_view, M01Result) else result_or_view
    if not isinstance(view, M01ContractView):
        raise TypeError("require_m01_imprint_packet_consumer requires M01Result/M01ContractView")
    if not view.imprint_packet_consumer_ready:
        raise PermissionError("m01 imprint-packet consumer requires typed imprint packets")
    return view


def require_m01_axis_scope_consumer(result_or_view: M01Result | M01ContractView) -> M01ContractView:
    view = derive_m01_contract_view(result_or_view) if isinstance(result_or_view, M01Result) else result_or_view
    if not isinstance(view, M01ContractView):
        raise TypeError("require_m01_axis_scope_consumer requires M01Result/M01ContractView")
    if not view.axis_scope_consumer_ready:
        raise PermissionError("m01 axis-scope consumer requires axis-preserving imprint packets")
    return view
