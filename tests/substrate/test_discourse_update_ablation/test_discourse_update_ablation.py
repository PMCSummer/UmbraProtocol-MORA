from __future__ import annotations

from dataclasses import replace

from substrate.discourse_update import build_discourse_update, evaluate_discourse_update_downstream_gate
from tests.substrate.l06_testkit import build_l06_context


def test_ablation_of_uncertainty_markers_reduces_repair_load() -> None:
    ctx = build_l06_context("this is true", "l06-ablation-uncertainty")
    baseline = ctx.discourse_update
    ablated_modus = replace(
        ctx.modus.bundle,
        hypothesis_records=tuple(
            replace(record, uncertainty_markers=tuple(marker for marker in record.uncertainty_markers if marker not in {"unresolved_argument_slots", "scope_ambiguity"}))
            for record in ctx.modus.bundle.hypothesis_records
        ),
    )
    ablated = build_discourse_update(ablated_modus)
    assert len(baseline.bundle.repair_triggers) > len(ablated.bundle.repair_triggers)

    base_gate = evaluate_discourse_update_downstream_gate(baseline)
    ablated_gate = evaluate_discourse_update_downstream_gate(ablated)
    assert len(baseline.bundle.blocked_update_ids) >= len(ablated.bundle.blocked_update_ids)
    assert len(baseline.bundle.guarded_update_ids) != len(ablated.bundle.guarded_update_ids) or len(baseline.bundle.repair_triggers) != len(ablated.bundle.repair_triggers)
    assert base_gate.accepted is True and ablated_gate.accepted is True


def test_ablation_of_localization_refs_breaks_lawful_gate_shape() -> None:
    ctx = build_l06_context('he said "you are tired?"', "l06-ablation-localization")
    malformed = replace(
        ctx.discourse_update.bundle,
        repair_triggers=tuple(
            replace(trigger, localized_ref_ids=())
            for trigger in ctx.discourse_update.bundle.repair_triggers
        ),
    )
    gate = evaluate_discourse_update_downstream_gate(malformed)
    assert "repair_localization_gap_detected" in gate.restrictions
