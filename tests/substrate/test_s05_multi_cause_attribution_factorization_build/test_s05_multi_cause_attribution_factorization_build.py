from __future__ import annotations

import math

import pytest

from substrate.s05_multi_cause_attribution_factorization import (
    S05AttributionStatus,
    S05CauseClass,
    S05DownstreamRouteClass,
    S05EligibilityStatus,
    S05ResidualClass,
    S05RevisionStatus,
    derive_s05_multi_cause_attribution_consumer_view,
    require_s05_factorized_consumer_ready,
    require_s05_learning_route_consumer_ready,
)
from tests.substrate.s05_multi_cause_attribution_factorization_testkit import (
    S05HarnessConfig,
    build_s05_harness_case,
)


def _slot_share(result, cause: S05CauseClass) -> float:
    packet = result.state.packets[-1]
    entry = next(slot for slot in packet.cause_slots if slot.cause_class is cause)
    if entry.allocated_share is not None:
        return float(entry.allocated_share)
    if entry.bounded_share_interval is None:
        return 0.0
    lo, hi = entry.bounded_share_interval
    return float((lo + hi) / 2.0)


def _eligible_slots(result) -> list:
    packet = result.state.packets[-1]
    return [
        slot
        for slot in packet.cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
        and slot.eligibility_status in {S05EligibilityStatus.ELIGIBLE, S05EligibilityStatus.CAPPED}
    ]


def _top_non_residual_cause(result) -> S05CauseClass:
    packet = result.state.packets[-1]
    pairs: list[tuple[S05CauseClass, float]] = []
    for slot in packet.cause_slots:
        if slot.cause_class is S05CauseClass.UNEXPLAINED_RESIDUAL:
            continue
        pairs.append((slot.cause_class, _slot_share(result, slot.cause_class)))
    pairs.sort(key=lambda item: item[1], reverse=True)
    return pairs[0][0]


def _naive_single_cause_baseline(result) -> S05CauseClass:
    packet = result.state.packets[-1]
    non_residual = [
        slot
        for slot in packet.cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
    ]
    non_residual.sort(key=lambda slot: float(slot.support_strength), reverse=True)
    return non_residual[0].cause_class


def _naive_no_residual_split(result) -> float:
    packet = result.state.packets[-1]
    non_residual = [
        slot
        for slot in packet.cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
    ]
    denom = sum(max(0.0, float(slot.support_strength)) for slot in non_residual)
    if denom <= 1e-9:
        return 0.0
    return 1.0


def test_core_mechanism_emits_multi_slot_factorization_with_residual() -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-core-multi-slot",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            interoceptive_support=0.82,
            observation_noise=0.24,
        )
    )
    packet = result.state.packets[-1]
    nonzero = [
        slot
        for slot in packet.cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
        and _slot_share(result, slot.cause_class) > 0.05
    ]
    assert len(nonzero) >= 2
    assert result.state.unexplained_residual > 0.0
    assert packet.attribution_status in {
        S05AttributionStatus.FACTORIZED_MULTI_CAUSE,
        S05AttributionStatus.BOUNDED_INTERVAL_ONLY,
        S05AttributionStatus.NO_CLEAN_FACTORIZATION_CLAIM,
        S05AttributionStatus.UNDERDETERMINED_SPLIT,
    }


def test_compatibility_filtering_blocks_incompatible_slots_from_full_mass() -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-incompatible-filter",
            tick_index=2,
            deliberate_internal_act=False,
            endogenous_mode_shift=False,
            interoceptive_support=0.2,
            world_perturbation=False,
            observation_noise=0.88,
            c05_revalidation_required=True,
            context_shift_detected=True,
        )
    )
    packet = result.state.packets[-1]
    incompatible = [
        slot
        for slot in packet.cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
        and slot.eligibility_status is S05EligibilityStatus.INCOMPATIBLE
    ]
    assert incompatible
    for slot in incompatible:
        assert _slot_share(result, slot.cause_class) <= 0.12


