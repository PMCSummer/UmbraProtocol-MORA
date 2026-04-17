from __future__ import annotations

from dataclasses import dataclass

from substrate.o01_other_entity_model import O01EntitySignal, build_o01_other_entity_model
from substrate.o02_intersubjective_allostasis import (
    O02InteractionDiagnosticsInput,
    build_o02_intersubjective_allostasis,
)
from substrate.o03_strategy_class_evaluation import (
    O03CandidateMoveKind,
    O03CandidateStrategyInput,
    O03LocalEffectivenessBand,
    build_o03_strategy_class_evaluation,
)
from tests.substrate.s05_multi_cause_attribution_factorization_testkit import (
    S05HarnessConfig,
    build_s05_harness_case,
)


@dataclass(frozen=True, slots=True)
class O03HarnessCase:
    case_id: str
    tick_index: int
    o01_signals: tuple[O01EntitySignal, ...] = ()
    o02_diagnostics: O02InteractionDiagnosticsInput = O02InteractionDiagnosticsInput()
    candidate_strategy: O03CandidateStrategyInput = O03CandidateStrategyInput()
    c04_selected_mode: str = "continue_stream"
    c05_revalidation_required: bool = False
    regulation_pressure_level: float = 0.48
    evaluation_enabled: bool = True
    s05_config: S05HarnessConfig | None = None


def _signal(
    *,
    signal_id: str,
    authority: str,
    relation: str,
    claim: str,
    referent: str = "user",
    turn_index: int = 1,
    confidence: float = 0.8,
    grounded: bool = True,
    quoted: bool = False,
    entity_id_hint: str | None = None,
) -> O01EntitySignal:
    return O01EntitySignal(
        signal_id=signal_id,
        entity_id_hint=entity_id_hint,
        referent_label=referent,
        source_authority=authority,
        relation_class=relation,
        claim_value=claim,
        confidence=confidence,
        grounded=grounded,
        quoted=quoted,
        turn_index=turn_index,
        provenance=f"tests.o03.signal:{signal_id}",
        target_claim=None,
    )


def _grounded_user_signals() -> tuple[O01EntitySignal, ...]:
    return (
        _signal(
            signal_id="u1",
            authority="current_user_direct",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=1,
        ),
        _signal(
            signal_id="u2",
            authority="current_user_direct",
            relation="stable_claim",
            claim="prefers_structured_lists",
            turn_index=2,
        ),
        _signal(
            signal_id="u3",
            authority="current_user_direct",
            relation="knowledge_boundary",
            claim="knows_cli_basics",
            turn_index=3,
        ),
    )


def build_o03_harness_case(case: O03HarnessCase):
    o01_result = build_o01_other_entity_model(
        tick_id=f"o01-for-o03:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        signals=case.o01_signals,
        source_lineage=(f"tests.o03:{case.case_id}",),
        model_enabled=True,
    )
    s05_result = build_s05_harness_case(
        case.s05_config
        or S05HarnessConfig(
            case_id=f"o03-s05:{case.case_id}",
            tick_index=case.tick_index,
            deliberate_internal_act=True,
            endogenous_mode_shift=False,
            interoceptive_support=0.58,
            world_perturbation=True,
            observation_noise=0.25,
            c05_revalidation_required=case.c05_revalidation_required,
        )
    )
    o02_result = build_o02_intersubjective_allostasis(
        tick_id=f"o02-for-o03:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        o01_result=o01_result,
        s05_result=s05_result,
        c04_selected_mode=case.c04_selected_mode,
        c05_revalidation_required=case.c05_revalidation_required,
        regulation_pressure_level=case.regulation_pressure_level,
        interaction_diagnostics=case.o02_diagnostics,
        prior_state=None,
        source_lineage=(f"tests.o03:{case.case_id}",),
        allostasis_enabled=True,
    )
    return build_o03_strategy_class_evaluation(
        tick_id=f"o03:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        o01_result=o01_result,
        o02_result=o02_result,
        s05_result=s05_result,
        candidate_strategy=case.candidate_strategy,
        regulation_pressure_level=case.regulation_pressure_level,
        c05_revalidation_required=case.c05_revalidation_required,
        source_lineage=(f"tests.o03:{case.case_id}",),
        evaluation_enabled=case.evaluation_enabled,
    )


