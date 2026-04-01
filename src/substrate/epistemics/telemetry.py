from __future__ import annotations

from substrate.epistemics.models import (
    DownstreamAllowance,
    EpistemicUnit,
    GroundingTelemetry,
    InputMaterial,
)


def build_grounding_telemetry(
    *,
    material: InputMaterial,
    unit: EpistemicUnit,
    allowance: DownstreamAllowance,
    attempted_paths: tuple[str, ...],
) -> GroundingTelemetry:
    return GroundingTelemetry(
        material_id=material.material_id,
        material_content=material.content,
        source_class=unit.source_class,
        modality=unit.modality,
        status=unit.status,
        confidence=unit.confidence,
        attempted_paths=attempted_paths,
        support_basis=unit.support.basis if unit.support else None,
        contestation_reason=unit.contestation.reason if unit.contestation else None,
        conflict_reason=unit.conflict.reason if unit.conflict else None,
        unknown_reason=unit.unknown.reason if unit.unknown else None,
        abstain_reason=unit.abstention.reason if unit.abstention else None,
        classification_basis=unit.classification_basis,
        downstream_claim_strength=allowance.claim_strength,
        downstream_restrictions=allowance.restrictions,
    )
