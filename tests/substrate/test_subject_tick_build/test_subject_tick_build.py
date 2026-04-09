from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickOutcome,
    SubjectTickRoleMapSource,
    choose_runtime_execution_outcome,
    derive_subject_tick_contract_view,
    require_subject_tick_bounded_n_scope,
    require_subject_tick_strong_narrative_commitment,
)
from tests.substrate.subject_tick_testkit import build_subject_tick


def _result(case_id: str, *, context: SubjectTickContext | None = None, unresolved: bool = False):
    return build_subject_tick(
        case_id=case_id,
        energy=14.0 if unresolved else 66.0,
        cognitive=95.0 if unresolved else 44.0,
        safety=34.0 if unresolved else 74.0,
        unresolved_preference=unresolved,
        context=context,
    )


def test_subject_tick_generates_typed_state_with_fixed_order() -> None:
    result = _result("rt-build-order", unresolved=True)
    phases = tuple(step.phase_id for step in result.state.downstream_step_results)
    assert phases == ("R", "C01", "C02", "C03", "C04", "C05")
    assert result.state.tick_id
    assert result.state.c04_selected_mode
    assert result.state.c05_validity_action
    assert result.telemetry.phase_order == phases


def test_subject_tick_basic_continue_path() -> None:
    result = _result("rt-continue")
    assert result.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert choose_runtime_execution_outcome(result) == "continue"


