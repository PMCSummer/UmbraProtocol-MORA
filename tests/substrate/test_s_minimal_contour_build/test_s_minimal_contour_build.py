from __future__ import annotations

from substrate.self_contour import (
    AttributionClass,
    build_s_minimal_contour,
    derive_s_minimal_contour_contract_view,
    s_minimal_contour_snapshot,
)
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    SubjectTickOutcome,
    execute_subject_tick,
    subject_tick_result_to_payload,
)
from substrate.world_adapter import (
    WorldAdapterInput,
    build_world_effect_packet,
    build_world_observation_packet,
    run_world_adapter_cycle,
)
from substrate.world_entry_contract import build_world_entry_contract


def _tick_input(case_id: str) -> SubjectTickInput:
    return SubjectTickInput(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
    )


def _observation(case_id: str):
    return build_world_observation_packet(
        observation_id=f"obs-{case_id}",
        source_ref="world.sensor.sprint8b",
        observed_at="2026-04-09T12:00:00+00:00",
        payload_ref=f"payload:{case_id}",
    )


def _world_entry_result(case_id: str, *, request_action: bool, matched_effect: bool | None):
    tick_id = f"tick-{case_id}"
    effect_packet = None
    if matched_effect is True:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id=f"world-action-{tick_id}",
            observed_at="2026-04-09T12:00:01+00:00",
            source_ref="world.effect.sprint8b",
            success=True,
        )
    elif matched_effect is False:
        effect_packet = build_world_effect_packet(
            effect_id=f"eff-{case_id}",
            action_id="wrong-action-id",
            observed_at="2026-04-09T12:00:01+00:00",
            source_ref="world.effect.sprint8b",
            success=True,
        )
    adapter_result = run_world_adapter_cycle(
        tick_id=tick_id,
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=_observation(case_id),
            effect_packet=effect_packet,
        ),
        request_action_candidate=request_action,
        source_lineage=("test.s-minimal",),
    )
    return build_world_entry_contract(
        tick_id=tick_id,
        world_adapter_result=adapter_result,
        source_lineage=("test.s-minimal",),
    ), adapter_result


def test_s_minimal_contour_materializes_typed_contract_and_scope() -> None:
    world_entry, adapter = _world_entry_result(
        "s8b-typed",
        request_action=True,
        matched_effect=True,
    )
    result = build_s_minimal_contour(
        tick_id="tick-s8b-typed",
        world_entry_result=world_entry,
        world_adapter_result=adapter,
        require_self_side_claim=True,
        require_self_controlled_transition_claim=True,
        source_lineage=("test.s-minimal",),
    )
    view = derive_s_minimal_contour_contract_view(result)
    snapshot = s_minimal_contour_snapshot(result)
    assert result.state.boundary_state_id.startswith("s-boundary:")
    assert result.state.attribution_class == AttributionClass.SELF_CONTROLLED_TRANSITION_CLAIM
    assert result.gate.self_controlled_transition_claim_allowed is True
    assert result.admission.admission_ready_for_s01 is True
    assert result.admission.readiness_blockers == ()
    assert view.scope == "rt01_contour_only"
    assert view.scope_rt01_contour_only is True
    assert view.scope_s_minimal_only is True
    assert view.scope_s01_implemented is False
    assert view.scope_s_line_implemented is False
    assert view.scope_minimal_contour_only is True
    assert view.scope_s01_s05_implemented is False
    assert view.scope_full_self_model_implemented is False
    assert view.scope_repo_wide_adoption is False
    assert snapshot["scope_marker"]["scope"] == "rt01_contour_only"
    assert snapshot["scope_marker"]["rt01_contour_only"] is True
    assert snapshot["scope_marker"]["s_minimal_only"] is True
    assert snapshot["scope_marker"]["s01_implemented"] is False
    assert snapshot["scope_marker"]["s_line_implemented"] is False
    assert snapshot["scope_marker"]["minimal_contour_only"] is True
    assert snapshot["scope_marker"]["s01_s05_implemented"] is False


