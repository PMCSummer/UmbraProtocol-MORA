from __future__ import annotations

from dataclasses import replace

from substrate.s01_efference_copy import (
    S01ComparisonAxis,
    S01ComparisonStatus,
    S01EfferenceCopyResult,
)
from substrate.s02_prediction_boundary.models import (
    ForbiddenS02Shortcut,
    S02BoundaryGateDecision,
    S02BoundaryStatus,
    S02EvidenceCounters,
    S02PredictionBoundaryResult,
    S02PredictionBoundaryState,
    S02ScopeMarker,
    S02SeamEntry,
    S02Telemetry,
)


_MATCHED_STATUSES = {
    S01ComparisonStatus.MATCHED_AS_EXPECTED,
    S01ComparisonStatus.LATENCY_MISMATCH,
}
_PARTIAL_STATUSES = {S01ComparisonStatus.PARTIAL_MATCH}
_MISMATCH_STATUSES = {
    S01ComparisonStatus.MAGNITUDE_MISMATCH,
    S01ComparisonStatus.DIRECTION_MISMATCH,
    S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED,
    S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED,
}
_EFFECT_CHANNELS = {
    S01ComparisonAxis.WORLD_EFFECT_FEEDBACK.value,
    S01ComparisonAxis.WORLD_CONFIDENCE_DELTA.value,
}


