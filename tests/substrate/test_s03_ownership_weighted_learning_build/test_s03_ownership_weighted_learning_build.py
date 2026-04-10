from __future__ import annotations

from substrate.s03_ownership_weighted_learning import (
    S03CommitClass,
    S03OwnershipUpdateClass,
    derive_s03_learning_contract_view,
    derive_s03_update_packet_consumer_view,
)
from tests.substrate.s01_efference_copy_testkit import build_s01
from tests.substrate.s02_prediction_boundary_testkit import build_s02
from tests.substrate.s03_ownership_weighted_learning_testkit import build_s03


def _shared_mismatch_s01(case_id: str):
    seed = build_s01(
        case_id=f"{case_id}-seed",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
    )
    return build_s01(
        case_id=f"{case_id}-obs",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=False,
        prior_state=seed.state,
    )


def _repeated_boundary(case_id: str, *, s01_result, effector_available: bool):
    first = build_s02(
        case_id=f"{case_id}-first",
        tick_index=2,
        s01_result=s01_result,
        effector_available=effector_available,
    )
    return build_s02(
        case_id=f"{case_id}-second",
        tick_index=3,
        s01_result=s01_result,
        effector_available=effector_available,
        prior_state=first.state,
    )


def test_same_error_magnitude_but_different_ownership_routes_differently() -> None:
    shared_s01 = _shared_mismatch_s01("s03-same-magnitude")
    self_boundary = _repeated_boundary(
        "s03-same-magnitude-self",
        s01_result=shared_s01,
        effector_available=True,
    )
    world_boundary = _repeated_boundary(
        "s03-same-magnitude-world",
        s01_result=shared_s01,
        effector_available=False,
    )
    self_route = build_s03(
        case_id="s03-same-magnitude-self",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=self_boundary,
    )
    world_route = build_s03(
        case_id="s03-same-magnitude-world",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=world_boundary,
    )
    self_packet = self_route.state.packets[-1]
    world_packet = world_route.state.packets[-1]
    assert self_packet.update_class != world_packet.update_class
    assert self_packet.self_update_weight != world_packet.self_update_weight


def test_repeated_self_side_mismatch_strengthens_internal_update_pressure() -> None:
    shared_s01 = _shared_mismatch_s01("s03-repeat-self")
    self_boundary = _repeated_boundary(
        "s03-repeat-self",
        s01_result=shared_s01,
        effector_available=True,
    )
    first = build_s03(
        case_id="s03-repeat-self",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=self_boundary,
    )
    second = build_s03(
        case_id="s03-repeat-self",
        tick_index=5,
        s01_result=shared_s01,
        s02_result=self_boundary,
        prior_state=first.state,
    )
    assert second.state.repeated_self_support >= first.state.repeated_self_support
    assert second.state.packets[-1].self_update_weight >= first.state.packets[-1].self_update_weight


def test_world_dominated_residual_routes_outward() -> None:
    shared_s01 = _shared_mismatch_s01("s03-world-dominated")
    world_boundary = _repeated_boundary(
        "s03-world-dominated",
        s01_result=shared_s01,
        effector_available=False,
    )
    result = build_s03(
        case_id="s03-world-dominated",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=world_boundary,
    )
    packet = result.state.packets[-1]
    assert packet.update_class in {
        S03OwnershipUpdateClass.WORLD_UPDATE_DOMINANT,
        S03OwnershipUpdateClass.OBSERVATION_CHANNEL_RECALIBRATION_CANDIDATE,
        S03OwnershipUpdateClass.ANOMALY_ONLY_ROUTING,
    }
    assert (
        packet.world_update_weight
        + packet.observation_update_weight
        + packet.anomaly_update_weight
    ) >= packet.self_update_weight


