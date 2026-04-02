from dataclasses import fields

import pytest

from substrate.dictum_candidates import (
    DictumCandidate,
    DictumCandidateBundle,
    DictumCandidateResult,
    build_dictum_candidates,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _typed_inputs():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l04-bound", content="we track alpha"),
        SourceMetadata(
            source_id="user-l04-bound",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    return lexical, syntax, surface


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "illocution",
        "commitment",
        "accepted_fact",
        "world_truth",
        "intent",
        "policy",
        "self_applicability",
        "discourse_acceptance",
        "final_proposition",
    }
    field_names = (
        {field_info.name for field_info in fields(DictumCandidate)}
        | {field_info.name for field_info in fields(DictumCandidateBundle)}
        | {field_info.name for field_info in fields(DictumCandidateResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_typed_only_input_required_on_critical_path() -> None:
    with pytest.raises(TypeError):
        build_dictum_candidates("raw lexical", "raw syntax")


def test_no_hidden_final_resolution_contract_is_explicit() -> None:
    lexical, syntax, surface = _typed_inputs()
    result = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    assert result.no_final_resolution_performed is True
    assert result.bundle.no_final_resolution_performed is True
