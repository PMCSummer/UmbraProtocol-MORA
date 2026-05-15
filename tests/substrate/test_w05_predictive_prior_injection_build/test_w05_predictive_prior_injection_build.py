from __future__ import annotations

from dataclasses import replace

from substrate.w05_predictive_prior_injection import (
    W05InjectionTarget,
    W05MismatchClass,
    W05SignalChannel,
)
from tests.substrate.w05_predictive_prior_injection_testkit import (
    build_w05_harness,
    clone_input,
    w05_desired_signal,
    w05_gain_config,
    w05_input_bundle,
    w05_observed_signal,
    w05_permitted_signal,
    w05_predicted_signal,
)


def _run(case_id: str, bundle):
    return build_w05_harness(case_id, input_bundle=bundle)


def _packet(result):
    return result.downstream_routing_packets[0]


def _mismatch(result):
    return result.mismatch_classifications[0]


def _routing(result):
    return result.update_routing_packets[0]


def _gain(result):
    return result.prior_gain_decisions[0]


def _prediction_use(result):
    return result.prediction_use_records[0]


def test_clean_w04_allowed_prior_builds_four_channel_signal_stack() -> None:
    result = _run("clean", w05_input_bundle("clean"))
    stack = result.signal_stacks[0]
    assert stack.desired_signal.signal_id.endswith("desired:signal")
    assert stack.predicted_signal.signal_id.endswith("predicted:signal")
    assert stack.observed_signal.signal_id.endswith("observed:signal")
    assert stack.permitted_signal.signal_id.endswith("permitted:signal")


def test_missing_permitted_channel_blocks_clean_routing() -> None:
    base = w05_input_bundle("missing-permitted")
    result = _run("missing-permitted", clone_input(base, permitted_signal=None))
    assert result.gate.no_clean_routing is True


def test_desired_predicted_observed_permitted_channels_remain_separate() -> None:
    result = _run("separate", w05_input_bundle("separate"))
    stack = result.signal_stacks[0]
    ids = {
        stack.desired_signal.signal_id,
        stack.predicted_signal.signal_id,
        stack.observed_signal.signal_id,
        stack.permitted_signal.signal_id,
    }
    assert len(ids) == 4


def test_collapsed_channels_are_rejected_as_malformed_stack() -> None:
    base = w05_input_bundle("collapsed")
    desired = replace(base.desired_signal, signal_id=base.predicted_signal.signal_id)
    result = _run("collapsed", clone_input(base, desired_signal=desired))
    assert _mismatch(result).mismatch_class is W05MismatchClass.MALFORMED_SIGNAL_STACK
    assert _packet(result).must_abstain is True
    assert "duplicate_signal_id_across_channels" in _mismatch(result).reason_codes


def test_signal_stack_preserves_per_channel_provenance_authority_confidence_precision() -> None:
    base = w05_input_bundle("channel-separation")
    desired = replace(
        base.desired_signal,
        provenance=("prov.desired",),
        source_authority="authority.desired",
        confidence=0.31,
        precision=0.41,
    )
    predicted = replace(
        base.predicted_signal,
        provenance=("prov.predicted",),
        source_authority="authority.predicted",
        confidence=0.72,
        precision=0.82,
        prior_strength=0.77,
    )
    observed = replace(
        base.observed_signal,
        provenance=("prov.observed",),
        source_authority="authority.observed",
        confidence=0.63,
        evidence_precision=0.93,
    )
    permitted = replace(
        base.permitted_signal,
        provenance=("prov.permitted",),
        source_authority="authority.permitted",
        may_deploy_candidate=False,
        must_block=True,
    )
    result = _run(
        "channel-separation",
        clone_input(
            base,
            desired_signal=desired,
            predicted_signal=predicted,
            observed_signal=observed,
            permitted_signal=permitted,
        ),
    )
    stack = result.signal_stacks[0]
    provenance = dict(stack.per_channel_provenance)
    authority = dict(stack.per_channel_authority)
    confidence = dict(stack.per_channel_confidence)
    precision = dict(stack.per_channel_precision)
    assert provenance[W05SignalChannel.DESIRED] == ("prov.desired",)
    assert provenance[W05SignalChannel.PREDICTED] == ("prov.predicted",)
    assert provenance[W05SignalChannel.OBSERVED] == ("prov.observed",)
    assert provenance[W05SignalChannel.PERMITTED] == ("prov.permitted",)
    assert authority[W05SignalChannel.DESIRED] == "authority.desired"
    assert authority[W05SignalChannel.PREDICTED] == "authority.predicted"
    assert authority[W05SignalChannel.OBSERVED] == "authority.observed"
    assert authority[W05SignalChannel.PERMITTED] == "authority.permitted"
    assert confidence[W05SignalChannel.OBSERVED] != confidence[W05SignalChannel.PREDICTED]
    assert precision[W05SignalChannel.OBSERVED] == 0.93
    assert precision[W05SignalChannel.PREDICTED] == 0.82
    assert stack.channel_integrity_status == "separated"
    assert _packet(result).may_consider_update is False


