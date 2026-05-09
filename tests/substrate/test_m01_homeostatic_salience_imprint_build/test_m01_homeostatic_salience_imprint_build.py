from __future__ import annotations

from substrate.m01_homeostatic_salience_imprint import (
    M01AttributionStatus,
    M01ImprintDecisionType,
    M01LifecycleAdjustment,
    M01RegulatoryDirection,
    M01SignOfEffect,
    M01TemporalWindowStatus,
    derive_m01_consumer_packets,
)
from tests.substrate.m01_homeostatic_salience_imprint_testkit import (
    M01HarnessCase,
    build_m01_harness_case,
    m01_attribution,
    m01_bundle,
    m01_coupling,
    m01_delta,
    m01_trace,
)


def _run_single(
    case_id: str,
    *,
    trace_kwargs: dict | None = None,
    delta_kwargs: dict | None = None,
    coupling_status: M01TemporalWindowStatus = M01TemporalWindowStatus.WITHIN_WINDOW,
    attribution_status: M01AttributionStatus = M01AttributionStatus.SELF_RELEVANT,
    prior_imprints=(),
):
    trace = m01_trace(trace_id=f"{case_id}:trace", **(trace_kwargs or {}))
    deltas = ()
    coupling = ()
    if delta_kwargs is not None:
        delta = m01_delta(delta_id=f"{case_id}:delta", axis_id="axis:reg", **delta_kwargs)
        deltas = (delta,)
        coupling = (
            m01_coupling(
                trace_id=trace.trace_id,
                delta_refs=(delta.delta_id,),
                temporal_window_status=coupling_status,
            ),
        )
    attribution = (
        m01_attribution(trace_id=trace.trace_id, attribution_status=attribution_status),
    )
    bundle = m01_bundle(
        bundle_id=f"{case_id}:bundle",
        traces=(trace,),
        deltas=deltas,
        coupling=coupling,
        attribution=attribution,
        prior_imprints=prior_imprints,
        source_lineage=("tests.m01.owner", case_id),
        reason=case_id,
    )
    return build_m01_harness_case(M01HarnessCase(case_id=case_id, input_bundle=bundle)).m01_result


def test_owner_import_surface_and_init_integrity() -> None:
    from substrate.m01_homeostatic_salience_imprint import (
        M01InputBundle,
        M01Result,
        build_m01_homeostatic_salience_imprint,
        m01_homeostatic_salience_imprint_snapshot,
    )

    assert M01InputBundle is not None
    assert M01Result is not None
    assert callable(build_m01_homeostatic_salience_imprint)
    assert callable(m01_homeostatic_salience_imprint_snapshot)


def test_semantically_identical_traces_with_different_regulatory_delta_get_different_imprints() -> None:
    no_delta = _run_single("same-semantics-no-delta", delta_kwargs=None)
    with_delta = _run_single("same-semantics-strain", delta_kwargs={"intensity": 0.82})
    assert no_delta.imprint_packets[0].decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM
    assert with_delta.imprint_packets[0].decision is M01ImprintDecisionType.STRONG_STRAIN_IMPRINT


def test_novelty_without_regulatory_delta_does_not_create_strong_homeostatic_imprint() -> None:
    result = _run_single(
        "novelty-no-delta",
        trace_kwargs={"novelty_hint": 0.99},
        delta_kwargs=None,
    )
    assert result.imprint_packets[0].decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM


def test_recency_without_regulatory_delta_does_not_create_strong_homeostatic_imprint() -> None:
    result = _run_single(
        "recency-no-delta",
        trace_kwargs={"recency_hint": 0.99},
        delta_kwargs=None,
    )
    assert result.imprint_packets[0].decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM


def test_outcome_only_success_or_failure_is_insufficient_without_regulatory_linkage() -> None:
    success = _run_single(
        "outcome-success-no-delta",
        trace_kwargs={"outcome_hint": "success"},
        delta_kwargs=None,
    )
    failure = _run_single(
        "outcome-failure-no-delta",
        trace_kwargs={"outcome_hint": "failure"},
        delta_kwargs=None,
    )
    assert success.imprint_packets[0].decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM
    assert failure.imprint_packets[0].decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM


def test_temporal_coupling_out_of_window_blocks_or_downgrades_imprint() -> None:
    result = _run_single(
        "temporal-out-of-window",
        delta_kwargs={"intensity": 0.9},
        coupling_status=M01TemporalWindowStatus.OUT_OF_WINDOW,
    )
    assert result.imprint_packets[0].decision is M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT


