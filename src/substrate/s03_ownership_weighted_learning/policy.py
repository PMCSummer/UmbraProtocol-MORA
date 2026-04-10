from __future__ import annotations

from substrate.s01_efference_copy import (
    S01ComparisonStatus,
    S01EfferenceCopyResult,
)
from substrate.s02_prediction_boundary import (
    S02BoundaryStatus,
    S02PredictionBoundaryResult,
)
from substrate.s03_ownership_weighted_learning.models import (
    S03AmbiguityClass,
    S03CandidateTargetClass,
    S03CommitClass,
    S03FreezeOrDeferStatus,
    S03LearningAttributionPacket,
    S03LearningGateDecision,
    S03OwnershipUpdateClass,
    S03OwnershipWeightedLearningResult,
    S03OwnershipWeightedLearningState,
    S03ScopeMarker,
    S03TargetAllocation,
    S03Telemetry,
)


_MISMATCH_STATUSES = {
    S01ComparisonStatus.MAGNITUDE_MISMATCH,
    S01ComparisonStatus.DIRECTION_MISMATCH,
    S01ComparisonStatus.LATENCY_MISMATCH,
    S01ComparisonStatus.EXPECTED_BUT_UNOBSERVED,
    S01ComparisonStatus.UNEXPECTED_CHANGE_DETECTED,
}


