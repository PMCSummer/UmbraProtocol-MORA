from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.modus_hypotheses import (
    ModusHypothesisBundle,
    ModusHypothesisResult,
    build_modus_hypotheses,
    evaluate_modus_hypothesis_downstream_gate,
)
from tests.substrate.l05_testkit import build_l05_context


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "final_intent",
        "planner_action",
        "discourse_update",
        "repair_plan",
        "world_truth",
        "psychological_diagnosis",
    }
    field_names = (
        {field_info.name for field_info in fields(ModusHypothesisBundle)}
        | {field_info.name for field_info in fields(ModusHypothesisResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_l05_requires_typed_l04_upstream_only() -> None:
    ctx = build_l05_context('he said "you are tired"', "l05-boundary")
    with pytest.raises(TypeError):
        build_modus_hypotheses("raw text")
    with pytest.raises(TypeError):
        evaluate_modus_hypothesis_downstream_gate("raw modus")
    assert ctx.modus.bundle.hypothesis_records


def test_insufficient_basis_forces_abstain() -> None:
    ctx = build_l05_context("i am tired", "l05-boundary-abstain")
    degraded = replace(ctx.dictum.bundle, dictum_candidates=())
    result = build_modus_hypotheses(degraded)
    gate = evaluate_modus_hypothesis_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_l05_records" in gate.restrictions
