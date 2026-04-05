from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.semantic_acquisition.models import AcquisitionStatus
from substrate.targeted_clarification import InterventionStatus, build_targeted_clarification


def test_real_uncertainty_can_be_blocked_when_questionability_is_insufficient(g07_factory) -> None:
    base = g07_factory('he said "you are tired?"', "g07-questionability-blocked")
    blocked = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    acquisition_status=AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        unresolved_slots=("source_scope", "commitment_owner"),
                    ),
                )
                for record in base.acquisition.bundle.acquisition_records
            ),
        ),
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    statuses = {record.intervention_status for record in blocked.bundle.intervention_records}
    assert InterventionStatus.ASK_NOW not in statuses
    assert InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in statuses


def test_low_value_uncertainty_goes_to_not_worth_or_defer_not_forced_ask(g07_factory) -> None:
    base = g07_factory("it is cold", "g07-questionability-low-value")
    low_value = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.CONTEXT_ONLY_FRAME_HINT)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    statuses = {record.intervention_status for record in low_value.bundle.intervention_records}
    assert InterventionStatus.ASK_NOW not in statuses
    assert (
        InterventionStatus.CLARIFICATION_NOT_WORTH_COST in statuses
        or InterventionStatus.DEFER_UNTIL_NEEDED in statuses
        or InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS in statuses
        or InterventionStatus.ABSTAIN_WITHOUT_QUESTION in statuses
    )