def test_wrong_channel_marker_in_slot_is_rejected_as_collapse() -> None:
    base = w05_input_bundle("channel-marker-mismatch")
    desired = replace(base.desired_signal, channel=W05SignalChannel.PREDICTED)
    result = _run("channel-marker-mismatch", clone_input(base, desired_signal=desired))
    mismatch = _mismatch(result)
    assert mismatch.mismatch_class is W05MismatchClass.MALFORMED_SIGNAL_STACK
    assert "channel_marker_mismatch" in mismatch.reason_codes
    assert _packet(result).may_consider_update is False
    assert _packet(result).must_abstain is True


def test_w04_must_block_prevents_prior_injection() -> None:
    base = w05_input_bundle("w04-block")
    permitted = replace(base.permitted_signal, must_block=True, may_deploy_candidate=False)
    result = _run("w04-block", clone_input(base, permitted_signal=permitted))
    assert _packet(result).may_consider_update is False
    assert _packet(result).must_abstain is True


def test_w04_must_revalidate_routes_to_revalidation_not_clean_injection() -> None:
    base = w05_input_bundle("w04-revalidate")
    permitted = replace(base.permitted_signal, must_revalidate=True, may_deploy_candidate=False, may_use_after_revalidation=True)
    result = _run("w04-revalidate", clone_input(base, permitted_signal=permitted))
    assert _packet(result).must_revalidate is True
    assert _packet(result).may_consider_update is False


def test_w04_hint_only_cannot_become_clean_policy_influence() -> None:
    base = w05_input_bundle("w04-hint")
    permitted = replace(base.permitted_signal, may_deploy_candidate=False, may_use_as_hint_only=True)
    result = _run("w04-hint", clone_input(base, permitted_signal=permitted))
    assert _packet(result).may_adjust_policy_hint is False


def test_w04_prohibited_uses_preserved_in_w05_downstream_packet() -> None:
    base = w05_input_bundle("w04-prohibited")
    permitted = replace(base.permitted_signal, prohibited_uses=("no_universal_world_truth", "no_action_authorization"))
    result = _run("w04-prohibited", clone_input(base, permitted_signal=permitted))
    packet = _packet(result)
    assert "no_universal_world_truth" in packet.prohibited_uses
    assert "no_action_authorization" in packet.prohibited_uses


def test_predicted_utility_does_not_override_permitted_false() -> None:
    base = w05_input_bundle("utility-not-permission")
    predicted = replace(base.predicted_signal, prior_strength=1.0, prediction_confidence=1.0)
    permitted = replace(base.permitted_signal, may_deploy_candidate=False, must_block=True)
    result = _run("utility-not-permission", clone_input(base, predicted_signal=predicted, permitted_signal=permitted))
    assert _packet(result).may_consider_update is False


def test_strong_desired_state_does_not_override_permitted_false() -> None:
    base = w05_input_bundle("desired-not-permission")
    desired = replace(base.desired_signal, priority="urgent")
    permitted = replace(base.permitted_signal, may_deploy_candidate=False, must_abstain=True)
    result = _run("desired-not-permission", clone_input(base, desired_signal=desired, permitted_signal=permitted))
    assert _packet(result).may_consider_update is False


