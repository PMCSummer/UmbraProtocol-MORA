from __future__ import annotations

from dataclasses import asdict

from .models import CostValidationResult


def cost1_snapshot(result: CostValidationResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": result.status.value,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "vector_refs": result.vector_refs,
        "authority_flags": asdict(result.authority_flags),
    }
    if result.comparison is not None:
        payload["comparison"] = {
            "comparison_id": result.comparison.comparison_id,
            "candidates": result.comparison.compared_candidate_refs,
            "validation_status": result.comparison.validation_status.value,
            "dimension_breakdown_refs": result.comparison.dimension_breakdown_refs,
            "mismatch_residue_refs": result.comparison.mismatch_residue_refs,
        }
    return payload
