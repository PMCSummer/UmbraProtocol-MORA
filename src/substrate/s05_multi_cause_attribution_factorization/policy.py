from __future__ import annotations

from substrate.s01_efference_copy import S01EfferenceCopyResult
from substrate.s02_prediction_boundary import (
    S02BoundaryStatus,
    S02PredictionBoundaryResult,
)
from substrate.s03_ownership_weighted_learning import S03OwnershipWeightedLearningResult
from substrate.s04_interoceptive_self_binding import S04InteroceptiveSelfBindingResult
from substrate.s05_multi_cause_attribution_factorization.models import (
    S05AttributionGateDecision,
    S05AttributionStatus,
    S05CauseClass,
    S05CauseSlotEntry,
    S05DownstreamRouteClass,
    S05EligibilityStatus,
    S05FactorizationPacket,
    S05MultiCauseAttributionResult,
    S05MultiCauseAttributionState,
    S05OutcomePacketInput,
    S05ResidualClass,
    S05RevisionStatus,
    S05ScopeMarker,
    S05ScopeValidity,
    S05Telemetry,
)


_SLOT_SEQUENCE: tuple[S05CauseClass, ...] = (
    S05CauseClass.SELF_INITIATED_ACT,
    S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION,
    S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT,
    S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
    S05CauseClass.OBSERVATION_OR_CHANNEL_ARTIFACT,
)


