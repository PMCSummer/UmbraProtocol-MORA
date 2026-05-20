from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from substrate.ab03_hypothesis_frontier import AB3ExplanationFrontier
from substrate.ab07_recipe_automation_integration import (
    AB7PrecursorCandidateRecord,
    AB7RecipeCandidateRecord,
)


@dataclass(frozen=True, slots=True)
class ABLiveTickInput:
    tick_id: str
    public_observation_refs: tuple[str, ...]
    public_effect_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    action_effect_refs: tuple[str, ...]
    prior_frontier_refs: tuple[str, ...]
    prior_ab_state_refs: tuple[str, ...]
    recipe_candidate_refs: tuple[str, ...]
    precursor_candidate_refs: tuple[str, ...]
    value_chain_refs: tuple[str, ...]
    factory_chain_refs: tuple[str, ...]
    protected_eval_present: bool = False
    scenario_label_present: bool = False
    prior_frontier_object: AB3ExplanationFrontier | None = None
    recipe_candidate_records: tuple[AB7RecipeCandidateRecord, ...] = ()
    precursor_candidate_records: tuple[AB7PrecursorCandidateRecord, ...] = ()
    p13_credit_refs: tuple[str, ...] = ()
    p14_station_affordance_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ABLiveTickConfig:
    enable_ab_live_contour: bool = False
    run_ab1: bool = True
    run_ab2: bool = True
    run_ab3: bool = True
    run_ab4: bool = True
    run_ab5: bool = True
    run_ab6: bool = True
    run_ab7: bool = True
    max_event_digests: int = 8
    max_hypothesis_seeds: int = 16
    max_frontier_hypotheses: int = 12
    max_epistemic_basis_items: int = 8
    strict_public_basis_only: bool = True
    no_action_authority: bool = True
    no_publication_authority: bool = True
    no_execution_authority: bool = True


@dataclass(frozen=True, slots=True)
class ABLiveCounters:
    ab1_digest_count: int = 0
    ab2_seed_count: int = 0
    ab3_frontier_count: int = 0
    ab4_basis_count: int = 0
    ab5_update_count: int = 0
    ab6_attribution_count: int = 0
    ab7_constraint_count: int = 0
    skipped_no_public_basis_count: int = 0
    blocked_protected_eval_count: int = 0
    blocked_scenario_label_count: int = 0
    action_authority_violation_count: int = 0
    fact_closure_violation_count: int = 0
    performance_guard_triggered_count: int = 0


@dataclass(frozen=True, slots=True)
class ABLiveStageTrace:
    stage_name: str
    ran: bool
    skipped_reason: str | None
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    authority_flags: tuple[str, ...]
    duration_ms: int | None = None
    error_or_blocked_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ABLiveTickResult:
    tick_id: str
    ab1_event_digest_refs: tuple[str, ...]
    ab2_seed_set_refs: tuple[str, ...]
    ab3_frontier_refs: tuple[str, ...]
    ab4_epistemic_basis_refs: tuple[str, ...]
    ab5_update_refs: tuple[str, ...]
    ab6_attribution_refs: tuple[str, ...]
    ab7_constraint_refs: tuple[str, ...]
    ab_live_counters: ABLiveCounters
    stage_traces: tuple[ABLiveStageTrace, ...]
    blocked_reasons: tuple[str, ...]
    skipped_reasons: tuple[str, ...]
    public_basis_refs: tuple[str, ...]
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    fact_claimed: bool = False
    cause_confirmed: bool = False
    action_request_emitted: bool = False
    world_submission_emitted: bool = False
    automation_claimed: bool = False
    mature_recipe_claimed: bool = False
    subject_tick_state_mutation_scope: str = "ab_live_fields_only"
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
