from __future__ import annotations

from substrate.m02_predictive_relevance.models import (
    M02GateDecision,
    M02InputBundle,
    M02LedgerEntry,
    M02PredictiveFeedback,
    M02PredictiveLifecycleAdjustment,
    M02PredictiveRelevanceDecision,
    M02PredictiveRelevanceMark,
    M02PredictionTarget,
    M02Result,
    M02ScopeMarker,
    M02Telemetry,
    M02UtilityHorizon,
)


def build_m02_predictive_relevance(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: M02InputBundle | None,
    relevance_enabled: bool = True,
) -> M02Result:
    if not relevance_enabled:
        return _minimal_result(
            bundle_id=f"m02:{tick_id}:bundle:none",
            reason="M02 gate disabled in test fixture",
            restrictions=("m02_disabled", "m02_no_safe_predictive_mark"),
        )

    if not isinstance(input_bundle, M02InputBundle):
        return _minimal_result(
            bundle_id=f"m02:{tick_id}:bundle:none",
            reason=(
                "m02 requires typed trace/target/feedback input and does not treat repetition, novelty, "
                "vividness, outcome labels, or homeostatic imprint strength as predictive relevance by themselves"
            ),
            restrictions=("insufficient_m02_basis", "m02_no_safe_predictive_mark"),
        )

    if not input_bundle.traces:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="m02 received no traces and preserves explicit no-safe-predictive-mark state",
            restrictions=("m02_no_trace_input", "m02_no_safe_predictive_mark"),
        )

    targets_by_id = {item.target_id: item for item in input_bundle.prediction_targets}
    feedback_by_trace: dict[str, list[M02PredictiveFeedback]] = {}
    for item in input_bundle.predictive_feedback:
        feedback_by_trace.setdefault(item.trace_id, []).append(item)

    marks: list[M02PredictiveRelevanceMark] = []
    ledger: list[M02LedgerEntry] = []
    clean_count = 0
    weak_count = 0
    context_locked_count = 0
    spurious_count = 0
    no_safe_count = 0

    for trace in input_bundle.traces:
        mark, record = _evaluate_trace(
            tick_id=tick_id,
            tick_index=tick_index,
            trace=trace,
            feedback=tuple(feedback_by_trace.get(trace.trace_id, [])),
            targets_by_id=targets_by_id,
            source_lineage=input_bundle.source_lineage,
        )
        marks.append(mark)
        ledger.append(record)

        if mark.decision in {
            M02PredictiveRelevanceDecision.STRONG_BORING_PREDICTOR,
            M02PredictiveRelevanceDecision.REPEATED_WEAK_PREDICTOR,
        }:
            clean_count += 1
        if mark.decision in {
            M02PredictiveRelevanceDecision.WEAK_PREDICTIVE_SUPPORT,
            M02PredictiveRelevanceDecision.INSUFFICIENT_REPETITION,
            M02PredictiveRelevanceDecision.PROVISIONAL_PREDICTOR,
        }:
            weak_count += 1
        if mark.decision is M02PredictiveRelevanceDecision.CONTEXT_LOCKED_PREDICTOR:
            context_locked_count += 1
        if mark.decision is M02PredictiveRelevanceDecision.SPURIOUS_PATTERN_RISK:
            spurious_count += 1
        if mark.decision in {
            M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK,
            M02PredictiveRelevanceDecision.TARGET_UNCERTAIN,
        }:
            no_safe_count += 1

    consumer_ready = clean_count > 0 and spurious_count == 0 and no_safe_count == 0
    telemetry = M02Telemetry(
        trace_count=len(input_bundle.traces),
        predictive_mark_count=len(marks),
        clean_predictive_mark_count=clean_count,
        weak_mark_count=weak_count,
        context_locked_count=context_locked_count,
        spurious_risk_count=spurious_count,
        no_safe_mark_count=no_safe_count,
        consumer_ready=consumer_ready,
    )
    gate = _build_gate(telemetry=telemetry, marks=tuple(marks))

    return M02Result(
        bundle_id=input_bundle.bundle_id,
        predictive_marks=tuple(marks),
        ledger=tuple(ledger),
        telemetry=telemetry,
        gate=gate,
        scope_marker=M02ScopeMarker(
            scope="frontier_hosted_m02_predictive_relevance_slice",
            frontier_only=True,
            narrow_slice_only=True,
            predictive_relevance_not_generic_importance=True,
            no_full_prediction_claim=True,
            no_full_memory_lifecycle_claim=True,
            no_planner_policy_claim=True,
            separate_from_homeostatic_imprint=True,
            reason=(
                "m02 emits bounded target-linked predictive relevance marks for useful-but-boring traces and "
                "does not claim generic importance, full prediction, or full memory lifecycle authority"
            ),
        ),
        reason="m02 produced typed predictive relevance marks",
    )


