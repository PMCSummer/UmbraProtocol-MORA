import pytest

from substrate.epistemics import (
    ClaimPolarity,
    ConfidenceLevel,
    EpistemicStatus,
    GroundingContext,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    evaluate_downstream_allowance,
    ground_epistemic_input,
)


def test_report_is_not_promoted_to_observation_in_downstream_gate() -> None:
    result = ground_epistemic_input(
        InputMaterial(material_id="m-report-1", content="it is raining"),
        SourceMetadata(
            source_id="user-3",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
        ),
        GroundingContext(require_observation=True),
    )

    assert result.unit.status == EpistemicStatus.REPORT
    assert result.allowance.can_treat_as_observation is False
    assert result.allowance.should_abstain is True
    assert "observation_required" in result.allowance.restrictions


def test_low_confidence_materially_changes_downstream_allowance() -> None:
    result = ground_epistemic_input(
        InputMaterial(material_id="m-lowconf-1", content="temp=40"),
        SourceMetadata(
            source_id="sensor-low",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            confidence_hint=ConfidenceLevel.LOW,
        ),
        GroundingContext(require_observation=True),
    )

    assert result.unit.status == EpistemicStatus.OBSERVATION
    assert result.allowance.can_treat_as_observation is False
    assert result.allowance.should_abstain is True
    assert "observation_confidence_too_low" in result.allowance.restrictions


def test_downstream_must_use_epistemic_unit_not_raw_content() -> None:
    with pytest.raises(TypeError):
        evaluate_downstream_allowance("raw content", require_observation=True)


def test_critical_downstream_path_requires_epistemic_unit_and_policy_gate() -> None:
    grounded = ground_epistemic_input(
        InputMaterial(material_id="m-critical-path", content="speed=10"),
        SourceMetadata(
            source_id="sensor-critical",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
        ),
    )
    allowance = evaluate_downstream_allowance(
        grounded.unit, require_observation=True
    )
    assert allowance.can_treat_as_observation is True

    with pytest.raises(TypeError):
        evaluate_downstream_allowance(grounded.unit.content, require_observation=True)


def test_boundary_non_overreach_no_truth_or_dialogue_claims() -> None:
    content = "The sky is green."
    result = ground_epistemic_input(
        InputMaterial(material_id="m-boundary-1", content=content),
        SourceMetadata(
            source_id="user-boundary",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
        ),
    )

    assert result.unit.content == content
    assert result.unit.status == EpistemicStatus.REPORT
    assert not hasattr(result.unit, "world_truth")
    assert not hasattr(result.unit, "intent")
    assert not hasattr(result.unit, "dialogue_policy")


def test_ablation_lite_ignoring_metadata_breaks_claim_discipline() -> None:
    content = "door=closed"
    with_metadata = ground_epistemic_input(
        InputMaterial(material_id="m-ablate-1", content=content),
        SourceMetadata(
            source_id="sensor-ablate",
            source_class=SourceClass.SENSOR,
            modality=ModalityClass.SENSOR_STREAM,
            claim_key="door-state",
            claim_polarity=ClaimPolarity.AFFIRM,
        ),
        GroundingContext(require_observation=True),
    )
    without_metadata = ground_epistemic_input(
        InputMaterial(material_id="m-ablate-1", content=content),
        SourceMetadata(
            source_id=None,
            source_class=SourceClass.UNKNOWN,
            modality=ModalityClass.UNSPECIFIED,
            claim_key="door-state",
            claim_polarity=ClaimPolarity.AFFIRM,
        ),
        GroundingContext(require_observation=True),
    )

    assert with_metadata.unit.status == EpistemicStatus.OBSERVATION
    assert with_metadata.allowance.can_treat_as_observation is True
    assert without_metadata.unit.status == EpistemicStatus.UNKNOWN
    assert without_metadata.allowance.should_abstain is True


def test_falsifier_demonstration_policy_surface_is_load_bearing() -> None:
    report = ground_epistemic_input(
        InputMaterial(material_id="m-policy-falsifier", content="reactor=stable"),
        SourceMetadata(
            source_id="user-falsifier",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
        ),
        GroundingContext(require_observation=True),
    )

    naive_accepts_by_content = bool(report.unit.content.strip())
    assert naive_accepts_by_content is True
    assert report.allowance.should_abstain is True
    assert report.allowance.can_treat_as_observation is False
