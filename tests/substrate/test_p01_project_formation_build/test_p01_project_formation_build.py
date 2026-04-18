from __future__ import annotations

from substrate.p01_project_formation import (
    P01AdmissibilityVerdict,
    P01AuthoritySourceKind,
    P01ProjectStatus,
    derive_p01_project_formation_consumer_view,
)
from tests.substrate.p01_project_formation_testkit import (
    P01HarnessCase,
    build_p01_harness_case,
    harness_cases,
    p01_signal,
)


def test_harness_has_authority_and_conflict_coverage() -> None:
    cases = harness_cases()
    assert {
        "user_directive",
        "standing_obligation",
        "low_authority_suggestion",
        "disallowed_self_generated",
        "missing_precondition",
        "conflict_pair_equal_authority",
        "disabled",
    }.issubset(set(cases.keys()))


def test_authority_source_changes_project_admission() -> None:
    user_directive = build_p01_harness_case(harness_cases()["user_directive"])
    standing_obligation = build_p01_harness_case(harness_cases()["standing_obligation"])
    low_authority = build_p01_harness_case(harness_cases()["low_authority_suggestion"])
    disallowed = build_p01_harness_case(harness_cases()["disallowed_self_generated"])

    assert user_directive.state.active_projects[0].admissibility_verdict is P01AdmissibilityVerdict.ADMITTED
    assert standing_obligation.state.active_projects[0].admissibility_verdict is P01AdmissibilityVerdict.ADMITTED
    assert low_authority.state.candidate_projects[0].admissibility_verdict is P01AdmissibilityVerdict.CANDIDATE_ONLY
    assert disallowed.state.rejected_candidates[0].current_status is P01ProjectStatus.REJECTED


def test_prompt_local_goal_substitution_is_blocked() -> None:
    seed = build_p01_harness_case(harness_cases()["user_directive"])
    low_authority_follow_up = build_p01_harness_case(
        P01HarnessCase(
            case_id="prompt-local-substitution",
            tick_index=2,
            signals=(
                p01_signal(
                    signal_id="pls1",
                    authority=P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION,
                    target="switch to unrelated polishing task",
                    signal_kind="suggestion",
                ),
            ),
        ),
        prior_state=seed.state,
    )
    assert low_authority_follow_up.state.prompt_local_capture_risk is True
    assert any(
        entry.current_status is P01ProjectStatus.CANDIDATE_ONLY
        for entry in low_authority_follow_up.state.candidate_projects
    )
    assert low_authority_follow_up.gate.project_handoff_consumer_ready is False


def test_project_identity_dedup_preserves_same_project_under_rephrase() -> None:
    initial = build_p01_harness_case(
        P01HarnessCase(
            case_id="dedup-1",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="dedup-a",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="Prepare nightly reviewer run",
                ),
            ),
        )
    )
    rephrased = build_p01_harness_case(
        P01HarnessCase(
            case_id="dedup-2",
            tick_index=2,
            signals=(
                p01_signal(
                    signal_id="dedup-b",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="  prepare   NIGHTLY reviewer run  ",
                ),
            ),
        ),
        prior_state=initial.state,
    )
    assert len(rephrased.state.active_projects) == 1
    assert rephrased.state.active_projects[0].project_id == initial.state.active_projects[0].project_id
    assert rephrased.state.active_projects[0].project_identity_key == initial.state.active_projects[0].project_identity_key


def test_conflicting_projects_require_explicit_arbitration() -> None:
    result = build_p01_harness_case(harness_cases()["conflict_pair_equal_authority"])
    assert result.state.conflicting_authority is True
    assert result.state.arbitration_records
    assert result.state.arbitration_records[0].outcome.value in {
        "no_safe_resolution",
        "reject_weaker_source",
    }
    if result.state.arbitration_records[0].outcome.value == "no_safe_resolution":
        assert result.state.no_safe_project_formation is True


def test_conflict_fallback_without_conflict_group_id() -> None:
    result = build_p01_harness_case(
        P01HarnessCase(
            case_id="implicit-conflict-fallback",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="implicit-a",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    signal_kind="directive",
                ),
                p01_signal(
                    signal_id="implicit-b",
                    authority=P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION,
                    target="prepare nightly reviewer run",
                    signal_kind="suggestion",
                ),
            ),
        )
    )
    assert result.state.conflicting_authority is True
    assert len(result.state.arbitration_records) >= 1
    assert any(
        record.outcome.value in {"reject_weaker_source", "no_safe_resolution"}
        for record in result.state.arbitration_records
    )


