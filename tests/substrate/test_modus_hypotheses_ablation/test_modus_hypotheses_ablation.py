from __future__ import annotations

from dataclasses import replace

from substrate.modus_hypotheses import (
    IllocutionKind,
    build_modus_hypotheses,
    evaluate_modus_hypothesis_downstream_gate,
)
from tests.substrate.l05_testkit import build_l05_context


def test_ablation_of_quoted_markers_changes_force_and_addressivity() -> None:
    ctx = build_l05_context('he said "you are tired"', "l05-ablation-quote")
    baseline = ctx.modus

    ablated_bundle = replace(
        ctx.dictum.bundle,
        dictum_candidates=tuple(
            replace(
                candidate,
                quotation_sensitive=False,
                ambiguity_reasons=tuple(
                    reason for reason in candidate.ambiguity_reasons if "quotation" not in reason.lower()
                ),
            )
            for candidate in ctx.dictum.bundle.dictum_candidates
        ),
    )
    ablated = build_modus_hypotheses(ablated_bundle)

    baseline_kinds = {
        hypothesis.illocution_kind
        for record in baseline.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    ablated_kinds = {
        hypothesis.illocution_kind
        for record in ablated.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }
    assert IllocutionKind.QUOTED_FORCE_CANDIDATE in baseline_kinds
    assert IllocutionKind.QUOTED_FORCE_CANDIDATE not in ablated_kinds


def test_ablation_of_unresolved_slots_reduces_unknown_target_pressure() -> None:
    ctx = build_l05_context("this is true", "l05-ablation-addressivity")
    baseline = ctx.modus
    ablated_bundle = replace(
        ctx.dictum.bundle,
        dictum_candidates=tuple(
            replace(
                candidate,
                argument_slots=tuple(
                    replace(slot, unresolved=False, unresolved_reason=None)
                    for slot in candidate.argument_slots
                ),
            )
            for candidate in ctx.dictum.bundle.dictum_candidates
        ),
    )
    ablated = build_modus_hypotheses(ablated_bundle)

    baseline_unknown_weight = sum(
        hypothesis.confidence_weight
        for record in baseline.bundle.hypothesis_records
        for hypothesis in record.addressivity_hypotheses
        if hypothesis.addressivity_kind.value == "unknown_target"
    )
    ablated_unknown_weight = sum(
        hypothesis.confidence_weight
        for record in ablated.bundle.hypothesis_records
        for hypothesis in record.addressivity_hypotheses
        if hypothesis.addressivity_kind.value == "unknown_target"
    )
    assert baseline_unknown_weight > ablated_unknown_weight

    base_gate = evaluate_modus_hypothesis_downstream_gate(baseline)
    ablated_gate = evaluate_modus_hypothesis_downstream_gate(ablated)
    assert "unresolved_slot_pressure_must_be_read" in base_gate.restrictions
    assert base_gate.restrictions != ablated_gate.restrictions
