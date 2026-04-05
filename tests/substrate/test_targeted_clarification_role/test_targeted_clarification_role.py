from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.targeted_clarification import build_targeted_clarification


def test_uncertainty_structure_changes_intervention_status(g07_factory) -> None:
    base = g07_factory("you are tired", "g07-role-base")

    low_conflict = build_targeted_clarification(
        base.acquisition,
        base.framing,
        base.discourse_update,
    )
    high_conflict_framing = replace(
        base.framing.bundle,
        framing_records=tuple(
            replace(record, framing_status=FramingStatus.COMPETING_FRAMES)
            for record in base.framing.bundle.framing_records
        ),
    )
    high_conflict = build_targeted_clarification(
        base.acquisition,
        high_conflict_framing,
        base.discourse_update,
    )

    low_sig = {record.intervention_status.value for record in low_conflict.bundle.intervention_records}
    high_sig = {record.intervention_status.value for record in high_conflict.bundle.intervention_records}
    assert low_sig != high_sig


def test_confidence_alone_does_not_drive_ask_policy(g07_factory) -> None:
    base = g07_factory("he said that you are tired", "g07-role-confidence")
    high_conf_acq = replace(
        base.acquisition.bundle,
        acquisition_records=tuple(replace(record, confidence=0.9) for record in base.acquisition.bundle.acquisition_records),
    )
    low_conf_acq = replace(
        base.acquisition.bundle,
        acquisition_records=tuple(replace(record, confidence=0.22) for record in base.acquisition.bundle.acquisition_records),
    )
    high_conf = build_targeted_clarification(
        high_conf_acq,
        base.framing,
        base.discourse_update,
    )
    low_conf = build_targeted_clarification(
        low_conf_acq,
        base.framing,
        base.discourse_update,
    )

    high_status = {record.intervention_status for record in high_conf.bundle.intervention_records}
    low_status = {record.intervention_status for record in low_conf.bundle.intervention_records}
    assert high_status == low_status
