from __future__ import annotations

from substrate.r05_appraisal_sovereign_protective_regulation import (
    R05AuthorityLevel,
    R05InhibitedSurface,
    R05ProtectiveMode,
    derive_r05_protective_consumer_view,
)
from tests.substrate.r05_appraisal_sovereign_protective_regulation_testkit import (
    R05HarnessCase,
    build_r05_harness_case,
    harness_cases,
    r05_trigger,
)


def test_harness_has_required_contrast_coverage() -> None:
    cases = harness_cases()
    assert len(cases) >= 12
    assert {
        "no_signal",
        "rude_low_basis_tone_only",
        "polite_structural_threat",
        "same_words_low_structure",
        "same_words_high_structure",
        "surface_exposure_wide",
        "surface_exposure_narrow",
        "weak_basis_candidate",
        "insufficient_basis_for_override",
        "disabled",
    }.issubset(set(cases.keys()))


def test_same_wording_different_threat_structure_changes_regulation_mode() -> None:
    low = build_r05_harness_case(harness_cases()["same_words_low_structure"])
    high = build_r05_harness_case(harness_cases()["same_words_high_structure"])
    assert low.state.protective_mode in {
        R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE,
        R05ProtectiveMode.PROTECTIVE_CANDIDATE_ONLY,
    }
    assert high.state.protective_mode is R05ProtectiveMode.DEGRADED_OPERATION_ONLY
    assert high.state.authority_level is R05AuthorityLevel.BOUNDED_MONITORING
    assert high.state.structural_basis_score > low.state.structural_basis_score


def test_polite_structural_threat_beats_rude_low_basis_case() -> None:
    polite_structural = build_r05_harness_case(harness_cases()["polite_structural_threat"])
    rude_low_basis = build_r05_harness_case(harness_cases()["rude_low_basis_tone_only"])
    assert polite_structural.state.protective_mode is R05ProtectiveMode.DEGRADED_OPERATION_ONLY
    assert rude_low_basis.state.protective_mode is R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE
    assert polite_structural.state.project_override_active is False
    assert rude_low_basis.state.project_override_active is False


def test_surface_specific_inhibition_changes_with_available_surfaces() -> None:
    wide = build_r05_harness_case(harness_cases()["surface_exposure_wide"])
    narrow = build_r05_harness_case(harness_cases()["surface_exposure_narrow"])
    assert set(wide.state.inhibited_surfaces) == {
        R05InhibitedSurface.COMMUNICATION_EXPOSURE,
        R05InhibitedSurface.INTERACTION_INTENSITY,
    }
    assert set(narrow.state.inhibited_surfaces) == {R05InhibitedSurface.INTERACTION_INTENSITY}


def test_weak_and_insufficient_basis_do_not_jump_to_hard_override() -> None:
    weak = build_r05_harness_case(harness_cases()["weak_basis_candidate"])
    insufficient = build_r05_harness_case(harness_cases()["insufficient_basis_for_override"])
    assert weak.state.protective_mode is R05ProtectiveMode.PROTECTIVE_CANDIDATE_ONLY
    assert weak.state.authority_level is R05AuthorityLevel.BOUNDED_MONITORING
    assert weak.state.project_override_active is False
    assert insufficient.state.protective_mode is R05ProtectiveMode.INSUFFICIENT_BASIS_FOR_OVERRIDE
    assert insufficient.state.authority_level is R05AuthorityLevel.NONE
    assert insufficient.state.insufficient_basis_for_override is True


def test_release_and_hysteresis_are_real_and_non_sticky() -> None:
    first = build_r05_harness_case(harness_cases()["release_candidate_high"])
    second = build_r05_harness_case(
        R05HarnessCase(
            case_id="release-step-2",
            tick_index=2,
            prior_state=first.state,
            protective_triggers=(
                r05_trigger(
                    trigger_id="release-step-2",
                    threat_structure_score=0.5,
                    p01_project_continuation_active=False,
                    release_signal_present=True,
                    counterevidence_present=True,
                    project_continuation_requested=True,
                ),
            ),
        )
    )
    third = build_r05_harness_case(
        R05HarnessCase(
            case_id="release-step-3",
            tick_index=3,
            prior_state=second.state,
            protective_triggers=(
                r05_trigger(
                    trigger_id="release-step-3",
                    threat_structure_score=0.22,
                    p01_project_continuation_active=False,
                    project_continuation_requested=True,
                ),
            ),
        )
    )
    assert first.state.protective_mode is R05ProtectiveMode.DEGRADED_OPERATION_ONLY
    assert second.state.protective_mode is R05ProtectiveMode.RECOVERY_IN_PROGRESS
    assert second.state.release_pending is False
    assert second.state.hysteresis_hold_ticks == 0
    assert third.state.protective_mode in {
        R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE,
        R05ProtectiveMode.PROTECTIVE_CANDIDATE_ONLY,
    }
    assert third.state.protective_mode is not R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE


def test_state_and_provenance_are_inspectable_and_not_blanket_controller() -> None:
    result = build_r05_harness_case(harness_cases()["polite_structural_threat"])
    view = derive_r05_protective_consumer_view(result)
    assert result.state.regulation_id.startswith("r05-regulation:")
    assert result.state.trigger_ids
    assert result.state.provenance
    assert result.state.source_lineage
    assert result.scope_marker.rt01_hosted_only is True
    assert result.scope_marker.r05_first_slice_only is True
    assert result.state.override_scope in {
        "project_continuation_bounded_override",
        "surface_throttle_only",
        "none",
    }
    assert result.state.override_scope != "global_full_control"
    assert view.reason


def test_disabled_path_returns_honest_no_safe_fallback() -> None:
    disabled = build_r05_harness_case(harness_cases()["disabled"])
    assert disabled.state.protective_mode is R05ProtectiveMode.INSUFFICIENT_BASIS_FOR_OVERRIDE
    assert disabled.gate.protective_state_consumer_ready is False
    assert "r05_disabled" in disabled.gate.restrictions
