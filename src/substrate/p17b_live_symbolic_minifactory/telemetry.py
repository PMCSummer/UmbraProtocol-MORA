from __future__ import annotations

from dataclasses import asdict

from .models import P17BLiveMiniFactoryRun
from .policy import summarize_p17b_run


def p17b_run_snapshot(run: P17BLiveMiniFactoryRun) -> dict[str, object]:
    summary = summarize_p17b_run(run)
    return {
        "summary": summary,
        "step_traces": tuple(
            {
                "step_id": trace.step_id,
                "status": trace.status.value,
                "ap01_request_refs": trace.ap01_request_refs,
                "backend_execution_refs": trace.backend_execution_refs,
                "world_effect_feedback_refs": trace.world_effect_feedback_refs,
                "verified_intermediate_refs": trace.verified_intermediate_refs,
                "blocked_reasons": tuple(reason.value for reason in trace.blocked_reasons),
                "residue_refs": trace.residue_refs,
                "uncertainty_refs": trace.uncertainty_refs,
            }
            for trace in run.step_traces
        ),
        "counters": asdict(run.counters),
        "authority_flags": asdict(run.authority_flags),
    }

