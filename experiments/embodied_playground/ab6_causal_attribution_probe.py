from __future__ import annotations

from dataclasses import dataclass

from substrate.ab06_causal_attribution import AB6CausalAttributionInput, AB6CausalAttributionResult, build_ab6_causal_attribution

from .ab3_hypothesis_frontier_probe import run_ab3_probe_case
from .ab5_hypothesis_update_probe import run_ab5_probe_case
from .ownership_perturbation import run_ownership_perturbation_case


@dataclass(frozen=True, slots=True)
class AB6ProbeCase:
    case_id: str
    description: str


def list_ab6_probe_cases() -> tuple[AB6ProbeCase, ...]:
    return (
        AB6ProbeCase("self_action_correlated_effect", "self action with AP01+correlated effect"),
        AB6ProbeCase("world_only_change", "world-only public change without AP01"),
        AB6ProbeCase("other_actor_change", "other actor change should not be self"),
        AB6ProbeCase("delayed_self_effect", "delayed self effect is not immediate self closure"),
        AB6ProbeCase("mixed_self_world_effect", "mixed self/world cause preserved"),
        AB6ProbeCase("unknown_unexplained_effect", "unknown cause preserved"),
        AB6ProbeCase("sensor_projection_mismatch", "mismatch candidate without world-fact closure"),
        AB6ProbeCase("blocked_action_no_success", "blocked action does not become success claim"),
        AB6ProbeCase("hidden_eval_only_cause", "hidden/eval-only basis rejected"),
    )


def run_ab6_probe_case(case_id: str) -> AB6CausalAttributionResult:
    if case_id == "self_action_correlated_effect":
        return _run_from_ownership("self_caused_move_effect", ab5_case="correlated_effect_support_increase", effect_correlated=True)
    if case_id == "world_only_change":
        return _run_from_ownership("world_only_object_change", ab5_case="uncorrelated_effect_weak_or_blocked_update", effect_correlated=False)
    if case_id == "other_actor_change":
        return _run_from_ownership("other_actor_object_change", ab5_case="uncorrelated_effect_weak_or_blocked_update", effect_correlated=False, other_actor=True)
    if case_id == "delayed_self_effect":
        return _run_from_ownership("delayed_self_effect", ab5_case="ambiguous_effect_no_closure", effect_correlated=False, delayed=True)
    if case_id == "mixed_self_world_effect":
        return _run_from_ownership("mixed_self_and_world_effect", ab5_case="correlated_effect_support_increase", effect_correlated=True, mixed=True)
    if case_id == "unknown_unexplained_effect":
        return _run_from_ownership("unknown_unexplained_effect", ab5_case="no_effect_no_update", effect_correlated=False, unknown=True)
    if case_id == "sensor_projection_mismatch":
        return _run_from_ownership("sensor_or_projection_mismatch", ab5_case="ambiguous_effect_no_closure", effect_correlated=False, mismatch=True)
    if case_id == "blocked_action_no_success":
        return _run_from_ownership("blocked_self_action_no_world_delta", ab5_case="disconfirming_effect_support_decrease", effect_correlated=True, blocked=True)
    if case_id == "hidden_eval_only_cause":
        # Explicitly reject hidden/eval-only basis.
        owner = run_ownership_perturbation_case("hidden_eval_only_cause")
        fallback_frontier = run_ab3_probe_case("effect_mismatch").frontier
        frontier_refs = owner.frontier_refs or ((fallback_frontier.frontier_id,) if fallback_frontier is not None else ("ab3:probe:fallback",))
        return build_ab6_causal_attribution(
            AB6CausalAttributionInput(
                tick_ref="ab6:probe:hidden_eval_only_cause",
                source_frontier_refs=frontier_refs,
                source_update_refs=(),
                source_event_digest_refs=owner.event_digest_refs,
                source_effect_refs=owner.effect_refs,
                source_request_refs=owner.ap01_request_refs,
                source_candidate_refs=owner.self_action_refs,
                source_observation_refs=(f"ownership:{owner.scenario_id}",),
                timing_refs=("tick:1",),
                external_event_refs=owner.external_event_refs,
                other_actor_refs=(),
                uncertainty_refs=("hidden_eval_only",),
                missing_evidence_refs=("public_evidence_required",),
                effect_correlated=False,
                blocked_action=False,
                delayed_marker=False,
                mixed_marker=False,
                unknown_marker=True,
                sensor_mismatch_marker=False,
                public_only=True,
                hidden_eval_excluded=False,
                scenario_label_excluded=True,
                source="ab6_probe.hidden_eval_only_cause",
            )
        )
    raise ValueError(f"Unknown AB6 probe case: {case_id}")


def _run_from_ownership(
    scenario_id: str,
    *,
    ab5_case: str,
    effect_correlated: bool,
    other_actor: bool = False,
    delayed: bool = False,
    mixed: bool = False,
    unknown: bool = False,
    mismatch: bool = False,
    blocked: bool = False,
) -> AB6CausalAttributionResult:
    owner = run_ownership_perturbation_case(scenario_id)
    ab5 = run_ab5_probe_case(ab5_case)
    fallback_frontier = run_ab3_probe_case("effect_mismatch").frontier
    frontier_refs = owner.frontier_refs or ((fallback_frontier.frontier_id,) if fallback_frontier is not None else ("ab3:probe:fallback",))
    update_refs = (ab5.update.update_id,) if ab5.update is not None else ()
    return build_ab6_causal_attribution(
        AB6CausalAttributionInput(
            tick_ref=f"ab6:probe:{scenario_id}",
            source_frontier_refs=frontier_refs,
            source_update_refs=update_refs,
            source_event_digest_refs=owner.event_digest_refs,
            source_effect_refs=owner.effect_refs,
            source_request_refs=owner.ap01_request_refs,
            source_candidate_refs=owner.self_action_refs,
            source_observation_refs=(f"ownership:{owner.scenario_id}",),
            timing_refs=("tick:1", "tick:2") if delayed else ("tick:1",),
            external_event_refs=owner.external_event_refs,
            other_actor_refs=("other_actor:public:1",) if other_actor else (),
            uncertainty_refs=("ownership_uncertain",),
            missing_evidence_refs=owner.ownership_assessment.missing_evidence,
            effect_correlated=effect_correlated,
            blocked_action=blocked,
            delayed_marker=delayed,
            mixed_marker=mixed,
            unknown_marker=unknown,
            sensor_mismatch_marker=mismatch,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source=f"ab6_probe.{scenario_id}",
        )
    )
