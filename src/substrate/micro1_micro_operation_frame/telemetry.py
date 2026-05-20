from __future__ import annotations

from dataclasses import asdict

from .models import MicroOperationValidationResult


def micro1_operation_snapshot(result: MicroOperationValidationResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": result.status.value,
        "operation_status": result.operation_status.value if result.operation_status is not None else None,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "authority_flags": asdict(result.authority_flags),
    }
    if result.operation is not None:
        payload["operation"] = {
            "operation_id": result.operation.operation_id,
            "operation_kind": result.operation.operation_kind.value,
            "status": result.operation.status.value,
            "target_affordance_refs": result.operation.target_affordance_refs,
            "action_surface_refs": result.operation.action_surface_refs,
            "residue_frame_refs": result.operation.residue_frame_refs,
        }
    if result.graph is not None:
        payload["graph"] = {
            "graph_id": result.graph.graph_id,
            "graph_status": result.graph.graph_status.value,
            "operation_refs": result.graph.operation_refs,
            "blocked_edges": result.graph.blocked_edges,
            "unresolved_refs": result.graph.unresolved_refs,
        }
    return payload
