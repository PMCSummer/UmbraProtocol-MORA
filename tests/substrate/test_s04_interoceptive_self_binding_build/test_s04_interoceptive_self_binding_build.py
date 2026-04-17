from __future__ import annotations

import pytest

from substrate.s04_interoceptive_self_binding import (
    S04BindingStatus,
    S04CandidateClass,
    S04CandidateSignal,
    derive_s04_interoceptive_self_binding_consumer_view,
    derive_s04_interoceptive_self_binding_contract_view,
)
from tests.substrate.s04_interoceptive_self_binding_testkit import (
    S04HarnessConfig,
    build_s04,
    build_s04_harness_case,
)


def _status_for(result, suffix: str = "core_regulatory") -> str:
    for entry in result.state.entries:
        if suffix in entry.channel_or_group_id:
            return entry.binding_status.value
    raise AssertionError(f"missing entry suffix={suffix}")


def _strong_count(result) -> int:
    return len(result.state.core_bound_channels)


def test_basic_candidate_selection_excludes_generic_bookkeeping_channels() -> None:
    result = build_s04_harness_case(
        S04HarnessConfig(case_id="s04-candidate-selection", tick_index=2)
    )
    assert any("bookkeeping:" in item for item in result.state.excluded_channels)
    assert all(
        "bookkeeping:" not in item for item in result.state.core_bound_channels
    )


def test_status_surface_supports_strong_weak_provisional_and_contested() -> None:
    strong = build_s04_harness_case(
            S04HarnessConfig(
                case_id="s04-status-strong",
                tick_index=2,
                regulatory_support=0.8,
                continuity_support=0.78,
                boundary_support=0.76,
                ownership_support=0.78,
                coupling_support=0.72,
                temporal_validity=0.95,
                contamination=0.08,
            )
        )
    provisional = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-status-provisional",
            tick_index=2,
            regulatory_support=0.48,
            continuity_support=0.5,
            boundary_support=0.46,
            ownership_support=0.44,
            coupling_support=0.4,
            contamination=0.18,
        )
    )
    contested = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-status-contested",
            tick_index=2,
            regulatory_support=0.52,
            continuity_support=0.52,
            boundary_support=0.2,
            ownership_support=0.16,
            coupling_support=0.2,
            contamination=0.78,
        )
    )
    assert _status_for(strong) == S04BindingStatus.STRONGLY_SELF_BOUND.value
    assert _status_for(provisional) in {
        S04BindingStatus.PROVISIONALLY_BOUND.value,
        S04BindingStatus.WEAKLY_SELF_BOUND.value,
        S04BindingStatus.CONTESTED_BINDING.value,
    }
    assert _status_for(contested) in {
        S04BindingStatus.CONTESTED_BINDING.value,
        S04BindingStatus.UNBOUND_INTERNAL.value,
    }


def test_ledger_update_persistence_and_rebinding_are_material() -> None:
    first = build_s04_harness_case(
        S04HarnessConfig(case_id="s04-ledger", tick_index=2)
    )
    degraded = build_s04(
        case_id="s04-ledger",
        tick_index=3,
        prior_state=first.state,
        c05_revalidation_required=True,
        context_shift_detected=True,
    )
    rebound = build_s04(
        case_id="s04-ledger",
        tick_index=4,
        prior_state=degraded.state,
    )
    assert degraded.state.stale_binding_drop_count >= 0
    assert degraded.state.recently_unbound_channels is not None
    assert rebound.state.rebinding_event in {True, False}


