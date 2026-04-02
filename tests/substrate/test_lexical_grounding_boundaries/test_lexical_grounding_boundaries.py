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
    LexemeCandidate,
    LexicalGroundingBundle,
    LexicalGroundingResult,
    ReferenceHypothesis,
    build_lexical_grounding_hypotheses,
    evaluate_lexical_grounding_downstream_gate,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _l03_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-l03-bound-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-l03-bound",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    return build_lexical_grounding_hypotheses(syntax_result, utterance_surface=surface_result)


def test_public_l03_models_exclude_dictum_illocution_commitment_and_final_resolution_fields() -> None:
    forbidden = {
        "dictum",
        "proposition",
        "accepted_fact",
        "world_truth",
        "illocution",
        "commitment",
        "repair_policy",
        "final_resolution",
        "selected_referent",
        "selected_sense",
    }
    field_names = (
        {field_info.name for field_info in fields(LexicalGroundingBundle)}
        | {field_info.name for field_info in fields(LexicalGroundingResult)}
        | {field_info.name for field_info in fields(LexemeCandidate)}
        | {field_info.name for field_info in fields(ReferenceHypothesis)}
    )
    assert forbidden.isdisjoint(field_names)


def test_build_and_gate_reject_raw_untyped_critical_path() -> None:
    with pytest.raises(TypeError):
        build_lexical_grounding_hypotheses("raw text")
    with pytest.raises(TypeError):
        evaluate_lexical_grounding_downstream_gate("raw lexical grounding")


def test_gate_restrictions_reflect_uncertainty_as_load_bearing_output() -> None:
    result = _l03_result("he qzxv here")
    gate = evaluate_lexical_grounding_downstream_gate(result)

    assert gate.accepted is True
    assert "no_final_resolution_performed" in gate.restrictions
    assert (
        "unknown_grounding_present" in gate.restrictions
        or "unresolved_reference_present" in gate.restrictions
        or "grounding_conflict_present" in gate.restrictions
    )
