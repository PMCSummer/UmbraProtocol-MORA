from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import InsertionKind, build_utterance_surface


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


def test_normalization_log_has_provenance_and_reversible_records() -> None:
    result = build_utterance_surface(_epistemic_unit("  blarf   zint  "))

    assert result.surface.normalization_log
    for record in result.surface.normalization_log:
        assert record.op_name
        assert record.input_span_ref
        assert record.provenance
        assert isinstance(record.reversible, bool)


def test_parenthetical_and_code_like_spans_are_preserved() -> None:
    result = build_utterance_surface(_epistemic_unit("(вставка) `code-like` blarf zint"))

    kinds = {insertion.insertion_kind for insertion in result.surface.insertions}
    assert InsertionKind.PARENTHETICAL in kinds
    assert InsertionKind.CODE in kinds
