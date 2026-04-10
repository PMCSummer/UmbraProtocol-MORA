from __future__ import annotations

from substrate.s01_efference_copy import S01ComparisonAxis
from substrate.s02_prediction_boundary import (
    S02BoundaryStatus,
    derive_s02_boundary_contract_view,
    derive_s02_boundary_consumer_view,
    s02_prediction_boundary_snapshot,
)
from tests.substrate.s01_efference_copy_testkit import build_s01
from tests.substrate.s02_prediction_boundary_testkit import build_s02


def _s01_observed(
    case_id: str,
    *,
    tick_index: int,
    emit_world_action_candidate: bool,
    world_effect_feedback_correlated: bool,
):
    seed = build_s01(
        case_id=f"{case_id}-seed-{tick_index}",
        tick_index=tick_index,
        emit_world_action_candidate=emit_world_action_candidate,
        world_effect_feedback_correlated=False,
    )
    observed = build_s01(
        case_id=f"{case_id}-obs-{tick_index+1}",
        tick_index=tick_index + 1,
        emit_world_action_candidate=emit_world_action_candidate,
        world_effect_feedback_correlated=world_effect_feedback_correlated,
        prior_state=seed.state,
    )
    return observed


def _entry(result, channel: str):
    for item in result.state.seam_entries:
        if item.channel_or_effect_class == channel:
            return item
    raise AssertionError(f"channel {channel} not found")


