from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
    O03LocalEffectivenessBand,
    O03StrategyClass,
    derive_o03_strategy_consumer_view,
)
from tests.substrate.o03_strategy_class_evaluation_testkit import (
    O03HarnessCase,
    build_o03_harness_case,
    harness_cases,
)


def test_harness_has_required_paired_coverage() -> None:
    cases = harness_cases()
    assert len(cases) >= 12
    assert {
        "cooperative_transparent",
        "concealment_local_gain",
        "selective_omission_material",
        "dependency_shaping_repeated_high",
        "underconstrained_strategy",
        "transparent_persuasion",
    }.issubset(set(cases.keys()))


def test_transparent_cooperation_beats_concealment_dependent_local_gain() -> None:
    transparent = build_o03_harness_case(harness_cases()["cooperative_transparent"])
    concealed = build_o03_harness_case(harness_cases()["concealment_local_gain"])
    assert transparent.state.cooperation_score > concealed.state.cooperation_score
    assert transparent.state.strategy_class in {
        O03StrategyClass.COOPERATIVE_PREFERRED,
        O03StrategyClass.NEUTRAL_COORDINATION,
        O03StrategyClass.COOPERATIVE_BUT_COSTLY,
        O03StrategyClass.ASYMMETRY_PRESENT_BUT_BOUNDED,
    }
    assert concealed.state.hidden_divergence_cost > transparent.state.hidden_divergence_cost
    assert concealed.state.strategy_class in {
        O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY,
        O03StrategyClass.MANIPULATION_RISK_HIGH,
    }


def test_selective_omission_raises_hidden_divergence_and_manipulation_risk() -> None:
    omitted = build_o03_harness_case(harness_cases()["selective_omission_material"])
    disclosed = build_o03_harness_case(harness_cases()["selective_omission_disclosed"])
    assert omitted.state.hidden_divergence_cost > disclosed.state.hidden_divergence_cost
    assert omitted.state.manipulation_risk_score > disclosed.state.manipulation_risk_score
    assert omitted.state.hidden_divergence_band.value in {"medium", "high"}


def test_dependency_shaping_accumulates_strategy_risk() -> None:
    low = build_o03_harness_case(harness_cases()["dependency_shaping_low"])
    high = build_o03_harness_case(harness_cases()["dependency_shaping_repeated_high"])
    assert high.state.dependency_induction_risk > low.state.dependency_induction_risk
    assert high.state.dependency_risk_band.value in {"medium", "high"}
    assert high.state.trust_fragility_forecast >= low.state.trust_fragility_forecast


def test_transparent_persuasion_is_not_mislabeled_as_manipulation() -> None:
    transparent = build_o03_harness_case(harness_cases()["transparent_persuasion"])
    assert transparent.state.strategy_class not in {
        O03StrategyClass.MANIPULATION_RISK_HIGH,
        O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY,
    }
    assert transparent.state.transparency_score >= 0.5
    assert transparent.state.no_safe_classification is False


def test_underconstrained_strategy_classification_falls_back_honestly() -> None:
    result = build_o03_harness_case(harness_cases()["underconstrained_strategy"])
    view = derive_o03_strategy_consumer_view(result)
    assert result.state.no_safe_classification is True or result.state.strategy_underconstrained is True
    assert result.state.strategy_class in {
        O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED,
        O03StrategyClass.NO_SAFE_CLASSIFICATION,
    }
    assert view.cooperative_default_preferred is True
    assert view.transparency_increase_required is True


def test_asymmetry_disclosed_bounded_not_auto_manipulation() -> None:
    bounded = build_o03_harness_case(harness_cases()["asymmetry_disclosed_bounded"])
    concealed = build_o03_harness_case(harness_cases()["asymmetry_concealed_exploitative"])
    assert bounded.state.strategy_class in {
        O03StrategyClass.ASYMMETRY_PRESENT_BUT_BOUNDED,
        O03StrategyClass.NEUTRAL_COORDINATION,
        O03StrategyClass.COOPERATIVE_BUT_COSTLY,
        O03StrategyClass.COOPERATIVE_PREFERRED,
    }
    assert concealed.state.strategy_class in {
        O03StrategyClass.MANIPULATION_RISK_HIGH,
        O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY,
    }
    assert concealed.state.concealed_state_divergence_required is True


def test_politeness_baseline_does_not_match_true_strategy_evaluation() -> None:
    warm_manipulative = build_o03_harness_case(harness_cases()["polite_manipulative"])
    transparent = build_o03_harness_case(harness_cases()["transparent_persuasion"])
    warm_view = derive_o03_strategy_consumer_view(warm_manipulative)
    transparent_view = derive_o03_strategy_consumer_view(transparent)
    assert warm_manipulative.state.candidate_move_id != transparent.state.candidate_move_id
    assert warm_view.block_exploitative_move_required != transparent_view.block_exploitative_move_required
    assert warm_view.transparency_increase_required is True
    assert transparent_view.transparency_increase_required is False


