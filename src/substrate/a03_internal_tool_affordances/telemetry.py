from __future__ import annotations

from substrate.a03_internal_tool_affordances.models import A03InternalToolAffordanceResult


def a03_internal_tool_affordances_snapshot(result: A03InternalToolAffordanceResult) -> dict[str, object]:
    if not isinstance(result, A03InternalToolAffordanceResult):
        raise TypeError("a03_internal_tool_affordances_snapshot requires A03InternalToolAffordanceResult")
    return {
        "result": {
            "candidate_set_id": result.candidate_set_id,
            "reason": result.reason,
        },
        "registry": {
            "registry_id": result.canonical_registry.registry_id,
            "canonical_tool_count": len(result.canonical_registry.canonical_tools),
            "alias_count": len(result.canonical_registry.aliases),
            "composition_role_count": len(result.canonical_registry.composition_roles),
        },
        "cleanup_ledger": {
            "canonical_tool_count": result.cleanup_ledger.canonical_tool_count,
            "rejected_operation_count": result.cleanup_ledger.rejected_operation_count,
            "contested_tool_count": result.cleanup_ledger.contested_tool_count,
            "contract_incomplete_count": result.cleanup_ledger.contract_incomplete_count,
            "degraded_tool_count": result.cleanup_ledger.degraded_tool_count,
            "blocked_tool_count": result.cleanup_ledger.blocked_tool_count,
            "missing_internal_tool_gap_count": result.cleanup_ledger.missing_internal_tool_gap_count,
            "blocked_internal_tool_gap_count": result.cleanup_ledger.blocked_internal_tool_gap_count,
            "overbroad_generic_operation_rejected": result.cleanup_ledger.overbroad_generic_operation_rejected,
            "legacy_direct_call_detected": result.cleanup_ledger.legacy_direct_call_detected,
            "canonical_tool_id_hint_used_count": result.cleanup_ledger.canonical_tool_id_hint_used_count,
            "canonical_tool_id_generated_count": result.cleanup_ledger.canonical_tool_id_generated_count,
            "canonical_tool_id_coverage_complete": result.cleanup_ledger.canonical_tool_id_coverage_complete,
            "source_lineage_count": result.cleanup_ledger.source_lineage_count,
            "source_lineage_complete": result.cleanup_ledger.source_lineage_complete,
            "reason": result.cleanup_ledger.reason,
        },
        "gap_linkage": {
            "linkage_kind": result.gap_linkage.linkage_kind.value,
            "missing_internal_tool_count": len(result.gap_linkage.missing_internal_tools),
            "blocked_internal_tool_count": len(result.gap_linkage.blocked_internal_tools),
            "tool_insufficiency_count": len(result.gap_linkage.tool_insufficiency),
            "reason": result.gap_linkage.reason,
        },
        "gate": {
            "internal_tool_consumer_ready": result.gate.internal_tool_consumer_ready,
            "tool_contract_consumer_ready": result.gate.tool_contract_consumer_ready,
            "tool_gap_linkage_consumer_ready": result.gate.tool_gap_linkage_consumer_ready,
            "no_legacy_direct_call_consumer_ready": result.gate.no_legacy_direct_call_consumer_ready,
            "downstream_readiness_status": result.gate.downstream_readiness_status.value,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "internal_tool_ontology_not_executor": result.scope_marker.internal_tool_ontology_not_executor,
            "depends_on_a01_canonical_ontology": result.scope_marker.depends_on_a01_canonical_ontology,
            "depends_on_a02_gap_packets": result.scope_marker.depends_on_a02_gap_packets,
            "no_map_wide_claim": result.scope_marker.no_map_wide_claim,
            "no_tool_invention_claim": result.scope_marker.no_tool_invention_claim,
            "no_truth_or_correctness_guarantee_claim": result.scope_marker.no_truth_or_correctness_guarantee_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "canonical_tool_count": result.telemetry.canonical_tool_count,
            "rejected_operation_count": result.telemetry.rejected_operation_count,
            "contested_tool_count": result.telemetry.contested_tool_count,
            "contract_incomplete_count": result.telemetry.contract_incomplete_count,
            "degraded_tool_count": result.telemetry.degraded_tool_count,
            "blocked_tool_count": result.telemetry.blocked_tool_count,
            "missing_internal_tool_gap_count": result.telemetry.missing_internal_tool_gap_count,
            "blocked_internal_tool_gap_count": result.telemetry.blocked_internal_tool_gap_count,
            "overbroad_generic_operation_rejected": result.telemetry.overbroad_generic_operation_rejected,
            "legacy_direct_call_detected": result.telemetry.legacy_direct_call_detected,
            "canonical_tool_id_coverage_complete": result.telemetry.canonical_tool_id_coverage_complete,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
    }

