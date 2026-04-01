from substrate.epistemics import (
    ClaimPolarity,
    EpistemicStatus,
    GroundingContext,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)


def test_conflicting_sources_emit_conflict_and_contestation() -> None:
    material = InputMaterial(material_id="m-conflict-1", content="valve=closed")
    first = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-1",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key="valve-state",
            claim_polarity=ClaimPolarity.AFFIRM,
        ),
    )
    second = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-2",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key="valve-state",
            claim_polarity=ClaimPolarity.DENY,
        ),
        GroundingContext(existing_units=(first.unit,), require_observation=True),
    )

    assert first.unit.status == EpistemicStatus.OBSERVATION
    assert second.unit.status == EpistemicStatus.CONFLICT
    assert second.unit.conflict is not None
    assert first.unit.unit_id in second.unit.conflict.conflicting_unit_ids
    assert second.unit.contestation is not None
    assert second.allowance.should_abstain is True
    assert second.allowance.claim_strength != "grounded_observation"
    assert "unknown_or_conflict" in second.allowance.restrictions


def test_insufficient_alignment_metadata_does_not_force_conflict_claim() -> None:
    material = InputMaterial(material_id="m-conflict-bound", content="pump=on")
    existing = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-bound-a",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key="pump-state",
            claim_polarity=ClaimPolarity.AFFIRM,
        ),
    )
    incoming_without_alignment = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-bound-b",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key=None,
            claim_polarity=ClaimPolarity.UNSPECIFIED,
        ),
        GroundingContext(existing_units=(existing.unit,), require_observation=True),
    )

    assert incoming_without_alignment.unit.status == EpistemicStatus.UNKNOWN
    assert incoming_without_alignment.unit.conflict is None
    assert incoming_without_alignment.unit.unknown is not None
    assert "insufficient claim alignment metadata" in incoming_without_alignment.unit.unknown.reason
    assert incoming_without_alignment.allowance.should_abstain is True