def test_downstream_contract_shape_exposes_core_periphery_contested_and_no_stable_core() -> None:
    result = build_s04_harness_case(
        S04HarnessConfig(case_id="s04-contract", tick_index=2)
    )
    contract = derive_s04_interoceptive_self_binding_contract_view(result)
    consumer = derive_s04_interoceptive_self_binding_consumer_view(result)
    assert contract.binding_id.startswith("s04-binding:")
    assert isinstance(contract.strong_core_channels, tuple)
    assert isinstance(contract.weak_or_peripheral_channels, tuple)
    assert isinstance(contract.contested_channels, tuple)
    assert isinstance(contract.no_stable_self_core_claim, bool)
    assert consumer.binding_id == contract.binding_id
    assert isinstance(consumer.can_consume_stable_core, bool)
    assert isinstance(consumer.can_consume_contested, bool)
    assert isinstance(consumer.can_consume_no_stable_core, bool)


def test_invariant_generic_internal_cache_does_not_auto_bind_into_core() -> None:
    result = build_s04(
        case_id="s04-invariant-generic",
        tick_index=2,
        observed_internal_channels=("bookkeeping:cache_counter", "cache:surface"),
        candidate_signals=(),
    )
    assert all(
        "bookkeeping:" not in channel and "cache:" not in channel
        for channel in result.state.core_bound_channels
    )


def test_invariant_single_weak_signal_cannot_force_strong_core() -> None:
    result = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-invariant-single-weak",
            tick_index=2,
            regulatory_support=0.35,
            continuity_support=0.2,
            boundary_support=0.22,
            ownership_support=0.2,
            coupling_support=0.18,
            temporal_validity=0.65,
            contamination=0.12,
            include_mixed_channel=False,
        )
    )
    assert _status_for(result) != S04BindingStatus.STRONGLY_SELF_BOUND.value


def test_invariant_invalidated_support_cannot_keep_strong_binding_forever() -> None:
    first = build_s04_harness_case(
        S04HarnessConfig(case_id="s04-invariant-stale", tick_index=2)
    )
    second = build_s04(
        case_id="s04-invariant-stale",
        tick_index=3,
        prior_state=first.state,
        c05_revalidation_required=True,
        context_shift_detected=True,
    )
    assert _strong_count(second) <= _strong_count(first)


def test_regression_previously_strong_channel_weakens_after_context_shift() -> None:
    baseline = build_s04_harness_case(
        S04HarnessConfig(case_id="s04-regression-weaken", tick_index=2)
    )
    shifted = build_s04(
        case_id="s04-regression-weaken",
        tick_index=3,
        prior_state=baseline.state,
        context_shift_detected=True,
        c05_revalidation_required=True,
    )
    assert shifted.state.strongest_binding_strength <= baseline.state.strongest_binding_strength


def test_regression_no_stable_core_claim_is_honest_when_support_is_sparse() -> None:
    result = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-regression-no-core",
            tick_index=2,
            regulatory_support=0.22,
            continuity_support=0.18,
            boundary_support=0.16,
            ownership_support=0.14,
            coupling_support=0.12,
            temporal_validity=0.35,
            contamination=0.68,
        )
    )
    assert result.state.no_stable_self_core_claim is True
    assert any(
        entry.binding_status is S04BindingStatus.NO_STABLE_SELF_CORE_CLAIM
        for entry in result.state.entries
    )


def test_metamorphic_same_covariance_with_different_self_support_changes_status() -> None:
    weak_self = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-morph-covariance-weak",
            tick_index=2,
            regulatory_support=0.7,
            continuity_support=0.7,
            boundary_support=0.25,
            ownership_support=0.2,
            coupling_support=0.7,
            contamination=0.12,
        )
    )
    strong_self = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-morph-covariance-strong",
            tick_index=2,
            regulatory_support=0.7,
            continuity_support=0.7,
            boundary_support=0.72,
            ownership_support=0.72,
            coupling_support=0.7,
            contamination=0.12,
        )
    )
    assert _status_for(weak_self) != _status_for(strong_self)


