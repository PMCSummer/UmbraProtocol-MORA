from __future__ import annotations

from substrate.concept_framing.models import (
    ConceptFramingBundle,
    ConceptFramingGateDecision,
    ConceptFramingResult,
    FramingStatus,
    FramingUsabilityClass,
)


def evaluate_concept_framing_downstream_gate(
    concept_framing_result_or_bundle: object,
) -> ConceptFramingGateDecision:
    if isinstance(concept_framing_result_or_bundle, ConceptFramingResult):
        bundle = concept_framing_result_or_bundle.bundle
    elif isinstance(concept_framing_result_or_bundle, ConceptFramingBundle):
        bundle = concept_framing_result_or_bundle
    else:
        raise TypeError("concept framing gate requires typed ConceptFramingResult/ConceptFramingBundle")

    restrictions: list[str] = [
        "no_final_semantic_closure",
        "accepted_provisional_not_closure",
        "frame_status_must_be_read",
        "framing_basis_must_be_read",
        "downstream_cautions_must_be_read",
        "vulnerability_profile_must_be_read",
    ]
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    has_competing = False
    has_underframed = False
    has_blocked = False
    has_context_only = False
    has_discarded = False
    has_high_impact = False
    has_reframing_conditions = False

    for record in bundle.framing_records:
        if record.confidence >= 0.2 and record.framing_status is not FramingStatus.DISCARDED_OVERREACH:
            accepted_ids.append(record.framing_id)
        else:
            rejected_ids.append(record.framing_id)

        if record.framing_status is FramingStatus.COMPETING_FRAMES:
            has_competing = True
        elif record.framing_status is FramingStatus.UNDERFRAMED_MEANING:
            has_underframed = True
        elif record.framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME:
            has_blocked = True
        elif record.framing_status is FramingStatus.CONTEXT_ONLY_FRAME_HINT:
            has_context_only = True
        elif record.framing_status is FramingStatus.DISCARDED_OVERREACH:
            has_discarded = True

        if record.vulnerability_profile.high_impact:
            has_high_impact = True
        if record.reframing_conditions:
            has_reframing_conditions = True

    if has_competing:
        restrictions.append("competing_frames_preserved")
    if has_underframed:
        restrictions.append("underframed_meaning")
    if has_blocked:
        restrictions.append("blocked_high_impact_frame")
    if has_context_only:
        restrictions.append("context_only_frame_hint")
    if has_high_impact:
        restrictions.append("high_impact_frame_guard_required")
    if has_reframing_conditions:
        restrictions.append("reframing_conditions_must_be_read")
    if has_competing or has_underframed or has_blocked or has_context_only or has_discarded:
        restrictions.append("memory_uptake_blocked")

    if bundle.l06_update_proposal_absent:
        restrictions.append("l06_update_proposal_absent")
        restrictions.append("framing_requires_discourse_update_read")
    if bundle.repair_trigger_basis_incomplete:
        restrictions.append("repair_trigger_basis_incomplete")

    accepted = bool(accepted_ids)
    if not accepted:
        usability_class = FramingUsabilityClass.BLOCKED
        reason = "concept framing produced no records above confidence floor"
        restrictions.append("no_usable_framing_records")
    else:
        usability_class = FramingUsabilityClass.USABLE_BOUNDED
        reason = "typed concept framing emitted with bounded vulnerability restrictions"

    degraded = (
        bundle.low_coverage_mode
        or bool(bundle.ambiguity_reasons)
        or bundle.l06_update_proposal_absent
        or bundle.repair_trigger_basis_incomplete
        or has_competing
        or has_underframed
        or has_blocked
        or has_context_only
        or has_discarded
        or has_high_impact
    )
    if degraded:
        restrictions.append("downstream_authority_degraded")
        if accepted:
            restrictions.append("accepted_degraded_requires_restrictions_read")
    if degraded and accepted:
        usability_class = FramingUsabilityClass.DEGRADED_BOUNDED

    return ConceptFramingGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_framing_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_framing_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_acquisition_ref,
    )
