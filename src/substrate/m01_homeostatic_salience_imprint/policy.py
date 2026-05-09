from __future__ import annotations

from substrate.m01_homeostatic_salience_imprint.models import (
    M01AttributionEvidence,
    M01AttributionStatus,
    M01GateDecision,
    M01ImprintDecisionType,
    M01ImprintPacket,
    M01InputBundle,
    M01LedgerEntry,
    M01LifecycleAdjustment,
    M01RegulatoryDirection,
    M01RegulatoryAxisDelta,
    M01Result,
    M01ScopeMarker,
    M01SignOfEffect,
    M01TemporalCouplingEvidence,
    M01TemporalWindowStatus,
    M01Telemetry,
    M01AllowedMemoryUse,
)


def build_m01_homeostatic_salience_imprint(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: M01InputBundle | None,
    imprint_enabled: bool = True,
) -> M01Result:
    if not imprint_enabled:
        return _minimal_result(
            bundle_id=f"m01:{tick_id}:bundle:none",
            reason="M01 gate disabled in test fixture",
            restrictions=("m01_disabled", "m01_no_safe_imprint_claim"),
        )

    if not isinstance(input_bundle, M01InputBundle):
        return _minimal_result(
            bundle_id=f"m01:{tick_id}:bundle:none",
            reason=(
                "m01 requires typed trace/regulatory/attribution coupling input and does not promote "
                "novelty, recency, or outcome hints into homeostatic imprint by themselves"
            ),
            restrictions=("insufficient_m01_basis", "m01_no_safe_imprint_claim"),
        )

    if not input_bundle.traces:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="m01 received no traces and preserves explicit no-safe-imprint state",
            restrictions=("m01_no_trace_input", "m01_no_safe_imprint_claim"),
        )

    deltas_by_id = {item.delta_id: item for item in input_bundle.regulatory_deltas}
    coupling_by_trace = {item.trace_id: item for item in input_bundle.temporal_coupling}
    attribution_by_trace = {item.trace_id: item for item in input_bundle.attribution}

    packets: list[M01ImprintPacket] = []
    ledger: list[M01LedgerEntry] = []
    strong_count = 0
    weak_or_no_claim_count = 0
    attribution_limited_count = 0
    recovery_imprint_count = 0
    no_safe_count = 0

    for trace in input_bundle.traces:
        coupling = coupling_by_trace.get(trace.trace_id)
        attribution = attribution_by_trace.get(trace.trace_id)
        packet, record = _evaluate_trace(
            tick_id=tick_id,
            tick_index=tick_index,
            trace_id=trace.trace_id,
            coupling=coupling,
            attribution=attribution,
            deltas_by_id=deltas_by_id,
            prior_imprints=input_bundle.prior_imprints,
            source_lineage=input_bundle.source_lineage,
        )
        packets.append(packet)
        ledger.append(record)

        if packet.decision in {
            M01ImprintDecisionType.STRONG_THREAT_IMPRINT,
            M01ImprintDecisionType.STRONG_STRAIN_IMPRINT,
            M01ImprintDecisionType.STRONG_RELIEF_IMPRINT,
            M01ImprintDecisionType.STRONG_RECOVERY_IMPRINT,
        }:
            strong_count += 1
        if packet.decision in {
            M01ImprintDecisionType.WEAK_HOMEOSTATIC_LINK,
            M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM,
            M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT,
        }:
            weak_or_no_claim_count += 1
        if packet.decision is M01ImprintDecisionType.ATTRIBUTION_LIMITED_IMPRINT:
            attribution_limited_count += 1
        if packet.decision in {
            M01ImprintDecisionType.STRONG_RELIEF_IMPRINT,
            M01ImprintDecisionType.STRONG_RECOVERY_IMPRINT,
        }:
            recovery_imprint_count += 1
        if packet.decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM:
            no_safe_count += 1

    consumer_ready = strong_count > 0 or recovery_imprint_count > 0
    telemetry = M01Telemetry(
        trace_count=len(input_bundle.traces),
        imprint_count=len(packets),
        strong_imprint_count=strong_count,
        weak_or_no_claim_count=weak_or_no_claim_count,
        attribution_limited_count=attribution_limited_count,
        recovery_imprint_count=recovery_imprint_count,
        no_safe_imprint_count=no_safe_count,
        consumer_ready=consumer_ready,
    )
    gate = _build_gate(telemetry=telemetry, packets=tuple(packets))

    return M01Result(
        bundle_id=input_bundle.bundle_id,
        imprint_packets=tuple(packets),
        ledger=tuple(ledger),
        telemetry=telemetry,
        gate=gate,
        scope_marker=M01ScopeMarker(
            scope="frontier_hosted_m01_homeostatic_imprint_slice",
            frontier_only=True,
            narrow_slice_only=True,
            homeostatic_imprint_not_general_importance=True,
            not_reward_function=True,
            not_narrative_relevance=True,
            not_full_memory_system=True,
            no_policy_claim=True,
            no_global_value_claim=True,
            reason=(
                "m01 emits bounded memory-economics imprint packets only when traces are coupled to "
                "observed regulatory perturbation/strain/relief/recovery under temporal and attribution limits"
            ),
        ),
        reason="m01 produced typed homeostatic salience imprint packets",
    )