def test_contested_timing_caps_strong_imprint() -> None:
    within = _run_single(
        "timing-within-strong",
        delta_kwargs={"intensity": 0.88},
        coupling_status=M01TemporalWindowStatus.WITHIN_WINDOW,
    )
    contested = _run_single(
        "timing-contested",
        delta_kwargs={"intensity": 0.88},
        coupling_status=M01TemporalWindowStatus.CONTESTED_TIMING,
    )
    strong_decisions = {
        M01ImprintDecisionType.STRONG_THREAT_IMPRINT,
        M01ImprintDecisionType.STRONG_STRAIN_IMPRINT,
        M01ImprintDecisionType.STRONG_RELIEF_IMPRINT,
        M01ImprintDecisionType.STRONG_RECOVERY_IMPRINT,
    }
    assert within.imprint_packets[0].decision in strong_decisions
    assert contested.imprint_packets[0].decision not in strong_decisions
    assert contested.imprint_packets[0].decision is M01ImprintDecisionType.WEAK_HOMEOSTATIC_LINK
    assert contested.imprint_packets[0].imprint_strength < within.imprint_packets[0].imprint_strength
    assert "contested_timing_cap" in contested.imprint_packets[0].reason_codes
    assert contested.imprint_packets[0].allowed_memory_use.must_not_treat_as_general_importance is True


def test_self_relevant_attribution_allows_stronger_imprint_than_externally_dominated_attribution() -> None:
    self_relevant = _run_single(
        "attr-self",
        delta_kwargs={"intensity": 0.8},
        attribution_status=M01AttributionStatus.SELF_RELEVANT,
    )
    external = _run_single(
        "attr-external",
        delta_kwargs={"intensity": 0.8},
        attribution_status=M01AttributionStatus.EXTERNALLY_DOMINATED,
    )
    assert self_relevant.imprint_packets[0].decision is M01ImprintDecisionType.STRONG_STRAIN_IMPRINT
    assert external.imprint_packets[0].decision is M01ImprintDecisionType.ATTRIBUTION_LIMITED_IMPRINT


def test_observation_artifact_risk_blocks_strong_imprint() -> None:
    result = _run_single(
        "artifact-risk",
        delta_kwargs={"intensity": 0.85},
        attribution_status=M01AttributionStatus.OBSERVATION_ARTIFACT_RISK,
    )
    assert result.imprint_packets[0].decision is M01ImprintDecisionType.ATTRIBUTION_LIMITED_IMPRINT


def test_relief_and_recovery_traces_receive_positive_memory_bias() -> None:
    relief = _run_single(
        "relief",
        delta_kwargs={
            "direction": M01RegulatoryDirection.IMPROVING,
            "intensity": 0.8,
            "deviation_before": 0.8,
            "deviation_after": 0.2,
        },
    )
    recovery = _run_single(
        "recovery",
        delta_kwargs={
            "direction": M01RegulatoryDirection.IMPROVING,
            "intensity": 0.82,
            "recovery_marker": True,
            "deviation_before": 0.7,
            "deviation_after": 0.2,
        },
    )
    assert relief.imprint_packets[0].decision is M01ImprintDecisionType.STRONG_RELIEF_IMPRINT
    assert recovery.imprint_packets[0].decision is M01ImprintDecisionType.STRONG_RECOVERY_IMPRINT
    assert relief.imprint_packets[0].retention_bias > 0.6
    assert recovery.imprint_packets[0].retention_bias > 0.6


def test_multi_axis_imprint_preserves_axis_structure() -> None:
    trace = m01_trace(trace_id="multi:trace")
    d1 = m01_delta(delta_id="multi:d1", axis_id="axis:energy", intensity=0.74)
    d2 = m01_delta(
        delta_id="multi:d2",
        axis_id="axis:safety",
        intensity=0.72,
        direction=M01RegulatoryDirection.IMPROVING,
    )
    bundle = m01_bundle(
        bundle_id="multi:bundle",
        traces=(trace,),
        deltas=(d1, d2),
        coupling=(m01_coupling(trace_id=trace.trace_id, delta_refs=(d1.delta_id, d2.delta_id)),),
        attribution=(m01_attribution(trace_id=trace.trace_id),),
        source_lineage=("tests.m01.owner", "multi"),
    )
    result = build_m01_harness_case(M01HarnessCase(case_id="multi-axis", input_bundle=bundle)).m01_result
    assert result.imprint_packets[0].decision is M01ImprintDecisionType.PROVISIONAL_MULTI_AXIS_IMPRINT
    assert result.imprint_packets[0].affected_axes == ("axis:energy", "axis:safety")


