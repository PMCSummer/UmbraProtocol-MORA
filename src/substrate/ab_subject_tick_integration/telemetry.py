from __future__ import annotations

from .models import ABLiveCounters, ABLiveStageTrace


def counters_from_stage_traces(stage_traces: tuple[ABLiveStageTrace, ...]) -> ABLiveCounters:
    counters = ABLiveCounters(
        ab1_digest_count=0,
        ab2_seed_count=0,
        ab3_frontier_count=0,
        ab4_basis_count=0,
        ab5_update_count=0,
        ab6_attribution_count=0,
        ab7_constraint_count=0,
        skipped_no_public_basis_count=sum(1 for item in stage_traces if item.skipped_reason == "no_public_basis"),
        blocked_protected_eval_count=sum(1 for item in stage_traces if item.error_or_blocked_reason == "protected_eval_present"),
        blocked_scenario_label_count=sum(1 for item in stage_traces if item.error_or_blocked_reason == "scenario_label_present"),
    )
    return counters
