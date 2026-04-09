from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.a_line_normalization import build_a_line_normalization
from substrate.m_minimal import build_m_minimal
from substrate.n_minimal import build_n_minimal
from substrate.self_contour import build_s_minimal_contour
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome, execute_subject_tick
from substrate.t01_semantic_field import T01SceneStatus, build_t01_active_semantic_field
from substrate.t02_relation_binding import (
    T02AssemblyMode,
    T02BindingStatus,
    T02Operation,
    build_t02_constrained_scene,
    derive_t02_constrained_scene_contract_view,
    derive_t02_preverbal_constraint_consumer_view,
    derive_t02_relation_signature,
    evolve_t02_constrained_scene,
    require_t02_preverbal_constraint_consumer_ready,
    t02_constrained_scene_snapshot,
)
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_effect_packet,
    build_world_observation_packet,
    run_world_adapter_cycle,
)
from substrate.world_entry_contract import build_world_entry_contract


def _observation(case_id: str):
    return build_world_observation_packet(
        observation_id=f"obs-{case_id}",
        source_ref="world.sensor.t02",
        observed_at="2026-04-16T10:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _upstream_bundle(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str,
):
    tick_id = f"tick-{case_id}"
    if effect_action_id == "__MATCHED__":
        effect_action_id = f"world-action-{tick_id}"
    effect_packet = None
    if effect_action_id is not None:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=effect_action_id,
            observed_at="2026-04-16T10:00:01+00:00",
            source_ref="world.effect.t02",
            success=True,
        )
    adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=include_observation,
            adapter_available=include_observation,
            observation_packet=_observation(case_id) if include_observation else None,
            effect_packet=effect_packet,
        ),
        request_action_candidate=request_action,
        source_lineage=("test.t02",),
    )
    world_entry_result = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.t02",),
    )
    s_minimal_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        world_adapter_result=adapter_result,
        source_lineage=("test.t02",),
    )
    a_line_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        source_lineage=("test.t02",),
    )
    m_minimal_result = build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        c05_validity_action=c05_action,
        source_lineage=("test.t02",),
    )
    n_minimal_result = build_n_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        source_lineage=("test.t02",),
    )
    return tick_id, world_entry_result, s_minimal_result, a_line_result, m_minimal_result, n_minimal_result


def _t01_result(
    case_id: str,
    *,
    wording_ref: str,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str,
):
    tick_id, world_entry_result, s_minimal_result, a_line_result, m_minimal_result, n_minimal_result = (
        _upstream_bundle(
            case_id,
            include_observation=include_observation,
            request_action=request_action,
            effect_action_id=effect_action_id,
            c05_action=c05_action,
        )
    )
    t01_result = build_t01_active_semantic_field(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        wording_surface_ref=wording_ref,
        source_lineage=("test.t02",),
    )
    return (
        tick_id,
        world_entry_result,
        s_minimal_result,
        a_line_result,
        m_minimal_result,
        n_minimal_result,
        t01_result,
    )


def _t02_result(
    case_id: str,
    *,
    wording_ref: str,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str = "reuse_without_revalidation",
    assembly_mode: T02AssemblyMode = T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION,
    preserve_conflicts: bool = True,
    enforce_stop_conditions: bool = True,
    conflict_seed: bool = False,
):
    (
        tick_id,
        world_entry_result,
        s_minimal_result,
        a_line_result,
        m_minimal_result,
        n_minimal_result,
        t01_result,
    ) = _t01_result(
        case_id,
        wording_ref=wording_ref,
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
        c05_action=c05_action,
    )
    if conflict_seed and t01_result.state.relation_edges:
        forced_edges = tuple(
            replace(
                edge,
                contested=True,
                relation_type=f"{edge.relation_type}:conflict:forced",
            )
            for edge in t01_result.state.relation_edges
        )
        t01_result = replace(
            t01_result,
            state=replace(
                t01_result.state,
                relation_edges=forced_edges,
                scene_status=T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
            ),
        )
    return (
        build_t02_constrained_scene(
            tick_id=tick_id,
            t01_result=t01_result,
            world_entry_result=world_entry_result,
            s_minimal_result=s_minimal_result,
            a_line_result=a_line_result,
            m_minimal_result=m_minimal_result,
            n_minimal_result=n_minimal_result,
            c05_validity_action=c05_action,
            assembly_mode=assembly_mode,
            preserve_conflicts=preserve_conflicts,
            enforce_stop_conditions=enforce_stop_conditions,
            source_lineage=("test.t02",),
        ),
        t01_result,
    )


