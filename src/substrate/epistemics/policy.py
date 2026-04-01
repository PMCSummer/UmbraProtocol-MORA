from __future__ import annotations

from substrate.epistemics.models import (
    ConfidenceLevel,
    DownstreamAllowance,
    EpistemicStatus,
    EpistemicUnit,
    ModalityClass,
    SourceClass,
)


def evaluate_downstream_allowance(
    unit: EpistemicUnit, *, require_observation: bool
) -> DownstreamAllowance:
    if not isinstance(unit, EpistemicUnit):
        raise TypeError("downstream allowance requires EpistemicUnit, not raw content")

    restrictions: list[str] = []
    can_treat_as_observation = False
    should_abstain = False
    claim_strength = "weak"
    reason = "epistemic unit requires guarded downstream use"

    if unit.status in {EpistemicStatus.UNKNOWN, EpistemicStatus.CONFLICT}:
        should_abstain = True
        restrictions.append("unknown_or_conflict")
        reason = "epistemic status is unknown or conflicting"

    if unit.abstention is not None:
        should_abstain = True
        restrictions.append("abstention_marker")
        reason = "explicit abstention marker is present"

    if unit.confidence == ConfidenceLevel.LOW:
        restrictions.append("low_confidence")
        claim_strength = "weak"

    if require_observation:
        if unit.status != EpistemicStatus.OBSERVATION:
            should_abstain = True
            restrictions.append("observation_required")
            reason = "downstream requires grounded observation"
        elif unit.source_class != SourceClass.SENSOR:
            should_abstain = True
            restrictions.append("non_sensor_source")
            reason = "observation usage requires sensor source class"
        elif unit.modality != ModalityClass.SENSOR_STREAM:
            should_abstain = True
            restrictions.append("non_sensor_modality")
            reason = "observation usage requires sensor modality"
        elif unit.confidence == ConfidenceLevel.LOW:
            should_abstain = True
            restrictions.append("observation_confidence_too_low")
            reason = "observation usage requires confidence above low"
        else:
            can_treat_as_observation = True
            claim_strength = "grounded_observation"
            reason = "grounded observation allowed"
    else:
        if unit.status == EpistemicStatus.OBSERVATION and unit.confidence != ConfidenceLevel.LOW:
            can_treat_as_observation = True
            claim_strength = "grounded_observation"
            reason = "observation allowed for non-strict downstream use"
        elif unit.status == EpistemicStatus.REPORT:
            restrictions.append("reported_not_observed")
            claim_strength = "reported_claim"
            reason = "report cannot be promoted to observation"
        elif unit.status == EpistemicStatus.RECALL:
            restrictions.append("memory_recall")
            claim_strength = "recall_claim"
            reason = "recall remains memory-origin claim"
        elif unit.status == EpistemicStatus.INFERENCE:
            restrictions.append("derived_inference")
            claim_strength = "inferred_claim"
            reason = "inference remains derived claim"
        elif unit.status == EpistemicStatus.ASSUMPTION:
            restrictions.append("assumptive_claim")
            claim_strength = "assumption"
            reason = "assumption requires additional support"

    return DownstreamAllowance(
        can_treat_as_observation=can_treat_as_observation,
        should_abstain=should_abstain,
        claim_strength=claim_strength,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
    )
