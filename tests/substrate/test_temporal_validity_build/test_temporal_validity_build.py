from __future__ import annotations

from dataclasses import replace

from substrate.temporal_validity import (
    TemporalCarryoverItemKind,
    TemporalValidityContext,
    TemporalValidityStatus,
    build_temporal_validity,
    can_continue_mode_hold,
    can_open_branch_access,
    can_reuse_item,
    can_revisit_with_basis,
    choose_temporal_reuse_execution_mode,
    derive_temporal_validity_contract_view,
    select_reusable_items,
    select_revalidation_targets,
)
from tests.substrate.c05_testkit import build_c05_upstream


def _build_result(upstream, **context_overrides):
    return build_temporal_validity(
        upstream.stream,
        upstream.scheduler,
        upstream.diversification,
        upstream.mode_arbitration,
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=TemporalValidityContext(**context_overrides),
    )


def _item_by_kind(result, kind: TemporalCarryoverItemKind):
    for item in result.state.items:
        if item.item_kind == kind:
            return item
    return None


def _items_by_kind(result, kind: TemporalCarryoverItemKind):
    return tuple(item for item in result.state.items if item.item_kind == kind)


def _status_rank(status: TemporalValidityStatus) -> int:
    return {
        TemporalValidityStatus.STILL_VALID: 7,
        TemporalValidityStatus.CONDITIONALLY_CARRIED: 6,
        TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION: 5,
        TemporalValidityStatus.NEEDS_FULL_REVALIDATION: 4,
        TemporalValidityStatus.DEPENDENCY_CONTAMINATED: 3,
        TemporalValidityStatus.NO_SAFE_REUSE_CLAIM: 2,
        TemporalValidityStatus.EXPIRED: 1,
        TemporalValidityStatus.INVALIDATED: 0,
    }[status]


