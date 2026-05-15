from __future__ import annotations

from .models import ScenarioResult


def summarize_result(result: ScenarioResult) -> dict[str, object]:
    falsifier_summary = {
        item.name: item.passed
        for item in result.falsifier_results
    }
    return {
        "scenario_id": result.scenario_id,
        "stage": result.stage.value,
        "packet_count": len(result.emitted_packets),
        "phase_obligation_count": len(result.phase_obligation_summary),
        "falsifier_summary": falsifier_summary,
        "claim_discipline_markers": result.claim_discipline_markers,
    }
