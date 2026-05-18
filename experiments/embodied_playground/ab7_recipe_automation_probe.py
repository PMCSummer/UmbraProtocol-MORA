from __future__ import annotations

from dataclasses import dataclass

from substrate.ab07_recipe_automation_integration import (
    AB7PrecursorCandidateRecord,
    AB7RecipeAutomationInput,
    AB7RecipeCandidateRecord,
    AB7IntegrationEnvelope,
    build_ab7_recipe_automation_integration,
)

from .ab3_hypothesis_frontier_probe import run_ab3_probe_case
from .ab5_hypothesis_update_probe import run_ab5_probe_case
from .ab6_causal_attribution_probe import run_ab6_probe_case
from .delayed_credit_scenarios import delayed_credit_scenario_for_id
from .delayed_credit_learning import run_delayed_credit_learning_case
from .recipe_precursor_learning import run_recipe_precursor_learning_case
from .recipe_precursor_scenarios import recipe_precursor_scenario_for_id
from .station_affordance import run_station_affordance_case


@dataclass(frozen=True, slots=True)
class AB7ProbeCase:
    case_id: str
    description: str


def list_ab7_probe_cases() -> tuple[AB7ProbeCase, ...]:
    return (
        AB7ProbeCase("p15_candidate_bound_to_ab_frontier", "P15 candidate bound to AB frontier/update/attribution refs"),
        AB7ProbeCase("p15_candidate_requires_p13_gate", "Missing P13 gate refs blocks maturity"),
        AB7ProbeCase("repeated_trace_candidate_with_ab_support", "Repeated trace candidate remains non-automation"),
        AB7ProbeCase("disconfirming_effect_blocks_recipe_integration", "Disconfirming trace blocks integration"),
        AB7ProbeCase("active_confounder_blocks_recipe_maturity", "Active confounder blocks maturity/readiness"),
        AB7ProbeCase("station_affordance_missing_blocks_integration", "Missing P14 affordance blocks integration"),
        AB7ProbeCase("protected_eval_only_rule_rejected", "Protected evaluator-only rule is rejected"),
        AB7ProbeCase("one_success_trace_not_automation", "Single trace remains provisional and non-automation"),
        AB7ProbeCase("ambiguous_recipe_effect_preserves_frontier", "Ambiguity preserves unresolved frontier"),
        AB7ProbeCase("recipe_candidate_does_not_emit_action", "Frame has no action or world submission emission"),
        AB7ProbeCase("attribution_not_recipe_oracle", "AB6 attribution can support but not close recipe truth"),
        AB7ProbeCase("support_update_not_recipe_oracle", "AB5 update can support but not close recipe truth"),
    )


def run_ab7_probe_case(case_id: str) -> AB7IntegrationEnvelope:
    if case_id == "p15_candidate_bound_to_ab_frontier":
        return _build_from_p15("one_success_trace_provisional_only")
    if case_id == "p15_candidate_requires_p13_gate":
        return _build_from_p15("one_success_trace_provisional_only", drop_p13_gate=True)
    if case_id == "repeated_trace_candidate_with_ab_support":
        return _build_from_p15("repeated_consistent_traces_candidate_strengthens")
    if case_id == "disconfirming_effect_blocks_recipe_integration":
        return _build_from_p15("disconfirming_trace_blocks_maturity")
    if case_id == "active_confounder_blocks_recipe_maturity":
        return _build_from_p15("confounded_station_effect", force_active_confounder=True)
    if case_id == "station_affordance_missing_blocks_integration":
        return _build_from_p15("one_success_trace_provisional_only", drop_p14_affordance=True)
    if case_id == "protected_eval_only_rule_rejected":
        return _build_from_p15("hidden_recipe_only_no_candidate", protected_eval_only=True)
    if case_id == "one_success_trace_not_automation":
        return _build_from_p15("one_success_trace_provisional_only")
    if case_id == "ambiguous_recipe_effect_preserves_frontier":
        return _build_from_p15("ambiguous_output_effect", ambiguous_frontier=True)
    if case_id == "recipe_candidate_does_not_emit_action":
        return _build_from_p15("recipe_candidate_does_not_emit_action")
    if case_id == "attribution_not_recipe_oracle":
        return _build_from_p15("one_success_trace_provisional_only")
    if case_id == "support_update_not_recipe_oracle":
        return _build_from_p15("repeated_consistent_traces_candidate_strengthens")
    if case_id == "blocks_without_ab_frontier":
        return _build_from_p15("one_success_trace_provisional_only", drop_ab_frontier=True)
    raise ValueError(f"Unknown AB7 probe case: {case_id}")


