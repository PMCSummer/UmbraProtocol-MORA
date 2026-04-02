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
            source_id="metamorphic-user",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    ).unit
    return build_utterance_surface(unit)


def test_question_mark_changes_punctuation_sensitive_surface_profile() -> None:
    dot = _surface("blarf zint.")
    question = _surface("blarf zint?")
    assert dot.surface.tokens[-1].raw_text == "."
    assert question.surface.tokens[-1].raw_text == "?"
    assert dot.surface.segments[0].raw_span.raw_text != question.surface.segments[0].raw_span.raw_text


def test_adding_quotes_creates_quoted_span_and_removing_quotes_removes_it() -> None:
    quoted = _surface('"blarf zint"')
    plain = _surface("blarf zint")
    assert quoted.surface.quotes
    assert not plain.surface.quotes


def test_adding_parentheses_creates_parenthetical_insertion() -> None:
    with_parenthetical = _surface("(вставка) blarf zint")
    without_parenthetical = _surface("вставка blarf zint")
    assert any(
        insertion.insertion_kind.value == "parenthetical"
        for insertion in with_parenthetical.surface.insertions
    )
    assert not any(
        insertion.insertion_kind.value == "parenthetical"
        for insertion in without_parenthetical.surface.insertions
    )


def test_noisy_punctuation_does_not_increase_confidence() -> None:
    normal = _surface("blarf zint?")
    noisy = _surface("blarf zint?!?!?!")
    assert noisy.confidence <= normal.confidence


def test_whitespace_changes_do_not_break_reversible_traceability() -> None:
    tidy = _surface("blarf zint")
    noisy = _surface("  blarf\t zint \r\n")
    assert tidy.surface.reversible_span_map_present is True
    assert noisy.surface.reversible_span_map_present is True
    for token in noisy.surface.tokens:
        assert noisy.surface.raw_text[token.raw_span.start : token.raw_span.end] == token.raw_text


def test_surface_variations_do_not_create_semantic_like_outputs() -> None:
    result = _surface("blarf zint")
    assert not hasattr(result, "meaning")
    assert not hasattr(result, "truth")
    assert not hasattr(result, "intent")
    assert not hasattr(result, "appraisal")
