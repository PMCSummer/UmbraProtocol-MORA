from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from substrate.epistemics.models import (
    AbstentionMarker,
    ClaimPolarity,
    ConfidenceLevel,
    ConflictMarker,
    ContestationMarker,
    EpistemicResult,
    EpistemicStatus,
    EpistemicUnit,
    GroundingContext,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    SupportMarker,
    UnknownMarker,
)
from substrate.epistemics.policy import evaluate_downstream_allowance
from substrate.epistemics.telemetry import build_grounding_telemetry


ATTEMPTED_GROUNDING_PATHS: tuple[str, ...] = (
    "epistemic.source_class",
    "epistemic.modality",
    "epistemic.status",
    "epistemic.confidence",
    "epistemic.support",
    "epistemic.contestation",
    "epistemic.conflict_or_unknown",
    "epistemic.downstream_allowance",
)


def ground_epistemic_input(
    input_material: InputMaterial,
    metadata: SourceMetadata,
    context: GroundingContext | None = None,
) -> EpistemicResult:
    context = context or GroundingContext()
    is_valid_input, input_error = validate_input_shape(input_material)
    is_valid_metadata, metadata_error = validate_source_metadata(metadata)
    source_class = classify_source_class(metadata)
    modality = classify_modality(metadata)
    content = separate_content_from_status(input_material)
    status = _resolve_initial_status(source_class, modality)
    confidence, support, contestation, basis = assign_confidence_support_contestation(
        status=status, metadata=metadata
    )
    conflict_marker, insufficient_reasons = detect_conflict_or_insufficient_basis(
        context=context,
        material_content=content,
        metadata=metadata,
        is_valid_input=is_valid_input,
        is_valid_metadata=is_valid_metadata,
        input_error=input_error,
        metadata_error=metadata_error,
        source_class=source_class,
        modality=modality,
    )
    (
        status,
        confidence,
        support,
        contestation,
        conflict_marker,
        unknown_marker,
        abstention_marker,
        basis,
    ) = emit_unknown_or_conflict_if_needed(
        status=status,
        confidence=confidence,
        support=support,
        contestation=contestation,
        conflict_marker=conflict_marker,
        insufficient_reasons=insufficient_reasons,
        basis=basis,
    )

    unit = EpistemicUnit(
        unit_id=f"epu-{uuid4().hex}",
        material_id=input_material.material_id if is_valid_input else "invalid-material",
        content=content,
        source_id=metadata.source_id or "unknown-source",
        source_class=source_class,
        modality=modality,
        status=status,
        confidence=confidence,
        support=support,
        contestation=contestation,
        conflict=conflict_marker,
        unknown=unknown_marker,
        abstention=abstention_marker,
        claim_key=metadata.claim_key,
        claim_polarity=metadata.claim_polarity,
        classification_basis=basis,
    )
    unit = enforce_epistemic_invariants(unit)
    allowance = evaluate_downstream_allowance(
        unit, require_observation=context.require_observation
    )
    telemetry = build_grounding_telemetry(
        material=input_material if is_valid_input else InputMaterial("invalid-material", ""),
        unit=unit,
        allowance=allowance,
        attempted_paths=ATTEMPTED_GROUNDING_PATHS,
    )
    return return_typed_epistemic_result(unit=unit, allowance=allowance, telemetry=telemetry)


def validate_input_shape(input_material: InputMaterial) -> tuple[bool, str | None]:
    if not isinstance(input_material, InputMaterial):
        return False, "input material must be InputMaterial"
    if not input_material.material_id:
        return False, "input material requires material_id"
    if not input_material.content or not input_material.content.strip():
        return False, "input material requires non-empty content"
    return True, None


def validate_source_metadata(metadata: SourceMetadata) -> tuple[bool, str | None]:
    if not isinstance(metadata, SourceMetadata):
        return False, "metadata must be SourceMetadata"
    if not metadata.source_id:
        return False, "metadata.source_id is required for grounded classification"
    return True, None


def classify_source_class(metadata: SourceMetadata) -> SourceClass:
    return metadata.source_class or SourceClass.UNKNOWN


def classify_modality(metadata: SourceMetadata) -> ModalityClass:
    return metadata.modality or ModalityClass.UNSPECIFIED


def separate_content_from_status(input_material: InputMaterial) -> str:
    if isinstance(input_material, InputMaterial):
        return input_material.content
    return ""


def assign_confidence_support_contestation(
    *,
    status: EpistemicStatus,
    metadata: SourceMetadata,
) -> tuple[ConfidenceLevel, SupportMarker | None, ContestationMarker | None, str]:
    confidence_map = {
        EpistemicStatus.OBSERVATION: ConfidenceLevel.HIGH,
        EpistemicStatus.REPORT: ConfidenceLevel.MEDIUM,
        EpistemicStatus.RECALL: ConfidenceLevel.LOW,
        EpistemicStatus.INFERENCE: ConfidenceLevel.LOW,
        EpistemicStatus.ASSUMPTION: ConfidenceLevel.LOW,
        EpistemicStatus.UNKNOWN: ConfidenceLevel.LOW,
        EpistemicStatus.CONFLICT: ConfidenceLevel.LOW,
    }
    confidence = metadata.confidence_hint or confidence_map[status]
    support = (
        SupportMarker(basis=metadata.support_note, evidence_ref=metadata.source_id)
        if metadata.support_note
        else None
    )
    contestation = (
        ContestationMarker(reason=metadata.contestation_note, contested_by=metadata.source_id)
        if metadata.contestation_note
        else None
    )
    basis = f"classified as {status.value} from source/modality mapping"
    return confidence, support, contestation, basis


