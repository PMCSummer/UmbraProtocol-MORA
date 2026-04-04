from __future__ import annotations

from substrate.semantic_acquisition.models import (
    AcquisitionStatus,
    AcquisitionUsabilityClass,
    SemanticAcquisitionBundle,
    SemanticAcquisitionGateDecision,
    SemanticAcquisitionResult,
)


def evaluate_semantic_acquisition_downstream_gate(
    semantic_acquisition_result_or_bundle: object,
) -> SemanticAcquisitionGateDecision:
    if isinstance(semantic_acquisition_result_or_bundle, SemanticAcquisitionResult):
        bundle = semantic_acquisition_result_or_bundle.bundle
    elif isinstance(semantic_acquisition_result_or_bundle, SemanticAcquisitionBundle):
        bundle = semantic_acquisition_result_or_bundle
    else:
        raise TypeError(
            "semantic acquisition gate requires typed SemanticAcquisitionResult/SemanticAcquisitionBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_final_semantic_closure:
        restrictions.append("no_final_semantic_closure")
    restrictions.append("accepted_provisional_not_final_meaning")
    restrictions.append("accepted_provisional_not_commitment")
    restrictions.append("acquisition_status_must_be_read")
    restrictions.append("restrictions_must_be_read")

    has_stable = False
    has_weak = False
    has_competing = False
    has_blocked = False
    has_context_only = False
    has_discarded = False
    has_revision_hooks = False
    has_support_conflict_trace = False

    for record in bundle.acquisition_records:
        if record.confidence >= 0.2 and record.acquisition_status is not AcquisitionStatus.DISCARDED_AS_INCOHERENT:
            accepted_ids.append(record.acquisition_id)
        else:
            rejected_ids.append(record.acquisition_id)

        status = record.acquisition_status
        if status is AcquisitionStatus.STABLE_PROVISIONAL:
            has_stable = True
        elif status is AcquisitionStatus.WEAK_PROVISIONAL:
            has_weak = True
        elif status is AcquisitionStatus.COMPETING_PROVISIONAL:
            has_competing = True
        elif status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION:
            has_blocked = True
        elif status is AcquisitionStatus.CONTEXT_ONLY:
            has_context_only = True
        elif status is AcquisitionStatus.DISCARDED_AS_INCOHERENT:
            has_discarded = True

        if record.revision_conditions:
            has_revision_hooks = True
        if (
            record.support_conflict_profile.support_reasons
            or record.support_conflict_profile.conflict_reasons
            or record.support_conflict_profile.unresolved_slots
        ):
            has_support_conflict_trace = True

    if has_competing:
        restrictions.append("competing_meanings_preserved")
    if has_revision_hooks:
        restrictions.append("revision_hooks_must_be_read")
    if has_blocked:
        restrictions.append("closure_blocked_pending_clarification")
    if has_context_only:
        restrictions.append("context_only_output")
    if has_support_conflict_trace:
        restrictions.append("support_conflict_trace_required")

    if has_blocked or has_competing or has_context_only or has_weak or has_discarded:
        restrictions.append("memory_uptake_blocked")

    accepted = bool(accepted_ids)
    if not accepted:
        restrictions.append("no_usable_provisional_acquisitions")
        usability_class = AcquisitionUsabilityClass.BLOCKED
        reason = "semantic acquisition produced no provisional records above confidence floor"
    else:
        usability_class = AcquisitionUsabilityClass.USABLE_BOUNDED
        reason = "typed provisional acquisition emitted; bounded status/restrictions remain mandatory"

    degraded = (
        bundle.low_coverage_mode
        or bool(bundle.ambiguity_reasons)
        or has_weak
        or has_competing
        or has_blocked
        or has_context_only
        or has_discarded
    )
    if degraded:
        restrictions.append("downstream_authority_degraded")
        if accepted:
            restrictions.append("accepted_degraded_requires_restrictions_read")
    if degraded and accepted:
        usability_class = AcquisitionUsabilityClass.DEGRADED_BOUNDED

    return SemanticAcquisitionGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_acquisition_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_acquisition_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_perspective_chain_ref,
    )
