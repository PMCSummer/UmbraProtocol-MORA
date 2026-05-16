from __future__ import annotations

import json

from experiments.symbolic_trade import stage25_result_to_dict
from experiments.symbolic_trade.internal_state import build_self_state_probe_for_scenario
from experiments.symbolic_trade.runner import list_scenarios, run_stage25_reaction
from experiments.symbolic_trade.subject_reaction_probe import ExecutionSurfaceLevel


def test_stage25_modules_import_from_repo_root_without_manual_pythonpath() -> None:
    import experiments.symbolic_trade.subject_reaction_probe as probe  # noqa: F401
    import experiments.symbolic_trade.stage25_runner as runner  # noqa: F401


def test_stage25_self_state_probe_keeps_computational_boundary() -> None:
    probe = build_self_state_probe_for_scenario("mirrored_resource_asymmetry")
    assert probe.deficit_markers
    assert probe.surplus_markers
    assert probe.action_authorization_granted is False
    assert probe.evidence_boundary == "self_state_may_inform_desired_signal_only"
    for state in probe.resource_states:
        assert state.may_count_as_world_evidence is False
        assert state.may_authorize_action is False


def test_stage25_all_scenarios_run_with_phase_coverage_and_honest_claim_boundary() -> None:
    for scenario in list_scenarios():
        run = run_stage25_reaction(scenario, include_falsifiers=True)
        assert run.stage == "stage25_reaction_probe"
        assert run.steps
        assert run.execution_surface.execution_level in {
            ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION,
            ExecutionSurfaceLevel.PARTIAL_SUBJECT_TICK_EXECUTION,
            ExecutionSurfaceLevel.OWNER_SURFACE_EXECUTION,
            ExecutionSurfaceLevel.ADAPTER_PROJECTION_ONLY,
            ExecutionSurfaceLevel.NON_EXECUTABLE,
        }
        assert run.claim_boundary.instrumentation_only is True
        assert run.claim_boundary.adapter_projection_not_competence is True
        assert all(item["passed"] for item in run.falsifier_results), scenario
        for step in run.steps:
            assert {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(step.phase_trace_summary.phase_coverage))
            if run.execution_surface.execution_level is ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION:
                assert step.phase_trace_summary.phase_coverage_verified is True
                assert step.phase_trace_summary.phase_coverage_verification_mode == "tick_result_artifact_presence"
                evidence_phases = {
                    item.split(":", 1)[0]
                    for item in step.phase_trace_summary.phase_coverage_evidence
                    if ":" in item
                }
                assert {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(evidence_phases)


def test_stage25_false_counterpart_claim_remains_claim_not_fact() -> None:
    run = run_stage25_reaction("false_counterpart_claim", include_falsifiers=False)
    claim_steps = [step for step in run.steps if step.counterpart_claim_reaction.claim_detected]
    assert claim_steps
    assert all(step.counterpart_claim_reaction.claim_not_fact_preserved for step in claim_steps)
    assert all(step.counterpart_claim_reaction.promoted_to_fact is False for step in claim_steps)


def test_stage25_blocked_aperture_does_not_clean_route() -> None:
    run = run_stage25_reaction("blocked_aperture", include_falsifiers=False)
    blocked = [step for step in run.steps if step.world_event_reaction.blocked_aperture_seen]
    assert blocked
    assert all(step.phase_trace_summary.w04_clean_applicability_allowed is False for step in blocked)


def test_stage25_noisy_signal_keeps_uncertainty_and_noisy_not_fact() -> None:
    run = run_stage25_reaction("noisy_signal", include_falsifiers=False)
    noisy = [step for step in run.steps if step.world_event_reaction.contradiction_seen]
    assert noisy
    assert all(step.phase_trace_summary.w06_residual_uncertainty_present for step in noisy)


def test_stage25_self_state_desired_not_observed_and_not_permission() -> None:
    run = run_stage25_reaction("mirrored_resource_asymmetry", include_falsifiers=False)
    assert all(step.phase_trace_summary.w05_desired_as_observed is False for step in run.steps)
    assert all(step.phase_trace_summary.w05_predicted_as_permitted is False for step in run.steps)


def test_stage25_correction_candidate_not_executed() -> None:
    run = run_stage25_reaction("noisy_signal", include_falsifiers=False)
    assert all(step.phase_trace_summary.w06_execution_prohibited for step in run.steps)
    assert all(step.phase_trace_summary.w06_correction_executed is False for step in run.steps)


def test_stage25_default_json_excludes_eval_only_and_visible_sections_no_hidden_truth() -> None:
    run = run_stage25_reaction("eval_label_leak_attack", include_falsifiers=False)
    payload = stage25_result_to_dict(run, include_eval_only=False)
    assert "eval_only" not in payload
    blob = json.dumps(payload["steps"], sort_keys=True)
    assert "harness_truth" not in blob
    assert "mutually_beneficial_trade_possible_eval_only" not in blob
    assert "success_labels" not in blob


def test_stage25_include_eval_only_scoped_to_eval_section() -> None:
    run = run_stage25_reaction("eval_label_leak_attack", include_falsifiers=False)
    payload = stage25_result_to_dict(run, include_eval_only=True)
    assert "eval_only" in payload
    blob = json.dumps(payload["steps"], sort_keys=True)
    assert "harness_truth" not in blob
    assert "mutually_beneficial_trade_possible_eval_only" not in blob
    assert "success_labels" not in blob
