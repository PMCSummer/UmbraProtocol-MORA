from __future__ import annotations

import pytest

from substrate.o02_intersubjective_allostasis import (
    O02BoundaryProtectionStatus,
    O02InteractionDiagnosticsInput,
    O02InteractionMode,
    O02OtherModelRelianceStatus,
    O02RegulationLeverPreference,
    O02RepairPressureBand,
)
from tests.substrate.o02_intersubjective_allostasis_testkit import (
    O02HarnessCase,
    build_o02_harness_case,
    harness_cases,
)
from tests.substrate.s05_multi_cause_attribution_factorization_testkit import S05HarnessConfig


def test_harness_has_required_coverage() -> None:
    cases = harness_cases()
    assert len(cases) >= 6
    assert {
        "clean_grounded",
        "repair_heavy",
        "underconstrained_other",
        "precision_request",
        "social_smoothing_conflict",
        "disabled_path",
    }.issubset(set(cases.keys()))


def test_repair_history_changes_later_regulation_strategy() -> None:
    clean = build_o02_harness_case(harness_cases()["clean_grounded"])
    repair_heavy = build_o02_harness_case(harness_cases()["repair_heavy"])
    assert clean.state.interaction_mode in {
        O02InteractionMode.LOW_FRICTION_MODE,
        O02InteractionMode.HIGH_PRECISION_MODE,
    }
    assert repair_heavy.state.interaction_mode in {
        O02InteractionMode.REPAIR_HEAVY,
        O02InteractionMode.CONSERVATIVE_MODE_ONLY,
    }
    assert repair_heavy.state.repair_pressure in {
        O02RepairPressureBand.MEDIUM,
        O02RepairPressureBand.HIGH,
    }
    assert O02RegulationLeverPreference.ASK_TARGETED_CHECK in repair_heavy.state.lever_preferences


def test_underconstrained_other_model_triggers_conservative_mode() -> None:
    result = build_o02_harness_case(harness_cases()["underconstrained_other"])
    assert result.state.other_load_underconstrained is True
    assert result.state.other_model_reliance_status is O02OtherModelRelianceStatus.UNDERCONSTRAINED
    assert result.state.interaction_mode is O02InteractionMode.CONSERVATIVE_MODE_ONLY
    assert result.state.no_safe_regulation_claim is True
    assert result.gate.clarification_ready is False


def test_self_boundary_preserved_under_social_smoothing_pressure() -> None:
    result = build_o02_harness_case(harness_cases()["social_smoothing_conflict"])
    assert result.state.self_other_constraint_conflict is True
    assert result.state.boundary_protection_status is O02BoundaryProtectionStatus.CONFLICTED
    assert O02RegulationLeverPreference.PRESERVE_BOUNDARY in result.state.lever_preferences
    assert (
        O02RegulationLeverPreference.PRESERVE_EXPLICIT_UNCERTAINTY
        in result.state.lever_preferences
    )


def test_state_is_not_just_tone_label() -> None:
    result = build_o02_harness_case(harness_cases()["precision_request"])
    assert result.state.detail_budget.value in {"narrow", "balanced", "expanded"}
    assert result.state.pace_budget.value in {"narrow", "balanced", "expanded"}
    assert isinstance(result.state.clarification_threshold, float)
    assert result.state.justification_links
    assert result.state.lever_preferences
    assert result.state.uncertainty_notice_policy in {
        "preserve_explicit_uncertainty",
        "bounded_directness",
    }


def test_politeness_baseline_does_not_match_true_regulation() -> None:
    grounded = build_o02_harness_case(harness_cases()["clean_grounded"])
    underconstrained = build_o02_harness_case(harness_cases()["underconstrained_other"])
    assert grounded.state.interaction_mode != underconstrained.state.interaction_mode
    assert grounded.gate.clarification_ready is True
    assert underconstrained.gate.clarification_ready is False
    assert "comfort" not in underconstrained.reason.lower()
    assert "empathy" not in underconstrained.reason.lower()


