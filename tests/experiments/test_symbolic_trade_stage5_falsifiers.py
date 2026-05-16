from __future__ import annotations

from dataclasses import replace

from experiments.symbolic_trade.falsifiers import run_stage5_affordance_trace_falsifiers
from experiments.symbolic_trade.models import TransferOutcome
from experiments.symbolic_trade.stage5_affordance_trace_runner import run_stage5_affordance_trace


REQUIRED_STAGE5_FALSIFIERS = {
    "stage5_selection_without_offer_candidate",
    "stage5_affordance_available_as_invoked",
    "stage5_invocation_request_as_execution",
    "stage5_execution_without_explicit_actuator_flag",
    "stage5_execution_without_valid_request",
    "stage5_transfer_result_as_completion_oracle",
    "stage5_passive_packet_as_causal_response",
    "stage5_b_claim_as_fact",
    "stage5_a_deficit_as_permission",
    "stage5_a_surplus_as_auto_offer",
    "stage5_complementarity_as_oracle",
    "stage5_blocked_affordance_invoked",
    "stage5_failed_transfer_erases_residue",
    "stage5_noexec_completion_claim",
    "stage5_world_actuator_claims_subject_motor_control",
    "stage5_w06_revision_executed",
    "stage5_trade_specific_magic_channel",
    "stage5_eval_only_used_in_affordance_decision",
    "stage5_hidden_inventory_used_in_affordance_decision",
    "stage5_core_contamination",
    "stage5_module_responsibility_missing",
    "stage5_phase_evidence_fabricated",
}


def _map(results) -> dict[str, bool]:
    return {item.name: item.passed for item in results}


def test_stage5_falsifiers_exist_and_pass_clean() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    results = run_stage5_affordance_trace_falsifiers(trace)
    names = {item.name for item in results}
    assert REQUIRED_STAGE5_FALSIFIERS.issubset(names)
    assert all(item.passed for item in results)


def test_stage5_falsifier_negative_selection_without_offer_candidate() -> None:
    trace = run_stage5_affordance_trace("mirrored_resource_asymmetry", include_falsifiers=False, execute_world_actuator=False)
    bad_selection = replace(
        trace.selection_record,
        response_candidate_ref=None,
    )
    bad_trace = replace(trace, selection_record=bad_selection)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_selection_without_offer_candidate"] is False


def test_stage5_falsifier_negative_transfer_result_as_completion_oracle() -> None:
    trace = run_stage5_affordance_trace("mirrored_resource_asymmetry", include_falsifiers=False, execute_world_actuator=True)
    bad_episode = replace(trace.episode_record)
    object.__setattr__(bad_episode, "verification_status", "unverified")
    object.__setattr__(bad_episode, "completion_claim", True)
    bad_trace = replace(
        trace,
        transfer_result=TransferOutcome.SUCCEEDED,
        episode_record=bad_episode,
    )
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_transfer_result_as_completion_oracle"] is False


def test_stage5_falsifier_negative_completion_missing_chain_requirements() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    bad_episode = replace(
        trace.episode_record,
        completion_claim=True,
        completion_basis_chain_verified=False,
        completion_basis_missing=("world_actuator_invoked", "episode_verified"),
        causing_invocation_id=None,
        causing_attempt_id=None,
    )
    bad_envelope = replace(
        trace.world_actuator_envelope,
        invoked=False,
        explicit_execution_flag=False,
        invocation_id=None,
        attempt_id=None,
    )
    bad_request = replace(
        trace.affordance_use_request,
        execution_requested=False,
        request_valid=False,
        may_be_sent_to_world_actuator=False,
    )
    bad_trace = replace(trace, episode_record=bad_episode, world_actuator_envelope=bad_envelope, affordance_use_request=bad_request)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_transfer_result_as_completion_oracle"] is False
    assert results["stage5_invocation_request_as_execution"] is True


def test_stage5_falsifier_negative_passive_packet_as_causal_response() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=False)
    bad_episode = replace(
        trace.episode_record,
        passive_packet_refs=("packet:passive",),
        causal_post_invocation_refs=("packet:causal",),
    )
    bad_trace = replace(trace, episode_record=bad_episode)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_passive_packet_as_causal_response"] is False