def test_s_minimal_forbidden_shortcuts_machine_readable_without_self_basis() -> None:
    adapter_result = run_world_adapter_cycle(
        tick_id="tick-s8b-no-self-basis",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
            observation_packet=_observation("s8b-no-self-basis"),
        ),
        request_action_candidate=False,
    )
    world_entry = build_world_entry_contract(
        tick_id="tick-s8b-no-self-basis",
        world_adapter_result=adapter_result,
    )
    result = build_s_minimal_contour(
        tick_id="tick-s8b-no-self-basis",
        world_entry_result=world_entry,
        world_adapter_result=adapter_result,
        require_self_side_claim=True,
    )
    assert result.gate.self_owned_state_claim_allowed is False
    assert result.gate.no_safe_self_claim is True
    assert "self_claim_without_self_basis" in result.gate.forbidden_shortcuts
    assert "ownership_claim_without_action_or_boundary_basis" in result.gate.forbidden_shortcuts
    assert result.admission.admission_ready_for_s01 is False
    assert "self_attribution_basis_insufficient" in result.admission.readiness_blockers
    assert "no_safe_self_basis" in result.admission.readiness_blockers


def test_s_minimal_mixed_attribution_forbidden_when_both_sides_requested() -> None:
    world_entry, adapter = _world_entry_result(
        "s8b-mixed",
        request_action=True,
        matched_effect=None,
    )
    result = build_s_minimal_contour(
        tick_id="tick-s8b-mixed",
        world_entry_result=world_entry,
        world_adapter_result=adapter,
        require_self_side_claim=True,
        require_world_side_claim=True,
    )
    assert result.state.internal_vs_external_source_status.value == "mixed"
    assert "mixed_attribution_without_uncertainty_marking" in result.gate.forbidden_shortcuts


def test_s_minimal_admission_not_ready_when_contour_exists_but_basis_underconstrained() -> None:
    adapter_result = run_world_adapter_cycle(
        tick_id="tick-s8b-underconstrained-admission",
        execution_mode="continue_stream",
        adapter_input=WorldAdapterInput(
            adapter_presence=True,
            adapter_available=True,
        ),
        request_action_candidate=False,
    )
    world_entry = build_world_entry_contract(
        tick_id="tick-s8b-underconstrained-admission",
        world_adapter_result=adapter_result,
    )
    result = build_s_minimal_contour(
        tick_id="tick-s8b-underconstrained-admission",
        world_entry_result=world_entry,
        world_adapter_result=adapter_result,
    )
    assert result.admission.s_minimal_contour_materialized is True
    assert result.admission.admission_ready_for_s01 is False
    assert result.admission.attribution_underconstrained is True
    assert "attribution_underconstrained" in result.admission.readiness_blockers
    assert "no_safe_world_basis" in result.admission.readiness_blockers


def test_rt01_s_minimal_self_side_requirement_is_path_affecting() -> None:
    baseline = execute_subject_tick(
        _tick_input("s8b-self-side-baseline"),
        context=SubjectTickContext(
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-self-side-baseline"),
            ),
        ),
    )
    enforced = execute_subject_tick(
        _tick_input("s8b-self-side-enforced"),
        context=SubjectTickContext(
            require_self_side_claim=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-self-side-enforced"),
            ),
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.s_minimal_contour_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in enforced.state.execution_checkpoints
    )


def test_rt01_s_minimal_self_control_claim_distinguishes_matched_vs_mismatched_effect() -> None:
    matched = execute_subject_tick(
        _tick_input("s8b-control-matched"),
        context=SubjectTickContext(
            require_self_controlled_transition_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-control-matched"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-s8b-control-matched",
                    action_id="world-action-subject-tick-s8b-control-matched-1",
                    observed_at="2026-04-09T12:01:01+00:00",
                    source_ref="world.effect.sprint8b",
                    success=True,
                ),
            ),
        ),
    )
    mismatched = execute_subject_tick(
        _tick_input("s8b-control-mismatch"),
        context=SubjectTickContext(
            require_self_controlled_transition_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-control-mismatch"),
                effect_packet=build_world_effect_packet(
                    effect_id="eff-s8b-control-mismatch",
                    action_id="wrong-action-id",
                    observed_at="2026-04-09T12:01:11+00:00",
                    source_ref="world.effect.sprint8b",
                    success=True,
                ),
            ),
        ),
    )
    assert matched.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert mismatched.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert matched.state.s_attribution_class == "self_controlled_transition_claim"
    assert mismatched.state.s_attribution_class != "self_controlled_transition_claim"


