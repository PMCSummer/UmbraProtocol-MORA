from __future__ import annotations

import pytest

from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.modus_hypotheses import evaluate_modus_hypothesis_downstream_gate
from tests.substrate.l05_testkit import build_l05_context


def test_legacy_l04_to_g01_shortcut_still_carries_modus_like_work_as_debt() -> None:
    ctx = build_l05_context('he said "you are tired?"', "l05-shortcut-debt")
    gate = evaluate_modus_hypothesis_downstream_gate(ctx.modus)
    grounded = ctx.grounded
    assert "legacy_l04_g01_shortcut_operational_debt" in gate.restrictions
    assert "legacy_shortcut_bypass_risk" in gate.restrictions
    assert "legacy_shortcut_bypass_forbidden" in gate.restrictions
    assert grounded.bundle.modus_carriers
    assert grounded.bundle.source_anchors
    assert any(
        "surface" in carrier.provenance or "report cue" in carrier.provenance
        for carrier in grounded.bundle.modus_carriers
    )
    assert any(
        "surface" in anchor.provenance
        for anchor in grounded.bundle.source_anchors
    )


def test_g01_does_not_consume_l05_output_directly() -> None:
    ctx = build_l05_context("you are tired", "l05-shortcut-type-guard")
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(ctx.modus)  # type: ignore[arg-type]
