from __future__ import annotations

from substrate.stream_diversification.models import (
    C03RestrictionCode,
    DiversificationDecisionStatus,
    StreamDiversificationGateDecision,
    StreamDiversificationResult,
    StreamDiversificationState,
    StreamDiversificationUsabilityClass,
)


def evaluate_stream_diversification_downstream_gate(
    diversification_state_or_result: object,
) -> StreamDiversificationGateDecision:
    if isinstance(diversification_state_or_result, StreamDiversificationResult):
        state = diversification_state_or_result.state
    elif isinstance(diversification_state_or_result, StreamDiversificationState):
        state = diversification_state_or_result
    else:
        raise TypeError(
            "evaluate_stream_diversification_downstream_gate requires StreamDiversificationState/StreamDiversificationResult"
        )

    restrictions: list[C03RestrictionCode] = [
        C03RestrictionCode.DIVERSIFICATION_STATE_MUST_BE_READ,
        C03RestrictionCode.STAGNATION_SIGNATURES_MUST_BE_READ,
        C03RestrictionCode.REDUNDANCY_SCORES_MUST_BE_READ,
        C03RestrictionCode.DIVERSIFICATION_PRESSURE_MUST_BE_READ,
        C03RestrictionCode.REPEAT_JUSTIFICATION_MUST_BE_READ,
        C03RestrictionCode.PROTECTED_RECURRENCE_MUST_BE_READ,
        C03RestrictionCode.ALTERNATIVE_CLASSES_MUST_BE_READ,
        C03RestrictionCode.ALTERNATIVE_ACTIONABILITY_MUST_BE_READ,
        C03RestrictionCode.PROGRESS_EVIDENCE_CLASS_MUST_BE_READ,
        C03RestrictionCode.PROGRESS_EVIDENCE_AXES_MUST_BE_READ,
        C03RestrictionCode.STRUCTURAL_STAGNATION_NOT_TEXT_ANTIREPEAT,
        C03RestrictionCode.RANDOMNESS_NOT_DIVERSIFICATION,
    ]
    accepted = bool(state.path_assessments)
    usability = StreamDiversificationUsabilityClass.USABLE_BOUNDED
    reason = "typed diversification state available for bounded structural anti-rumination checks"

    has_signatures = bool(state.stagnation_signatures)
    has_repeat_gating = bool(state.repeat_requires_justification_for)
    has_protected = bool(state.protected_recurrence_classes)
    has_no_safe = state.no_safe_diversification
    has_edge_band = any(
        assessment.edge_band_applied for assessment in state.path_assessments
    )
    has_survival_filtered = any(
        assessment.survival_filtered_alternatives for assessment in state.path_assessments
    )

    if has_signatures:
        restrictions.append(C03RestrictionCode.STAGNATION_SIGNATURE_PRESENT)
    if has_repeat_gating and has_protected:
        restrictions.append(C03RestrictionCode.REPEAT_DETECTED_BUT_JUSTIFIED_MUST_BE_READ)
    if state.low_confidence_stagnation:
        restrictions.append(C03RestrictionCode.LOW_CONFIDENCE_STAGNATION_MUST_BE_READ)
    if has_no_safe:
        restrictions.append(C03RestrictionCode.NO_SAFE_DIVERSIFICATION_CLAIM_PRESENT)
        restrictions.append(C03RestrictionCode.NO_SAFE_DIVERSIFICATION_MUST_BE_READ)
    if has_edge_band:
        restrictions.append(C03RestrictionCode.EDGE_BAND_APPLIED_MUST_BE_READ)
    if has_survival_filtered:
        restrictions.append(
            C03RestrictionCode.SURVIVAL_FILTERED_ALTERNATIVES_MUST_BE_READ
        )
    if state.diversification_conflict_with_survival:
        restrictions.append(
            C03RestrictionCode.DIVERSIFICATION_CONFLICT_WITH_SURVIVAL_MUST_BE_READ
        )

    degraded = (
        state.decision_status == DiversificationDecisionStatus.AMBIGUOUS_STAGNATION
        or state.low_confidence_stagnation
        or state.diversification_conflict_with_survival
        or (has_no_safe and has_repeat_gating)
        or has_edge_band
    )
    blocked = bool(
        state.decision_status == DiversificationDecisionStatus.NO_SAFE_DIVERSIFICATION
        and has_no_safe
        and has_repeat_gating
        and not has_protected
    )

    if blocked:
        accepted = False
        usability = StreamDiversificationUsabilityClass.BLOCKED
        restrictions.append(C03RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "no safe diversification path available for repeating route without protected recurrence"
    elif degraded:
        usability = StreamDiversificationUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(C03RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "diversification pressure is bounded/degraded and requires cautious downstream interpretation"

    if not state.path_assessments:
        accepted = False
        usability = StreamDiversificationUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(C03RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "no schedule-aware path assessments produced by c03"

    return StreamDiversificationGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.diversification_id}@{state.source_stream_sequence_index}",
    )