def test_rt01_s_minimal_world_side_requirement_can_force_no_safe_world_claim_detour() -> None:
    result = execute_subject_tick(
        _tick_input("s8b-world-side-enforced"),
        context=SubjectTickContext(
            require_world_side_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
            ),
        ),
    )
    assert result.state.s_no_safe_world_claim is True
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_rt01_strict_mixed_ambiguity_guard_triggers_revalidate_under_claim_pressure() -> None:
    result = execute_subject_tick(
        _tick_input("s8b-mixed-guard-pressure"),
        context=SubjectTickContext(
            require_self_side_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-mixed-guard-pressure"),
            ),
        ),
    )
    assert result.state.s_source_status == "mixed"
    assert "mixed_attribution_without_uncertainty_marking" in result.state.s_forbidden_shortcuts
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_rt01_mixed_guard_can_be_ablated_explicitly_without_phase_creep() -> None:
    strict = execute_subject_tick(
        _tick_input("s8b-mixed-guard-strict"),
        context=SubjectTickContext(
            require_self_side_claim=True,
            emit_world_action_candidate=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-mixed-guard-strict"),
            ),
        ),
    )
    relaxed = execute_subject_tick(
        _tick_input("s8b-mixed-guard-relaxed"),
        context=SubjectTickContext(
            require_self_side_claim=True,
            emit_world_action_candidate=True,
            strict_mixed_attribution_guard=False,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-mixed-guard-relaxed"),
            ),
        ),
    )
    assert strict.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert relaxed.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_rt01_s_minimal_ablation_contrast_proves_enforcement_causal_effect() -> None:
    enforced = execute_subject_tick(
        _tick_input("s8b-ablation-enforced"),
        context=SubjectTickContext(
            require_self_side_claim=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-ablation-enforced"),
            ),
        ),
    )
    ablated = execute_subject_tick(
        _tick_input("s8b-ablation-disabled"),
        context=SubjectTickContext(
            require_self_side_claim=True,
            disable_s_minimal_enforcement=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-ablation-disabled"),
            ),
        ),
    )
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert ablated.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_s_minimal_contour_does_not_break_existing_world_seam_contract() -> None:
    result = execute_subject_tick(
        _tick_input("s8b-world-seam-regression"),
        context=SubjectTickContext(
            require_world_grounded_transition=True,
            world_adapter_input=WorldAdapterInput(
                adapter_presence=True,
                adapter_available=True,
                observation_packet=_observation("s8b-world-seam-regression"),
            ),
        ),
    )
    assert result.state.world_entry_episode_id.startswith("world-episode:")
    assert result.state.world_entry_scope == "rt01_contour_only"
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_subject_tick_snapshot_exposes_s_minimal_scope_and_contract_fields() -> None:
    result = execute_subject_tick(_tick_input("s8b-snapshot"))
    payload = subject_tick_result_to_payload(result)
    state = payload["state"]
    assert state["s_boundary_state_id"].startswith("s-boundary:")
    assert state["s_scope"] == "rt01_contour_only"
    assert state["s_scope_rt01_contour_only"] is True
    assert state["s_scope_s_minimal_only"] is True
    assert state["s_scope_s01_implemented"] is False
    assert state["s_scope_s_line_implemented"] is False
    assert state["s_scope_minimal_contour_only"] is True
    assert state["s_scope_s01_s05_implemented"] is False
    assert state["s_scope_full_self_model_implemented"] is False
    assert state["s_scope_repo_wide_adoption"] is False
    assert isinstance(state["s_readiness_blockers"], tuple)
    assert payload["self_contour_result"]["scope_marker"]["scope"] == "rt01_contour_only"
    assert payload["self_contour_result"]["scope_marker"]["rt01_contour_only"] is True
    assert payload["self_contour_result"]["scope_marker"]["s_minimal_only"] is True
    assert payload["self_contour_result"]["scope_marker"]["s01_implemented"] is False
    assert payload["self_contour_result"]["scope_marker"]["s_line_implemented"] is False
    assert payload["self_contour_result"]["scope_marker"]["s01_s05_implemented"] is False


def test_rt01_consumes_s_minimal_result_without_becoming_self_semantics_owner() -> None:
    result = execute_subject_tick(_tick_input("s8b-boundary-role"))
    assert result.no_planner_orchestrator_dependency is True
    assert result.no_phase_semantics_override_dependency is True
    assert result.state.s_attribution_class == result.self_contour_result.state.attribution_class.value
    assert any(
        checkpoint.checkpoint_id == "rt01.s_minimal_contour_checkpoint"
        for checkpoint in result.state.execution_checkpoints
    )
