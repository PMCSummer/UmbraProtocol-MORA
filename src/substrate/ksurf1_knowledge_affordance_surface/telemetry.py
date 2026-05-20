from __future__ import annotations

from dataclasses import asdict

from .models import KnowledgeSurfaceValidationResult


def ksurf1_affordance_snapshot(result: KnowledgeSurfaceValidationResult) -> dict[str, object]:
    frame = result.frame
    payload: dict[str, object] = {
        "status": result.status.value,
        "blocked_reasons": result.blocked_reasons,
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "authority_flags": asdict(result.authority_flags),
    }
    if frame is not None:
        payload["frame"] = {
            "frame_id": frame.frame_id,
            "provider_count": len(frame.provider_refs),
            "claim_count": len(frame.provider_claim_refs),
            "hint_count": len(frame.knowledge_hint_refs),
            "locked_slot_count": len(frame.locked_slot_refs),
            "partial_slot_count": len(frame.partial_slot_refs),
            "conflict_count": len(frame.provider_conflict_refs),
            "validation_status": frame.validation_status.value,
            "action_request_emitted": frame.action_request_emitted,
            "action_selected": frame.action_selected,
            "goal_selected": frame.goal_selected,
            "fact_claimed": frame.fact_claimed,
            "cause_confirmed": frame.cause_confirmed,
            "value_assigned": frame.value_assigned,
            "mature_recipe_claimed": frame.mature_recipe_claimed,
            "mature_skill_claimed": frame.mature_skill_claimed,
            "automation_claimed": frame.automation_claimed,
        }
    return payload