def test_stale_project_does_not_persist_after_termination_conditions() -> None:
    seed = build_p01_harness_case(harness_cases()["user_directive"])
    prior_project_id = seed.state.active_projects[0].project_id
    terminated = build_p01_harness_case(
        P01HarnessCase(
            case_id="terminated-follow-up",
            tick_index=2,
            signals=(
                p01_signal(
                    signal_id="term-1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    continuation_of_prior_project_id=prior_project_id,
                    completion_evidence_present=True,
                ),
            ),
        ),
        prior_state=seed.state,
    )
    assert all(
        entry.project_id != prior_project_id for entry in terminated.state.active_projects
    )
    assert terminated.state.stale_active_project_detected is True
    assert any(
        entry.current_status is P01ProjectStatus.TERMINATED
        for entry in terminated.state.rejected_candidates
    )


def test_structurally_distinct_targets_do_not_false_merge() -> None:
    result = build_p01_harness_case(
        P01HarnessCase(
            case_id="structural-no-false-merge",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="merge-a",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    signal_kind="directive",
                ),
                p01_signal(
                    signal_id="merge-b",
                    authority=P01AuthoritySourceKind.STANDING_OBLIGATION,
                    target="prepare nightly reviewer run",
                    signal_kind="obligation",
                    persistent_obligation_marker=True,
                ),
            ),
        )
    )
    all_entries = (
        *result.state.active_projects,
        *result.state.candidate_projects,
        *result.state.suspended_projects,
        *result.state.rejected_candidates,
    )
    assert len(all_entries) >= 2
    assert len({entry.project_id for entry in all_entries}) >= 2
    assert len({entry.project_identity_key for entry in all_entries}) >= 2


def test_same_target_different_blocker_status_changes_project_status() -> None:
    active = build_p01_harness_case(harness_cases()["user_directive"])
    blocked = build_p01_harness_case(harness_cases()["missing_precondition"])
    assert active.state.active_projects[0].current_status is P01ProjectStatus.ACTIVE
    assert blocked.state.suspended_projects[0].current_status is P01ProjectStatus.BLOCKED_BY_MISSING_PRECONDITION
    assert blocked.state.blocked_pending_grounding is True


def test_o03_conservative_pressure_can_demote_non_high_authority_signal() -> None:
    low_pressure = build_p01_harness_case(
        P01HarnessCase(
            case_id="o03-low-pressure",
            tick_index=1,
            o03_case_id="cooperative_transparent",
            signals=(
                p01_signal(
                    signal_id="o03lp-1",
                    authority=P01AuthoritySourceKind.CLARIFICATION_REQUIRED_PRECONDITION,
                    target="prepare nightly reviewer run",
                ),
            ),
        )
    )
    high_pressure = build_p01_harness_case(
        P01HarnessCase(
            case_id="o03-high-pressure",
            tick_index=1,
            o03_case_id="underconstrained_strategy",
            signals=(
                p01_signal(
                    signal_id="o03hp-1",
                    authority=P01AuthoritySourceKind.CLARIFICATION_REQUIRED_PRECONDITION,
                    target="prepare nightly reviewer run",
                ),
            ),
        )
    )
    assert low_pressure.state.active_projects[0].current_status is P01ProjectStatus.ACTIVE
    assert high_pressure.state.candidate_projects[0].current_status is P01ProjectStatus.CANDIDATE_ONLY


def test_disabled_path_returns_honest_no_safe_fallback() -> None:
    disabled = build_p01_harness_case(harness_cases()["disabled"])
    assert disabled.state.no_safe_project_formation is True
    assert disabled.gate.project_handoff_consumer_ready is False
    assert "p01_disabled" in disabled.gate.restrictions


def test_state_is_not_just_goal_summary() -> None:
    result = build_p01_harness_case(harness_cases()["user_directive"])
    entry = result.state.active_projects[0]
    assert entry.project_id.startswith("p01-project:")
    assert entry.source_of_authority is P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE
    assert entry.current_status is P01ProjectStatus.ACTIVE
    assert entry.admissibility_verdict is P01AdmissibilityVerdict.ADMITTED
    assert result.state.justification_links
    assert result.gate.reason
    assert result.scope_marker.rt01_hosted_only is True


def test_real_consumer_view_exposes_authority_and_grounding_constraints() -> None:
    blocked = build_p01_harness_case(harness_cases()["missing_precondition"])
    view = derive_p01_project_formation_consumer_view(blocked)
    assert view.clarification_or_grounding_required is True
    assert view.project_handoff_consumer_ready is False
    assert view.has_candidate_projects is False
    assert view.has_active_projects is False
