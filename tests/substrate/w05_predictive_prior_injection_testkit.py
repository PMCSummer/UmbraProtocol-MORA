from __future__ import annotations

from dataclasses import replace

from substrate.w05_predictive_prior_injection import (
    W05DesiredSignal,
    W05InjectionTarget,
    W05InputBundle,
    W05ObservedSignal,
    W05PermittedSignal,
    W05PredictedSignal,
    W05PriorGainControlConfig,
    W05ResultBundle,
    build_w05_predictive_prior_injection,
)


def w05_desired_signal(case_id: str, **overrides) -> W05DesiredSignal:
    base = W05DesiredSignal(
        signal_id=f"{case_id}:desired:signal",
        desired_state_id=f"{case_id}:desired",
        requested_outcome="bounded_alignment",
        actor_id="actor_a",
        perspective_id="self",
        priority="normal",
        source_authority="trusted_authority",
        provenance=("tests.w05", case_id, "desired"),
        allowed_relaxation_fields=("soft_conflict",),
        non_negotiable_constraints=("hard_non_negotiable",),
        forbidden_update_targets=(),
        malformed_markers=(),
        target_scope=("bounded_scope",),
        confidence=0.6,
        precision=0.6,
        uncertainty_markers=(),
    )
    return replace(base, **overrides)


def w05_predicted_signal(case_id: str, **overrides) -> W05PredictedSignal:
    base = W05PredictedSignal(
        signal_id=f"{case_id}:predicted:signal",
        prediction_id=f"{case_id}:prediction",
        prior_id=f"{case_id}:prior",
        expected_observation="obs:expected",
        expected_action_effect="effect:expected",
        expected_affordance="affordance:expected",
        expected_goal_satisfaction="bounded_alignment",
        expected_validity_window=(1, 10),
        prior_strength=0.8,
        prediction_confidence=0.8,
        source_reliability=0.85,
        source_authority="trusted_authority",
        provenance=("tests.w05", case_id, "predicted"),
        target_scope=("bounded_scope",),
        confidence=0.8,
        precision=0.7,
        timestamp_or_sequence=1,
        uncertainty_markers=(),
    )
    return replace(base, **overrides)


def w05_observed_signal(case_id: str, **overrides) -> W05ObservedSignal:
    base = W05ObservedSignal(
        signal_id=f"{case_id}:observed:signal",
        observation_id=f"{case_id}:observation",
        observation_refs=(f"{case_id}:obs:1",),
        observed_outcome="obs:expected",
        observed_action_effect="effect:expected",
        observed_affordance="affordance:expected",
        evidence_precision=0.75,
        source_reliability=0.8,
        source_authority="trusted_authority",
        presence_mode="present",
        timestamp_or_sequence=2,
        contradiction_markers=(),
        provenance=("tests.w05", case_id, "observed"),
        target_scope=("bounded_scope",),
        confidence=0.8,
        precision=0.75,
        uncertainty_markers=(),
    )
    return replace(base, **overrides)


def w05_permitted_signal(case_id: str, **overrides) -> W05PermittedSignal:
    base = W05PermittedSignal(
        signal_id=f"{case_id}:permitted:signal",
        permitted_signal_id=f"{case_id}:permitted",
        w04_decision_ref=f"{case_id}:w04:decision",
        permitted_status="allowed",
        may_deploy_candidate=True,
        may_use_as_hint_only=False,
        may_use_after_revalidation=False,
        may_use_with_relaxation=False,
        must_abstain=False,
        must_block=False,
        must_revalidate=False,
        prohibited_uses=("no_action_authorization",),
        protected_targets=(W05InjectionTarget.PROTECTED_CONSTITUTIONAL_LAYER,),
        non_learnable_layer_flags=("constitutional_locked",),
        allowed_update_targets=(W05InjectionTarget.INTERPRETATION_INTERFACE, W05InjectionTarget.POLICY_INTERFACE),
        prohibited_update_targets=(W05InjectionTarget.PROTECTED_CONSTITUTIONAL_LAYER,),
        constitutional_guard_flags=("preserve_constitution",),
        source_authority="trusted_authority",
        provenance=("tests.w05", case_id, "permitted"),
        target_scope=("bounded_scope",),
        confidence=1.0,
        precision=1.0,
        timestamp_or_sequence=2,
        uncertainty_markers=(),
    )
    return replace(base, **overrides)


