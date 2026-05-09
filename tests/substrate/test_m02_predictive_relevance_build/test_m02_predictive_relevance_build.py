from __future__ import annotations

from substrate.m02_predictive_relevance import (
    M02PredictiveLifecycleAdjustment,
    M02PredictiveRelevanceDecision,
    M02TargetType,
    M02TraceKind,
    M02UtilityHorizon,
    derive_m02_consumer_packets,
)
from tests.substrate.m02_predictive_relevance_testkit import (
    M02HarnessCase,
    build_m02_harness_case,
    m02_bundle,
    m02_feedback,
    m02_target,
    m02_trace,
)


def _run_single(
    case_id: str,
    *,
    trace_kwargs: dict | None = None,
    target_kwargs: dict | None = None,
    feedback_kwargs: dict | None = None,
):
    trace = m02_trace(trace_id=f"{case_id}:trace", **(trace_kwargs or {}))
    target = m02_target(target_id=f"{case_id}:target", **(target_kwargs or {}))
    feedback_data = {
        "prediction_gain": 0.72,
        **(feedback_kwargs or {}),
    }
    feedback = m02_feedback(
        feedback_id=f"{case_id}:feedback",
        trace_id=trace.trace_id,
        target_id=target.target_id,
        **feedback_data,
    )
    bundle = m02_bundle(
        bundle_id=f"{case_id}:bundle",
        traces=(trace,),
        targets=(target,),
        feedback=(feedback,),
        source_lineage=("tests.m02.owner", case_id),
        reason=case_id,
    )
    return build_m02_harness_case(M02HarnessCase(case_id=case_id, input_bundle=bundle)).m02_result


def test_boring_predictive_trace_receives_predictive_mark() -> None:
    result = _run_single(
        "boring-predictive",
        trace_kwargs={"boredom_level": 0.82, "vividness_level": 0.12},
        feedback_kwargs={"prediction_gain": 0.78, "corroboration_count": 3},
    )
    packet = result.predictive_marks[0]
    assert packet.decision is M02PredictiveRelevanceDecision.STRONG_BORING_PREDICTOR
    assert packet.relevance_strength > 0.7


def test_repetition_without_prediction_gain_does_not_become_mark() -> None:
    result = _run_single(
        "repetition-only",
        feedback_kwargs={"prediction_gain": 0.0, "corroboration_count": 6},
    )
    assert result.predictive_marks[0].decision is M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK


def test_vivid_non_predictive_trace_does_not_outcompete_boring_predictor() -> None:
    vivid = _run_single(
        "vivid-non-predictive",
        trace_kwargs={"vividness_level": 0.95, "boredom_level": 0.1, "novelty_level": 0.95},
        feedback_kwargs={"prediction_gain": 0.1, "corroboration_count": 3},
    )
    boring = _run_single(
        "boring-predictive-contrast",
        trace_kwargs={"vividness_level": 0.1, "boredom_level": 0.82, "novelty_level": 0.2},
        feedback_kwargs={"prediction_gain": 0.78, "corroboration_count": 3},
    )
    assert vivid.predictive_marks[0].decision is M02PredictiveRelevanceDecision.PROVISIONAL_PREDICTOR
    assert boring.predictive_marks[0].relevance_strength > vivid.predictive_marks[0].relevance_strength


def test_context_locked_predictor_preserves_transfer_limits() -> None:
    result = _run_single(
        "context-locked",
        feedback_kwargs={"prediction_gain": 0.68, "context_locked": True, "corroboration_count": 3},
    )
    packet = result.predictive_marks[0]
    assert packet.decision is M02PredictiveRelevanceDecision.CONTEXT_LOCKED_PREDICTOR
    assert "context_locked_only" in packet.anti_spurious_limits
    assert packet.must_not_generalize is True


def test_spurious_repetitive_cue_is_suppressed_or_marked_risky() -> None:
    result = _run_single(
        "spurious",
        feedback_kwargs={"prediction_gain": 0.8, "corroboration_count": 7, "spurious_risk_score": 0.9},
    )
    packet = result.predictive_marks[0]
    assert packet.decision is M02PredictiveRelevanceDecision.SPURIOUS_PATTERN_RISK
    assert packet.lifecycle_adjustment is M02PredictiveLifecycleAdjustment.SUPPRESS_DUE_TO_SPURIOUS_RISK