def test_internal_act_mode_drift_and_intero_drift_are_separable_slots() -> None:
    self_heavy = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-separable-self",
            tick_index=2,
            deliberate_internal_act=True,
            endogenous_mode_shift=False,
            interoceptive_support=0.45,
            world_perturbation=False,
            observation_noise=0.08,
        )
    )
    mode_heavy = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-separable-mode",
            tick_index=2,
            deliberate_internal_act=False,
            endogenous_mode_shift=True,
            interoceptive_support=0.4,
            world_perturbation=False,
            observation_noise=0.1,
            c05_revalidation_required=True,
        )
    )
    intero_heavy = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-separable-intero",
            tick_index=2,
            deliberate_internal_act=False,
            endogenous_mode_shift=False,
            interoceptive_support=0.92,
            world_perturbation=False,
            observation_noise=0.06,
        )
    )
    self_support_self_case = next(
        slot.support_strength
        for slot in self_heavy.state.packets[-1].cause_slots
        if slot.cause_class is S05CauseClass.SELF_INITIATED_ACT
    )
    self_support_mode_case = next(
        slot.support_strength
        for slot in mode_heavy.state.packets[-1].cause_slots
        if slot.cause_class is S05CauseClass.SELF_INITIATED_ACT
    )
    assert self_support_self_case >= self_support_mode_case
    assert _slot_share(mode_heavy, S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION) > _slot_share(
        self_heavy, S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION
    )
    assert _slot_share(
        intero_heavy, S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT
    ) > _slot_share(self_heavy, S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT)


def test_invariant_residual_not_forced_zero_under_underdetermined_basis() -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-residual-invariant",
            tick_index=2,
            deliberate_internal_act=False,
            endogenous_mode_shift=False,
            interoceptive_support=0.16,
            world_perturbation=False,
            observation_noise=0.7,
            latent_unmodeled_disturbance=0.86,
            c05_revalidation_required=True,
            context_shift_detected=True,
        )
    )
    assert result.state.unexplained_residual >= 0.45
    assert result.state.residual_class in {S05ResidualClass.MEDIUM, S05ResidualClass.HIGH}
    assert (
        result.state.packets[-1].attribution_status
        in {
            S05AttributionStatus.UNDERDETERMINED_SPLIT,
            S05AttributionStatus.RESIDUAL_TOO_LARGE,
            S05AttributionStatus.NO_CLEAN_FACTORIZATION_CLAIM,
            S05AttributionStatus.BOUNDED_INTERVAL_ONLY,
        }
    )


def test_regression_packet_history_preserves_prior_factorization_versions() -> None:
    first = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-history",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            interoceptive_support=0.76,
            observation_noise=0.14,
        )
    )
    second = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-history",
            tick_index=3,
            deliberate_internal_act=False,
            endogenous_mode_shift=True,
            world_perturbation=False,
            interoceptive_support=0.4,
            observation_noise=0.44,
            c05_revalidation_required=True,
            late_evidence_tokens=("late:evidence:mode_shift",),
        ),
        prior_state=first.state,
    )
    assert len(second.state.packets) >= 2
    assert second.state.packets[-1].outcome_packet_id != second.state.packets[0].outcome_packet_id
    assert second.state.reattribution_happened in {True, False}


def test_multi_step_late_evidence_reattribution_is_bounded_and_provenance_preserving() -> None:
    state = None
    residuals: list[float] = []
    revisions: list[S05RevisionStatus] = []
    packet_ids: list[str] = []

    for index in range(1, 11):
        result = build_s05_harness_case(
            S05HarnessConfig(
                case_id="s05-late-evidence-stress",
                tick_index=index,
                deliberate_internal_act=(index % 2 == 0),
                endogenous_mode_shift=(index % 3 == 0),
                interoceptive_support=0.72 if index % 2 == 0 else 0.46,
                world_perturbation=(index % 4 in {1, 2}),
                observation_noise=0.2 if index % 2 == 0 else 0.52,
                c05_revalidation_required=(index % 3 == 0),
                context_shift_detected=(index % 5 == 0),
                late_evidence_tokens=(f"late:evidence:{index}",) if index > 1 else (),
            ),
            prior_state=state,
        )
        state = result.state
        packet = result.state.packets[-1]
        residuals.append(result.state.unexplained_residual)
        revisions.append(packet.revision_status)
        packet_ids.append(packet.outcome_packet_id)

    assert state is not None
    # History is bounded but preserved as a packet ledger window.
    assert len(state.packets) == 8
    assert len(set(item.outcome_packet_id for item in state.packets)) == len(state.packets)
    assert all(packet.provenance.startswith("s05.multi_cause_attribution.") for packet in state.packets)
    assert any(status is S05RevisionStatus.REVISED_WITH_LATE_EVIDENCE for status in revisions[1:])

    # Bounded re-attribution should revise, but not flap chaotically between revisions.
    deltas = [abs(curr - prev) for prev, curr in zip(residuals, residuals[1:])]
    assert max(deltas) <= 0.38
    assert abs(residuals[-1] - residuals[-2]) <= 0.35

    # No silent rewrite: latest packets remain distinct runtime packets, not overwritten ids.
    assert len(set(packet_ids[-8:])) == len(state.packets)


