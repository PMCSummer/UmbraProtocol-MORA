from __future__ import annotations

from dataclasses import dataclass

from substrate.n03_autobiographical_relevance.models import (
    N03RelevanceKind,
    N03Result,
    N03TransferDecision,
)


@dataclass(frozen=True, slots=True)
class N03ContractView:
    relevance_entry_count: int
    relevant_trace_count: int
    blocked_transfer_count: int
    conflict_count: int
    provisional_transfer_count: int
    no_safe_transfer_count: int
    consumer_ready: bool
    transfer_packet_consumer_ready: bool
    consistency_consumer_ready: bool
    required_restrictions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    autobiographical_relevance_not_retrieval: bool
    autobiographical_relevance_not_planner: bool
    autobiographical_relevance_not_memory_lifecycle: bool
    autobiographical_relevance_not_identity_generator: bool
    reason: str


@dataclass(frozen=True, slots=True)
class N03ConsumerPacket:
    relevance_id: str
    source_trace_id: str
    current_target_id: str
    relevance_kind: str
    transfer_decision: str
    transfer_scope: str
    relevance_strength: float
    supported_by_dimensions: tuple[str, ...]
    anti_generalization_limits: tuple[str, ...]
    routing_signal: str
    caution_markers: tuple[str, ...]
    confidence: float
    no_claim_markers: tuple[str, ...]


def derive_n03_contract_view(result: N03Result) -> N03ContractView:
    if not isinstance(result, N03Result):
        raise TypeError("derive_n03_contract_view requires N03Result")
    return N03ContractView(
        relevance_entry_count=result.telemetry.relevance_entry_count,
        relevant_trace_count=result.telemetry.relevant_trace_count,
        blocked_transfer_count=result.telemetry.blocked_transfer_count,
        conflict_count=result.telemetry.conflict_count,
        provisional_transfer_count=result.telemetry.provisional_transfer_count,
        no_safe_transfer_count=result.telemetry.no_safe_transfer_count,
        consumer_ready=result.gate.consumer_ready,
        transfer_packet_consumer_ready=result.gate.transfer_packet_consumer_ready,
        consistency_consumer_ready=result.gate.consistency_consumer_ready,
        required_restrictions=result.gate.required_restrictions,
        reason_codes=result.gate.reason_codes,
        autobiographical_relevance_not_retrieval=result.scope_marker.autobiographical_relevance_not_retrieval,
        autobiographical_relevance_not_planner=result.scope_marker.autobiographical_relevance_not_planner,
        autobiographical_relevance_not_memory_lifecycle=result.scope_marker.autobiographical_relevance_not_memory_lifecycle,
        autobiographical_relevance_not_identity_generator=result.scope_marker.autobiographical_relevance_not_identity_generator,
        reason=result.reason,
    )


def derive_n03_consumer_packets(result: N03Result) -> tuple[N03ConsumerPacket, ...]:
    if not isinstance(result, N03Result):
        raise TypeError("derive_n03_consumer_packets requires N03Result")
    return tuple(
        N03ConsumerPacket(
            relevance_id=item.relevance_id,
            source_trace_id=item.source_trace_id,
            current_target_id=item.current_target_id,
            relevance_kind=item.relevance_kind.value,
            transfer_decision=item.transfer_decision.value,
            transfer_scope=item.transfer_scope.value,
            relevance_strength=item.relevance_strength,
            supported_by_dimensions=tuple(d.value for d in item.supported_by_dimensions),
            anti_generalization_limits=item.anti_generalization_limits,
            routing_signal=_routing_signal(item.relevance_kind, item.transfer_decision),
            caution_markers=tuple(reason.value for reason in item.limiting_reasons),
            confidence=item.confidence,
            no_claim_markers=(
                "not_retrieval_system",
                "not_planner_command",
                "not_memory_lifecycle",
                "not_identity_truth",
            ),
        )
        for item in result.relevance_entries
    )


def require_n03_transfer_packet_consumer_ready(result_or_view: N03Result | N03ContractView) -> N03ContractView:
    view = derive_n03_contract_view(result_or_view) if isinstance(result_or_view, N03Result) else result_or_view
    if not isinstance(view, N03ContractView):
        raise TypeError("require_n03_transfer_packet_consumer_ready requires N03Result/N03ContractView")
    if not view.transfer_packet_consumer_ready:
        raise PermissionError("n03 transfer consumer requires typed autobiographical transfer packets")
    return view


def require_n03_consistency_consumer_ready(result_or_view: N03Result | N03ContractView) -> N03ContractView:
    view = derive_n03_contract_view(result_or_view) if isinstance(result_or_view, N03Result) else result_or_view
    if not isinstance(view, N03ContractView):
        raise TypeError("require_n03_consistency_consumer_ready requires N03Result/N03ContractView")
    if not view.consistency_consumer_ready:
        raise PermissionError("n03 consistency consumer requires conflict review before transfer")
    return view


def _routing_signal(relevance_kind: N03RelevanceKind, transfer_decision: N03TransferDecision) -> str:
    if transfer_decision is N03TransferDecision.USE_AS_REGULATORY_WARNING:
        return "amplify_prior_failure_caution"
    if transfer_decision is N03TransferDecision.USE_AS_RECOVERY_TEMPLATE:
        return "preserve_recovery_pattern"
    if transfer_decision is N03TransferDecision.USE_AS_PLAN_CONSTRAINT:
        return "constrain_overreach"
    if transfer_decision is N03TransferDecision.USE_AS_COMMITMENT_ANCHOR:
        return "preserve_commitment_anchor"
    if transfer_decision is N03TransferDecision.CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE:
        return "require_conflict_review"
    if transfer_decision in {
        N03TransferDecision.DO_NOT_TRANSFER,
        N03TransferDecision.NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER,
    }:
        return "no_downstream_transfer"
    if relevance_kind is N03RelevanceKind.CAPABILITY_BOUNDARY_RELEVANCE:
        return "trigger_tool_recheck"
    return "mark_route_high_risk"
