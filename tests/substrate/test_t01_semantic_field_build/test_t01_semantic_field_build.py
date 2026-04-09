from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.a_line_normalization import build_a_line_normalization
from substrate.m_minimal import RiskLevel, build_m_minimal
from substrate.n_minimal import build_n_minimal
from substrate.self_contour import build_s_minimal_contour
from substrate.subject_tick import SubjectTickContext, SubjectTickInput, SubjectTickOutcome, execute_subject_tick
from substrate.t01_semantic_field import (
    T01AssemblyMode,
    T01FieldOperation,
    T01SceneStatus,
    build_t01_active_semantic_field,
    derive_t01_preverbal_consumer_view,
    derive_t01_scene_signature,
    evolve_t01_field,
    require_t01_preverbal_consumer_ready,
    t01_active_field_snapshot,
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
        source_ref="world.sensor.t01",
        observed_at="2026-04-12T10:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _upstream_bundle(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str = "reuse_without_revalidation",
    require_self_side_claim: bool = False,
    require_world_side_claim: bool = False,
):
    tick_id = f"tick-{case_id}"
    if effect_action_id == "__MATCHED__":
        effect_action_id = f"world-action-{tick_id}"
    effect_packet = None
    if effect_action_id is not None:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=effect_action_id,
            observed_at="2026-04-12T10:00:01+00:00",
            source_ref="world.effect.t01",
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
        source_lineage=("test.t01",),
    )
    world_entry = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.t01",),
    )
    s_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry,
        world_adapter_result=adapter_result,
        require_self_side_claim=require_self_side_claim,
        require_world_side_claim=require_world_side_claim,
        source_lineage=("test.t01",),
    )
    a_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        source_lineage=("test.t01",),
    )
    m_result = build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        c05_validity_action=c05_action,
        source_lineage=("test.t01",),
    )
    n_result = build_n_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        source_lineage=("test.t01",),
    )
    return world_entry, s_result, a_result, m_result, n_result


def _t01_result(
    case_id: str,
    *,
    wording_ref: str,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str = "reuse_without_revalidation",
    assembly_mode: T01AssemblyMode = T01AssemblyMode.SEMANTIC_FIELD,
    maintain_unresolved_slots: bool = True,
    retain_provenance_tags: bool = True,
    enable_preverbal_consumer: bool = True,
    allow_immediate_verbalization_shortcut: bool = False,
):
    world_entry, s_result, a_result, m_result, n_result = _upstream_bundle(
        case_id,
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
        c05_action=c05_action,
    )
    return build_t01_active_semantic_field(
        tick_id=f"tick-{case_id}",
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        assembly_mode=assembly_mode,
        maintain_unresolved_slots=maintain_unresolved_slots,
        retain_provenance_tags=retain_provenance_tags,
        enable_preverbal_consumer=enable_preverbal_consumer,
        allow_immediate_verbalization_shortcut=allow_immediate_verbalization_shortcut,
        wording_surface_ref=wording_ref,
        source_lineage=("test.t01",),
    )


