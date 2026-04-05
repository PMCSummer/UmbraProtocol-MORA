from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.targeted_clarification import (
    InterventionBundle,
    TargetedClarificationResult,
    build_targeted_clarification,
    evaluate_targeted_clarification_downstream_gate,
)


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "world_truth",
        "final_referent",
        "self_state_fact",
        "planner_decision",
        "policy_decision",
        "final_reply_text",
    }
    field_names = (
        {field_info.name for field_info in fields(InterventionBundle)}
        | {field_info.name for field_info in fields(TargetedClarificationResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_g07_requires_typed_g05_g06_l06_upstream_only(g07_factory) -> None:
    ctx = g07_factory("he said that you are tired", "g07-boundary")
    with pytest.raises(TypeError):
        build_targeted_clarification("raw text", ctx.framing, ctx.discourse_update)
    with pytest.raises(TypeError):
        build_targeted_clarification(ctx.acquisition, "raw framing", ctx.discourse_update)
    with pytest.raises(TypeError):
        build_targeted_clarification(ctx.acquisition, ctx.framing, "raw l06")
    with pytest.raises(TypeError):
        evaluate_targeted_clarification_downstream_gate("raw intervention")


def test_insufficient_basis_forces_abstain(g07_factory) -> None:
    ctx = g07_factory("i am tired", "g07-boundary-abstain")
    degraded = replace(ctx.framing.bundle, framing_records=(), competition_links=())
    result = build_targeted_clarification(ctx.acquisition, degraded, ctx.discourse_update)
    gate = evaluate_targeted_clarification_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_intervention_records" in gate.restrictions
