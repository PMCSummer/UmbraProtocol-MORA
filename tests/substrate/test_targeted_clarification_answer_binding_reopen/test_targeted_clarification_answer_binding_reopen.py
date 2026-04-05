from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.targeted_clarification import build_targeted_clarification


def test_answer_binding_hooks_are_first_class_and_typed(g07_factory) -> None:
    result = g07_factory('he said "you are tired?"', "g07-answer-hooks").intervention
    assert result.bundle.answer_binding_ready is True
    assert result.bundle.answer_binding_hooks
    assert all(record.uncertainty_target_id for record in result.bundle.intervention_records)
    assert all(record.reopen_conditions for record in result.bundle.intervention_records)


def test_targeted_answer_updates_same_targets_not_unrelated_new_records(g07_factory) -> None:
    base = g07_factory('he said "you are tired?"', "g07-answer-update")
    initial = build_targeted_clarification(
        base.acquisition,
        base.framing,
        base.discourse_update,
    )
    resolved_acq = replace(
        base.acquisition.bundle,
        acquisition_records=tuple(
            replace(
                record,
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
    resolved_framing = replace(
        base.framing.bundle,
        framing_records=tuple(
            replace(record, framing_status=FramingStatus.DOMINANT_PROVISIONAL_FRAME)
            for record in base.framing.bundle.framing_records
        ),
    )
    reopened = build_targeted_clarification(
        resolved_acq,
        resolved_framing,
        base.discourse_update,
    )

    initial_by_target = {record.uncertainty_target_id: record for record in initial.bundle.intervention_records}
    reopened_by_target = {record.uncertainty_target_id: record for record in reopened.bundle.intervention_records}
    assert initial_by_target.keys() == reopened_by_target.keys()
    assert any(
        initial_by_target[key].intervention_status != reopened_by_target[key].intervention_status
        or initial_by_target[key].uncertainty_class != reopened_by_target[key].uncertainty_class
        for key in initial_by_target
    )
