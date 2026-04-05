from __future__ import annotations

import pytest

from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.modus_hypotheses import evaluate_modus_hypothesis_downstream_gate
from tests.substrate.l05_testkit import build_l05_context


def test_legacy_l04_to_g01_shortcut_markers_remain_but_g01_runtime_route_is_normative() -> None:
    ctx = build_l05_context('he said "you are tired?"', "l05-shortcut-debt")
    gate = evaluate_modus_hypothesis_downstream_gate(ctx.modus)
    grounded = ctx.grounded
    assert "legacy_l04_g01_shortcut_operational_debt" in gate.restrictions
    assert "legacy_shortcut_bypass_risk" in gate.restrictions
    assert "legacy_shortcut_bypass_forbidden" in gate.restrictions
    assert grounded.bundle.normative_l05_l06_route_active is True
    assert grounded.bundle.legacy_surface_cue_fallback_used is False
    assert grounded.bundle.modus_carriers
    assert grounded.bundle.source_anchors
    assert all("surface" not in carrier.provenance for carrier in grounded.bundle.modus_carriers)


def test_g01_does_not_consume_l05_output_directly() -> None:
    ctx = build_l05_context("you are tired", "l05-shortcut-type-guard")
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate_normative(ctx.modus)  # type: ignore[arg-type]