def test_t02_ordinary_binding_constraint_state_is_materialized() -> None:
    result, _ = _t02_result(
        "ordinary",
        wording_ref="wording:t02-ordinary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert result.state.constrained_scene_id.startswith("t02-constrained-scene:")
    assert result.state.relation_bindings
    assert result.state.propagation_records
    assert isinstance(result.state.conflict_records, tuple)
    assert result.state.narrowed_role_candidates
    assert "t02_relation_binding_contract_must_be_read" in result.gate.restrictions


def test_t02_invariants_state_is_separate_from_t01_and_preserves_status_distinctions() -> None:
    weak, weak_t01 = _t02_result(
        "invariant-weak",
        wording_ref="wording:t02-invariant-weak",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert weak.state.source_t01_scene_id == weak_t01.state.scene_id
    assert weak.state.raw_scene_nodes == tuple(
        entity.entity_id for entity in weak_t01.state.active_entities
    )
    assert weak.state.scene_status in {
        weak.state.scene_status.FRAGMENT_ONLY,
        weak.state.scene_status.AUTHORITY_INSUFFICIENT_FOR_PROPAGATION,
        weak.state.scene_status.NO_CLEAN_BINDING_COMMIT,
    }
    assert weak.gate.pre_verbal_constraint_consumer_ready is False


def test_t02_metamorphic_paraphrase_invariance_for_three_groups() -> None:
    groups = (
        (
            "p1a",
            "wording:agent places cup on table",
            "p1b",
            "wording:cup is placed on table by agent",
        ),
        (
            "p2a",
            "wording:signal shifts after action",
            "p2b",
            "wording:after acting, the signal changes",
        ),
        (
            "p3a",
            "wording:memory remains under review",
            "p3b",
            "wording:review is still required for memory",
        ),
    )
    for left_id, left_wording, right_id, right_wording in groups:
        left, _ = _t02_result(
            left_id,
            wording_ref=left_wording,
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        )
        right, _ = _t02_result(
            right_id,
            wording_ref=right_wording,
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        )
        assert derive_t02_relation_signature(left) == derive_t02_relation_signature(right)


def test_t02_metamorphic_authority_and_scope_change_propagation_reach() -> None:
    strong, _ = _t02_result(
        "contrast-strong",
        wording_ref="wording:t02-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c05_action="reuse_without_revalidation",
    )
    scoped, _ = _t02_result(
        "contrast-scoped",
        wording_ref="wording:t02-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    strong_active = sum(
        1
        for item in strong.state.propagation_records
        if item.status.value == "active" and item.effect_type.value != "no_effect"
    )
    scoped_active = sum(
        1
        for item in scoped.state.propagation_records
        if item.status.value == "active" and item.effect_type.value != "no_effect"
    )
    assert strong.state.scene_status != scoped.state.scene_status
    assert strong_active >= scoped_active


def test_t02_ablation_shortcuts_are_machine_readable_and_causally_degrading() -> None:
    lawful, _ = _t02_result(
        "abl-lawful",
        wording_ref="wording:t02-abl-lawful",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    graph, _ = _t02_result(
        "abl-graph",
        wording_ref="wording:t02-abl-graph",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
        assembly_mode=T02AssemblyMode.GRAPH_EDGE_HEURISTIC_ABLATION,
    )
    spread, _ = _t02_result(
        "abl-spread",
        wording_ref="wording:t02-abl-spread",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        assembly_mode=T02AssemblyMode.SPREADING_ACTIVATION_ABLATION,
    )
    hidden, _ = _t02_result(
        "abl-hidden",
        wording_ref="wording:t02-abl-hidden",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        assembly_mode=T02AssemblyMode.HIDDEN_LOGIC_ABLATION,
    )
    flattened, _ = _t02_result(
        "abl-flattened",
        wording_ref="wording:t02-abl-flattened",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        assembly_mode=T02AssemblyMode.RAW_VS_PROPAGATED_FLATTEN_ABLATION,
    )
    no_stop, _ = _t02_result(
        "abl-no-stop",
        wording_ref="wording:t02-abl-no-stop",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
        enforce_stop_conditions=False,
    )
    no_conflict, _ = _t02_result(
        "abl-no-conflict",
        wording_ref="wording:t02-abl-no-conflict",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        conflict_seed=True,
        preserve_conflicts=False,
    )

    assert lawful.gate.forbidden_shortcuts == ()
    assert "graph_edge_heuristic_rebranding" in graph.gate.forbidden_shortcuts
    assert "authority_leak_propagation" in graph.gate.forbidden_shortcuts
    assert "spreading_activation_rebranding" in spread.gate.forbidden_shortcuts
    assert "hidden_logic_shortcut" in hidden.gate.forbidden_shortcuts
    assert "raw_vs_propagated_collapse" in flattened.gate.forbidden_shortcuts
    assert (
        derive_t02_preverbal_constraint_consumer_view(flattened).raw_vs_propagated_distinct
        is False
    )
    assert "scope_leak_propagation" in no_stop.gate.forbidden_shortcuts
    assert "silent_conflict_overwrite" in no_conflict.gate.forbidden_shortcuts
    assert no_conflict.state.conflict_records == ()


def test_t02_matrix_covers_confirmed_provisional_blocked_conflicted_and_incompatible() -> None:
    confirmed, _ = _t02_result(
        "matrix-confirmed",
        wording_ref="wording:t02-matrix-confirmed",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    provisional, _ = _t02_result(
        "matrix-provisional",
        wording_ref="wording:t02-matrix-provisional",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    blocked, _ = _t02_result(
        "matrix-blocked",
        wording_ref="wording:t02-matrix-blocked",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    conflicted, _ = _t02_result(
        "matrix-conflicted",
        wording_ref="wording:t02-matrix-conflicted",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        conflict_seed=True,
    )
    confirmed_id = next(
        item.binding_id
        for item in confirmed.state.relation_bindings
        if item.status is T02BindingStatus.CONFIRMED
    )
    incompatible = evolve_t02_constrained_scene(
        result=confirmed,
        operation=T02Operation.MARK_INCOMPATIBLE,
        binding_id=confirmed_id,
    )

    statuses = {
        *(item.status for item in confirmed.state.relation_bindings),
        *(item.status for item in provisional.state.relation_bindings),
        *(item.status for item in blocked.state.relation_bindings),
        *(item.status for item in conflicted.state.relation_bindings),
        *(item.status for item in incompatible.state.relation_bindings),
    }
    assert T02BindingStatus.CONFIRMED in statuses
    assert T02BindingStatus.PROVISIONAL in statuses
    assert any(status in statuses for status in {T02BindingStatus.BLOCKED, T02BindingStatus.CANDIDATE})
    assert T02BindingStatus.CONFLICTED in statuses
    assert T02BindingStatus.INCOMPATIBLE in statuses


def test_t02_role_boundary_does_not_rebuild_scene_or_act_as_planner() -> None:
    result, t01_result = _t02_result(
        "role-boundary",
        wording_ref="wording:t02-role-boundary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert result.state.source_t01_scene_id == t01_result.state.scene_id
    assert all(item.provenance.startswith("t02.binding.") for item in result.state.relation_bindings)
    assert all(item.provenance.startswith("t02.constraint.") for item in result.state.constraint_objects)
    assert "planner" not in result.reason
    assert result.scope_marker.t03_implemented is False
    assert result.scope_marker.t04_implemented is False
    assert result.scope_marker.o01_implemented is False


def test_t02_conflict_preservation_vs_silent_overwrite_differ_causally() -> None:
    preserved, _ = _t02_result(
        "conflict-preserved",
        wording_ref="wording:t02-conflict-preserved",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        conflict_seed=True,
        preserve_conflicts=True,
    )
    overwritten, _ = _t02_result(
        "conflict-overwritten",
        wording_ref="wording:t02-conflict-overwritten",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        conflict_seed=True,
        preserve_conflicts=False,
    )
    assert preserved.state.scene_status.value == "conflict_preserved"
    assert overwritten.state.scene_status.value == "no_clean_binding_commit"
    assert len(preserved.state.conflict_records) > 0
    assert len(overwritten.state.conflict_records) == 0
    assert "silent_conflict_overwrite" in overwritten.gate.forbidden_shortcuts


def test_t02_downstream_preverbal_consumer_is_load_bearing() -> None:
    clean, _ = _t02_result(
        "downstream-clean",
        wording_ref="wording:t02-downstream-clean",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    weak, _ = _t02_result(
        "downstream-weak",
        wording_ref="wording:t02-downstream-weak",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    clean_view = derive_t02_preverbal_constraint_consumer_view(clean)
    weak_view = derive_t02_preverbal_constraint_consumer_view(weak)
    assert clean_view.can_consume_constrained_scene is True
    assert weak_view.can_consume_constrained_scene is False
    assert require_t02_preverbal_constraint_consumer_ready(clean).can_consume_constrained_scene is True
    with pytest.raises(PermissionError):
        require_t02_preverbal_constraint_consumer_ready(weak)


def test_t02_downstream_contract_distinguishes_raw_scene_from_propagated_consequences() -> None:
    result, _ = _t02_result(
        "downstream-distinction",
        wording_ref="wording:t02-downstream-distinction",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    view = derive_t02_constrained_scene_contract_view(result)
    consumer_view = derive_t02_preverbal_constraint_consumer_view(view)
    assert view.raw_relation_candidates
    assert view.confirmed_bindings
    assert consumer_view.raw_vs_propagated_distinct is True


def test_t02_blocked_or_conflicted_consequences_keep_raw_vs_propagated_distinction() -> None:
    conflict, _ = _t02_result(
        "downstream-conflict-distinction",
        wording_ref="wording:t02-downstream-conflict-distinction",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        conflict_seed=True,
        preserve_conflicts=True,
    )
    view = derive_t02_constrained_scene_contract_view(conflict)
    consumer_view = derive_t02_preverbal_constraint_consumer_view(view)
    assert view.blocked_or_conflicted_consequences
    assert consumer_view.raw_vs_propagated_distinct is True


def test_t02_rt01_consumer_requirement_is_path_affecting() -> None:
    baseline = execute_subject_tick(
        SubjectTickInput(
            case_id="t02-rt01-baseline",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(),
    )
    required = execute_subject_tick(
        SubjectTickInput(
            case_id="t02-rt01-required",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(require_t02_constrained_scene_consumer=True),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.t02_relation_binding_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.state.execution_checkpoints
    )


def test_t02_harness_contains_minimum_case_inventory() -> None:
    scene_cases = (
        ("case-1", True, True, "__MATCHED__", "reuse_without_revalidation"),
        ("case-2", True, True, None, "run_selective_revalidation"),
        ("case-3", True, False, None, "reuse_without_revalidation"),
        ("case-4", False, False, None, "reuse_without_revalidation"),
        ("case-5", True, True, "__MATCHED__", "run_bounded_revalidation"),
        ("case-6", True, True, None, "suspend_until_revalidation_basis"),
        ("case-7", False, True, None, "halt_reuse_and_rebuild_scope"),
        ("case-8", True, True, "__MATCHED__", "reuse_without_revalidation"),
    )
    paraphrase_groups = (
        ("pg-1a", "wording:pg-1a", "pg-1b", "wording:pg-1b"),
        ("pg-2a", "wording:pg-2a", "pg-2b", "wording:pg-2b"),
        ("pg-3a", "wording:pg-3a", "pg-3b", "wording:pg-3b"),
    )
    multi_binding_competition_cases = (
        ("cmp-1", True, True, "__MATCHED__", "reuse_without_revalidation"),
        ("cmp-2", True, True, None, "run_selective_revalidation"),
        ("cmp-3", True, True, "__MATCHED__", "run_bounded_revalidation"),
    )
    authority_conflict_cases = (
        ("ac-1", False, False, None, "reuse_without_revalidation"),
        ("ac-2", False, True, None, "run_selective_revalidation"),
    )
    scoped_constraint_cases = (
        ("sc-1", True, True, None, "run_selective_revalidation"),
        ("sc-2", True, True, None, "suspend_until_revalidation_basis"),
    )
    assert len(scene_cases) >= 8
    assert len(paraphrase_groups) >= 3
    assert len(multi_binding_competition_cases) >= 3
    assert len(authority_conflict_cases) >= 2
    assert len(scoped_constraint_cases) >= 2

    results = [
        _t02_result(
            case_id,
            wording_ref=f"wording:{case_id}",
            include_observation=obs,
            request_action=action,
            effect_action_id=effect,
            c05_action=c05_action,
        )[0]
        for case_id, obs, action, effect, c05_action in scene_cases
    ]
    assert len(results) == 8


def test_t02_snapshot_is_inspectable() -> None:
    result, _ = _t02_result(
        "snapshot",
        wording_ref="wording:t02-snapshot",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    snapshot = t02_constrained_scene_snapshot(result)
    assert "state" in snapshot
    assert "gate" in snapshot
    assert "scope_marker" in snapshot
    assert "telemetry" in snapshot
    assert snapshot["state"]["constrained_scene_id"] == result.state.constrained_scene_id
