from __future__ import annotations

from dataclasses import dataclass

from substrate.a02_capability_gap_detection.models import (
    A02CapabilityGapResult,
)


@dataclass(frozen=True, slots=True)
class A02CapabilityGapContractView:
    demand_count: int
    gap_entry_count: int
    fully_covered_count: int
    partial_coverage_count: int
    missing_gap_count: int
    blocked_gap_count: int
    composition_gap_count: int
    composition_unverified_count: int
    ownership_boundary_gap_count: int
    no_clean_coverage_count: int
    source_lineage_count: int
    source_lineage_complete: bool
    canonical_id_hint_used_count: int
    canonical_id_generated_count: int
    canonical_id_coverage_complete: bool
    gap_packet_consumer_ready: bool
    partial_coverage_consumer_ready: bool
    ownership_boundary_consumer_ready: bool
    composition_consumer_ready: bool
    downstream_consumer_ready: bool
    downstream_readiness_status: str
    restrictions: tuple[str, ...]
    scope: str
    scope_frontier_only: bool
    scope_narrow_slice_only: bool
    scope_capability_gap_not_planner: bool
    scope_depends_on_a01_canonical_ontology: bool
    scope_no_map_wide_claim: bool
    scope_no_affordance_discovery_claim: bool
    scope_no_hidden_action_execution_claim: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class A02CapabilityGapConsumerView:
    demand_count: int
    gap_entry_count: int
    fully_covered_count: int
    partial_coverage_count: int
    missing_gap_count: int
    blocked_gap_count: int
    composition_gap_count: int
    composition_unverified_count: int
    ownership_boundary_gap_count: int
    no_clean_coverage_count: int
    source_lineage_count: int
    source_lineage_complete: bool
    canonical_id_hint_used_count: int
    canonical_id_generated_count: int
    canonical_id_coverage_complete: bool
    gap_packet_consumer_ready: bool
    partial_coverage_consumer_ready: bool
    ownership_boundary_consumer_ready: bool
    composition_consumer_ready: bool
    downstream_consumer_ready: bool
    downstream_readiness_status: str
    restrictions: tuple[str, ...]
    reason: str


def derive_a02_capability_gap_contract_view(
    result: A02CapabilityGapResult,
) -> A02CapabilityGapContractView:
    if not isinstance(result, A02CapabilityGapResult):
        raise TypeError("derive_a02_capability_gap_contract_view requires A02CapabilityGapResult")
    telemetry = result.telemetry
    gate = result.gate
    scope = result.scope_marker
    return A02CapabilityGapContractView(
        demand_count=telemetry.demand_count,
        gap_entry_count=telemetry.gap_entry_count,
        fully_covered_count=telemetry.fully_covered_count,
        partial_coverage_count=telemetry.partial_coverage_count,
        missing_gap_count=telemetry.missing_gap_count,
        blocked_gap_count=telemetry.blocked_gap_count,
        composition_gap_count=telemetry.composition_gap_count,
        composition_unverified_count=telemetry.composition_unverified_count,
        ownership_boundary_gap_count=telemetry.ownership_boundary_gap_count,
        no_clean_coverage_count=telemetry.no_clean_coverage_count,
        source_lineage_count=telemetry.source_lineage_count,
        source_lineage_complete=telemetry.source_lineage_complete,
        canonical_id_hint_used_count=telemetry.canonical_id_hint_used_count,
        canonical_id_generated_count=telemetry.canonical_id_generated_count,
        canonical_id_coverage_complete=telemetry.canonical_id_coverage_complete,
        gap_packet_consumer_ready=gate.gap_packet_consumer_ready,
        partial_coverage_consumer_ready=gate.partial_coverage_consumer_ready,
        ownership_boundary_consumer_ready=gate.ownership_boundary_consumer_ready,
        composition_consumer_ready=gate.composition_consumer_ready,
        downstream_consumer_ready=telemetry.downstream_consumer_ready,
        downstream_readiness_status=gate.downstream_readiness_status.value,
        restrictions=gate.restrictions,
        scope=scope.scope,
        scope_frontier_only=scope.frontier_only,
        scope_narrow_slice_only=scope.narrow_slice_only,
        scope_capability_gap_not_planner=scope.capability_gap_not_planner,
        scope_depends_on_a01_canonical_ontology=scope.depends_on_a01_canonical_ontology,
        scope_no_map_wide_claim=scope.no_map_wide_claim,
        scope_no_affordance_discovery_claim=scope.no_affordance_discovery_claim,
        scope_no_hidden_action_execution_claim=scope.no_hidden_action_execution_claim,
        scope_reason=scope.reason,
        reason=result.reason,
    )


