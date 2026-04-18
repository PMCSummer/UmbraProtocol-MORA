from __future__ import annotations

from substrate.o04_rupture_hostility_coercion import (
    O04DynamicType,
    O04RuptureStatus,
    derive_o04_dynamic_consumer_view,
)
from tests.substrate.o04_rupture_hostility_coercion_testkit import (
    build_o04_harness_case,
    harness_cases,
)


def test_harness_has_required_contrast_coverage() -> None:
    cases = harness_cases()
    assert len(cases) >= 12
    assert {
        "rude_noncoercive",
        "polite_coercive",
        "same_words_low_leverage",
        "same_words_high_leverage",
        "repeated_withdrawal_pattern",
        "underconstrained_no_events",
    }.issubset(set(cases.keys()))


def test_same_words_different_leverage_changes_coercion_assessment() -> None:
    low = build_o04_harness_case(harness_cases()["same_words_low_leverage"])
    high = build_o04_harness_case(harness_cases()["same_words_high_leverage"])
    assert low.state.coercion_candidates == ()
    assert len(high.state.coercion_candidates) > 0
    assert low.telemetry.dynamic_type in {
        O04DynamicType.DISAGREEMENT_ONLY,
        O04DynamicType.AMBIGUOUS_PRESSURE,
        O04DynamicType.HARD_BARGAINING,
    }
    assert high.telemetry.dynamic_type in {
        O04DynamicType.COERCIVE_PRESSURE_CANDIDATE,
        O04DynamicType.FORCED_COMPLIANCE_CANDIDATE,
    }


def test_rude_but_noncoercive_does_not_trigger_strong_coercion() -> None:
    rude = build_o04_harness_case(harness_cases()["rude_noncoercive"])
    assert rude.state.coercion_candidates == ()
    assert rude.telemetry.dynamic_type in {
        O04DynamicType.HOSTILITY_CANDIDATE,
        O04DynamicType.DISAGREEMENT_ONLY,
        O04DynamicType.AMBIGUOUS_PRESSURE,
    }
    assert rude.state.tone_shortcut_forbidden_applied is True


def test_polite_coercion_is_not_missed() -> None:
    polite = build_o04_harness_case(harness_cases()["polite_coercive"])
    view = derive_o04_dynamic_consumer_view(polite)
    assert len(polite.state.coercion_candidates) > 0
    assert polite.telemetry.dynamic_type in {
        O04DynamicType.COERCIVE_PRESSURE_CANDIDATE,
        O04DynamicType.FORCED_COMPLIANCE_CANDIDATE,
        O04DynamicType.RUPTURE_RISK,
    }
    assert view.coercive_structure_candidate is True


def test_legitimacy_hint_prevents_overcalling_coercion() -> None:
    supported = build_o04_harness_case(harness_cases()["legitimacy_supported_boundary"])
    unknown = build_o04_harness_case(harness_cases()["legitimacy_unknown_pressure"])
    assert supported.telemetry.dynamic_type in {
        O04DynamicType.BOUNDARY_ENFORCEMENT_BOUNDED,
        O04DynamicType.HARD_BARGAINING,
    }
    assert unknown.telemetry.dynamic_type in {
        O04DynamicType.AMBIGUOUS_PRESSURE,
        O04DynamicType.HARD_BARGAINING,
    }
    assert unknown.state.legitimacy_boundary_underconstrained is True
    assert supported.state.legitimacy_boundary_underconstrained is False


def test_repeated_withdrawal_updates_rupture_state() -> None:
    repeated = build_o04_harness_case(harness_cases()["repeated_withdrawal_pattern"])
    repaired = build_o04_harness_case(harness_cases()["repair_attempt_after_withdrawal"])
    assert repeated.state.rupture_status in {
        O04RuptureStatus.RUPTURE_RISK_ONLY,
        O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE,
    }
    assert repaired.state.rupture_status in {
        O04RuptureStatus.REPAIR_IN_PROGRESS,
        O04RuptureStatus.DEESCALATED_BUT_NOT_CLOSED,
        O04RuptureStatus.RUPTURE_RISK_ONLY,
    }
    assert repaired.state.counterevidence_summary


def test_underconstrained_strategy_falls_back_honestly() -> None:
    underconstrained = build_o04_harness_case(harness_cases()["underconstrained_no_events"])
    view = derive_o04_dynamic_consumer_view(underconstrained)
    assert underconstrained.state.no_safe_dynamic_claim is True
    assert underconstrained.telemetry.dynamic_type is O04DynamicType.AMBIGUOUS_PRESSURE
    assert view.no_strong_dynamic_claim is True
    assert underconstrained.gate.dynamic_contract_consumer_ready is False


def test_state_is_not_just_negative_tone() -> None:
    result = build_o04_harness_case(harness_cases()["polite_coercive_vs_rude_noncoercive_pair"])
    assert result.state.interaction_model_id.startswith("o04-dynamic:")
    assert len(result.state.directional_links) >= 1
    first_link = result.state.directional_links[0]
    assert first_link.actor_ref is not None or first_link.target_ref is not None
    assert first_link.leverage_surface.value in {
        "none_detected",
        "blocked_option",
        "sanction_threat",
        "access_withdrawal",
        "dependency_withdrawal",
        "resource_control",
        "commitment_leverage",
        "exclusion_channel",
    }
    assert result.state.justification_links
    assert result.reason


def test_disabled_path_returns_honest_no_safe_fallback() -> None:
    disabled = build_o04_harness_case(harness_cases()["disabled"])
    assert disabled.state.no_safe_dynamic_claim is True
    assert disabled.gate.dynamic_contract_consumer_ready is False
    assert "o04_disabled" in disabled.gate.restrictions
