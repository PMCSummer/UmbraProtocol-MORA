from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    GroundedSemanticResult,
    OperatorKind,
    SourceAnchorKind,
    UncertaintyKind,
    build_grounded_semantic_substrate_legacy_compatibility,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.lexicon import create_seed_lexicon_state
from substrate.morphosyntax import build_morphosyntax_candidate_space


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    category: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    # Negation / scope.
    CaseSpec("neg-1", "negation_scope", "we do not trust alpha if beta shifts"),
    CaseSpec("neg-2", "negation_scope", "alpha is not stable unless beta recovers"),
    CaseSpec("neg-3", "negation_scope", "мы не должны запускать delta и epsilon"),
    CaseSpec("neg-4", "negation_scope", "if alpha is not ready, we hold"),
    # Quotation / source.
    CaseSpec("src-1", "quotation_source", '"alpha moved" said we'),
    CaseSpec("src-2", "quotation_source", 'he said "beta is fine" according to gamma'),
    CaseSpec("src-3", "quotation_source", '"delta is not ready", operator said'),
    CaseSpec("src-4", "quotation_source", 'according to analyst, "epsilon may wait"'),
    # Dictum / modus.
    CaseSpec("mod-1", "dictum_modus", "maybe alpha should move now?"),
    CaseSpec("mod-2", "dictum_modus", "perhaps we can proceed?"),
    CaseSpec("mod-3", "dictum_modus", "может ли beta быть готов?"),
    CaseSpec("mod-4", "dictum_modus", "well we must probably hold"),
    # Clause ambiguity / punctuation perturbation.
    CaseSpec("amb-1", "clause_punctuation", "alpha, beta... maybe gamma"),
    CaseSpec("amb-2", "clause_punctuation", "if alpha then beta, or gamma??"),
    CaseSpec("amb-3", "clause_punctuation", '"alpha"... said he??'),
    CaseSpec("amb-4", "clause_punctuation", "delta... maybe, maybe not"),
    # Noisy / ASR-like corruption.
    CaseSpec("noise-1", "noisy_input", "um alpha uh not sure qzxv"),
    CaseSpec("noise-2", "noisy_input", "alpha beta ???"),
    CaseSpec("noise-3", "noisy_input", "i i i think gamma..."),
    CaseSpec("noise-4", "noisy_input", "там это эээ beta maybe"),
)


def _run_pipeline(case: CaseSpec) -> GroundedSemanticResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-g01-{case.case_id}", content=case.text),
        SourceMetadata(
            source_id=f"user-g01-{case.case_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref=f"ctx-g01-{case.case_id}"),
        lexicon_state=create_seed_lexicon_state(),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref=f"ctx-g01-{case.case_id}"),
    )
    return build_grounded_semantic_substrate_legacy_compatibility(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref=f"m03-anchor-{case.case_id}",
        cooperation_anchor_ref=f"o03-anchor-{case.case_id}",
    )


def test_case_matrix_contains_required_20_inputs() -> None:
    assert len(_CASES) == 20
    category_counts: dict[str, int] = {}
    for case in _CASES:
        category_counts[case.category] = category_counts.get(case.category, 0) + 1
    assert category_counts == {
        "negation_scope": 4,
        "quotation_source": 4,
        "dictum_modus": 4,
        "clause_punctuation": 4,
        "noisy_input": 4,
    }


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g01_builds_typed_grounded_substrate_for_required_case_matrix(case: CaseSpec) -> None:
    result = _run_pipeline(case)
    assert isinstance(result, GroundedSemanticResult)
    assert result.bundle.substrate_units
    assert result.bundle.phrase_scaffolds
    assert result.bundle.dictum_carriers
    assert result.no_final_semantic_resolution is True
    assert result.bundle.no_final_semantic_resolution is True
    assert result.telemetry.attempted_paths
    assert result.telemetry.reversible_span_mapping_present is True

    operator_kinds = {kind for kind in result.telemetry.operator_kinds}
    anchor_kinds = {anchor.anchor_kind for anchor in result.bundle.source_anchors}
    uncertainty_kinds = {kind for kind in result.telemetry.uncertainty_kinds}

    if case.category == "negation_scope":
        assert OperatorKind.NEGATION.value in operator_kinds
    elif case.category == "quotation_source":
        assert (
            OperatorKind.QUOTATION.value in operator_kinds
            or SourceAnchorKind.REPORTED_SPEECH in anchor_kinds
        )
    elif case.category == "dictum_modus":
        assert result.bundle.modus_carriers
        assert operator_kinds.intersection(
            {
                OperatorKind.MODALITY.value,
                OperatorKind.INTERROGATION.value,
                OperatorKind.DISCOURSE_PARTICLE.value,
            }
        )
    elif case.category == "clause_punctuation":
        assert uncertainty_kinds.intersection(
            {
                UncertaintyKind.SURFACE_CORRUPTION_PRESENT.value,
                UncertaintyKind.CLAUSE_BOUNDARY_UNCERTAIN.value,
                UncertaintyKind.TOKENIZATION_AMBIGUOUS.value,
            }
        )
    elif case.category == "noisy_input":
        assert result.partial_known is True
        assert result.bundle.uncertainty_markers


def test_scope_sensitive_operator_perturbation_changes_scaffold_state() -> None:
    with_negation = _run_pipeline(CaseSpec("scope-a", "negation_scope", "we do not track alpha"))
    without_negation = _run_pipeline(CaseSpec("scope-b", "negation_scope", "we track alpha"))
    with_ops = {carrier.operator_kind for carrier in with_negation.bundle.operator_carriers}
    without_ops = {carrier.operator_kind for carrier in without_negation.bundle.operator_carriers}
    assert OperatorKind.NEGATION in with_ops
    assert OperatorKind.NEGATION not in without_ops
