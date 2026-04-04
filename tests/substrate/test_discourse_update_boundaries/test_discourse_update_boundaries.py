from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.discourse_update import (
    DiscourseUpdateBundle,
    DiscourseUpdateResult,
    build_discourse_update,
    evaluate_discourse_update_downstream_gate,
)
from tests.substrate.l06_testkit import build_l06_context


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "accepted_truth",
        "common_ground_mutation",
        "self_state_mutation",
        "dialogue_manager_plan",
        "planner_action",
        "final_response_text",
    }
    field_names = (
        {field_info.name for field_info in fields(DiscourseUpdateBundle)}
        | {field_info.name for field_info in fields(DiscourseUpdateResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_l06_requires_typed_l05_upstream_only() -> None:
    ctx = build_l06_context('he said "you are tired"', "l06-boundary")
    with pytest.raises(TypeError):
        build_discourse_update("raw l05")
    with pytest.raises(TypeError):
        evaluate_discourse_update_downstream_gate("raw l06")
    assert ctx.discourse_update.bundle.update_proposals


def test_insufficient_basis_forces_abstain() -> None:
    ctx = build_l06_context("i am tired", "l06-boundary-abstain")
    degraded = replace(ctx.modus.bundle, hypothesis_records=())
    result = build_discourse_update(degraded)
    gate = evaluate_discourse_update_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_update_proposals" in gate.restrictions
