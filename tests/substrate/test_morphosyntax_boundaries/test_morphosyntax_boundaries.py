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
    MorphTokenFeatures,
    SyntaxHypothesis,
    SyntaxHypothesisResult,
    SyntaxHypothesisSet,
    build_morphosyntax_candidate_space,
    evaluate_morphosyntax_downstream_gate,
)


def _surface_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-bnd-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


def test_public_l02_models_do_not_expose_semantic_truth_or_policy_fields() -> None:
    forbidden = {
        "dictum",
        "truth",
        "meaning",
        "semantics",
        "illocution",
        "intent",
        "commitment",
        "policy",
        "referent",
        "entity",
        "lexeme",
    }
    model_field_names = (
        {f.name for f in fields(MorphTokenFeatures)}
        | {f.name for f in fields(SyntaxHypothesis)}
        | {f.name for f in fields(SyntaxHypothesisSet)}
        | {f.name for f in fields(SyntaxHypothesisResult)}
    )
    assert forbidden.isdisjoint(model_field_names)


def test_ambiguity_heavy_case_keeps_no_selected_winner_contract() -> None:
    result = build_morphosyntax_candidate_space(_surface_result("alpha beta ... gamma delta"))
    unresolved_count = sum(
        len(h.unresolved_attachments) for h in result.hypothesis_set.hypotheses
    )
    assert result.hypothesis_set.no_selected_winner is True
    assert len(result.hypothesis_set.hypotheses) > 1 or unresolved_count > 0


def test_gate_rejects_raw_surface_and_raw_text_paths() -> None:
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate("raw text")

    surface_result = _surface_result("alpha beta.")
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate(surface_result.surface)


def test_ablation_lite_replacing_typed_syntax_path_with_raw_surface_breaks_contract() -> None:
    surface_result = _surface_result("we do not track alpha beta")
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    gate = evaluate_morphosyntax_downstream_gate(syntax_result.hypothesis_set)
    assert gate.accepted is True
    with pytest.raises(TypeError):
        evaluate_morphosyntax_downstream_gate(surface_result)