def _evaluate_trace(
    *,
    tick_id: str,
    tick_index: int,
    trace_id: str,
    coupling: M01TemporalCouplingEvidence | None,
    attribution: M01AttributionEvidence | None,
    deltas_by_id: dict[str, M01RegulatoryAxisDelta],
    prior_imprints: tuple[M01ImprintPacket, ...],
    source_lineage: tuple[str, ...],
) -> tuple[M01ImprintPacket, M01LedgerEntry]:
    reason_codes: list[str] = []
    transfer_limits = [
        "axis_scoped_only",
        "structural_similarity_required",
        "must_not_treat_as_general_importance",
    ]

    attribution_status = (
        attribution.attribution_status
        if isinstance(attribution, M01AttributionEvidence)
        else M01AttributionStatus.NO_CLEAN_ATTRIBUTION
    )
    coupling_status = (
        coupling.temporal_window_status
        if isinstance(coupling, M01TemporalCouplingEvidence)
        else M01TemporalWindowStatus.MISSING_TIMING
    )

    delta_refs = coupling.regulatory_delta_refs if isinstance(coupling, M01TemporalCouplingEvidence) else ()
    deltas = [deltas_by_id[item] for item in delta_refs if item in deltas_by_id]

    if not deltas:
        reason_codes.append("no_regulatory_delta_link")
        decision = M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM
        sign = M01SignOfEffect.UNCLEAR
        strength = 0.0
        lifecycle = M01LifecycleAdjustment.DECAY_WITHOUT_RECONFIRMATION if prior_imprints else M01LifecycleAdjustment.NO_ADJUSTMENT
    else:
        sign = _derive_sign(deltas)
        intensity = max(item.intensity * item.measurement_confidence for item in deltas)
        severe = any(item.deviation_after >= 0.75 for item in deltas)

        if coupling_status in {M01TemporalWindowStatus.OUT_OF_WINDOW, M01TemporalWindowStatus.MISSING_TIMING}:
            reason_codes.append("temporal_coupling_insufficient")
            decision = M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT
            strength = min(0.35, intensity * 0.5)
            lifecycle = M01LifecycleAdjustment.DECAY_WITHOUT_RECONFIRMATION
        elif coupling_status is M01TemporalWindowStatus.CONTESTED_TIMING:
            reason_codes.append("contested_timing_cap")
            decision = M01ImprintDecisionType.WEAK_HOMEOSTATIC_LINK
            strength = min(0.45, intensity * 0.6)
            lifecycle = M01LifecycleAdjustment.KEEP_NARROW_SCOPE_ONLY
        elif attribution_status in {
            M01AttributionStatus.EXTERNALLY_DOMINATED,
            M01AttributionStatus.OBSERVATION_ARTIFACT_RISK,
            M01AttributionStatus.NO_CLEAN_ATTRIBUTION,
        }:
            reason_codes.append("attribution_limited")
            decision = M01ImprintDecisionType.ATTRIBUTION_LIMITED_IMPRINT
            strength = min(0.4, intensity * 0.6)
            lifecycle = M01LifecycleAdjustment.DOWNGRADE_DUE_TO_ATTRIBUTION_CHANGE
        elif sign is M01SignOfEffect.MIXED:
            reason_codes.append("multi_axis_mixed_effect")
            decision = M01ImprintDecisionType.PROVISIONAL_MULTI_AXIS_IMPRINT
            strength = min(0.62, intensity)
            lifecycle = M01LifecycleAdjustment.KEEP_NARROW_SCOPE_ONLY
        elif sign in {M01SignOfEffect.RELIEF, M01SignOfEffect.RECOVERY, M01SignOfEffect.STABILIZATION}:
            decision = (
                M01ImprintDecisionType.STRONG_RECOVERY_IMPRINT
                if sign in {M01SignOfEffect.RECOVERY, M01SignOfEffect.STABILIZATION}
                else M01ImprintDecisionType.STRONG_RELIEF_IMPRINT
            )
            strength = max(0.6, intensity)
            lifecycle = M01LifecycleAdjustment.NO_ADJUSTMENT
        else:
            if severe and sign is M01SignOfEffect.PERTURBATION:
                decision = M01ImprintDecisionType.STRONG_THREAT_IMPRINT
            elif intensity >= 0.65:
                decision = M01ImprintDecisionType.STRONG_STRAIN_IMPRINT
            elif coupling_status is M01TemporalWindowStatus.DELAYED_BUT_PLAUSIBLE:
                decision = M01ImprintDecisionType.WEAK_HOMEOSTATIC_LINK
                reason_codes.append("delayed_temporal_link")
            else:
                decision = M01ImprintDecisionType.WEAK_HOMEOSTATIC_LINK
            strength = intensity if decision.name.startswith("STRONG") else min(0.55, intensity)
            lifecycle = M01LifecycleAdjustment.NO_ADJUSTMENT

    if coupling_status is M01TemporalWindowStatus.CONTESTED_TIMING:
        reason_codes.append("contested_timing")
    if attribution_status is M01AttributionStatus.MIXED:
        reason_codes.append("mixed_attribution")
    if attribution_status is M01AttributionStatus.ATTRIBUTION_UNCERTAIN:
        reason_codes.append("attribution_uncertain")
    if coupling_status is M01TemporalWindowStatus.DELAYED_BUT_PLAUSIBLE:
        transfer_limits.append("delayed_coupling_only")

    prior_match = [
        item
        for item in prior_imprints
        if item.sign_of_effect == sign and set(item.affected_axes).intersection({d.axis_id for d in deltas})
    ]
    if prior_match and strength > 0.0 and decision not in {
        M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM,
        M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT,
    }:
        strength = min(1.0, strength + 0.1)
        lifecycle = M01LifecycleAdjustment.REINFORCE_EXISTING_IMPRINT
        reason_codes.append("structural_reinforcement")
    elif prior_imprints and deltas and decision not in {
        M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM,
        M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT,
    }:
        reason_codes.append("reinforcement_not_supported_by_overlap")

    if decision in {
        M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM,
        M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT,
        M01ImprintDecisionType.ATTRIBUTION_LIMITED_IMPRINT,
    }:
        retention_bias = min(0.3, strength)
        replay_priority = min(0.25, strength)
        retrieval_bias = min(0.3, strength)
        persistence = "bounded_decay"
    else:
        retention_bias = min(1.0, 0.35 + strength * 0.55)
        replay_priority = min(1.0, 0.25 + strength * 0.6)
        retrieval_bias = min(1.0, 0.3 + strength * 0.55)
        persistence = "bounded_retain"

    reason_codes = list(dict.fromkeys(reason_codes or [decision.value]))
    affected_axes = tuple(dict.fromkeys(d.axis_id for d in deltas))
    confidence = _derive_confidence(
        decision=decision,
        coupling_status=coupling_status,
        attribution_status=attribution_status,
        deltas=deltas,
    )

    packet = M01ImprintPacket(
        imprint_id=f"m01:{tick_id}:{tick_index}:imprint:{trace_id}",
        source_trace_id=trace_id,
        affected_axes=affected_axes,
        sign_of_effect=sign,
        decision=decision,
        imprint_strength=round(strength, 4),
        retention_bias=round(retention_bias, 4),
        replay_priority=round(replay_priority, 4),
        retrieval_bias=round(retrieval_bias, 4),
        persistence_hint=persistence,
        transfer_limits=tuple(dict.fromkeys(transfer_limits)),
        confidence=confidence,
        reason_codes=tuple(reason_codes),
        lifecycle_adjustment=lifecycle,
        allowed_memory_use=M01AllowedMemoryUse(
            may_bias_retention=retention_bias > 0.0,
            may_bias_replay=replay_priority > 0.0,
            may_bias_retrieval=retrieval_bias > 0.0,
            must_preserve_axis_scope=True,
            must_preserve_transfer_limits=True,
            must_not_treat_as_general_importance=True,
        ),
        provenance=tuple(dict.fromkeys((*source_lineage, trace_id))),
    )

    ledger = M01LedgerEntry(
        entry_id=f"m01:{tick_id}:{tick_index}:ledger:{trace_id}",
        source_trace_id=trace_id,
        decision=decision,
        temporal_window_status=coupling_status,
        attribution_status=attribution_status,
        affected_axes=affected_axes,
        reason_codes=tuple(reason_codes),
        anti_overgeneralization_limits=packet.transfer_limits,
        lifecycle_adjustment=lifecycle,
    )
    return packet, ledger