def build_s05_multi_cause_attribution_factorization(
    *,
    tick_id: str,
    tick_index: int,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    s03_result: S03OwnershipWeightedLearningResult,
    s04_result: S04InteroceptiveSelfBindingResult,
    c04_selected_mode: str,
    c05_validity_action: str,
    c05_revalidation_required: bool,
    world_presence_mode: str,
    world_effect_feedback_correlated: bool,
    context_shift_detected: bool,
    late_evidence_tokens: tuple[str, ...] = (),
    outcome_packet: S05OutcomePacketInput | None = None,
    prior_state: S05MultiCauseAttributionState | None = None,
    source_lineage: tuple[str, ...] = (),
    factorization_enabled: bool = True,
) -> S05MultiCauseAttributionResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if tick_index < 1:
        raise ValueError("tick_index must be >= 1")
    if not isinstance(s01_result, S01EfferenceCopyResult):
        raise TypeError("s01_result must be S01EfferenceCopyResult")
    if not isinstance(s02_result, S02PredictionBoundaryResult):
        raise TypeError("s02_result must be S02PredictionBoundaryResult")
    if not isinstance(s03_result, S03OwnershipWeightedLearningResult):
        raise TypeError("s03_result must be S03OwnershipWeightedLearningResult")
    if not isinstance(s04_result, S04InteroceptiveSelfBindingResult):
        raise TypeError("s04_result must be S04InteroceptiveSelfBindingResult")

    packet_input = outcome_packet or _derive_outcome_packet(
        tick_id=tick_id,
        tick_index=tick_index,
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
    )
    if not factorization_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            packet_input=packet_input,
            source_lineage=source_lineage,
        )

    slot_candidates = _derive_slot_candidates(
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        s04_result=s04_result,
        c04_selected_mode=c04_selected_mode,
        c05_validity_action=c05_validity_action,
        c05_revalidation_required=c05_revalidation_required,
        world_presence_mode=world_presence_mode,
        world_effect_feedback_correlated=world_effect_feedback_correlated,
        context_shift_detected=context_shift_detected,
        packet_input=packet_input,
    )
    prior_packet = _latest_packet(prior_state)
    raw_allocations, _, residual, _ = _allocate_with_residual(
        slot_candidates=slot_candidates,
        packet_input=packet_input,
    )
    (
        blended_allocations,
        blended_residual,
        reattribution_happened,
        revision_status,
    ) = _apply_bounded_reattribution(
        raw_allocations=raw_allocations,
        residual=residual,
        prior_packet=prior_packet,
        late_evidence_tokens=late_evidence_tokens,
        slot_candidates=slot_candidates,
    )
    residual = _clamp(blended_residual)
    residual_class = _residual_class(residual)

    confidence = _derive_confidence(
        slot_candidates=slot_candidates,
        residual=residual,
        context_shift_detected=context_shift_detected,
        c05_revalidation_required=c05_revalidation_required,
    )
    attribution_status = _derive_attribution_status(
        slot_candidates=slot_candidates,
        allocations=blended_allocations,
        residual=residual,
        confidence=confidence,
    )
    bounded_interval_only = attribution_status is S05AttributionStatus.BOUNDED_INTERVAL_ONLY

    slot_entries = tuple(
        _build_slot_entry(
            cause_class=cause_class,
            candidate=slot_candidates[cause_class],
            allocation=blended_allocations.get(cause_class, 0.0),
            confidence=confidence,
            bounded_interval_only=bounded_interval_only,
        )
        for cause_class in _SLOT_SEQUENCE
    )
    residual_entry = _build_residual_entry(
        residual=residual,
        residual_class=residual_class,
        confidence=confidence,
    )
    all_entries = (*slot_entries, residual_entry)
    slot_shares = tuple(
        (
            entry.cause_class.value,
            entry.allocated_share
            if entry.allocated_share is not None
            else (entry.bounded_share_interval or (0.0, 1.0)),
        )
        for entry in all_entries
    )

    temporal_misalignment_present = any(
        item["temporal_fit"] < 0.35 for item in slot_candidates.values()
    )
    contamination_present = bool(
        packet_input.contaminated
        or any(item["contamination_penalty"] >= 0.45 for item in slot_candidates.values())
    )
    downstream_route = _derive_downstream_route(blended_allocations, residual)
    packet = S05FactorizationPacket(
        outcome_packet_id=packet_input.outcome_packet_id,
        cause_slots=all_entries,
        slot_weights_or_bounded_shares=slot_shares,
        unexplained_residual=round(residual, 3),
        residual_class=residual_class,
        compatibility_basis=_compatibility_basis(slot_candidates),
        temporal_alignment_basis=_temporal_alignment_basis(slot_candidates, packet_input),
        contamination_notes=_contamination_notes(slot_candidates, packet_input),
        confidence=confidence,
        provenance="s05.multi_cause_attribution.factorization_packet",
        revision_status=revision_status,
        attribution_status=attribution_status,
        scope_validity=_derive_scope_validity(
            attribution_status=attribution_status,
            residual=residual,
            c05_revalidation_required=c05_revalidation_required,
        ),
        downstream_route_class=downstream_route,
    )
    packets = (packet,)
    if isinstance(prior_state, S05MultiCauseAttributionState):
        packets = (*prior_state.packets, packet)
        if len(packets) > 8:
            packets = packets[-8:]

    gate = _build_gate(
        attribution_status=attribution_status,
        residual=residual,
        slot_candidates=slot_candidates,
        downstream_route=downstream_route,
    )
    state = S05MultiCauseAttributionState(
        factorization_id=f"s05-factorization:{tick_id}",
        tick_index=tick_index,
        packets=tuple(packets),
        latest_packet_id=packet.outcome_packet_id,
        dominant_cause_classes=_dominant_cause_classes(blended_allocations, residual),
        unexplained_residual=round(residual, 3),
        residual_class=residual_class,
        underdetermined_split=attribution_status
        in {
            S05AttributionStatus.UNDERDETERMINED_SPLIT,
            S05AttributionStatus.BOUNDED_INTERVAL_ONLY,
        },
        incompatible_candidates_present=any(
            item["eligibility_status"] is S05EligibilityStatus.INCOMPATIBLE
            for item in slot_candidates.values()
        ),
        temporal_misalignment_present=temporal_misalignment_present,
        contamination_present=contamination_present,
        reattribution_happened=reattribution_happened,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *s01_result.state.source_lineage,
                    *s02_result.state.source_lineage,
                    *s03_result.state.source_lineage,
                    *s04_result.state.source_lineage,
                )
            )
        ),
        last_update_provenance="s05.multi_cause_attribution.first_runtime_slice",
    )
    telemetry = S05Telemetry(
        factorization_id=state.factorization_id,
        tick_index=state.tick_index,
        dominant_slot_count=len(state.dominant_cause_classes),
        residual_share=state.unexplained_residual,
        residual_class=state.residual_class,
        underdetermined_split=state.underdetermined_split,
        contamination_present=state.contamination_present,
        temporal_misalignment_present=state.temporal_misalignment_present,
        reattribution_happened=state.reattribution_happened,
        downstream_route_class=downstream_route,
        factorization_consumer_ready=gate.factorization_consumer_ready,
        learning_route_ready=gate.learning_route_ready,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S05MultiCauseAttributionResult(
        state=state,
        gate=gate,
        scope_marker=_build_scope_marker(),
        telemetry=telemetry,
        reason="s05 bounded multi-cause attribution factorization",
    )


def _derive_outcome_packet(
    *,
    tick_id: str,
    tick_index: int,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    s03_result: S03OwnershipWeightedLearningResult,
) -> S05OutcomePacketInput:
    latest = s01_result.state.latest_comparison_status
    mismatch = 0.38
    if latest is not None:
        token = latest.value
        if token in {"magnitude_mismatch", "direction_mismatch", "latency_mismatch"}:
            mismatch = 0.66
        elif token in {"expected_but_unobserved", "unexpected_change_detected"}:
            mismatch = 0.74
        elif token in {"matched_as_expected", "partial_match"}:
            mismatch = 0.22
    if s03_result.state.requested_revalidation:
        mismatch = max(mismatch, 0.58)
    if s02_result.state.no_clean_seam_claim:
        mismatch = max(mismatch, 0.64)
    return S05OutcomePacketInput(
        outcome_packet_id=f"s05-outcome:{tick_id}:{tick_index}",
        mismatch_magnitude=round(_clamp(mismatch), 3),
        observed_delta_class=(
            "unexpected_change"
            if s01_result.state.unexpected_change_detected
            else "bounded_change"
        ),
        expected_delta_class=(
            "predicted_change"
            if s01_result.state.pending_predictions
            else "weak_prediction_basis"
        ),
        outcome_channel="rt01.runtime_tick_outcome",
        observed_tick=tick_index,
        preferred_tick=tick_index,
        expires_tick=tick_index + 2,
        contaminated=bool(
            s01_result.state.comparison_blocked_by_contamination
            or s02_result.state.no_clean_seam_claim
            or s02_result.state.boundary_uncertain
        ),
        source_ref="s05.outcome_packet.derived_from_s01_s03",
    )


def _derive_slot_candidates(
    *,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    s03_result: S03OwnershipWeightedLearningResult,
    s04_result: S04InteroceptiveSelfBindingResult,
    c04_selected_mode: str,
    c05_validity_action: str,
    c05_revalidation_required: bool,
    world_presence_mode: str,
    world_effect_feedback_correlated: bool,
    context_shift_detected: bool,
    packet_input: S05OutcomePacketInput,
) -> dict[S05CauseClass, dict[str, object]]:
    s03_packet = s03_result.state.packets[-1]
    boundary_entry = next(iter(s02_result.state.seam_entries), None)
    boundary_external = (
        0.0 if boundary_entry is None else float(boundary_entry.external_dominance_estimate)
    )
    boundary_mixed = (
        0.0 if boundary_entry is None else float(boundary_entry.mixed_source_score)
    )
    boundary_controllable = (
        0.0 if boundary_entry is None else float(boundary_entry.controllability_estimate)
    )
    boundary_status = s02_result.state.active_boundary_status
    strong_core_count = len(s04_result.state.core_bound_channels)
    weak_core_count = len(s04_result.state.peripheral_or_weakly_bound_channels)
    contested_count = len(s04_result.state.contested_channels)

    observation_contaminated = bool(
        packet_input.contaminated
        or s01_result.state.comparison_blocked_by_contamination
        or s02_result.state.no_clean_seam_claim
        or s02_result.state.boundary_uncertain
    )
    world_present = str(world_presence_mode or "").strip().lower() not in {"", "absent", "none"}
    mode_shift_like = str(c04_selected_mode or "").strip() in {
        "hold_safe_idle",
        "repair_runtime_path",
        "revalidate_scope",
    }

    temporal_fit = _temporal_fit(
        observed_tick=packet_input.observed_tick,
        preferred_tick=packet_input.preferred_tick,
        expires_tick=packet_input.expires_tick,
        c05_revalidation_required=c05_revalidation_required,
        c05_validity_action=c05_validity_action,
        context_shift_detected=context_shift_detected,
    )

    self_support = _clamp(
        (0.45 if s01_result.state.strong_self_attribution_allowed else 0.0)
        + (s03_packet.self_update_weight * 0.35)
        + (boundary_controllable * 0.2)
    )
    self_temporal = _clamp(temporal_fit + (0.08 if s01_result.gate.comparison_ready else -0.05))
    self_channel = _clamp(0.4 + (0.25 if s01_result.state.pending_predictions else 0.0))
    self_compat = self_channel * self_temporal

    mode_support = _clamp(
        (0.52 if mode_shift_like else 0.18)
        + (0.18 if context_shift_detected else 0.0)
        + (0.2 if c05_revalidation_required else 0.0)
    )
    mode_temporal = _clamp(temporal_fit + (0.1 if mode_shift_like else -0.1))
    mode_channel = _clamp(0.36 + (0.18 if mode_shift_like else 0.0))
    mode_compat = mode_temporal * mode_channel

    intero_support = _clamp(
        (0.2 + min(0.38, strong_core_count * 0.22))
        + min(0.18, weak_core_count * 0.08)
        + min(0.16, contested_count * 0.06)
        + (s03_packet.self_update_weight * 0.16)
    )
    intero_temporal = _clamp(
        temporal_fit
        + (0.1 if not s04_result.state.no_stable_self_core_claim else -0.12)
        - (0.12 if s04_result.state.contamination_detected else 0.0)
    )
    intero_channel = _clamp(0.42 + (0.22 if strong_core_count > 0 else 0.0))
    intero_compat = intero_temporal * intero_channel

    world_support = _clamp(
        (boundary_external * 0.48)
        + (boundary_mixed * 0.2)
        + (s03_packet.world_update_weight * 0.25)
        + (0.12 if world_present else 0.0)
        + (0.08 if world_effect_feedback_correlated else 0.0)
    )
    world_temporal = _clamp(temporal_fit + (0.08 if world_present else -0.12))
    world_channel = _clamp(0.3 + (0.36 if world_present else 0.0))
    world_compat = world_temporal * world_channel

    artifact_support = _clamp(
        (0.45 if observation_contaminated else 0.05)
        + (
            0.15
            if boundary_status
            in {
                S02BoundaryStatus.BOUNDARY_UNCERTAIN,
                S02BoundaryStatus.NO_CLEAN_SEAM_CLAIM,
                S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT,
            }
            else 0.0
        )
        + (s03_packet.observation_update_weight * 0.25)
    )
    artifact_temporal = _clamp(temporal_fit + (0.12 if observation_contaminated else -0.16))
    artifact_channel = _clamp(0.3 + (0.32 if observation_contaminated else 0.0))
    artifact_compat = artifact_temporal * artifact_channel

    return {
        S05CauseClass.SELF_INITIATED_ACT: _candidate(
            cause=S05CauseClass.SELF_INITIATED_ACT,
            support=self_support,
            temporal_fit=self_temporal,
            channel_fit=self_channel,
            compatibility=self_compat,
            contamination_penalty=0.18 if observation_contaminated else 0.05,
            evidence_basis=(
                f"s01_strong_self_attribution={s01_result.state.strong_self_attribution_allowed}",
                f"s03_self_update_weight={s03_packet.self_update_weight:.3f}",
                f"s02_controllability={boundary_controllable:.3f}",
            ),
        ),
        S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION: _candidate(
            cause=S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION,
            support=mode_support,
            temporal_fit=mode_temporal,
            channel_fit=mode_channel,
            compatibility=mode_compat,
            contamination_penalty=0.1 if mode_shift_like else 0.18,
            evidence_basis=(
                f"c04_selected_mode={c04_selected_mode}",
                f"context_shift_detected={context_shift_detected}",
                f"c05_revalidation_required={c05_revalidation_required}",
            ),
        ),
        S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT: _candidate(
            cause=S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT,
            support=intero_support,
            temporal_fit=intero_temporal,
            channel_fit=intero_channel,
            compatibility=intero_compat,
            contamination_penalty=0.22 if s04_result.state.contamination_detected else 0.08,
            evidence_basis=(
                f"s04_strong_core_count={strong_core_count}",
                f"s04_no_stable_core={s04_result.state.no_stable_self_core_claim}",
                f"s04_contested_count={contested_count}",
            ),
        ),
        S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION: _candidate(
            cause=S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
            support=world_support,
            temporal_fit=world_temporal,
            channel_fit=world_channel,
            compatibility=world_compat,
            contamination_penalty=0.08 if world_effect_feedback_correlated else 0.16,
            evidence_basis=(
                f"world_presence_mode={world_presence_mode}",
                f"s02_external_dominance={boundary_external:.3f}",
                f"s03_world_update_weight={s03_packet.world_update_weight:.3f}",
            ),
        ),
        S05CauseClass.OBSERVATION_OR_CHANNEL_ARTIFACT: _candidate(
            cause=S05CauseClass.OBSERVATION_OR_CHANNEL_ARTIFACT,
            support=artifact_support,
            temporal_fit=artifact_temporal,
            channel_fit=artifact_channel,
            compatibility=artifact_compat,
            contamination_penalty=0.04 if observation_contaminated else 0.2,
            evidence_basis=(
                f"observation_contaminated={observation_contaminated}",
                f"s01_comparison_blocked={s01_result.state.comparison_blocked_by_contamination}",
                f"s03_observation_update_weight={s03_packet.observation_update_weight:.3f}",
            ),
        ),
    }


def _candidate(
    *,
    cause: S05CauseClass,
    support: float,
    temporal_fit: float,
    channel_fit: float,
    compatibility: float,
    contamination_penalty: float,
    evidence_basis: tuple[str, ...],
) -> dict[str, object]:
    eligibility = S05EligibilityStatus.ELIGIBLE
    if compatibility < 0.2:
        eligibility = S05EligibilityStatus.INCOMPATIBLE
    elif support < 0.18:
        eligibility = S05EligibilityStatus.INSUFFICIENT_BASIS
    elif support < 0.32:
        eligibility = S05EligibilityStatus.CAPPED
    return {
        "cause_class": cause,
        "support_strength": round(_clamp(support), 3),
        "temporal_fit": round(_clamp(temporal_fit), 3),
        "channel_fit": round(_clamp(channel_fit), 3),
        "compatibility": round(_clamp(compatibility), 3),
        "contamination_penalty": round(_clamp(contamination_penalty), 3),
        "eligibility_status": eligibility,
        "evidence_basis": evidence_basis,
    }


def _allocate_with_residual(
    *,
    slot_candidates: dict[S05CauseClass, dict[str, object]],
    packet_input: S05OutcomePacketInput,
) -> tuple[dict[S05CauseClass, float], float, float, S05ResidualClass]:
    compatible = {
        cause: float(item["support_strength"]) * float(item["compatibility"])
        for cause, item in slot_candidates.items()
        if item["eligibility_status"]
        in {S05EligibilityStatus.ELIGIBLE, S05EligibilityStatus.CAPPED}
    }
    total = sum(compatible.values())
    if total <= 0.001:
        return ({cause: 0.0 for cause in _SLOT_SEQUENCE}, 0.0, 1.0, S05ResidualClass.HIGH)

    avg_support = _clamp(
        sum(float(item["support_strength"]) for item in slot_candidates.values())
        / len(_SLOT_SEQUENCE)
    )
    avg_temporal = _clamp(
        sum(float(item["temporal_fit"]) for item in slot_candidates.values())
        / len(_SLOT_SEQUENCE)
    )
    contamination = max(float(item["contamination_penalty"]) for item in slot_candidates.values())
    explained_cap = _clamp(
        0.22
        + (0.56 * avg_support * avg_temporal)
        + (0.24 * _clamp(packet_input.mismatch_magnitude))
        - (0.16 * contamination),
        low=0.12,
        high=0.9,
    )
    allocations: dict[S05CauseClass, float] = {cause: 0.0 for cause in _SLOT_SEQUENCE}
    for cause in _SLOT_SEQUENCE:
        if cause not in compatible:
            continue
        raw = explained_cap * (compatible[cause] / total)
        if slot_candidates[cause]["eligibility_status"] is S05EligibilityStatus.CAPPED:
            raw = min(raw, 0.22)
        allocations[cause] = round(_clamp(raw), 6)
    explained_mass = _clamp(sum(allocations.values()))
    residual = _clamp(1.0 - explained_mass)
    return allocations, explained_mass, residual, _residual_class(residual)


def _apply_bounded_reattribution(
    *,
    raw_allocations: dict[S05CauseClass, float],
    residual: float,
    prior_packet: S05FactorizationPacket | None,
    late_evidence_tokens: tuple[str, ...],
    slot_candidates: dict[S05CauseClass, dict[str, object]],
) -> tuple[dict[S05CauseClass, float], float, bool, S05RevisionStatus]:
    if not isinstance(prior_packet, S05FactorizationPacket):
        return raw_allocations, residual, False, S05RevisionStatus.INITIAL_PROVISIONAL

    prior_map = _slot_share_map(prior_packet)
    compatible_now = sum(
        1
        for item in slot_candidates.values()
        if item["eligibility_status"] in {S05EligibilityStatus.ELIGIBLE, S05EligibilityStatus.CAPPED}
    )
    compatible_before = sum(
        1
        for item in prior_packet.cause_slots
        if item.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
        and item.eligibility_status in {S05EligibilityStatus.ELIGIBLE, S05EligibilityStatus.CAPPED}
    )
    late = bool(late_evidence_tokens)
    alpha = 0.55 if late else 0.24
    blended: dict[S05CauseClass, float] = {cause: 0.0 for cause in _SLOT_SEQUENCE}
    for cause in _SLOT_SEQUENCE:
        old = float(prior_map.get(cause, 0.0))
        new = float(raw_allocations.get(cause, 0.0))
        blended[cause] = _clamp(old + (new - old) * alpha)
    explained = _clamp(sum(blended.values()))
    new_residual = _clamp(1.0 - explained)
    prior_residual = float(prior_map.get(S05CauseClass.UNEXPLAINED_RESIDUAL, 1.0))
    if not late and new_residual < prior_residual and compatible_now <= compatible_before:
        # Bounded re-attribution: residual may only shrink materially if compatible evidence expands.
        new_residual = max(prior_residual - 0.03, new_residual)
        explained = _clamp(1.0 - new_residual)
        scale = 0.0 if sum(blended.values()) <= 0 else explained / sum(blended.values())
        for cause in _SLOT_SEQUENCE:
            blended[cause] = _clamp(blended[cause] * scale)
    reattribution_happened = (
        abs(new_residual - prior_residual) >= 0.04
        or any(abs(blended[cause] - float(prior_map.get(cause, 0.0))) >= 0.04 for cause in _SLOT_SEQUENCE)
    )
    if reattribution_happened and late:
        revision = S05RevisionStatus.REVISED_WITH_LATE_EVIDENCE
    else:
        revision = S05RevisionStatus.STABLE_NO_REVISION
    return blended, new_residual, reattribution_happened, revision


def _build_slot_entry(
    *,
    cause_class: S05CauseClass,
    candidate: dict[str, object],
    allocation: float,
    confidence: float,
    bounded_interval_only: bool,
) -> S05CauseSlotEntry:
    interval = (
        (round(_clamp(allocation - 0.12), 3), round(_clamp(allocation + 0.12), 3))
        if confidence < 0.55 or bounded_interval_only
        else (round(allocation, 3), round(allocation, 3))
    )
    allocated = None if confidence < 0.55 or bounded_interval_only else round(allocation, 3)
    return S05CauseSlotEntry(
        cause_class=cause_class,
        eligibility_status=candidate["eligibility_status"],
        support_strength=round(float(candidate["support_strength"]), 3),
        allocated_share=allocated,
        bounded_share_interval=interval,
        evidence_basis=tuple(str(item) for item in candidate["evidence_basis"]),
        temporal_fit=round(float(candidate["temporal_fit"]), 3),
        channel_fit=round(float(candidate["channel_fit"]), 3),
        contamination_penalty=round(float(candidate["contamination_penalty"]), 3),
        provenance="s05.multi_cause_attribution.slot_entry",
    )


def _build_residual_entry(
    *,
    residual: float,
    residual_class: S05ResidualClass,
    confidence: float,
) -> S05CauseSlotEntry:
    interval = (
        (round(_clamp(residual - 0.1), 3), round(_clamp(residual + 0.1), 3))
        if confidence < 0.55
        else (round(residual, 3), round(residual, 3))
    )
    allocated = None if confidence < 0.55 else round(residual, 3)
    return S05CauseSlotEntry(
        cause_class=S05CauseClass.UNEXPLAINED_RESIDUAL,
        eligibility_status=S05EligibilityStatus.ELIGIBLE,
        support_strength=round(residual, 3),
        allocated_share=allocated,
        bounded_share_interval=interval,
        evidence_basis=(f"residual_class={residual_class.value}",),
        temporal_fit=1.0,
        channel_fit=1.0,
        contamination_penalty=0.0,
        provenance="s05.multi_cause_attribution.residual_slot",
    )


def _derive_attribution_status(
    *,
    slot_candidates: dict[S05CauseClass, dict[str, object]],
    allocations: dict[S05CauseClass, float],
    residual: float,
    confidence: float,
) -> S05AttributionStatus:
    eligible = [
        cause
        for cause, item in slot_candidates.items()
        if item["eligibility_status"] in {S05EligibilityStatus.ELIGIBLE, S05EligibilityStatus.CAPPED}
    ]
    incompatible = [
        cause
        for cause, item in slot_candidates.items()
        if item["eligibility_status"] is S05EligibilityStatus.INCOMPATIBLE
    ]
    if not eligible:
        if len(incompatible) >= 3:
            return S05AttributionStatus.INCOMPATIBLE_CAUSE_CANDIDATES
        return S05AttributionStatus.INSUFFICIENT_FACTOR_BASIS
    if residual >= 0.72:
        return S05AttributionStatus.RESIDUAL_TOO_LARGE
    shares = [allocations.get(cause, 0.0) for cause in eligible]
    if len(shares) >= 2 and (max(shares) - min(shares)) <= 0.08 and confidence < 0.62:
        return S05AttributionStatus.UNDERDETERMINED_SPLIT
    if confidence < 0.55:
        return S05AttributionStatus.BOUNDED_INTERVAL_ONLY
    if residual >= 0.45:
        return S05AttributionStatus.NO_CLEAN_FACTORIZATION_CLAIM
    return S05AttributionStatus.FACTORIZED_MULTI_CAUSE


def _derive_confidence(
    *,
    slot_candidates: dict[S05CauseClass, dict[str, object]],
    residual: float,
    context_shift_detected: bool,
    c05_revalidation_required: bool,
) -> float:
    support = _clamp(
        sum(float(item["support_strength"]) for item in slot_candidates.values()) / len(_SLOT_SEQUENCE)
    )
    temporal = _clamp(
        sum(float(item["temporal_fit"]) for item in slot_candidates.values()) / len(_SLOT_SEQUENCE)
    )
    contamination = max(float(item["contamination_penalty"]) for item in slot_candidates.values())
    score = (
        0.16
        + (support * 0.34)
        + (temporal * 0.2)
        + ((1.0 - residual) * 0.24)
        - (contamination * 0.2)
    )
    if context_shift_detected:
        score -= 0.07
    if c05_revalidation_required:
        score -= 0.09
    return round(_clamp(score, low=0.05, high=0.94), 3)


def _derive_scope_validity(
    *,
    attribution_status: S05AttributionStatus,
    residual: float,
    c05_revalidation_required: bool,
) -> S05ScopeValidity:
    if attribution_status in {
        S05AttributionStatus.INSUFFICIENT_FACTOR_BASIS,
        S05AttributionStatus.INCOMPATIBLE_CAUSE_CANDIDATES,
    }:
        return S05ScopeValidity.INVALID_FOR_STRONG_CLAIMS
    if c05_revalidation_required or residual >= 0.45:
        return S05ScopeValidity.PROVISIONAL_REQUIRES_REVALIDATION
    return S05ScopeValidity.BOUNDED_VALID_FOR_ROUTING


def _derive_downstream_route(
    allocations: dict[S05CauseClass, float],
    residual: float,
) -> S05DownstreamRouteClass:
    if residual >= 0.55:
        return S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED
    ranked = sorted(allocations.items(), key=lambda pair: pair[1], reverse=True)
    if len(ranked) >= 2 and ranked[0][1] >= 0.2 and ranked[1][1] >= 0.2 and ranked[0][1] < 0.45:
        return S05DownstreamRouteClass.MIXED_FACTORIZED
    top_cause = ranked[0][0] if ranked else S05CauseClass.UNEXPLAINED_RESIDUAL
    if top_cause is S05CauseClass.SELF_INITIATED_ACT:
        return S05DownstreamRouteClass.SELF_ACT_HEAVY
    if top_cause is S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION:
        return S05DownstreamRouteClass.MODE_DRIFT_HEAVY
    if top_cause is S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT:
        return S05DownstreamRouteClass.INTEROCEPTIVE_DRIFT_HEAVY
    if top_cause is S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION:
        return S05DownstreamRouteClass.WORLD_HEAVY
    if top_cause is S05CauseClass.OBSERVATION_OR_CHANNEL_ARTIFACT:
        return S05DownstreamRouteClass.OBSERVATION_ARTIFACT_HEAVY
    return S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED


def _dominant_cause_classes(
    allocations: dict[S05CauseClass, float],
    residual: float,
) -> tuple[S05CauseClass, ...]:
    dominant = [
        cause
        for cause, share in sorted(allocations.items(), key=lambda pair: pair[1], reverse=True)
        if share >= 0.2
    ][:2]
    if residual >= 0.4:
        dominant.append(S05CauseClass.UNEXPLAINED_RESIDUAL)
    if not dominant:
        dominant.append(S05CauseClass.UNEXPLAINED_RESIDUAL)
    return tuple(dict.fromkeys(dominant))


def _compatibility_basis(slot_candidates: dict[S05CauseClass, dict[str, object]]) -> tuple[str, ...]:
    return tuple(
        f"{cause.value}:{item['eligibility_status'].value}@compat={float(item['compatibility']):.3f}"
        for cause, item in slot_candidates.items()
    )


def _temporal_alignment_basis(
    slot_candidates: dict[S05CauseClass, dict[str, object]],
    packet_input: S05OutcomePacketInput,
) -> tuple[str, ...]:
    return (
        f"observed_tick={packet_input.observed_tick}",
        f"preferred_tick={packet_input.preferred_tick}",
        f"expires_tick={packet_input.expires_tick}",
        *(
            f"{cause.value}:temporal_fit={float(item['temporal_fit']):.3f}"
            for cause, item in slot_candidates.items()
        ),
    )


def _contamination_notes(
    slot_candidates: dict[S05CauseClass, dict[str, object]],
    packet_input: S05OutcomePacketInput,
) -> tuple[str, ...]:
    notes = [f"outcome_packet_contaminated={packet_input.contaminated}"]
    for cause, item in slot_candidates.items():
        penalty = float(item["contamination_penalty"])
        if penalty >= 0.35:
            notes.append(f"{cause.value}:contamination_penalty={penalty:.3f}")
    return tuple(notes)


def _build_gate(
    *,
    attribution_status: S05AttributionStatus,
    residual: float,
    slot_candidates: dict[S05CauseClass, dict[str, object]],
    downstream_route: S05DownstreamRouteClass,
) -> S05AttributionGateDecision:
    eligible_count = len(
        [
            item
            for item in slot_candidates.values()
            if item["eligibility_status"] in {S05EligibilityStatus.ELIGIBLE, S05EligibilityStatus.CAPPED}
        ]
    )
    factorization_ready = attribution_status not in {
        S05AttributionStatus.INSUFFICIENT_FACTOR_BASIS,
        S05AttributionStatus.INCOMPATIBLE_CAUSE_CANDIDATES,
    }
    learning_route_ready = (
        factorization_ready
        and residual < 0.52
        and downstream_route is not S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED
    )
    no_binary_recollapse = eligible_count >= 2 or residual >= 0.3
    restrictions = [
        "s05_factorization_contract_must_be_read",
        "s05_internal_causes_must_not_collapse_into_binary_self_bucket",
        "s05_residual_must_not_be_forced_to_zero",
        "s05_temporal_alignment_must_gate_slot_eligibility",
    ]
    if not factorization_ready:
        restrictions.append("s05_factorization_consumer_not_ready")
    if not learning_route_ready:
        restrictions.append("s05_learning_route_not_ready")
    if no_binary_recollapse:
        restrictions.append("s05_single_cause_collapse_forbidden")
    return S05AttributionGateDecision(
        factorization_consumer_ready=factorization_ready,
        learning_route_ready=learning_route_ready,
        no_binary_recollapse_required=no_binary_recollapse,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="s05 emitted bounded multi-cause attribution packet with explicit residual and compatibility filtering",
    )


def _build_scope_marker() -> S05ScopeMarker:
    return S05ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        s05_first_slice_only=True,
        downstream_rollout_minimal=True,
        repo_wide_adoption=False,
        reason="first bounded s05 slice only; no broad downstream rollout and no global causal engine",
    )