def _evaluate_trace(
    *,
    tick_id: str,
    tick_index: int,
    trace,
    feedback: tuple[M02PredictiveFeedback, ...],
    targets_by_id: dict[str, M02PredictionTarget],
    source_lineage: tuple[str, ...],
) -> tuple[M02PredictiveRelevanceMark, M02LedgerEntry]:
    reason_codes: list[str] = []
    anti_spurious_limits = [
        "target_link_required",
        "context_scope_preserved",
        "must_not_treat_as_generic_importance",
        "no_full_prediction_claim",
        "no_full_memory_lifecycle_claim",
    ]

    valid_target_refs = tuple(
        dict.fromkeys(item.target_id for item in feedback if item.target_id in targets_by_id)
    )
    target_types = tuple(
        dict.fromkeys(targets_by_id[item].target_type for item in valid_target_refs)
    )
    if valid_target_refs:
        horizons = [targets_by_id[item].utility_horizon for item in valid_target_refs]
        utility_horizon = (
            horizons[0]
            if len(set(horizons)) == 1
            else M02UtilityHorizon.UNKNOWN
        )
    else:
        utility_horizon = M02UtilityHorizon.UNKNOWN

    total_gain = sum(item.prediction_gain for item in feedback)
    avg_gain = total_gain / len(feedback) if feedback else 0.0
    corroboration_count = sum(max(0, item.corroboration_count) for item in feedback)
    failed_transfer_count = sum(max(0, item.failed_transfer_count) for item in feedback)
    max_spurious_risk = max((item.spurious_risk_score for item in feedback), default=0.0)
    context_locked = any(item.context_locked for item in feedback)
    attribution_noise = any(item.attribution_noise_risk for item in feedback)
    confidence = (
        sum(item.confidence for item in feedback) / len(feedback)
        if feedback
        else 0.2
    )

    if not feedback:
        decision = M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK
        lifecycle = M02PredictiveLifecycleAdjustment.NO_REINFORCEMENT_WITHOUT_GAIN
        strength = 0.0
        reason_codes.append("no_predictive_feedback")
    elif not valid_target_refs:
        decision = M02PredictiveRelevanceDecision.TARGET_UNCERTAIN
        lifecycle = M02PredictiveLifecycleAdjustment.KEEP_PROVISIONAL_UNTIL_CORROBORATED
        strength = 0.15
        reason_codes.append("target_uncertain")
    elif max_spurious_risk >= 0.65 or attribution_noise:
        decision = M02PredictiveRelevanceDecision.SPURIOUS_PATTERN_RISK
        lifecycle = M02PredictiveLifecycleAdjustment.SUPPRESS_DUE_TO_SPURIOUS_RISK
        strength = min(0.35, max(avg_gain, 0.0))
        reason_codes.append("spurious_pattern_risk")
    elif avg_gain <= 0.0:
        decision = M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK
        lifecycle = M02PredictiveLifecycleAdjustment.NO_REINFORCEMENT_WITHOUT_GAIN
        strength = 0.0
        reason_codes.append("no_predictive_gain")
    elif corroboration_count < 2:
        decision = M02PredictiveRelevanceDecision.INSUFFICIENT_REPETITION
        lifecycle = M02PredictiveLifecycleAdjustment.KEEP_PROVISIONAL_UNTIL_CORROBORATED
        strength = min(0.45, avg_gain)
        reason_codes.append("insufficient_repetition")
    elif context_locked:
        decision = M02PredictiveRelevanceDecision.CONTEXT_LOCKED_PREDICTOR
        lifecycle = M02PredictiveLifecycleAdjustment.NARROW_SCOPE_DUE_TO_CONTEXT_LOCK
        strength = min(0.68, avg_gain + 0.1)
        anti_spurious_limits.append("context_locked_only")
        reason_codes.append("context_locked_predictor")
    elif failed_transfer_count > 0:
        decision = M02PredictiveRelevanceDecision.WEAK_PREDICTIVE_SUPPORT
        lifecycle = M02PredictiveLifecycleAdjustment.DECAY_AFTER_FAILED_TRANSFER
        strength = min(0.55, avg_gain)
        anti_spurious_limits.append("failed_transfer_decay")
        reason_codes.append("failed_transfer_decay")
    elif avg_gain >= 0.62 and trace.boredom_level >= 0.55:
        decision = M02PredictiveRelevanceDecision.STRONG_BORING_PREDICTOR
        lifecycle = M02PredictiveLifecycleAdjustment.REINFORCE_AFTER_REPLICATION
        strength = min(1.0, avg_gain + 0.15)
        reason_codes.append("boring_predictive_signal")
    elif avg_gain >= 0.45:
        decision = M02PredictiveRelevanceDecision.REPEATED_WEAK_PREDICTOR
        lifecycle = M02PredictiveLifecycleAdjustment.REINFORCE_AFTER_REPLICATION
        strength = min(0.78, avg_gain + 0.08)
        reason_codes.append("repeated_weak_predictive_signal")
    else:
        decision = M02PredictiveRelevanceDecision.PROVISIONAL_PREDICTOR
        lifecycle = M02PredictiveLifecycleAdjustment.KEEP_PROVISIONAL_UNTIL_CORROBORATED
        strength = min(0.5, avg_gain)
        reason_codes.append("weak_predictive_support")

    if trace.homeostatic_strength_hint is not None:
        reason_codes.append("m01_strength_not_primary_predictive_basis")
    if trace.vividness_level > 0.75 and avg_gain < 0.25:
        reason_codes.append("vividness_not_predictive_gain")
    if utility_horizon is M02UtilityHorizon.UNKNOWN:
        anti_spurious_limits.append("horizon_unknown_no_generalization")

    mark = M02PredictiveRelevanceMark(
        predictive_mark_id=f"m02:{tick_id}:{tick_index}:mark:{trace.trace_id}",
        source_trace_id=trace.trace_id,
        predicted_target_types=target_types,
        decision=decision,
        relevance_strength=round(max(0.0, min(1.0, strength)), 4),
        utility_horizon=utility_horizon,
        context_scope=trace.context_scope,
        corroboration_count=corroboration_count,
        anti_spurious_limits=tuple(dict.fromkeys(anti_spurious_limits)),
        retrieval_bias=round(min(1.0, 0.15 + max(0.0, strength) * 0.7), 4),
        retention_bias=round(min(1.0, 0.12 + max(0.0, strength) * 0.68), 4),
        replay_priority=round(min(1.0, 0.1 + max(0.0, strength) * 0.72), 4),
        indexing_bias=round(min(1.0, 0.14 + max(0.0, strength) * 0.66), 4),
        planning_support_recall_bias=round(min(1.0, 0.1 + max(0.0, strength) * 0.65), 4),
        confidence=round(max(0.0, min(1.0, confidence)), 4),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        lifecycle_adjustment=lifecycle,
        must_preserve_context=True,
        must_not_generalize=(
            decision
            in {
                M02PredictiveRelevanceDecision.CONTEXT_LOCKED_PREDICTOR,
                M02PredictiveRelevanceDecision.SPURIOUS_PATTERN_RISK,
                M02PredictiveRelevanceDecision.TARGET_UNCERTAIN,
                M02PredictiveRelevanceDecision.NO_SAFE_PREDICTIVE_MARK,
            }
            or utility_horizon is M02UtilityHorizon.UNKNOWN
        ),
        must_not_treat_as_generic_importance=True,
        provenance=tuple(dict.fromkeys((*source_lineage, trace.trace_id))),
    )
    record = M02LedgerEntry(
        entry_id=f"m02:{tick_id}:{tick_index}:ledger:{trace.trace_id}",
        trace_id=trace.trace_id,
        target_refs=valid_target_refs,
        decision=decision,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        utility_gain=round(avg_gain, 4),
        anti_spurious_result="elevated" if max_spurious_risk >= 0.65 else "bounded",
        utility_horizon=utility_horizon,
        context_scope=trace.context_scope,
        lifecycle_adjustment=lifecycle,
    )
    return mark, record


