from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.semantic_acquisition.models import AcquisitionStatus
from substrate.targeted_clarification import build_targeted_clarification


def test_ownership_and_quote_shift_change_intervention_outcome(g07_factory) -> None:
    direct = g07_factory("you are tired", "g07-meta-direct").intervention
    quote = g07_factory('"you are tired"', "g07-meta-quote").intervention
    report = g07_factory("he said that you are tired", "g07-meta-report").intervention

    sig = lambda result: {
        (record.intervention_status.value, record.uncertainty_class.value)
        for record in result.bundle.intervention_records
    }
    variants = {tuple(sorted(signature)) for signature in map(sig, (direct, quote, report))}
    assert len(variants) >= 2


def test_temporal_anchor_shift_changes_decision_causally(g07_factory) -> None:
    base = g07_factory('he said "you are tired"', "g07-meta-temporal")
    baseline = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    acquisition_status=AcquisitionStatus.WEAK_PROVISIONAL,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        conflict_reasons=(),
                        conflict_score=0.0,
                        unresolved_slots=(),
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
    temporal_shift = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    acquisition_status=AcquisitionStatus.WEAK_PROVISIONAL,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        conflict_reasons=tuple(
                            reason
                            for reason in record.support_conflict_profile.conflict_reasons
                            if reason not in {"source_scope_unknown", "commitment_owner_ambiguous"}
                        ),
                        unresolved_slots=tuple(dict.fromkeys((*record.support_conflict_profile.unresolved_slots, "temporal_anchor"))),
                    ),
                )
                for record in base.acquisition.bundle.acquisition_records
            ),
        ),
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.UNDERFRAMED_MEANING)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    assert {
        (record.intervention_status.value, record.uncertainty_class.value)
        for record in baseline.bundle.intervention_records
    } != {
        (record.intervention_status.value, record.uncertainty_class.value)
        for record in temporal_shift.bundle.intervention_records
    }


def test_modality_like_shift_changes_ask_vs_defer_surface(g07_factory) -> None:
    base = g07_factory("you are tired", "g07-meta-modality")
    assertive = build_targeted_clarification(
        base.acquisition,
        base.framing,
        base.discourse_update,
    )
    questioned = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.UNDERFRAMED_MEANING)
                for record in base.framing.bundle.framing_records
            ),
        ),
        base.discourse_update,
    )
    assert {
        record.intervention_status.value for record in assertive.bundle.intervention_records
    } != {
        record.intervention_status.value for record in questioned.bundle.intervention_records
    }
