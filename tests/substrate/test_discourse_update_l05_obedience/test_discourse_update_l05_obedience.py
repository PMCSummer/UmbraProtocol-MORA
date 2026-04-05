from __future__ import annotations

from dataclasses import replace

from substrate.discourse_update import ContinuationStatus, build_discourse_update
from substrate.modus_hypotheses.models import L05CautionCode, ModusEvidenceKind
from tests.substrate.l06_testkit import build_l06_context


def _with_first_record(bundle, mutate):
    first = bundle.hypothesis_records[0]
    mutated = mutate(first)
    return replace(
        bundle,
        hypothesis_records=(mutated, *bundle.hypothesis_records[1:]),
    )


def test_l05_evidence_gap_is_not_advisory_for_l06_continuation_topology() -> None:
    modus_bundle = build_l06_context("you are tired", "l05-l06-obedience-evidence-gap").modus.bundle
    baseline = build_discourse_update(modus_bundle)
    degraded_bundle = _with_first_record(
        modus_bundle,
        lambda record: replace(
            record,
            evidence_records=tuple(
                evidence
                for evidence in record.evidence_records
                if evidence.evidence_kind
                not in {ModusEvidenceKind.FORCE_CUE, ModusEvidenceKind.ADDRESSIVITY_CUE}
            ),
        ),
    )
    degraded = build_discourse_update(degraded_bundle)

    baseline_repair_basis = {
        basis
        for trigger in baseline.bundle.repair_triggers
        for basis in trigger.repair_basis
    }
    degraded_repair_basis = {
        basis
        for trigger in degraded.bundle.repair_triggers
        for basis in trigger.repair_basis
    }

    assert degraded_repair_basis != baseline_repair_basis
    assert any(
        "l05_force_evidence_missing" in trigger.repair_basis
        for trigger in degraded.bundle.repair_triggers
    )
    assert any(
        "l05_addressivity_evidence_missing" in trigger.repair_basis
        for trigger in degraded.bundle.repair_triggers
    )


def test_quote_caution_gap_forces_localized_l06_force_owner_repair() -> None:
    modus_bundle = build_l06_context(
        'he said "you are tired?"',
        "l05-l06-obedience-quote-caution-gap",
    ).modus.bundle
    degraded_bundle = _with_first_record(
        modus_bundle,
        lambda record: replace(
            record,
            downstream_cautions=tuple(
                caution
                for caution in record.downstream_cautions
                if caution != L05CautionCode.QUOTED_FORCE_NOT_CURRENT_COMMITMENT
            ),
        ),
    )
    degraded = build_discourse_update(degraded_bundle)

    assert any(
        trigger.localized_trouble_source == "l05_quote_commitment_caution_gap"
        for trigger in degraded.bundle.repair_triggers
    )
    assert any(
        "l05_quote_commitment_caution_missing" in trigger.repair_basis
        for trigger in degraded.bundle.repair_triggers
    )
    assert all(
        trigger.suggested_clarification_type.startswith("bounded_")
        for trigger in degraded.bundle.repair_triggers
    )


def test_l05_gap_with_guarded_signal_prefers_block_over_guarded_precedence() -> None:
    modus_bundle = build_l06_context(
        'he said "you are tired?"',
        "l05-l06-obedience-hard-block-precedence",
    ).modus.bundle
    normalized_bundle = _with_first_record(
        modus_bundle,
        lambda record: replace(
            record,
            uncertainty_markers=("quoted_or_echoic_force_present",),
            uncertainty_entropy=0.3,
        ),
    )
    baseline = build_discourse_update(normalized_bundle)
    degraded_bundle = _with_first_record(
        normalized_bundle,
        lambda record: replace(
            record,
            evidence_records=tuple(
                evidence
                for evidence in record.evidence_records
                if evidence.evidence_kind is not ModusEvidenceKind.FORCE_CUE
            ),
        ),
    )
    degraded = build_discourse_update(degraded_bundle)

    baseline_statuses = {
        state.continuation_status for state in baseline.bundle.continuation_states
    }
    degraded_statuses = {
        state.continuation_status for state in degraded.bundle.continuation_states
    }

    assert ContinuationStatus.GUARDED_CONTINUE in baseline_statuses
    assert ContinuationStatus.BLOCKED_PENDING_REPAIR in degraded_statuses
    assert ContinuationStatus.GUARDED_CONTINUE not in degraded_statuses