def test_s02_contrast_predictability_vs_controllability_is_explicit() -> None:
    controllable_s01 = _s01_observed(
        "contrast-controllable",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    predictable_s01 = _s01_observed(
        "contrast-predictable",
        tick_index=1,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    controllable = build_s02(
        case_id="contrast-controllable",
        tick_index=2,
        s01_result=controllable_s01,
        effector_available=True,
    )
    predictable = build_s02(
        case_id="contrast-predictable",
        tick_index=2,
        s01_result=predictable_s01,
        effector_available=False,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    controllable_entry = _entry(controllable, channel)
    predictable_entry = _entry(predictable, channel)
    assert controllable_entry.prediction_reliability_estimate == predictable_entry.prediction_reliability_estimate
    assert controllable_entry.controllability_estimate > predictable_entry.controllability_estimate


def test_s02_repeated_evidence_aggregation_strengthens_local_seam() -> None:
    first_observed = _s01_observed(
        "aggregation",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    first = build_s02(
        case_id="aggregation",
        tick_index=2,
        s01_result=first_observed,
        effector_available=True,
    )
    second_observed = _s01_observed(
        "aggregation",
        tick_index=3,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    second = build_s02(
        case_id="aggregation",
        tick_index=4,
        s01_result=second_observed,
        effector_available=True,
        prior_state=first.state,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    first_entry = _entry(first, channel)
    second_entry = _entry(second, channel)
    assert first_entry.evidence_counters.repeated_outcome_support <= 2
    assert second_entry.evidence_counters.repeated_outcome_support > first_entry.evidence_counters.repeated_outcome_support
    assert second_entry.boundary_confidence >= first_entry.boundary_confidence


def test_s02_mixed_source_boundary_is_preserved_in_adversarial_mix() -> None:
    internal_observed = _s01_observed(
        "mixed-source",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    first = build_s02(
        case_id="mixed-source",
        tick_index=2,
        s01_result=internal_observed,
        effector_available=True,
    )
    external_observed = build_s01(
        case_id="mixed-source-external-3",
        tick_index=3,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=True,
        prior_state=None,
    )
    mixed = build_s02(
        case_id="mixed-source",
        tick_index=4,
        s01_result=external_observed,
        effector_available=True,
        prior_state=first.state,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    mixed_entry = _entry(mixed, channel)
    assert mixed_entry.mixed_source_score > 0.0
    assert mixed_entry.boundary_status in {
        S02BoundaryStatus.MIXED_SOURCE_BOUNDARY,
        S02BoundaryStatus.BOUNDARY_UNCERTAIN,
    }


def test_s02_predictable_but_not_self_driven_status_is_available() -> None:
    observed = _s01_observed(
        "predictable-not-self",
        tick_index=1,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    first = build_s02(
        case_id="predictable-not-self",
        tick_index=2,
        s01_result=observed,
        effector_available=False,
    )
    second_observed = _s01_observed(
        "predictable-not-self",
        tick_index=3,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    second = build_s02(
        case_id="predictable-not-self",
        tick_index=4,
        s01_result=second_observed,
        effector_available=False,
        prior_state=first.state,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    entry = _entry(second, channel)
    assert entry.boundary_status is S02BoundaryStatus.PREDICTABLE_BUT_NOT_SELF_DRIVEN


def test_s02_context_shift_or_effector_loss_invalidates_prior_self_side_seam() -> None:
    observed = _s01_observed(
        "context-shift",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    strong = build_s02(
        case_id="context-shift",
        tick_index=2,
        s01_result=observed,
        effector_available=True,
    )
    shifted = build_s02(
        case_id="context-shift",
        tick_index=3,
        s01_result=observed,
        effector_available=False,
        context_shift_detected=True,
        prior_state=strong.state,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    shifted_entry = _entry(shifted, channel)
    assert shifted_entry.boundary_status is S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT


def test_s02_stale_boundary_requires_revalidation_and_does_not_stay_strong() -> None:
    observed = _s01_observed(
        "stale",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    strong = build_s02(
        case_id="stale",
        tick_index=2,
        s01_result=observed,
        effector_available=True,
    )
    stale = build_s02(
        case_id="stale",
        tick_index=3,
        s01_result=observed,
        effector_available=True,
        c05_revalidation_required=True,
        prior_state=strong.state,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    stale_entry = _entry(stale, channel)
    assert stale_entry.boundary_status is S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT
    assert "stale_seam_carried_without_revalidation" not in stale.gate.forbidden_shortcuts


def test_s02_ablation_without_controllability_signal_collapses_self_side_claim() -> None:
    observed = _s01_observed(
        "ablation",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    strong = build_s02(
        case_id="ablation",
        tick_index=2,
        s01_result=observed,
        effector_available=True,
    )
    ablated = build_s02(
        case_id="ablation",
        tick_index=2,
        s01_result=observed,
        effector_available=True,
        controllability_sensitive_signal_enabled=False,
        aggregation_enabled=False,
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    strong_entry = _entry(strong, channel)
    ablated_entry = _entry(ablated, channel)
    assert strong_entry.controllability_estimate > ablated_entry.controllability_estimate
    assert ablated_entry.boundary_status is not S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM


def test_s02_manual_map_baseline_fails_mixed_and_context_sensitive_cases() -> None:
    observed = _s01_observed(
        "manual-map",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    lawful = build_s02(
        case_id="manual-map",
        tick_index=2,
        s01_result=observed,
        effector_available=False,
        context_shift_detected=True,
    )
    mapped = build_s02(
        case_id="manual-map",
        tick_index=2,
        s01_result=observed,
        effector_available=False,
        context_shift_detected=True,
        manual_channel_map={
            S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value: "inside_self_predictive_seam"
        },
    )
    channel = S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value
    lawful_entry = _entry(lawful, channel)
    mapped_entry = _entry(mapped, channel)
    assert lawful_entry.boundary_status is S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT
    assert mapped_entry.boundary_status is S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM
    assert "hardcoded_channel_self_world_map" in mapped.gate.forbidden_shortcuts


def test_s02_contract_view_snapshot_and_consumer_surface_are_inspectable() -> None:
    observed = _s01_observed(
        "snapshot",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    result = build_s02(
        case_id="snapshot",
        tick_index=2,
        s01_result=observed,
        effector_available=True,
    )
    view = derive_s02_boundary_contract_view(result)
    consumer = derive_s02_boundary_consumer_view(result)
    snapshot = s02_prediction_boundary_snapshot(result)
    assert view.boundary_id == result.state.boundary_id
    assert consumer.boundary_id == result.state.boundary_id
    assert snapshot["scope_marker"]["scope"] == "rt01_contour_only"
    assert snapshot["scope_marker"]["s03_implemented"] is False