def test_disclosed_limitation_beats_concealment_dependent_omission() -> None:
    disclosed = build_o03_harness_case(
        O03HarnessCase(
            case_id="disclosed-limitation",
            tick_index=1,
            o01_signals=harness_cases()["cooperative_transparent"].o01_signals,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="dl-1",
                candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
                explicit_disclosure_present=True,
                material_uncertainty_omitted=False,
                selective_omission_risk_marker=True,
                downstream_effect_visibility_marker=True,
                truthfulness_constraint_tension=0.34,
                expected_local_effectiveness_band=O03LocalEffectivenessBand.HIGH,
            ),
        )
    )
    concealed = build_o03_harness_case(
        O03HarnessCase(
            case_id="concealment-dependent-omission",
            tick_index=1,
            o01_signals=harness_cases()["cooperative_transparent"].o01_signals,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="cd-1",
                candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
                explicit_disclosure_present=False,
                material_uncertainty_omitted=True,
                selective_omission_risk_marker=True,
                downstream_effect_visibility_marker=False,
                truthfulness_constraint_tension=0.34,
                expected_local_effectiveness_band=O03LocalEffectivenessBand.HIGH,
                strong_compliance_pull_marker=True,
            ),
        )
    )
    assert concealed.state.hidden_divergence_cost > disclosed.state.hidden_divergence_cost
    assert concealed.state.concealed_state_divergence_required is True
    assert disclosed.state.concealed_state_divergence_required is False
    assert concealed.gate.exploitative_move_block_required is True


def test_candidate_move_kind_is_behaviorally_relevant_under_same_markers() -> None:
    base = O03CandidateStrategyInput(
        candidate_move_id="kind-base",
        explicit_disclosure_present=True,
        material_uncertainty_omitted=False,
        selective_omission_risk_marker=False,
        autonomy_narrowing_marker=True,
        strong_compliance_pull_marker=True,
        expected_local_effectiveness_band=O03LocalEffectivenessBand.HIGH,
    )
    clarification = build_o03_harness_case(
        O03HarnessCase(
            case_id="kind-clarification",
            tick_index=1,
            o01_signals=harness_cases()["cooperative_transparent"].o01_signals,
            candidate_strategy=replace(
                base,
                candidate_move_id="kind-clarification",
                candidate_move_kind=O03CandidateMoveKind.CLARIFICATION,
            ),
        )
    )
    constraint = build_o03_harness_case(
        O03HarnessCase(
            case_id="kind-constraint",
            tick_index=1,
            o01_signals=harness_cases()["cooperative_transparent"].o01_signals,
            candidate_strategy=replace(
                base,
                candidate_move_id="kind-constraint",
                candidate_move_kind=O03CandidateMoveKind.CONSTRAINT_PROPOSAL,
            ),
        )
    )
    assert constraint.state.asymmetry_exploitation_score > clarification.state.asymmetry_exploitation_score
    assert constraint.state.manipulation_risk_score >= clarification.state.manipulation_risk_score


def test_regulation_pressure_level_is_behaviorally_relevant() -> None:
    risky = O03CandidateStrategyInput(
        candidate_move_id="pressure-risky",
        candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
        explicit_disclosure_present=False,
        material_uncertainty_omitted=True,
        selective_omission_risk_marker=True,
        dependency_shaping_marker=True,
        autonomy_narrowing_marker=True,
        strong_compliance_pull_marker=True,
        expected_local_effectiveness_band=O03LocalEffectivenessBand.HIGH,
    )
    low_pressure = build_o03_harness_case(
        O03HarnessCase(
            case_id="pressure-low",
            tick_index=1,
            o01_signals=harness_cases()["cooperative_transparent"].o01_signals,
            candidate_strategy=risky,
            regulation_pressure_level=0.35,
        )
    )
    high_pressure = build_o03_harness_case(
        O03HarnessCase(
            case_id="pressure-high",
            tick_index=1,
            o01_signals=harness_cases()["cooperative_transparent"].o01_signals,
            candidate_strategy=replace(risky, candidate_move_id="pressure-risky-high"),
            regulation_pressure_level=0.9,
        )
    )
    assert high_pressure.state.hidden_divergence_cost >= low_pressure.state.hidden_divergence_cost
    assert high_pressure.state.dependency_induction_risk >= low_pressure.state.dependency_induction_risk


def test_ablation_without_o03_collapses_to_honest_underconstrained_fallback() -> None:
    case = harness_cases()["cooperative_transparent"]
    disabled = build_o03_harness_case(
        O03HarnessCase(
            case_id="disabled",
            tick_index=case.tick_index,
            o01_signals=case.o01_signals,
            o02_diagnostics=case.o02_diagnostics,
            candidate_strategy=case.candidate_strategy,
            c04_selected_mode=case.c04_selected_mode,
            c05_revalidation_required=case.c05_revalidation_required,
            regulation_pressure_level=case.regulation_pressure_level,
            evaluation_enabled=False,
            s05_config=case.s05_config,
        )
    )
    assert disabled.state.no_safe_classification is True
    assert disabled.gate.strategy_contract_consumer_ready is False
    assert "o03_disabled" in disabled.gate.restrictions


@pytest.mark.parametrize(
    "case_id,expected_classes",
    [
        (
            "cooperative_transparent",
            {
                O03StrategyClass.COOPERATIVE_PREFERRED,
                O03StrategyClass.NEUTRAL_COORDINATION,
                O03StrategyClass.COOPERATIVE_BUT_COSTLY,
                O03StrategyClass.ASYMMETRY_PRESENT_BUT_BOUNDED,
            },
        ),
        (
            "concealment_local_gain",
            {
                O03StrategyClass.MANIPULATION_RISK_HIGH,
                O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY,
            },
        ),
        (
            "underconstrained_strategy",
            {
                O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED,
                O03StrategyClass.NO_SAFE_CLASSIFICATION,
            },
        ),
    ],
)
def test_matrix_strategy_class_bands_vary_by_input_profile(
    case_id: str,
    expected_classes: set[O03StrategyClass],
) -> None:
    result = build_o03_harness_case(harness_cases()[case_id])
    assert result.state.strategy_class in expected_classes