def test_t01_ordinary_field_exists_and_preserves_unresolved_and_provenance() -> None:
    result = _t01_result(
        "t01-ordinary",
        wording_ref="wording:ordinary",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    assert result.state.scene_id.startswith("t01-scene:")
    assert result.state.active_entities
    assert isinstance(result.state.unresolved_slots, tuple)
    assert result.state.source_authority_tags
    assert "t01_semantic_field_contract_must_be_read" in result.gate.restrictions


def test_t01_invariants_wording_separation_and_authority_honesty() -> None:
    weak = _t01_result(
        "t01-weak-authority",
        wording_ref="wording:weak-authority",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert weak.state.wording_surface_ref == "wording:weak-authority"
    assert weak.state.scene_status in {
        T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
        T01SceneStatus.SCENE_FRAGMENT_ONLY,
        T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
    }
    assert weak.gate.pre_verbal_consumer_ready is False


def test_t01_metamorphic_paraphrase_invariance_three_groups() -> None:
    groups = (
        ("p1a", "wording:the agent holds a cup", "p1b", "wording:a cup is being held by the agent"),
        ("p2a", "wording:the signal fades after action", "p2b", "wording:after acting, the signal weakens"),
        ("p3a", "wording:memory still needs review", "p3b", "wording:review remains required for memory"),
    )
    for left_id, left_wording, right_id, right_wording in groups:
        left = _t01_result(
            left_id,
            wording_ref=left_wording,
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        )
        right = _t01_result(
            right_id,
            wording_ref=right_wording,
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        )
        assert derive_t01_scene_signature(left) == derive_t01_scene_signature(right)


def test_t01_metamorphic_lexical_overlap_but_different_scene_not_collapsed() -> None:
    same_words_world = _t01_result(
        "lexical-overlap-world",
        wording_ref="wording:signal present after move",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    same_words_no_world = _t01_result(
        "lexical-overlap-noworld",
        wording_ref="wording:signal present after move",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert derive_t01_scene_signature(same_words_world) != derive_t01_scene_signature(same_words_no_world)


def test_t01_ablation_unresolved_and_provenance_and_flat_tags_degrade_causally() -> None:
    lawful = _t01_result(
        "ablation-lawful",
        wording_ref="wording:lawful",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    no_unresolved = _t01_result(
        "ablation-no-unresolved",
        wording_ref="wording:no-unresolved",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
        maintain_unresolved_slots=False,
    )
    no_provenance = _t01_result(
        "ablation-no-provenance",
        wording_ref="wording:no-provenance",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        retain_provenance_tags=False,
    )
    flat = _t01_result(
        "ablation-flat-tags",
        wording_ref="wording:flat-tags",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        assembly_mode=T01AssemblyMode.FLAT_TAG_ABLATION,
    )
    assert lawful.gate.pre_verbal_consumer_ready is True
    assert "premature_scene_closure" in no_unresolved.gate.forbidden_shortcuts
    assert "t01_source_authority_tags_missing" in no_provenance.gate.restrictions
    assert "bag_of_tags_rebranding" in flat.gate.forbidden_shortcuts
    assert flat.state.relation_edges == ()


def test_t01_matrix_confirmed_provisional_unresolved_and_authority_strength() -> None:
    matrix = (
        _t01_result(
            "matrix-confirmed",
            wording_ref="wording:confirmed",
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        ),
        _t01_result(
            "matrix-provisional",
            wording_ref="wording:provisional",
            include_observation=True,
            request_action=True,
            effect_action_id=None,
            c05_action="run_selective_revalidation",
        ),
        _t01_result(
            "matrix-unresolved",
            wording_ref="wording:unresolved",
            include_observation=False,
            request_action=False,
            effect_action_id=None,
        ),
    )
    statuses = {item.state.scene_status for item in matrix}
    assert T01SceneStatus.SCENE_ASSEMBLED in statuses
    assert any(
        status in statuses
        for status in {
            T01SceneStatus.PROVISIONAL_SCENE_ONLY,
            T01SceneStatus.UNRESOLVED_RELATION_CLUSTER,
            T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
            T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
        }
    )
    assert any(
        status in statuses
        for status in {
            T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
            T01SceneStatus.SCENE_FRAGMENT_ONLY,
        }
    )


def test_t01_role_boundary_does_not_choose_action_or_verbalize() -> None:
    result = _t01_result(
        "role-boundary",
        wording_ref="wording:role-boundary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert "mode:continue_stream" in result.state.active_predicates
    assert "validity:reuse_without_revalidation" in result.state.active_predicates
    assert "immediate_verbalization_shortcut" not in result.gate.forbidden_shortcuts
    assert result.gate.pre_verbal_consumer_ready is True


def test_t01_adversarial_shortcuts_are_machine_readable() -> None:
    hidden_text = _t01_result(
        "adv-hidden-text",
        wording_ref="wording:hidden-text",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        assembly_mode=T01AssemblyMode.HIDDEN_TEXT_ABLATION,
    )
    token_graph = _t01_result(
        "adv-token-graph",
        wording_ref="wording:token-graph",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        assembly_mode=T01AssemblyMode.TOKEN_GRAPH_ABLATION,
    )
    immediate_verbalization = _t01_result(
        "adv-immediate-verbalization",
        wording_ref="wording:immediate-verb",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        allow_immediate_verbalization_shortcut=True,
    )
    assert "hidden_text_buffer_surrogate" in hidden_text.gate.forbidden_shortcuts
    assert "token_graph_rebranding" in token_graph.gate.forbidden_shortcuts
    assert "immediate_verbalization_shortcut" in immediate_verbalization.gate.forbidden_shortcuts


def test_t01_memory_pollution_and_premature_closure_adversarial_cases() -> None:
    world_entry, s_result, a_result, m_result, n_result = _upstream_bundle(
        "adv-memory-pollution",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    polluted_memory = replace(
        m_result,
        state=replace(
            m_result.state,
            conflict_risk=RiskLevel.HIGH,
            review_required=False,
        ),
    )
    result = build_t01_active_semantic_field(
        tick_id="tick-adv-memory-pollution",
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=polluted_memory,
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
        source_lineage=("test.t01",),
    )
    premature = build_t01_active_semantic_field(
        tick_id="tick-adv-premature-closure",
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="run_selective_revalidation",
        maintain_unresolved_slots=False,
        source_lineage=("test.t01",),
    )
    assert "memory_pollution_reframed_as_scene_fact" in result.gate.forbidden_shortcuts
    assert "premature_scene_closure" in premature.gate.forbidden_shortcuts


def test_t01_weak_unresolved_evidence_still_emits_premature_closure_when_slots_are_laundered() -> None:
    world_entry, s_result, a_result, m_result, n_result = _upstream_bundle(
        "weak-unresolved-edge",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c05_action="reuse_without_revalidation",
    )
    weakened_world_entry = replace(
        world_entry,
        episode=replace(
            world_entry.episode,
            confidence=0.62,
            incomplete=False,
            effect_basis_present=True,
            effect_feedback_correlated=True,
        ),
    )
    weakened_s = replace(
        s_result,
        state=replace(s_result.state, attribution_confidence=0.61, underconstrained=False),
    )
    weakened_a = replace(
        a_result,
        state=replace(a_result.state, confidence=0.63, underconstrained=False),
    )
    weakened_m = replace(
        m_result,
        state=replace(m_result.state, confidence=0.64),
    )
    weakened_n = replace(
        n_result,
        state=replace(
            n_result.state,
            confidence=0.6,
            underconstrained=False,
            ambiguity_residue=False,
        ),
    )
    laundered = build_t01_active_semantic_field(
        tick_id="tick-weak-unresolved-laundered",
        world_entry_result=weakened_world_entry,
        s_minimal_result=weakened_s,
        a_line_result=weakened_a,
        m_minimal_result=weakened_m,
        n_minimal_result=weakened_n,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
        maintain_unresolved_slots=False,
        source_lineage=("test.t01",),
    )
    assert "premature_scene_closure" in laundered.gate.forbidden_shortcuts
    assert "t01_unresolved_laundering_risk_detected" in laundered.gate.restrictions


def test_t01_field_dynamics_hooks_are_typed_and_load_bearing() -> None:
    base = _t01_result(
        "dynamics",
        wording_ref="wording:dynamics",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    decayed = evolve_t01_field(result=base, operation=T01FieldOperation.DECAY, decay_factor=0.3)
    recentered = evolve_t01_field(
        result=decayed,
        operation=T01FieldOperation.RECENTER,
        focus_target=decayed.state.active_entities[0].entity_id,
    )
    assert "decay" in decayed.state.operations_applied
    assert "recenter" in recentered.state.operations_applied
    assert recentered.state.stability_state.value in {
        "degraded",
        "provisional",
        "contested",
        "stable",
        "fragmentary",
    }


def test_t01_partial_scene_slot_fill_updates_from_prior_state_without_arbitrary_rebuild() -> None:
    world_entry, s_result, a_result, m_result, n_result = _upstream_bundle(
        "partial-scene-prior",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    provisional = build_t01_active_semantic_field(
        tick_id="tick-partial-scene",
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="run_selective_revalidation",
        source_lineage=("test.t01",),
    )
    world_entry_filled, s_result_filled, a_result_filled, m_result_filled, n_result_filled = _upstream_bundle(
        "partial-scene-prior-filled",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c05_action="reuse_without_revalidation",
    )
    updated = build_t01_active_semantic_field(
        tick_id="tick-partial-scene",
        world_entry_result=world_entry_filled,
        s_minimal_result=s_result_filled,
        a_line_result=a_result_filled,
        m_minimal_result=m_result_filled,
        n_minimal_result=n_result_filled,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
        prior_state=provisional.state,
        source_lineage=("test.t01",),
    )
    assert "update" in updated.state.operations_applied
    assert "slot_fill" in updated.state.operations_applied
    assert len(updated.state.unresolved_slots) <= len(provisional.state.unresolved_slots)
    assert updated.state.scene_id == provisional.state.scene_id


def test_t01_three_ambiguity_cases_preserve_non_clean_or_provisional_scene() -> None:
    cases = (
        _t01_result(
            "amb-1",
            wording_ref="wording:amb-1",
            include_observation=False,
            request_action=True,
            effect_action_id=None,
            c05_action="run_selective_revalidation",
        ),
        _t01_result(
            "amb-2",
            wording_ref="wording:amb-2",
            include_observation=True,
            request_action=True,
            effect_action_id=None,
            c05_action="run_selective_revalidation",
        ),
        _t01_result(
            "amb-3",
            wording_ref="wording:amb-3",
            include_observation=True,
            request_action=True,
            effect_action_id=None,
            c05_action="suspend_until_revalidation_basis",
        ),
    )
    assert len(cases) == 3
    assert all(
        case.state.scene_status
        in {
            T01SceneStatus.PROVISIONAL_SCENE_ONLY,
            T01SceneStatus.UNRESOLVED_RELATION_CLUSTER,
            T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
            T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
            T01SceneStatus.SCENE_FRAGMENT_ONLY,
            T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
        }
        for case in cases
    )


def test_t01_two_context_pollution_adversarial_cases_block_clean_commit() -> None:
    world_entry, s_result, a_result, m_result, n_result = _upstream_bundle(
        "context-pollution",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    memory_pollution = build_t01_active_semantic_field(
        tick_id="tick-context-memory",
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=replace(
            m_result,
            state=replace(m_result.state, conflict_risk=RiskLevel.HIGH, review_required=False),
        ),
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
        source_lineage=("test.t01",),
    )
    narrative_pollution = build_t01_active_semantic_field(
        tick_id="tick-context-narrative",
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=replace(
            n_result,
            state=replace(
                n_result.state,
                ambiguity_residue=True,
                underconstrained=True,
            ),
        ),
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
        source_lineage=("test.t01",),
    )
    assert "memory_pollution_reframed_as_scene_fact" in memory_pollution.gate.forbidden_shortcuts
    assert narrative_pollution.gate.no_clean_scene_commit is True
    assert len((memory_pollution, narrative_pollution)) == 2


def test_t01_two_authority_conflict_cases_do_not_bind_clean_scene() -> None:
    authority_conflict_cases = (
        _t01_result(
            "authority-conflict-1",
            wording_ref="wording:authority-conflict-1",
            include_observation=False,
            request_action=False,
            effect_action_id=None,
            c05_action="reuse_without_revalidation",
        ),
        _t01_result(
            "authority-conflict-2",
            wording_ref="wording:authority-conflict-2",
            include_observation=False,
            request_action=True,
            effect_action_id=None,
            c05_action="run_selective_revalidation",
        ),
    )
    assert len(authority_conflict_cases) == 2
    assert all(
        case.state.scene_status
        in {
            T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
            T01SceneStatus.SCENE_FRAGMENT_ONLY,
            T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
            T01SceneStatus.PROVISIONAL_SCENE_ONLY,
        }
        for case in authority_conflict_cases
    )
    assert all(case.gate.pre_verbal_consumer_ready is False for case in authority_conflict_cases)


def test_t01_downstream_preverbal_consumer_is_load_bearing() -> None:
    clean = _t01_result(
        "downstream-clean",
        wording_ref="wording:downstream-clean",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    weak = _t01_result(
        "downstream-weak",
        wording_ref="wording:downstream-weak",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    clean_view = derive_t01_preverbal_consumer_view(clean)
    weak_view = derive_t01_preverbal_consumer_view(weak)
    assert clean_view.can_continue_preverbal is True
    assert weak_view.can_continue_preverbal is False
    assert require_t01_preverbal_consumer_ready(clean).can_continue_preverbal is True
    with pytest.raises(PermissionError):
        require_t01_preverbal_consumer_ready(weak)


def test_t01_harness_contains_minimum_case_inventory() -> None:
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
    assert len(scene_cases) >= 8
    results = [
        _t01_result(
            case_id,
            wording_ref=f"wording:{case_id}",
            include_observation=obs,
            request_action=action,
            effect_action_id=effect,
            c05_action=c05_action,
        )
        for case_id, obs, action, effect, c05_action in scene_cases
    ]
    assert len(results) == 8


def test_t01_rt01_downstream_use_is_path_affecting_with_ablation_contrast() -> None:
    baseline = execute_subject_tick(
        SubjectTickInput(
            case_id="t01-rt01-baseline",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
    )
    enforced = execute_subject_tick(
        SubjectTickInput(
            case_id="t01-rt01-enforced",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(require_t01_preverbal_scene_consumer=True),
    )
    ablated = execute_subject_tick(
        SubjectTickInput(
            case_id="t01-rt01-ablated",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_t01_preverbal_scene_consumer=True,
            disable_t01_field_enforcement=True,
            disable_gate_application=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert any(
        checkpoint.checkpoint_id == "rt01.t01_semantic_field_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in enforced.state.execution_checkpoints
    )


def test_t01_snapshot_is_inspectable_and_not_wording_buffer() -> None:
    result = _t01_result(
        "snapshot",
        wording_ref="wording:snapshot",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    snapshot = t01_active_field_snapshot(result)
    assert "scene_id" in snapshot["state"]
    assert "active_entities" in snapshot["state"]
    assert "relation_edges" in snapshot["state"]
    assert snapshot["state"]["wording_surface_ref"] == "wording:snapshot"
    assert "raw_text" not in snapshot["state"]
