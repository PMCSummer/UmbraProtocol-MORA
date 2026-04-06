from __future__ import annotations

from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickOutcome,
    choose_runtime_execution_outcome,
    derive_subject_tick_contract_view,
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
