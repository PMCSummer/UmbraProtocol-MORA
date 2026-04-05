from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.semantic_acquisition.models import AcquisitionStatus
from substrate.targeted_clarification import InterventionStatus, build_targeted_clarification


def test_contrastive_intervention_not_collapsing_to_generic_single_path(g07_factory) -> None:
    base = g07_factory("you are tired", "g07-contrast")

    ask_now = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.COMPETING_FRAMES)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    abstain = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    acquisition_status=AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        support_score=0.0,
                        conflict_score=2.0,
                        conflict_reasons=("cross_turn_repair_pending",),
                        unresolved_slots=("cross_turn_repair",),
                    ),
                )
                for record in base.acquisition.bundle.acquisition_records
            ),
        ),
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.DOMINANT_PROVISIONAL_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    guarded = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                    replace(
                        record,
                        acquisition_status=AcquisitionStatus.WEAK_PROVISIONAL,
                        support_conflict_profile=replace(
                            record.support_conflict_profile,
                            unresolved_slots=("temporal_anchor",),
                            conflict_reasons=("assertion_mode:question_frame",),
                            conflict_score=1.0,
                        ),
                    )
                for record in base.acquisition.bundle.acquisition_records
            ),
        ),
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.DOMINANT_PROVISIONAL_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )

    ask_statuses = {record.intervention_status for record in ask_now.bundle.intervention_records}
    abstain_statuses = {record.intervention_status for record in abstain.bundle.intervention_records}
    guarded_statuses = {record.intervention_status for record in guarded.bundle.intervention_records}

    assert InterventionStatus.ASK_NOW in ask_statuses
    assert InterventionStatus.ABSTAIN_WITHOUT_QUESTION in abstain_statuses or InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in abstain_statuses
    assert InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS in guarded_statuses


def test_ask_now_requires_concrete_target_and_targeted_contrast(g07_factory) -> None:
    base = g07_factory("you are tired", "g07-target-specificity")
    ask_now = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.COMPETING_FRAMES)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    ask_records = [
        record for record in ask_now.bundle.intervention_records if record.intervention_status is InterventionStatus.ASK_NOW
    ]
    assert ask_records
    assert all(record.uncertainty_target_id.startswith("target:") for record in ask_records)
    assert all(
        record.minimal_question_spec.clarification_intent.target_contrast != "can_you_clarify_generic"
        for record in ask_records
    )
