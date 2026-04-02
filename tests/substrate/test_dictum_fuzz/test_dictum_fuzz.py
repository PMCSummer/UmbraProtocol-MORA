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
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _dictum_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-l04-fuzz-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-l04-fuzz",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    return build_dictum_candidates(lexical, syntax, utterance_surface=surface)


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "!!! ... ??",
        "qzxv",
        "he ???",
        "\"unterminated",
        "if alpha then",
        "###",
        "abcяdef",
        "3 4 5",
    ),
)
def test_fuzz_inputs_do_not_crash_and_fail_honestly(text: str) -> None:
    result = _dictum_result(text)
    assert result is not None
    assert result.no_final_resolution_performed is True
    assert result.partial_known or result.abstain or bool(result.bundle.dictum_candidates)
    assert result.confidence <= 0.95
