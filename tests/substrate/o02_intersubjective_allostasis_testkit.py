from __future__ import annotations

from dataclasses import dataclass

from substrate.o01_other_entity_model import O01EntitySignal, build_o01_other_entity_model
from substrate.o02_intersubjective_allostasis import (
    O02IntersubjectiveAllostasisState,
    O02InteractionDiagnosticsInput,
    build_o02_intersubjective_allostasis,
)
from tests.substrate.s05_multi_cause_attribution_factorization_testkit import (
    S05HarnessConfig,
    build_s05_harness_case,
)


@dataclass(frozen=True, slots=True)
class O02HarnessCase:
    case_id: str
    tick_index: int
    o01_signals: tuple[O01EntitySignal, ...] = ()
    interaction_diagnostics: O02InteractionDiagnosticsInput = O02InteractionDiagnosticsInput()
    c04_selected_mode: str = "continue_stream"
    c05_revalidation_required: bool = False
    regulation_pressure_level: float = 0.42
    allostasis_enabled: bool = True
    s05_config: S05HarnessConfig | None = None


def _signal(
    *,
    signal_id: str,
    authority: str,
    relation: str,
    claim: str,
    referent: str = "user",
    turn_index: int = 1,
    confidence: float = 0.78,
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
        provenance=f"tests.o02.signal:{signal_id}",
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


def build_o02_harness_case(
    case: O02HarnessCase,
    *,
    prior_state: O02IntersubjectiveAllostasisState | None = None,
):
    o01_result = build_o01_other_entity_model(
        tick_id=f"o01-for-o02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        signals=case.o01_signals,
        source_lineage=(f"tests.o02:{case.case_id}",),
        model_enabled=True,
    )
    s05_result = build_s05_harness_case(
        case.s05_config
        or S05HarnessConfig(
            case_id=f"o02-s05:{case.case_id}",
            tick_index=case.tick_index,
            deliberate_internal_act=True,
            endogenous_mode_shift=False,
            interoceptive_support=0.68,
            world_perturbation=True,
            observation_noise=0.24,
            c05_revalidation_required=case.c05_revalidation_required,
        )
    )
    return build_o02_intersubjective_allostasis(
        tick_id=f"o02-{case.case_id}-{case.tick_index}",
        tick_index=case.tick_index,
        o01_result=o01_result,
        s05_result=s05_result,
        c04_selected_mode=case.c04_selected_mode,
        c05_revalidation_required=case.c05_revalidation_required,
        regulation_pressure_level=case.regulation_pressure_level,
        interaction_diagnostics=case.interaction_diagnostics,
        prior_state=prior_state,
        source_lineage=(f"tests.o02:{case.case_id}",),
        allostasis_enabled=case.allostasis_enabled,
    )


def harness_cases() -> dict[str, O02HarnessCase]:
    return {
        "clean_grounded": O02HarnessCase(
            case_id="clean_grounded",
            tick_index=1,
            o01_signals=_grounded_user_signals(),
            interaction_diagnostics=O02InteractionDiagnosticsInput(),
            regulation_pressure_level=0.4,
        ),
        "repair_heavy": O02HarnessCase(
            case_id="repair_heavy",
            tick_index=1,
            o01_signals=_grounded_user_signals(),
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                recent_corrections_count=2,
                recent_misunderstanding_count=2,
                clarification_failures=1,
                repetition_request_count=1,
            ),
            regulation_pressure_level=0.52,
        ),
        "underconstrained_other": O02HarnessCase(
            case_id="underconstrained_other",
            tick_index=1,
            o01_signals=(),
            interaction_diagnostics=O02InteractionDiagnosticsInput(),
            regulation_pressure_level=0.46,
        ),
        "precision_request": O02HarnessCase(
            case_id="precision_request",
            tick_index=1,
            o01_signals=_grounded_user_signals(),
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                precision_request=True,
            ),
            regulation_pressure_level=0.44,
        ),
        "social_smoothing_conflict": O02HarnessCase(
            case_id="social_smoothing_conflict",
            tick_index=1,
            o01_signals=_grounded_user_signals(),
            interaction_diagnostics=O02InteractionDiagnosticsInput(
                impatience_or_compression_request=True,
                self_side_caution_required=True,
            ),
            regulation_pressure_level=0.71,
        ),
        "disabled_path": O02HarnessCase(
            case_id="disabled_path",
            tick_index=1,
            o01_signals=_grounded_user_signals(),
            interaction_diagnostics=O02InteractionDiagnosticsInput(),
            allostasis_enabled=False,
        ),
    }
