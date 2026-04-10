from __future__ import annotations

from substrate.s01_efference_copy.models import (
    S01AttributionStatus,
    S01ComparisonAxis,
    S01ComparisonEntry,
    S01ComparisonStatus,
    S01EfferenceCopyResult,
    S01EfferenceCopyState,
    S01ForwardModelPacket,
    S01GateDecision,
    S01ObservedWindow,
    S01Prediction,
    S01ScopeMarker,
    S01SourceKind,
    S01Telemetry,
)

_DEFAULT_MISMATCH_HOOKS: tuple[str, ...] = (
    S01ComparisonStatus.MAGNITUDE_MISMATCH.value,
    S01ComparisonStatus.DIRECTION_MISMATCH.value,
    S01ComparisonStatus.LATENCY_MISMATCH.value,
    S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED.value,
    S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED.value,
    S01ComparisonStatus.COMPARISON_BLOCKED_BY_CONTAMINATION.value,
)

_ACTIVE_WORLD_EFFECT_MODES = {
    "continue_stream",
    "run_recovery",
    "probe_alternatives",
    "prepare_output",
}


def build_s01_efference_copy(
    *,
    tick_id: str,
    tick_index: int,
    c04_selected_mode: str,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    c05_no_safe_reuse: bool,
    c05_revalidation_required: bool,
    c05_dependency_contaminated: bool,
    world_grounded_transition_admissible: bool,
    world_effect_feedback_correlated: bool,
    world_confidence: float | None,
    world_incomplete: bool,
    world_degraded: bool,
    emit_world_action_candidate: bool,
    prior_selected_mode: str | None = None,
    prior_state: S01EfferenceCopyState | None = None,
    source_lineage: tuple[str, ...] = (),
    register_prediction: bool = True,
) -> S01EfferenceCopyResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if tick_index < 1:
        raise ValueError("tick_index must be >= 1")

    observed = S01ObservedWindow(
        tick_index=tick_index,
        selected_mode=c04_selected_mode,
        mode_transition_detected=(
            bool(prior_selected_mode) and str(prior_selected_mode) != str(c04_selected_mode)
        ),
        world_grounded_transition_admissible=world_grounded_transition_admissible,
        world_effect_feedback_correlated=world_effect_feedback_correlated,
        world_confidence=world_confidence,
        contaminated=bool(
            c05_dependency_contaminated or c05_no_safe_reuse or world_incomplete or world_degraded
        ),
        incomplete=bool(world_incomplete or world_degraded),
        source_refs=(f"s01.observed@{tick_id}", f"c04:{c04_execution_mode_claim}", f"c05:{c05_validity_action}"),
    )

    prior_pending = ()
    if isinstance(prior_state, S01EfferenceCopyState):
        prior_pending = prior_state.pending_predictions

    comparisons: list[S01ComparisonEntry] = []
    pending_next: list[S01Prediction] = []
    stale_prediction_detected = False
    comparison_blocked_by_contamination = False
    unexpected_change_detected = False

    for prediction in prior_pending:
        if tick_index < prediction.earliest_tick:
            pending_next.append(prediction)
            continue
        entry = _compare_prediction(
            tick_id=tick_id,
            prediction=prediction,
            observed=observed,
            c05_revalidation_required=c05_revalidation_required,
        )
        comparisons.append(entry)
        if entry.status == S01ComparisonStatus.COMPARISON_BLOCKED_BY_CONTAMINATION:
            comparison_blocked_by_contamination = True
        if entry.status == S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED:
            stale_prediction_detected = True
        if entry.status == S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED:
            unexpected_change_detected = True
        if entry.status in {
            S01ComparisonStatus.PARTIAL_MATCH,
            S01ComparisonStatus.COMPARISON_BLOCKED_BY_CONTAMINATION,
        } and tick_index <= prediction.expires_tick:
            pending_next.append(prediction)

    if not prior_pending and observed.world_effect_feedback_correlated:
        comparisons.append(
            S01ComparisonEntry(
                comparison_id=f"cmp:{tick_id}:unexpected:world_effect_feedback",
                prediction_id=None,
                axis=S01ComparisonAxis.WORLD_EFFECT_FEEDBACK,
                status=S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED,
                attribution_status=S01AttributionStatus.MIXED_CAUSE_CONTAMINATED,
                observed_tick=tick_index,
                latency_ticks=None,
                magnitude_error=None,
                observed_direction=None,
                contamination_markers=("no_live_prediction",),
                reason="world effect feedback observed without live pre-observation efference copy",
            )
        )
        unexpected_change_detected = True

    forward_packets: list[S01ForwardModelPacket] = []
    if register_prediction:
        packet, predictions = _build_forward_packet_and_predictions(
            tick_id=tick_id,
            tick_index=tick_index,
            c04_selected_mode=c04_selected_mode,
            c04_execution_mode_claim=c04_execution_mode_claim,
            emit_world_action_candidate=emit_world_action_candidate,
            world_confidence=world_confidence,
        )
        forward_packets.append(packet)
        pending_next.extend(predictions)

    latest_status = comparisons[-1].status if comparisons else None
    prediction_validity_ready = not (
        stale_prediction_detected
        or c05_no_safe_reuse
        or c05_revalidation_required
        or comparison_blocked_by_contamination
    )
    restrictions = _derive_restrictions(
        comparison_blocked_by_contamination=comparison_blocked_by_contamination,
        stale_prediction_detected=stale_prediction_detected,
        unexpected_change_detected=unexpected_change_detected,
        c05_revalidation_required=c05_revalidation_required,
    )
    gate = S01GateDecision(
        comparison_ready=bool(comparisons),
        prediction_validity_ready=prediction_validity_ready,
        unexpected_change_detected=unexpected_change_detected,
        no_post_hoc_prediction_fabrication=True,
        restrictions=restrictions,
        reason=(
            "s01 compares live pending pre-observation expectations against typed observed window; "
            "prediction-compatible outcomes remain attribution-gated"
        ),
    )
    state = S01EfferenceCopyState(
        efference_id=f"s01-efference:{tick_id}",
        tick_index=tick_index,
        pending_predictions=tuple(pending_next),
        forward_packets=tuple(forward_packets),
        comparisons=tuple(comparisons),
        latest_comparison_status=latest_status,
        comparison_blocked_by_contamination=comparison_blocked_by_contamination,
        stale_prediction_detected=stale_prediction_detected,
        unexpected_change_detected=unexpected_change_detected,
        strong_self_attribution_allowed=False,
        source_lineage=tuple(dict.fromkeys(source_lineage)),
        last_update_provenance="s01.efference_copy.intended_vs_observed_comparator",
    )
    telemetry = S01Telemetry(
        efference_id=state.efference_id,
        tick_index=state.tick_index,
        pending_predictions_count=len(state.pending_predictions),
        comparisons_count=len(state.comparisons),
        latest_comparison_status=(
            None if state.latest_comparison_status is None else state.latest_comparison_status.value
        ),
        comparison_blocked_by_contamination=state.comparison_blocked_by_contamination,
        stale_prediction_detected=state.stale_prediction_detected,
        unexpected_change_detected=state.unexpected_change_detected,
        no_post_hoc_prediction_fabrication=True,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S01EfferenceCopyResult(
        state=state,
        gate=gate,
        scope_marker=_build_scope_marker(),
        telemetry=telemetry,
        reason="s01.first_bounded_efference_copy_slice",
    )


def _compare_prediction(
    *,
    tick_id: str,
    prediction: S01Prediction,
    observed: S01ObservedWindow,
    c05_revalidation_required: bool,
) -> S01ComparisonEntry:
    contamination_markers: list[str] = []
    if observed.contaminated and prediction.contamination_sensitive:
        contamination_markers.append("observed_window_contaminated")
    if c05_revalidation_required:
        contamination_markers.append("c05_revalidation_required")
    if contamination_markers:
        return S01ComparisonEntry(
            comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:blocked",
            prediction_id=prediction.prediction_id,
            axis=prediction.axis,
            status=S01ComparisonStatus.COMPARISON_BLOCKED_BY_CONTAMINATION,
            attribution_status=S01AttributionStatus.ATTRIBUTION_BLOCKED,
            observed_tick=observed.tick_index,
            latency_ticks=None,
            magnitude_error=None,
            observed_direction=None,
            contamination_markers=tuple(dict.fromkeys(contamination_markers)),
            reason="comparison blocked by contamination/revalidation constraints",
        )

    if observed.tick_index > prediction.expires_tick:
        return S01ComparisonEntry(
            comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:expired",
            prediction_id=prediction.prediction_id,
            axis=prediction.axis,
            status=S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED,
            attribution_status=S01AttributionStatus.ATTRIBUTION_BLOCKED,
            observed_tick=observed.tick_index,
            latency_ticks=observed.tick_index - prediction.preferred_tick,
            magnitude_error=None,
            observed_direction=None,
            contamination_markers=(),
            reason="prediction expired before expected change was cleanly observed",
        )

    if prediction.axis == S01ComparisonAxis.MODE_TOKEN:
        return _compare_mode_token(tick_id=tick_id, prediction=prediction, observed=observed)
    if prediction.axis == S01ComparisonAxis.WORLD_GROUNDED:
        observed_bool = observed.world_grounded_transition_admissible
        return _compare_bool_axis(
            tick_id=tick_id,
            prediction=prediction,
            observed_tick=observed.tick_index,
            observed_bool=observed_bool,
            axis=S01ComparisonAxis.WORLD_GROUNDED,
        )
    if prediction.axis == S01ComparisonAxis.WORLD_EFFECT_FEEDBACK:
        observed_bool = observed.world_effect_feedback_correlated
        return _compare_bool_axis(
            tick_id=tick_id,
            prediction=prediction,
            observed_tick=observed.tick_index,
            observed_bool=observed_bool,
            axis=S01ComparisonAxis.WORLD_EFFECT_FEEDBACK,
        )
    return _compare_world_confidence_delta(
        tick_id=tick_id,
        prediction=prediction,
        observed=observed,
    )


def _compare_mode_token(
    *,
    tick_id: str,
    prediction: S01Prediction,
    observed: S01ObservedWindow,
) -> S01ComparisonEntry:
    expected = str(prediction.expected_token or "")
    observed_mode = str(observed.selected_mode or "")
    latency = max(0, observed.tick_index - prediction.preferred_tick)
    if observed_mode == expected:
        status = (
            S01ComparisonStatus.MATCHED_AS_EXPECTED
            if observed.tick_index <= prediction.preferred_tick
            else S01ComparisonStatus.LATENCY_MISMATCH
        )
        return S01ComparisonEntry(
            comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:mode_match",
            prediction_id=prediction.prediction_id,
            axis=S01ComparisonAxis.MODE_TOKEN,
            status=status,
            attribution_status=S01AttributionStatus.PREDICTED_COMPATIBLE_ONLY,
            observed_tick=observed.tick_index,
            latency_ticks=latency,
            magnitude_error=None,
            observed_direction=None,
            contamination_markers=(),
            reason="observed mode token matched pre-observation expectation",
        )
    return S01ComparisonEntry(
        comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:mode_mismatch",
        prediction_id=prediction.prediction_id,
        axis=S01ComparisonAxis.MODE_TOKEN,
        status=S01ComparisonStatus.DIRECTION_MISMATCH,
        attribution_status=S01AttributionStatus.PREDICTED_COMPATIBLE_ONLY,
        observed_tick=observed.tick_index,
        latency_ticks=latency,
        magnitude_error=None,
        observed_direction=None,
        contamination_markers=(),
        reason="observed mode token diverged from pre-observation expectation",
    )


def _compare_bool_axis(
    *,
    tick_id: str,
    prediction: S01Prediction,
    observed_tick: int,
    observed_bool: bool,
    axis: S01ComparisonAxis,
) -> S01ComparisonEntry:
    expected_bool = bool(prediction.expected_bool)
    latency = max(0, observed_tick - prediction.preferred_tick)
    if observed_bool == expected_bool:
        status = (
            S01ComparisonStatus.MATCHED_AS_EXPECTED
            if latency == 0
            else S01ComparisonStatus.LATENCY_MISMATCH
        )
        return S01ComparisonEntry(
            comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:{axis.value}_match",
            prediction_id=prediction.prediction_id,
            axis=axis,
            status=status,
            attribution_status=S01AttributionStatus.PREDICTED_COMPATIBLE_ONLY,
            observed_tick=observed_tick,
            latency_ticks=latency,
            magnitude_error=None,
            observed_direction=1 if observed_bool else -1,
            contamination_markers=(),
            reason="boolean observed change matched pre-observation expectation",
        )
    if expected_bool and not observed_bool and observed_tick >= prediction.expires_tick:
        status = S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED
    elif expected_bool and not observed_bool:
        status = S01ComparisonStatus.PARTIAL_MATCH
    else:
        status = S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED
    return S01ComparisonEntry(
        comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:{axis.value}_mismatch",
        prediction_id=prediction.prediction_id,
        axis=axis,
        status=status,
        attribution_status=S01AttributionStatus.PREDICTED_COMPATIBLE_ONLY,
        observed_tick=observed_tick,
        latency_ticks=latency,
        magnitude_error=None,
        observed_direction=1 if observed_bool else -1,
        contamination_markers=(),
        reason="boolean observed change diverged from pre-observation expectation",
    )


def _compare_world_confidence_delta(
    *,
    tick_id: str,
    prediction: S01Prediction,
    observed: S01ObservedWindow,
) -> S01ComparisonEntry:
    if prediction.baseline_value is None or observed.world_confidence is None:
        return S01ComparisonEntry(
            comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:confidence_partial",
            prediction_id=prediction.prediction_id,
            axis=S01ComparisonAxis.WORLD_CONFIDENCE_DELTA,
            status=S01ComparisonStatus.PARTIAL_MATCH,
            attribution_status=S01AttributionStatus.ATTRIBUTION_BLOCKED,
            observed_tick=observed.tick_index,
            latency_ticks=None,
            magnitude_error=None,
            observed_direction=None,
            contamination_markers=("confidence_basis_missing",),
            reason="confidence delta comparison cannot be completed without baseline and observed confidence",
        )

    observed_delta = observed.world_confidence - prediction.baseline_value
    observed_direction = 0 if abs(observed_delta) < 1e-9 else (1 if observed_delta > 0 else -1)
    expected_direction = int(prediction.expected_direction or 0)
    expected_magnitude = float(prediction.expected_magnitude or 0.0)
    magnitude_error = abs(abs(observed_delta) - expected_magnitude)
    if expected_direction != 0 and observed_direction != expected_direction:
        status = S01ComparisonStatus.DIRECTION_MISMATCH
    elif magnitude_error > float(prediction.tolerance):
        status = S01ComparisonStatus.MAGNITUDE_MISMATCH
    elif magnitude_error > float(prediction.tolerance) * 0.5:
        status = S01ComparisonStatus.PARTIAL_MATCH
    elif observed.tick_index > prediction.preferred_tick:
        status = S01ComparisonStatus.LATENCY_MISMATCH
    else:
        status = S01ComparisonStatus.MATCHED_AS_EXPECTED
    return S01ComparisonEntry(
        comparison_id=f"cmp:{tick_id}:{prediction.prediction_id}:confidence_delta",
        prediction_id=prediction.prediction_id,
        axis=S01ComparisonAxis.WORLD_CONFIDENCE_DELTA,
        status=status,
        attribution_status=S01AttributionStatus.PREDICTED_COMPATIBLE_ONLY,
        observed_tick=observed.tick_index,
        latency_ticks=max(0, observed.tick_index - prediction.preferred_tick),
        magnitude_error=round(magnitude_error, 6),
        observed_direction=observed_direction,
        contamination_markers=(),
        reason="world confidence delta compared against pre-observation expected direction/magnitude",
    )


def _build_forward_packet_and_predictions(
    *,
    tick_id: str,
    tick_index: int,
    c04_selected_mode: str,
    c04_execution_mode_claim: str,
    emit_world_action_candidate: bool,
    world_confidence: float | None,
) -> tuple[S01ForwardModelPacket, tuple[S01Prediction, ...]]:
    prediction_window = (tick_index + 1, tick_index + 2)
    packet = S01ForwardModelPacket(
        packet_id=f"s01-forward:{tick_id}",
        intended_change=f"mode={c04_selected_mode}",
        expected_consequence=(
            "maintain_mode_token_and_world_signal_consistency"
            if c04_selected_mode in _ACTIVE_WORLD_EFFECT_MODES
            else "maintain_mode_token_with_low_world_effect_pressure"
        ),
        action_context=(
            f"c04_execution_mode_claim={c04_execution_mode_claim}",
            f"selected_mode={c04_selected_mode}",
            f"emit_world_action_candidate={emit_world_action_candidate}",
        ),
        timing_window=prediction_window,
        mismatch_hooks=_DEFAULT_MISMATCH_HOOKS,
        created_tick=tick_index,
        expires_tick=prediction_window[1],
        source_ref=f"s01.forward_model@{tick_id}",
    )

    effect_expected = bool(emit_world_action_candidate or c04_selected_mode in _ACTIVE_WORLD_EFFECT_MODES)
    confidence_direction = 1 if effect_expected else -1
    confidence_magnitude = 0.08 if effect_expected else 0.03

    predictions = (
        S01Prediction(
            prediction_id=f"s01-pred:{tick_id}:mode",
            packet_id=packet.packet_id,
            source_kind=S01SourceKind.MODE_TRANSITION,
            source_ref=f"c04.mode_transition@{tick_id}",
            axis=S01ComparisonAxis.MODE_TOKEN,
            created_tick=tick_index,
            earliest_tick=prediction_window[0],
            preferred_tick=prediction_window[0],
            expires_tick=prediction_window[1],
            expected_bool=None,
            expected_token=c04_selected_mode,
            expected_direction=None,
            expected_magnitude=None,
            tolerance=0.0,
            baseline_value=None,
            contamination_sensitive=False,
        ),
        S01Prediction(
            prediction_id=f"s01-pred:{tick_id}:effect",
            packet_id=packet.packet_id,
            source_kind=S01SourceKind.INTERNAL_ACT,
            source_ref=f"rt01.execution_mode@{tick_id}",
            axis=S01ComparisonAxis.WORLD_EFFECT_FEEDBACK,
            created_tick=tick_index,
            earliest_tick=prediction_window[0],
            preferred_tick=prediction_window[0],
            expires_tick=prediction_window[1],
            expected_bool=effect_expected,
            expected_token=None,
            expected_direction=confidence_direction,
            expected_magnitude=confidence_magnitude,
            tolerance=0.08,
            baseline_value=world_confidence,
            contamination_sensitive=True,
        ),
        S01Prediction(
            prediction_id=f"s01-pred:{tick_id}:confidence",
            packet_id=packet.packet_id,
            source_kind=S01SourceKind.INTERNAL_ACT,
            source_ref=f"world_entry.confidence@{tick_id}",
            axis=S01ComparisonAxis.WORLD_CONFIDENCE_DELTA,
            created_tick=tick_index,
            earliest_tick=prediction_window[0],
            preferred_tick=prediction_window[0],
            expires_tick=prediction_window[1],
            expected_bool=None,
            expected_token=None,
            expected_direction=confidence_direction,
            expected_magnitude=confidence_magnitude,
            tolerance=0.07,
            baseline_value=world_confidence,
            contamination_sensitive=True,
        ),
    )
    return packet, predictions


def _build_scope_marker() -> S01ScopeMarker:
    return S01ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        s01_first_slice_only=True,
        s02_implemented=False,
        s03_implemented=False,
        s04_implemented=False,
        s05_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded s01 slice only; s02-s05 self/nonself rollout remains out of scope"
        ),
    )


def _derive_restrictions(
    *,
    comparison_blocked_by_contamination: bool,
    stale_prediction_detected: bool,
    unexpected_change_detected: bool,
    c05_revalidation_required: bool,
) -> tuple[str, ...]:
    restrictions = [
        "s01_pre_observation_registry_must_be_read",
        "s01_expected_vs_observed_comparison_must_be_read",
        "s01_prediction_compatibility_is_not_strong_self_attribution",
    ]
    if comparison_blocked_by_contamination:
        restrictions.append("s01_comparison_blocked_by_contamination")
    if stale_prediction_detected:
        restrictions.append("s01_prediction_stale_or_expired")
    if unexpected_change_detected:
        restrictions.append("s01_unexpected_change_detected")
    if c05_revalidation_required:
        restrictions.append("s01_c05_revalidation_constraints_apply")
    return tuple(dict.fromkeys(restrictions))
