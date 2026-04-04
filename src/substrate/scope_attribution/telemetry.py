from __future__ import annotations

from substrate.scope_attribution.models import (
    ApplicabilityBundle,
    ApplicabilityGateDecision,
    ApplicabilityResult,
    ApplicabilityTelemetry,
)


def build_applicability_telemetry(
    *,
    bundle: ApplicabilityBundle,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: ApplicabilityGateDecision,
    causal_basis: str,
) -> ApplicabilityTelemetry:
    return ApplicabilityTelemetry(
        source_lineage=source_lineage,
        source_runtime_graph_ref=bundle.source_runtime_graph_ref,
        source_grounded_ref=bundle.source_grounded_ref,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        record_count=len(bundle.records),
        permission_mapping_count=len(bundle.permission_mappings),
        source_scope_classes=tuple(dict.fromkeys(record.source_scope_class.value for record in bundle.records)),
        target_scope_classes=tuple(dict.fromkeys(record.target_scope_class.value for record in bundle.records)),
        applicability_classes=tuple(dict.fromkeys(record.applicability_class.value for record in bundle.records)),
        self_applicability_statuses=tuple(dict.fromkeys(record.self_applicability_status.value for record in bundle.records)),
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def applicability_result_snapshot(result: ApplicabilityResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_truth_upgrade": result.no_truth_upgrade,
        "bundle": {
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
            "no_truth_upgrade": bundle.no_truth_upgrade,
            "reason": bundle.reason,
            "records": tuple(
                {
                    "attribution_id": record.attribution_id,
                    "semantic_unit_id": record.semantic_unit_id,
                    "proposition_id": record.proposition_id,
                    "source_scope_class": record.source_scope_class.value,
                    "target_scope_class": record.target_scope_class.value,
                    "applicability_class": record.applicability_class.value,
                    "commitment_level": record.commitment_level.value,
                    "self_applicability_status": record.self_applicability_status.value,
                    "downstream_permissions": record.downstream_permissions,
                    "confidence": record.confidence,
                    "provenance": record.provenance,
                }
                for record in bundle.records
            ),
            "permission_mappings": tuple(
                {
                    "proposition_id": mapping.proposition_id,
                    "permissions": mapping.permissions,
                    "blocked_reasons": mapping.blocked_reasons,
                    "confidence": mapping.confidence,
                }
                for mapping in bundle.permission_mappings
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_runtime_graph_ref": result.telemetry.source_runtime_graph_ref,
            "source_grounded_ref": result.telemetry.source_grounded_ref,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "record_count": result.telemetry.record_count,
            "permission_mapping_count": result.telemetry.permission_mapping_count,
            "source_scope_classes": result.telemetry.source_scope_classes,
            "target_scope_classes": result.telemetry.target_scope_classes,
            "applicability_classes": result.telemetry.applicability_classes,
            "self_applicability_statuses": result.telemetry.self_applicability_statuses,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_record_ids": result.telemetry.downstream_gate.accepted_record_ids,
                "rejected_record_ids": result.telemetry.downstream_gate.rejected_record_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