def harness_cases() -> dict[str, O03HarnessCase]:
    grounded = _grounded_user_signals()
    return {
        "cooperative_transparent": O03HarnessCase(
            case_id="cooperative_transparent",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c1",
                candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
                explicit_disclosure_present=True,
                material_uncertainty_omitted=False,
                selective_omission_risk_marker=False,
                reversibility_preserved=True,
                repairability_preserved=True,
            ),
        ),
        "concealment_local_gain": O03HarnessCase(
            case_id="concealment_local_gain",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c2",
                candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
                explicit_disclosure_present=False,
                material_uncertainty_omitted=True,
                selective_omission_risk_marker=True,
                asymmetry_opportunity_marker=True,
                expected_local_effectiveness_band=O03LocalEffectivenessBand.HIGH,
                strong_compliance_pull_marker=True,
                reversibility_preserved=False,
                repairability_preserved=False,
            ),
        ),
        "selective_omission_material": O03HarnessCase(
            case_id="selective_omission_material",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c3",
                selective_omission_risk_marker=True,
                material_uncertainty_omitted=True,
                explicit_disclosure_present=False,
            ),
        ),
        "selective_omission_disclosed": O03HarnessCase(
            case_id="selective_omission_disclosed",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c4",
                selective_omission_risk_marker=True,
                material_uncertainty_omitted=False,
                explicit_disclosure_present=True,
            ),
        ),
        "dependency_shaping_low": O03HarnessCase(
            case_id="dependency_shaping_low",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c5",
                dependency_shaping_marker=True,
                repeated_dependency_pressure_count=1,
            ),
        ),
        "dependency_shaping_repeated_high": O03HarnessCase(
            case_id="dependency_shaping_repeated_high",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c6",
                dependency_shaping_marker=True,
                autonomy_narrowing_marker=True,
                repeated_dependency_pressure_count=4,
                strong_compliance_pull_marker=True,
                reversibility_preserved=False,
                repairability_preserved=False,
            ),
        ),
        "autonomy_pressure_high": O03HarnessCase(
            case_id="autonomy_pressure_high",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c7",
                autonomy_narrowing_marker=True,
                strong_compliance_pull_marker=True,
            ),
        ),
        "asymmetry_disclosed_bounded": O03HarnessCase(
            case_id="asymmetry_disclosed_bounded",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c8",
                asymmetry_opportunity_marker=True,
                explicit_disclosure_present=True,
                selective_omission_risk_marker=False,
            ),
        ),
        "asymmetry_concealed_exploitative": O03HarnessCase(
            case_id="asymmetry_concealed_exploitative",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c9",
                asymmetry_opportunity_marker=True,
                explicit_disclosure_present=False,
                selective_omission_risk_marker=True,
                material_uncertainty_omitted=True,
            ),
        ),
        "underconstrained_strategy": O03HarnessCase(
            case_id="underconstrained_strategy",
            tick_index=1,
            o01_signals=(),
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c10",
                explicit_disclosure_present=False,
            ),
        ),
        "polite_manipulative": O03HarnessCase(
            case_id="polite_manipulative",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c11",
                candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
                explicit_disclosure_present=False,
                material_uncertainty_omitted=True,
                selective_omission_risk_marker=True,
                dependency_shaping_marker=True,
                strong_compliance_pull_marker=True,
                expected_local_effectiveness_band=O03LocalEffectivenessBand.HIGH,
            ),
        ),
        "transparent_persuasion": O03HarnessCase(
            case_id="transparent_persuasion",
            tick_index=1,
            o01_signals=grounded,
            candidate_strategy=O03CandidateStrategyInput(
                candidate_move_id="c12",
                candidate_move_kind=O03CandidateMoveKind.RECOMMENDATION,
                explicit_disclosure_present=True,
                material_uncertainty_omitted=False,
                selective_omission_risk_marker=False,
                reversibility_preserved=True,
                repairability_preserved=True,
                strong_compliance_pull_marker=False,
            ),
        ),
    }