def test_desired_state_is_not_treated_as_observation_or_evidence() -> None:
    base = w05_input_bundle("desired-not-evidence")
    desired = replace(base.desired_signal, requested_outcome="different_outcome")
    result = _run("desired-not-evidence", clone_input(base, desired_signal=desired))
    assert _mismatch(result).mismatch_class is W05MismatchClass.DESIRED_VS_PREDICTED


def test_semantic_desired_observed_collapse_is_rejected() -> None:
    base = w05_input_bundle("desired-observed-collapse")
    observed = replace(
        base.observed_signal,
        observed_outcome=base.desired_signal.requested_outcome,
        provenance=base.desired_signal.provenance,
        observation_refs=(),
    )
    result = _run("desired-observed-collapse", clone_input(base, observed_signal=observed))
    mismatch = _mismatch(result)
    assert mismatch.mismatch_class is W05MismatchClass.MALFORMED_SIGNAL_STACK
    assert "desired_observed_collapse_suspected" in mismatch.reason_codes
    assert _packet(result).may_consider_update is False
    assert _packet(result).must_abstain is True
    assert _packet(result).must_not_execute_update is True


def test_predicted_or_observed_signal_cannot_stand_in_for_permitted_channel() -> None:
    base = w05_input_bundle("permitted-standin")
    predicted_permitted = replace(
        base.permitted_signal,
        permitted_signal_id=base.predicted_signal.prediction_id,
        w04_decision_ref="",
        provenance=base.predicted_signal.provenance,
    )
    result = _run(
        "permitted-standin-predicted",
        clone_input(base, permitted_signal=predicted_permitted),
    )
    mismatch = _mismatch(result)
    assert mismatch.mismatch_class is W05MismatchClass.MALFORMED_SIGNAL_STACK
    assert "predicted_permitted_collapse_suspected" in mismatch.reason_codes
    assert (
        "missing_w04_permission_boundary" in mismatch.reason_codes
        or "predicted_permitted_collapse_suspected" in mismatch.reason_codes
    )
    assert _packet(result).may_consider_update is False
    assert _packet(result).execution_authorization_granted is False

    observed_permitted = replace(
        base.permitted_signal,
        permitted_signal_id=base.observed_signal.observation_id,
        w04_decision_ref="",
        provenance=base.observed_signal.provenance,
    )
    result_observed = _run(
        "permitted-standin-observed",
        clone_input(base, permitted_signal=observed_permitted),
    )
    mismatch_observed = _mismatch(result_observed)
    assert mismatch_observed.mismatch_class is W05MismatchClass.MALFORMED_SIGNAL_STACK
    assert "observed_permitted_collapse_suspected" in mismatch_observed.reason_codes
    assert _packet(result_observed).may_consider_update is False


def test_prediction_use_record_contains_prior_strength_precision_reliability_and_gain() -> None:
    result = _run("prediction-use", w05_input_bundle("prediction-use"))
    record = _prediction_use(result)
    assert record.prior_strength > 0
    assert record.evidence_precision > 0
    assert record.effective_prior_gain >= 0


def test_high_precision_contradictory_observation_suppresses_prior_gain() -> None:
    base = w05_input_bundle("high-precision-contradiction")
    observed = replace(base.observed_signal, evidence_precision=0.95, contradiction_markers=("c1",))
    result = _run("high-precision-contradiction", clone_input(base, observed_signal=observed))
    gain = _gain(result)
    assert gain.suppressed is True


def test_low_precision_noisy_observation_does_not_erase_prior_without_revalidation_marker() -> None:
    base = w05_input_bundle("low-precision-noise")
    observed = replace(base.observed_signal, evidence_precision=0.1)
    result = _run("low-precision-noise", clone_input(base, observed_signal=observed))
    gain = _gain(result)
    assert gain.effective_gain >= gain.gain_bounds[0]
    assert _packet(result).must_revalidate is True


def test_source_reliability_changes_effective_gain_or_routing_confidence() -> None:
    base = w05_input_bundle("source-reliability")
    high = _run("source-reliability-high", base)
    low_predicted = replace(base.predicted_signal, source_reliability=0.2)
    low = _run("source-reliability-low", clone_input(base, predicted_signal=low_predicted))
    assert _gain(high).effective_gain != _gain(low).effective_gain