def build_s02_prediction_boundary(
    *,
    tick_id: str,
    tick_index: int,
    s01_result: S01EfferenceCopyResult,
    c04_selected_mode: str,
    c05_validity_action: str,
    c05_revalidation_required: bool,
    c05_dependency_contaminated: bool,
    context_shift_detected: bool,
    effector_available: bool,
    observation_degraded: bool,
    prior_state: S02PredictionBoundaryState | None = None,
    source_lineage: tuple[str, ...] = (),
    context_scope: tuple[str, ...] = (),
    aggregation_enabled: bool = True,
    controllability_sensitive_signal_enabled: bool = True,
    manual_channel_map: dict[str, str] | None = None,
) -> S02PredictionBoundaryResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if tick_index < 1:
        raise ValueError("tick_index must be >= 1")
    if not isinstance(s01_result, S01EfferenceCopyResult):
        raise TypeError("s01_result must be S01EfferenceCopyResult")

    prior_entries = {}
    if aggregation_enabled and isinstance(prior_state, S02PredictionBoundaryState):
        prior_entries = {item.channel_or_effect_class: item for item in prior_state.seam_entries}

    comparisons_by_axis: dict[str, list[object]] = {}
    for item in s01_result.state.comparisons:
        key = item.axis.value
        comparisons_by_axis.setdefault(key, []).append(item)

    candidate_channels = set(prior_entries.keys()) | set(comparisons_by_axis.keys())
    if not candidate_channels:
        candidate_channels = {S01ComparisonAxis.MODE_TOKEN.value}

    entries: list[S02SeamEntry] = []
    shortcut_markers: list[str] = []
    for channel in sorted(candidate_channels):
        previous_entry = prior_entries.get(channel)
        evidence = _build_evidence_counters(
            channel=channel,
            comparisons=comparisons_by_axis.get(channel, []),
            previous=(
                None if (previous_entry is None or not aggregation_enabled) else previous_entry.evidence_counters
            ),
            effector_available=effector_available,
            controllability_sensitive_signal_enabled=controllability_sensitive_signal_enabled,
        )
        status = _derive_boundary_status(
            evidence=evidence,
            c05_revalidation_required=c05_revalidation_required,
            c05_dependency_contaminated=c05_dependency_contaminated,
            context_shift_detected=context_shift_detected,
            effector_available=effector_available,
            observation_degraded=observation_degraded,
        )
        confidence = _derive_boundary_confidence(
            evidence=evidence,
            status=status,
        )
        validity_marker = _derive_validity_marker(
            c05_revalidation_required=c05_revalidation_required,
            c05_dependency_contaminated=c05_dependency_contaminated,
            observation_degraded=observation_degraded,
            context_shift_detected=context_shift_detected,
        )
        entry = S02SeamEntry(
            seam_entry_id=f"s02-seam:{tick_id}:{channel}",
            channel_or_effect_class=channel,
            boundary_status=status,
            controllability_estimate=_derive_controllability_estimate(
                evidence=evidence,
                controllability_sensitive_signal_enabled=controllability_sensitive_signal_enabled,
            ),
            prediction_reliability_estimate=_derive_prediction_reliability(evidence=evidence),
            external_dominance_estimate=_derive_external_dominance(evidence=evidence),
            mixed_source_score=_derive_mixed_source_score(evidence=evidence),
            context_scope=(
                context_scope
                if context_scope
                else ("c04_mode", c04_selected_mode, "c05_action", c05_validity_action)
            ),
            validity_marker=validity_marker,
            boundary_confidence=confidence,
            provenance="s02.prediction_boundary.repeated_s01_aggregation",
            evidence_counters=evidence,
            last_boundary_update=tick_index,
        )

        if manual_channel_map and channel in manual_channel_map:
            shortcut_markers.append(ForbiddenS02Shortcut.HARDCODED_CHANNEL_SELF_WORLD_MAP.value)
            forced = _normalize_boundary_status(manual_channel_map[channel])
            entry = replace(entry, boundary_status=forced)

        if (
            entry.boundary_status is S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM
            and entry.evidence_counters.repeated_outcome_support <= 1
        ):
            shortcut_markers.append(ForbiddenS02Shortcut.ONE_SHOT_SEAM_FROM_SINGLE_SUCCESS.value)
        if (
            entry.prediction_reliability_estimate >= 0.65
            and entry.controllability_estimate < 0.45
            and entry.boundary_status is S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM
        ):
            shortcut_markers.append(
                ForbiddenS02Shortcut.PREDICTABLE_COLLAPSED_INTO_SELF_SIDE.value
            )
        if (
            entry.mixed_source_score >= 0.45
            and entry.boundary_status
            in {
                S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM,
                S02BoundaryStatus.EXTERNALLY_DOMINATED_BOUNDARY,
            }
        ):
            shortcut_markers.append(ForbiddenS02Shortcut.MIXED_SOURCE_BINARIZED.value)
        if (
            entry.validity_marker == "stale_or_revalidation_required"
            and entry.boundary_status is S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM
        ):
            shortcut_markers.append(
                ForbiddenS02Shortcut.STALE_SEAM_CARRIED_WITHOUT_REVALIDATION.value
            )
        if (
            entry.prediction_reliability_estimate >= 0.65
            and entry.controllability_estimate < 0.45
            and entry.boundary_status is not S02BoundaryStatus.PREDICTABLE_BUT_NOT_SELF_DRIVEN
        ):
            shortcut_markers.append(
                ForbiddenS02Shortcut.PREDICTION_SUCCESS_AS_SELF_CONTROL_PROXY.value
            )

        entries.append(entry)

    active_status = _derive_active_status(entries)
    boundary_uncertain = active_status in {
        S02BoundaryStatus.BOUNDARY_UNCERTAIN,
        S02BoundaryStatus.INSUFFICIENT_COVERAGE,
        S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT,
    }
    insufficient_coverage = bool(
        entries
        and all(item.boundary_status is S02BoundaryStatus.INSUFFICIENT_COVERAGE for item in entries)
    )
    no_clean = active_status in {
        S02BoundaryStatus.NO_CLEAN_SEAM_CLAIM,
        S02BoundaryStatus.BOUNDARY_UNCERTAIN,
        S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT,
    }
    gate = _build_gate(
        entries=tuple(entries),
        boundary_uncertain=boundary_uncertain,
        no_clean_seam_claim=no_clean,
        forbidden_shortcuts=tuple(dict.fromkeys(shortcut_markers)),
    )
    state = S02PredictionBoundaryState(
        boundary_id=f"s02-boundary:{tick_id}",
        tick_index=tick_index,
        seam_entries=tuple(entries),
        active_boundary_status=active_status,
        boundary_uncertain=boundary_uncertain,
        insufficient_coverage=insufficient_coverage,
        no_clean_seam_claim=no_clean,
        source_lineage=tuple(dict.fromkeys((*source_lineage, *s01_result.state.source_lineage))),
        last_update_provenance="s02.prediction_boundary.seam_ledger",
    )
    scope = _build_scope_marker()
    telemetry = S02Telemetry(
        boundary_id=state.boundary_id,
        tick_index=state.tick_index,
        seam_entries_count=len(state.seam_entries),
        active_boundary_status=state.active_boundary_status,
        boundary_uncertain=state.boundary_uncertain,
        insufficient_coverage=state.insufficient_coverage,
        no_clean_seam_claim=state.no_clean_seam_claim,
        boundary_consumer_ready=gate.boundary_consumer_ready,
        controllability_consumer_ready=gate.controllability_consumer_ready,
        mixed_source_consumer_ready=gate.mixed_source_consumer_ready,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S02PredictionBoundaryResult(
        state=state,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason="s02.first_bounded_prediction_boundary_slice",
    )


def _build_evidence_counters(
    *,
    channel: str,
    comparisons: list[object],
    previous: S02EvidenceCounters | None,
    effector_available: bool,
    controllability_sensitive_signal_enabled: bool,
) -> S02EvidenceCounters:
    matched = 0
    mismatch = 0
    contamination = 0
    unexpected = 0
    internal_support = 0
    external_support = 0
    for item in comparisons:
        if item.status in _MATCHED_STATUSES:
            matched += 1
        elif item.status in _PARTIAL_STATUSES:
            matched += 1
        elif item.status in _MISMATCH_STATUSES:
            mismatch += 1
        elif item.status is S01ComparisonStatus.COMPARISON_BLOCKED_BY_CONTAMINATION:
            contamination += 1
        if item.status is S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED:
            unexpected += 1

        if item.status in _MATCHED_STATUSES:
            if channel == S01ComparisonAxis.MODE_TOKEN.value:
                if controllability_sensitive_signal_enabled and effector_available:
                    internal_support += 1
            elif (
                channel in _EFFECT_CHANNELS
                and controllability_sensitive_signal_enabled
                and effector_available
            ):
                internal_support += 1
            else:
                external_support += 1
        elif (
            channel in _EFFECT_CHANNELS
            and item.status in _MISMATCH_STATUSES
        ):
            # Mismatch on effect channels contributes external-pressure evidence
            # and prevents silent collapse into purely self-side seam.
            external_support += 1

    if (
        previous is not None
        and channel in _EFFECT_CHANNELS
        and not effector_available
        and previous.internal_control_support > 0
        and internal_support == 0
    ):
        # Lost effector control after prior internal coupling should add
        # external-pressure evidence even when the current pass has no usable
        # internal control support for this channel.
        mismatch += 1
        external_support += 1

    support = matched + mismatch + contamination
    if previous is None:
        return S02EvidenceCounters(
            repeated_outcome_support=support,
            matched_support=matched,
            mismatch_support=mismatch,
            contamination_support=contamination,
            unexpected_residual_support=unexpected,
            internal_control_support=internal_support,
            external_regularity_support=external_support,
        )
    return S02EvidenceCounters(
        repeated_outcome_support=previous.repeated_outcome_support + support,
        matched_support=previous.matched_support + matched,
        mismatch_support=previous.mismatch_support + mismatch,
        contamination_support=previous.contamination_support + contamination,
        unexpected_residual_support=previous.unexpected_residual_support + unexpected,
        internal_control_support=previous.internal_control_support + internal_support,
        external_regularity_support=previous.external_regularity_support + external_support,
    )


def _derive_prediction_reliability(*, evidence: S02EvidenceCounters) -> float:
    total = max(1, evidence.repeated_outcome_support)
    weighted_match = evidence.matched_support
    reliability = weighted_match / total
    reliability -= min(0.2, evidence.unexpected_residual_support * 0.08)
    return round(max(0.0, min(1.0, reliability)), 3)


def _derive_controllability_estimate(
    *,
    evidence: S02EvidenceCounters,
    controllability_sensitive_signal_enabled: bool,
) -> float:
    if not controllability_sensitive_signal_enabled:
        return 0.0
    total = max(1, evidence.repeated_outcome_support)
    score = evidence.internal_control_support / total
    score -= min(0.15, evidence.unexpected_residual_support * 0.06)
    return round(max(0.0, min(1.0, score)), 3)


def _derive_external_dominance(*, evidence: S02EvidenceCounters) -> float:
    total = max(1, evidence.repeated_outcome_support)
    score = evidence.external_regularity_support / total
    score += min(0.2, evidence.unexpected_residual_support * 0.05)
    return round(max(0.0, min(1.0, score)), 3)


def _derive_mixed_source_score(*, evidence: S02EvidenceCounters) -> float:
    internal = evidence.internal_control_support
    external = evidence.external_regularity_support + evidence.unexpected_residual_support
    total = max(1, evidence.repeated_outcome_support)
    internal_norm = internal / total
    external_norm = external / total
    mixed = min(internal_norm, external_norm) * 2.0
    mixed += min(0.25, evidence.contamination_support * 0.08)
    return round(max(0.0, min(1.0, mixed)), 3)


def _derive_validity_marker(
    *,
    c05_revalidation_required: bool,
    c05_dependency_contaminated: bool,
    observation_degraded: bool,
    context_shift_detected: bool,
) -> str:
    if c05_revalidation_required or c05_dependency_contaminated:
        return "stale_or_revalidation_required"
    if observation_degraded:
        return "observation_degraded"
    if context_shift_detected:
        return "context_shift_detected"
    return "valid"


def _derive_boundary_confidence(
    *,
    evidence: S02EvidenceCounters,
    status: S02BoundaryStatus,
) -> float:
    coverage = min(1.0, evidence.repeated_outcome_support / 4.0)
    mismatch_penalty = min(0.3, evidence.mismatch_support * 0.06)
    contamination_penalty = min(0.35, evidence.contamination_support * 0.08)
    score = 0.35 + (coverage * 0.5) - mismatch_penalty - contamination_penalty
    if status in {
        S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT,
        S02BoundaryStatus.INSUFFICIENT_COVERAGE,
    }:
        score = min(score, 0.4)
    return round(max(0.0, min(1.0, score)), 3)


def _derive_boundary_status(
    *,
    evidence: S02EvidenceCounters,
    c05_revalidation_required: bool,
    c05_dependency_contaminated: bool,
    context_shift_detected: bool,
    effector_available: bool,
    observation_degraded: bool,
) -> S02BoundaryStatus:
    reliability = _derive_prediction_reliability(evidence=evidence)
    controllability = _derive_controllability_estimate(
        evidence=evidence,
        controllability_sensitive_signal_enabled=True,
    )
    external = _derive_external_dominance(evidence=evidence)
    mixed = _derive_mixed_source_score(evidence=evidence)

    effector_loss_with_internal_history = (
        (not effector_available) and evidence.internal_control_support > 0
    )
    if (
        context_shift_detected
        or effector_loss_with_internal_history
        or observation_degraded
        or c05_revalidation_required
        or c05_dependency_contaminated
    ):
        return S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT
    if evidence.repeated_outcome_support < 2:
        return S02BoundaryStatus.INSUFFICIENT_COVERAGE
    if mixed >= 0.5:
        return S02BoundaryStatus.MIXED_SOURCE_BOUNDARY
    if controllability >= 0.62 and reliability >= 0.62:
        return S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM
    if controllability >= 0.58 and reliability < 0.62:
        return S02BoundaryStatus.CONTROLLABLE_BUT_UNRELIABLE
    if reliability >= 0.62 and controllability < 0.45:
        return S02BoundaryStatus.PREDICTABLE_BUT_NOT_SELF_DRIVEN
    if external >= 0.62 and controllability < 0.45:
        return S02BoundaryStatus.EXTERNALLY_DOMINATED_BOUNDARY
    if reliability < 0.4 and controllability < 0.4 and external < 0.4:
        return S02BoundaryStatus.NO_CLEAN_SEAM_CLAIM
    return S02BoundaryStatus.BOUNDARY_UNCERTAIN


def _derive_active_status(entries: list[S02SeamEntry]) -> S02BoundaryStatus:
    if not entries:
        return S02BoundaryStatus.NO_CLEAN_SEAM_CLAIM
    ordered = sorted(entries, key=lambda item: item.boundary_confidence, reverse=True)
    return ordered[0].boundary_status


def _build_gate(
    *,
    entries: tuple[S02SeamEntry, ...],
    boundary_uncertain: bool,
    no_clean_seam_claim: bool,
    forbidden_shortcuts: tuple[str, ...],
) -> S02BoundaryGateDecision:
    boundary_consumer_ready = bool(entries) and not boundary_uncertain and not no_clean_seam_claim
    controllability_consumer_ready = any(
        item.boundary_status in {
            S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM,
            S02BoundaryStatus.CONTROLLABLE_BUT_UNRELIABLE,
        }
        and item.controllability_estimate >= 0.55
        for item in entries
    )
    mixed_source_consumer_ready = any(
        item.boundary_status is S02BoundaryStatus.MIXED_SOURCE_BOUNDARY
        for item in entries
    )
    restrictions = [
        "s02_prediction_boundary_contract_must_be_read",
        "s02_controllability_vs_predictability_must_be_read",
        "s02_mixed_source_status_must_be_preserved",
        "s02_context_stale_invalidation_must_be_obeyed",
    ]
    if not boundary_consumer_ready:
        restrictions.append("s02_boundary_consumer_not_ready")
    if not controllability_consumer_ready:
        restrictions.append("s02_controllability_consumer_not_ready")
    if not mixed_source_consumer_ready:
        restrictions.append("s02_mixed_source_consumer_not_ready")
    if forbidden_shortcuts:
        restrictions.append("s02_forbidden_shortcut_detected")
    return S02BoundaryGateDecision(
        boundary_consumer_ready=boundary_consumer_ready,
        controllability_consumer_ready=controllability_consumer_ready,
        mixed_source_consumer_ready=mixed_source_consumer_ready,
        forbidden_shortcuts=forbidden_shortcuts,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "s02 aggregated repeated s01 outcomes into bounded prediction seam ledger with controllability/predictability separation"
        ),
    )


def _build_scope_marker() -> S02ScopeMarker:
    return S02ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        s02_first_slice_only=True,
        s03_implemented=False,
        s04_implemented=False,
        s05_implemented=False,
        full_self_model_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded s02 slice only; s03-s05 ownership/interoception/multi-cause phases remain out of scope"
        ),
    )


def _normalize_boundary_status(token: str) -> S02BoundaryStatus:
    try:
        return S02BoundaryStatus(str(token).strip())
    except ValueError:
        return S02BoundaryStatus.BOUNDARY_UNCERTAIN
