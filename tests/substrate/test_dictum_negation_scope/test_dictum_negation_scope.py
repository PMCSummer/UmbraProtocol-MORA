from substrate.dictum_candidates import DictumPolarity, build_dictum_candidates
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


def test_negation_marker_survives_and_scope_ambiguity_remains_visible() -> None:
    result = _dictum_result("we do not track alpha beta", "m-l04-neg-amb")
    assert result.bundle.dictum_candidates
    assert any(candidate.negation_markers for candidate in result.bundle.dictum_candidates)
    assert any(
        marker.marker_kind == "negation_scope_ambiguous"
        for candidate in result.bundle.dictum_candidates
        for marker in candidate.scope_markers
    )
    assert any(candidate.polarity == DictumPolarity.NEGATED for candidate in result.bundle.dictum_candidates)


def test_non_negated_case_does_not_invent_negation() -> None:
    result = _dictum_result("we track alpha", "m-l04-neg-plain")
    assert result.bundle.dictum_candidates
    assert any(candidate.polarity == DictumPolarity.AFFIRMATIVE for candidate in result.bundle.dictum_candidates)
