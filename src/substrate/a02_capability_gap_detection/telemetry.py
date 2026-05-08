from __future__ import annotations

from substrate.a02_capability_gap_detection.models import A02CapabilityGapResult


def a02_capability_gap_detection_snapshot(result: A02CapabilityGapResult) -> dict[str, object]:
    if not isinstance(result, A02CapabilityGapResult):
        raise TypeError("a02_capability_gap_detection_snapshot requires A02CapabilityGapResult")
    return {
        "result": {
            "demand_set_id": result.demand_set_id,
            "gap_entry_count": len(result.gap_entries),
            "reason": result.reason,
        },
        "ledger": {
            "source_lineage_count": result.ledger.source_lineage_count,
            "source_lineage_complete": result.ledger.source_lineage_complete,
            "canonical_id_hint_used_count": result.ledger.canonical_id_hint_used_count,
            "canonical_id_generated_count": result.ledger.canonical_id_generated_count,
            "canonical_id_coverage_complete": result.ledger.canonical_id_coverage_complete,
            "no_affordance_invention_observed": result.ledger.no_affordance_invention_observed,
            "reason": result.ledger.reason,
        },
        "gate": {
            "gap_packet_consumer_ready": result.gate.gap_packet_consumer_ready,
            "partial_coverage_consumer_ready": result.gate.partial_coverage_consumer_ready,
            "ownership_boundary_consumer_ready": result.gate.ownership_boundary_consumer_ready,
            "composition_consumer_ready": result.gate.composition_consumer_ready,
            "downstream_readiness_status": result.gate.downstream_readiness_status.value,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "capability_gap_not_planner": result.scope_marker.capability_gap_not_planner,
            "depends_on_a01_canonical_ontology": result.scope_marker.depends_on_a01_canonical_ontology,
            "no_map_wide_claim": result.scope_marker.no_map_wide_claim,
            "no_affordance_discovery_claim": result.scope_marker.no_affordance_discovery_claim,
            "no_hidden_action_execution_claim": result.scope_marker.no_hidden_action_execution_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "demand_count": result.telemetry.demand_count,
            "gap_entry_count": result.telemetry.gap_entry_count,
            "fully_covered_count": result.telemetry.fully_covered_count,
            "partial_coverage_count": result.telemetry.partial_coverage_count,
            "missing_gap_count": result.telemetry.missing_gap_count,
            "blocked_gap_count": result.telemetry.blocked_gap_count,
            "composition_gap_count": result.telemetry.composition_gap_count,
            "composition_unverified_count": result.telemetry.composition_unverified_count,
            "ownership_boundary_gap_count": result.telemetry.ownership_boundary_gap_count,
            "no_clean_coverage_count": result.telemetry.no_clean_coverage_count,
            "source_lineage_count": result.telemetry.source_lineage_count,
            "source_lineage_complete": result.telemetry.source_lineage_complete,
            "canonical_id_hint_used_count": result.telemetry.canonical_id_hint_used_count,
            "canonical_id_generated_count": result.telemetry.canonical_id_generated_count,
            "canonical_id_coverage_complete": result.telemetry.canonical_id_coverage_complete,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
    }
