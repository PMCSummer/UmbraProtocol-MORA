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


def _surface(text: str):
    unit = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="regression-user",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    ).unit
    return build_utterance_surface(unit)


@pytest.mark.parametrize(
    ("text", "expect_quote", "expect_parenthetical", "expect_code", "expect_ambiguity"),
    [
        ('"blarf zint", — сказал user', True, False, False, True),
        ('«blarf "zint"»', True, False, False, True),
        ("(вставка) blarf zint", False, True, False, True),
        ("ну э-э я... не знаю", False, False, False, True),
        ("`code-like` or ```broken", False, False, True, True),
        ("blarf... zint", False, False, False, True),
        ("blarf zint?!", False, False, False, True),
        ("blarf   zint??", False, False, False, True),
        ("кириллица mixed Latin blarf", False, False, False, True),
        ("asr uh uh blarf -- zint", False, False, False, True),
    ],
)
def test_evil_surface_regression_corpus(
    text: str,
    expect_quote: bool,
    expect_parenthetical: bool,
    expect_code: bool,
    expect_ambiguity: bool,
) -> None:
    result = _surface(text)
    assert result.surface.reversible_span_map_present is True
    assert result.surface.tokens
    assert result.surface.normalization_log

    has_quote = bool(result.surface.quotes)
    has_parenthetical = any(
        insertion.insertion_kind.value == "parenthetical"
        for insertion in result.surface.insertions
    )
    has_code = any(
        insertion.insertion_kind.value == "code" for insertion in result.surface.insertions
    )
    has_ambiguity = bool(result.surface.ambiguities)

    assert has_quote is expect_quote
    assert has_parenthetical is expect_parenthetical
    assert has_code is expect_code
    assert has_ambiguity is expect_ambiguity
