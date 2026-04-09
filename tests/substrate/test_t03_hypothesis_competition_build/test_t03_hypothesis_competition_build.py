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
    build_t02_constrained_scene,
    derive_t02_preverbal_constraint_consumer_view,
)
from substrate.t03_hypothesis_competition import (
    T03CompetitionMode,
    T03ConvergenceStatus,
    build_t03_hypothesis_competition,
    derive_t03_competition_contract_view,
    derive_t03_competition_signature,
    derive_t03_preverbal_competition_consumer_view,
    require_t03_convergence_consumer_ready,
    require_t03_frontier_consumer_ready,
    t03_hypothesis_competition_snapshot,
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
        source_ref="world.sensor.t03",
        observed_at="2026-04-20T10:00:00+00:00",
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
            observed_at="2026-04-20T10:00:01+00:00",
            source_ref="world.effect.t03",
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
        source_lineage=("test.t03",),
    )
    world_entry = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.t03",),
    )
    s_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry,
        world_adapter_result=adapter_result,
        source_lineage=("test.t03",),
    )
    a_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        source_lineage=("test.t03",),
    )
    m_result = build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        c05_validity_action=c05_action,
        source_lineage=("test.t03",),
    )
    n_result = build_n_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        source_lineage=("test.t03",),
    )
    return tick_id, world_entry, s_result, a_result, m_result, n_result