def test_mixed_source_outcome_produces_split_or_capped_update() -> None:
    internal_s01 = build_s01(
        case_id="s03-mixed-internal",
        tick_index=1,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
    )
    internal_boundary = build_s02(
        case_id="s03-mixed-internal",
        tick_index=2,
        s01_result=internal_s01,
        effector_available=True,
    )
    external_s01 = build_s01(
        case_id="s03-mixed-external",
        tick_index=3,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    mixed_boundary = build_s02(
        case_id="s03-mixed",
        tick_index=4,
        s01_result=external_s01,
        effector_available=True,
        prior_state=internal_boundary.state,
    )
    result = build_s03(
        case_id="s03-mixed",
        tick_index=5,
        s01_result=external_s01,
        s02_result=mixed_boundary,
    )
    packet = result.state.packets[-1]
    assert packet.commit_class in {
        S03CommitClass.SPLIT_ACROSS_TARGETS,
        S03CommitClass.CAP_UPDATE_MAGNITUDE,
        S03CommitClass.DEFER_UNTIL_REVALIDATION,
    }
    assert (packet.self_update_weight + packet.world_update_weight) > 0 or packet.commit_class in {
        S03CommitClass.CAP_UPDATE_MAGNITUDE,
        S03CommitClass.DEFER_UNTIL_REVALIDATION,
    }


def test_stale_or_invalid_basis_freezes_or_weakens_update() -> None:
    shared_s01 = _shared_mismatch_s01("s03-stale")
    self_boundary = _repeated_boundary(
        "s03-stale",
        s01_result=shared_s01,
        effector_available=True,
    )
    result = build_s03(
        case_id="s03-stale",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=self_boundary,
        c05_revalidation_required=True,
        c05_no_safe_reuse=True,
    )
    packet = result.state.packets[-1]
    view = derive_s03_update_packet_consumer_view(result)
    assert packet.stale_or_invalidated is True
    assert packet.freeze_or_defer_status.value in {
        "freeze_pending_revalidation",
        "defer_until_revalidation",
    }
    assert view.can_consume_learning_packet is False


def test_degraded_observation_prefers_observation_or_anomaly_route() -> None:
    degraded_s01 = build_s01(
        case_id="s03-degraded-observation",
        tick_index=2,
        emit_world_action_candidate=True,
        world_effect_feedback_correlated=True,
        world_degraded=True,
        c05_dependency_contaminated=True,
    )
    degraded_s02 = build_s02(
        case_id="s03-degraded-observation",
        tick_index=3,
        s01_result=degraded_s01,
        observation_degraded=True,
        c05_dependency_contaminated=True,
        effector_available=True,
    )
    result = build_s03(
        case_id="s03-degraded-observation",
        tick_index=4,
        s01_result=degraded_s01,
        s02_result=degraded_s02,
    )
    packet = result.state.packets[-1]
    assert (
        packet.observation_update_weight + packet.anomaly_update_weight
    ) >= packet.self_update_weight


def test_insufficient_ownership_basis_does_not_force_confident_commit() -> None:
    sparse_s01 = build_s01(
        case_id="s03-insufficient",
        tick_index=1,
        emit_world_action_candidate=False,
        world_effect_feedback_correlated=False,
    )
    sparse_s02 = build_s02(
        case_id="s03-insufficient",
        tick_index=2,
        s01_result=sparse_s01,
        effector_available=False,
    )
    result = build_s03(
        case_id="s03-insufficient",
        tick_index=3,
        s01_result=sparse_s01,
        s02_result=sparse_s02,
    )
    packet = result.state.packets[-1]
    assert packet.commit_class is not S03CommitClass.COMMIT_UPDATE
    assert packet.confidence <= 0.7


def test_ablation_or_disable_path_collapses_s03_specific_routing() -> None:
    shared_s01 = _shared_mismatch_s01("s03-ablation")
    self_boundary = _repeated_boundary(
        "s03-ablation",
        s01_result=shared_s01,
        effector_available=True,
    )
    enabled = build_s03(
        case_id="s03-ablation",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=self_boundary,
    )
    ablated = build_s03(
        case_id="s03-ablation",
        tick_index=4,
        s01_result=shared_s01,
        s02_result=self_boundary,
        ownership_weighting_enabled=False,
    )
    enabled_view = derive_s03_learning_contract_view(enabled)
    ablated_view = derive_s03_learning_contract_view(ablated)
    assert enabled_view.latest_update_class != ablated_view.latest_update_class
    assert ablated_view.learning_packet_consumer_ready is False