def test_subject_tick_basic_revalidate_path_from_c05() -> None:
    result = _result(
        "rt-revalidate",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert choose_runtime_execution_outcome(result) == "revalidate"
    assert "revalidate" in result.state.active_execution_mode


def test_subject_tick_basic_halt_path_from_c05_legality_block() -> None:
    result = _result(
        "rt-halt",
        unresolved=True,
        context=SubjectTickContext(
            withdrawn_source_refs=(
                "c01.stream_kernel_from_r01_r02_r03_r04",
                "c02.tension_scheduler_from_c01_r01_r02_r03_r04",
                "c03.stream_diversification_from_c01_c02_r04",
                "c04.mode_arbitration_from_c01_c02_c03_r04",
            ),
        ),
    )
    assert result.state.final_execution_outcome == SubjectTickOutcome.HALT
    assert result.state.halt_reason == "c05_halt_reuse_and_rebuild_scope"
    assert choose_runtime_execution_outcome(result) == "halt"


def test_subject_tick_invariant_c05_restriction_cannot_be_silently_ignored() -> None:
    obeyed = _result(
        "rt-c05-obeyed",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    bypassed = _result(
        "rt-c05-bypassed",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            disable_c05_validity_enforcement=True,
            disable_gate_application=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert obeyed.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert bypassed.state.final_execution_outcome != SubjectTickOutcome.HALT
    assert obeyed.state.active_execution_mode != bypassed.state.active_execution_mode


def test_subject_tick_invariant_c04_selected_mode_is_load_bearing() -> None:
    result = _result("rt-c04-invariant", unresolved=True)
    assert result.state.c04_selected_mode
    assert result.state.active_execution_mode
    assert result.state.active_execution_mode in {
        "continue_stream",
        "run_revisit",
        "run_recovery",
        "probe_alternatives",
        "monitor_only",
        "prepare_output",
        "idle",
        "hold_safe_idle",
        "revalidate_mode_hold",
        "revalidate_revisit_basis",
        "revalidate_scope",
        "repair_branch_access",
        "repair_runtime_path",
        "halt_execution",
    }


def test_subject_tick_metamorphic_changed_c04_mode_changes_execution_stance() -> None:
    endogenous = _result("rt-mode-endo", unresolved=True)
    reactive = _result(
        "rt-mode-reactive",
        unresolved=True,
        context=SubjectTickContext(
            external_turn_present=True,
            allow_endogenous_tick=False,
        ),
    )
    assert endogenous.state.c04_selected_mode != reactive.state.c04_selected_mode
    assert endogenous.state.c04_execution_mode_claim != reactive.state.c04_execution_mode_claim
    assert endogenous.state.execution_stance.value == reactive.state.execution_stance.value == "repair_path"


def test_subject_tick_metamorphic_changed_c05_legality_changes_outcome() -> None:
    baseline = _result("rt-c05-legal", unresolved=True)
    restricted = _result(
        "rt-c05-restricted",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    assert baseline.state.final_execution_outcome != restricted.state.final_execution_outcome


def test_subject_tick_ablation_gate_bypass_changes_contour_behavior() -> None:
    enforced = _result(
        "rt-ablate-gate-enforced",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    ablated = _result(
        "rt-ablate-gate-disabled",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            disable_gate_application=True,
            disable_c05_validity_enforcement=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert ablated.state.final_execution_outcome != SubjectTickOutcome.HALT
    assert enforced.state.final_execution_outcome != ablated.state.final_execution_outcome


def test_subject_tick_ablation_ignoring_c04_output_collapses_execution_profile() -> None:
    obeyed = _result("rt-ablate-c04-obeyed", unresolved=True)
    ignored = _result(
        "rt-ablate-c04-ignored",
        unresolved=True,
        context=SubjectTickContext(disable_c04_mode_execution_binding=True),
    )
    assert any(
        checkpoint.checkpoint_id == "rt01.c04_mode_binding"
        and checkpoint.status.value == "allowed"
        for checkpoint in obeyed.state.execution_checkpoints
    )
    assert ignored.state.c04_execution_mode_claim != ignored.state.active_execution_mode
    assert any(
        checkpoint.checkpoint_id == "rt01.c04_mode_binding"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in ignored.state.execution_checkpoints
    )


def test_subject_tick_ablation_ignoring_c05_signal_allows_illegal_profile() -> None:
    enforced = _result(
        "rt-ablate-c05-enforced",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    ignored = _result(
        "rt-ablate-c05-ignored",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            disable_c05_validity_enforcement=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert enforced.state.active_execution_mode != ignored.state.active_execution_mode


def test_subject_tick_matrix_outcomes_are_bounded_and_cover_all_runtime_branches() -> None:
    continue_case = _result("rt-matrix-continue")
    repair_case = _result(
        "rt-matrix-repair",
        unresolved=True,
        context=SubjectTickContext(
            allow_endogenous_tick=False,
            external_turn_present=False,
        ),
    )
    revalidate_case = _result(
        "rt-matrix-revalidate",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    halt_case = _result(
        "rt-matrix-halt",
        unresolved=True,
        context=SubjectTickContext(
            withdrawn_source_refs=(
                "c01.stream_kernel_from_r01_r02_r03_r04",
                "c02.tension_scheduler_from_c01_r01_r02_r03_r04",
                "c03.stream_diversification_from_c01_c02_r04",
                "c04.mode_arbitration_from_c01_c02_c03_r04",
            ),
        ),
    )
    outcomes = {
        continue_case.state.final_execution_outcome,
        repair_case.state.final_execution_outcome,
        revalidate_case.state.final_execution_outcome,
        halt_case.state.final_execution_outcome,
    }
    assert outcomes == {
        SubjectTickOutcome.CONTINUE,
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
        SubjectTickOutcome.HALT,
    }


def test_subject_tick_role_boundary_remains_execution_only_not_semantic_reinterpreter() -> None:
    result = _result("rt-role-boundary", unresolved=True)
    view = derive_subject_tick_contract_view(result)
    assert view.requires_restrictions_read is True
    assert view.c04_authority_role == "arbitration"
    assert view.c05_authority_role == "invalidation"
    assert view.d01_authority_role == "observability_only"
    assert not hasattr(result.state, "tensions")
    assert not hasattr(result.state, "active_mode")
    assert result.no_planner_orchestrator_dependency is True
    assert result.no_phase_semantics_override_dependency is True


def test_subject_tick_adversarial_telemetry_claim_without_behavior_change_fails() -> None:
    unrestricted = _result("rt-adv-unrestricted", unresolved=True)
    restricted = _result(
        "rt-adv-restricted",
        unresolved=True,
        context=SubjectTickContext(dependency_trigger_hits=("trigger:mode_shift",)),
    )
    assert unrestricted.state.c05_validity_action != restricted.state.c05_validity_action
    assert unrestricted.state.active_execution_mode != restricted.state.active_execution_mode


def test_subject_tick_critical_gate_checkpoint_is_path_affecting_not_label_only() -> None:
    enforced = _result(
        "rt-gate-checkpoint-enforced",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    bypassed = _result(
        "rt-gate-checkpoint-bypassed",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            disable_c05_validity_enforcement=True,
            disable_gate_application=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert any(
        checkpoint.checkpoint_id == "rt01.c05_legality_checkpoint"
        and checkpoint.status.value in {"enforced_detour", "blocked"}
        for checkpoint in enforced.state.execution_checkpoints
    )
    assert enforced.state.execution_stance.value == "revalidate_path"
    assert enforced.state.active_execution_mode == "revalidate_scope"
    assert bypassed.state.execution_stance.value == "continue_path"
    assert enforced.state.active_execution_mode != bypassed.state.active_execution_mode


def test_subject_tick_matched_continue_vs_repair_have_distinct_execution_stances() -> None:
    continue_case = _result("rt-continue-stance", unresolved=False)
    repair_case = _result(
        "rt-repair-stance",
        unresolved=True,
        context=SubjectTickContext(
            allow_endogenous_tick=False,
            external_turn_present=False,
        ),
    )
    assert continue_case.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert repair_case.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert continue_case.state.execution_stance.value == "continue_path"
    assert repair_case.state.execution_stance.value == "repair_path"
    assert repair_case.state.active_execution_mode == "repair_runtime_path"


def test_subject_tick_role_boundary_c04_claim_consumed_without_reselection() -> None:
    obeyed = _result(
        "rt-c04-role-obeyed",
        unresolved=True,
        context=SubjectTickContext(
            disable_c05_validity_enforcement=True,
            disable_gate_application=True,
        ),
    )
    ignored = _result(
        "rt-c04-role-ignored",
        unresolved=True,
        context=SubjectTickContext(
            disable_c05_validity_enforcement=True,
            disable_gate_application=True,
            disable_c04_mode_execution_binding=True,
        ),
    )
    assert obeyed.state.c04_execution_mode_claim == obeyed.state.active_execution_mode
    assert ignored.state.c04_execution_mode_claim != ignored.state.active_execution_mode
    assert any(
        checkpoint.checkpoint_id == "rt01.c04_mode_binding"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in ignored.state.execution_checkpoints
    )


def test_subject_tick_role_boundary_c05_legality_enforced_without_semantic_reinterpretation() -> None:
    enforced = _result(
        "rt-c05-role-enforced",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    bypassed = _result(
        "rt-c05-role-bypassed",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            disable_c05_validity_enforcement=True,
            disable_gate_application=True,
            disable_downstream_obedience_enforcement=True,
        ),
    )
    assert enforced.state.c05_execution_action_claim in {
        "run_selective_revalidation",
        "run_bounded_revalidation",
        "suspend_until_revalidation_basis",
        "halt_reuse_and_rebuild_scope",
    }
    assert enforced.state.active_execution_mode == "revalidate_scope"
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert bypassed.state.final_execution_outcome == SubjectTickOutcome.CONTINUE


def test_subject_tick_adversarial_late_bound_falsifier_now_requires_checkpoint_detour() -> None:
    baseline = _result("rt-late-bound-baseline", unresolved=True)
    restricted = _result(
        "rt-late-bound-restricted",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert restricted.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert baseline.state.execution_stance.value == "repair_path"
    assert restricted.state.execution_stance.value == "revalidate_path"
    assert any(
        checkpoint.checkpoint_id == "rt01.outcome_resolution_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in restricted.state.execution_checkpoints
    )


def test_subject_tick_authority_roles_are_runtime_load_bearing_for_c05_enforcement() -> None:
    enforced = _result(
        "rt-authority-c05-enforced",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            phase_authority_roles={"C05": "invalidation"},
        ),
    )
    downgraded = _result(
        "rt-authority-c05-downgraded",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            phase_authority_roles={"C05": "computational"},
        ),
    )
    assert enforced.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE
    assert downgraded.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert any(
        checkpoint.checkpoint_id == "rt01.c05_legality_checkpoint"
        and checkpoint.status.value == "blocked"
        for checkpoint in downgraded.state.execution_checkpoints
    )


def test_subject_tick_explicit_injected_role_map_overrides_default_and_context_maps() -> None:
    injected = SubjectTickRoleMapSource(
        source_ref="test.injected_role_map",
        phase_authority_roles={"C05": "computational"},
        phase_computational_roles={"C05": "evaluator"},
        frontier_role_typed=True,
        map_wide_role_ready=False,
        role_frontier_only=True,
    )
    result = _result(
        "rt-injected-role-map-priority",
        unresolved=True,
        context=SubjectTickContext(
            dependency_trigger_hits=("trigger:mode_shift",),
            phase_authority_roles={"C05": "invalidation"},
            role_map_source=injected,
        ),
    )
    assert result.state.role_source_ref == "test.injected_role_map"
    assert result.state.c05_authority_role == "computational"
    assert result.state.final_execution_outcome == SubjectTickOutcome.REPAIR


def test_subject_tick_role_fallback_still_works_without_injected_role_map() -> None:
    result = _result("rt-default-role-map", unresolved=False)
    assert result.state.role_source_ref == "rt01.default_frontier_role_map"
    assert result.state.role_frontier_typed is True
    assert result.state.role_frontier_only is True
    assert result.state.role_map_ready is False


def test_subject_tick_role_readiness_summary_is_exposed_in_contract_view() -> None:
    injected = SubjectTickRoleMapSource(
        source_ref="test.frontier_only",
        phase_authority_roles={"C04": "arbitration", "C05": "invalidation", "D01": "observability_only", "F01": "observability_only", "R04": "gating", "RT01": "gating"},
        phase_computational_roles={"C04": "scheduler", "C05": "evaluator", "D01": "observability", "F01": "bridge_contract", "R04": "evaluator", "RT01": "execution_spine"},
        frontier_role_typed=True,
        map_wide_role_ready=False,
        role_frontier_only=True,
    )
    result = _result(
        "rt-role-readiness-contract",
        unresolved=False,
        context=SubjectTickContext(role_map_source=injected),
    )
    view = derive_subject_tick_contract_view(result)
    assert view.role_source_ref == "test.frontier_only"
    assert view.role_frontier_only is True
    assert view.role_map_ready is False
    assert view.role_frontier_typed is True


def test_subject_tick_observability_only_phase_does_not_gain_enforcement_authority() -> None:
    baseline = _result(
        "rt-authority-d01-observe",
        unresolved=False,
        context=SubjectTickContext(phase_authority_roles={"D01": "observability_only"}),
    )
    adversarial = _result(
        "rt-authority-d01-adversarial",
        unresolved=False,
        context=SubjectTickContext(phase_authority_roles={"D01": "gating"}),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert adversarial.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert adversarial.state.active_execution_mode == "repair_runtime_path"
    assert adversarial.state.execution_stance.value == "repair_path"
    assert any(
        checkpoint.checkpoint_id == "rt01.d01_observability_guard"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in adversarial.state.execution_checkpoints
    )


def test_subject_tick_f01_role_mismatch_forces_runtime_repair_detour() -> None:
    baseline = _result("rt-f01-baseline", unresolved=False)
    adversarial = _result(
        "rt-f01-adversarial",
        unresolved=False,
        context=SubjectTickContext(
            role_map_source=SubjectTickRoleMapSource(
                source_ref="test.f01_bad_role",
                phase_authority_roles={"F01": "gating"},
                frontier_role_typed=True,
                map_wide_role_ready=False,
                role_frontier_only=True,
            )
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert adversarial.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert adversarial.state.active_execution_mode == "repair_runtime_path"
    assert any(
        checkpoint.checkpoint_id == "rt01.authority_role_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in adversarial.state.execution_checkpoints
    )


def test_subject_tick_c04_role_mismatch_blocks_full_mode_binding_legitimacy() -> None:
    baseline = _result("rt-c04-role-baseline", unresolved=False)
    adversarial = _result(
        "rt-c04-role-adversarial",
        unresolved=False,
        context=SubjectTickContext(
            role_map_source=SubjectTickRoleMapSource(
                source_ref="test.c04_bad_role",
                phase_authority_roles={"C04": "computational"},
                frontier_role_typed=True,
                map_wide_role_ready=False,
                role_frontier_only=True,
            )
        ),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert adversarial.state.final_execution_outcome == SubjectTickOutcome.REPAIR
    assert adversarial.state.active_execution_mode == "repair_runtime_path"
    assert any(
        checkpoint.checkpoint_id == "rt01.c04_mode_binding"
        and checkpoint.status.value == "blocked"
        for checkpoint in adversarial.state.execution_checkpoints
    )


def test_subject_tick_n_minimal_safe_narrative_claim_requirement_is_path_affecting() -> None:
    baseline = _result("rt-n-minimal-baseline", unresolved=False)
    enforced = _result(
        "rt-n-minimal-enforced",
        unresolved=False,
        context=SubjectTickContext(require_narrative_safe_claim=True),
    )
    assert baseline.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert enforced.state.final_execution_outcome in {
        SubjectTickOutcome.REPAIR,
        SubjectTickOutcome.REVALIDATE,
    }
    assert any(
        checkpoint.checkpoint_id == "rt01.n_minimal_contour_checkpoint"
        and checkpoint.status.value == "enforced_detour"
        for checkpoint in enforced.state.execution_checkpoints
    )


def test_subject_tick_n_scope_validator_blocks_tampered_or_unsafe_strong_claim() -> None:
    result = _result("rt-n-scope-validator", unresolved=False)
    view = derive_subject_tick_contract_view(result)
    assert require_subject_tick_bounded_n_scope(view) is view
    with pytest.raises(PermissionError):
        require_subject_tick_strong_narrative_commitment(view)
    tampered = replace(view, n_scope_n_minimal_only=False)
    with pytest.raises(PermissionError):
        require_subject_tick_bounded_n_scope(tampered)
