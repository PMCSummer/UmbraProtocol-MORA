from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import AmbiguityKind, InsertionKind, build_utterance_surface


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


def test_ellipsis_creates_ambiguity_and_alternative_segmentation() -> None:
    result = build_utterance_surface(_epistemic_unit("blarf... zint"))

    assert result.partial_known is True
    assert result.surface.ambiguities
    assert any(
        ambiguity.ambiguity_kind == AmbiguityKind.BOUNDARY_UNCERTAIN_ELLIPSIS
        for ambiguity in result.surface.ambiguities
    )
    assert result.surface.alternative_segmentations


def test_repair_fragment_is_preserved_not_flattened() -> None:
    result = build_utterance_surface(_epistemic_unit("ну э-э я... не знаю"))

    assert any(
        insertion.insertion_kind == InsertionKind.REPAIR_FRAGMENT
        for insertion in result.surface.insertions
    )
    assert any("э-э" in token.raw_text for token in result.surface.tokens)


def test_noisy_punctuation_cluster_marks_boundary_ambiguity() -> None:
    result = build_utterance_surface(_epistemic_unit("blarf zint?!"))

    assert any(
        ambiguity.ambiguity_kind == AmbiguityKind.BOUNDARY_UNCERTAIN_PUNCT_CLUSTER
        for ambiguity in result.surface.ambiguities
    )