def _build_from_p15(
    p15_case_id: str,
    *,
    drop_p13_gate: bool = False,
    drop_p14_affordance: bool = False,
    protected_eval_only: bool = False,
    drop_ab_frontier: bool = False,
    force_active_confounder: bool = False,
    ambiguous_frontier: bool = False,
) -> AB7IntegrationEnvelope:
    p15_run = run_recipe_precursor_learning_case(p15_case_id)
    scenario = recipe_precursor_scenario_for_id(p15_case_id)

    # Build from P15 candidates when present.
    recipe_candidates = tuple(_to_recipe_candidate(item) for item in p15_run.recipe_candidates)
    precursor_candidates = tuple(_to_precursor_candidate(item) for item in p15_run.precursor_candidates)

    # Gather upstream refs from AB/P13/P14 probes.
    ab3_case = "ambiguous_evidence" if (ambiguous_frontier or scenario.ambiguous_output) else "effect_mismatch"
    frontier = run_ab3_probe_case(ab3_case).frontier
    ab5_case = "disconfirming_effect_support_decrease" if scenario.expect_disconfirming else "correlated_effect_support_increase"
    ab5_probe = run_ab5_probe_case(ab5_case)
    ab6_case = "mixed_self_world_effect" if (force_active_confounder or scenario.expect_active_confounder) else "self_action_correlated_effect"
    ab6_probe = run_ab6_probe_case(ab6_case)

    p13_case = delayed_credit_scenario_for_id(scenario.p13_case_id)
    p13_run = run_delayed_credit_learning_case(p13_case.scenario_id)
    p14_run = run_station_affordance_case(scenario.p14_case_id)

    ab_frontier_refs = () if drop_ab_frontier else ((frontier.frontier_id,) if frontier is not None else ())
    unresolved_refs = ()
    if frontier is not None:
        unresolved_refs = tuple(frontier.unresolved_conflicts)

    p13_credit_refs = () if drop_p13_gate else tuple(item.link_id for item in p13_run.candidate_credit_links)
    if drop_p13_gate and recipe_candidates:
        recipe_candidates = tuple(
            AB7RecipeCandidateRecord(
                recipe_candidate_ref=item.recipe_candidate_ref,
                station_ref=item.station_ref,
                input_refs=item.input_refs,
                output_refs=item.output_refs,
                effect_refs=item.effect_refs,
                supporting_trace_refs=item.supporting_trace_refs,
                disconfirming_trace_refs=item.disconfirming_trace_refs,
                p13_schema_candidate_refs=(),
                confounder_refs=item.confounder_refs,
                missing_evidence=item.missing_evidence,
                maturity_status=item.maturity_status,
                maturity_score=item.maturity_score,
                hidden_recipe_used=item.hidden_recipe_used,
                protected_eval_used=item.protected_eval_used,
            )
            for item in recipe_candidates
        )

    p14_refs = () if drop_p14_affordance else ((f"p14:affordance:{p14_run.station_ref or 'none'}",))

    active_confounders = tuple(item.confounder_ref for item in p13_run.confounder_records if item.status in {"active", "unresolved"})
    if force_active_confounder and recipe_candidates and not active_confounders:
        active_confounders = ("confounder:active:1",)
        recipe_candidates = tuple(
            AB7RecipeCandidateRecord(
                recipe_candidate_ref=item.recipe_candidate_ref,
                station_ref=item.station_ref,
                input_refs=item.input_refs,
                output_refs=item.output_refs,
                effect_refs=item.effect_refs,
                supporting_trace_refs=item.supporting_trace_refs,
                disconfirming_trace_refs=item.disconfirming_trace_refs,
                p13_schema_candidate_refs=item.p13_schema_candidate_refs,
                confounder_refs=("confounder:active:1",),
                missing_evidence=item.missing_evidence,
                maturity_status=item.maturity_status,
                maturity_score=item.maturity_score,
                hidden_recipe_used=item.hidden_recipe_used,
                protected_eval_used=item.protected_eval_used,
            )
            for item in recipe_candidates
        )

    maturity_flags: list[str] = []
    assessment = p15_run.maturity_assessment
    if assessment.hidden_recipe_detected:
        maturity_flags.append("hidden_recipe_detected")
    if assessment.one_shot_maturity_detected:
        maturity_flags.append("one_shot_maturity_detected")
    if assessment.confounder_bypass_detected:
        maturity_flags.append("confounder_bypass_detected")
    if assessment.disconfirmation_ignored_detected:
        maturity_flags.append("disconfirmation_ignored_detected")
    if assessment.missing_evidence_erased_detected:
        maturity_flags.append("missing_evidence_erased_detected")

    input_payload = AB7RecipeAutomationInput(
        tick_ref=f"ab7:probe:{p15_case_id}",
        recipe_candidates=recipe_candidates,
        precursor_candidates=precursor_candidates,
        lived_trace_refs=tuple(f"trace:public:{idx+1}" for idx, _ in enumerate(p15_run.lived_trace_records)),
        p13_credit_refs=tuple(_sanitize_ref(ref, "p13_credit") for ref in p13_credit_refs),
        p14_station_affordance_refs=tuple(_sanitize_ref(ref, "p14_affordance") for ref in p14_refs),
        ab_event_digest_refs=("ab1:event:recipe_effect",),
        ab_hypothesis_seed_refs=("ab2:seed:recipe",),
        ab_frontier_refs=tuple(_sanitize_ref(ref, "ab3_frontier") for ref in ab_frontier_refs),
        ab_update_refs=((_sanitize_ref(ab5_probe.update.update_id, "ab5_update"),) if ab5_probe.update is not None else ()),
        ab_attribution_refs=((_sanitize_ref(ab6_probe.frame.attribution_frame_id, "ab6_attribution"),) if ab6_probe.frame is not None else ()),
        unresolved_frontier_refs=tuple(_sanitize_ref(ref, "ab3_conflict") for ref in unresolved_refs),
        missing_evidence_refs=tuple(_sanitize_ref(ref, "missing") for ref in maturity_flags),
        disconfirming_evidence_refs=tuple(_sanitize_ref(item.get("trace_ref", "disconfirm"), "disconfirm") for item in p15_run.disconfirming_records),
        active_confounder_refs=tuple(_sanitize_ref(ref, "confounder") for ref in active_confounders),
        public_effect_refs=tuple("effect:output_appeared" for _ in p15_run.lived_trace_records if _.public_effect_refs),
        public_input_refs=tuple("input:item_a" for _ in p15_run.lived_trace_records if _.public_input_refs),
        protected_eval_only_rule=protected_eval_only,
        ambiguous_frontier=ambiguous_frontier or scenario.ambiguous_output,
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        source="ab7_recipe_automation_probe",
    )
    return build_ab7_recipe_automation_integration(input_payload)


