from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup.models import (
    A01CanonicalOntologyResult,
)


def a01_internal_affordance_ontology_cleanup_snapshot(
    result: A01CanonicalOntologyResult,
) -> dict[str, object]:
    if not isinstance(result, A01CanonicalOntologyResult):
        raise TypeError(
            "a01_internal_affordance_ontology_cleanup_snapshot requires A01CanonicalOntologyResult"
        )
    return {
        "snapshot": {
            "snapshot_id": result.ontology_snapshot.snapshot_id,
            "canonical_entry_count": len(result.ontology_snapshot.canonical_entries),
            "merge_decision_count": len(result.ontology_snapshot.ledger.merge_decisions),
            "split_decision_count": len(result.ontology_snapshot.ledger.split_decisions),
            "contested_count": len(result.ontology_snapshot.ledger.contested),
            "deprecated_count": sum(
                int(item.validity_status.value in {"deprecated", "unavailable"})
                for item in result.ontology_snapshot.canonical_entries
            ),
            "reason": result.ontology_snapshot.reason,
        },
        "ledger": {
            "same_label_diff_precondition_count": (
                result.ontology_snapshot.ledger.same_label_diff_precondition_count
            ),
            "class_conflict_count": result.ontology_snapshot.ledger.class_conflict_count,
            "legacy_label_bypass_detected": (
                result.ontology_snapshot.ledger.legacy_label_bypass_detected
            ),
            "reason": result.ontology_snapshot.ledger.reason,
        },
        "gate": {
            "canonical_affordance_consumer_ready": result.gate.canonical_affordance_consumer_ready,
            "contested_affordance_consumer_ready": result.gate.contested_affordance_consumer_ready,
            "deprecated_affordance_consumer_ready": result.gate.deprecated_affordance_consumer_ready,
            "downstream_readiness_status": result.gate.downstream_readiness_status.value,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "frontier_only": result.scope_marker.frontier_only,
            "narrow_slice_only": result.scope_marker.narrow_slice_only,
            "ontology_cleanup_not_planner_selection": (
                result.scope_marker.ontology_cleanup_not_planner_selection
            ),
            "no_hidden_planner_selection_authority": (
                result.scope_marker.no_hidden_planner_selection_authority
            ),
            "no_map_wide_migration_claim": result.scope_marker.no_map_wide_migration_claim,
            "no_world_ontology_completeness_claim": (
                result.scope_marker.no_world_ontology_completeness_claim
            ),
            "no_affordance_discovery_claim": result.scope_marker.no_affordance_discovery_claim,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "raw_candidate_count": result.telemetry.raw_candidate_count,
            "canonical_entry_count": result.telemetry.canonical_entry_count,
            "merged_alias_group_count": result.telemetry.merged_alias_group_count,
            "split_decision_count": result.telemetry.split_decision_count,
            "contested_entry_count": result.telemetry.contested_entry_count,
            "deprecated_entry_count": result.telemetry.deprecated_entry_count,
            "parent_child_relation_count": result.telemetry.parent_child_relation_count,
            "same_label_diff_precondition_count": (
                result.telemetry.same_label_diff_precondition_count
            ),
            "class_conflict_count": result.telemetry.class_conflict_count,
            "legacy_label_bypass_detected": result.telemetry.legacy_label_bypass_detected,
            "downstream_consumer_ready": result.telemetry.downstream_consumer_ready,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
