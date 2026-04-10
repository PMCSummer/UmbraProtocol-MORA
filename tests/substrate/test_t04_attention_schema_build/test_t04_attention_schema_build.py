from __future__ import annotations

from substrate.a_line_normalization import build_a_line_normalization
from substrate.m_minimal import build_m_minimal
from substrate.n_minimal import build_n_minimal
from substrate.self_contour import build_s_minimal_contour
from substrate.t01_semantic_field import build_t01_active_semantic_field
from substrate.t02_relation_binding import build_t02_constrained_scene
from substrate.t03_hypothesis_competition import (
    T03CompetitionMode,
    build_t03_hypothesis_competition,
)
from substrate.t04_attention_schema import (
    T04AttentionOwner,
    T04ReportabilityStatus,
    build_t04_attention_schema,
    derive_t04_attention_schema_contract_view,
    derive_t04_preverbal_focus_consumer_view,
    require_t04_focus_ownership_consumer_ready,
    require_t04_reportable_focus_consumer_ready,
    t04_attention_schema_snapshot,
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
        source_ref="world.sensor.t04",
        observed_at="2026-04-21T10:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _build_t03_result(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c05_validity_action: str,
    t03_mode: T03CompetitionMode = T03CompetitionMode.BOUNDED_COMPETITION,
):
    tick_id = f"tick-{case_id}"
    if effect_action_id == "__MATCHED__":
        effect_action_id = f"world-action-{tick_id}"
    effect_packet = (
        None
        if effect_action_id is None
        else build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=effect_action_id,
            observed_at="2026-04-21T10:00:01+00:00",
            source_ref="world.effect.t04",
            success=True,
        )
    )
    world_adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=include_observation,
            adapter_available=include_observation,
            observation_packet=_observation(case_id) if include_observation else None,
            effect_packet=effect_packet,
        ),
        request_action_candidate=request_action,
        source_lineage=("test.t04",),
    )
    world_entry_result = build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=world_adapter_result,
        source_lineage=("test.t04",),
    )
    s_result = build_s_minimal_contour(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        world_adapter_result=world_adapter_result,
        source_lineage=("test.t04",),
    )
    a_result = build_a_line_normalization(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_validity_action,
        source_lineage=("test.t04",),
    )
    m_result = build_m_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        a_line_result=a_result,
        c05_validity_action=c05_validity_action,
        source_lineage=("test.t04",),
    )
    n_result = build_n_minimal(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        source_lineage=("test.t04",),
    )
    t01_result = build_t01_active_semantic_field(
        tick_id=tick_id,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action=c05_validity_action,
        wording_surface_ref=f"wording:{case_id}",
        source_lineage=("test.t04",),
    )
    t02_result = build_t02_constrained_scene(
        tick_id=tick_id,
        t01_result=t01_result,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c05_validity_action=c05_validity_action,
        source_lineage=("test.t04",),
    )
    return build_t03_hypothesis_competition(
        tick_id=tick_id,
        t01_result=t01_result,
        t02_result=t02_result,
        world_entry_result=world_entry_result,
        s_minimal_result=s_result,
        a_line_result=a_result,
        m_minimal_result=m_result,
        n_minimal_result=n_result,
        c05_validity_action=c05_validity_action,
        competition_mode=t03_mode,
        source_lineage=("test.t04",),
    )


def _build_t04_result(
    case_id: str,
    *,
    include_observation: bool,
    request_action: bool,
    effect_action_id: str | None,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    t03_mode: T03CompetitionMode = T03CompetitionMode.BOUNDED_COMPETITION,
):
    t03_result = _build_t03_result(
        case_id,
        include_observation=include_observation,
        request_action=request_action,
        effect_action_id=effect_action_id,
        c05_validity_action=c05_validity_action,
        t03_mode=t03_mode,
    )
    return build_t04_attention_schema(
        tick_id=f"tick-{case_id}",
        t03_result=t03_result,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        source_lineage=("test.t04",),
    )


def test_t04_ordinary_typed_attention_schema_state_materializes() -> None:
    result = _build_t04_result(
        "ordinary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
    )
    assert result.state.schema_id.startswith("t04-attention-schema:")
    assert isinstance(result.state.focus_targets, tuple)
    assert isinstance(result.state.peripheral_targets, tuple)
    assert result.gate.restrictions


