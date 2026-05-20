from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from substrate.ab01_event_digest import AB1EventDigestInput, build_ab1_event_digests
from substrate.ab02_hypothesis_seed import AB2HypothesisSeedInput, build_ab2_hypothesis_seeds
from substrate.ab03_hypothesis_frontier import AB3FrontierInput, build_ab3_hypothesis_frontier
from substrate.ab04_epistemic_candidate_basis import AB4EpistemicBasisInput, build_ab4_epistemic_candidate_basis
from substrate.ab05_hypothesis_update import AB5HypothesisUpdateInput, build_ab5_hypothesis_update
from substrate.ab06_causal_attribution import AB6CausalAttributionInput, build_ab6_causal_attribution
from substrate.ab07_recipe_automation_integration import (
    AB7PrecursorCandidateRecord,
    AB7RecipeAutomationInput,
    AB7RecipeCandidateRecord,
    build_ab7_recipe_automation_integration,
)

from .models import (
    ABLiveCounters,
    ABLiveStageTrace,
    ABLiveTickConfig,
    ABLiveTickInput,
    ABLiveTickResult,
)


def run_ab_live_subject_tick_contour(
    candidate_input: ABLiveTickInput,
    config: ABLiveTickConfig,
) -> ABLiveTickResult:
    traces: list[ABLiveStageTrace] = []
    blocked_reasons: list[str] = []
    skipped_reasons: list[str] = []
    guard_count = 0

    if not config.enable_ab_live_contour:
        for stage_name in _stage_names():
            traces.append(
                ABLiveStageTrace(
                    stage_name=stage_name,
                    ran=False,
                    skipped_reason="ab_live_disabled",
                    input_refs=(),
                    output_refs=(),
                    authority_flags=_authority_flags(config),
                )
            )
        return ABLiveTickResult(
            tick_id=candidate_input.tick_id,
            ab1_event_digest_refs=(),
            ab2_seed_set_refs=(),
            ab3_frontier_refs=(),
            ab4_epistemic_basis_refs=(),
            ab5_update_refs=(),
            ab6_attribution_refs=(),
            ab7_constraint_refs=(),
            ab_live_counters=ABLiveCounters(),
            stage_traces=tuple(traces),
            blocked_reasons=(),
            skipped_reasons=("ab_live_disabled",),
            public_basis_refs=(),
        )

    if candidate_input.protected_eval_present:
        blocked_reasons.append("protected_eval_present")
    if candidate_input.scenario_label_present:
        blocked_reasons.append("scenario_label_present")
    if blocked_reasons:
        for stage_name in _stage_names():
            traces.append(
                ABLiveStageTrace(
                    stage_name=stage_name,
                    ran=False,
                    skipped_reason="blocked_unsafe_basis",
                    input_refs=(),
                    output_refs=(),
                    authority_flags=_authority_flags(config),
                    error_or_blocked_reason=blocked_reasons[0],
                )
            )
        counters = ABLiveCounters(
            blocked_protected_eval_count=1 if "protected_eval_present" in blocked_reasons else 0,
            blocked_scenario_label_count=1 if "scenario_label_present" in blocked_reasons else 0,
        )
        return ABLiveTickResult(
            tick_id=candidate_input.tick_id,
            ab1_event_digest_refs=(),
            ab2_seed_set_refs=(),
            ab3_frontier_refs=(),
            ab4_epistemic_basis_refs=(),
            ab5_update_refs=(),
            ab6_attribution_refs=(),
            ab7_constraint_refs=(),
            ab_live_counters=counters,
            stage_traces=tuple(traces),
            blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
            skipped_reasons=("blocked_unsafe_basis",),
            public_basis_refs=(),
            hidden_eval_used=False,
            scenario_label_used=False,
        )

    public_basis_refs = _public_basis_refs(candidate_input)
    if config.strict_public_basis_only and not public_basis_refs:
        skipped_reasons.append("no_public_basis")
        for stage_name in _stage_names():
            traces.append(
                ABLiveStageTrace(
                    stage_name=stage_name,
                    ran=False,
                    skipped_reason="no_public_basis",
                    input_refs=(),
                    output_refs=(),
                    authority_flags=_authority_flags(config),
                    error_or_blocked_reason="no_public_basis",
                )
            )
        counters = ABLiveCounters(skipped_no_public_basis_count=len(_stage_names()))
        return ABLiveTickResult(
            tick_id=candidate_input.tick_id,
            ab1_event_digest_refs=(),
            ab2_seed_set_refs=(),
            ab3_frontier_refs=(),
            ab4_epistemic_basis_refs=(),
            ab5_update_refs=(),
            ab6_attribution_refs=(),
            ab7_constraint_refs=(),
            ab_live_counters=counters,
            stage_traces=tuple(traces),
            blocked_reasons=(),
            skipped_reasons=tuple(skipped_reasons),
            public_basis_refs=(),
        )

    ab1_refs: tuple[str, ...] = ()
    ab2_refs: tuple[str, ...] = ()
    ab3_refs: tuple[str, ...] = tuple(candidate_input.prior_frontier_refs)
    ab4_refs: tuple[str, ...] = ()
    ab5_refs: tuple[str, ...] = ()
    ab6_refs: tuple[str, ...] = ()
    ab7_refs: tuple[str, ...] = ()

    ab1_result = None
    ab2_result = None
    ab3_result = None
    ab5_result = None
    ab6_result = None
    frontier_for_update = candidate_input.prior_frontier_object

    if config.run_ab1 and _has_ab1_basis(candidate_input):
        expected_refs = tuple(f"expected:{idx}" for idx, _ in enumerate(candidate_input.public_effect_refs, start=1))
        observed_refs = (
            tuple(candidate_input.public_effect_refs)
            if candidate_input.public_effect_refs
            else tuple(candidate_input.public_observation_refs)
        )
        ab1_input = AB1EventDigestInput(
            tick_ref=candidate_input.tick_id,
            source_refs=public_basis_refs,
            observation_refs=tuple(candidate_input.public_observation_refs or candidate_input.public_effect_refs),
            raw_window_refs=tuple(candidate_input.public_observation_refs),
            raw_window_missing_reason=(
                None if candidate_input.public_observation_refs else "public_observation_window_unavailable"
            ),
            effect_refs=tuple(candidate_input.public_effect_refs),
            residue_refs=tuple(candidate_input.residue_refs),
            expected_refs=expected_refs,
            observed_refs=observed_refs,
            anomaly_markers=tuple(candidate_input.uncertainty_refs),
            effect_status="blocked" if candidate_input.conflict_refs else "observed_success",
            delayed_effect_ticks=1 if _contains_token(candidate_input.uncertainty_refs, "delayed") else None,
            magnitude=0.55 if (candidate_input.public_effect_refs or candidate_input.residue_refs) else 0.2,
            noise_level=0.2,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="ab_int_subject_tick",
        )
        ab1_result = build_ab1_event_digests(ab1_input)
        ab1_refs = _cap(tuple(item.event_id for item in ab1_result.digests), config.max_event_digests)
        if len(ab1_result.digests) > config.max_event_digests:
            guard_count += 1
        traces.append(
            ABLiveStageTrace(
                stage_name="ab1_event_digest",
                ran=True,
                skipped_reason=None,
                input_refs=public_basis_refs,
                output_refs=ab1_refs,
                authority_flags=_authority_flags(config),
            )
        )
    else:
        traces.append(_skipped("ab1_event_digest", "insufficient_ab1_basis", public_basis_refs, config))

    if config.run_ab2 and ab1_result is not None and ab1_result.digests:
        ab2_input = AB2HypothesisSeedInput(
            tick_ref=candidate_input.tick_id,
            event_digests=ab1_result.digests,
            source_refs=public_basis_refs,
            observation_refs=tuple(candidate_input.public_observation_refs),
            residue_refs=tuple(candidate_input.residue_refs),
            effect_refs=tuple(candidate_input.public_effect_refs),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="ab_int_subject_tick",
        )
        ab2_result = build_ab2_hypothesis_seeds(ab2_input)
        if ab2_result.seed_set is not None:
            ab2_refs = (ab2_result.seed_set.seed_set_id,)
        seed_count = len(ab2_result.seed_set.hypotheses) if ab2_result.seed_set is not None else 0
        if seed_count > config.max_hypothesis_seeds:
            guard_count += 1
        traces.append(
            ABLiveStageTrace(
                stage_name="ab2_hypothesis_seed",
                ran=True,
                skipped_reason=None,
                input_refs=ab1_refs,
                output_refs=ab2_refs,
                authority_flags=_authority_flags(config),
            )
        )
    else:
        traces.append(_skipped("ab2_hypothesis_seed", "ab1_digest_required", ab1_refs, config))

    if config.run_ab3 and ab2_result is not None and ab2_result.seed_set is not None:
        ab3_input = AB3FrontierInput(
            tick_ref=candidate_input.tick_id,
            seed_set=ab2_result.seed_set,
            source_refs=public_basis_refs,
            observation_refs=tuple(candidate_input.public_observation_refs),
            residue_refs=tuple(candidate_input.residue_refs),
            effect_refs=tuple(candidate_input.public_effect_refs),
            disconfirming_evidence_refs=tuple(candidate_input.conflict_refs),
            ambiguous_evidence=bool(candidate_input.uncertainty_refs or candidate_input.conflict_refs),
            require_competing_hypotheses=True,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="ab_int_subject_tick",
        )
        ab3_result = build_ab3_hypothesis_frontier(ab3_input)
        if ab3_result.frontier is not None:
            frontier_for_update = ab3_result.frontier
            ab3_refs = (ab3_result.frontier.frontier_id,)
            if len(ab3_result.frontier.hypotheses) > config.max_frontier_hypotheses:
                guard_count += 1
        traces.append(
            ABLiveStageTrace(
                stage_name="ab3_hypothesis_frontier",
                ran=True,
                skipped_reason=None,
                input_refs=ab2_refs,
                output_refs=ab3_refs,
                authority_flags=_authority_flags(config),
            )
        )
    else:
        traces.append(_skipped("ab3_hypothesis_frontier", "ab2_seed_set_required", ab2_refs, config))

    if config.run_ab5 and frontier_for_update is not None and candidate_input.public_effect_refs:
        support_ref = (
            (frontier_for_update.hypotheses[0].hypothesis_id,)
            if (frontier_for_update.hypotheses and _effect_correlated(candidate_input))
            else ()
        )
        ab5_input = AB5HypothesisUpdateInput(
            tick_ref=candidate_input.tick_id,
            prior_frontier=frontier_for_update,
            source_refs=public_basis_refs,
            source_effect_refs=tuple(candidate_input.public_effect_refs),
            source_event_digests=ab1_result.digests if ab1_result is not None else (),
            source_request_refs=tuple(candidate_input.ap01_request_refs),
            epistemic_basis_refs=(),
            source_observation_refs=tuple(candidate_input.public_observation_refs),
            supporting_hypothesis_refs=support_ref,
            disconfirming_hypothesis_refs=(),
            ambiguous_evidence=bool(candidate_input.uncertainty_refs or candidate_input.conflict_refs),
            effect_correlated=_effect_correlated(candidate_input),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="ab_int_subject_tick",
        )
        ab5_result = build_ab5_hypothesis_update(ab5_input)
        if ab5_result.update is not None:
            ab5_refs = (ab5_result.update.update_id,)
            if ab5_result.update.updated_frontier_snapshot is not None:
                frontier_for_update = ab5_result.update.updated_frontier_snapshot
                ab3_refs = (frontier_for_update.frontier_id,)
        traces.append(
            ABLiveStageTrace(
                stage_name="ab5_hypothesis_update",
                ran=True,
                skipped_reason=None,
                input_refs=ab3_refs,
                output_refs=ab5_refs,
                authority_flags=_authority_flags(config),
            )
        )
    else:
        traces.append(_skipped("ab5_hypothesis_update", "prior_frontier_and_effect_required", ab3_refs, config))

    if config.run_ab6 and ab3_refs and candidate_input.public_effect_refs:
        ab6_input = AB6CausalAttributionInput(
            tick_ref=candidate_input.tick_id,
            source_frontier_refs=ab3_refs,
            source_update_refs=ab5_refs,
            source_event_digest_refs=ab1_refs,
            source_effect_refs=tuple(candidate_input.public_effect_refs),
            source_request_refs=tuple(candidate_input.ap01_request_refs),
            source_candidate_refs=tuple(candidate_input.prior_ab_state_refs),
            source_observation_refs=tuple(candidate_input.public_observation_refs),
            timing_refs=tuple(ref for ref in candidate_input.uncertainty_refs if "time" in ref or "delay" in ref),
            external_event_refs=tuple(ref for ref in candidate_input.conflict_refs if "external" in ref),
            other_actor_refs=tuple(ref for ref in candidate_input.conflict_refs if "other_actor" in ref),
            uncertainty_refs=tuple(candidate_input.uncertainty_refs),
            missing_evidence_refs=tuple(candidate_input.residue_refs),
            effect_correlated=_effect_correlated(candidate_input),
            blocked_action=_contains_token(candidate_input.conflict_refs, "blocked"),
            delayed_marker=_contains_token(candidate_input.uncertainty_refs, "delayed"),
            mixed_marker=_contains_token(candidate_input.conflict_refs, "mixed"),
            unknown_marker=not bool(candidate_input.ap01_request_refs),
            sensor_mismatch_marker=_contains_token(candidate_input.conflict_refs, "sensor"),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="ab_int_subject_tick",
        )
        ab6_result = build_ab6_causal_attribution(ab6_input)
        if ab6_result.frame is not None:
            ab6_refs = (ab6_result.frame.attribution_frame_id,)
        traces.append(
            ABLiveStageTrace(
                stage_name="ab6_causal_attribution",
                ran=True,
                skipped_reason=None,
                input_refs=tuple(dict.fromkeys((*ab3_refs, *ab5_refs, *ab1_refs))),
                output_refs=ab6_refs,
                authority_flags=_authority_flags(config),
            )
        )
    else:
        traces.append(_skipped("ab6_causal_attribution", "frontier_and_effect_required", ab3_refs, config))

    if config.run_ab7 and (candidate_input.recipe_candidate_refs or candidate_input.recipe_candidate_records):
        recipe_candidates = (
            tuple(candidate_input.recipe_candidate_records)
            if candidate_input.recipe_candidate_records
            else tuple(
                AB7RecipeCandidateRecord(
                    recipe_candidate_ref=ref,
                    station_ref="station:generic_station",
                    input_refs=("input:item_a",),
                    output_refs=("output:item_b",),
                    effect_refs=tuple(candidate_input.public_effect_refs) or ("effect:output_appeared",),
                    supporting_trace_refs=tuple(candidate_input.value_chain_refs) or ("trace:public:1",),
                    disconfirming_trace_refs=(),
                    p13_schema_candidate_refs=tuple(candidate_input.p13_credit_refs) or ("p13:schema:1",),
                    confounder_refs=(),
                    missing_evidence=(),
                    maturity_status="provisional_candidate",
                    maturity_score=0.45,
                    hidden_recipe_used=False,
                    protected_eval_used=False,
                )
                for ref in candidate_input.recipe_candidate_refs
            )
        )
        precursor_candidates = (
            tuple(candidate_input.precursor_candidate_records)
            if candidate_input.precursor_candidate_records
            else tuple(
                AB7PrecursorCandidateRecord(
                    precursor_candidate_ref=ref,
                    precursor_refs=("input:item_a",),
                    effect_refs=tuple(candidate_input.public_effect_refs) or ("effect:output_appeared",),
                    support_status="provisional",
                    missing_evidence=(),
                )
                for ref in candidate_input.precursor_candidate_refs
            )
        )
        seed_hypothesis_refs = ()
        if ab2_result is not None and ab2_result.seed_set is not None:
            seed_hypothesis_refs = tuple(item.hypothesis_id for item in ab2_result.seed_set.hypotheses)
        ab7_input = AB7RecipeAutomationInput(
            tick_ref=candidate_input.tick_id,
            recipe_candidates=recipe_candidates,
            precursor_candidates=precursor_candidates,
            lived_trace_refs=tuple(candidate_input.value_chain_refs) or ("trace:public:1",),
            p13_credit_refs=tuple(candidate_input.p13_credit_refs) or ("p13:credit:1",),
            p14_station_affordance_refs=tuple(candidate_input.p14_station_affordance_refs),
            ab_event_digest_refs=ab1_refs,
            ab_hypothesis_seed_refs=seed_hypothesis_refs,
            ab_frontier_refs=ab3_refs,
            ab_update_refs=ab5_refs,
            ab_attribution_refs=ab6_refs,
            unresolved_frontier_refs=tuple(frontier_for_update.unresolved_conflicts) if frontier_for_update is not None else (),
            missing_evidence_refs=tuple(candidate_input.residue_refs),
            disconfirming_evidence_refs=tuple(candidate_input.conflict_refs),
            active_confounder_refs=tuple(ref for ref in candidate_input.conflict_refs if "confounder" in ref),
            public_effect_refs=tuple(candidate_input.public_effect_refs),
            public_input_refs=("input:item_a",),
            protected_eval_only_rule=False,
            ambiguous_frontier=bool(candidate_input.uncertainty_refs or candidate_input.conflict_refs),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="ab_int_subject_tick",
        )
        ab7_result = build_ab7_recipe_automation_integration(ab7_input)
        if ab7_result.frame is not None:
            ab7_refs = tuple(item.constraint_id for item in ab7_result.frame.abductive_constraints)
            if len(ab7_refs) > config.max_frontier_hypotheses:
                ab7_refs = ab7_refs[: config.max_frontier_hypotheses]
                guard_count += 1
        traces.append(
            ABLiveStageTrace(
                stage_name="ab7_recipe_constraints",
                ran=True,
                skipped_reason=None,
                input_refs=tuple(candidate_input.recipe_candidate_refs),
                output_refs=ab7_refs,
                authority_flags=_authority_flags(config),
            )
        )
    else:
        traces.append(_skipped("ab7_recipe_constraints", "recipe_candidate_refs_required", candidate_input.recipe_candidate_refs, config))

    if config.run_ab4 and frontier_for_update is not None:
        if frontier_for_update.discriminating_tests and (
            frontier_for_update.unresolved_conflicts or frontier_for_update.missing_evidence
        ):
            ab4_input = AB4EpistemicBasisInput(
                tick_ref=candidate_input.tick_id,
                frontier=frontier_for_update,
                source_refs=public_basis_refs,
                observation_refs=tuple(candidate_input.public_observation_refs),
                residue_refs=tuple(candidate_input.residue_refs),
                effect_refs=tuple(candidate_input.public_effect_refs),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                allow_numeric_eig=False,
                source="ab_int_subject_tick",
            )
            ab4_result = build_ab4_epistemic_candidate_basis(ab4_input)
            ab4_refs = _cap(tuple(item.basis_id for item in ab4_result.bases), config.max_epistemic_basis_items)
            if len(ab4_result.bases) > config.max_epistemic_basis_items:
                guard_count += 1
            traces.append(
                ABLiveStageTrace(
                    stage_name="ab4_epistemic_basis",
                    ran=True,
                    skipped_reason=None,
                    input_refs=ab3_refs,
                    output_refs=ab4_refs,
                    authority_flags=_authority_flags(config),
                )
            )
        else:
            traces.append(_skipped("ab4_epistemic_basis", "frontier_discriminating_tests_required", ab3_refs, config))
    else:
        traces.append(_skipped("ab4_epistemic_basis", "frontier_required", ab3_refs, config))

    counters = ABLiveCounters(
        ab1_digest_count=len(ab1_refs),
        ab2_seed_count=(len(ab2_result.seed_set.hypotheses) if (ab2_result is not None and ab2_result.seed_set is not None) else 0),
        ab3_frontier_count=(len(frontier_for_update.hypotheses) if frontier_for_update is not None else 0),
        ab4_basis_count=len(ab4_refs),
        ab5_update_count=len(ab5_refs),
        ab6_attribution_count=len(ab6_refs),
        ab7_constraint_count=len(ab7_refs),
        skipped_no_public_basis_count=sum(1 for item in traces if item.skipped_reason == "no_public_basis"),
        blocked_protected_eval_count=0,
        blocked_scenario_label_count=0,
        action_authority_violation_count=0,
        fact_closure_violation_count=0,
        performance_guard_triggered_count=guard_count,
    )

    return ABLiveTickResult(
        tick_id=candidate_input.tick_id,
        ab1_event_digest_refs=ab1_refs,
        ab2_seed_set_refs=ab2_refs,
        ab3_frontier_refs=ab3_refs,
        ab4_epistemic_basis_refs=ab4_refs,
        ab5_update_refs=ab5_refs,
        ab6_attribution_refs=ab6_refs,
        ab7_constraint_refs=ab7_refs,
        ab_live_counters=counters,
        stage_traces=tuple(traces),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        skipped_reasons=tuple(dict.fromkeys(skipped_reasons)),
        public_basis_refs=public_basis_refs,
        hidden_eval_used=False,
        scenario_label_used=False,
        fact_claimed=False,
        cause_confirmed=False,
        action_request_emitted=False,
        world_submission_emitted=False,
        automation_claimed=False,
        mature_recipe_claimed=False,
        subject_tick_state_mutation_scope="ab_live_fields_only",
    )


