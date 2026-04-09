from __future__ import annotations

from substrate.t01_semantic_field.models import T01ActiveFieldResult


def t01_active_field_snapshot(result: T01ActiveFieldResult) -> dict[str, object]:
    if not isinstance(result, T01ActiveFieldResult):
        raise TypeError("t01_active_field_snapshot requires T01ActiveFieldResult")
    return {
        "state": {
            "scene_id": result.state.scene_id,
            "scene_status": result.state.scene_status.value,
            "active_entities": tuple(
                {
                    "entity_id": entity.entity_id,
                    "label": entity.label,
                    "entity_type": entity.entity_type,
                    "provisional": entity.provisional,
                    "source_authority_tag": entity.source_authority_tag,
                }
                for entity in result.state.active_entities
            ),
            "relation_edges": tuple(
                {
                    "edge_id": edge.edge_id,
                    "source_entity_id": edge.source_entity_id,
                    "relation_type": edge.relation_type,
                    "target_entity_id": edge.target_entity_id,
                    "weight": edge.weight,
                    "provisional": edge.provisional,
                    "contested": edge.contested,
                    "source_authority_tag": edge.source_authority_tag,
                }
                for edge in result.state.relation_edges
            ),
            "role_bindings": tuple(
                {
                    "role_id": binding.role_id,
                    "entity_id": binding.entity_id,
                    "binding_confidence": binding.binding_confidence,
                    "provisional": binding.provisional,
                    "unresolved": binding.unresolved,
                    "source_authority_tag": binding.source_authority_tag,
                }
                for binding in result.state.role_bindings
            ),
            "active_predicates": result.state.active_predicates,
            "unresolved_slots": tuple(
                {
                    "slot_id": slot.slot_id,
                    "slot_kind": slot.slot_kind,
                    "candidate_entity_ids": slot.candidate_entity_ids,
                    "contested": slot.contested,
                    "reason": slot.reason,
                }
                for slot in result.state.unresolved_slots
            ),
            "attention_weights": result.state.attention_weights,
            "salience_weights": result.state.salience_weights,
            "temporal_links": tuple(
                {
                    "link_id": link.link_id,
                    "source_entity_id": link.source_entity_id,
                    "target_entity_id": link.target_entity_id,
                    "temporal_relation": link.temporal_relation,
                    "provisional": link.provisional,
                }
                for link in result.state.temporal_links
            ),
            "expectation_links": tuple(
                {
                    "link_id": link.link_id,
                    "source_entity_id": link.source_entity_id,
                    "target_entity_id": link.target_entity_id,
                    "predicate": link.predicate,
                    "confidence": link.confidence,
                    "provisional": link.provisional,
                }
                for link in result.state.expectation_links
            ),
            "source_authority_tags": result.state.source_authority_tags,
            "stability_state": result.state.stability_state.value,
            "operations_applied": result.state.operations_applied,
            "wording_surface_ref": result.state.wording_surface_ref,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "pre_verbal_consumer_ready": result.gate.pre_verbal_consumer_ready,
            "no_clean_scene_commit": result.gate.no_clean_scene_commit,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "t01_first_slice_only": result.scope_marker.t01_first_slice_only,
            "t02_implemented": result.scope_marker.t02_implemented,
            "t03_implemented": result.scope_marker.t03_implemented,
            "t04_implemented": result.scope_marker.t04_implemented,
            "o01_implemented": result.scope_marker.o01_implemented,
            "full_silent_thought_line_implemented": (
                result.scope_marker.full_silent_thought_line_implemented
            ),
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "scene_id": result.telemetry.scene_id,
            "scene_status": result.telemetry.scene_status.value,
            "stability_state": result.telemetry.stability_state.value,
            "active_entities_count": result.telemetry.active_entities_count,
            "relation_edges_count": result.telemetry.relation_edges_count,
            "unresolved_slots_count": result.telemetry.unresolved_slots_count,
            "contested_relations_count": result.telemetry.contested_relations_count,
            "pre_verbal_consumer_ready": result.telemetry.pre_verbal_consumer_ready,
            "no_clean_scene_commit": result.telemetry.no_clean_scene_commit,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
