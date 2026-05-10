from __future__ import annotations

from substrate.n02_identity_drift_reflection import (
    N02BaselineValidityStatus,
    N02DriftKind,
    N02IdentityRegionKind,
    N02SubstrateChangeKind,
    derive_n02_consumer_packets,
)
from tests.substrate.n02_identity_drift_reflection_testkit import (
    N02HarnessCase,
    build_n02_harness_case,
    n02_baseline,
    n02_bundle,
    n02_change,
    n02_current,
    n02_history,
)


def _run_case(
    case_id: str,
    *,
    baselines=(),
    currents=(),
    changes=(),
    history=(),
):
    bundle = n02_bundle(
        bundle_id=f"{case_id}:bundle",
        baselines=baselines,
        currents=currents,
        changes=changes,
        history=history,
        source_lineage=("tests.n02.owner", case_id),
        reason=case_id,
    )
    return build_n02_harness_case(N02HarnessCase(case_id=case_id, input_bundle=bundle)).n02_result


def test_no_typed_basis_returns_no_clean_drift_claim() -> None:
    result = build_n02_harness_case(N02HarnessCase(case_id="no-basis", input_bundle=None)).n02_result
    assert result.drift_entries == ()
    assert result.gate.n02_consumer_ready is False
    assert "n02_no_clean_drift_claim" in result.gate.required_restrictions


def test_stable_baseline_current_substrate_emits_stable_continuation() -> None:
    result = _run_case(
        "stable",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.STABLE_CONTINUATION
    assert result.drift_entries[0].continuity_preserved_flag is True


def test_local_grounded_revision_is_bounded_revision_not_rupture() -> None:
    result = _run_case(
        "bounded-revision",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.LOCAL_REVISION),),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.BOUNDED_REVISION


def test_repeated_scoped_revisions_emit_gradual_shift() -> None:
    result = _run_case(
        "gradual-shift",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.REPETITIVE_REVISION),
            n02_change(change_id="chg2", change_kind=N02SubstrateChangeKind.REPETITIVE_REVISION),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.GRADUAL_SHIFT