def _derive_sign(deltas: list[M01RegulatoryAxisDelta]) -> M01SignOfEffect:
    if not deltas:
        return M01SignOfEffect.UNCLEAR
    signs = set()
    for delta in deltas:
        if delta.recovery_marker:
            signs.add(M01SignOfEffect.RECOVERY)
        elif delta.stabilization_marker:
            signs.add(M01SignOfEffect.STABILIZATION)
        elif delta.direction is M01RegulatoryDirection.IMPROVING:
            signs.add(M01SignOfEffect.RELIEF)
        elif delta.direction is M01RegulatoryDirection.WORSENING:
            if delta.deviation_after >= delta.deviation_before:
                signs.add(M01SignOfEffect.STRAIN)
            else:
                signs.add(M01SignOfEffect.PERTURBATION)
        elif delta.direction is M01RegulatoryDirection.STABILIZING:
            signs.add(M01SignOfEffect.STABILIZATION)
        else:
            signs.add(M01SignOfEffect.UNCLEAR)
    if len(signs) == 1:
        return next(iter(signs))
    return M01SignOfEffect.MIXED


def _derive_confidence(
    *,
    decision: M01ImprintDecisionType,
    coupling_status: M01TemporalWindowStatus,
    attribution_status: M01AttributionStatus,
    deltas: list[M01RegulatoryAxisDelta],
) -> float:
    if not deltas:
        return 0.2
    base = sum(item.measurement_confidence for item in deltas) / len(deltas)
    if coupling_status in {M01TemporalWindowStatus.OUT_OF_WINDOW, M01TemporalWindowStatus.MISSING_TIMING}:
        base *= 0.55
    if attribution_status in {
        M01AttributionStatus.EXTERNALLY_DOMINATED,
        M01AttributionStatus.OBSERVATION_ARTIFACT_RISK,
        M01AttributionStatus.NO_CLEAN_ATTRIBUTION,
    }:
        base *= 0.5
    if decision is M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM:
        base *= 0.4
    return round(max(0.0, min(1.0, base)), 4)