def test_stage5_falsifier_negative_causal_refs_without_invocation() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    bad_episode = replace(
        trace.episode_record,
        causal_post_invocation_refs=("packet:causal",),
    )
    bad_envelope = replace(trace.world_actuator_envelope, invoked=False, invocation_id=None, attempt_id=None)
    bad_trace = replace(trace, episode_record=bad_episode, world_actuator_envelope=bad_envelope)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_passive_packet_as_causal_response"] is False


def test_stage5_falsifier_negative_causal_refs_missing_invocation_ids() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    bad_causal = tuple(
        {
            **item,
            "causing_invocation_id": None,
            "attempt_id": None,
            "invocation_link_verified": False,
        }
        for item in trace.causal_response_records
    )
    bad_trace = replace(trace, causal_response_records=bad_causal)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_passive_packet_as_causal_response"] is False


def test_stage5_falsifier_negative_eval_and_hidden_leak() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    bad_selection = replace(
        trace.selection_record,
        why_this_affordance=trace.selection_record.why_this_affordance + ("eval_only_success_label", "hidden_inventory_ref"),
    )
    bad_trace = replace(trace, selection_record=bad_selection)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_eval_only_used_in_affordance_decision"] is False
    assert results["stage5_hidden_inventory_used_in_affordance_decision"] is False


def test_stage5_falsifier_negative_blocked_affordance_invoked_structural() -> None:
    trace = run_stage5_affordance_trace("blocked_aperture", include_falsifiers=False, execute_world_actuator=True)
    bad_selection = replace(
        trace.selection_record,
        selected_affordance_status="blocked",
        selected_affordance_id="blocked_aperture:affordance:aperture_transfer",
        selected_affordance_kind="aperture_transfer",
    )
    bad_request = replace(
        trace.affordance_use_request,
        selected_affordance_ref="blocked_aperture:affordance:aperture_transfer",
        request_valid=True,
        may_be_sent_to_world_actuator=True,
    )
    bad_envelope = replace(
        trace.world_actuator_envelope,
        invoked=True,
        explicit_execution_flag=True,
        invocation_id="inv:1",
        attempt_id="attempt:1",
    )
    bad_trace = replace(
        trace,
        selection_record=bad_selection,
        affordance_use_request=bad_request,
        world_actuator_envelope=bad_envelope,
        transfer_result=TransferOutcome.SUCCEEDED,
    )
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_blocked_affordance_invoked"] is False


def test_stage5_falsifier_negative_w06_correction_execution_typed_boundary() -> None:
    trace = run_stage5_affordance_trace("transfer_affordance_failure", include_falsifiers=False, execute_world_actuator=True)
    bad_episode = replace(
        trace.episode_record,
        used_w06_correction_execution_for_completion=True,
        completion_claim=True,
        verification_status="verified",
    )
    bad_trace = replace(trace, episode_record=bad_episode)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_w06_revision_executed"] is False
    assert results["stage5_transfer_result_as_completion_oracle"] is False


def test_stage5_falsifier_negative_trade_magic_channel_structured_payload() -> None:
    trace = run_stage5_affordance_trace("mirrored_resource_asymmetry", include_falsifiers=False, execute_world_actuator=False)
    bad_selection = replace(
        trace.selection_record,
        why_this_affordance=trace.selection_record.why_this_affordance + ("magic_trade_channel",),
    )
    bad_trace = replace(trace, selection_record=bad_selection)
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_trade_specific_magic_channel"] is False


def test_stage5_falsifier_negative_module_ledger_missing_and_phase_evidence_fake() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    bad_ledger = replace(trace.module_responsibility_ledger, W04_responsibility="")
    bad_trace = replace(
        trace,
        module_responsibility_ledger=bad_ledger,
        phase_coverage_evidence=("fake:evidence",),
    )
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_module_responsibility_missing"] is False
    assert results["stage5_phase_evidence_fabricated"] is False


def test_stage5_falsifier_negative_phase_evidence_unlinked_to_stage4() -> None:
    trace = run_stage5_affordance_trace("successful_scripted_exchange_cycle", include_falsifiers=False, execute_world_actuator=True)
    bad_trace = replace(
        trace,
        phase_coverage_verified=True,
        phase_coverage_evidence=("W01:fake", "W02:fake", "W03:fake", "W04:fake", "W05:fake", "W06:fake"),
    )
    results = _map(run_stage5_affordance_trace_falsifiers(bad_trace))
    assert results["stage5_phase_evidence_fabricated"] is False