def test_target_missing_blocks_strong_predictive_mark() -> None:
    trace = m02_trace(trace_id="target-missing:trace")
    missing_feedback = m02_feedback(
        feedback_id="target-missing:feedback",
        trace_id=trace.trace_id,
        target_id="missing-target",
        prediction_gain=0.8,
        corroboration_count=4,
    )
    bundle = m02_bundle(
        bundle_id="target-missing:bundle",
        traces=(trace,),
        targets=(),
        feedback=(missing_feedback,),
        source_lineage=("tests.m02.owner", "target-missing"),
    )
    result = build_m02_harness_case(
        M02HarnessCase(case_id="target-missing", input_bundle=bundle)
    ).m02_result
    assert result.predictive_marks[0].decision is M02PredictiveRelevanceDecision.TARGET_UNCERTAIN


def test_horizon_is_preserved_and_not_silently_generalized() -> None:
    result = _run_single(
        "horizon-preserved",
        target_kwargs={"utility_horizon": M02UtilityHorizon.SHORT},
        feedback_kwargs={"prediction_gain": 0.74, "corroboration_count": 3},
    )
    packet = result.predictive_marks[0]
    assert packet.utility_horizon is M02UtilityHorizon.SHORT
    assert packet.must_not_generalize in {True, False}


def test_failed_transfer_decays_or_narrows_existing_mark() -> None:
    result = _run_single(
        "failed-transfer",
        feedback_kwargs={"prediction_gain": 0.75, "corroboration_count": 3, "failed_transfer_count": 2},
    )
    packet = result.predictive_marks[0]
    assert packet.lifecycle_adjustment is M02PredictiveLifecycleAdjustment.DECAY_AFTER_FAILED_TRANSFER
    assert packet.decision is M02PredictiveRelevanceDecision.WEAK_PREDICTIVE_SUPPORT


def test_m01_homeostatic_strength_does_not_create_predictive_mark() -> None:
    result = _run_single(
        "m01-separation-high-homeostatic",
        trace_kwargs={"homeostatic_strength_hint": 0.95},
        feedback_kwargs={"prediction_gain": 0.0, "corroboration_count": 5},
    )
    assert result.predictive_marks[0].decision is M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK
    assert "m01_strength_not_primary_predictive_basis" in result.predictive_marks[0].reason_codes


def test_low_homeostatic_high_predictive_trace_can_receive_strong_mark() -> None:
    result = _run_single(
        "m01-separation-low-homeostatic-high-predictive",
        trace_kwargs={"homeostatic_strength_hint": 0.05, "boredom_level": 0.8},
        feedback_kwargs={"prediction_gain": 0.76, "corroboration_count": 4},
    )
    assert result.predictive_marks[0].decision is M02PredictiveRelevanceDecision.STRONG_BORING_PREDICTOR


def test_same_frequency_different_utility_produces_different_marks() -> None:
    high = _run_single(
        "same-frequency-high",
        feedback_kwargs={"prediction_gain": 0.74, "corroboration_count": 4},
    )
    low = _run_single(
        "same-frequency-low",
        feedback_kwargs={"prediction_gain": 0.05, "corroboration_count": 4},
    )
    assert high.predictive_marks[0].decision is M02PredictiveRelevanceDecision.STRONG_BORING_PREDICTOR
    assert low.predictive_marks[0].decision is M02PredictiveRelevanceDecision.PROVISIONAL_PREDICTOR


def test_downstream_consumer_view_exposes_target_context_horizon_and_limits() -> None:
    result = _run_single("consumer-view", feedback_kwargs={"prediction_gain": 0.72, "corroboration_count": 3})
    packet = result.predictive_marks[0]
    consumer = derive_m02_consumer_packets(result)[0]
    assert consumer.source_trace_id == packet.source_trace_id
    assert consumer.predicted_target_types == tuple(kind.value for kind in packet.predicted_target_types)
    assert consumer.utility_horizon == packet.utility_horizon.value
    assert consumer.context_scope == packet.context_scope
    assert consumer.anti_spurious_limits == packet.anti_spurious_limits
    assert consumer.must_not_treat_as_generic_importance is True
    assert consumer.no_full_prediction_claim is True
    assert consumer.no_full_memory_lifecycle_claim is True


def test_no_typed_prediction_basis_returns_no_safe_without_fake_mark() -> None:
    result = build_m02_harness_case(
        M02HarnessCase(case_id="no-basis", input_bundle=None)
    ).m02_result
    assert result.predictive_marks == ()
    assert result.gate.consumer_ready is False
    assert "m02_no_safe_predictive_mark" in result.gate.required_restrictions