def test_t04_contrast_same_t03_but_different_control_conditions_changes_owner() -> None:
    t03_result = _build_t03_result(
        "owner-contrast",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c05_validity_action="reuse_without_revalidation",
    )
    self_guided = build_t04_attention_schema(
        tick_id="tick-owner-contrast-self",
        t03_result=t03_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
        source_lineage=("test.t04",),
    )
    validity_guarded = build_t04_attention_schema(
        tick_id="tick-owner-contrast-validity",
        t03_result=t03_result,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="run_selective_revalidation",
        source_lineage=("test.t04",),
    )
    assert self_guided.state.attention_owner != validity_guarded.state.attention_owner
    assert self_guided.state.focus_targets == validity_guarded.state.focus_targets


def test_t04_adversarial_highest_salience_does_not_auto_become_self_guided_owner() -> None:
    result = _build_t04_result(
        "owner-adversarial",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="run_selective_revalidation",
    )
    assert result.state.focus_targets
    assert result.state.attention_owner is T04AttentionOwner.VALIDITY_GUARDED


def test_t04_peripheral_preservation_under_competing_t03_frontier() -> None:
    result = _build_t04_result(
        "peripheral-preservation",
        include_observation=True,
        request_action=True,
        effect_action_id=None,
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="run_selective_revalidation",
        t03_mode=T03CompetitionMode.BOUNDED_COMPETITION,
    )
    assert result.state.peripheral_targets
    assert result.gate.peripheral_preservation_ready is True


def test_t04_reportability_is_not_overstated_when_stability_is_weak() -> None:
    result = _build_t04_result(
        "reportability",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        c04_execution_mode_claim="monitor_only",
        c05_validity_action="run_bounded_revalidation",
    )
    assert result.state.stability_estimate <= 0.72
    assert result.state.reportability_status in {
        T04ReportabilityStatus.REPORTABLE_PROVISIONAL,
        T04ReportabilityStatus.NOT_REPORTABLE,
    }
    assert not (
        result.state.reportability_status is T04ReportabilityStatus.REPORTABLE_STABLE
        and result.state.stability_estimate < 0.72
    )


def test_t04_role_boundary_keeps_no_planner_no_final_closure_claim() -> None:
    result = _build_t04_result(
        "role-boundary",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
    )
    assert "planner" not in result.reason
    assert result.scope_marker.t04_first_slice_only is True
    assert result.scope_marker.o01_implemented is False
    assert result.scope_marker.o02_implemented is False
    assert result.scope_marker.o03_implemented is False


def test_t04_contract_view_and_snapshot_are_inspectable() -> None:
    result = _build_t04_result(
        "snapshot",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
    )
    view = derive_t04_attention_schema_contract_view(result)
    snapshot = t04_attention_schema_snapshot(result)
    consumer_view = derive_t04_preverbal_focus_consumer_view(result)
    assert view.schema_id == result.state.schema_id
    assert snapshot["state"]["schema_id"] == result.state.schema_id
    assert snapshot["scope_marker"]["scope"] == "rt01_contour_only"
    assert view.scope_t04_first_slice_only is True
    assert view.scope_o01_implemented is False
    assert view.scope_o02_implemented is False
    assert view.scope_o03_implemented is False
    assert view.scope_repo_wide_adoption is False
    assert isinstance(consumer_view.restrictions, tuple)


def test_t04_consumer_requirements_are_falsifiable() -> None:
    strong = _build_t04_result(
        "consumer-strong",
        include_observation=True,
        request_action=True,
        effect_action_id="__MATCHED__",
        c04_execution_mode_claim="continue_stream",
        c05_validity_action="reuse_without_revalidation",
    )
    weak = _build_t04_result(
        "consumer-weak",
        include_observation=False,
        request_action=False,
        effect_action_id=None,
        c04_execution_mode_claim="monitor_only",
        c05_validity_action="run_bounded_revalidation",
    )
    assert require_t04_focus_ownership_consumer_ready(strong).can_consume_focus_ownership is True
    if not weak.gate.reportable_focus_consumer_ready:
        try:
            require_t04_reportable_focus_consumer_ready(weak)
            raised = False
        except PermissionError:
            raised = True
        assert raised is True