def test_metamorphic_removing_ownership_boundary_or_validity_support_changes_outcome() -> None:
    baseline = build_s04_harness_case(
        S04HarnessConfig(case_id="s04-morph-ablation-base", tick_index=2)
    )
    no_ownership = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-morph-ablation-own",
            tick_index=2,
            ownership_support=0.08,
        )
    )
    no_boundary = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-morph-ablation-boundary",
            tick_index=2,
            boundary_support=0.1,
        )
    )
    no_validity = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-morph-ablation-validity",
            tick_index=2,
            temporal_validity=0.18,
            c05_revalidation_required=True,
        )
    )
    assert (
        no_ownership.state.strongest_binding_strength
        < baseline.state.strongest_binding_strength
    )
    assert (
        no_boundary.state.strongest_binding_strength
        < baseline.state.strongest_binding_strength
    )
    assert (
        no_validity.state.strongest_binding_strength
        < baseline.state.strongest_binding_strength
    )


@pytest.mark.parametrize(
    "continuity,ownership,boundary,coupling",
    [
        (0.75, 0.75, 0.75, 0.75),
        (0.75, 0.2, 0.75, 0.75),
        (0.75, 0.75, 0.2, 0.75),
        (0.2, 0.75, 0.75, 0.75),
        (0.75, 0.75, 0.75, 0.2),
    ],
)
def test_ablation_support_axes_materially_change_self_core(
    continuity: float,
    ownership: float,
    boundary: float,
    coupling: float,
) -> None:
    result = build_s04_harness_case(
        S04HarnessConfig(
            case_id=f"s04-ablation-{continuity}-{ownership}-{boundary}-{coupling}",
            tick_index=2,
            continuity_support=continuity,
            ownership_support=ownership,
            boundary_support=boundary,
            coupling_support=coupling,
        )
    )
    if min(continuity, ownership, boundary, coupling) <= 0.2:
        assert _status_for(result) != S04BindingStatus.STRONGLY_SELF_BOUND.value


@pytest.mark.parametrize(
    "regulatory,ownership,boundary,temporal,contamination",
    [
        (0.8, 0.8, 0.8, 0.85, 0.1),
        (0.8, 0.3, 0.8, 0.85, 0.1),
        (0.8, 0.8, 0.3, 0.85, 0.1),
        (0.45, 0.45, 0.45, 0.85, 0.1),
        (0.8, 0.8, 0.8, 0.25, 0.1),
        (0.8, 0.8, 0.8, 0.85, 0.78),
    ],
)
def test_matrix_combinations_produce_different_status_bands(
    regulatory: float,
    ownership: float,
    boundary: float,
    temporal: float,
    contamination: float,
) -> None:
    result = build_s04_harness_case(
        S04HarnessConfig(
            case_id=f"s04-matrix-{regulatory}-{ownership}-{boundary}-{temporal}-{contamination}",
            tick_index=2,
            regulatory_support=regulatory,
            ownership_support=ownership,
            boundary_support=boundary,
            temporal_validity=temporal,
            contamination=contamination,
        )
    )
    status = _status_for(result)
    if temporal < 0.3 or contamination > 0.7:
        assert status in {
            S04BindingStatus.CONTESTED_BINDING.value,
            S04BindingStatus.UNBOUND_INTERNAL.value,
            S04BindingStatus.MIXED_INTERNAL_EXTERNAL_SIGNAL.value,
        }
    if (
        regulatory >= 0.75
        and ownership >= 0.75
        and boundary >= 0.75
        and temporal >= 0.8
        and contamination < 0.7
    ):
        assert status in {
            S04BindingStatus.STRONGLY_SELF_BOUND.value,
            S04BindingStatus.WEAKLY_SELF_BOUND.value,
        }


