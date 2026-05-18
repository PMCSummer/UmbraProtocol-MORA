from __future__ import annotations

from substrate.ab01_event_digest import AB1DigestStatus, AB1EventDigest, AB1EventDigestKind

from .models import (
    AB2ClosureStatus,
    AB2HypothesisKind,
    AB2HypothesisSeed,
    AB2HypothesisSeedInput,
    AB2HypothesisSeedResult,
    AB2HypothesisSeedSet,
    AB2ScopeMarker,
    AB2SeedStatus,
)
from .telemetry import build_ab2_telemetry

_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "test_label",
    "hidden",
    "eval",
    "private",
)

_WORLD_SPECIFIC_TOKENS: tuple[str, ...] = (
    "water",
    "flask",
    "ore",
    "filter",
    "station",
    "recipe",
    "minecraft",
)


def build_ab2_hypothesis_seeds(candidate_input: AB2HypothesisSeedInput) -> AB2HypothesisSeedResult:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    if unsafe_reasons:
        seed_set = None
        hypotheses: tuple[AB2HypothesisSeed, ...] = ()
    else:
        seed_set, hypotheses = _build_seed_set(candidate_input)

    telemetry = build_ab2_telemetry(
        candidate_input=candidate_input,
        hypotheses=hypotheses,
        unsafe_basis_count=len(unsafe_reasons),
    )
    scope_marker = AB2ScopeMarker(
        scope="ab02_hypothesis_seed_from_residue_anomaly",
        hypothesis_seed_only=True,
        no_fact_selection_authority=True,
        no_hypothesis_competition_authority=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_execution_authority=True,
        reason="ab2 emits bounded competing hypothesis seeds without selecting cause/fact",
    )
    if unsafe_reasons:
        reason_codes = tuple(unsafe_reasons)
    elif seed_set is None:
        reason_codes = ("no_hypothesis_seeds",)
    else:
        reason_codes = ("hypothesis_seeds_emitted",)
    return AB2HypothesisSeedResult(
        tick_ref=candidate_input.tick_ref,
        seed_set=seed_set,
        telemetry=telemetry,
        scope_marker=scope_marker,
        reason_codes=reason_codes,
        source_lineage=("ab02_hypothesis_seed.policy",),
    )


def _build_seed_set(
    candidate_input: AB2HypothesisSeedInput,
) -> tuple[AB2HypothesisSeedSet | None, tuple[AB2HypothesisSeed, ...]]:
    if not candidate_input.event_digests:
        return None, ()
    for digest in candidate_input.event_digests:
        if digest.cause_claimed or not digest.explicit_non_causal_closure:
            return None, ()

    all_hypotheses: list[AB2HypothesisSeed] = []
    for digest in candidate_input.event_digests:
        all_hypotheses.extend(_build_hypotheses_for_digest(candidate_input, digest))

    if not all_hypotheses:
        return None, ()

    ambiguous_kind = len(_usable_hypotheses(all_hypotheses)) <= 1 and len(candidate_input.event_digests) == 1
    blocked_due_ambiguity = False
    if ambiguous_kind and not _can_be_single_seed_kind(candidate_input.event_digests[0]):
        blocked = _build_blocked_seed(
            candidate_input=candidate_input,
            digest=candidate_input.event_digests[0],
            suffix="ambiguous_requires_competing_hypotheses",
            missing=("competing_hypotheses_required",),
        )
        all_hypotheses.append(blocked)
        blocked_due_ambiguity = True

    hypotheses = tuple(all_hypotheses)
    uncertainty_summary = _summarize_uncertainty(hypotheses)
    seed_set = AB2HypothesisSeedSet(
        seed_set_id=f"ab2:{candidate_input.tick_ref}:seed_set",
        source_event_refs=tuple(item.event_id for item in candidate_input.event_digests),
        source_residue_refs=tuple(dict.fromkeys((*candidate_input.residue_refs, *tuple(_residue_refs(candidate_input))))),
        source_effect_refs=tuple(dict.fromkeys((*candidate_input.effect_refs, *tuple(_effect_refs(candidate_input))))),
        source_observation_refs=tuple(
            dict.fromkeys((*candidate_input.observation_refs, *tuple(_observation_refs(candidate_input))))
        ),
        hypotheses=hypotheses,
        seed_policy="ab2_seed_from_public_event_residue_v1",
        uncertainty_summary=uncertainty_summary,
        hidden_eval_used=False,
        scenario_label_used=False,
        fact_claimed=False,
        selected_fact_hypothesis_id=None,
        closure_status=(
            AB2ClosureStatus.BLOCKED
            if (not _usable_hypotheses(hypotheses) or blocked_due_ambiguity)
            else AB2ClosureStatus.OPEN
        ),
        blocked_status=(not bool(_usable_hypotheses(hypotheses))) or blocked_due_ambiguity,
    )
    return seed_set, hypotheses


