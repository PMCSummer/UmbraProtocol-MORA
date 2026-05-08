from __future__ import annotations

from dataclasses import dataclass

from substrate.a03_internal_tool_affordances.models import (
    A03InternalToolAffordanceResult,
)


@dataclass(frozen=True, slots=True)
class A03ToolContractView:
    canonical_tool_count: int
    rejected_operation_count: int
    contested_tool_count: int
    contract_incomplete_count: int
    degraded_tool_count: int
    blocked_tool_count: int
    missing_internal_tool_gap_count: int
    blocked_internal_tool_gap_count: int
    overbroad_generic_operation_rejected: bool
    legacy_direct_call_detected: bool
    canonical_tool_id_coverage_complete: bool
    internal_tool_consumer_ready: bool
    tool_contract_consumer_ready: bool
    tool_gap_linkage_consumer_ready: bool
    no_legacy_direct_call_consumer_ready: bool
    downstream_consumer_ready: bool
    downstream_readiness_status: str
    restrictions: tuple[str, ...]
    scope: str
    scope_frontier_only: bool
    scope_narrow_slice_only: bool
    scope_internal_tool_ontology_not_executor: bool
    scope_depends_on_a01_canonical_ontology: bool
    scope_depends_on_a02_gap_packets: bool
    scope_no_map_wide_claim: bool
    scope_no_tool_invention_claim: bool
    scope_no_truth_or_correctness_guarantee_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class A03ToolConsumerView:
    canonical_tool_count: int
    rejected_operation_count: int
    contested_tool_count: int
    contract_incomplete_count: int
    degraded_tool_count: int
    blocked_tool_count: int
    missing_internal_tool_gap_count: int
    blocked_internal_tool_gap_count: int
    overbroad_generic_operation_rejected: bool
    legacy_direct_call_detected: bool
    canonical_tool_id_coverage_complete: bool
    internal_tool_consumer_ready: bool
    tool_contract_consumer_ready: bool
    tool_gap_linkage_consumer_ready: bool
    no_legacy_direct_call_consumer_ready: bool
    downstream_consumer_ready: bool
    downstream_readiness_status: str
    restrictions: tuple[str, ...]
    reason: str


def derive_a03_tool_contract_view(result: A03InternalToolAffordanceResult) -> A03ToolContractView:
    if not isinstance(result, A03InternalToolAffordanceResult):
        raise TypeError("derive_a03_tool_contract_view requires A03InternalToolAffordanceResult")
    telemetry = result.telemetry
    gate = result.gate
    scope = result.scope_marker
    return A03ToolContractView(
        canonical_tool_count=telemetry.canonical_tool_count,
        rejected_operation_count=telemetry.rejected_operation_count,
        contested_tool_count=telemetry.contested_tool_count,
        contract_incomplete_count=telemetry.contract_incomplete_count,
        degraded_tool_count=telemetry.degraded_tool_count,
        blocked_tool_count=telemetry.blocked_tool_count,
        missing_internal_tool_gap_count=telemetry.missing_internal_tool_gap_count,
        blocked_internal_tool_gap_count=telemetry.blocked_internal_tool_gap_count,
        overbroad_generic_operation_rejected=telemetry.overbroad_generic_operation_rejected,
        legacy_direct_call_detected=telemetry.legacy_direct_call_detected,
        canonical_tool_id_coverage_complete=telemetry.canonical_tool_id_coverage_complete,
        internal_tool_consumer_ready=gate.internal_tool_consumer_ready,
        tool_contract_consumer_ready=gate.tool_contract_consumer_ready,
        tool_gap_linkage_consumer_ready=gate.tool_gap_linkage_consumer_ready,
        no_legacy_direct_call_consumer_ready=gate.no_legacy_direct_call_consumer_ready,
        downstream_consumer_ready=telemetry.downstream_consumer_ready,
        downstream_readiness_status=gate.downstream_readiness_status.value,
        restrictions=gate.restrictions,
        scope=scope.scope,
        scope_frontier_only=scope.frontier_only,
        scope_narrow_slice_only=scope.narrow_slice_only,
        scope_internal_tool_ontology_not_executor=scope.internal_tool_ontology_not_executor,
        scope_depends_on_a01_canonical_ontology=scope.depends_on_a01_canonical_ontology,
        scope_depends_on_a02_gap_packets=scope.depends_on_a02_gap_packets,
        scope_no_map_wide_claim=scope.no_map_wide_claim,
        scope_no_tool_invention_claim=scope.no_tool_invention_claim,
        scope_no_truth_or_correctness_guarantee_claim=scope.no_truth_or_correctness_guarantee_claim,
        scope_reason=scope.reason,
        reason=result.reason,
    )