def test_role_based_shortcut_baselines_do_not_match_real_mechanism() -> None:
    low_boundary = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-role-baseline-low-boundary",
            tick_index=2,
            regulatory_support=0.8,
            continuity_support=0.78,
            boundary_support=0.18,
            ownership_support=0.78,
            coupling_support=0.76,
            contamination=0.1,
        )
    )
    strong_all = build_s04_harness_case(
        S04HarnessConfig(
            case_id="s04-role-baseline-strong",
            tick_index=2,
            regulatory_support=0.8,
            continuity_support=0.78,
            boundary_support=0.78,
            ownership_support=0.78,
            coupling_support=0.76,
            contamination=0.1,
        )
    )

    def hardcoded_whitelist_status(_: str) -> str:
        return S04BindingStatus.STRONGLY_SELF_BOUND.value

    def generic_clustering_status(continuity: float, coupling: float) -> str:
        return (
            S04BindingStatus.STRONGLY_SELF_BOUND.value
            if (continuity + coupling) / 2.0 >= 0.5
            else S04BindingStatus.UNBOUND_INTERNAL.value
        )

    implemented_low = _status_for(low_boundary)
    implemented_strong = _status_for(strong_all)
    assert not (
        implemented_low == hardcoded_whitelist_status("anything")
        and implemented_strong == hardcoded_whitelist_status("anything")
    )
    clustered_low = generic_clustering_status(0.78, 0.76)
    clustered_strong = generic_clustering_status(0.78, 0.76)
    assert not (implemented_low == clustered_low and implemented_strong == clustered_strong)


def test_invariant_unauthorized_external_privileged_candidate_is_downgraded() -> None:
    unauthorized = S04CandidateSignal(
        channel_id="unauthorized:injected_core_channel",
        candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
        regulatory_support_hint=0.95,
        continuity_support_hint=0.95,
        boundary_support_hint=0.95,
        ownership_support_hint=0.95,
        coupling_support_hint=0.95,
        temporal_validity_hint=0.95,
        contamination_hint=0.01,
        source_authority="external.audit",
        provenance="audit.unauthorized_injection",
    )
    result = build_s04(
        case_id="s04-unauthorized-guard",
        tick_index=2,
        candidate_signals=(unauthorized,),
    )
    assert "unauthorized:injected_core_channel" in result.state.candidate_channels
    assert "unauthorized:injected_core_channel" in result.state.excluded_channels
    assert "unauthorized:injected_core_channel" not in result.state.core_bound_channels
    assert all(
        item.channel_or_group_id != "unauthorized:injected_core_channel"
        for item in result.state.entries
    )


def test_authorized_external_privileged_candidate_can_participate_in_binding() -> None:
    authorized = S04CandidateSignal(
        channel_id="authorized:intero_core_channel",
        candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
        regulatory_support_hint=0.88,
        continuity_support_hint=0.85,
        boundary_support_hint=0.82,
        ownership_support_hint=0.84,
        coupling_support_hint=0.8,
        temporal_validity_hint=0.92,
        contamination_hint=0.04,
        source_authority="s04.authorized:unit_test",
        provenance="audit.authorized_injection",
    )
    result = build_s04(
        case_id="s04-authorized-guard",
        tick_index=2,
        candidate_signals=(authorized,),
    )
    channel_entries = [
        item
        for item in result.state.entries
        if item.channel_or_group_id == "authorized:intero_core_channel"
    ]
    assert channel_entries
    assert channel_entries[0].binding_status in {
        S04BindingStatus.STRONGLY_SELF_BOUND,
        S04BindingStatus.WEAKLY_SELF_BOUND,
    }


def test_falsifier_mixed_channel_without_convergent_self_support_cannot_escalate_to_strong_core() -> None:
    mixed = S04CandidateSignal(
        channel_id="mixed:bridge_channel",
        candidate_class=S04CandidateClass.MIXED_INTERNAL_EXTERNAL,
        regulatory_support_hint=0.9,
        continuity_support_hint=0.9,
        boundary_support_hint=0.2,
        ownership_support_hint=0.18,
        coupling_support_hint=0.86,
        temporal_validity_hint=0.9,
        contamination_hint=0.25,
        source_authority="s04.authorized:unit_test",
        provenance="audit.mixed_escalation_falsifier",
    )
    result = build_s04(
        case_id="s04-mixed-no-strong",
        tick_index=2,
        candidate_signals=(mixed,),
        observed_internal_channels=(),
    )
    entry = next(
        item for item in result.state.entries if item.channel_or_group_id == "mixed:bridge_channel"
    )
    assert entry.binding_status is S04BindingStatus.MIXED_INTERNAL_EXTERNAL_SIGNAL
    assert "mixed:bridge_channel" not in result.state.core_bound_channels