def _t01_t02_bundle(
    case_id: str,
    *,
    wording_ref: str,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str,
    t02_mode: T02AssemblyMode = T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION,
    conflict_seed: bool = False,
):
    tick_id, world_entry, s_result, a_result, m_result, n_result = _upstream_bundle(
        case_id,
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
        c05_action=c05_action,
    )
    t01_result = build_t01_active_semantic_field(
        tick_id=tick_id,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_action,
        wording_surface_ref=wording_ref,
        source_lineage=("test.t03",),
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
    t02_result = build_t02_constrained_scene(
        tick_id=tick_id,
        t01_result=t01_result,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c05_validity_action=c05_action,
        assembly_mode=t02_mode,
        source_lineage=("test.t03",),
    )
    return tick_id, world_entry, s_result, a_result, m_result, n_result, t01_result, t02_result


def _t03_result(
    case_id: str,
    *,
    wording_ref: str,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_action: str = "reuse_without_revalidation",
    t02_mode: T02AssemblyMode = T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION,
    t03_mode: T03CompetitionMode = T03CompetitionMode.BOUNDED_COMPETITION,
    prior_state=None,
    conflict_seed: bool = False,
):
    (
        tick_id,
        world_entry,
        s_result,
        a_result,
        m_result,
        n_result,
        t01_result,
        t02_result,
    ) = _t01_t02_bundle(
        case_id,
        wording_ref=wording_ref,
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
        c05_action=c05_action,
        t02_mode=t02_mode,
        conflict_seed=conflict_seed,
    )
    t03_result = build_t03_hypothesis_competition(
        tick_id=tick_id,
        t01_result=t01_result,
        t02_result=t02_result,
        world_entry_result=world_entry,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c05_validity_action=c05_action,
        prior_state=prior_state,
        competition_mode=t03_mode,
        source_lineage=("test.t03",),
    )
    return t03_result, t01_result, t02_result


def _find_bounded_tie_result():
    tie_cases = (
        ("tie-1", True, True, None, "run_selective_revalidation"),
        ("tie-2", True, True, "__MATCHED__", "run_bounded_revalidation"),
        ("tie-3", True, False, None, "run_selective_revalidation"),
    )
    for case_id, include_obs, request_action, effect_id, c05_action in tie_cases:
        result, _, _ = _t03_result(
            case_id,
            wording_ref=f"wording:{case_id}",
            include_observation=include_obs,
            request_action=request_action,
            effect_action_id=effect_id,
            c05_action=c05_action,
            t03_mode=T03CompetitionMode.BOUNDED_COMPETITION,
            conflict_seed=True,
        )
        if result.state.bounded_plurality and result.state.honest_nonconvergence:
            return result
    return None


def test_t03_ordinary_competition_state_materializes() -> None:
    result, _, _ = _t03_result(
        "ordinary",
        wording_ref="wording:t03-ordinary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    assert result.state.competition_id.startswith("t03-competition:")
    assert result.state.candidates
    assert result.state.publication_frontier.competitive_neighborhood
    assert result.gate.restrictions


def test_t03_ordinary_bounded_tie_can_be_preserved_without_forced_winner() -> None:
    tie_result = _find_bounded_tie_result()
    assert tie_result is not None
    assert tie_result.state.convergence_status is T03ConvergenceStatus.HONEST_NONCONVERGENCE
    assert tie_result.state.bounded_plurality is True
    assert tie_result.state.current_leader_hypothesis_id is None


def test_t03_invariants_candidate_statuses_and_frontier_consistency_hold() -> None:
    result, _, _ = _t03_result(
        "invariants",
        wording_ref="wording:t03-invariants",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    leading = {
        item.hypothesis_id
        for item in result.state.candidates
        if item.status.value == "leading"
    }
    eliminated = set(result.state.eliminated_hypothesis_ids)
    blocked = set(result.state.blocked_hypothesis_ids)
    assert leading.isdisjoint(eliminated)
    assert leading.isdisjoint(blocked)
    if result.state.publication_frontier.current_leader is not None:
        assert (
            result.state.publication_frontier.current_leader
            in result.state.publication_frontier.competitive_neighborhood
        )


def test_t03_regression_existing_t01_t02_contract_surfaces_stay_present() -> None:
    result, _, t02_result = _t03_result(
        "regression",
        wording_ref="wording:t03-regression",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    t02_view = derive_t02_preverbal_constraint_consumer_view(t02_result)
    assert t02_view.raw_vs_propagated_distinct is True
    assert result.scope_marker.t04_implemented is False
    assert result.scope_marker.o01_implemented is False


def test_t03_metamorphic_paraphrase_groups_preserve_competition_signature_shape() -> None:
    groups = (
        ("pg1a", "wording:agent places cup on table", "pg1b", "wording:cup is placed on table by agent"),
        ("pg2a", "wording:signal shifts after action", "pg2b", "wording:after acting signal changes"),
        ("pg3a", "wording:review remains required", "pg3b", "wording:memory still needs review"),
    )
    for left_id, left_wording, right_id, right_wording in groups:
        left, _, _ = _t03_result(
            left_id,
            wording_ref=left_wording,
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        )
        right, _, _ = _t03_result(
            right_id,
            wording_ref=right_wording,
            include_observation=True,
            request_action=True,
            effect_action_id="__MATCHED__",
        )
        assert derive_t03_competition_signature(left) == derive_t03_competition_signature(right)


def test_t03_metamorphic_authority_contrast_changes_competition_shape() -> None:
    strong, _, _ = _t03_result(
        "authority-strong",
        wording_ref="wording:t03-authority-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    weak, _, _ = _t03_result(
        "authority-weak",
        wording_ref="wording:t03-authority-contrast",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    assert strong.state.convergence_status != weak.state.convergence_status or (
        strong.state.current_leader_hypothesis_id != weak.state.current_leader_hypothesis_id
    )


def test_t03_metamorphic_delayed_support_can_reactivate_previous_candidate() -> None:
    prior, _, _ = _t03_result(
        "revival-prior",
        wording_ref="wording:t03-revival",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        t03_mode=T03CompetitionMode.CONVENIENCE_BIAS_ABLATION,
    )
    revived, _, _ = _t03_result(
        "revival-next",
        wording_ref="wording:t03-revival",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        prior_state=prior.state,
    )
    assert revived.state.reactivated_hypothesis_ids


def test_t03_ablation_modes_emit_machine_readable_shortcuts() -> None:
    greedy, _, _ = _t03_result(
        "abl-greedy",
        wording_ref="wording:t03-abl-greedy",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        t03_mode=T03CompetitionMode.GREEDY_ARGMAX_ABLATION,
    )
    hidden, _, _ = _t03_result(
        "abl-hidden",
        wording_ref="wording:t03-abl-hidden",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        t03_mode=T03CompetitionMode.HIDDEN_TEXT_RERANKING_ABLATION,
    )
    convenience, _, _ = _t03_result(
        "abl-convenience",
        wording_ref="wording:t03-abl-convenience",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        t03_mode=T03CompetitionMode.CONVENIENCE_BIAS_ABLATION,
    )
    authority_disable, _, _ = _t03_result(
        "abl-authority-disable",
        wording_ref="wording:t03-abl-authority-disable",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        t03_mode=T03CompetitionMode.AUTHORITY_WEIGHT_DISABLE_ABLATION,
    )
    assert "greedy_winner_take_all_argmax" in greedy.gate.forbidden_shortcuts
    assert "hidden_text_reranking" in hidden.gate.forbidden_shortcuts
    assert "convenience_biased_candidate_selection" in convenience.gate.forbidden_shortcuts
    assert "authority_weight_disabled" in authority_disable.gate.forbidden_shortcuts


def test_t03_ablation_no_revival_and_forced_single_winner_are_falsifiable() -> None:
    tie_result = _find_bounded_tie_result()
    assert tie_result is not None
    forced, _, _ = _t03_result(
        "abl-forced-single",
        wording_ref="wording:t03-abl-forced-single",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        t03_mode=T03CompetitionMode.FORCED_SINGLE_WINNER_ABLATION,
        conflict_seed=True,
    )
    prior, _, _ = _t03_result(
        "abl-no-revival-prior",
        wording_ref="wording:t03-no-revival",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        t03_mode=T03CompetitionMode.CONVENIENCE_BIAS_ABLATION,
    )
    no_revival, _, _ = _t03_result(
        "abl-no-revival-next",
        wording_ref="wording:t03-no-revival",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        prior_state=prior.state,
        t03_mode=T03CompetitionMode.NO_REVIVAL_ABLATION,
    )
    assert "forced_single_winner_under_ambiguity" in forced.gate.forbidden_shortcuts
    assert "no_revival_competition" in no_revival.gate.forbidden_shortcuts


def test_t03_matrix_covers_strong_provisional_tie_nonconvergence_and_revival() -> None:
    strong, _, _ = _t03_result(
        "matrix-strong",
        wording_ref="wording:t03-matrix-strong",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    provisional, _, _ = _t03_result(
        "matrix-provisional",
        wording_ref="wording:t03-matrix-provisional",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c05_action="run_selective_revalidation",
    )
    tie = _find_bounded_tie_result()
    assert tie is not None
    prior, _, _ = _t03_result(
        "matrix-revival-prior",
        wording_ref="wording:t03-matrix-revival",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        t03_mode=T03CompetitionMode.CONVENIENCE_BIAS_ABLATION,
    )
    revival, _, _ = _t03_result(
        "matrix-revival-next",
        wording_ref="wording:t03-matrix-revival",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        prior_state=prior.state,
    )
    statuses = {
        strong.state.convergence_status.value,
        provisional.state.convergence_status.value,
        tie.state.convergence_status.value,
        revival.state.convergence_status.value,
    }
    assert "stable_local_convergence" in statuses or "provisional_convergence" in statuses
    assert "honest_nonconvergence" in statuses
    assert revival.state.reactivated_hypothesis_ids


def test_t03_role_boundary_does_not_invent_evidence_or_emit_planner_semantics() -> None:
    result, _, t02_result = _t03_result(
        "role-boundary",
        wording_ref="wording:t03-role-boundary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    t02_binding_ids = {item.binding_id for item in t02_result.state.relation_bindings}
    for candidate in result.state.candidates:
        assert set(candidate.support_sources).issubset(t02_binding_ids)
    assert "planner" not in result.reason
    assert result.scope_marker.t04_implemented is False
    assert result.scope_marker.o01_implemented is False
    assert result.scope_marker.o02_implemented is False
    assert result.scope_marker.o03_implemented is False


def test_t03_adversarial_balanced_ambiguity_does_not_force_single_winner() -> None:
    tie_result = _find_bounded_tie_result()
    assert tie_result is not None
    assert tie_result.state.current_leader_hypothesis_id is None
    assert tie_result.state.honest_nonconvergence is True
    assert tie_result.state.bounded_plurality is True


def test_t03_adversarial_convenience_and_low_authority_shortcuts_do_not_look_lawful() -> None:
    result, _, _ = _t03_result(
        "adv-convenience-low-authority",
        wording_ref="wording:cleanly-verbalized-but-weak",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        t03_mode=T03CompetitionMode.CONVENIENCE_BIAS_ABLATION,
    )
    assert (
        "convenience_biased_candidate_selection" in result.gate.forbidden_shortcuts
        or "low_authority_smooth_domination" in result.gate.forbidden_shortcuts
    )


def test_t03_downstream_preverbal_consumer_is_load_bearing() -> None:
    strong, _, _ = _t03_result(
        "downstream-strong",
        wording_ref="wording:t03-downstream",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    weak, _, _ = _t03_result(
        "downstream-weak",
        wording_ref="wording:t03-downstream",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    strong_view = derive_t03_preverbal_competition_consumer_view(strong)
    weak_view = derive_t03_preverbal_competition_consumer_view(weak)
    assert strong_view.frontier_consumer_ready is True
    assert weak_view.can_consume_convergence is False
    assert require_t03_frontier_consumer_ready(strong).frontier_consumer_ready is True
    with pytest.raises(PermissionError):
        require_t03_convergence_consumer_ready(weak)


def test_t03_rt01_convergence_consumer_requirement_is_path_affecting() -> None:
    baseline = execute_subject_tick(
        SubjectTickInput(
            case_id="t03-rt01-baseline",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            world_adapter_input=WorldAdapterInput(
                adapter_presence=False,
                adapter_available=False,
            ),
        ),
    )
    required = execute_subject_tick(
        SubjectTickInput(
            case_id="t03-rt01-required",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_t03_convergence_consumer=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=False,
                adapter_available=False,
            ),
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.t03_hypothesis_competition_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.state.execution_checkpoints
    )


def test_t03_rt01_nonconvergence_preservation_requirement_is_path_affecting() -> None:
    baseline = execute_subject_tick(
        SubjectTickInput(
            case_id="t03-rt01-nonconv-baseline",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
    )
    required = execute_subject_tick(
        SubjectTickInput(
            case_id="t03-rt01-nonconv-required",
            energy=66.0,
            cognitive=44.0,
            safety=74.0,
            unresolved_preference=False,
        ),
        context=SubjectTickContext(
            require_t03_nonconvergence_preservation=True,
            t03_competition_mode="greedy_argmax_ablation",
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert required.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.t03_hypothesis_competition_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in required.state.execution_checkpoints
    )


def test_t03_raw_t02_surface_cannot_masquerade_as_convergence_output() -> None:
    t03_result, _, t02_result = _t03_result(
        "downstream-contrast",
        wording_ref="wording:t03-downstream-contrast",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
    )
    t02_view = derive_t02_preverbal_constraint_consumer_view(t02_result)
    t03_view = derive_t03_preverbal_competition_consumer_view(t03_result)
    assert t02_view.can_consume_constrained_scene in {True, False}
    assert t03_view.can_consume_convergence is False


def test_t03_harness_inventory_meets_minimum_case_requirements() -> None:
    competition_cases = (
        ("h1", True, True, "__MATCHED__", "reuse_without_revalidation"),
        ("h2", True, True, None, "run_selective_revalidation"),
        ("h3", True, False, None, "reuse_without_revalidation"),
        ("h4", False, False, None, "reuse_without_revalidation"),
        ("h5", True, True, "__MATCHED__", "run_bounded_revalidation"),
        ("h6", True, True, None, "suspend_until_revalidation_basis"),
        ("h7", False, True, None, "halt_reuse_and_rebuild_scope"),
        ("h8", True, True, "__MATCHED__", "reuse_without_revalidation"),
        ("h9", True, True, None, "run_selective_revalidation"),
        ("h10", True, True, "__MATCHED__", "reuse_without_revalidation"),
    )
    balanced_tie_cases = (
        ("tie-h1", True, True, None, "run_selective_revalidation"),
        ("tie-h2", True, True, "__MATCHED__", "run_bounded_revalidation"),
        ("tie-h3", True, False, None, "run_selective_revalidation"),
    )
    revival_cases = (
        ("rev-h1-prior", "rev-h1-next"),
        ("rev-h2-prior", "rev-h2-next"),
        ("rev-h3-prior", "rev-h3-next"),
    )
    authority_conflict_cases = (
        ("ac-h1", False, False, None, "reuse_without_revalidation"),
        ("ac-h2", False, True, None, "run_selective_revalidation"),
    )
    convenience_bias_cases = (
        ("cb-h1", "wording:clean-weak-1"),
        ("cb-h2", "wording:clean-weak-2"),
    )
    assert len(competition_cases) >= 10
    assert len(balanced_tie_cases) >= 3
    assert len(revival_cases) >= 3
    assert len(authority_conflict_cases) >= 2
    assert len(convenience_bias_cases) >= 2

    results = [
        _t03_result(
            case_id,
            wording_ref=f"wording:{case_id}",
            include_observation=obs,
            request_action=action,
            effect_action_id=effect,
            c05_action=c05_action,
        )[0]
        for case_id, obs, action, effect, c05_action in competition_cases
    ]
    consumer_reads = [derive_t03_preverbal_competition_consumer_view(item) for item in results]
    assert len(results) == 10
    assert len(consumer_reads) == 10


def test_t03_snapshot_and_contract_view_are_inspectable() -> None:
    result, _, _ = _t03_result(
        "snapshot",
        wording_ref="wording:t03-snapshot",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
    )
    snapshot = t03_hypothesis_competition_snapshot(result)
    view = derive_t03_competition_contract_view(result)
    assert snapshot["state"]["competition_id"] == result.state.competition_id
    assert snapshot["state"]["publication_frontier"]["stability_status"] == result.state.convergence_status.value
    assert view.scope == "rt01_contour_only"
    assert view.scope_t03_first_slice_only is True
    assert view.scope_t04_implemented is False
    assert view.scope_o01_implemented is False