def derive_a02_capability_gap_consumer_view(
    result_or_view: A02CapabilityGapResult | A02CapabilityGapContractView,
) -> A02CapabilityGapConsumerView:
    view = (
        derive_a02_capability_gap_contract_view(result_or_view)
        if isinstance(result_or_view, A02CapabilityGapResult)
        else result_or_view
    )
    if not isinstance(view, A02CapabilityGapContractView):
        raise TypeError(
            "derive_a02_capability_gap_consumer_view requires A02CapabilityGapResult/A02CapabilityGapContractView"
        )
    return A02CapabilityGapConsumerView(
        demand_count=view.demand_count,
        gap_entry_count=view.gap_entry_count,
        fully_covered_count=view.fully_covered_count,
        partial_coverage_count=view.partial_coverage_count,
        missing_gap_count=view.missing_gap_count,
        blocked_gap_count=view.blocked_gap_count,
        composition_gap_count=view.composition_gap_count,
        composition_unverified_count=view.composition_unverified_count,
        ownership_boundary_gap_count=view.ownership_boundary_gap_count,
        no_clean_coverage_count=view.no_clean_coverage_count,
        source_lineage_count=view.source_lineage_count,
        source_lineage_complete=view.source_lineage_complete,
        canonical_id_hint_used_count=view.canonical_id_hint_used_count,
        canonical_id_generated_count=view.canonical_id_generated_count,
        canonical_id_coverage_complete=view.canonical_id_coverage_complete,
        gap_packet_consumer_ready=view.gap_packet_consumer_ready,
        partial_coverage_consumer_ready=view.partial_coverage_consumer_ready,
        ownership_boundary_consumer_ready=view.ownership_boundary_consumer_ready,
        composition_consumer_ready=view.composition_consumer_ready,
        downstream_consumer_ready=view.downstream_consumer_ready,
        downstream_readiness_status=view.downstream_readiness_status,
        restrictions=view.restrictions,
        reason="a02 capability-gap consumer view",
    )


def require_a02_gap_packet_consumer(
    result_or_view: A02CapabilityGapResult | A02CapabilityGapContractView,
) -> A02CapabilityGapConsumerView:
    view = derive_a02_capability_gap_consumer_view(result_or_view)
    if not view.gap_packet_consumer_ready:
        raise PermissionError("a02 gap-packet consumer requires typed capability gap entries")
    return view


def require_a02_partial_coverage_consumer(
    result_or_view: A02CapabilityGapResult | A02CapabilityGapContractView,
) -> A02CapabilityGapConsumerView:
    view = derive_a02_capability_gap_consumer_view(result_or_view)
    if not view.partial_coverage_consumer_ready:
        raise PermissionError("a02 partial-coverage consumer requires explicit partial coverage entries")
    return view


def require_a02_ownership_boundary_consumer(
    result_or_view: A02CapabilityGapResult | A02CapabilityGapContractView,
) -> A02CapabilityGapConsumerView:
    view = derive_a02_capability_gap_consumer_view(result_or_view)
    if not view.ownership_boundary_consumer_ready:
        raise PermissionError(
            "a02 ownership-boundary consumer requires explicit ownership-boundary gap entries"
        )
    return view


def require_a02_composition_consumer(
    result_or_view: A02CapabilityGapResult | A02CapabilityGapContractView,
) -> A02CapabilityGapConsumerView:
    view = derive_a02_capability_gap_consumer_view(result_or_view)
    if not view.composition_consumer_ready:
        raise PermissionError("a02 composition consumer requires composition-dependent entries")
    return view