def test_ablation_disabled_model_returns_honest_fallback() -> None:
    result = build_o02_harness_case(harness_cases()["disabled_path"])
    assert result.state.no_safe_regulation_claim is True
    assert result.gate.downstream_consumer_ready is False
    assert "o02_disabled" in result.gate.restrictions


def test_metamorphic_self_side_caution_changes_boundary_posture() -> None:
    base = build_o02_harness_case(harness_cases()["clean_grounded"])
    caution_case = O02HarnessCase(
        case_id="metamorphic_caution",
        tick_index=1,
        o01_signals=harness_cases()["clean_grounded"].o01_signals,
        interaction_diagnostics=harness_cases()["social_smoothing_conflict"].interaction_diagnostics,
        regulation_pressure_level=0.72,
    )
    caution = build_o02_harness_case(caution_case)
    assert base.state.boundary_protection_status != caution.state.boundary_protection_status
    assert base.state.interaction_mode != caution.state.interaction_mode


def test_s05_shape_branch_modulates_o02_posture_under_matched_o01_context() -> None:
    base = build_o02_harness_case(
        O02HarnessCase(
            case_id="s05-shape-base",
            tick_index=1,
            o01_signals=harness_cases()["clean_grounded"].o01_signals,
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_misunderstanding_count=1,
            ),
            s05_config=S05HarnessConfig(
                case_id="o02-s05-shape-base",
                tick_index=1,
                world_perturbation=True,
                observation_noise=0.2,
                latent_unmodeled_disturbance=0.0,
            ),
        )
    )
    shaped = build_o02_harness_case(
        O02HarnessCase(
            case_id="s05-shape-shaped",
            tick_index=1,
            o01_signals=harness_cases()["clean_grounded"].o01_signals,
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_misunderstanding_count=1,
            ),
            s05_config=S05HarnessConfig(
                case_id="o02-s05-shape-shaped",
                tick_index=1,
                world_perturbation=False,
                observation_noise=0.85,
                latent_unmodeled_disturbance=0.7,
            ),
        )
    )
    assert base.state.s05_shape_modulation_applied is False
    assert shaped.state.s05_shape_modulation_applied is True
    assert base.state.uncertainty_notice_policy != shaped.state.uncertainty_notice_policy
    assert shaped.state.uncertainty_notice_policy == "preserve_explicit_uncertainty"


def test_strong_disagreement_risk_activates_boundary_guard_under_smoothing_pressure() -> None:
    baseline = build_o02_harness_case(
        O02HarnessCase(
            case_id="disagreement-baseline",
            tick_index=1,
            o01_signals=harness_cases()["clean_grounded"].o01_signals,
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
            ),
        )
    )
    guarded = build_o02_harness_case(
        O02HarnessCase(
            case_id="disagreement-guarded",
            tick_index=1,
            o01_signals=harness_cases()["clean_grounded"].o01_signals,
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
                strong_disagreement_risk=True,
            ),
        )
    )
    assert baseline.state.strong_disagreement_guard_applied is False
    assert guarded.state.strong_disagreement_guard_applied is True
    assert guarded.state.boundary_protection_status is O02BoundaryProtectionStatus.CONFLICTED
    assert O02RegulationLeverPreference.PRESERVE_BOUNDARY in guarded.state.lever_preferences
    assert O02RegulationLeverPreference.PRESERVE_EXPLICIT_UNCERTAINTY in guarded.state.lever_preferences


@pytest.mark.parametrize(
    "case_id,expected_mode",
    [
        ("clean_grounded", {O02InteractionMode.LOW_FRICTION_MODE}),
        (
            "repair_heavy",
            {O02InteractionMode.REPAIR_HEAVY, O02InteractionMode.CONSERVATIVE_MODE_ONLY},
        ),
        ("underconstrained_other", {O02InteractionMode.CONSERVATIVE_MODE_ONLY}),
        ("social_smoothing_conflict", {O02InteractionMode.BOUNDARY_PROTECTIVE_MODE}),
    ],
)
def test_matrix_modes_vary_across_regulation_inputs(
    case_id: str,
    expected_mode: set[O02InteractionMode],
) -> None:
    result = build_o02_harness_case(harness_cases()[case_id])
    assert result.state.interaction_mode in expected_mode
