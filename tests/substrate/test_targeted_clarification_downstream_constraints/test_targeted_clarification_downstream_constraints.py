from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus, VulnerabilityLevel
from substrate.semantic_acquisition.models import AcquisitionStatus
from substrate.targeted_clarification import (
    InterventionUsabilityClass,
    build_targeted_clarification,
    derive_targeted_clarification_contract_view,
    evaluate_targeted_clarification_downstream_gate,
)


def test_contract_requires_target_binding_and_lockouts_read(g07_factory) -> None:
    result = g07_factory("you are tired?", "g07-contract").intervention
    view = derive_targeted_clarification_contract_view(result)
    gate = evaluate_targeted_clarification_downstream_gate(result)

    assert view.requires_target_binding_read is True
    assert view.requires_lockouts_read is True
    assert view.requires_question_spec_target_binding_read is True
    assert view.requires_forbidden_presuppositions_read is True
    assert view.intervention_object_presence_not_permission is True
    assert view.accepted_intervention_not_resolution is True
    assert "clarification_not_equal_realized_question" in gate.restrictions
    assert "asked_question_not_equal_resolved_uncertainty" in gate.restrictions
    assert view.strong_continue_permission is False


def test_intervention_state_materially_differs_by_uncertainty_structure(g07_factory) -> None:
    base = g07_factory("you are tired", "g07-contract-structure")
    normalized_acq = replace(
        base.acquisition.bundle,
        acquisition_records=tuple(
            replace(
                record,
                acquisition_status=AcquisitionStatus.WEAK_PROVISIONAL,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    unresolved_slots=(),
                    conflict_reasons=(),
                    conflict_score=0.0,
                ),
            )
            for record in base.acquisition.bundle.acquisition_records
        ),
    )
    conservative_framing = replace(
        base.framing.bundle,
        framing_records=tuple(
            replace(
                record,
                framing_status=FramingStatus.DOMINANT_PROVISIONAL_FRAME,
                vulnerability_profile=replace(
                    record.vulnerability_profile,
                    high_impact=False,
                    vulnerability_level=VulnerabilityLevel.LOW,
                ),
            )
            for record in base.framing.bundle.framing_records
        ),
    )
    conservative = build_targeted_clarification(normalized_acq, conservative_framing)

    escalated_framing = replace(
        base.framing.bundle,
        framing_records=tuple(
            replace(record, framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME)
            for record in base.framing.bundle.framing_records
        ),
    )
    escalated = build_targeted_clarification(normalized_acq, escalated_framing)

    conservative_sig = {
        (record.intervention_status.value, record.uncertainty_class.value, tuple(sorted(record.downstream_lockouts)))
        for record in conservative.bundle.intervention_records
    }
    escalated_sig = {
        (record.intervention_status.value, record.uncertainty_class.value, tuple(sorted(record.downstream_lockouts)))
        for record in escalated.bundle.intervention_records
    }
    assert conservative_sig != escalated_sig

    gate = evaluate_targeted_clarification_downstream_gate(escalated)
    assert gate.usability_class in {InterventionUsabilityClass.DEGRADED_BOUNDED, InterventionUsabilityClass.BLOCKED}
