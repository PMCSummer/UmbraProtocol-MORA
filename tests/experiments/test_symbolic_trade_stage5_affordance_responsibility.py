from __future__ import annotations

from pytest import raises

from experiments.symbolic_trade.affordance_responsibility import (
    AffordanceEpisodeResponsibilityRecord,
    AffordanceUseRequest,
    WorldActuatorEnvelope,
)


def test_affordance_use_request_cannot_drop_subject_execution_prohibition() -> None:
    with raises(ValueError):
        AffordanceUseRequest(
            request_id="req:1",
            selected_affordance_ref="aff:1",
            give_resource="food",
            requested_or_expected_receive_resource="water",
            target_counterpart_ref="counterpart_b",
            intended_effect="bounded_external_transfer_attempt_request",
            required_permissions=("w04_gate",),
            prohibited_interpretations=("no_autonomous_trade_claim",),
            execution_requested=True,
            request_valid=True,
            execution_prohibited_until_world_actuator=False,
            may_be_sent_to_world_actuator=True,
            must_not_execute_inside_subject=True,
            source_phase_refs=("W04:w04_result.gate",),
            claim_boundary=("invocation_request_not_execution",),
        )


def test_world_actuator_envelope_cannot_claim_subject_motor_control() -> None:
    with raises(ValueError):
        WorldActuatorEnvelope(
            actuator_id="act:1",
            actuator_kind="external_world_actuator",
            invocation_request_ref="req:1",
            explicit_execution_flag=True,
            invocation_id="inv:1",
            precondition_check_result="passed",
            invoked=True,
            invocation_reason=("world_execution_harness_only",),
            blocked_reason=(),
            attempt_id="attempt:1",
            observed_result_ref="result:1",
            actuator_authority="harness_world_execution_surface",
            subject_motor_control_claim="true",
        )


def test_episode_completion_claim_requires_verified_status() -> None:
    with raises(ValueError):
        AffordanceEpisodeResponsibilityRecord(
            episode_id="ep:1",
            offer_candidate_ref="offer:1",
            selection_ref="sel:1",
            invocation_request_ref="req:1",
            actuator_envelope_ref="act:1",
            observed_result_ref="result:1",
            causing_invocation_id="inv:1",
            causing_attempt_id="attempt:1",
            verification_status="unverified",
            completion_claim=True,
            completion_basis=("a_to_b_attempt_visible",),
            completion_basis_chain_verified=False,
            completion_basis_missing=("episode_verified",),
            completion_authority="episode_verification_chain",
            used_transfer_result_as_sole_authority=True,
            used_eval_only_for_completion=False,
            used_hidden_truth_for_completion=False,
            used_scenario_label_for_completion=False,
            used_w06_correction_execution_for_completion=False,
            residue_status="no_residue",
            failed_or_blocked_reason=(),
            passive_packet_refs=(),
            causal_post_invocation_refs=("packet:4",),
            claim_boundary=("candidate_attempt_result_verification_separated",),
        )
