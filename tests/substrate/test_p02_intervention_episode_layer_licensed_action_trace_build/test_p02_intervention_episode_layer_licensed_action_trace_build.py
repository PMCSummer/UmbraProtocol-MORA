from __future__ import annotations

from substrate.p02_intervention_episode_layer_licensed_action_trace import (
    P02EpisodeStatus,
    P02ExecutionStatus,
    P02InterventionEpisodeResult,
)
from tests.substrate.p02_intervention_episode_layer_licensed_action_trace_testkit import (
    build_p02_harness_case,
    harness_cases,
)


def test_episode_schema_is_typed_and_not_prose_wrapper() -> None:
    result = build_p02_harness_case(harness_cases()["schema_baseline"])
    assert isinstance(result, P02InterventionEpisodeResult)
    assert result.metadata.episode_count == 1
    episode = result.episodes[0]
    assert episode.boundary_report.included_event_refs
    assert episode.completion_and_verification.status in set(P02EpisodeStatus)
    assert isinstance(episode.residue, tuple)
    assert isinstance(episode.uncertainty_markers, tuple)


def test_same_events_different_license_changes_episode_status() -> None:
    licensed = build_p02_harness_case(harness_cases()["same_events_license_ok"])
    missing = build_p02_harness_case(harness_cases()["same_events_license_missing"])
    assert licensed.episodes[0].status is P02EpisodeStatus.COMPLETED_AS_LICENSED
    assert missing.episodes[0].status is P02EpisodeStatus.OVERRAN_SCOPE
    assert licensed.episodes[0].status != missing.episodes[0].status


def test_same_execution_different_outcome_evidence_changes_status() -> None:
    verified = build_p02_harness_case(harness_cases()["same_execution_outcome_variants_verified"])
    unverified = build_p02_harness_case(harness_cases()["same_execution_outcome_variants_unverified"])
    conflicted = build_p02_harness_case(harness_cases()["same_execution_outcome_variants_conflicted"])

    assert verified.episodes[0].status is P02EpisodeStatus.COMPLETED_AS_LICENSED
    assert unverified.episodes[0].status is P02EpisodeStatus.AWAITING_VERIFICATION
    assert conflicted.episodes[0].status is P02EpisodeStatus.VERIFICATION_CONFLICTED


def test_boundary_contrast_avoids_false_merge_and_false_split() -> None:
    continued = build_p02_harness_case(harness_cases()["boundary_continue"])
    split = build_p02_harness_case(harness_cases()["boundary_split"])

    assert len(continued.episodes[0].action_trace_refs) == 2
    assert len(continued.episodes[0].excluded_event_refs) == 0
    assert len(split.episodes[0].action_trace_refs) == 1
    assert len(split.episodes[0].excluded_event_refs) == 1
    assert split.episodes[0].boundary_report.reason_codes


def test_boundary_adversarial_hints_resolve_with_explicit_split_rationale() -> None:
    result = build_p02_harness_case(harness_cases()["boundary_adversarial_hint_conflict"])
    episode = result.episodes[0]
    report = episode.boundary_report
    assert episode.action_trace_refs == ("ev:1",)
    assert episode.excluded_event_refs == ("ev:2",)
    assert report.boundary_ambiguous is True
    assert "new_episode_hint" in report.reason_codes


def test_partial_blocked_and_overrun_do_not_collapse() -> None:
    partial = build_p02_harness_case(harness_cases()["partial_case"])
    blocked = build_p02_harness_case(harness_cases()["blocked_case"])
    overrun = build_p02_harness_case(harness_cases()["overrun_case"])

    assert partial.episodes[0].status is P02EpisodeStatus.PARTIAL
    assert partial.episodes[0].execution_status is P02ExecutionStatus.PARTIAL
    assert blocked.episodes[0].status is P02EpisodeStatus.BLOCKED
    assert blocked.episodes[0].execution_status is P02ExecutionStatus.BLOCKED
    assert overrun.episodes[0].status is P02EpisodeStatus.OVERRAN_SCOPE
    assert overrun.episodes[0].overrun_detected is True


def test_residue_persists_even_when_trace_looks_successful() -> None:
    result = build_p02_harness_case(harness_cases()["residue_case"])
    assert result.metadata.residue_count > 0
    kinds = {item.residue_kind.value for item in result.episodes[0].residue}
    assert "pending_verification" in kinds or "unresolved_side_effect" in kinds


def test_excluded_event_rationale_is_visible() -> None:
    split = build_p02_harness_case(harness_cases()["boundary_split"])
    report = split.episodes[0].boundary_report
    assert report.excluded_event_refs
    assert report.reason_codes
    assert report.reason.strip()


def test_anti_completion_inflation_without_verification() -> None:
    result = build_p02_harness_case(harness_cases()["anti_completion_inflation"])
    assert result.episodes[0].status is P02EpisodeStatus.AWAITING_VERIFICATION


def test_disabled_or_no_basis_returns_honest_candidate_only_fallback() -> None:
    disabled = build_p02_harness_case(harness_cases()["disabled"])
    no_basis = build_p02_harness_case(harness_cases()["no_basis"])
    assert disabled.metadata.episode_count == 0
    assert no_basis.metadata.episode_count == 0
    assert disabled.gate.episode_consumer_ready is False
    assert no_basis.gate.episode_consumer_ready is False