def build_s03_ownership_weighted_learning(
    *,
    tick_id: str,
    tick_index: int,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    c04_selected_mode: str,
    c05_validity_action: str,
    c05_revalidation_required: bool,
    c05_dependency_contaminated: bool,
    c05_no_safe_reuse: bool,
    context_shift_detected: bool,
    prior_state: S03OwnershipWeightedLearningState | None = None,
    source_lineage: tuple[str, ...] = (),
    ownership_weighting_enabled: bool = True,
    repeated_evidence_enabled: bool = True,
) -> S03OwnershipWeightedLearningResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if tick_index < 1:
        raise ValueError("tick_index must be >= 1")
    if not isinstance(s01_result, S01EfferenceCopyResult):
        raise TypeError("s01_result must be S01EfferenceCopyResult")
    if not isinstance(s02_result, S02PredictionBoundaryResult):
        raise TypeError("s02_result must be S02PredictionBoundaryResult")

    boundary_status = s02_result.state.active_boundary_status
    latest_status = s01_result.state.latest_comparison_status
    mixed_score = max(
        (item.mixed_source_score for item in s02_result.state.seam_entries),
        default=0.0,
    )
    boundary_confidence = max(
        (item.boundary_confidence for item in s02_result.state.seam_entries),
        default=0.0,
    )
    controllability = max(
        (item.controllability_estimate for item in s02_result.state.seam_entries),
        default=0.0,
    )
    external_dominance = max(
        (item.external_dominance_estimate for item in s02_result.state.seam_entries),
        default=0.0,
    )

    stale_or_invalidated = bool(
        c05_no_safe_reuse
        or c05_dependency_contaminated
        or c05_revalidation_required
        or c05_validity_action
        in {
            "run_selective_revalidation",
            "run_bounded_revalidation",
            "suspend_until_revalidation_basis",
            "halt_reuse_and_rebuild_scope",
        }
        or context_shift_detected
    )
    observation_suspicion = bool(
        s01_result.state.comparison_blocked_by_contamination
        or boundary_status
        in {
            S02BoundaryStatus.BOUNDARY_UNCERTAIN,
            S02BoundaryStatus.INSUFFICIENT_COVERAGE,
            S02BoundaryStatus.NO_CLEAN_SEAM_CLAIM,
            S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT,
        }
        or s02_result.state.boundary_uncertain
        or s02_result.state.no_clean_seam_claim
    )
    mixed_source = bool(
        boundary_status is S02BoundaryStatus.MIXED_SOURCE_BOUNDARY or mixed_score >= 0.45
    )
    self_side = boundary_status in {
        S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM,
        S02BoundaryStatus.CONTROLLABLE_BUT_UNRELIABLE,
    }
    world_side = boundary_status in {
        S02BoundaryStatus.EXTERNALLY_DOMINATED_BOUNDARY,
        S02BoundaryStatus.PREDICTABLE_BUT_NOT_SELF_DRIVEN,
    } or bool(s01_result.gate.unexpected_change_detected)

    repeated_self_support = _seed_repeated_support(prior_state, "self")
    repeated_world_support = _seed_repeated_support(prior_state, "world")
    repeated_mixed_support = _seed_repeated_support(prior_state, "mixed")
    if repeated_evidence_enabled:
        if self_side and latest_status in _MISMATCH_STATUSES:
            repeated_self_support += 1
        if world_side and latest_status in _MISMATCH_STATUSES:
            repeated_world_support += 1
        if mixed_source:
            repeated_mixed_support += 1
    else:
        repeated_self_support = 1 if self_side else 0
        repeated_world_support = 1 if world_side else 0
        repeated_mixed_support = 1 if mixed_source else 0

    if not ownership_weighting_enabled:
        update_class = S03OwnershipUpdateClass.NO_SAFE_UPDATE
        commit_class = S03CommitClass.BLOCK_DUE_TO_CONFLICT
        ambiguity_class = S03AmbiguityClass.INSUFFICIENT_OWNERSHIP_BASIS
        freeze_status = S03FreezeOrDeferStatus.BLOCKED
        self_w = 0.0
        world_w = 0.0
        obs_w = 0.0
        anomaly_w = 0.0
    elif stale_or_invalidated:
        update_class = S03OwnershipUpdateClass.NO_SAFE_UPDATE
        commit_class = S03CommitClass.DEFER_UNTIL_REVALIDATION
        ambiguity_class = S03AmbiguityClass.FREEZE_PENDING_REVALIDATION
        freeze_status = S03FreezeOrDeferStatus.FROZEN
        self_w = 0.0
        world_w = 0.0
        obs_w = 0.0
        anomaly_w = 0.0
    else:
        update_class, commit_class, ambiguity_class, freeze_status = _choose_route_classes(
            self_side=self_side,
            world_side=world_side,
            mixed_source=mixed_source,
            observation_suspicion=observation_suspicion,
            unexpected=s01_result.gate.unexpected_change_detected,
        )
        scale = _derive_capped_scale(
            latest_status=latest_status,
            repeated_self_support=repeated_self_support,
            repeated_world_support=repeated_world_support,
            repeated_mixed_support=repeated_mixed_support,
            mixed_source=mixed_source,
        )
        self_w, world_w, obs_w, anomaly_w = _derive_weights(
            update_class=update_class,
            scale=scale,
            controllability=controllability,
            external_dominance=external_dominance,
            unexpected=s01_result.gate.unexpected_change_detected,
            observation_suspicion=observation_suspicion,
        )

    confidence = _derive_confidence(
        boundary_confidence=boundary_confidence,
        stale_or_invalidated=stale_or_invalidated,
        ambiguity_class=ambiguity_class,
        repeated_support=max(repeated_self_support, repeated_world_support, repeated_mixed_support),
    )
    target_allocations = _build_target_allocations(
        self_w=self_w,
        world_w=world_w,
        obs_w=obs_w,
        anomaly_w=anomaly_w,
    )
    target_classes = tuple(item.target_class for item in target_allocations)
    repeated_support = max(
        repeated_self_support,
        repeated_world_support,
        repeated_mixed_support,
    )
    convergent_support = repeated_support >= 2
    update_scope = (
        "rt01_local_learning_packet"
        if commit_class
        in {
            S03CommitClass.COMMIT_UPDATE,
            S03CommitClass.CAP_UPDATE_MAGNITUDE,
            S03CommitClass.ROUTE_TO_WORLD_MODEL_ONLY,
            S03CommitClass.ROUTE_TO_INTERNAL_MODEL_ONLY,
            S03CommitClass.SPLIT_ACROSS_TARGETS,
        }
        else "rt01_local_deferred_update_packet"
    )
    packet = S03LearningAttributionPacket(
        outcome_packet_id=f"s03-packet:{tick_id}:{tick_index}",
        attribution_basis=(
            f"s01_status={latest_status.value if latest_status is not None else 'none'}",
            f"s02_status={boundary_status.value}",
            f"c04_mode={c04_selected_mode}",
            f"c05_action={c05_validity_action}",
            f"mixed_score={mixed_score:.3f}",
            f"controllability={controllability:.3f}",
            f"external_dominance={external_dominance:.3f}",
        ),
        update_class=update_class,
        commit_class=commit_class,
        ambiguity_class=ambiguity_class,
        self_update_weight=self_w,
        world_update_weight=world_w,
        observation_update_weight=obs_w,
        anomaly_update_weight=anomaly_w,
        freeze_or_defer_status=freeze_status,
        target_model_classes=target_classes,
        target_allocations=target_allocations,
        update_scope=update_scope,
        confidence=confidence,
        repeated_support=repeated_support,
        convergent_support=convergent_support,
        validity_status=(
            "stale_or_invalidated"
            if stale_or_invalidated
            else "bounded_valid_for_routing"
        ),
        stale_or_invalidated=stale_or_invalidated,
        provenance="s03.ownership_weighted_learning.packet_routing",
    )
    packets = (packet,)
    if isinstance(prior_state, S03OwnershipWeightedLearningState):
        packets = (*prior_state.packets, packet)
        if len(packets) > 6:
            packets = packets[-6:]

    gate = _build_gate(
        packet=packet,
        ownership_weighting_enabled=ownership_weighting_enabled,
    )
    state = S03OwnershipWeightedLearningState(
        learning_id=f"s03-learning:{tick_id}",
        tick_index=tick_index,
        packets=tuple(packets),
        latest_packet_id=packet.outcome_packet_id,
        latest_update_class=packet.update_class,
        latest_commit_class=packet.commit_class,
        latest_ambiguity_class=packet.ambiguity_class,
        freeze_or_defer_state=packet.freeze_or_defer_status,
        requested_revalidation=packet.freeze_or_defer_status
        in {
            S03FreezeOrDeferStatus.DEFERRED,
            S03FreezeOrDeferStatus.FROZEN,
            S03FreezeOrDeferStatus.BLOCKED,
        },
        repeated_self_support=repeated_self_support,
        repeated_world_support=repeated_world_support,
        repeated_mixed_support=repeated_mixed_support,
        source_lineage=tuple(
            dict.fromkeys((*source_lineage, *s01_result.state.source_lineage, *s02_result.state.source_lineage))
        ),
        last_update_provenance="s03.ownership_weighted_learning.first_bounded_slice",
    )
    telemetry = S03Telemetry(
        learning_id=state.learning_id,
        tick_index=state.tick_index,
        latest_packet_id=state.latest_packet_id,
        latest_update_class=state.latest_update_class.value,
        latest_commit_class=state.latest_commit_class.value,
        freeze_or_defer_state=state.freeze_or_defer_state.value,
        requested_revalidation=state.requested_revalidation,
        self_update_weight=packet.self_update_weight,
        world_update_weight=packet.world_update_weight,
        observation_update_weight=packet.observation_update_weight,
        anomaly_update_weight=packet.anomaly_update_weight,
        repeated_self_support=state.repeated_self_support,
        repeated_world_support=state.repeated_world_support,
        repeated_mixed_support=state.repeated_mixed_support,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S03OwnershipWeightedLearningResult(
        state=state,
        gate=gate,
        scope_marker=_build_scope_marker(),
        telemetry=telemetry,
        reason="s03.first_bounded_ownership_weighted_learning_slice",
    )


def _choose_route_classes(
    *,
    self_side: bool,
    world_side: bool,
    mixed_source: bool,
    observation_suspicion: bool,
    unexpected: bool,
) -> tuple[
    S03OwnershipUpdateClass,
    S03CommitClass,
    S03AmbiguityClass | None,
    S03FreezeOrDeferStatus,
]:
    if mixed_source:
        return (
            S03OwnershipUpdateClass.MIXED_SPLIT_UPDATE,
            S03CommitClass.SPLIT_ACROSS_TARGETS,
            S03AmbiguityClass.MIXED_SOURCE_UPDATE_ONLY,
            S03FreezeOrDeferStatus.CAPPED,
        )
    if self_side and not world_side:
        return (
            S03OwnershipUpdateClass.SELF_UPDATE_DOMINANT,
            S03CommitClass.ROUTE_TO_INTERNAL_MODEL_ONLY,
            None,
            S03FreezeOrDeferStatus.CAPPED,
        )
    if world_side and not self_side:
        if observation_suspicion:
            return (
                S03OwnershipUpdateClass.OBSERVATION_CHANNEL_RECALIBRATION_CANDIDATE,
                S03CommitClass.CAP_UPDATE_MAGNITUDE,
                None,
                S03FreezeOrDeferStatus.CAPPED,
            )
        if unexpected:
            return (
                S03OwnershipUpdateClass.ANOMALY_ONLY_ROUTING,
                S03CommitClass.CAP_UPDATE_MAGNITUDE,
                None,
                S03FreezeOrDeferStatus.CAPPED,
            )
        return (
            S03OwnershipUpdateClass.WORLD_UPDATE_DOMINANT,
            S03CommitClass.ROUTE_TO_WORLD_MODEL_ONLY,
            None,
            S03FreezeOrDeferStatus.CAPPED,
        )
    if observation_suspicion:
        return (
            S03OwnershipUpdateClass.OBSERVATION_CHANNEL_RECALIBRATION_CANDIDATE,
            S03CommitClass.CAP_UPDATE_MAGNITUDE,
            S03AmbiguityClass.INSUFFICIENT_OWNERSHIP_BASIS,
            S03FreezeOrDeferStatus.CAPPED,
        )
    return (
        S03OwnershipUpdateClass.NO_SAFE_UPDATE,
        S03CommitClass.BLOCK_DUE_TO_CONFLICT,
        S03AmbiguityClass.ATTRIBUTION_CONFLICT,
        S03FreezeOrDeferStatus.BLOCKED,
    )


def _derive_capped_scale(
    *,
    latest_status: S01ComparisonStatus | None,
    repeated_self_support: int,
    repeated_world_support: int,
    repeated_mixed_support: int,
    mixed_source: bool,
) -> float:
    if latest_status is None:
        one_shot = 0.2
    elif latest_status in {
        S01ComparisonStatus.MATCHED_AS_EXPECTED,
        S01ComparisonStatus.PARTIAL_MATCH,
    }:
        one_shot = 0.3
    elif latest_status in _MISMATCH_STATUSES:
        one_shot = 0.55
    else:
        one_shot = 0.4
    repeated = max(repeated_self_support, repeated_world_support, repeated_mixed_support)
    boost = min(0.25, max(0, repeated - 1) * 0.08)
    if mixed_source:
        boost = min(boost, 0.12)
    return round(min(0.85, one_shot + boost), 3)


def _derive_weights(
    *,
    update_class: S03OwnershipUpdateClass,
    scale: float,
    controllability: float,
    external_dominance: float,
    unexpected: bool,
    observation_suspicion: bool,
) -> tuple[float, float, float, float]:
    self_w = 0.0
    world_w = 0.0
    obs_w = 0.0
    anomaly_w = 0.0
    if update_class is S03OwnershipUpdateClass.SELF_UPDATE_DOMINANT:
        self_w = max(0.1, scale * max(0.55, controllability))
        world_w = min(0.15, scale * 0.18)
    elif update_class is S03OwnershipUpdateClass.WORLD_UPDATE_DOMINANT:
        world_w = max(0.1, scale * max(0.55, external_dominance))
        obs_w = min(0.18, scale * 0.22 if observation_suspicion else 0.08)
    elif update_class is S03OwnershipUpdateClass.MIXED_SPLIT_UPDATE:
        split = scale * 0.45
        self_w = split
        world_w = split
        obs_w = min(0.18, scale * 0.18)
    elif update_class is S03OwnershipUpdateClass.OBSERVATION_CHANNEL_RECALIBRATION_CANDIDATE:
        obs_w = max(0.1, scale * 0.6)
        world_w = min(0.2, scale * 0.2)
    elif update_class is S03OwnershipUpdateClass.ANOMALY_ONLY_ROUTING:
        anomaly_w = max(0.1, scale * (0.65 if unexpected else 0.5))
        obs_w = min(0.15, scale * 0.2)

    total = self_w + world_w + obs_w + anomaly_w
    if total <= 0:
        return 0.0, 0.0, 0.0, 0.0
    if total > 1.0:
        self_w /= total
        world_w /= total
        obs_w /= total
        anomaly_w /= total
    return (
        round(self_w, 3),
        round(world_w, 3),
        round(obs_w, 3),
        round(anomaly_w, 3),
    )


def _build_target_allocations(
    *,
    self_w: float,
    world_w: float,
    obs_w: float,
    anomaly_w: float,
) -> tuple[S03TargetAllocation, ...]:
    allocations: list[S03TargetAllocation] = []
    if self_w > 0:
        allocations.append(
            S03TargetAllocation(
                target_class=S03CandidateTargetClass.INTERNAL_CONTROL_PREDICTION,
                weight=round(self_w, 3),
            )
        )
    if world_w > 0:
        allocations.append(
            S03TargetAllocation(
                target_class=S03CandidateTargetClass.WORLD_SIDE_PREDICTION,
                weight=round(world_w, 3),
            )
        )
    if obs_w > 0:
        allocations.append(
            S03TargetAllocation(
                target_class=S03CandidateTargetClass.OBSERVATION_CALIBRATION,
                weight=round(obs_w, 3),
            )
        )
    if anomaly_w > 0:
        allocations.append(
            S03TargetAllocation(
                target_class=S03CandidateTargetClass.ANOMALY_CHANNEL,
                weight=round(anomaly_w, 3),
            )
        )
    return tuple(allocations)


def _derive_confidence(
    *,
    boundary_confidence: float,
    stale_or_invalidated: bool,
    ambiguity_class: S03AmbiguityClass | None,
    repeated_support: int,
) -> float:
    if stale_or_invalidated:
        return 0.15
    score = 0.25 + (boundary_confidence * 0.55)
    score += min(0.15, max(0, repeated_support - 1) * 0.04)
    if ambiguity_class is not None:
        score -= 0.15
    return round(max(0.05, min(0.95, score)), 3)


def _build_gate(
    *,
    packet: S03LearningAttributionPacket,
    ownership_weighting_enabled: bool,
) -> S03LearningGateDecision:
    learning_ready = bool(
        ownership_weighting_enabled
        and packet.commit_class
        not in {
            S03CommitClass.DEFER_UNTIL_REVALIDATION,
            S03CommitClass.BLOCK_DUE_TO_CONFLICT,
        }
        and (
            packet.self_update_weight
            + packet.world_update_weight
            + packet.observation_update_weight
            + packet.anomaly_update_weight
        )
        > 0
    )
    mixed_ready = bool(
        packet.update_class is S03OwnershipUpdateClass.MIXED_SPLIT_UPDATE
        and packet.self_update_weight > 0
        and packet.world_update_weight > 0
        and packet.commit_class is S03CommitClass.SPLIT_ACROSS_TARGETS
    )
    freeze_ready = packet.freeze_or_defer_status not in {
        S03FreezeOrDeferStatus.FROZEN,
        S03FreezeOrDeferStatus.BLOCKED,
    }
    restrictions = [
        "s03_learning_packet_contract_must_be_read",
        "s03_same_error_magnitude_must_not_collapse_to_uniform_update",
        "s03_mixed_source_must_not_collapse_to_binary_blame",
        "s03_stale_or_invalidated_basis_must_weaken_or_freeze",
    ]
    if not learning_ready:
        restrictions.append("s03_learning_packet_consumer_not_ready")
    if not mixed_ready:
        restrictions.append("s03_mixed_update_consumer_not_ready")
    if not freeze_ready:
        restrictions.append("s03_freeze_obedience_consumer_not_ready")
    return S03LearningGateDecision(
        learning_packet_consumer_ready=learning_ready,
        mixed_update_consumer_ready=mixed_ready,
        freeze_obedience_consumer_ready=freeze_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "s03 mapped s01/s02/c05/context signals into bounded ownership-weighted update packet routing"
        ),
    )


def _build_scope_marker() -> S03ScopeMarker:
    return S03ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        s03_first_slice_only=True,
        s04_implemented=False,
        s05_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded s03 slice only; no global learner engine and no s04/s05 rollout"
        ),
    )


def _seed_repeated_support(
    prior_state: S03OwnershipWeightedLearningState | None,
    key: str,
) -> int:
    if not isinstance(prior_state, S03OwnershipWeightedLearningState):
        return 0
    if key == "self":
        return prior_state.repeated_self_support
    if key == "world":
        return prior_state.repeated_world_support
    return prior_state.repeated_mixed_support