def test_revoked_or_unknown_source_reliability_reduces_gain_or_blocks_clean_routing() -> None:
    base = w05_input_bundle("source-revoked")
    predicted = replace(base.predicted_signal, source_reliability=0.0)
    result = _run("source-revoked", clone_input(base, predicted_signal=predicted))
    assert _gain(result).effective_gain <= 0.01


def test_prior_strength_cannot_bypass_permitted_channel() -> None:
    base = w05_input_bundle("strength-bypass")
    predicted = replace(base.predicted_signal, prior_strength=1.0)
    permitted = replace(base.permitted_signal, may_deploy_candidate=False, must_block=True)
    result = _run("strength-bypass", clone_input(base, predicted_signal=predicted, permitted_signal=permitted))
    assert _packet(result).may_consider_update is False


def test_protected_target_caps_or_blocks_gain() -> None:
    base = w05_input_bundle("protected-cap")
    permitted = replace(base.permitted_signal, protected_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE,))
    result = _run("protected-cap", clone_input(base, permitted_signal=permitted))
    assert _gain(result).effective_gain <= base.prior_gain_config.protected_target_gain_cap


def test_predicted_vs_observed_mismatch_routes_to_world_or_affordance_candidate_without_execution() -> None:
    base = w05_input_bundle("pred-vs-obs")
    observed = replace(base.observed_signal, observed_outcome="obs:other")
    result = _run("pred-vs-obs", clone_input(base, observed_signal=observed))
    routing = _routing(result)
    assert _mismatch(result).mismatch_class is W05MismatchClass.PREDICTED_VS_OBSERVED
    assert _mismatch(result).compared_channels == (
        W05SignalChannel.PREDICTED,
        W05SignalChannel.OBSERVED,
    )
    assert routing.execution_prohibited is True


def test_desired_vs_permitted_mismatch_routes_to_permission_review_not_world_update() -> None:
    base = w05_input_bundle("desired-vs-permitted")
    permitted = replace(base.permitted_signal, must_block=True, may_deploy_candidate=False)
    result = _run("desired-vs-permitted", clone_input(base, permitted_signal=permitted))
    assert _mismatch(result).mismatch_class is W05MismatchClass.DESIRED_VS_PERMITTED
    assert _mismatch(result).compared_channels == (
        W05SignalChannel.DESIRED,
        W05SignalChannel.PERMITTED,
    )
    assert _routing(result).target_layer is W05InjectionTarget.POLICY_INTERFACE


def test_observed_vs_permitted_mismatch_routes_to_authority_or_guard_review() -> None:
    base = w05_input_bundle("obs-vs-permitted")
    observed = replace(base.observed_signal, source_authority="other_authority")
    result = _run("obs-vs-permitted", clone_input(base, observed_signal=observed))
    assert _mismatch(result).mismatch_class is W05MismatchClass.AUTHORITY_SCOPE
    assert _mismatch(result).compared_channels == (
        W05SignalChannel.OBSERVED,
        W05SignalChannel.PERMITTED,
    )


def test_prior_vs_current_evidence_mismatch_classified_distinctly() -> None:
    base = w05_input_bundle("prior-vs-current")
    predicted = replace(base.predicted_signal, expected_validity_window=(1, 1))
    observed = replace(base.observed_signal, timestamp_or_sequence=9)
    result = _run("prior-vs-current", clone_input(base, predicted_signal=predicted, observed_signal=observed))
    assert _mismatch(result).mismatch_direction.value == "prior_vs_current_evidence"
    assert _mismatch(result).compared_channels == (
        W05SignalChannel.PREDICTED,
        W05SignalChannel.OBSERVED,
    )


def test_ownership_mismatch_routes_to_ownership_target_without_executing_learning() -> None:
    base = w05_input_bundle("ownership-mismatch")
    observed = replace(base.observed_signal, source_authority="other_authority")
    result = _run("ownership-mismatch", clone_input(base, observed_signal=observed))
    assert _routing(result).target_layer is W05InjectionTarget.OWNERSHIP_MODEL
    assert _routing(result).execution_prohibited is True


