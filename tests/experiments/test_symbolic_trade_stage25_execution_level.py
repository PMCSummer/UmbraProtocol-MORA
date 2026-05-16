from __future__ import annotations

from dataclasses import replace

import experiments.symbolic_trade.falsifiers as falsifier_module
from experiments.symbolic_trade.runner import run_stage25_reaction
from experiments.symbolic_trade.subject_reaction_probe import ExecutionSurfaceLevel


def _outcome_map(items) -> dict[str, bool]:
    return {item.name: item.passed for item in items}


def test_stage25_execution_surface_report_has_required_fields() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    surface = run.execution_surface
    assert surface.execution_level in {
        ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION,
        ExecutionSurfaceLevel.PARTIAL_SUBJECT_TICK_EXECUTION,
        ExecutionSurfaceLevel.OWNER_SURFACE_EXECUTION,
        ExecutionSurfaceLevel.ADAPTER_PROJECTION_ONLY,
        ExecutionSurfaceLevel.NON_EXECUTABLE,
    }
    assert surface.attempted_surfaces
    assert surface.callable_surfaces or surface.failed_surfaces
    if surface.execution_level is not ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION:
        assert surface.fallback_reasons


def test_stage25_execution_level_does_not_label_adapter_projection_as_full_execution() -> None:
    run = run_stage25_reaction("presence_only", include_falsifiers=False)
    if run.execution_surface.subject_tick_used is False:
        assert run.execution_surface.execution_level is not ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION


def test_stage25_falsifier_detects_untracked_forbidden_core_path(monkeypatch) -> None:
    run = run_stage25_reaction("presence_only", include_falsifiers=False)
    monkeypatch.setattr(falsifier_module, "_modified_paths", lambda _repo_root: ())
    monkeypatch.setattr(falsifier_module, "_untracked_paths", lambda _repo_root: ("src/substrate/subject_tick/leak_probe.py",))
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(run))
    assert outcomes["core_contamination"] is False


def test_stage25_falsifier_detects_a_deficit_promoted_to_permission() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(step.phase_trace_summary, w04_usefulness_as_permission=True)
    bad_step = replace(step, phase_trace_summary=bad_summary, world_event_reaction=replace(step.world_event_reaction, blocked_aperture_seen=False))
    mutated = replace(run, steps=(bad_step,) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["a_deficit_as_permission"] is False


def test_stage25_falsifier_detects_w05_desired_as_observed_and_predicted_as_permission() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(
        step.phase_trace_summary,
        w05_desired_as_observed=True,
        w05_predicted_as_permitted=True,
    )
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["desired_as_observed"] is False
    assert outcomes["predicted_as_permitted"] is False


def test_stage25_falsifier_detects_blocked_aperture_clean_route() -> None:
    run = run_stage25_reaction("blocked_aperture", include_falsifiers=False)
    step = next(item for item in run.steps if item.world_event_reaction.blocked_aperture_seen)
    bad_summary = replace(step.phase_trace_summary, w04_clean_applicability_allowed=True)
    bad_step = replace(step, phase_trace_summary=bad_summary)
    mutated_steps = tuple(bad_step if item.step_index == step.step_index else item for item in run.steps)
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(replace(run, steps=mutated_steps)))
    assert outcomes["blocked_aperture_clean_route"] is False