def test_c05_generates_typed_temporal_validity_state_and_gate() -> None:
    upstream = build_c05_upstream(
        case_id="c05-gen",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = _build_result(upstream)

    assert result.state.validity_id
    assert result.state.items
    assert result.telemetry.ledger_events
    assert result.downstream_gate.restrictions
    assert result.no_ttl_only_shortcut_dependency is True
    assert result.no_blanket_reset_dependency is True
    assert result.no_blanket_reuse_dependency is True
    assert result.no_global_recompute_dependency is True


def test_c05_dependency_hit_requires_revalidation_and_unrelated_hit_preserves_unaffected() -> None:
    upstream = build_c05_upstream(
        case_id="c05-hit",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    baseline = _build_result(upstream)
    mode_item = _item_by_kind(baseline, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    assert mode_item is not None

    relevant = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))
    unrelated = _build_result(upstream, dependency_trigger_hits=("trigger:unrelated_noise",))

    relevant_mode = _item_by_kind(relevant, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    unrelated_mode = _item_by_kind(unrelated, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    assert relevant_mode is not None and unrelated_mode is not None
    assert relevant_mode.current_validity_status in {
        TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION,
        TemporalValidityStatus.NEEDS_FULL_REVALIDATION,
        TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
    }
    assert unrelated_mode.current_validity_status in {
        TemporalValidityStatus.STILL_VALID,
        TemporalValidityStatus.CONDITIONALLY_CARRIED,
        TemporalValidityStatus.NO_SAFE_REUSE_CLAIM,
    }


def test_c05_invariants_invalidated_provisional_and_contaminated() -> None:
    upstream = build_c05_upstream(
        case_id="c05-invariants",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    invalidated = _build_result(upstream, withdrawn_source_refs=("c04.mode_arbitration_from_c01_c02_c03_r04",))
    for item in invalidated.state.items:
        if item.current_validity_status == TemporalValidityStatus.INVALIDATED:
            assert item.item_id not in select_reusable_items(invalidated, include_provisional=True)
            assert can_reuse_item(invalidated, item.item_id, allow_provisional=True) is False

    provisional = _build_result(
        upstream,
        prior_temporal_validity_state=replace(invalidated.state, source_stream_sequence_index=-10),
        default_grace_window=0,
        provisional_horizon_steps=2,
    )
    for item in provisional.state.items:
        if item.current_validity_status == TemporalValidityStatus.CONDITIONALLY_CARRIED:
            assert item.current_validity_status != TemporalValidityStatus.STILL_VALID

    contaminated = _build_result(
        upstream,
        dependency_graph_complete=False,
        dependency_trigger_hits=("trigger:mode_shift",),
    )
    for item in contaminated.state.items:
        if item.current_validity_status == TemporalValidityStatus.DEPENDENCY_CONTAMINATED:
            assert item.item_id in contaminated.state.revalidation_item_ids
            assert item.item_id not in contaminated.state.reusable_item_ids


def test_c05_missing_dependency_basis_not_upgraded_and_grace_not_eternal() -> None:
    upstream = build_c05_upstream(
        case_id="c05-missing-basis",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    weak_basis = _build_result(
        upstream,
        dependency_graph_complete=False,
        context_shift_markers=("context:unknown_shift",),
    )
    assert any(
        item.current_validity_status == TemporalValidityStatus.DEPENDENCY_CONTAMINATED
        for item in weak_basis.state.items
    )

    seed = _build_result(upstream)
    aged_items = tuple(
        replace(item, last_validated_sequence_index=-3)
        for item in seed.state.items
    )
    aged_seed = replace(seed.state, items=aged_items)
    first = _build_result(
        upstream,
        prior_temporal_validity_state=aged_seed,
        default_grace_window=0,
        provisional_horizon_steps=1,
        expire_after_steps=1,
    )
    aged_first = replace(
        first.state,
        items=tuple(
            replace(item, last_validated_sequence_index=-3)
            for item in first.state.items
        ),
    )
    second = _build_result(
        upstream,
        prior_temporal_validity_state=aged_first,
        default_grace_window=0,
        provisional_horizon_steps=1,
        expire_after_steps=1,
    )
    assert any(
        item.current_validity_status in {TemporalValidityStatus.EXPIRED, TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION}
        for item in first.state.items
    )
    assert any(
        item.current_validity_status in {TemporalValidityStatus.EXPIRED, TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION}
        for item in second.state.items
    )


def test_c05_regression_ttl_only_blanket_reuse_blanket_invalidate_global_recompute_profiles() -> None:
    upstream = build_c05_upstream(
        case_id="c05-regression",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    baseline = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))
    ttl_like = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:mode_shift",),
        disable_dependency_trigger_logic=True,
    )
    blanket_reuse_like = _build_result(upstream, dependency_trigger_hits=())
    blanket_invalidate_like = _build_result(
        upstream,
        force_full_revalidation_items=tuple(item.item_id for item in baseline.state.items),
    )
    global_recompute_like = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:mode_shift",),
        disable_selective_scope_handling=True,
    )

    assert baseline.state.revalidation_item_ids != ttl_like.state.revalidation_item_ids
    assert len(blanket_reuse_like.state.reusable_item_ids) >= len(baseline.state.reusable_item_ids)
    assert len(blanket_invalidate_like.state.invalidated_item_ids) + len(blanket_invalidate_like.state.revalidation_item_ids) >= len(
        baseline.state.invalidated_item_ids
    )
    assert len(global_recompute_like.state.selective_scope_targets) >= len(
        baseline.state.selective_scope_targets
    )


def test_c05_metamorphic_relevant_dependency_weakening_never_strengthens_validity() -> None:
    upstream = build_c05_upstream(
        case_id="c05-metamorphic",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    stable = _build_result(upstream)
    weakened = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))
    contradicted = _build_result(upstream, contradicted_source_refs=("c04.mode_arbitration_from_c01_c02_c03_r04",))

    stable_mode = _item_by_kind(stable, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    weakened_mode = _item_by_kind(weakened, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    contradicted_mode = _item_by_kind(contradicted, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    assert stable_mode is not None and weakened_mode is not None and contradicted_mode is not None
    assert _status_rank(weakened_mode.current_validity_status) <= _status_rank(
        stable_mode.current_validity_status
    )
    assert _status_rank(contradicted_mode.current_validity_status) <= _status_rank(
        weakened_mode.current_validity_status
    )


def test_c05_ablation_dependency_trigger_propagation_provisional_selective_scope() -> None:
    upstream = build_c05_upstream(
        case_id="c05-ablation",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    full = _build_result(upstream, dependency_trigger_hits=("trigger:stream_source_withdrawal",))
    no_trigger = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:stream_source_withdrawal",),
        disable_dependency_trigger_logic=True,
    )
    no_propagation = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:stream_source_withdrawal",),
        disable_propagation_logic=True,
    )
    no_provisional = _build_result(
        upstream,
        prior_temporal_validity_state=full.state,
        default_grace_window=0,
        disable_provisional_handling=True,
    )
    no_selective = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:mode_shift",),
        disable_selective_scope_handling=True,
    )
    assert full.state.revalidation_item_ids != no_trigger.state.revalidation_item_ids
    assert len(no_propagation.state.dependency_contaminated_item_ids) <= len(
        full.state.dependency_contaminated_item_ids
    )
    assert len(no_selective.state.selective_scope_targets) >= len(full.state.selective_scope_targets)
    assert any(
        item.current_validity_status != TemporalValidityStatus.CONDITIONALLY_CARRIED
        for item in no_provisional.state.items
    )


def test_c05_matrix_item_kind_dependency_context_and_time_axes() -> None:
    profiles = (
        ("matrix-a", 14.0, 95.0, 34.0, True, ("trigger:mode_shift",), False),
        ("matrix-b", 66.0, 44.0, 74.0, False, ("trigger:unrelated_noise",), True),
        ("matrix-c", 58.0, 44.0, 62.0, True, (), False),
    )
    seen_kinds = set()
    for case_id, energy, cognitive, safety, unresolved, hits, incomplete in profiles:
        upstream = build_c05_upstream(
            case_id=case_id,
            energy=energy,
            cognitive=cognitive,
            safety=safety,
            unresolved_preference=unresolved,
        )
        result = _build_result(
            upstream,
            dependency_trigger_hits=hits,
            dependency_graph_complete=not incomplete,
        )
        seen_kinds.update(item.item_kind for item in result.state.items)
        assert result.state.items
        assert result.state.source_stream_sequence_index >= 0
    assert TemporalCarryoverItemKind.MODE_HOLD_PERMISSION in seen_kinds
    assert TemporalCarryoverItemKind.BRANCH_ACCESS_GATE in seen_kinds


def test_c05_role_boundary_does_not_choose_mode_or_close_tension() -> None:
    upstream = build_c05_upstream(
        case_id="c05-role-boundary",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = _build_result(upstream)
    view = derive_temporal_validity_contract_view(result)
    mode = choose_temporal_reuse_execution_mode(result)

    assert hasattr(result.state, "items")
    assert not hasattr(result.state, "active_mode")
    assert not hasattr(result.state, "tensions")
    assert view.requires_restrictions_read is True
    assert mode in {
        "reuse_valid_only",
        "reuse_with_provisional_limits",
        "run_selective_revalidation",
        "run_bounded_revalidation",
        "halt_reuse_and_rebuild_scope",
        "suspend_until_revalidation_basis",
    }


def test_c05_adversarial_old_stable_vs_fresh_broken_and_withdrawal_propagation() -> None:
    stable_upstream = build_c05_upstream(
        case_id="c05-old-stable",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    stable_seed = _build_result(stable_upstream)
    old_but_stable = _build_result(
        stable_upstream,
        prior_temporal_validity_state=stable_seed.state,
        dependency_trigger_hits=(),
        context_shift_markers=(),
    )

    broken_upstream = build_c05_upstream(
        case_id="c05-fresh-broken",
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )
    fresh_but_broken = _build_result(
        broken_upstream,
        dependency_trigger_hits=("trigger:mode_shift",),
        context_shift_markers=("c04.mode_hold_permission",),
    )
    withdrawn = _build_result(
        broken_upstream,
        withdrawn_source_refs=("c03.stream_diversification_from_c01_c02_r04",),
    )

    assert len(old_but_stable.state.reusable_item_ids) >= len(fresh_but_broken.state.reusable_item_ids)
    assert fresh_but_broken.state.revalidation_item_ids or fresh_but_broken.state.dependency_contaminated_item_ids
    assert withdrawn.state.invalidated_item_ids


def test_c05_provisional_grace_abuse_and_selective_scope_vs_full_scope() -> None:
    upstream = build_c05_upstream(
        case_id="c05-provisional-abuse",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    seed = _build_result(upstream)
    step1 = _build_result(
        upstream,
        prior_temporal_validity_state=seed.state,
        default_grace_window=0,
        provisional_horizon_steps=1,
        expire_after_steps=1,
    )
    step2 = _build_result(
        upstream,
        prior_temporal_validity_state=step1.state,
        default_grace_window=0,
        provisional_horizon_steps=1,
        expire_after_steps=1,
    )
    selective = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))
    full_like = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:mode_shift",),
        disable_selective_scope_handling=True,
    )

    assert any(
        item.current_validity_status != TemporalValidityStatus.CONDITIONALLY_CARRIED
        for item in step2.state.items
    )
    assert len(selective.state.selective_scope_targets) <= len(full_like.state.selective_scope_targets)


def test_c05_downstream_obedience_mode_revisit_branch_permissions() -> None:
    upstream = build_c05_upstream(
        case_id="c05-obedience",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    baseline = _build_result(upstream)
    degraded = _build_result(
        upstream,
        dependency_trigger_hits=(
            "trigger:mode_shift",
            "trigger:tension_closed",
            "trigger:diversification_conflict",
        ),
    )
    assert (
        can_continue_mode_hold(baseline),
        can_revisit_with_basis(baseline),
        can_open_branch_access(baseline),
    ) != (
        can_continue_mode_hold(degraded),
        can_revisit_with_basis(degraded),
        can_open_branch_access(degraded),
    )
    assert choose_temporal_reuse_execution_mode(degraded) in {
        "run_selective_revalidation",
        "run_bounded_revalidation",
        "halt_reuse_and_rebuild_scope",
        "suspend_until_revalidation_basis",
    }


def test_c05_causal_contour_stability_vs_ttl_and_blanket_reset_substitutes() -> None:
    upstream = build_c05_upstream(
        case_id="c05-causal-contour",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    baseline = _build_result(upstream)
    affected = _build_result(
        upstream,
        prior_temporal_validity_state=baseline.state,
        dependency_trigger_hits=("trigger:mode_shift",),
    )
    ttl_like = _build_result(
        upstream,
        prior_temporal_validity_state=baseline.state,
        dependency_trigger_hits=("trigger:mode_shift",),
        disable_dependency_trigger_logic=True,
    )
    blanket_reset_like = _build_result(
        upstream,
        prior_temporal_validity_state=baseline.state,
        force_full_revalidation_items=tuple(item.item_id for item in baseline.state.items),
    )

    assert len(affected.state.revalidation_item_ids) > 0
    assert len(affected.state.revalidation_item_ids) < len(baseline.state.items)
    assert len(ttl_like.state.revalidation_item_ids) < len(affected.state.revalidation_item_ids)
    assert len(blanket_reset_like.state.revalidation_item_ids) >= len(affected.state.revalidation_item_ids)


def test_c05_trigger_alias_equivalence_for_mode_shift_family() -> None:
    upstream = build_c05_upstream(
        case_id="c05-trigger-alias",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    canonical = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))
    alias = _build_result(upstream, dependency_trigger_hits=("trigger:modeShift",))
    context_alias = _build_result(
        upstream,
        context_shift_markers=("context:c04_mode_shift",),
    )

    canonical_mode = _item_by_kind(canonical, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    alias_mode = _item_by_kind(alias, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    context_mode = _item_by_kind(context_alias, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    assert canonical_mode is not None and alias_mode is not None and context_mode is not None
    assert canonical_mode.current_validity_status == alias_mode.current_validity_status
    assert canonical_mode.current_validity_status == context_mode.current_validity_status
    assert canonical.state.selective_scope_targets == alias.state.selective_scope_targets
    assert canonical.state.selective_scope_targets == context_alias.state.selective_scope_targets


def test_c05_incomplete_graph_local_shift_is_contained_not_blanket() -> None:
    upstream = build_c05_upstream(
        case_id="c05-incomplete-contained",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = _build_result(
        upstream,
        dependency_graph_complete=False,
        dependency_trigger_hits=("trigger:mode_shift",),
    )

    assert 0 < len(result.state.dependency_contaminated_item_ids) < len(result.state.items)
    assert len(result.state.selective_scope_targets) < len(result.state.items)
    branch_item = _item_by_kind(result, TemporalCarryoverItemKind.BRANCH_ACCESS_GATE)
    assert branch_item is not None
    assert branch_item.current_validity_status == TemporalValidityStatus.CONDITIONALLY_CARRIED


def test_c05_root_anchor_propagation_partitions_strict_and_review_dependents() -> None:
    upstream = build_c05_upstream(
        case_id="c05-root-partition",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    baseline = _build_result(upstream)
    stream_anchor = _item_by_kind(baseline, TemporalCarryoverItemKind.STREAM_ANCHOR)
    assert stream_anchor is not None
    withdrawn = _build_result(
        upstream,
        withdrawn_source_refs=(stream_anchor.source_provenance,),
    )

    mode_item = _item_by_kind(withdrawn, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    revisit_items = _items_by_kind(withdrawn, TemporalCarryoverItemKind.REVISIT_BASIS)
    weak_items = (
        _item_by_kind(withdrawn, TemporalCarryoverItemKind.BRANCH_ACCESS_GATE),
        _item_by_kind(withdrawn, TemporalCarryoverItemKind.CARRIED_ASSUMPTION),
    )
    assert mode_item is not None
    assert mode_item.current_validity_status == TemporalValidityStatus.DEPENDENCY_CONTAMINATED
    assert revisit_items
    assert all(
        item.current_validity_status == TemporalValidityStatus.DEPENDENCY_CONTAMINATED
        for item in revisit_items
    )
    assert all(item is not None for item in weak_items)
    assert all(
        item.current_validity_status == TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION
        for item in weak_items
        if item is not None
    )


def test_c05_weak_basis_pattern_reaches_no_safe_reuse_claim() -> None:
    upstream = build_c05_upstream(
        case_id="c05-no-safe-weak-basis",
        energy=58.0,
        cognitive=44.0,
        safety=62.0,
        unresolved_preference=True,
    )
    result = _build_result(
        upstream,
        dependency_graph_complete=False,
        context_shift_markers=("context:c04_mode_shift",),
    )

    assert result.state.no_safe_reuse_item_ids
    assumption_item = _item_by_kind(result, TemporalCarryoverItemKind.CARRIED_ASSUMPTION)
    assert assumption_item is not None
    assert assumption_item.current_validity_status == TemporalValidityStatus.NO_SAFE_REUSE_CLAIM
    assert len(result.state.no_safe_reuse_item_ids) < len(result.state.items)


def test_c05_regression_complete_graph_partial_hit_stays_local() -> None:
    upstream = build_c05_upstream(
        case_id="c05-locality-regression",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    result = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))

    mode_item = _item_by_kind(result, TemporalCarryoverItemKind.MODE_HOLD_PERMISSION)
    branch_item = _item_by_kind(result, TemporalCarryoverItemKind.BRANCH_ACCESS_GATE)
    assert mode_item is not None and branch_item is not None
    assert result.state.selective_scope_targets == (mode_item.item_id,)
    assert branch_item.item_id not in result.state.selective_scope_targets
    assert len(result.state.selective_scope_targets) < len(result.state.items)


def test_c05_downstream_obedience_specific_permissions_preserved_after_hardening() -> None:
    upstream = build_c05_upstream(
        case_id="c05-obedience-specific",
        energy=14.0,
        cognitive=95.0,
        safety=34.0,
        unresolved_preference=True,
    )
    baseline = _build_result(upstream)
    mode_invalidated = _build_result(upstream, dependency_trigger_hits=("trigger:mode_shift",))
    revisit_invalidated = _build_result(upstream, dependency_trigger_hits=("trigger:tension_closed",))
    branch_invalidated = _build_result(
        upstream,
        dependency_trigger_hits=("trigger:diversification_conflict",),
    )

    assert can_continue_mode_hold(baseline) is True
    assert can_revisit_with_basis(baseline) is True
    assert can_open_branch_access(baseline) is True

    assert can_continue_mode_hold(mode_invalidated) is False
    assert can_revisit_with_basis(mode_invalidated) is True
    assert can_open_branch_access(mode_invalidated) is True

    assert can_continue_mode_hold(revisit_invalidated) is True
    assert can_revisit_with_basis(revisit_invalidated) is False
    assert can_open_branch_access(revisit_invalidated) is True

    assert can_continue_mode_hold(branch_invalidated) is True
    assert can_revisit_with_basis(branch_invalidated) is True
    assert can_open_branch_access(branch_invalidated) is False
