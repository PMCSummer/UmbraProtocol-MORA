from __future__ import annotations

from substrate.semantic_acquisition.models import (
    SemanticAcquisitionBundle,
    SemanticAcquisitionGateDecision,
    SemanticAcquisitionResult,
    SemanticAcquisitionTelemetry,
)


def build_semantic_acquisition_telemetry(
    *,
    bundle: SemanticAcquisitionBundle,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: SemanticAcquisitionGateDecision,
    causal_basis: str,
) -> SemanticAcquisitionTelemetry:
    return SemanticAcquisitionTelemetry(
        source_lineage=source_lineage,
        source_perspective_chain_ref=bundle.source_perspective_chain_ref,
        source_applicability_ref=bundle.source_applicability_ref,
        source_runtime_graph_ref=bundle.source_runtime_graph_ref,
        source_grounded_ref=bundle.source_grounded_ref,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        acquisition_record_count=len(bundle.acquisition_records),
        cluster_link_count=len(bundle.cluster_links),
        acquisition_statuses=tuple(dict.fromkeys(record.acquisition_status.value for record in bundle.acquisition_records)),
        stability_classes=tuple(dict.fromkeys(record.stability_class.value for record in bundle.acquisition_records)),
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def semantic_acquisition_result_snapshot(result: SemanticAcquisitionResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_semantic_closure": result.no_final_semantic_closure,
        "bundle": {
            "source_perspective_chain_ref": bundle.source_perspective_chain_ref,
            "source_applicability_ref": bundle.source_applicability_ref,
            "source_runtime_graph_ref": bundle.source_runtime_graph_ref,
            "source_grounded_ref": bundle.source_grounded_ref,
            "source_dictum_ref": bundle.source_dictum_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_proposition_ids": bundle.linked_proposition_ids,
            "linked_semantic_unit_ids": bundle.linked_semantic_unit_ids,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "low_coverage_mode": bundle.low_coverage_mode,
            "low_coverage_reasons": bundle.low_coverage_reasons,
            "no_final_semantic_closure": bundle.no_final_semantic_closure,
            "reason": bundle.reason,
            "acquisition_records": tuple(
                {
                    "acquisition_id": record.acquisition_id,
                    "proposition_id": record.proposition_id,
                    "semantic_unit_id": record.semantic_unit_id,
                    "acquisition_status": record.acquisition_status.value,
                    "stability_class": record.stability_class.value,
                    "support_conflict_profile": {
                        "support_score": record.support_conflict_profile.support_score,
                        "conflict_score": record.support_conflict_profile.conflict_score,
                        "support_reasons": record.support_conflict_profile.support_reasons,
                        "conflict_reasons": record.support_conflict_profile.conflict_reasons,
                        "unresolved_slots": record.support_conflict_profile.unresolved_slots,
                    },
                    "revision_conditions": tuple(
                        {
                            "condition_id": condition.condition_id,
                            "condition_kind": condition.condition_kind.value,
                            "trigger_reason": condition.trigger_reason,
                            "confidence": condition.confidence,
                            "provenance": condition.provenance,
                        }
                        for condition in record.revision_conditions
                    ),
                    "downstream_permissions": record.downstream_permissions,
                    "cluster_id": record.cluster_id,
                    "compatible_acquisition_ids": record.compatible_acquisition_ids,
                    "competing_acquisition_ids": record.competing_acquisition_ids,
                    "blocked_reason": record.blocked_reason,
                    "context_anchor": record.context_anchor,
                    "confidence": record.confidence,
                    "provenance": record.provenance,
                }
                for record in bundle.acquisition_records
            ),
            "cluster_links": tuple(
                {
                    "cluster_id": cluster.cluster_id,
                    "member_acquisition_ids": cluster.member_acquisition_ids,
                    "compatible_member_ids": cluster.compatible_member_ids,
                    "competing_member_ids": cluster.competing_member_ids,
                    "confidence": cluster.confidence,
                    "provenance": cluster.provenance,
                }
                for cluster in bundle.cluster_links
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_perspective_chain_ref": result.telemetry.source_perspective_chain_ref,
            "source_applicability_ref": result.telemetry.source_applicability_ref,
            "source_runtime_graph_ref": result.telemetry.source_runtime_graph_ref,
            "source_grounded_ref": result.telemetry.source_grounded_ref,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "acquisition_record_count": result.telemetry.acquisition_record_count,
            "cluster_link_count": result.telemetry.cluster_link_count,
            "acquisition_statuses": result.telemetry.acquisition_statuses,
            "stability_classes": result.telemetry.stability_classes,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_acquisition_ids": result.telemetry.downstream_gate.accepted_acquisition_ids,
                "rejected_acquisition_ids": result.telemetry.downstream_gate.rejected_acquisition_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