def test_stage25_falsifier_detects_false_counterpart_claim_becomes_truth() -> None:
    run = run_stage25_reaction("false_counterpart_claim", include_falsifiers=False)
    step = run.steps[0]
    bad_claim = replace(step.counterpart_claim_reaction, promoted_to_fact=True, claim_not_fact_preserved=False)
    mutated = replace(run, steps=(replace(step, counterpart_claim_reaction=bad_claim),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["b_claim_as_fact"] is False


def test_stage25_falsifier_detects_correction_candidate_execution() -> None:
    run = run_stage25_reaction("noisy_signal", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(step.phase_trace_summary, w06_correction_executed=True, w06_execution_prohibited=False)
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["correction_candidate_executed"] is False


def test_stage25_falsifier_detects_execution_level_overclaim() -> None:
    run = run_stage25_reaction("presence_only", include_falsifiers=False)
    bad_surface = replace(
        run.execution_surface,
        execution_level=ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION,
        subject_tick_used=False,
        successful_surfaces=(),
    )
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(replace(run, execution_surface=bad_surface)))
    assert outcomes["execution_level_overclaim"] is False


def test_stage25_falsifier_detects_execution_level_overclaim_when_projection_step_exists() -> None:
    run = run_stage25_reaction("resource_claim_contact", include_falsifiers=False)
    step = run.steps[0]
    projected = replace(
        step,
        execution_surface_source="adapter_projection",
        adapter_limitations=("subject_tick_unavailable_or_failed",),
    )
    mutated = replace(run, steps=(projected,) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["execution_level_overclaim"] is False
    assert outcomes["adapter_projection_labeled_real"] is False


def test_stage25_falsifier_detects_execution_level_overclaim_when_full_claim_has_fallback_reasons() -> None:
    run = run_stage25_reaction("presence_only", include_falsifiers=False)
    bad_surface = replace(
        run.execution_surface,
        fallback_reasons=("adapter_projection_used_for_failed_step_only",),
    )
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(replace(run, execution_surface=bad_surface)))
    assert outcomes["execution_level_overclaim"] is False


def test_stage25_falsifier_detects_execution_level_overclaim_when_successful_surface_omits_subject_tick() -> None:
    run = run_stage25_reaction("presence_only", include_falsifiers=False)
    bad_surface = replace(
        run.execution_surface,
        successful_surfaces=("owner_surface.packet_to_w01_world_packet",),
        subject_tick_used=True,
        execution_level=ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION,
    )
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(replace(run, execution_surface=bad_surface)))
    assert outcomes["execution_level_overclaim"] is False


def test_stage25_falsifier_detects_phase_coverage_fake_without_tick_evidence() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(
        step.phase_trace_summary,
        phase_coverage=("W01", "W02", "W03", "W04", "W05", "W06"),
        coverage_complete=True,
        phase_coverage_verified=True,
        phase_coverage_verification_mode="tick_result_artifact_presence",
        phase_coverage_evidence=("W01:w01_result.gate",),
        phase_coverage_missing_reason=None,
    )
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["phase_coverage_fake"] is False


def test_stage25_falsifier_detects_phase_coverage_fake_when_tick_mode_claimed_but_unverified() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(
        step.phase_trace_summary,
        coverage_complete=True,
        phase_coverage_verified=False,
        phase_coverage_verification_mode="tick_result_artifact_presence",
        phase_coverage_missing_reason=None,
    )
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["phase_coverage_fake"] is False


def test_stage25_falsifier_detects_hidden_truth_leak_in_structured_payload_path() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    leaked_summary = dict(run.b_visible_claim_summary)
    leaked_summary["debug_meta"] = {"harness_truth": {"b": {"water": "surplus"}}}
    mutated = replace(run, b_visible_claim_summary=leaked_summary)
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["hidden_truth_leakage_stage25"] is False


def test_stage25_falsifier_detects_eval_label_leak_in_phase_trace_reason_codes() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(
        step.phase_trace_summary,
        reason_codes=step.phase_trace_summary.reason_codes + ("mutually_beneficial_trade_possible_eval_only",),
    )
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["hidden_truth_leakage_stage25"] is False
    assert outcomes["mirrored_complementarity_as_oracle"] is False


def test_stage25_falsifier_detects_a_surplus_promoted_to_trade_offer() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(
        step.phase_trace_summary,
        reason_codes=step.phase_trace_summary.reason_codes + ("trade_offer:true",),
    )
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["a_surplus_as_trade_offer"] is False


def test_stage25_falsifier_detects_mirrored_complementarity_oracle_in_trace_summary() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    bad_summary = replace(
        step.phase_trace_summary,
        reason_codes=step.phase_trace_summary.reason_codes + ("true_need_surplus_pairing",),
    )
    mutated = replace(run, steps=(replace(step, phase_trace_summary=bad_summary),) + run.steps[1:])
    outcomes = _outcome_map(falsifier_module.run_stage25_reaction_falsifiers(mutated))
    assert outcomes["mirrored_complementarity_as_oracle"] is False
