from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface


def _epistemic_unit(text: str):
    result = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return result.unit


def test_surface_build_produces_reversible_spans_tokens_and_segments() -> None:
    result = build_utterance_surface(_epistemic_unit("blarf zint."))

    assert result.abstain is False
    assert result.surface.reversible_span_map_present is True
    assert result.surface.tokens
    assert result.surface.segments
    assert result.surface.normalization_log

    raw_text = result.surface.raw_text
    token_ids = {token.token_id for token in result.surface.tokens}
    for token in result.surface.tokens:
        assert raw_text[token.raw_span.start : token.raw_span.end] == token.raw_text
    for segment in result.surface.segments:
        assert all(token_id in token_ids for token_id in segment.token_ids)
        assert segment.raw_span.raw_text == raw_text[segment.raw_span.start : segment.raw_span.end]


def test_punctuation_sensitive_segmentation_contrast() -> None:
    dot_result = build_utterance_surface(_epistemic_unit("blarf zint."))
    q_result = build_utterance_surface(_epistemic_unit("blarf zint?"))

    dot_last = dot_result.surface.tokens[-1].raw_text
    q_last = q_result.surface.tokens[-1].raw_text
    assert dot_last == "."
    assert q_last == "?"
    assert dot_result.surface.segments[0].raw_span.raw_text.endswith(".")
    assert q_result.surface.segments[0].raw_span.raw_text.endswith("?")


def test_quoted_span_is_preserved_as_first_class_surface_object() -> None:
    result = build_utterance_surface(_epistemic_unit('"blarf zint", — сказал user'))

    assert result.surface.quotes
    quoted = result.surface.quotes[0].raw_span.raw_text
    assert quoted.startswith('"')
    assert quoted.endswith('"')
