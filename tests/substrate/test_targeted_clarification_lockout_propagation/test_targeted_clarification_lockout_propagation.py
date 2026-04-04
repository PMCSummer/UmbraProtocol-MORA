from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.targeted_clarification import (
    build_targeted_clarification,
    derive_targeted_clarification_contract_view,
)


def test_lockout_propagation_materially_blocks_downstream_permissions(g07_factory) -> None:
    base = g07_factory("you are dangerous", "g07-lockout")
    high_impact = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
    )
    view = derive_targeted_clarification_contract_view(high_impact)
    assert view.closure_blocked_until_answer is True
    assert view.planning_forbidden_on_current_frame is True
    assert view.memory_uptake_deferred is True
    assert view.narrative_commitment_forbidden is True
    assert view.safety_escalation_not_authorized_from_current_evidence is True


def test_lockout_surface_differs_for_context_only_vs_high_impact(g07_factory) -> None:
    base = g07_factory("it is cold", "g07-lockout-contrast")
    context_only = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.CONTEXT_ONLY_FRAME_HINT)
                for record in base.framing.bundle.framing_records
            ),
        ),
    )
    high_impact = build_targeted_clarification(
        base.acquisition,
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
    )
    context_view = derive_targeted_clarification_contract_view(context_only)
    high_view = derive_targeted_clarification_contract_view(high_impact)
    assert context_view.appraisal_context_only is True
    assert high_view.planning_forbidden_on_current_frame is True
    assert context_view.ask_now_present != high_view.ask_now_present or context_view.blocked_due_to_insufficient_questionability_present != high_view.blocked_due_to_insufficient_questionability_present
