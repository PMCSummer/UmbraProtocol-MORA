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
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _l03_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-l03-fuzz-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-l03-fuzz",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    return build_lexical_grounding_hypotheses(syntax_result, utterance_surface=surface_result)


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "!!! ... ??",
        "\"unterminated quote",
        "qzxv",
        "qzxv ??? he",
        "blarf|||zint",
        "abcяdef",
        "h3",
        "он??",
        "яяя",
        "### not-a-word ###",
    ),
)
def test_fuzz_inputs_do_not_crash_and_keep_honest_uncertainty(text: str) -> None:
    result = _l03_result(text)

    assert result is not None
    assert result.no_final_resolution_performed is True
    assert result.bundle.no_final_resolution_performed is True
    assert result.confidence <= 0.95
    assert result.partial_known or result.abstain or bool(result.bundle.lexeme_candidates)


def test_unknown_heavy_noise_exposes_unknown_or_unresolved_paths() -> None:
    result = _l03_result("qzxv nrmpt he ???")
    has_unresolved = any(hypothesis.unresolved for hypothesis in result.bundle.reference_hypotheses)

    assert result.bundle.unknown_states or has_unresolved or result.bundle.conflicts