def _build_hypotheses_for_digest(
    candidate_input: AB2HypothesisSeedInput,
    digest: AB1EventDigest,
) -> tuple[AB2HypothesisSeed, ...]:
    base_refs = tuple(dict.fromkeys((*candidate_input.source_refs, *digest.source_refs)))
    specs = _seed_specs_for_event_kind(digest.event_kind)
    seeds: list[AB2HypothesisSeed] = []
    for index, spec in enumerate(specs, start=1):
        missing_evidence = _missing_evidence_for_spec(digest=digest, spec=spec)
        status = AB2SeedStatus.BLOCKED if missing_evidence else AB2SeedStatus.USABLE
        confidence = _confidence_for_kind(spec["kind"], digest=digest, blocked=(status is AB2SeedStatus.BLOCKED))
        expected_observations = tuple(spec["expected_observations"])
        possible_tests = tuple(spec["possible_tests"])
        if status is AB2SeedStatus.USABLE and (not expected_observations or not possible_tests):
            status = AB2SeedStatus.BLOCKED
            missing_evidence = tuple(dict.fromkeys((*missing_evidence, "expected_observations_and_possible_tests_required")))
        seeds.append(
            AB2HypothesisSeed(
                hypothesis_id=f"ab2:{digest.event_id}:{index}",
                hypothesis_kind=spec["kind"],
                explains_what=tuple(spec["explains_what"]),
                does_not_explain=tuple(spec["does_not_explain"]),
                expected_observations=expected_observations,
                possible_tests=possible_tests,
                missing_evidence=missing_evidence,
                scope="ab02_hypothesis_seed",
                confidence_initial=confidence,
                confidence_policy="provisional",
                source_refs=base_refs,
                event_refs=(digest.event_id,),
                residue_refs=tuple(digest.residue_refs),
                effect_refs=tuple(digest.effect_refs),
                forbidden_fact_closure=True,
                hidden_eval_used=False,
                scenario_label_used=False,
                cause_confirmed=False,
                rank=index,
                seed_status=status,
            )
        )
    return tuple(seeds)


