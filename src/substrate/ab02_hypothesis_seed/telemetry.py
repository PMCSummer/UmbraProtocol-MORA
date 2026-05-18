from __future__ import annotations

from .models import AB2HypothesisSeed, AB2HypothesisSeedInput, AB2SeedStatus, AB2Telemetry


def build_ab2_telemetry(
    *,
    candidate_input: AB2HypothesisSeedInput,
    hypotheses: tuple[AB2HypothesisSeed, ...],
    unsafe_basis_count: int,
) -> AB2Telemetry:
    usable_count = sum(1 for item in hypotheses if item.seed_status is AB2SeedStatus.USABLE)
    blocked_count = sum(1 for item in hypotheses if item.seed_status is AB2SeedStatus.BLOCKED)
    return AB2Telemetry(
        tick_ref=candidate_input.tick_ref,
        seed_count=len(hypotheses),
        usable_seed_count=usable_count,
        blocked_seed_count=blocked_count,
        ambiguous_events_count=1 if len(candidate_input.event_digests) >= 1 else 0,
        unsafe_basis_count=unsafe_basis_count,
        no_seed_count=1 if not hypotheses else 0,
        hidden_eval_excluded=candidate_input.hidden_eval_excluded,
        scenario_label_excluded=candidate_input.scenario_label_excluded,
    )
