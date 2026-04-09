from __future__ import annotations

from substrate.t02_relation_binding.models import T02ConstrainedSceneResult


def t02_constrained_scene_snapshot(result: T02ConstrainedSceneResult) -> dict[str, object]:
    if not isinstance(result, T02ConstrainedSceneResult):
        raise TypeError("t02_constrained_scene_snapshot requires T02ConstrainedSceneResult")
    return {
        "state": {
            "constrained_scene_id": result.state.constrained_scene_id,
            "source_t01_scene_id": result.state.source_t01_scene_id,
            "source_t01_scene_status": result.state.source_t01_scene_status,
            "raw_scene_nodes": result.state.raw_scene_nodes,
            "raw_relation_candidates": result.state.raw_relation_candidates,
            "relation_bindings": tuple(
                {
                    "binding_id": item.binding_id,
                    "source_nodes": item.source_nodes,
                    "relation_type": item.relation_type,
                    "role_constraints": item.role_constraints,
                    "authority_basis": item.authority_basis,
                    "confidence": item.confidence,
                    "status": item.status.value,
                    "downstream_effects": item.downstream_effects,
                    "provenance": item.provenance,
                }
                for item in result.state.relation_bindings
            ),
            "constraint_objects": tuple(
                {
                    "constraint_id": item.constraint_id,
                    "origin": item.origin,
                    "scope": item.scope,
                    "polarity": item.polarity.value,
                    "authority_basis": item.authority_basis,
                    "applicability_limits": item.applicability_limits,
                    "propagation_status": item.propagation_status.value,
                    "provenance": item.provenance,
                }
                for item in result.state.constraint_objects
            ),
            "propagation_records": tuple(
                {
                    "propagation_id": item.propagation_id,
                    "trigger_binding_or_constraint": item.trigger_binding_or_constraint,
                    "affected_nodes_or_roles": item.affected_nodes_or_roles,
                    "effect_type": item.effect_type.value,
                    "scope": item.scope,
                    "stop_reason_or_none": item.stop_reason_or_none,
                    "status": item.status.value,
                    "provenance": item.provenance,
                }
                for item in result.state.propagation_records
            ),
            "conflict_records": tuple(
                {
                    "conflict_id": item.conflict_id,
                    "conflicting_bindings_or_constraints": item.conflicting_bindings_or_constraints,
                    "conflict_class": item.conflict_class,
                    "preserved_status": item.preserved_status,
                    "overwrite_forbidden": item.overwrite_forbidden,
                    "downstream_visibility": item.downstream_visibility,
                    "provenance": item.provenance,
                }
                for item in result.state.conflict_records
            ),
            "narrowed_role_candidates": result.state.narrowed_role_candidates,
            "scene_status": result.state.scene_status.value,
            "operations_applied": result.state.operations_applied,
            "source_authority_tags": result.state.source_authority_tags,
            "source_lineage": result.state.source_lineage,
            "provenance": result.state.provenance,
        },
        "gate": {
            "pre_verbal_constraint_consumer_ready": result.gate.pre_verbal_constraint_consumer_ready,
            "no_clean_binding_commit": result.gate.no_clean_binding_commit,
            "forbidden_shortcuts": result.gate.forbidden_shortcuts,
            "restrictions": result.gate.restrictions,
            "reason": result.gate.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "rt01_contour_only": result.scope_marker.rt01_contour_only,
            "t02_first_slice_only": result.scope_marker.t02_first_slice_only,
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
            "constrained_scene_id": result.telemetry.constrained_scene_id,
            "source_t01_scene_id": result.telemetry.source_t01_scene_id,
            "scene_status": result.telemetry.scene_status.value,
            "relation_bindings_count": result.telemetry.relation_bindings_count,
            "confirmed_bindings_count": result.telemetry.confirmed_bindings_count,
            "provisional_bindings_count": result.telemetry.provisional_bindings_count,
            "blocked_bindings_count": result.telemetry.blocked_bindings_count,
            "conflicted_bindings_count": result.telemetry.conflicted_bindings_count,
            "constraint_objects_count": result.telemetry.constraint_objects_count,
            "propagation_records_count": result.telemetry.propagation_records_count,
            "stopped_propagation_count": result.telemetry.stopped_propagation_count,
            "conflict_records_count": result.telemetry.conflict_records_count,
            "pre_verbal_constraint_consumer_ready": result.telemetry.pre_verbal_constraint_consumer_ready,
            "no_clean_binding_commit": result.telemetry.no_clean_binding_commit,
            "forbidden_shortcuts": result.telemetry.forbidden_shortcuts,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