def test_goal_satisfaction_mismatch_does_not_become_world_model_update() -> None:
    base = w05_input_bundle("goal-mismatch")
    desired = replace(base.desired_signal, requested_outcome="other_goal")
    result = _run("goal-mismatch", clone_input(base, desired_signal=desired))
    assert _routing(result).target_layer is W05InjectionTarget.GOAL_SATISFACTION_MODEL


def test_validity_mismatch_routes_to_revalidation() -> None:
    base = w05_input_bundle("validity-mismatch")
    predicted = replace(base.predicted_signal, expected_validity_window=(1, 1))
    observed = replace(base.observed_signal, timestamp_or_sequence=5)
    result = _run("validity-mismatch", clone_input(base, predicted_signal=predicted, observed_signal=observed))
    assert _packet(result).must_revalidate is True


def test_authority_scope_mismatch_routes_to_revalidation_or_block() -> None:
    base = w05_input_bundle("authority-mismatch")
    observed = replace(base.observed_signal, source_authority="other_authority")
    result = _run("authority-mismatch", clone_input(base, observed_signal=observed))
    assert _packet(result).must_revalidate is True


def test_temporal_scope_mismatch_routes_to_revalidation() -> None:
    base = w05_input_bundle("temporal-mismatch")
    predicted = replace(base.predicted_signal, expected_validity_window=(1, 1))
    observed = replace(base.observed_signal, timestamp_or_sequence=3)
    result = _run("temporal-mismatch", clone_input(base, predicted_signal=predicted, observed_signal=observed))
    assert _packet(result).must_revalidate is True


def test_constitutional_boundary_mismatch_blocks_or_escalates() -> None:
    base = w05_input_bundle("constitutional")
    permitted = replace(base.permitted_signal, protected_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE,))
    result = _run("constitutional", clone_input(base, permitted_signal=permitted))
    assert _packet(result).must_escalate is True


def test_ambiguous_mismatch_preserves_competing_class_candidates() -> None:
    base = w05_input_bundle("ambiguous")
    observed = replace(base.observed_signal, evidence_precision=0.95, contradiction_markers=("c1",), observed_outcome="obs:other")
    result = _run("ambiguous", clone_input(base, observed_signal=observed))
    mismatch = _mismatch(result)
    assert mismatch.mismatch_class is W05MismatchClass.AMBIGUOUS_MULTI_CLASS
    assert len(mismatch.competing_class_candidates) >= 2


def test_all_update_routing_packets_have_execution_prohibited_true() -> None:
    result = _run("routing-prohibited", w05_input_bundle("routing-prohibited"))
    assert all(item.execution_prohibited is True for item in result.update_routing_packets)


def test_permitted_channel_enforcement_record_preserves_permission_markers() -> None:
    base = w05_input_bundle("perm-enforcement")
    predicted = replace(base.predicted_signal, prior_strength=1.0, prediction_confidence=1.0)
    desired = replace(base.desired_signal, priority="urgent")
    permitted = replace(base.permitted_signal, may_deploy_candidate=False, must_block=True)
    result = _run(
        "perm-enforcement",
        clone_input(base, predicted_signal=predicted, desired_signal=desired, permitted_signal=permitted),
    )
    assert result.permitted_channel_enforcement_records
    record = result.permitted_channel_enforcement_records[0]
    assert record.utility_not_permission is True
    assert record.desired_not_permission is True
    assert record.prediction_not_permission is True
    assert record.blocked_by_w04 is True
    assert "permitted_channel_block" in _gain(result).reason_codes
    assert _packet(result).may_consider_update is False
    assert (_packet(result).must_abstain or _packet(result).must_revalidate) is True
    assert _packet(result).must_not_execute_update is True
    assert _packet(result).execution_authorization_granted is False


def test_w04_prohibited_uses_and_guardrails_preserved_in_permitted_enforcement() -> None:
    base = w05_input_bundle("perm-guardrails")
    prohibited = (
        "no_action_authorization",
        "no_update_execution",
        "preserve_w04_scope",
        "protected_target_boundary",
    )
    permitted = replace(base.permitted_signal, prohibited_uses=prohibited)
    result = _run("perm-guardrails", clone_input(base, permitted_signal=permitted))
    packet = _packet(result)
    enforcement = result.permitted_channel_enforcement_records[0]
    for marker in prohibited:
        assert marker in packet.prohibited_uses
        assert marker in packet.preserved_guardrails
        assert marker in enforcement.prohibited_uses
    assert "must_not_execute_update" in packet.preserved_guardrails
    assert packet.execution_authorization_granted is False