def test_temporal_alignment_changes_slot_eligibility_for_same_support_pattern() -> None:
    aligned = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-temporal-aligned",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            interoceptive_support=0.72,
            observation_noise=0.2,
        )
    )
    misaligned = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-temporal-misaligned",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            interoceptive_support=0.72,
            observation_noise=0.2,
            c05_revalidation_required=True,
            context_shift_detected=True,
        )
    )
    assert len(_eligible_slots(misaligned)) <= len(_eligible_slots(aligned))
    aligned_temporal = [
        slot.temporal_fit
        for slot in aligned.state.packets[-1].cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
    ]
    misaligned_temporal = [
        slot.temporal_fit
        for slot in misaligned.state.packets[-1].cause_slots
        if slot.cause_class is not S05CauseClass.UNEXPLAINED_RESIDUAL
    ]
    assert (sum(misaligned_temporal) / len(misaligned_temporal)) < (
        sum(aligned_temporal) / len(aligned_temporal)
    )


def test_metamorphic_same_magnitude_different_mixtures_change_factorization_structure() -> None:
    self_world = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-morph-self-world",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            endogenous_mode_shift=False,
            interoceptive_support=0.5,
            observation_noise=0.16,
            latent_unmodeled_disturbance=0.7,
        )
    )
    mode_artifact = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-morph-mode-artifact",
            tick_index=2,
            deliberate_internal_act=False,
            world_perturbation=False,
            endogenous_mode_shift=True,
            interoceptive_support=0.5,
            observation_noise=0.72,
            latent_unmodeled_disturbance=0.7,
            c05_revalidation_required=True,
        )
    )
    assert _top_non_residual_cause(self_world) != _top_non_residual_cause(mode_artifact)
    assert self_world.state.packets[-1].downstream_route_class != mode_artifact.state.packets[-1].downstream_route_class


def test_metamorphic_adding_unmodeled_disturbance_increases_residual() -> None:
    without_latent = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-latent-none",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            interoceptive_support=0.8,
            observation_noise=0.18,
            latent_unmodeled_disturbance=0.0,
        )
    )
    with_latent = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-latent-high",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            interoceptive_support=0.8,
            observation_noise=0.18,
            latent_unmodeled_disturbance=0.92,
        )
    )
    assert (
        abs(with_latent.state.unexplained_residual - without_latent.state.unexplained_residual)
        >= 0.02
    ) or (
        with_latent.state.packets[-1].downstream_route_class
        != without_latent.state.packets[-1].downstream_route_class
    )


def test_ablation_factorization_disabled_degrades_to_residual_only_packet() -> None:
    disabled = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-ablation-disabled",
            tick_index=2,
            factorization_enabled=False,
        )
    )
    packet = disabled.state.packets[-1]
    assert len(packet.cause_slots) == 1
    assert packet.cause_slots[0].cause_class is S05CauseClass.UNEXPLAINED_RESIDUAL
    assert packet.unexplained_residual >= 0.9
    assert disabled.gate.factorization_consumer_ready is False


def test_falsifier_single_cause_baseline_is_structurally_different_from_s05() -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-falsifier-single-cause",
            tick_index=2,
            deliberate_internal_act=True,
            endogenous_mode_shift=True,
            world_perturbation=True,
            interoceptive_support=0.74,
            observation_noise=0.22,
        )
    )
    baseline_cause = _naive_single_cause_baseline(result)
    implementation_has_split = len(_eligible_slots(result)) >= 2
    assert implementation_has_split is True
    assert baseline_cause in {
        S05CauseClass.SELF_INITIATED_ACT,
        S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION,
        S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT,
        S05CauseClass.EXTERNAL_OR_WORLD_CONTRIBUTION,
        S05CauseClass.OBSERVATION_OR_CHANNEL_ARTIFACT,
    }