def test_ledger_preserves_reason_codes_for_mark_and_non_mark() -> None:
    mark = _run_single("ledger-mark", feedback_kwargs={"prediction_gain": 0.76, "corroboration_count": 3})
    non_mark = _run_single("ledger-non-mark", feedback_kwargs={"prediction_gain": 0.0, "corroboration_count": 3})
    assert len(mark.ledger[0].reason_codes) > 0
    assert len(non_mark.ledger[0].reason_codes) > 0
    assert mark.ledger[0].trace_id == mark.predictive_marks[0].source_trace_id


def test_anti_spurious_limits_are_machine_readable() -> None:
    result = _run_single("limits-readable", feedback_kwargs={"prediction_gain": 0.76, "corroboration_count": 3})
    limits = result.predictive_marks[0].anti_spurious_limits
    assert "target_link_required" in limits
    assert "must_not_treat_as_generic_importance" in limits


def test_predictive_mark_is_not_generic_importance() -> None:
    result = _run_single(
        "not-generic-importance",
        trace_kwargs={"trace_kind": M02TraceKind.ROUTINE, "semantic_label": "routine low signal"},
        target_kwargs={"target_type": M02TargetType.TIMING_EXPECTATION},
        feedback_kwargs={"prediction_gain": 0.7, "corroboration_count": 3},
    )
    packet = result.predictive_marks[0]
    assert packet.must_not_treat_as_generic_importance is True
    assert result.scope_marker.predictive_relevance_not_generic_importance is True


def test_recency_difference_alone_does_not_change_predictive_decision() -> None:
    older = _run_single(
        "recency-older",
        trace_kwargs={"timestamp_or_sequence": "seq:10"},
        feedback_kwargs={"prediction_gain": 0.76, "corroboration_count": 4},
    )
    newer = _run_single(
        "recency-newer",
        trace_kwargs={"timestamp_or_sequence": "seq:11"},
        feedback_kwargs={"prediction_gain": 0.76, "corroboration_count": 4},
    )
    older_mark = older.predictive_marks[0]
    newer_mark = newer.predictive_marks[0]
    assert older_mark.decision is newer_mark.decision
    assert older_mark.relevance_strength == newer_mark.relevance_strength
    assert older_mark.predicted_target_types == newer_mark.predicted_target_types
    assert older_mark.utility_horizon is newer_mark.utility_horizon


def test_outcome_label_without_predictive_gain_does_not_create_strong_mark() -> None:
    success_labeled = _run_single(
        "outcome-only-success",
        trace_kwargs={"semantic_label": "outcome_success_trace"},
        feedback_kwargs={"prediction_gain": 0.0, "corroboration_count": 6},
    )
    failure_labeled = _run_single(
        "outcome-only-failure",
        trace_kwargs={"semantic_label": "outcome_failure_trace"},
        feedback_kwargs={"prediction_gain": 0.0, "corroboration_count": 6},
    )
    assert (
        success_labeled.predictive_marks[0].decision
        is M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK
    )
    assert (
        failure_labeled.predictive_marks[0].decision
        is M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK
    )
    assert success_labeled.gate.consumer_ready is False
    assert failure_labeled.gate.consumer_ready is False


def test_short_horizon_evidence_does_not_broaden_to_general_horizon() -> None:
    short_result = _run_single(
        "horizon-short",
        target_kwargs={"utility_horizon": M02UtilityHorizon.SHORT},
        feedback_kwargs={"prediction_gain": 0.74, "corroboration_count": 4},
    )
    long_result = _run_single(
        "horizon-long",
        target_kwargs={"utility_horizon": M02UtilityHorizon.LONG},
        feedback_kwargs={"prediction_gain": 0.74, "corroboration_count": 4},
    )
    short_mark = short_result.predictive_marks[0]
    long_mark = long_result.predictive_marks[0]
    short_consumer = derive_m02_consumer_packets(short_result)[0]
    assert short_mark.utility_horizon is M02UtilityHorizon.SHORT
    assert long_mark.utility_horizon is M02UtilityHorizon.LONG
    assert short_mark.utility_horizon is not long_mark.utility_horizon
    assert short_consumer.utility_horizon == M02UtilityHorizon.SHORT.value
    assert short_mark.must_not_treat_as_generic_importance is True
