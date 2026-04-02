from dataclasses import replace

import pytest

from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    build_lexical_grounding_hypotheses,
    evaluate_lexical_grounding_downstream_gate,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _l03_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-l03-neg-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-l03-neg",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    return build_lexical_grounding_hypotheses(syntax_result, utterance_surface=surface_result)


def test_negative_control_without_candidate_bundle_downstream_contract_degrades() -> None:
    result = _l03_result("alpha he")
    gate_with_bundle = evaluate_lexical_grounding_downstream_gate(result)
    assert gate_with_bundle.accepted is True

    ablated_bundle = replace(
        result.bundle,
        mention_anchors=(),
        lexeme_candidates=(),
        sense_candidates=(),
        entity_candidates=(),
        reference_hypotheses=(),
        deixis_candidates=(),
        unknown_states=(),
        conflicts=(),
        ambiguity_reasons=("ablated",),
    )
    gate_ablated = evaluate_lexical_grounding_downstream_gate(ablated_bundle)
    assert gate_ablated.accepted is False
    assert "no_mentions" in gate_ablated.restrictions


def test_negative_control_post_hoc_text_report_is_not_typed_lexical_ledger() -> None:
    with pytest.raises(TypeError):
        evaluate_lexical_grounding_downstream_gate(
            {
                "report": "pronoun resolved to entity alpha",
                "confidence": 0.99,
            }
        )


def test_negative_control_adversarial_case_requires_uncertainty_markers() -> None:
    result = _l03_result("he bank qzxv here")
    has_uncertainty = (
        bool(result.bundle.unknown_states)
        or bool(result.bundle.conflicts)
        or any(hypothesis.unresolved for hypothesis in result.bundle.reference_hypotheses)
    )

    assert has_uncertainty is True