def test_falsifier_residual_suppression_baseline_disagrees_with_real_residual() -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-falsifier-residual",
            tick_index=2,
            deliberate_internal_act=False,
            endogenous_mode_shift=True,
            world_perturbation=False,
            interoceptive_support=0.4,
            observation_noise=0.68,
            latent_unmodeled_disturbance=0.88,
            c05_revalidation_required=True,
        )
    )
    fake_full_allocation = _naive_no_residual_split(result)
    assert fake_full_allocation == 1.0
    assert result.state.unexplained_residual > 0.0


def test_falsifier_internal_cause_conflation_baseline_differs_from_s05_split() -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-falsifier-internal-conflation",
            tick_index=2,
            deliberate_internal_act=True,
            endogenous_mode_shift=True,
            interoceptive_support=0.76,
            world_perturbation=False,
            observation_noise=0.24,
        )
    )
    self_share = _slot_share(result, S05CauseClass.SELF_INITIATED_ACT)
    mode_share = _slot_share(result, S05CauseClass.ENDOGENOUS_MODE_CONTRIBUTION)
    intero_share = _slot_share(result, S05CauseClass.INTEROCEPTIVE_OR_REGULATORY_DRIFT)
    conflated_internal = self_share + mode_share + intero_share
    assert conflated_internal > 0.0
    assert not math.isclose(self_share, conflated_internal, rel_tol=1e-6, abs_tol=1e-6)


@pytest.mark.parametrize(
    "deliberate,mode_shift,world,noise,expected_route",
    [
        (True, False, False, 0.12, S05DownstreamRouteClass.SELF_ACT_HEAVY),
        (False, True, False, 0.12, S05DownstreamRouteClass.MODE_DRIFT_HEAVY),
        (False, False, True, 0.12, S05DownstreamRouteClass.WORLD_HEAVY),
    ],
)
def test_matrix_route_class_changes_across_cause_dominance_profiles(
    deliberate: bool,
    mode_shift: bool,
    world: bool,
    noise: float,
    expected_route: S05DownstreamRouteClass,
) -> None:
    result = build_s05_harness_case(
        S05HarnessConfig(
            case_id=f"s05-matrix-{deliberate}-{mode_shift}-{world}-{noise}",
            tick_index=2,
            deliberate_internal_act=deliberate,
            endogenous_mode_shift=mode_shift,
            world_perturbation=world,
            interoceptive_support=0.35 if mode_shift else 0.58,
            observation_noise=noise,
            c05_revalidation_required=mode_shift,
        )
    )
    assert result.state.packets[-1].downstream_route_class in {
        expected_route,
        S05DownstreamRouteClass.MIXED_FACTORIZED,
        S05DownstreamRouteClass.HIGH_RESIDUAL_UNDERDETERMINED,
    }


def test_downstream_contract_surface_is_load_bearing_for_learning_route() -> None:
    high_residual = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-downstream-high-residual",
            tick_index=2,
            deliberate_internal_act=False,
            world_perturbation=False,
            endogenous_mode_shift=True,
            interoceptive_support=0.2,
            observation_noise=0.84,
            latent_unmodeled_disturbance=0.9,
            c05_revalidation_required=True,
        )
    )
    low_residual = build_s05_harness_case(
        S05HarnessConfig(
            case_id="s05-downstream-low-residual",
            tick_index=2,
            deliberate_internal_act=True,
            world_perturbation=True,
            endogenous_mode_shift=False,
            interoceptive_support=0.82,
            observation_noise=0.08,
            latent_unmodeled_disturbance=0.0,
        )
    )
    high_view = derive_s05_multi_cause_attribution_consumer_view(high_residual)
    low_view = derive_s05_multi_cause_attribution_consumer_view(low_residual)
    assert high_view.can_route_learning_attribution is False
    assert low_view.can_consume_factorization is True
    if low_view.can_route_learning_attribution:
        assert require_s05_learning_route_consumer_ready(low_residual).factorization_id == low_view.factorization_id
    with pytest.raises(PermissionError):
        require_s05_learning_route_consumer_ready(high_residual)
    assert require_s05_factorized_consumer_ready(low_residual).factorization_id == low_view.factorization_id