def detect_conflict_or_insufficient_basis(
    *,
    context: GroundingContext,
    material_content: str,
    metadata: SourceMetadata,
    is_valid_input: bool,
    is_valid_metadata: bool,
    input_error: str | None,
    metadata_error: str | None,
    source_class: SourceClass,
    modality: ModalityClass,
) -> tuple[ConflictMarker | None, tuple[str, ...]]:
    reasons: list[str] = []
    if not is_valid_input and input_error:
        reasons.append(input_error)
    if not is_valid_metadata and metadata_error:
        reasons.append(metadata_error)
    if source_class == SourceClass.UNKNOWN:
        reasons.append("source class unknown")
    if modality == ModalityClass.UNSPECIFIED:
        reasons.append("modality unspecified")
    potentially_conflicting_units = tuple(
        unit
        for unit in context.existing_units
        if unit.content == material_content
        and unit.claim_polarity != ClaimPolarity.UNSPECIFIED
        and unit.status not in {EpistemicStatus.UNKNOWN, EpistemicStatus.CONFLICT}
    )
    if potentially_conflicting_units and (
        not metadata.claim_key or metadata.claim_polarity == ClaimPolarity.UNSPECIFIED
    ):
        reasons.append("insufficient claim alignment metadata for conflict detection")

    if (
        metadata.claim_key
        and metadata.claim_polarity != ClaimPolarity.UNSPECIFIED
        and context.existing_units
    ):
        conflicting_ids = tuple(
            unit.unit_id
            for unit in context.existing_units
            if unit.claim_key == metadata.claim_key
            and unit.claim_polarity != ClaimPolarity.UNSPECIFIED
            and unit.claim_polarity != metadata.claim_polarity
            and unit.status not in {EpistemicStatus.UNKNOWN, EpistemicStatus.CONFLICT}
        )
        if conflicting_ids:
            return (
                ConflictMarker(
                    conflicting_unit_ids=conflicting_ids,
                    reason="claim polarity conflict across sources",
                ),
                tuple(reasons),
            )
    return None, tuple(reasons)


def emit_unknown_or_conflict_if_needed(
    *,
    status: EpistemicStatus,
    confidence: ConfidenceLevel,
    support: SupportMarker | None,
    contestation: ContestationMarker | None,
    conflict_marker: ConflictMarker | None,
    insufficient_reasons: tuple[str, ...],
    basis: str,
) -> tuple[
    EpistemicStatus,
    ConfidenceLevel,
    SupportMarker | None,
    ContestationMarker | None,
    ConflictMarker | None,
    UnknownMarker | None,
    AbstentionMarker | None,
    str,
]:
    if conflict_marker is not None:
        updated_contestation = contestation or ContestationMarker(
            reason="conflicting source record detected",
            contested_by=None,
        )
        return (
            EpistemicStatus.CONFLICT,
            ConfidenceLevel.LOW,
            support,
            updated_contestation,
            conflict_marker,
            None,
            AbstentionMarker(reason="conflict requires abstention"),
            f"{basis}; conflict detected",
        )

    if insufficient_reasons:
        reason = "; ".join(insufficient_reasons)
        return (
            EpistemicStatus.UNKNOWN,
            ConfidenceLevel.LOW,
            None,
            contestation,
            None,
            UnknownMarker(reason=reason),
            AbstentionMarker(reason="insufficient grounding basis"),
            f"{basis}; downgraded to unknown due to insufficient basis",
        )

    return status, confidence, support, contestation, None, None, None, basis


def enforce_epistemic_invariants(unit: EpistemicUnit) -> EpistemicUnit:
    if (
        unit.status == EpistemicStatus.OBSERVATION
        and unit.source_class != SourceClass.SENSOR
    ):
        return _downgrade_to_unknown(
            unit,
            "observation status requires sensor source class",
        )
    if (
        unit.status == EpistemicStatus.OBSERVATION
        and unit.modality != ModalityClass.SENSOR_STREAM
    ):
        return _downgrade_to_unknown(
            unit,
            "observation status requires sensor modality",
        )
    if unit.status == EpistemicStatus.REPORT and unit.source_class == SourceClass.SENSOR:
        return _downgrade_to_unknown(
            unit,
            "sensor source cannot be treated as report",
        )
    return unit


def return_typed_epistemic_result(
    *, unit: EpistemicUnit, allowance, telemetry
) -> EpistemicResult:
    return EpistemicResult(unit=unit, allowance=allowance, telemetry=telemetry)


def _resolve_initial_status(
    source_class: SourceClass, modality: ModalityClass
) -> EpistemicStatus:
    if source_class == SourceClass.SENSOR and modality == ModalityClass.SENSOR_STREAM:
        return EpistemicStatus.OBSERVATION
    if source_class == SourceClass.REPORTER and modality == ModalityClass.USER_TEXT:
        return EpistemicStatus.REPORT
    if source_class == SourceClass.RECALL_AGENT and modality == ModalityClass.MEMORY_TRACE:
        return EpistemicStatus.RECALL
    if source_class == SourceClass.INFERENCE_ENGINE and modality == ModalityClass.DERIVATION_NOTE:
        return EpistemicStatus.INFERENCE
    if source_class == SourceClass.ASSUMPTIVE and modality == ModalityClass.HYPOTHETICAL_NOTE:
        return EpistemicStatus.ASSUMPTION
    return EpistemicStatus.UNKNOWN


def _downgrade_to_unknown(unit: EpistemicUnit, reason: str) -> EpistemicUnit:
    return replace(
        unit,
        status=EpistemicStatus.UNKNOWN,
        confidence=ConfidenceLevel.LOW,
        support=None,
        unknown=UnknownMarker(reason=reason),
        abstention=AbstentionMarker(reason="epistemic invariant violation"),
        classification_basis=f"{unit.classification_basis}; downgraded by invariant: {reason}",
    )
