from __future__ import annotations

from substrate.p03_long_horizon_credit_assignment_intervention_learning import (
    P03AttributionClass,
    P03ContributionMode,
    P03UpdateRecommendationKind,
    P03WindowEvidenceStatus,
)
from tests.substrate.p03_long_horizon_credit_assignment_intervention_learning_testkit import (
    assert_credit_class,
    assert_recommendation,
    build_p03_harness_case,
    first_credit,
    first_no_update,
    harness_cases,
)


def _run(case_key: str):
    return build_p03_harness_case(harness_cases()[case_key])


def test_p03_output_is_explicit_typed_record_set() -> None:
    run = _run("modest_immediate_later_durable_success")
    result = run.p03_result
    assert result.record_set.assignment_id
    assert result.record_set.credit_records
    assert isinstance(result.record_set.evaluated_episode_refs, tuple)
    assert result.scope_marker.rt01_hosted_only is True
    assert result.scope_marker.no_policy_mutation_authority is True
    assert result.scope_marker.no_raw_approval_shortcut is True


def test_same_immediate_feedback_with_different_long_horizon_outcome_changes_credit() -> None:
    degraded = _run("immediate_positive_later_degraded")
    durable = _run("modest_immediate_later_durable_success")

    assert_credit_class(degraded, expected=P03AttributionClass.NEGATIVE)
    assert_recommendation(degraded, expected=P03UpdateRecommendationKind.WEAKEN_GUARDED)
    assert_credit_class(durable, expected=P03AttributionClass.POSITIVE)
    assert_recommendation(durable, expected=P03UpdateRecommendationKind.STRENGTHEN_GUARDED)
    assert first_credit(degraded).attribution_class is not first_credit(durable).attribution_class


def test_same_later_outcome_with_different_confounder_structure_changes_credit_class() -> None:
    weak = _run("same_outcome_weak_confounders")
    strong = _run("same_outcome_strong_parallel_confounder")

    assert_credit_class(weak, expected=P03AttributionClass.POSITIVE)
    assert_recommendation(weak, expected=P03UpdateRecommendationKind.STRENGTHEN_GUARDED)
    assert_credit_class(strong, expected=P03AttributionClass.CONFOUNDED_ASSOCIATION)
    assert_recommendation(strong, expected=P03UpdateRecommendationKind.DO_NOT_UPDATE)
    assert strong.p03_result.record_set.no_update_records
    assert first_no_update(strong).attribution_class is P03AttributionClass.CONFOUNDED_ASSOCIATION


def test_recency_bias_adversarial_case_preserves_early_enabling_credit() -> None:
    run = _run("recency_bias_adversarial")
    credits = {item.episode_ref: item for item in run.p03_result.record_set.credit_records}

    assert credits["ep:early-enabling"].attribution_class is P03AttributionClass.POSITIVE
    assert credits["ep:late-salient"].attribution_class is P03AttributionClass.UNRESOLVED
    assert run.p03_result.record_set.no_update_records
    assert first_no_update(run).episode_ref == "ep:late-salient"


def test_side_effect_retention_yields_mixed_side_effect_dominant_not_pure_positive() -> None:
    run = _run("side_effect_retention")
    credit = first_credit(run)

    assert credit.attribution_class is P03AttributionClass.MIXED
    assert credit.contribution_mode is P03ContributionMode.ADVERSE_SIDE_EFFECT
    assert credit.side_effect_dominant is True
    assert_recommendation(run, expected=P03UpdateRecommendationKind.WEAKEN_GUARDED)


def test_outcome_verification_ablation_downgrades_to_no_update() -> None:
    verified = _run("verification_present")
    removed = _run("verification_removed")

    assert_credit_class(verified, expected=P03AttributionClass.POSITIVE)
    assert_recommendation(verified, expected=P03UpdateRecommendationKind.STRENGTHEN_GUARDED)
    assert first_credit(removed).attribution_class is P03AttributionClass.UNRESOLVED
    assert first_credit(removed).window_status is P03WindowEvidenceStatus.OUTCOME_UNVERIFIED
    assert first_no_update(removed).reason_code == "window_or_verification_open"
    assert_recommendation(removed, expected=P03UpdateRecommendationKind.DO_NOT_UPDATE)


def test_horizon_contrast_within_window_vs_out_of_window_is_deterministic() -> None:
    within = _run("horizon_within_window")
    out = _run("horizon_out_of_window")

    assert first_credit(within).window_status is P03WindowEvidenceStatus.WITHIN_WINDOW
    assert_credit_class(within, expected=P03AttributionClass.POSITIVE)
    assert_recommendation(within, expected=P03UpdateRecommendationKind.STRENGTHEN_GUARDED)

    assert first_credit(out).window_status is P03WindowEvidenceStatus.OUT_OF_WINDOW
    assert_credit_class(out, expected=P03AttributionClass.NULL)
    assert_recommendation(out, expected=P03UpdateRecommendationKind.KEEP_UNCHANGED)


def test_no_update_honesty_for_open_window_is_first_class() -> None:
    run = _run("no_update_open_window")

    assert run.p03_result.telemetry.no_update_count == 1
    assert run.p03_result.record_set.no_update_records
    assert first_credit(run).attribution_class is P03AttributionClass.UNRESOLVED
    assert first_credit(run).window_status is P03WindowEvidenceStatus.WINDOW_STILL_OPEN
    assert first_no_update(run).reason_code == "window_or_verification_open"
    assert_recommendation(run, expected=P03UpdateRecommendationKind.DO_NOT_UPDATE)


def test_social_approval_only_is_not_treated_as_success_proxy() -> None:
    run = _run("social_approval_only")

    assert first_credit(run).attribution_class is P03AttributionClass.UNRESOLVED
    assert first_no_update(run).reason_code == "approval_signal_not_credit_basis"
    assert_recommendation(run, expected=P03UpdateRecommendationKind.DO_NOT_UPDATE)
