from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.concept_framing.models import FramingStatus
from substrate.discourse_update.models import ContinuationStatus, RepairClass
from substrate.semantic_acquisition.models import AcquisitionStatus
from substrate.targeted_clarification import (
    InterventionStatus,
    build_targeted_clarification,
    derive_targeted_clarification_contract_view,
    evaluate_targeted_clarification_downstream_gate,
)


def test_g07_requires_typed_l06_upstream_and_marks_l06_bound(g07_factory) -> None:
    ctx = g07_factory('he said "you are tired?"', "g07-l06-rewire-typed")
    result = build_targeted_clarification(
        ctx.acquisition,
        ctx.framing,
        ctx.discourse_update,
    )
    gate = evaluate_targeted_clarification_downstream_gate(result)

    assert result.bundle.l06_upstream_bound_here is True
    assert result.bundle.l06_update_proposal_absent is False
    assert result.bundle.l06_continuation_topology_present is True
    assert "l06_proposal_requires_acceptance_read" in gate.restrictions
    assert "intervention_not_discourse_acceptance" in gate.restrictions

    with pytest.raises(TypeError):
        build_targeted_clarification(ctx.acquisition, ctx.framing, "raw l06")


def test_l06_repair_localization_changes_g07_decision_surface(g07_factory) -> None:
    ctx = g07_factory('he said "you are tired?"', "g07-l06-rewire-localization")
    temporal_acq = replace(
        ctx.acquisition.bundle,
        acquisition_records=tuple(
            replace(
                record,
                acquisition_status=AcquisitionStatus.WEAK_PROVISIONAL,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    unresolved_slots=("temporal_anchor",),
                    conflict_reasons=(),
                ),
            )
            for record in ctx.acquisition.bundle.acquisition_records
        ),
    )
    temporal_frame = replace(
        ctx.framing.bundle,
        framing_records=tuple(
            replace(record, framing_status=FramingStatus.UNDERFRAMED_MEANING)
            for record in ctx.framing.bundle.framing_records
        ),
    )
    first_repair = ctx.discourse_update.bundle.repair_triggers[0]
    aligned_l06 = replace(
        ctx.discourse_update.bundle,
        repair_triggers=(replace(first_repair, repair_class=RepairClass.SCOPE_REPAIR),),
    )
    misaligned_l06 = replace(
        ctx.discourse_update.bundle,
        repair_triggers=(replace(first_repair, repair_class=RepairClass.TARGET_APPLICABILITY_REPAIR),),
    )

    aligned = build_targeted_clarification(temporal_acq, temporal_frame, aligned_l06)
    misaligned = build_targeted_clarification(temporal_acq, temporal_frame, misaligned_l06)
    misaligned_gate = evaluate_targeted_clarification_downstream_gate(misaligned)

    aligned_statuses = {record.intervention_status for record in aligned.bundle.intervention_records}
    misaligned_statuses = {record.intervention_status for record in misaligned.bundle.intervention_records}
    assert aligned_statuses != misaligned_statuses
    assert misaligned.bundle.l06_g07_target_drift_detected is True
    assert "l06_g07_target_drift_detected" in misaligned_gate.restrictions


def test_l06_proposal_acceptance_boundary_blocks_acceptance_inflation(g07_factory) -> None:
    result = g07_factory("you are tired?", "g07-l06-rewire-acceptance").intervention
    gate = evaluate_targeted_clarification_downstream_gate(result)
    view = derive_targeted_clarification_contract_view(result)

    assert "l06_update_not_accepted" in gate.restrictions
    assert "l06_update_not_authorized_yet" in gate.restrictions
    assert "accepted_intervention_not_accepted_update" in gate.restrictions
    assert view.l06_proposal_requires_acceptance_read is True
    assert view.l06_update_not_accepted is True
    assert view.intervention_not_discourse_acceptance is True


def test_l06_block_vs_guard_topology_materially_changes_intervention(g07_factory) -> None:
    ctx = g07_factory("you are dangerous", "g07-l06-rewire-block-guard")
    blocked_l06 = replace(
        ctx.discourse_update.bundle,
        repair_triggers=(),
        continuation_states=tuple(
            replace(
                state,
                continuation_status=ContinuationStatus.BLOCKED_PENDING_REPAIR,
                guarded_continue_allowed=False,
                guarded_continue_forbidden=True,
            )
            for state in ctx.discourse_update.bundle.continuation_states
        ),
    )
    guarded_l06 = replace(
        ctx.discourse_update.bundle,
        repair_triggers=(),
        continuation_states=tuple(
            replace(
                state,
                continuation_status=ContinuationStatus.GUARDED_CONTINUE,
                guarded_continue_allowed=True,
                guarded_continue_forbidden=False,
            )
            for state in ctx.discourse_update.bundle.continuation_states
        ),
    )

    blocked = build_targeted_clarification(ctx.acquisition, ctx.framing, blocked_l06)
    guarded = build_targeted_clarification(ctx.acquisition, ctx.framing, guarded_l06)
    blocked_gate = evaluate_targeted_clarification_downstream_gate(blocked)
    guarded_gate = evaluate_targeted_clarification_downstream_gate(guarded)

    assert {
        record.intervention_status for record in blocked.bundle.intervention_records
    } != {
        record.intervention_status for record in guarded.bundle.intervention_records
    }
    assert "l06_block_or_guard_must_be_read" in blocked_gate.restrictions
    assert "l06_block_or_guard_must_be_read" in guarded_gate.restrictions
    assert InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in {
        record.intervention_status for record in blocked.bundle.intervention_records
    }