def _stage_names() -> tuple[str, ...]:
    return (
        "ab1_event_digest",
        "ab2_hypothesis_seed",
        "ab3_hypothesis_frontier",
        "ab5_hypothesis_update",
        "ab6_causal_attribution",
        "ab7_recipe_constraints",
        "ab4_epistemic_basis",
    )


def _authority_flags(config: ABLiveTickConfig) -> tuple[str, ...]:
    out = ["no_action_authority" if config.no_action_authority else "action_authority_enabled"]
    out.append("no_publication_authority" if config.no_publication_authority else "publication_authority_enabled")
    out.append("no_execution_authority" if config.no_execution_authority else "execution_authority_enabled")
    return tuple(out)


def _public_basis_refs(candidate_input: ABLiveTickInput) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *candidate_input.public_observation_refs,
                *candidate_input.public_effect_refs,
                *candidate_input.residue_refs,
                *candidate_input.uncertainty_refs,
                *candidate_input.conflict_refs,
                *candidate_input.ap01_request_refs,
                *candidate_input.action_effect_refs,
                *candidate_input.prior_frontier_refs,
                *candidate_input.prior_ab_state_refs,
                *candidate_input.value_chain_refs,
                *candidate_input.factory_chain_refs,
            )
        )
    )


def _has_ab1_basis(candidate_input: ABLiveTickInput) -> bool:
    return bool(
        candidate_input.public_observation_refs
        or candidate_input.public_effect_refs
        or candidate_input.residue_refs
    )


def _effect_correlated(candidate_input: ABLiveTickInput) -> bool:
    return bool(candidate_input.public_effect_refs and (candidate_input.action_effect_refs or candidate_input.ap01_request_refs))


def _contains_token(values: tuple[str, ...], token: str) -> bool:
    lowered = token.lower()
    return any(lowered in str(item).lower() for item in values)


_T = TypeVar("_T")


def _cap(values: tuple[_T, ...], limit: int) -> tuple[_T, ...]:
    if limit <= 0:
        return ()
    return values[:limit]


def _skipped(
    stage_name: str,
    reason: str,
    input_refs: tuple[str, ...],
    config: ABLiveTickConfig,
) -> ABLiveStageTrace:
    return ABLiveStageTrace(
        stage_name=stage_name,
        ran=False,
        skipped_reason=reason,
        input_refs=tuple(input_refs),
        output_refs=(),
        authority_flags=_authority_flags(config),
    )