def _seed_specs_for_event_kind(event_kind: AB1EventDigestKind) -> tuple[dict[str, object], ...]:
    if event_kind is AB1EventDigestKind.UNEXPECTED_BLOCK:
        return (
            {
                "kind": AB2HypothesisKind.CAPABILITY_OR_CONSTRAINT_BLOCK,
                "explains_what": ("blocked_or_failed_effect_observed",),
                "does_not_explain": ("final_physical_cause", "long_horizon_intent"),
                "expected_observations": ("repeated_block_under_same_public_constraints",),
                "possible_tests": ("recheck_public_affordance_and_constraints",),
                "requires": ("effect", "residue"),
            },
            {
                "kind": AB2HypothesisKind.MEASUREMENT_OR_PROJECTION_MISMATCH,
                "explains_what": ("expected_vs_observed_block_mismatch",),
                "does_not_explain": ("true_world_state_change_cause",),
                "expected_observations": ("projection_inconsistency_across_consecutive_observations",),
                "possible_tests": ("repeat_observation_projection_consistency_check",),
                "requires": ("effect",),
            },
            {
                "kind": AB2HypothesisKind.PRIOR_ACTION_DELAYED_EFFECT,
                "explains_what": ("delayed_or_shifted_effect_timing",),
                "does_not_explain": ("specific_external_actor",),
                "expected_observations": ("effect_status_changes_after_wait_tick",),
                "possible_tests": ("wait_and_compare_followup_effect",),
                "requires": ("effect",),
            },
        )
    if event_kind is AB1EventDigestKind.INVENTORY_DELTA_MISMATCH:
        return (
            {
                "kind": AB2HypothesisKind.INTENDED_EFFECT_OBSERVED,
                "explains_what": ("partial_or_expected_inventory_transition",),
                "does_not_explain": ("why_delta_differs_from_expectation",),
                "expected_observations": ("inventory_delta_matches_effect_log_on_repeat_check",),
                "possible_tests": ("reconcile_inventory_snapshot_with_effect_refs",),
                "requires": ("effect",),
            },
            {
                "kind": AB2HypothesisKind.INVENTORY_TRANSITION_UNACCOUNTED,
                "explains_what": ("inventory_delta_not_fully_accounted",),
                "does_not_explain": ("final_resource_cause",),
                "expected_observations": ("continued_inventory_delta_disagreement",),
                "possible_tests": ("repeat_inventory_observation_with_same_view",),
                "requires": ("effect", "observed"),
            },
            {
                "kind": AB2HypothesisKind.MEASUREMENT_OR_PROJECTION_MISMATCH,
                "explains_what": ("inventory_reporting_inconsistency",),
                "does_not_explain": ("true_item_semantics",),
                "expected_observations": ("inventory_projection_changes_without_correlated_effect",),
                "possible_tests": ("compare_independent_public_inventory_views",),
                "requires": ("observed",),
            },
        )
    if event_kind is AB1EventDigestKind.EFFECT_MISMATCH:
        return (
            {
                "kind": AB2HypothesisKind.EXPECTED_EFFECT_MISSING,
                "explains_what": ("expected_effect_not_observed",),
                "does_not_explain": ("specific_failure_agent",),
                "expected_observations": ("expected_ref_absent_in_next_public_effect_window",),
                "possible_tests": ("recheck_expected_ref_in_followup_tick",),
                "requires": ("expected", "observed", "effect"),
            },
            {
                "kind": AB2HypothesisKind.PRIOR_ACTION_DELAYED_EFFECT,
                "explains_what": ("effect_timing_shift_vs_expectation",),
                "does_not_explain": ("definitive_external_interference_cause",),
                "expected_observations": ("delayed_alignment_between_expected_and_observed_refs",),
                "possible_tests": ("wait_tick_then_compare_expected_observed_alignment",),
                "requires": ("effect",),
            },
            {
                "kind": AB2HypothesisKind.MEASUREMENT_OR_PROJECTION_MISMATCH,
                "explains_what": ("projection_or_reporting_diff_between_expected_and_observed",),
                "does_not_explain": ("physical_cause_confirmation",),
                "expected_observations": ("projection_ref_changes_without_effect_state_change",),
                "possible_tests": ("cross_check_projection_channels",),
                "requires": ("observed", "expected"),
            },
            {
                "kind": AB2HypothesisKind.UNKNOWN_EXTERNAL_CAUSE,
                "explains_what": ("residual_unexplained_mismatch",),
                "does_not_explain": ("cause_identity", "causal_mechanism"),
                "expected_observations": ("mismatch_persists_under_repeated_public_checks",),
                "possible_tests": ("collect_additional_public_observation_before_commit",),
                "requires": ("effect",),
            },
        )
    if event_kind is AB1EventDigestKind.DELAYED_EFFECT_DETECTED:
        return (
            {
                "kind": AB2HypothesisKind.PRIOR_ACTION_DELAYED_EFFECT,
                "explains_what": ("observed_delayed_effect_signal",),
                "does_not_explain": ("cause_identity",),
                "expected_observations": ("effect_alignment_after_time_offset",),
                "possible_tests": ("repeat_measurement_after_one_tick",),
                "requires": ("effect",),
            },
            {
                "kind": AB2HypothesisKind.MEASUREMENT_OR_PROJECTION_MISMATCH,
                "explains_what": ("delay_might_be_reporting_artifact",),
                "does_not_explain": ("definitive_delay_cause",),
                "expected_observations": ("delay_disappears_under_repeated_sampling",),
                "possible_tests": ("sample_same_signal_multiple_times",),
                "requires": ("observed",),
            },
        )
    return (
        {
            "kind": AB2HypothesisKind.INSUFFICIENT_PUBLIC_EVIDENCE,
            "explains_what": ("anomaly_signal_present_but_underconstrained",),
            "does_not_explain": ("cause_identity", "causal_mechanism"),
            "expected_observations": ("additional_public_refs_reduce_uncertainty",),
            "possible_tests": ("gather_additional_public_observation_refs",),
            "requires": ("observed",),
        },
        {
            "kind": AB2HypothesisKind.OBSERVATION_NOISE_OR_REPORTING_ERROR,
            "explains_what": ("possible_measurement_noise",),
            "does_not_explain": ("physical_world_change_confirmation",),
            "expected_observations": ("high_variance_across_repeated_measurement",),
            "possible_tests": ("repeat_measurement_without_intervention",),
            "requires": ("observed",),
        },
    )


def _missing_evidence_for_spec(digest: AB1EventDigest, spec: dict[str, object]) -> tuple[str, ...]:
    missing: list[str] = []
    requires = tuple(spec["requires"])
    if "effect" in requires and not digest.effect_refs:
        missing.append("effect_refs_required")
    if "residue" in requires and not digest.residue_refs:
        missing.append("residue_refs_required")
    if "expected" in requires and not digest.expected_refs:
        missing.append("expected_refs_required")
    if "observed" in requires and not digest.observed_refs:
        missing.append("observed_refs_required")
    if digest.digest_status is AB1DigestStatus.BLOCKED:
        missing.append("upstream_digest_blocked")
    return tuple(dict.fromkeys(missing))


