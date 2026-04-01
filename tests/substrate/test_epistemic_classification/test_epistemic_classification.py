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


def test_classification_harness_distinguishes_epistemic_statuses() -> None:
    material = InputMaterial(material_id="m-classify-1", content="signal:alpha")

    observation = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-1",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
        ),
    )
    report = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="user-1",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
        ),
    )
    recall = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="memory-1",
            source_class=SourceClass.RECALL_AGENT,
            modality=ModalityClass.MEMORY_TRACE,
        ),
    )
    inference = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="solver-1",
            source_class=SourceClass.INFERENCE_ENGINE,
            modality=ModalityClass.DERIVATION_NOTE,
        ),
    )
    assumption = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="hypothesis-1",
            source_class=SourceClass.ASSUMPTIVE,
            modality=ModalityClass.HYPOTHETICAL_NOTE,
        ),
    )
    unknown = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="unknown-1",
            source_class=SourceClass.UNKNOWN,
            modality=ModalityClass.UNSPECIFIED,
        ),
    )

    assert observation.unit.status == EpistemicStatus.OBSERVATION
    assert report.unit.status == EpistemicStatus.REPORT
    assert recall.unit.status == EpistemicStatus.RECALL
    assert inference.unit.status == EpistemicStatus.INFERENCE
    assert assumption.unit.status == EpistemicStatus.ASSUMPTION
    assert unknown.unit.status == EpistemicStatus.UNKNOWN


def test_contrast_same_content_different_source_modality_changes_output() -> None:
    material = InputMaterial(material_id="m-contrast-1", content="door=open")
    observation = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-2",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
        ),
    )
    report = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="user-2",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
        ),
    )

    assert observation.unit.status == EpistemicStatus.OBSERVATION
    assert report.unit.status == EpistemicStatus.REPORT
    assert observation.allowance.claim_strength != report.allowance.claim_strength


def test_classification_harness_includes_conflict_vs_single_source() -> None:
    material = InputMaterial(material_id="m-conflict-classify", content="switch:on")
    first = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-a",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key="switch-state",
            claim_polarity=ClaimPolarity.AFFIRM,
        ),
    )
    second = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-b",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key="switch-state",
            claim_polarity=ClaimPolarity.DENY,
        ),
        GroundingContext(existing_units=(first.unit,)),
    )

    assert first.unit.status == EpistemicStatus.OBSERVATION
    assert second.unit.status == EpistemicStatus.CONFLICT


def test_grounding_telemetry_is_load_bearing_for_reconstruction() -> None:
    material = InputMaterial(material_id="m-telemetry-1", content="temp=27")
    result = ground_epistemic_input(
        material,
        SourceMetadata(
            source_id="sensor-telemetry",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            support_note="calibrated probe",
        ),
    )
    telemetry = result.telemetry

    assert telemetry.material_id == "m-telemetry-1"
    assert telemetry.material_content == "temp=27"
    assert telemetry.source_class == SourceClass.SENSOR
    assert telemetry.modality == ModalityClass.SENSOR_STREAM
    assert telemetry.status == EpistemicStatus.OBSERVATION
    assert telemetry.attempted_paths
    assert telemetry.support_basis == "calibrated probe"