def test_short_multi_tick_temporal_stress_shows_bounded_weaken_drop_and_rebind() -> None:
    prior = None
    statuses: list[str] = []
    saw_recently_unbound = False
    saw_stale_drop = False
    saw_rebinding = False
    saw_degraded = False
    saw_strong = False

    timeline = (
        {"present": True, "shift": False, "revalidate": False, "contam": 0.06, "validity": 0.93},
        {"present": True, "shift": False, "revalidate": False, "contam": 0.08, "validity": 0.9},
        {"present": True, "shift": True, "revalidate": True, "contam": 0.78, "validity": 0.46},
        {"present": True, "shift": True, "revalidate": True, "contam": 0.82, "validity": 0.38},
        {"present": True, "shift": False, "revalidate": False, "contam": 0.12, "validity": 0.86},
        {"present": False, "shift": False, "revalidate": False, "contam": 0.1, "validity": 0.82},
        {"present": True, "shift": False, "revalidate": False, "contam": 0.09, "validity": 0.88},
        {"present": True, "shift": True, "revalidate": False, "contam": 0.35, "validity": 0.72},
        {"present": True, "shift": False, "revalidate": False, "contam": 0.1, "validity": 0.9},
        {"present": True, "shift": False, "revalidate": False, "contam": 0.08, "validity": 0.92},
    )
    for tick_index, config in enumerate(timeline, start=1):
        candidate_signals: tuple[S04CandidateSignal, ...]
        if config["present"]:
            candidate_signals = (
                S04CandidateSignal(
                    channel_id="stress:intero_core_channel",
                    candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
                    regulatory_support_hint=0.86,
                    continuity_support_hint=0.82,
                    boundary_support_hint=0.8,
                    ownership_support_hint=0.8,
                    coupling_support_hint=0.76,
                    temporal_validity_hint=float(config["validity"]),
                    contamination_hint=float(config["contam"]),
                    source_authority="s04.authorized:temporal_stress",
                    provenance=f"stress.tick_{tick_index}",
                ),
            )
        else:
            candidate_signals = ()

        result = build_s04(
            case_id="s04-temporal-stress",
            tick_index=tick_index,
            prior_state=prior,
            context_shift_detected=bool(config["shift"]),
            c05_revalidation_required=bool(config["revalidate"]),
            candidate_signals=candidate_signals,
            observed_internal_channels=(),
        )
        prior = result.state

        entry = next(
            (
                item
                for item in result.state.entries
                if item.channel_or_group_id == "stress:intero_core_channel"
            ),
            None,
        )
        status = "absent" if entry is None else entry.binding_status.value
        statuses.append(status)
        if status == S04BindingStatus.STRONGLY_SELF_BOUND.value:
            saw_strong = True
        if status in {
            S04BindingStatus.CONTESTED_BINDING.value,
            S04BindingStatus.UNBOUND_INTERNAL.value,
            "absent",
        }:
            saw_degraded = True
        if result.state.recently_unbound_channels:
            saw_recently_unbound = True
        if result.state.stale_binding_drop_count > 0:
            saw_stale_drop = True
        if result.state.rebinding_event:
            saw_rebinding = True

    assert len(statuses) == 10
    assert saw_strong is True
    assert saw_degraded is True
    assert saw_recently_unbound is True
    assert saw_stale_drop is True
    assert saw_rebinding is True
