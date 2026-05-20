from __future__ import annotations

from dataclasses import asdict

from .models import ContactConformanceResult


def umwelt0_contact_snapshot(result: ContactConformanceResult) -> dict[str, object]:
    frame = result.phenomenal_contact_frame
    counters = result.counters
    return {
        "frame_id": frame.frame_id,
        "validation_status": frame.validation_status.value,
        "accepted_refs": result.accepted_refs,
        "blocked_refs": result.blocked_refs,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "authority": asdict(frame.authority_flags),
        "hidden_eval_used": frame.hidden_eval_used,
        "scenario_label_used": frame.scenario_label_used,
        "backend_truth_excluded": frame.backend_truth_excluded,
        "action_request_emitted": frame.action_request_emitted,
        "world_submission_emitted": frame.world_submission_emitted,
        "fact_claimed": frame.fact_claimed,
        "cause_confirmed": frame.cause_confirmed,
        "mature_recipe_claimed": frame.mature_recipe_claimed,
        "automation_claimed": frame.automation_claimed,
        "value_assigned": frame.value_assigned,
        "counters": asdict(counters),
    }
