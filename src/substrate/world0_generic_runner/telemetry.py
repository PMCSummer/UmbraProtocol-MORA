from __future__ import annotations

from dataclasses import asdict

from .models import WorldRunnerLoopResult


def world0_runner_snapshot(result: WorldRunnerLoopResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "run_id": result.run_id,
        "final_status": result.final_status.value,
        "cycle_count": len(result.cycle_traces),
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "counters": asdict(result.counters),
        "replay_trace_ref": result.replay_trace_ref,
        "residue_refs": result.residue_refs,
        "uncertainty_refs": result.uncertainty_refs,
        "no_action_selected_by_runner": result.no_action_selected_by_runner,
        "no_ap01_created_by_runner": result.no_ap01_created_by_runner,
        "no_world_submission_without_ap01": result.no_world_submission_without_ap01,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "recipe_matured": result.recipe_matured,
        "skill_matured": result.skill_matured,
        "automation_claimed": result.automation_claimed,
        "factory_solution_hardcoded": result.factory_solution_hardcoded,
    }
    if result.cycle_traces:
        payload["cycle_refs"] = tuple(item.cycle_id for item in result.cycle_traces)
    return payload
