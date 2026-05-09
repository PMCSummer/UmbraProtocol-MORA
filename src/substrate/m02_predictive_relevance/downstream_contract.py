from __future__ import annotations

from dataclasses import dataclass

from substrate.m02_predictive_relevance.models import M02Result


@dataclass(frozen=True, slots=True)
class M02ContractView:
    trace_count: int
    predictive_mark_count: int
    clean_predictive_mark_count: int
    weak_mark_count: int
    context_locked_count: int
    spurious_risk_count: int
    no_safe_mark_count: int
    consumer_ready: bool
    predictive_packet_consumer_ready: bool
    context_scope_consumer_ready: bool
    downstream_must_preserve_context: bool
    downstream_must_not_generalize: bool
    downstream_must_not_treat_as_generic_importance: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    predictive_relevance_not_generic_importance: bool
    no_full_prediction_claim: bool
    no_full_memory_lifecycle_claim: bool
    no_planner_policy_claim: bool
    separate_from_homeostatic_imprint: bool
    reason: str


@dataclass(frozen=True, slots=True)
class M02ConsumerView:
    source_trace_id: str
    predicted_target_types: tuple[str, ...]
    relevance_strength: float
    utility_horizon: str
    context_scope: str
    anti_spurious_limits: tuple[str, ...]
    retrieval_bias: float
    retention_bias: float
    replay_priority: float
    indexing_bias: float
    planning_support_recall_bias: float
    confidence: float
    must_preserve_context: bool
    must_not_generalize: bool
    must_not_treat_as_generic_importance: bool
    no_full_prediction_claim: bool
    no_full_memory_lifecycle_claim: bool
    reason_codes: tuple[str, ...]


def derive_m02_contract_view(result: M02Result) -> M02ContractView:
    if not isinstance(result, M02Result):
        raise TypeError("derive_m02_contract_view requires M02Result")
    return M02ContractView(
        trace_count=result.telemetry.trace_count,
        predictive_mark_count=result.telemetry.predictive_mark_count,
        clean_predictive_mark_count=result.telemetry.clean_predictive_mark_count,
        weak_mark_count=result.telemetry.weak_mark_count,
        context_locked_count=result.telemetry.context_locked_count,
        spurious_risk_count=result.telemetry.spurious_risk_count,
        no_safe_mark_count=result.telemetry.no_safe_mark_count,
        consumer_ready=result.gate.consumer_ready,
        predictive_packet_consumer_ready=result.gate.predictive_packet_consumer_ready,
        context_scope_consumer_ready=result.gate.context_scope_consumer_ready,
        downstream_must_preserve_context=result.gate.downstream_must_preserve_context,
        downstream_must_not_generalize=result.gate.downstream_must_not_generalize,
        downstream_must_not_treat_as_generic_importance=result.gate.downstream_must_not_treat_as_generic_importance,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        predictive_relevance_not_generic_importance=result.scope_marker.predictive_relevance_not_generic_importance,
        no_full_prediction_claim=result.scope_marker.no_full_prediction_claim,
        no_full_memory_lifecycle_claim=result.scope_marker.no_full_memory_lifecycle_claim,
        no_planner_policy_claim=result.scope_marker.no_planner_policy_claim,
        separate_from_homeostatic_imprint=result.scope_marker.separate_from_homeostatic_imprint,
        reason=result.reason,
    )


def derive_m02_consumer_packets(result: M02Result) -> tuple[M02ConsumerView, ...]:
    if not isinstance(result, M02Result):
        raise TypeError("derive_m02_consumer_packets requires M02Result")
    return tuple(
        M02ConsumerView(
            source_trace_id=item.source_trace_id,
            predicted_target_types=tuple(kind.value for kind in item.predicted_target_types),
            relevance_strength=item.relevance_strength,
            utility_horizon=item.utility_horizon.value,
            context_scope=item.context_scope,
            anti_spurious_limits=item.anti_spurious_limits,
            retrieval_bias=item.retrieval_bias,
            retention_bias=item.retention_bias,
            replay_priority=item.replay_priority,
            indexing_bias=item.indexing_bias,
            planning_support_recall_bias=item.planning_support_recall_bias,
            confidence=item.confidence,
            must_preserve_context=item.must_preserve_context,
            must_not_generalize=item.must_not_generalize,
            must_not_treat_as_generic_importance=item.must_not_treat_as_generic_importance,
            no_full_prediction_claim=True,
            no_full_memory_lifecycle_claim=True,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        item.decision.value,
                        *item.anti_spurious_limits,
                    )
                )
            ),
        )
        for item in result.predictive_marks
    )


def require_m02_predictive_packet_consumer(result_or_view: M02Result | M02ContractView) -> M02ContractView:
    view = derive_m02_contract_view(result_or_view) if isinstance(result_or_view, M02Result) else result_or_view
    if not isinstance(view, M02ContractView):
        raise TypeError("require_m02_predictive_packet_consumer requires M02Result/M02ContractView")
    if not view.predictive_packet_consumer_ready:
        raise PermissionError("m02 predictive-packet consumer requires typed target-linked predictive marks")
    return view


def require_m02_context_scope_consumer(result_or_view: M02Result | M02ContractView) -> M02ContractView:
    view = derive_m02_contract_view(result_or_view) if isinstance(result_or_view, M02Result) else result_or_view
    if not isinstance(view, M02ContractView):
        raise TypeError("require_m02_context_scope_consumer requires M02Result/M02ContractView")
    if not view.context_scope_consumer_ready:
        raise PermissionError("m02 context-scope consumer requires context-preserving predictive marks")
    return view