def test_abrupt_incompatible_broad_pattern_emits_abrupt_reorientation() -> None:
    result = _run_case(
        "abrupt-reorientation",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(
                change_id="chg1",
                change_kind=N02SubstrateChangeKind.ABRUPT_INCOMPATIBLE_REPLACEMENT,
                magnitude_hint=0.88,
                confidence=0.84,
            ),
            n02_change(
                change_id="chg2",
                change_kind=N02SubstrateChangeKind.ABRUPT_INCOMPATIBLE_REPLACEMENT,
                magnitude_hint=0.82,
                confidence=0.81,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.ABRUPT_REORIENTATION


def test_context_split_detected_for_incompatible_scoped_patterns() -> None:
    result = _run_case(
        "context-split",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(
                change_id="chg1",
                change_kind=N02SubstrateChangeKind.CONTEXT_SPLIT_SIGNAL,
                context_scope="context:analysis",
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.CONTEXT_SPLIT_DETECTED
    assert result.drift_entries[0].context_split_scope == "context:analysis"


def test_repeated_weakening_retraction_emits_commitment_erosion() -> None:
    result = _run_case(
        "erosion",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.COMMITMENT_WEAKENING),),
        history=(
            n02_history(event_id="h1", current_status="revised"),
            n02_history(event_id="h2", current_status="retired"),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.COMMITMENT_EROSION


def test_capability_shift_with_support_emits_capability_revision_drift() -> None:
    result = _run_case(
        "capability-drift",
        baselines=(n02_baseline(baseline_id="b1", baseline_kind=N02IdentityRegionKind.CAPABILITY_CONTOUR),),
        currents=(
            n02_current(
                current_reference_id="c1",
                observed_region=N02IdentityRegionKind.CAPABILITY_CONTOUR,
                capability_or_affordance_refs=("cap:a",),
            ),
        ),
        changes=(
            n02_change(
                change_id="chg1",
                region=N02IdentityRegionKind.CAPABILITY_CONTOUR,
                change_kind=N02SubstrateChangeKind.CAPABILITY_CONTOUR_SHIFT,
                affected_capability_refs=("cap:a",),
                self_related=True,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.CAPABILITY_REVISION_DRIFT


def test_plain_tool_availability_update_without_self_contour_is_not_identity_drift() -> None:
    result = _run_case(
        "tool-availability-only",
        baselines=(n02_baseline(baseline_id="b1", baseline_kind=N02IdentityRegionKind.CAPABILITY_CONTOUR),),
        currents=(n02_current(current_reference_id="c1", observed_region=N02IdentityRegionKind.CAPABILITY_CONTOUR),),
        changes=(
            n02_change(
                change_id="chg1",
                region=N02IdentityRegionKind.CAPABILITY_CONTOUR,
                change_kind=N02SubstrateChangeKind.CAPABILITY_CONTOUR_SHIFT,
                self_related=False,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.BOUNDED_REVISION
    assert "overreflection_guard_applied" in result.drift_entries[0].reason_codes


def test_noisy_self_binding_fluctuation_alone_not_strong_self_binding_drift() -> None:
    result = _run_case(
        "self-binding-noisy",
        baselines=(n02_baseline(baseline_id="b1", baseline_kind=N02IdentityRegionKind.SELF_BINDING_CORE),),
        currents=(n02_current(current_reference_id="c1", observed_region=N02IdentityRegionKind.SELF_BINDING_CORE),),
        changes=(
            n02_change(
                change_id="chg1",
                region=N02IdentityRegionKind.SELF_BINDING_CORE,
                change_kind=N02SubstrateChangeKind.SELF_BINDING_NOISY_FLUCTUATION,
                magnitude_hint=0.45,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.NO_CLEAN_DRIFT_CLAIM


def test_sustained_self_binding_core_change_emits_self_binding_drift() -> None:
    result = _run_case(
        "self-binding-core-shift",
        baselines=(n02_baseline(baseline_id="b1", baseline_kind=N02IdentityRegionKind.SELF_BINDING_CORE),),
        currents=(n02_current(current_reference_id="c1", observed_region=N02IdentityRegionKind.SELF_BINDING_CORE),),
        changes=(
            n02_change(
                change_id="chg1",
                region=N02IdentityRegionKind.SELF_BINDING_CORE,
                change_kind=N02SubstrateChangeKind.SELF_BINDING_CORE_SHIFT,
                magnitude_hint=0.82,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.SELF_BINDING_DRIFT


def test_unresolved_contradiction_accumulation_emits_unresolved_tension_or_fracture() -> None:
    result = _run_case(
        "contradiction-tension",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(
                change_id="chg1",
                change_kind=N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION,
                magnitude_hint=0.65,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind in {
        N02DriftKind.UNRESOLVED_IDENTITY_TENSION,
        N02DriftKind.CONTRADICTION_DRIVEN_FRACTURE,
    }


def test_text_diff_only_with_stable_substrate_is_blocked() -> None:
    result = _run_case(
        "text-diff-only",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.TEXTUAL_REPHRASE_ONLY),),
    )
    entry = result.drift_entries[0]
    assert entry.drift_kind is N02DriftKind.NO_CLEAN_DRIFT_CLAIM
    assert "text_diff_only_not_identity_drift" in entry.reason_codes


def test_same_textual_change_with_substrate_impact_changes_assessment() -> None:
    no_impact = _run_case(
        "text-no-impact",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.TEXTUAL_REPHRASE_ONLY),),
    )
    impact = _run_case(
        "text-with-impact",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.REPETITIVE_REVISION),
            n02_change(change_id="chg2", change_kind=N02SubstrateChangeKind.REPETITIVE_REVISION),
        ),
    )
    assert no_impact.drift_entries[0].drift_kind is N02DriftKind.NO_CLEAN_DRIFT_CLAIM
    assert impact.drift_entries[0].drift_kind in {
        N02DriftKind.BOUNDED_REVISION,
        N02DriftKind.GRADUAL_SHIFT,
    }


def test_baseline_stale_or_missing_produces_baseline_uncertain_no_clean() -> None:
    result = _run_case(
        "baseline-uncertain",
        baselines=(
            n02_baseline(
                baseline_id="b1",
                validity_status=N02BaselineValidityStatus.STALE,
            ),
        ),
        currents=(n02_current(current_reference_id="c1"),),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.NO_CLEAN_DRIFT_CLAIM
    assert "baseline_uncertain" in result.drift_entries[0].reason_codes


def test_context_split_not_flattened_to_global_rupture() -> None:
    result = _run_case(
        "context-split-caution",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1", context_scope="mode:analysis"),),
        changes=(
            n02_change(
                change_id="chg1",
                change_kind=N02SubstrateChangeKind.CONTEXT_SPLIT_SIGNAL,
                context_scope="mode:analysis",
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.CONTEXT_SPLIT_DETECTED
    assert "must_not_flatten_context_split_to_global_rupture" in result.drift_entries[0].downstream_caution


def test_bounded_revision_not_overcalled_as_abrupt_reorientation() -> None:
    result = _run_case(
        "bounded-not-abrupt",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(
                change_id="chg1",
                change_kind=N02SubstrateChangeKind.ABRUPT_INCOMPATIBLE_REPLACEMENT,
                magnitude_hint=0.78,
                confidence=0.4,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.BOUNDED_REVISION


def test_consumer_packets_expose_refs_region_kind_need_scope_non_claims() -> None:
    result = _run_case(
        "consumer-view",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.LOCAL_REVISION),),
    )
    packet = derive_n02_consumer_packets(result)[0]
    assert packet.baseline_reference_id == "b1"
    assert packet.current_reference_id == "c1"
    assert packet.affected_identity_region == N02IdentityRegionKind.SELF_DESCRIPTION.value
    assert packet.reflection_need_level in {"low", "moderate", "high", "none"}
    assert "does_not_rewrite_commitments" in packet.non_claim_constraints


def test_substrate_ablation_degrades_to_no_clean_not_text_only_drift() -> None:
    result = _run_case(
        "substrate-ablation",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(n02_change(change_id="chg1", change_kind=N02SubstrateChangeKind.UNKNOWN),),
    )
    assert result.drift_entries[0].drift_kind is N02DriftKind.NO_CLEAN_DRIFT_CLAIM
    assert "substrate_missing_or_ablation" in result.drift_entries[0].reason_codes


def test_silent_rewrite_scenario_not_reported_as_stable_continuation() -> None:
    result = _run_case(
        "silent-rewrite",
        baselines=(n02_baseline(baseline_id="b1"),),
        currents=(n02_current(current_reference_id="c1"),),
        changes=(
            n02_change(
                change_id="chg1",
                change_kind=N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION,
                magnitude_hint=0.9,
            ),
            n02_change(
                change_id="chg2",
                change_kind=N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION,
                magnitude_hint=0.85,
            ),
        ),
    )
    assert result.drift_entries[0].drift_kind is not N02DriftKind.STABLE_CONTINUATION
    assert result.drift_entries[0].drift_kind in {
        N02DriftKind.CONTRADICTION_DRIVEN_FRACTURE,
        N02DriftKind.UNRESOLVED_IDENTITY_TENSION,
    }


def test_competing_valid_baselines_resolve_deterministically_and_are_traceable() -> None:
    exact_scope = n02_baseline(
        baseline_id="baseline:exact",
        time_scope="context:analysis",
        confidence=0.62,
    )
    global_scope = n02_baseline(
        baseline_id="baseline:global",
        time_scope="global",
        confidence=0.95,
    )
    first_order = _run_case(
        "baseline-competing-order-a",
        baselines=(global_scope, exact_scope),
        currents=(n02_current(current_reference_id="c1", context_scope="context:analysis"),),
    )
    second_order = _run_case(
        "baseline-competing-order-b",
        baselines=(exact_scope, global_scope),
        currents=(n02_current(current_reference_id="c1", context_scope="context:analysis"),),
    )
    assert first_order.drift_entries[0].baseline_reference_id == "baseline:exact"
    assert second_order.drift_entries[0].baseline_reference_id == "baseline:exact"
    assert first_order.drift_entries[0].drift_kind is N02DriftKind.STABLE_CONTINUATION
    assert second_order.drift_entries[0].drift_kind is N02DriftKind.STABLE_CONTINUATION


def test_mixed_baseline_validity_does_not_launder_contested_baseline_into_clean_selection() -> None:
    contested_exact = n02_baseline(
        baseline_id="baseline:contested",
        time_scope="context:analysis",
        validity_status=N02BaselineValidityStatus.CONTESTED,
        confidence=0.96,
    )
    valid_global = n02_baseline(
        baseline_id="baseline:valid",
        time_scope="global",
        validity_status=N02BaselineValidityStatus.VALID,
        confidence=0.7,
    )
    result = _run_case(
        "baseline-mixed-validity",
        baselines=(contested_exact, valid_global),
        currents=(n02_current(current_reference_id="c1", context_scope="context:analysis"),),
    )
    entry = result.drift_entries[0]
    assert entry.baseline_reference_id == "baseline:valid"
    assert entry.drift_kind is N02DriftKind.STABLE_CONTINUATION
    assert "baseline_uncertain" not in entry.reason_codes