def test_mixed_axis_effect_does_not_collapse_to_single_importance_score() -> None:
    trace = m01_trace(trace_id="mixed:trace")
    d1 = m01_delta(
        delta_id="mixed:d1",
        axis_id="axis:energy",
        direction=M01RegulatoryDirection.WORSENING,
        intensity=0.72,
        deviation_before=0.2,
        deviation_after=0.8,
    )
    d2 = m01_delta(
        delta_id="mixed:d2",
        axis_id="axis:safety",
        direction=M01RegulatoryDirection.IMPROVING,
        intensity=0.7,
        deviation_before=0.8,
        deviation_after=0.3,
    )
    bundle = m01_bundle(
        bundle_id="mixed:bundle",
        traces=(trace,),
        deltas=(d1, d2),
        coupling=(m01_coupling(trace_id=trace.trace_id, delta_refs=(d1.delta_id, d2.delta_id)),),
        attribution=(m01_attribution(trace_id=trace.trace_id),),
        source_lineage=("tests.m01.owner", "mixed-axis"),
    )
    result = build_m01_harness_case(M01HarnessCase(case_id="mixed-axis", input_bundle=bundle)).m01_result
    assert result.imprint_packets[0].sign_of_effect is M01SignOfEffect.MIXED
    assert "multi_axis_mixed_effect" in result.imprint_packets[0].reason_codes


def test_repeated_structural_pattern_reinforces_with_transfer_limits() -> None:
    prior = _run_single("prior-pattern", delta_kwargs={"intensity": 0.7})
    reinforced = _run_single(
        "repeat-pattern",
        delta_kwargs={"intensity": 0.72},
        prior_imprints=prior.imprint_packets,
    )
    packet = reinforced.imprint_packets[0]
    assert packet.lifecycle_adjustment is M01LifecycleAdjustment.REINFORCE_EXISTING_IMPRINT
    assert "structural_similarity_required" in packet.transfer_limits


def test_non_overlapping_prior_imprint_does_not_trigger_reinforcement() -> None:
    prior_relief = _run_single(
        "prior-relief-for-non-overlap",
        delta_kwargs={
            "direction": M01RegulatoryDirection.IMPROVING,
            "intensity": 0.82,
            "deviation_before": 0.8,
            "deviation_after": 0.2,
        },
    )
    current_strain = _run_single(
        "current-strain-no-reinforce",
        delta_kwargs={
            "direction": M01RegulatoryDirection.WORSENING,
            "intensity": 0.82,
            "deviation_before": 0.2,
            "deviation_after": 0.85,
        },
        prior_imprints=prior_relief.imprint_packets,
    )
    packet = current_strain.imprint_packets[0]
    assert packet.lifecycle_adjustment is not M01LifecycleAdjustment.REINFORCE_EXISTING_IMPRINT
    assert "reinforcement_not_supported_by_overlap" in packet.reason_codes
    assert "structural_similarity_required" in packet.transfer_limits


def test_single_strong_event_does_not_overgeneralize_to_unrelated_context() -> None:
    result = _run_single("single-strong", delta_kwargs={"intensity": 0.9})
    packet = result.imprint_packets[0]
    assert "axis_scoped_only" in packet.transfer_limits
    assert packet.allowed_memory_use.must_not_treat_as_general_importance is True


def test_decay_without_reconfirmation_reduces_or_limits_imprint() -> None:
    prior = _run_single("decay-prior", delta_kwargs={"intensity": 0.76})
    decayed = _run_single("decay-now", delta_kwargs=None, prior_imprints=prior.imprint_packets)
    assert decayed.imprint_packets[0].lifecycle_adjustment is M01LifecycleAdjustment.DECAY_WITHOUT_RECONFIRMATION


def test_downstream_consumer_uses_imprint_packet_not_novelty_or_recency() -> None:
    novelty_only = _run_single(
        "consumer-novelty-only",
        trace_kwargs={"novelty_hint": 0.99, "recency_hint": 0.99},
        delta_kwargs=None,
    )
    strain = _run_single(
        "consumer-strain",
        trace_kwargs={"novelty_hint": 0.2, "recency_hint": 0.2},
        delta_kwargs={"intensity": 0.8},
    )
    novelty_packets = derive_m01_consumer_packets(novelty_only)
    strain_packets = derive_m01_consumer_packets(strain)
    assert novelty_packets[0].imprint_strength == 0.0
    assert strain_packets[0].imprint_strength > novelty_packets[0].imprint_strength
    assert strain_packets[0].retention_bias > novelty_packets[0].retention_bias


def test_downstream_consumer_view_exposes_axes_and_transfer_limits() -> None:
    result = _run_single("consumer-axes-transfer", delta_kwargs={"intensity": 0.78})
    packet = result.imprint_packets[0]
    consumer = derive_m01_consumer_packets(result)[0]
    assert consumer.affected_axes == packet.affected_axes
    assert consumer.transfer_limits == packet.transfer_limits
    assert consumer.affected_axes == ("axis:reg",)
    assert len(consumer.transfer_limits) > 0
    assert consumer.must_not_treat_as_general_importance is True


def test_no_claim_states_are_first_class_outputs() -> None:
    result = _run_single("no-claim", delta_kwargs=None)
    assert result.gate.no_safe_imprint_claim is True
    assert result.scope_marker.not_reward_function is True
    assert result.scope_marker.not_narrative_relevance is True
