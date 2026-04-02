from dataclasses import fields

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


def _dictum_result(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
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
    )
    return build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
    )


def test_public_dictum_models_do_not_carry_illocution_or_commitment_fields() -> None:
    forbidden = {
        "illocution",
        "intent",
        "commitment",
        "accepted_fact",
        "world_truth",
        "permission",
        "policy",
        "discourse_update",
        "self_applicability",
    }
    model_fields = (
        {item.name for item in fields(DictumCandidate)}
        | {item.name for item in fields(DictumCandidateBundle)}
        | {item.name for item in fields(DictumCandidateResult)}
    )
    assert forbidden.isdisjoint(model_fields)


def test_modus_like_surface_cues_do_not_change_candidate_only_contract() -> None:
    result = _dictum_result("please can you track alpha?", "m-l04-modus")
    assert result.bundle.dictum_candidates
    assert result.no_final_resolution_performed is True
    assert not hasattr(result.bundle, "illocution")
