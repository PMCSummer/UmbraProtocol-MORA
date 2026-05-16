from __future__ import annotations

from experiments.symbolic_trade.stage5_affordance_trace_runner import (
    STAGE5_SCENARIOS,
    run_stage5_affordance_trace,
)


def test_stage5_all_scenarios_run_noexec_and_keep_world_actuator_off() -> None:
    for scenario in STAGE5_SCENARIOS:
        trace = run_stage5_affordance_trace(scenario, include_falsifiers=True, execute_world_actuator=False)
        assert trace.world_actuator_envelope.invoked is False
        assert trace.world_actuator_envelope.explicit_execution_flag is False
        assert trace.episode_record.completion_claim is False
        assert trace.transfer_result.value == "not_attempted"
        assert len(trace.episode_record.causal_post_invocation_refs) == 0


def test_stage5_successful_scripted_exchange_cycle_exec_verifies_episode() -> None:
    trace = run_stage5_affordance_trace(
        "successful_scripted_exchange_cycle",
        include_falsifiers=True,
        execute_world_actuator=True,
    )
    assert trace.selection_record.selection_status.value == "selected_for_invocation_request"
    assert trace.affordance_use_request.may_be_sent_to_world_actuator is True
    assert trace.world_actuator_envelope.invoked is True
    assert bool(trace.world_actuator_envelope.invocation_id)
    assert bool(trace.world_actuator_envelope.attempt_id)
    assert trace.transfer_result.value == "succeeded"
    assert trace.episode_record.verification_status == "verified"
    assert trace.episode_record.completion_claim is True
    assert len(trace.episode_record.causal_post_invocation_refs) > 0
    assert trace.episode_record.completion_basis_chain_verified is True
    assert trace.episode_record.completion_basis_missing == ()
    assert trace.episode_record.used_transfer_result_as_sole_authority is False


def test_stage5_blocked_aperture_does_not_invoke_even_in_exec_mode() -> None:
    trace = run_stage5_affordance_trace("blocked_aperture", include_falsifiers=True, execute_world_actuator=True)
    assert trace.selection_record.selection_status.value in {
        "not_selected_blocked",
        "not_selected_insufficient_information",
        "not_selected_no_offer_candidate",
    }
    assert trace.affordance_use_request.may_be_sent_to_world_actuator is False
    assert trace.world_actuator_envelope.invoked is False
    assert trace.episode_record.completion_claim is False
    assert any(item.startswith("affordance_status:blocked") for item in trace.module_responsibility_ledger.unresolved_gaps)


def test_stage5_transfer_failure_keeps_residue() -> None:
    trace = run_stage5_affordance_trace("transfer_affordance_failure", include_falsifiers=True, execute_world_actuator=True)
    assert trace.world_actuator_envelope.invoked is True
    assert trace.transfer_result.value == "failed_unknown"
    assert "residue" in trace.episode_record.residue_status
    assert trace.episode_record.completion_claim is False
    assert trace.episode_record.used_w06_correction_execution_for_completion is False


def test_stage5_phase_evidence_and_ledger_present() -> None:
    trace = run_stage5_affordance_trace("mirrored_resource_asymmetry", include_falsifiers=True, execute_world_actuator=False)
    assert trace.phase_coverage_verified is True
    phase_codes = {item.split(":", 1)[0] for item in trace.phase_coverage_evidence}
    assert {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(phase_codes)
    assert trace.phase_evidence_source_run_id == trace.stage4_run_id
    assert set(trace.phase_coverage_evidence) == set(trace.stage4_phase_coverage_evidence)
    ledger = trace.module_responsibility_ledger
    assert ledger.W04_responsibility
    assert ledger.W05_responsibility
    assert ledger.W06_responsibility
    assert ledger.A04_affordance_binding_responsibility
    assert ledger.P02_episode_responsibility


def test_stage5_noexec_passive_packets_are_not_causal_in_successful_cycle() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=True, execute_world_actuator=False)
    assert trace.world_actuator_envelope.invoked is False
    assert len(trace.episode_record.passive_packet_refs) > 0
    assert len(trace.episode_record.causal_post_invocation_refs) == 0
    assert all(record["caused_by_transfer_invocation"] is False for record in trace.passive_response_records)
    assert len(trace.causal_response_records) == 0