def _build_gate(
    *,
    telemetry: M02Telemetry,
    marks: tuple[M02PredictiveRelevanceMark, ...],
) -> M02GateDecision:
    restrictions: list[str] = []
    reason_codes: list[str] = []
    if telemetry.no_safe_mark_count > 0:
        restrictions.append("m02_no_safe_predictive_mark")
        reason_codes.append("no_safe_predictive_mark")
    if telemetry.spurious_risk_count > 0:
        restrictions.append("m02_spurious_pattern_risk")
        reason_codes.append("spurious_pattern_risk")
    if telemetry.context_locked_count > 0:
        restrictions.append("m02_context_locked_predictor")
        reason_codes.append("context_locked_predictor")

    predictive_packet_ready = any(
        item.decision
        in {
            M02PredictiveRelevanceDecision.STRONG_BORING_PREDICTOR,
            M02PredictiveRelevanceDecision.REPEATED_WEAK_PREDICTOR,
            M02PredictiveRelevanceDecision.CONTEXT_LOCKED_PREDICTOR,
            M02PredictiveRelevanceDecision.PROVISIONAL_PREDICTOR,
        }
        for item in marks
    )
    context_scope_ready = all(item.must_preserve_context for item in marks) if marks else False
    consumer_ready = bool(
        predictive_packet_ready
        and context_scope_ready
        and telemetry.no_safe_mark_count == 0
        and telemetry.spurious_risk_count == 0
    )
    if not consumer_ready:
        restrictions.append("m02_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    return M02GateDecision(
        consumer_ready=consumer_ready,
        predictive_packet_consumer_ready=predictive_packet_ready,
        context_scope_consumer_ready=context_scope_ready,
        clean_predictive_mark_count=telemetry.clean_predictive_mark_count,
        weak_mark_count=telemetry.weak_mark_count,
        context_locked_count=telemetry.context_locked_count,
        spurious_risk_count=telemetry.spurious_risk_count,
        no_safe_mark_count=telemetry.no_safe_mark_count,
        downstream_must_preserve_context=True,
        downstream_must_not_generalize=any(item.must_not_generalize for item in marks) if marks else True,
        downstream_must_not_treat_as_generic_importance=True,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="m02 gate preserves target-linked predictive relevance discipline",
    )


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> M02Result:
    telemetry = M02Telemetry(
        trace_count=0,
        predictive_mark_count=0,
        clean_predictive_mark_count=0,
        weak_mark_count=0,
        context_locked_count=0,
        spurious_risk_count=0,
        no_safe_mark_count=1,
        consumer_ready=False,
    )
    gate = M02GateDecision(
        consumer_ready=False,
        predictive_packet_consumer_ready=False,
        context_scope_consumer_ready=False,
        clean_predictive_mark_count=0,
        weak_mark_count=0,
        context_locked_count=0,
        spurious_risk_count=0,
        no_safe_mark_count=1,
        downstream_must_preserve_context=True,
        downstream_must_not_generalize=True,
        downstream_must_not_treat_as_generic_importance=True,
        required_restrictions=restrictions,
        reason_codes=("no_safe_predictive_mark",),
        reason=reason,
    )
    return M02Result(
        bundle_id=bundle_id,
        predictive_marks=(),
        ledger=(),
        telemetry=telemetry,
        gate=gate,
        scope_marker=M02ScopeMarker(
            scope="frontier_hosted_m02_predictive_relevance_slice",
            frontier_only=True,
            narrow_slice_only=True,
            predictive_relevance_not_generic_importance=True,
            no_full_prediction_claim=True,
            no_full_memory_lifecycle_claim=True,
            no_planner_policy_claim=True,
            separate_from_homeostatic_imprint=True,
            reason=reason,
        ),
        reason=reason,
    )