def _build_gate(*, telemetry: M01Telemetry, packets: tuple[M01ImprintPacket, ...]) -> M01GateDecision:
    restrictions: list[str] = []
    reason_codes: list[str] = []

    if telemetry.imprint_count == 0:
        restrictions.append("m01_no_imprint_packets")
        reason_codes.append("no_imprint_packets")
    if telemetry.no_safe_imprint_count > 0:
        restrictions.append("m01_no_safe_imprint_claim")
        reason_codes.append("no_safe_imprint_claim")
    if telemetry.attribution_limited_count > 0:
        restrictions.append("m01_attribution_limited_imprint")
        reason_codes.append("attribution_limited_imprint")

    imprint_packet_ready = any(
        item.decision
        not in {
            M01ImprintDecisionType.NO_SAFE_IMPRINT_CLAIM,
            M01ImprintDecisionType.STALE_BASIS_NO_STRONG_IMPRINT,
        }
        for item in packets
    )
    axis_scope_ready = all(item.allowed_memory_use.must_preserve_axis_scope for item in packets) if packets else False
    consumer_ready = bool(imprint_packet_ready and axis_scope_ready and telemetry.no_safe_imprint_count == 0)
    if not consumer_ready:
        restrictions.append("m01_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    return M01GateDecision(
        consumer_ready=consumer_ready,
        imprint_packet_consumer_ready=imprint_packet_ready,
        axis_scope_consumer_ready=axis_scope_ready,
        no_safe_imprint_claim=telemetry.no_safe_imprint_count > 0,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="m01 gate preserves bounded homeostatic imprint discipline",
    )


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> M01Result:
    telemetry = M01Telemetry(
        trace_count=0,
        imprint_count=0,
        strong_imprint_count=0,
        weak_or_no_claim_count=0,
        attribution_limited_count=0,
        recovery_imprint_count=0,
        no_safe_imprint_count=1,
        consumer_ready=False,
    )
    gate = M01GateDecision(
        consumer_ready=False,
        imprint_packet_consumer_ready=False,
        axis_scope_consumer_ready=False,
        no_safe_imprint_claim=True,
        required_restrictions=restrictions,
        reason_codes=("no_safe_imprint_claim",),
        reason=reason,
    )
    return M01Result(
        bundle_id=bundle_id,
        imprint_packets=(),
        ledger=(),
        telemetry=telemetry,
        gate=gate,
        scope_marker=M01ScopeMarker(
            scope="frontier_hosted_m01_homeostatic_imprint_slice",
            frontier_only=True,
            narrow_slice_only=True,
            homeostatic_imprint_not_general_importance=True,
            not_reward_function=True,
            not_narrative_relevance=True,
            not_full_memory_system=True,
            no_policy_claim=True,
            no_global_value_claim=True,
            reason=reason,
        ),
        reason=reason,
    )
