from __future__ import annotations

from substrate.runtime_semantic_graph.models import (
    RuntimeGraphBundle,
    RuntimeGraphGateDecision,
    RuntimeGraphResult,
    RuntimeGraphTelemetry,
)


def build_runtime_graph_telemetry(
    *,
    bundle: RuntimeGraphBundle,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: RuntimeGraphGateDecision,
    causal_basis: str,
) -> RuntimeGraphTelemetry:
    return RuntimeGraphTelemetry(
        source_lineage=source_lineage,
        source_grounded_ref=bundle.source_grounded_ref,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        semantic_unit_count=len(bundle.semantic_units),
        role_binding_count=len(bundle.role_bindings),
        edge_count=len(bundle.graph_edges),
        proposition_count=len(bundle.proposition_candidates),
        alternative_count=len(bundle.graph_alternatives),
        unresolved_role_slot_count=len(bundle.unresolved_role_slots),
        polarity_classes=tuple(
            dict.fromkeys(candidate.polarity.value for candidate in bundle.proposition_candidates)
        ),
        certainty_classes=tuple(
            dict.fromkeys(candidate.certainty_class.value for candidate in bundle.proposition_candidates)
        ),
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def runtime_graph_result_snapshot(result: RuntimeGraphResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_semantic_closure": result.no_final_semantic_closure,
        "bundle": {
            "source_grounded_ref": bundle.source_grounded_ref,
            "source_dictum_ref": bundle.source_dictum_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_scaffold_ids": bundle.linked_scaffold_ids,
            "linked_dictum_ids": bundle.linked_dictum_ids,
            "unresolved_role_slots": bundle.unresolved_role_slots,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "low_coverage_mode": bundle.low_coverage_mode,
            "low_coverage_reasons": bundle.low_coverage_reasons,
            "no_final_semantic_closure": bundle.no_final_semantic_closure,
            "reason": bundle.reason,
            "semantic_units": tuple(
                {
                    "semantic_unit_id": unit.semantic_unit_id,
                    "unit_kind": unit.unit_kind.value,
                    "predicate": unit.predicate,
                    "role_bindings": unit.role_bindings,
                    "modifier_links": unit.modifier_links,
                    "source_scope": unit.source_scope,
                    "dictum_or_modus_class": unit.dictum_or_modus_class.value,
                    "polarity": unit.polarity.value,
                    "certainty_class": unit.certainty_class.value,
                    "provenance": unit.provenance,
                    "confidence": unit.confidence,
                }
                for unit in bundle.semantic_units
            ),
            "role_bindings": tuple(
                {
                    "binding_id": binding.binding_id,
                    "frame_node_id": binding.frame_node_id,
                    "role_label": binding.role_label,
                    "target_ref": binding.target_ref,
                    "unresolved": binding.unresolved,
                    "unresolved_reason": binding.unresolved_reason,
                    "confidence": binding.confidence,
                    "provenance": binding.provenance,
                }
                for binding in bundle.role_bindings
            ),
            "graph_edges": tuple(
                {
                    "edge_id": edge.edge_id,
                    "source_node_id": edge.source_node_id,
                    "target_node_id": edge.target_node_id,
                    "edge_kind": edge.edge_kind,
                    "uncertain": edge.uncertain,
                    "reason": edge.reason,
                    "confidence": edge.confidence,
                }
                for edge in bundle.graph_edges
            ),
            "proposition_candidates": tuple(
                {
                    "proposition_id": candidate.proposition_id,
                    "frame_node_id": candidate.frame_node_id,
                    "role_binding_ids": candidate.role_binding_ids,
                    "source_scope_refs": candidate.source_scope_refs,
                    "dictum_or_modus_class": candidate.dictum_or_modus_class.value,
                    "polarity": candidate.polarity.value,
                    "certainty_class": candidate.certainty_class.value,
                    "unresolved": candidate.unresolved,
                    "confidence": candidate.confidence,
                    "provenance": candidate.provenance,
                }
                for candidate in bundle.proposition_candidates
            ),
            "graph_alternatives": tuple(
                {
                    "alternative_id": alternative.alternative_id,
                    "competing_ref_ids": alternative.competing_ref_ids,
                    "reason": alternative.reason,
                    "confidence": alternative.confidence,
                }
                for alternative in bundle.graph_alternatives
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_grounded_ref": result.telemetry.source_grounded_ref,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "semantic_unit_count": result.telemetry.semantic_unit_count,
            "role_binding_count": result.telemetry.role_binding_count,
            "edge_count": result.telemetry.edge_count,
            "proposition_count": result.telemetry.proposition_count,
            "alternative_count": result.telemetry.alternative_count,
            "unresolved_role_slot_count": result.telemetry.unresolved_role_slot_count,
            "polarity_classes": result.telemetry.polarity_classes,
            "certainty_classes": result.telemetry.certainty_classes,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_proposition_ids": result.telemetry.downstream_gate.accepted_proposition_ids,
                "rejected_proposition_ids": result.telemetry.downstream_gate.rejected_proposition_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