def derive_a03_tool_consumer_view(
    result_or_view: A03InternalToolAffordanceResult | A03ToolContractView,
) -> A03ToolConsumerView:
    view = (
        derive_a03_tool_contract_view(result_or_view)
        if isinstance(result_or_view, A03InternalToolAffordanceResult)
        else result_or_view
    )
    if not isinstance(view, A03ToolContractView):
        raise TypeError(
            "derive_a03_tool_consumer_view requires A03InternalToolAffordanceResult/A03ToolContractView"
        )
    return A03ToolConsumerView(
        canonical_tool_count=view.canonical_tool_count,
        rejected_operation_count=view.rejected_operation_count,
        contested_tool_count=view.contested_tool_count,
        contract_incomplete_count=view.contract_incomplete_count,
        degraded_tool_count=view.degraded_tool_count,
        blocked_tool_count=view.blocked_tool_count,
        missing_internal_tool_gap_count=view.missing_internal_tool_gap_count,
        blocked_internal_tool_gap_count=view.blocked_internal_tool_gap_count,
        overbroad_generic_operation_rejected=view.overbroad_generic_operation_rejected,
        legacy_direct_call_detected=view.legacy_direct_call_detected,
        canonical_tool_id_coverage_complete=view.canonical_tool_id_coverage_complete,
        internal_tool_consumer_ready=view.internal_tool_consumer_ready,
        tool_contract_consumer_ready=view.tool_contract_consumer_ready,
        tool_gap_linkage_consumer_ready=view.tool_gap_linkage_consumer_ready,
        no_legacy_direct_call_consumer_ready=view.no_legacy_direct_call_consumer_ready,
        downstream_consumer_ready=view.downstream_consumer_ready,
        downstream_readiness_status=view.downstream_readiness_status,
        restrictions=view.restrictions,
        reason="a03 internal tool consumer view",
    )


def require_a03_internal_tool_consumer(
    result_or_view: A03InternalToolAffordanceResult | A03ToolContractView,
) -> A03ToolConsumerView:
    view = derive_a03_tool_consumer_view(result_or_view)
    if not view.internal_tool_consumer_ready:
        raise PermissionError("a03 internal-tool consumer requires canonical tool entries")
    return view


def require_a03_tool_contract_consumer(
    result_or_view: A03InternalToolAffordanceResult | A03ToolContractView,
) -> A03ToolConsumerView:
    view = derive_a03_tool_consumer_view(result_or_view)
    if not view.tool_contract_consumer_ready:
        raise PermissionError("a03 tool-contract consumer requires complete canonical invocation contracts")
    return view


def require_a03_tool_gap_linkage_consumer(
    result_or_view: A03InternalToolAffordanceResult | A03ToolContractView,
) -> A03ToolConsumerView:
    view = derive_a03_tool_consumer_view(result_or_view)
    if not view.tool_gap_linkage_consumer_ready:
        raise PermissionError("a03 tool-gap linkage consumer requires explicit a02 linkage packet")
    return view


def require_a03_no_legacy_direct_call_consumer(
    result_or_view: A03InternalToolAffordanceResult | A03ToolContractView,
) -> A03ToolConsumerView:
    view = derive_a03_tool_consumer_view(result_or_view)
    if not view.no_legacy_direct_call_consumer_ready:
        raise PermissionError(
            "a03 no-legacy-direct-call consumer requires absence of legacy direct-call path"
        )
    return view