def w05_gain_config(**overrides) -> W05PriorGainControlConfig:
    base = W05PriorGainControlConfig(
        prior_strength_policy="bounded_linear",
        evidence_precision_policy="precision_weighted",
        source_reliability_interaction_matrix=("reliable_amplify", "weak_suppress"),
        suppress_conditions=("high_precision_contradiction", "permitted_block"),
        amplify_conditions=("high_reliability_and_consistency",),
        maximum_gain=1.0,
        minimum_gain=0.0,
        high_precision_contradiction_threshold=0.8,
        low_precision_noise_threshold=0.25,
        protected_target_gain_cap=0.2,
        reason_codes=("w05.1_gain_control",),
    )
    return replace(base, **overrides)


def w05_input_bundle(case_id: str, **overrides) -> W05InputBundle:
    base = W05InputBundle(
        bundle_id=f"{case_id}:w05:bundle",
        source_lineage=("tests.w05", case_id),
        w04_decision_ref=f"{case_id}:w04:decision",
        w03_prior_ref=f"{case_id}:w03:prior",
        desired_signal=w05_desired_signal(case_id),
        predicted_signal=w05_predicted_signal(case_id),
        observed_signal=w05_observed_signal(case_id),
        permitted_signal=w05_permitted_signal(case_id),
        prior_gain_config=w05_gain_config(),
        protected_target_registry=(W05InjectionTarget.PROTECTED_CONSTITUTIONAL_LAYER,),
        reason=case_id,
    )
    return replace(base, **overrides)


def build_w05_harness(case_id: str, *, input_bundle: W05InputBundle | None, enforcement_enabled: bool = True) -> W05ResultBundle:
    return build_w05_predictive_prior_injection(
        tick_id=f"tests.w05:{case_id}",
        tick_index=1,
        input_bundle=input_bundle,
        enforcement_enabled=enforcement_enabled,
    )


def clone_input(base: W05InputBundle, **changes) -> W05InputBundle:
    return replace(base, **changes)


def w05_input_from_w04_result(*, case_id: str, w04_result) -> W05InputBundle:
    packet = next(iter(tuple(getattr(w04_result, "downstream_permission_packets", ()))), None)
    decision = next(iter(tuple(getattr(w04_result, "applicability_decisions", ()))), None)
    if packet is None:
        return w05_input_bundle(case_id)
    predicted = w05_predicted_signal(
        case_id,
        prior_id=str(getattr(decision, "prior_id", f"{case_id}:prior")),
    )
    permitted = w05_permitted_signal(
        case_id,
        w04_decision_ref=str(getattr(packet, "decision_id", f"{case_id}:w04:decision")),
        permitted_status="allowed" if bool(getattr(packet, "may_deploy_candidate", False)) else "restricted",
        may_deploy_candidate=bool(getattr(packet, "may_deploy_candidate", False)),
        may_use_as_hint_only=bool(getattr(packet, "may_use_as_hint_only", False)),
        may_use_after_revalidation=bool(getattr(packet, "may_use_after_revalidation", False)),
        may_use_with_relaxation=bool(getattr(packet, "may_use_with_relaxation", False)),
        must_abstain=bool(getattr(packet, "must_abstain", False)),
        must_block=bool(getattr(packet, "must_block", False)),
        must_revalidate=bool(getattr(packet, "must_revalidate", False)),
        prohibited_uses=tuple(getattr(packet, "prohibited_uses", ())),
    )
    return w05_input_bundle(case_id, predicted_signal=predicted, permitted_signal=permitted)
