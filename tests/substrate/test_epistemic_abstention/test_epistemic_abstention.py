from substrate.epistemics import (
    EpistemicStatus,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)


def test_missing_or_invalid_metadata_yields_unknown_and_abstain() -> None:
    material = InputMaterial(material_id="m-unknown-1", content="pressure=high")
    result = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id=None,
            source_class=SourceClass.UNKNOWN,
            modality=ModalityClass.UNSPECIFIED,
        ),
    )

    assert result.unit.status == EpistemicStatus.UNKNOWN
    assert result.unit.unknown is not None
    assert result.unit.abstention is not None
    assert result.allowance.should_abstain is True


def test_empty_material_content_forces_honest_unknown() -> None:
    material = InputMaterial(material_id="m-empty", content=" ")
    result = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-empty",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
        ),
    )

    assert result.unit.status == EpistemicStatus.UNKNOWN
    assert result.unit.unknown is not None
    assert "non-empty content" in result.unit.unknown.reason
    assert result.allowance.should_abstain is True
