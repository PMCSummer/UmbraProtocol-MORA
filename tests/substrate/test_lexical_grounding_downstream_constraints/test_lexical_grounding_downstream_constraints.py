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
from substrate.lexical_grounding import (
    LexicalGroundingBundle,
    LexicalGroundingResult,
    build_lexical_grounding_hypotheses,
    evaluate_lexical_grounding_downstream_gate,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _l03_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l03-gate", content="he and bank"),
        SourceMetadata(
            source_id="user-l03-gate",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    syntax_result = build_morphosyntax_candidate_space(
        build_utterance_surface(epistemic.unit)
    )
    return build_lexical_grounding_hypotheses(syntax_result), syntax_result


def test_downstream_gate_rejects_raw_input_and_accepts_typed_bundle() -> None:
    with pytest.raises(TypeError):
        evaluate_lexical_grounding_downstream_gate("raw text")
    with pytest.raises(TypeError):
        evaluate_lexical_grounding_downstream_gate({"bundle": "raw"})

    result, _ = _l03_result()
    gate_from_result = evaluate_lexical_grounding_downstream_gate(result)
    gate_from_bundle = evaluate_lexical_grounding_downstream_gate(result.bundle)
    assert gate_from_result.accepted is True
    assert gate_from_bundle.accepted is True
    assert gate_from_result.restrictions


def test_no_final_resolution_and_no_discourse_acceptance_fields() -> None:
    result, _ = _l03_result()
    assert result.no_final_resolution_performed is True
    assert result.bundle.no_final_resolution_performed is True
    assert not hasattr(result, "accepted_discourse_fact")
    assert not hasattr(result.bundle, "accepted_discourse_fact")


def test_anti_overreach_no_dictum_illocution_commitment_fields() -> None:
    forbidden = {
        "dictum",
        "proposition",
        "meaning",
        "truth",
        "illocution",
        "commitment",
        "repair_policy",
        "world_truth",
    }
    field_names = (
        {field_info.name for field_info in fields(LexicalGroundingBundle)}
        | {field_info.name for field_info in fields(LexicalGroundingResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_ablation_lite_without_l03_typed_bundle_downstream_contract_degrades() -> None:
    result, syntax_result = _l03_result()
    assert evaluate_lexical_grounding_downstream_gate(result).accepted is True
    with pytest.raises(TypeError):
        evaluate_lexical_grounding_downstream_gate(syntax_result)