def _to_recipe_candidate(candidate) -> AB7RecipeCandidateRecord:
    return AB7RecipeCandidateRecord(
        recipe_candidate_ref=_sanitize_ref(candidate.recipe_candidate_id, "recipe_candidate"),
        station_ref="station:generic_station" if candidate.station_ref else None,
        input_refs=tuple("input:item_a" for _ in candidate.input_refs),
        output_refs=tuple("output:item_b" for _ in candidate.output_refs),
        effect_refs=tuple("effect:output_appeared" for _ in candidate.effect_refs),
        supporting_trace_refs=tuple(_sanitize_ref(ref, "trace") for ref in candidate.supporting_trace_refs),
        disconfirming_trace_refs=tuple(_sanitize_ref(ref, "trace") for ref in candidate.disconfirming_trace_refs),
        p13_schema_candidate_refs=tuple(_sanitize_ref(ref, "p13_schema") for ref in candidate.p13_schema_candidate_refs),
        confounder_refs=tuple(_sanitize_ref(ref, "confounder") for ref in candidate.confounder_refs),
        missing_evidence=tuple(_sanitize_ref(ref, "missing") for ref in candidate.missing_evidence),
        maturity_status=candidate.maturity_status,
        maturity_score=float(candidate.maturity_score),
        hidden_recipe_used=bool(candidate.hidden_recipe_used),
        protected_eval_used=bool(candidate.protected_eval_used),
    )


def _to_precursor_candidate(candidate) -> AB7PrecursorCandidateRecord:
    return AB7PrecursorCandidateRecord(
        precursor_candidate_ref=_sanitize_ref(candidate.precursor_candidate_id, "precursor_candidate"),
        precursor_refs=tuple("input:item_a" for _ in candidate.precursor_refs),
        effect_refs=tuple("effect:output_appeared" for _ in candidate.effect_refs),
        support_status=candidate.support_status,
        missing_evidence=tuple(_sanitize_ref(ref, "missing") for ref in candidate.missing_evidence),
    )


def _sanitize_ref(value: str, prefix: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")
    if not safe:
        safe = "none"
    return f"{prefix}:{safe[:48]}"