def _confidence_for_kind(kind: AB2HypothesisKind, *, digest: AB1EventDigest, blocked: bool) -> float:
    if blocked:
        return 0.1
    base = max(0.15, min(0.75, float(digest.confidence) * 0.7))
    if kind is AB2HypothesisKind.UNKNOWN_EXTERNAL_CAUSE:
        base = min(base, 0.35)
    return round(base, 3)


def _build_blocked_seed(
    *,
    candidate_input: AB2HypothesisSeedInput,
    digest: AB1EventDigest,
    suffix: str,
    missing: tuple[str, ...],
) -> AB2HypothesisSeed:
    return AB2HypothesisSeed(
        hypothesis_id=f"ab2:{digest.event_id}:{suffix}",
        hypothesis_kind=AB2HypothesisKind.INSUFFICIENT_PUBLIC_EVIDENCE,
        explains_what=("insufficient_basis_for_competing_hypothesis_generation",),
        does_not_explain=("cause_identity",),
        expected_observations=(),
        possible_tests=(),
        missing_evidence=missing,
        scope="ab02_hypothesis_seed",
        confidence_initial=0.1,
        confidence_policy="provisional",
        source_refs=tuple(candidate_input.source_refs),
        event_refs=(digest.event_id,),
        residue_refs=tuple(digest.residue_refs),
        effect_refs=tuple(digest.effect_refs),
        forbidden_fact_closure=True,
        hidden_eval_used=False,
        scenario_label_used=False,
        cause_confirmed=False,
        rank=None,
        seed_status=AB2SeedStatus.BLOCKED,
    )


def _usable_hypotheses(hypotheses: list[AB2HypothesisSeed] | tuple[AB2HypothesisSeed, ...]) -> tuple[AB2HypothesisSeed, ...]:
    return tuple(item for item in hypotheses if item.seed_status is AB2SeedStatus.USABLE)


def _can_be_single_seed_kind(digest: AB1EventDigest) -> bool:
    return digest.event_kind in {
        AB1EventDigestKind.UNKNOWN_PUBLIC_ANOMALY,
        AB1EventDigestKind.ANOMALOUS_CHANGE,
    }


def _summarize_uncertainty(hypotheses: tuple[AB2HypothesisSeed, ...]) -> str:
    usable = _usable_hypotheses(hypotheses)
    if not usable:
        return "blocked:insufficient_public_evidence"
    low_conf = sum(1 for item in usable if item.confidence_initial <= 0.35)
    return f"open_competing:{len(usable)} hypotheses; low_confidence={low_conf}"


def _unsafe_basis_reasons(candidate_input: AB2HypothesisSeedInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if not candidate_input.source_refs:
        reasons.append("source_refs_required")

    values_to_check = (
        tuple(candidate_input.source_refs)
        + tuple(candidate_input.observation_refs)
        + tuple(candidate_input.residue_refs)
        + tuple(candidate_input.effect_refs)
    )
    lowered_values = " ".join(str(item).lower() for item in values_to_check)
    for marker in _FORBIDDEN_MARKERS:
        if marker in lowered_values:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_decision_basis")
            else:
                reasons.append("scenario_marker_in_decision_basis")
            break

    # Guard world-specific semantic leakage from entering AB2 substrate authority.
    for token in _WORLD_SPECIFIC_TOKENS:
        if token in lowered_values:
            reasons.append("world_specific_marker_forbidden_in_ab2_substrate")
            break

    for digest in candidate_input.event_digests:
        if digest.hidden_eval_used:
            reasons.append("upstream_digest_hidden_eval_forbidden")
        if digest.scenario_label_used:
            reasons.append("upstream_digest_scenario_label_forbidden")
        if digest.cause_claimed or not digest.explicit_non_causal_closure:
            reasons.append("upstream_digest_non_causal_closure_required")
    return list(dict.fromkeys(reasons))


def _residue_refs(candidate_input: AB2HypothesisSeedInput) -> tuple[str, ...]:
    refs: list[str] = []
    for digest in candidate_input.event_digests:
        refs.extend(digest.residue_refs)
    return tuple(dict.fromkeys(refs))


def _effect_refs(candidate_input: AB2HypothesisSeedInput) -> tuple[str, ...]:
    refs: list[str] = []
    for digest in candidate_input.event_digests:
        refs.extend(digest.effect_refs)
    return tuple(dict.fromkeys(refs))


def _observation_refs(candidate_input: AB2HypothesisSeedInput) -> tuple[str, ...]:
    refs: list[str] = []
    for digest in candidate_input.event_digests:
        refs.extend(digest.observation_refs)
    return tuple(dict.fromkeys(refs))
