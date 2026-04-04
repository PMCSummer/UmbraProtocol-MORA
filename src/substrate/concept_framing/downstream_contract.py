from __future__ import annotations

from dataclasses import dataclass

from substrate.concept_framing.models import (
    ConceptFramingBundle,
    ConceptFramingResult,
    FramingStatus,
    FramingUsabilityClass,
)
from substrate.concept_framing.policy import evaluate_concept_framing_downstream_gate


@dataclass(frozen=True, slots=True)
class ConceptFramingContractView:
    dominant_provisional_frame_present: bool
    competing_frames_present: bool
    underframed_meaning_present: bool
    blocked_high_impact_frame_present: bool
    context_only_frame_hint_present: bool
    clarification_worthy_frame_present: bool
    reframing_conditions_present: bool
    planning_blocked_high_impact_frame: bool
    appraisal_context_only: bool
    memory_uptake_allowed: bool
    usability_class: FramingUsabilityClass
    restrictions: tuple[str, ...]
    requires_status_read: bool
    requires_cautions_read: bool
    accepted_provisional_not_closure: bool
    accepted_degraded_requires_restrictions_read: bool
    strong_closure_permitted: bool
    reason: str


def derive_concept_framing_contract_view(
    concept_framing_result_or_bundle: ConceptFramingResult | ConceptFramingBundle,
) -> ConceptFramingContractView:
    if isinstance(concept_framing_result_or_bundle, ConceptFramingResult):
        bundle = concept_framing_result_or_bundle.bundle
    elif isinstance(concept_framing_result_or_bundle, ConceptFramingBundle):
        bundle = concept_framing_result_or_bundle
    else:
        raise TypeError("derive_concept_framing_contract_view requires ConceptFramingResult/ConceptFramingBundle")

    gate = evaluate_concept_framing_downstream_gate(bundle)
    statuses = [record.framing_status for record in bundle.framing_records]
    cautions = [
        caution
        for record in bundle.framing_records
        for caution in record.downstream_cautions
    ]
    permissions = [
        permission
        for record in bundle.framing_records
        for permission in record.downstream_permissions
    ]

    dominant = FramingStatus.DOMINANT_PROVISIONAL_FRAME in statuses
    competing = FramingStatus.COMPETING_FRAMES in statuses
    underframed = FramingStatus.UNDERFRAMED_MEANING in statuses
    blocked = FramingStatus.BLOCKED_HIGH_IMPACT_FRAME in statuses
    context_only = FramingStatus.CONTEXT_ONLY_FRAME_HINT in statuses

    return ConceptFramingContractView(
        dominant_provisional_frame_present=dominant,
        competing_frames_present=competing,
        underframed_meaning_present=underframed,
        blocked_high_impact_frame_present=blocked,
        context_only_frame_hint_present=context_only,
        clarification_worthy_frame_present=("clarification_worthy_frame" in cautions),
        reframing_conditions_present=any(record.reframing_conditions for record in bundle.framing_records),
        planning_blocked_high_impact_frame=("planning_blocked_high_impact_frame" in permissions),
        appraisal_context_only=("appraisal_context_only" in permissions),
        memory_uptake_allowed=("memory_uptake_blocked" not in gate.restrictions),
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_status_read=(
            "frame_status_must_be_read" in gate.restrictions
            and "framing_basis_must_be_read" in gate.restrictions
        ),
        requires_cautions_read=("downstream_cautions_must_be_read" in gate.restrictions),
        accepted_provisional_not_closure=("accepted_provisional_not_closure" in gate.restrictions),
        accepted_degraded_requires_restrictions_read=(
            "accepted_degraded_requires_restrictions_read" in gate.restrictions
        ),
        strong_closure_permitted=False,
        reason="g06 contract view exposes frame status/vulnerability/caution obligations",
    )
