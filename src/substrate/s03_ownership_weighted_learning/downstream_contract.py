from __future__ import annotations

from dataclasses import dataclass

from substrate.s03_ownership_weighted_learning.models import (
    S03OwnershipWeightedLearningResult,
)


@dataclass(frozen=True, slots=True)
class S03LearningContractView:
    learning_id: str
    tick_index: int
    latest_packet_id: str
    latest_update_class: str
    latest_commit_class: str
    latest_ambiguity_class: str | None
    freeze_or_defer_state: str
    requested_revalidation: bool
    self_update_weight: float
    world_update_weight: float
    observation_update_weight: float
    anomaly_update_weight: float
    target_model_classes: tuple[str, ...]
    confidence: float
    repeated_support: int
    convergent_support: bool
    validity_status: str
    stale_or_invalidated: bool
    learning_packet_consumer_ready: bool
    mixed_update_consumer_ready: bool
    freeze_obedience_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_s03_first_slice_only: bool
    scope_s04_implemented: bool
    scope_s05_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class S03UpdatePacketConsumerView:
    learning_id: str
    can_consume_learning_packet: bool
    can_consume_mixed_update: bool
    can_obey_freeze: bool
    freeze_or_defer_state: str
    latest_update_class: str
    restrictions: tuple[str, ...]
    reason: str


def derive_s03_learning_contract_view(
    result: S03OwnershipWeightedLearningResult,
) -> S03LearningContractView:
    if not isinstance(result, S03OwnershipWeightedLearningResult):
        raise TypeError(
            "derive_s03_learning_contract_view requires S03OwnershipWeightedLearningResult"
        )
    packet = result.state.packets[-1]
    return S03LearningContractView(
        learning_id=result.state.learning_id,
        tick_index=result.state.tick_index,
        latest_packet_id=result.state.latest_packet_id,
        latest_update_class=result.state.latest_update_class.value,
        latest_commit_class=result.state.latest_commit_class.value,
        latest_ambiguity_class=(
            None
            if result.state.latest_ambiguity_class is None
            else result.state.latest_ambiguity_class.value
        ),
        freeze_or_defer_state=result.state.freeze_or_defer_state.value,
        requested_revalidation=result.state.requested_revalidation,
        self_update_weight=packet.self_update_weight,
        world_update_weight=packet.world_update_weight,
        observation_update_weight=packet.observation_update_weight,
        anomaly_update_weight=packet.anomaly_update_weight,
        target_model_classes=tuple(item.value for item in packet.target_model_classes),
        confidence=packet.confidence,
        repeated_support=packet.repeated_support,
        convergent_support=packet.convergent_support,
        validity_status=packet.validity_status,
        stale_or_invalidated=packet.stale_or_invalidated,
        learning_packet_consumer_ready=result.gate.learning_packet_consumer_ready,
        mixed_update_consumer_ready=result.gate.mixed_update_consumer_ready,
        freeze_obedience_consumer_ready=result.gate.freeze_obedience_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_s03_first_slice_only=result.scope_marker.s03_first_slice_only,
        scope_s04_implemented=result.scope_marker.s04_implemented,
        scope_s05_implemented=result.scope_marker.s05_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_s03_update_packet_consumer_view(
    result_or_view: S03OwnershipWeightedLearningResult | S03LearningContractView,
) -> S03UpdatePacketConsumerView:
    view = (
        derive_s03_learning_contract_view(result_or_view)
        if isinstance(result_or_view, S03OwnershipWeightedLearningResult)
        else result_or_view
    )
    if not isinstance(view, S03LearningContractView):
        raise TypeError(
            "derive_s03_update_packet_consumer_view requires S03OwnershipWeightedLearningResult/S03LearningContractView"
        )
    return S03UpdatePacketConsumerView(
        learning_id=view.learning_id,
        can_consume_learning_packet=view.learning_packet_consumer_ready,
        can_consume_mixed_update=view.mixed_update_consumer_ready,
        can_obey_freeze=view.freeze_obedience_consumer_ready,
        freeze_or_defer_state=view.freeze_or_defer_state,
        latest_update_class=view.latest_update_class,
        restrictions=view.restrictions,
        reason="s03 bounded update-packet consumer view",
    )


def require_s03_learning_packet_consumer_ready(
    result_or_view: S03OwnershipWeightedLearningResult | S03LearningContractView,
) -> S03UpdatePacketConsumerView:
    view = derive_s03_update_packet_consumer_view(result_or_view)
    if not view.can_consume_learning_packet:
        raise PermissionError(
            "s03 learning packet consumer requires non-frozen ownership-weighted update packet"
        )
    return view


def require_s03_mixed_update_consumer_ready(
    result_or_view: S03OwnershipWeightedLearningResult | S03LearningContractView,
) -> S03UpdatePacketConsumerView:
    view = derive_s03_update_packet_consumer_view(result_or_view)
    if not view.can_consume_mixed_update:
        raise PermissionError(
            "s03 mixed-update consumer requires explicit capped split update packet"
        )
    return view


def require_s03_freeze_obedience_consumer_ready(
    result_or_view: S03OwnershipWeightedLearningResult | S03LearningContractView,
) -> S03UpdatePacketConsumerView:
    view = derive_s03_update_packet_consumer_view(result_or_view)
    if not view.can_obey_freeze:
        raise PermissionError(
            "s03 freeze-obedience consumer requires lawful freeze/defer handling readiness"
        )
    return view
