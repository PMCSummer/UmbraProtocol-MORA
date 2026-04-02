from dataclasses import fields

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
from substrate.morphosyntax import (
    SyntaxHypothesis,
    build_morphosyntax_candidate_space,
    evaluate_morphosyntax_downstream_gate,
)


def _surface_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


def test_downstream_gate_rejects_raw_and_accepts_typed_hypothesis_set() -> None:
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate("raw text")

    surface_result = _surface_result("blarf zint.")
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    gate = evaluate_morphosyntax_downstream_gate(syntax_result.hypothesis_set)
    assert gate.accepted is True
    assert gate.accepted_hypothesis_ids


def test_l02_ablation_lite_without_l02_typed_candidate_space_gate_fails() -> None:
    surface = _surface_result("blarf zint.").surface
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate(surface)


def test_l02_models_do_not_expose_semantic_or_illocution_fields() -> None:
    forbidden = {"dictum", "truth", "meaning", "illocution", "intent", "commitment", "appraisal"}
    field_names = {f.name for f in fields(SyntaxHypothesis)}
    assert forbidden.isdisjoint(field_names)