def test_downstream_packet_always_has_must_not_execute_update() -> None:
    result = _run("must-not-execute", w05_input_bundle("must-not-execute"))
    assert _packet(result).must_not_execute_update is True


def test_execution_authorization_granted_is_always_false() -> None:
    result = _run("exec-auth-false", w05_input_bundle("exec-auth-false"))
    assert _packet(result).execution_authorization_granted is False


def test_mock_consumer_cannot_execute_update_from_w05_packet() -> None:
    result = _run("mock-consumer", w05_input_bundle("mock-consumer"))
    packet = _packet(result)
    can_execute = packet.may_consider_update and not packet.must_not_execute_update and packet.execution_authorization_granted
    assert can_execute is False


def test_update_routing_packet_contains_target_scope_severity_confidence_evidence_refs() -> None:
    result = _run("routing-shape", w05_input_bundle("routing-shape"))
    routing = _routing(result)
    assert routing.target_scope
    assert routing.severity
    assert routing.confidence >= 0
    assert isinstance(routing.evidence_refs, tuple)


def test_constitutional_guard_flags_preserved_and_load_bearing() -> None:
    base = w05_input_bundle("guard-load-bearing")
    permitted = replace(base.permitted_signal, constitutional_guard_flags=("guard_a",), protected_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE,))
    result = _run("guard-load-bearing", clone_input(base, permitted_signal=permitted))
    assert result.constitutional_guard_checks[0].reason_codes
    assert _packet(result).must_escalate is True


def test_ablation_removing_permitted_channel_changes_outcome() -> None:
    base = w05_input_bundle("ablation-permitted")
    with_permitted = _run("ablation-permitted:with", base)
    without_permitted = _run("ablation-permitted:without", clone_input(base, permitted_signal=None))
    assert with_permitted.gate.no_clean_routing != without_permitted.gate.no_clean_routing


def test_ablation_removing_precision_weighting_changes_gain_decision() -> None:
    base = w05_input_bundle("ablation-precision")
    observed_high = replace(base.observed_signal, evidence_precision=0.95)
    observed_low = replace(base.observed_signal, evidence_precision=0.15)
    high = _run("ablation-precision:high", clone_input(base, observed_signal=observed_high))
    low = _run("ablation-precision:low", clone_input(base, observed_signal=observed_low))
    assert _gain(high).effective_gain != _gain(low).effective_gain


def test_ablation_removing_source_reliability_changes_gain_or_confidence() -> None:
    base = w05_input_bundle("ablation-reliability")
    high = _run("ablation-reliability:high", base)
    low_predicted = replace(base.predicted_signal, source_reliability=0.1)
    low = _run("ablation-reliability:low", clone_input(base, predicted_signal=low_predicted))
    assert _gain(high).effective_gain != _gain(low).effective_gain


def test_ablation_removing_constitutional_guard_changes_route() -> None:
    base = w05_input_bundle("ablation-guard")
    blocked_permitted = replace(base.permitted_signal, protected_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE,))
    blocked = _run("ablation-guard:blocked", clone_input(base, permitted_signal=blocked_permitted))
    clear_permitted = replace(base.permitted_signal, protected_targets=())
    clear = _run("ablation-guard:clear", clone_input(base, permitted_signal=clear_permitted))
    assert _packet(blocked).must_escalate != _packet(clear).must_escalate


def test_ablation_removing_routing_execution_seam_fails_consumer_obedience() -> None:
    result = _run("ablation-seam", w05_input_bundle("ablation-seam"))
    packet = _packet(result)
    simulated_violation = packet.may_consider_update and packet.must_not_execute_update is False
    assert simulated_violation is False


def test_telemetry_reconstructs_prior_injection_and_routing_path() -> None:
    result = _run("telemetry", w05_input_bundle("telemetry"))
    telemetry = result.telemetry
    assert telemetry.signal_stack_count == 1
    assert telemetry.prediction_use_count == 1
    assert telemetry.must_not_execute_update_count == 1