def _slot_share_map(packet: S05FactorizationPacket) -> dict[S05CauseClass, float]:
    mapping: dict[S05CauseClass, float] = {}
    for entry in packet.cause_slots:
        if entry.allocated_share is not None:
            mapping[entry.cause_class] = float(entry.allocated_share)
            continue
        interval = entry.bounded_share_interval or (0.0, 0.0)
        mapping[entry.cause_class] = float((interval[0] + interval[1]) / 2.0)
    return mapping


def _latest_packet(
    state: S05MultiCauseAttributionState | None,
) -> S05FactorizationPacket | None:
    if not isinstance(state, S05MultiCauseAttributionState):
        return None
    if not state.packets:
        return None
    return state.packets[-1]


def _residual_class(value: float) -> S05ResidualClass:
    if value >= 0.55:
        return S05ResidualClass.HIGH
    if value >= 0.25:
        return S05ResidualClass.MEDIUM
    return S05ResidualClass.LOW


def _temporal_fit(
    *,
    observed_tick: int,
    preferred_tick: int,
    expires_tick: int,
    c05_revalidation_required: bool,
    c05_validity_action: str,
    context_shift_detected: bool,
) -> float:
    delta = abs(int(observed_tick) - int(preferred_tick))
    fit = _clamp(1.0 - (delta * 0.28))
    if int(observed_tick) > int(expires_tick):
        fit = min(fit, 0.16)
    if c05_revalidation_required:
        fit -= 0.18
    if str(c05_validity_action or "").strip() in {
        "run_selective_revalidation",
        "run_bounded_revalidation",
        "suspend_until_revalidation_basis",
    }:
        fit -= 0.12
    if context_shift_detected:
        fit -= 0.08
    return round(_clamp(fit), 3)


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    packet_input: S05OutcomePacketInput,
    source_lineage: tuple[str, ...],
) -> S05MultiCauseAttributionResult:
    residual_entry = _build_residual_entry(
        residual=1.0,
        residual_class=S05ResidualClass.HIGH,
        confidence=0.1,
    )
    packet = S05FactorizationPacket(
        outcome_packet_id=packet_input.outcome_packet_id,
        cause_slots=(residual_entry,),
        slot_weights_or_bounded_shares=((S05CauseClass.UNEXPLAINED_RESIDUAL.value, (0.9, 1.0)),),
        unexplained_residual=1.0,
        residual_class=S05ResidualClass.HIGH,
        compatibility_basis=("s05_factorization_disabled",),
        temporal_alignment_basis=("s05_factorization_disabled",),
        contamination_notes=("s05_factorization_disabled",),
        confidence=0.1,
        provenance="s05.multi_cause_attribution.disabled",
        revision_status=S05RevisionStatus.INITIAL_PROVISIONAL,
        attribution_status=S05AttributionStatus.INSUFFICIENT_FACTOR_BASIS,
        scope_validity=S05ScopeValidity.INVALID_FOR_STRONG_CLAIMS,
        downstream_route_class=S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
    )
    gate = S05AttributionGateDecision(
        factorization_consumer_ready=False,
        learning_route_ready=False,
        no_binary_recollapse_required=True,
        restrictions=(
            "s05_factorization_contract_must_be_read",
            "s05_factorization_disabled_in_ablation_context",
            "s05_single_cause_collapse_forbidden",
        ),
        reason="s05 factorization disabled; residual-only packet emitted",
    )
    state = S05MultiCauseAttributionState(
        factorization_id=f"s05-factorization:{tick_id}",
        tick_index=tick_index,
        packets=(packet,),
        latest_packet_id=packet.outcome_packet_id,
        dominant_cause_classes=(S05CauseClass.UNEXPLAINED_RESIDUAL,),
        unexplained_residual=1.0,
        residual_class=S05ResidualClass.HIGH,
        underdetermined_split=True,
        incompatible_candidates_present=False,
        temporal_misalignment_present=False,
        contamination_present=False,
        reattribution_happened=False,
        source_lineage=source_lineage,
        last_update_provenance="s05.multi_cause_attribution.disabled",
    )
    telemetry = S05Telemetry(
        factorization_id=state.factorization_id,
        tick_index=state.tick_index,
        dominant_slot_count=1,
        residual_share=1.0,
        residual_class=S05ResidualClass.HIGH,
        underdetermined_split=True,
        contamination_present=False,
        temporal_misalignment_present=False,
        reattribution_happened=False,
        downstream_route_class=S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
        factorization_consumer_ready=False,
        learning_route_ready=False,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S05MultiCauseAttributionResult(
        state=state,
        gate=gate,
        scope_marker=_build_scope_marker(),
        telemetry=telemetry,
        reason="s05 multi-cause attribution disabled",
    )


def _clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))
