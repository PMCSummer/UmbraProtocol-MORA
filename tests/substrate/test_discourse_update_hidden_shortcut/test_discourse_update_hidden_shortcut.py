from __future__ import annotations

import pytest

from substrate.discourse_update import evaluate_discourse_update_downstream_gate
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from tests.substrate.l06_testkit import build_l06_context


def test_legacy_g01_path_still_represents_bypass_risk_as_debt() -> None:
    ctx = build_l06_context('he said "you are tired?"', "l06-hidden-shortcut")
    gate = evaluate_discourse_update_downstream_gate(ctx.discourse_update)
    grounded = ctx.grounded
    assert "legacy_bypass_risk_present" in gate.restrictions
    assert "legacy_bypass_forbidden" in gate.restrictions
    assert grounded.bundle.modus_carriers
    assert grounded.bundle.source_anchors


def test_g01_does_not_consume_l06_output_directly() -> None:
    ctx = build_l06_context("you are tired", "l06-hidden-shortcut-guard")
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate_normative(ctx.discourse_update)  # type: ignore[arg-type]
