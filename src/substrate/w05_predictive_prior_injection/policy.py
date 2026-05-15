from __future__ import annotations

from substrate.w05_predictive_prior_injection.models import (
    W05ConstitutionalGuardCheck,
    W05DownstreamRoutingPermissionPacket,
    W05GateDecision,
    W05InjectionTarget,
    W05InputBundle,
    W05MismatchClass,
    W05MismatchClassificationRecord,
    W05MismatchDirection,
    W05PermittedChannelEnforcementRecord,
    W05PermittedSignal,
    W05PredictionUseRecord,
    W05PriorGainControlConfig,
    W05PriorGainDecision,
    W05ResultBundle,
    W05RevalidationOrEscalationRequest,
    W05ScopeMarker,
    W05SignalChannel,
    W05Telemetry,
    W05TypedSignalStackRecord,
    W05UpdateRoutingPacket,
)


def build_w05_predictive_prior_injection(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: W05InputBundle | None,
    enforcement_enabled: bool = True,
) -> W05ResultBundle:
    if not enforcement_enabled:
        return _minimal_result(
            bundle_id=f"w05:{tick_id}:bundle:none",
            reason="W05 gate disabled in test fixture",
            restrictions=("w05_disabled", "w05_no_clean_routing"),
        )

    if not isinstance(input_bundle, W05InputBundle):
        return _minimal_result(
            bundle_id=f"w05:{tick_id}:bundle:none",
            reason="w05 requires typed w04 decision, four-channel stack and gain config",
            restrictions=("insufficient_w05_basis", "w05_no_clean_routing"),
        )

    desired = input_bundle.desired_signal
    predicted = input_bundle.predicted_signal
    observed = input_bundle.observed_signal
    permitted = input_bundle.permitted_signal
    config = input_bundle.prior_gain_config

    missing_markers: list[str] = []
    if desired is None:
        missing_markers.append("missing_desired_channel")
    if predicted is None:
        missing_markers.append("missing_predicted_channel")
    if observed is None:
        missing_markers.append("missing_observed_channel")
    if permitted is None:
        missing_markers.append("missing_permitted_channel")
    if config is None:
        missing_markers.append("missing_gain_config")

    if missing_markers:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="w05 missing typed channel inputs and cannot emit clean routing",
            restrictions=tuple(dict.fromkeys(("w05_no_clean_routing", *missing_markers))),
        )

    assert desired is not None
    assert predicted is not None
    assert observed is not None
    assert permitted is not None
    assert config is not None

    collapse_reasons = _channel_collapse_reasons(
        desired=desired,
        predicted=predicted,
        observed=observed,
        permitted=permitted,
    )
    collapsed = bool(collapse_reasons)
    stack = W05TypedSignalStackRecord(
        stack_id=f"w05:{tick_id}:stack:1",
        desired_signal=desired,
        predicted_signal=predicted,
        observed_signal=observed,
        permitted_signal=permitted,
        per_channel_provenance=(
            (W05SignalChannel.DESIRED, desired.provenance),
            (W05SignalChannel.PREDICTED, predicted.provenance),
            (W05SignalChannel.OBSERVED, observed.provenance),
            (W05SignalChannel.PERMITTED, permitted.provenance),
        ),
        per_channel_authority=(
            (W05SignalChannel.DESIRED, desired.source_authority),
            (W05SignalChannel.PREDICTED, predicted.source_authority),
            (W05SignalChannel.OBSERVED, observed.source_authority),
            (W05SignalChannel.PERMITTED, permitted.source_authority),
        ),
        per_channel_confidence=(
            (W05SignalChannel.DESIRED, desired.confidence),
            (W05SignalChannel.PREDICTED, predicted.confidence),
            (W05SignalChannel.OBSERVED, observed.confidence),
            (W05SignalChannel.PERMITTED, permitted.confidence),
        ),
        per_channel_precision=(
            (W05SignalChannel.DESIRED, desired.precision),
            (W05SignalChannel.PREDICTED, predicted.precision),
            (W05SignalChannel.OBSERVED, observed.evidence_precision),
            (W05SignalChannel.PERMITTED, permitted.precision),
        ),
        mismatch_readiness=not collapsed,
        channel_integrity_status="collapsed" if collapsed else "separated",
        missing_channel_markers=collapse_reasons,
        collapsed_channel_guard=collapsed,
    )

    gain = _derive_gain(predicted=predicted, observed=observed, permitted=permitted, config=config)
    mismatch = _classify_mismatch(
        desired=desired,
        predicted=predicted,
        observed=observed,
        permitted=permitted,
        gain=gain,
        collapsed=collapsed,
        collapse_reasons=collapse_reasons,
        tick_id=tick_id,
    )

    target = mismatch.target_scope_candidate
    protected_blocked = target in tuple(dict.fromkeys((*permitted.protected_targets, *input_bundle.protected_target_registry)))
    guard = _build_guard(permitted=permitted, target=target, protected_blocked=protected_blocked)

    permitted_block = _blocked_by_permitted(permitted=permitted)
    must_revalidate = _must_revalidate(permitted=permitted, mismatch=mismatch, observed=observed, gain=gain)
    must_escalate = bool(guard.escalation_required or mismatch.mismatch_class is W05MismatchClass.CONSTITUTIONAL_BOUNDARY)
    must_abstain = bool(collapsed or permitted_block or permitted.must_abstain)

    may_consider_update = (
        not must_abstain
        and not must_escalate
        and not must_revalidate
        and not protected_blocked
        and mismatch.mismatch_class is not W05MismatchClass.MALFORMED_SIGNAL_STACK
        and permitted.may_deploy_candidate
    )

    prediction_use = W05PredictionUseRecord(
        prediction_use_id=f"w05:{tick_id}:prediction_use:1",
        prior_id=predicted.prior_id,
        w04_decision_ref=permitted.w04_decision_ref,
        injection_target=target,
        allowed_scope=permitted.target_scope,
        prior_strength=predicted.prior_strength,
        effective_prior_gain=gain.effective_gain,
        evidence_precision=observed.evidence_precision,
        source_reliability_interaction="weighted",
        suppress_or_amplify_reason=(gain.suppression_reason or gain.amplification_reason or "unchanged"),
        constitutional_guard_status=guard.guard_status,
        permitted_boundary=permitted.permitted_status,
        gain_bounds=gain.gain_bounds,
        reason_codes=gain.reason_codes,
    )

    routing = W05UpdateRoutingPacket(
        routing_id=f"w05:{tick_id}:routing:1",
        mismatch_class=mismatch.mismatch_class,
        target_scope=permitted.target_scope,
        target_layer=target,
        update_candidate_type="bounded_update_candidate",
        severity=mismatch.severity,
        confidence=mismatch.confidence,
        evidence_refs=mismatch.evidence_refs,
        recommended_route=("escalate_guard_review" if must_escalate else "revalidate_and_route" if must_revalidate else "route_candidate"),
        required_revalidation=must_revalidate,
        execution_prohibited=True,
        constitutional_guard_flags=permitted.constitutional_guard_flags,
        protected_target_blocked=protected_blocked,
        permitted_channel_status=permitted.permitted_status,
        downstream_must_not_execute_update=True,
        reason_codes=tuple(dict.fromkeys((*mismatch.reason_codes, *(gain.reason_codes)))),
    )

    enforcement = W05PermittedChannelEnforcementRecord(
        permitted_status=permitted.permitted_status,
        prohibited_uses=permitted.prohibited_uses,
        utility_not_permission=True,
        desired_not_permission=True,
        prediction_not_permission=True,
        blocked_by_w04=permitted_block,
        downstream_permission_delta=(
            "blocked_by_w04" if permitted_block else "bounded_routing_only",
        ),
        reason_codes=("utility_not_permission", "desired_not_permission", "prediction_not_permission"),
    )

    revalidation_requests: tuple[W05RevalidationOrEscalationRequest, ...] = ()
    if must_revalidate or must_escalate:
        revalidation_requests = (
            W05RevalidationOrEscalationRequest(
                request_id=f"w05:{tick_id}:recheck:1",
                target_scope=permitted.target_scope,
                required_upstream_layer="W04" if permitted.must_revalidate else "W03",
                missing_evidence=(() if observed.provenance else ("observed_provenance_missing",)),
                ambiguous_mismatch_reason=("ambiguous_multi_class" if mismatch.mismatch_class is W05MismatchClass.AMBIGUOUS_MULTI_CLASS else ""),
                constitutional_concern=must_escalate,
                route_priority=desired.priority,
                blocked_until_revalidated=True,
            ),
        )

    prohibited_uses = tuple(
        dict.fromkeys(
            (
                *permitted.prohibited_uses,
                "update_execution_from_w05",
                "action_authorization_from_w05",
                "desired_as_evidence",
                "predicted_utility_as_permission",
            )
        )
    )
    preserved_guardrails = tuple(
        dict.fromkeys(
            (
                *permitted.prohibited_uses,
                *permitted.non_learnable_layer_flags,
                "preserve_w04_permission_boundary",
                "must_not_execute_update",
            )
        )
    )

    packet = W05DownstreamRoutingPermissionPacket(
        routing_id=routing.routing_id,
        may_consider_update=may_consider_update,
        may_request_learning=may_consider_update,
        may_adjust_interpretation=may_consider_update and target is W05InjectionTarget.INTERPRETATION_INTERFACE,
        may_adjust_policy_hint=may_consider_update and target is W05InjectionTarget.POLICY_INTERFACE,
        must_revalidate=must_revalidate,
        must_escalate=must_escalate,
        must_abstain=must_abstain,
        must_not_execute_update=True,
        must_preserve_desired_predicted_observed_permitted_separation=True,
        must_preserve_guardrails=True,
        protected_target_blocked=protected_blocked,
        prohibited_uses=prohibited_uses,
        preserved_guardrails=preserved_guardrails,
        execution_authorization_granted=False,
    )

    telemetry = W05Telemetry(
        signal_stack_count=1,
        prediction_use_count=1,
        prior_gain_suppressed_count=1 if gain.suppressed else 0,
        prior_gain_amplified_count=1 if gain.amplified else 0,
        prior_gain_unchanged_count=1 if gain.unchanged else 0,
        mismatch_count=0 if mismatch.mismatch_class is W05MismatchClass.NO_MISMATCH else 1,
        ambiguous_mismatch_count=1 if mismatch.mismatch_class is W05MismatchClass.AMBIGUOUS_MULTI_CLASS else 0,
        revalidate_route_count=1 if must_revalidate else 0,
        escalate_route_count=1 if must_escalate else 0,
        abstain_count=1 if must_abstain else 0,
        constitutional_guard_count=1 if guard.guard_status != "clear" else 0,
        protected_target_block_count=1 if protected_blocked else 0,
        must_not_execute_update_count=1,
        permitted_channel_block_count=1 if permitted_block else 0,
        channel_collapse_block_count=1 if collapsed else 0,
        consumer_ready=may_consider_update,
        no_clean_routing=not may_consider_update,
    )

    restrictions = []
    if telemetry.no_clean_routing:
        restrictions.append("w05_no_clean_routing")
    if telemetry.permitted_channel_block_count > 0:
        restrictions.append("w05_permitted_channel_block")
    if telemetry.channel_collapse_block_count > 0:
        restrictions.append("w05_channel_collapse_block")
    if telemetry.revalidate_route_count > 0:
        restrictions.append("w05_revalidate_route")
    if telemetry.escalate_route_count > 0:
        restrictions.append("w05_escalate_route")
    if telemetry.ambiguous_mismatch_count > 0:
        restrictions.append("w05_ambiguous_mismatch")
    if telemetry.constitutional_guard_count > 0:
        restrictions.append("w05_constitutional_guard")
    if telemetry.protected_target_block_count > 0:
        restrictions.append("w05_protected_target_block")
    if telemetry.prior_gain_suppressed_count > 0:
        restrictions.append("w05_prior_gain_suppressed")
    if telemetry.abstain_count > 0:
        restrictions.append("w05_must_abstain")

    gate = W05GateDecision(
        consumer_ready=telemetry.consumer_ready,
        no_clean_routing=telemetry.no_clean_routing,
        must_not_execute_update_count=telemetry.must_not_execute_update_count,
        revalidate_route_count=telemetry.revalidate_route_count,
        escalate_route_count=telemetry.escalate_route_count,
        abstain_count=telemetry.abstain_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(restrictions or ["w05_route_candidate"])),
        reason="w05 emits predictive prior injection routing and blocks update execution",
    )

    return W05ResultBundle(
        bundle_id=input_bundle.bundle_id,
        signal_stacks=(stack,),
        prediction_use_records=(prediction_use,),
        prior_gain_decisions=(gain,),
        mismatch_classifications=(mismatch,),
        update_routing_packets=(routing,),
        constitutional_guard_checks=(guard,),
        permitted_channel_enforcement_records=(enforcement,),
        revalidation_or_escalation_requests=revalidation_requests,
        downstream_routing_packets=(packet,),
        telemetry=telemetry,
        gate=gate,
        scope_marker=W05ScopeMarker(
            scope="frontier_hosted_w05_predictive_prior_injection_slice",
            prior_injection_only=True,
            no_w06_revision_claim=True,
            no_planner_claim=True,
            no_action_selector_claim=True,
            no_execution_claim=True,
            reason="w05 routes predictive pressure only and forbids execution",
        ),
        no_claim_markers=(
            "w05_not_w06",
            "w05_not_planner",
            "w05_not_action_selector",
            "w05_not_execution_authorizer",
        ),
        reason="w05 produced separated-channel routing packets with execution_prohibited seam",
    )


def _derive_gain(*, predicted, observed, permitted: W05PermittedSignal, config: W05PriorGainControlConfig) -> W05PriorGainDecision:
    min_gain = config.minimum_gain
    max_gain = config.maximum_gain
    effective = predicted.prior_strength * observed.evidence_precision * max(predicted.source_reliability, 0.0)
    suppressed = False
    amplified = False
    suppression_reason = ""
    amplification_reason = ""
    reasons: list[str] = []

    if observed.contradiction_markers and observed.evidence_precision >= config.high_precision_contradiction_threshold:
        effective = min_gain
        suppressed = True
        suppression_reason = "high_precision_contradiction"
        reasons.append("high_precision_contradiction_suppressed")
    elif observed.evidence_precision <= config.low_precision_noise_threshold:
        reasons.append("low_precision_noise_contested")
    elif predicted.source_reliability >= 0.8 and predicted.prior_strength >= 0.7:
        effective = min(max_gain, effective + 0.1)
        amplified = True
        amplification_reason = "reliable_source_amplified"
        reasons.append("source_reliability_amplified")

    if permitted.must_block or permitted.must_abstain:
        effective = min_gain
        suppressed = True
        suppression_reason = suppression_reason or "blocked_by_permitted_channel"
        reasons.append("permitted_channel_block")

    if permitted.protected_targets:
        effective = min(effective, config.protected_target_gain_cap)
        reasons.append("protected_target_gain_cap")

    effective = max(min_gain, min(max_gain, effective))
    unchanged = not suppressed and not amplified
    if unchanged:
        reasons.append("gain_unchanged")

    return W05PriorGainDecision(
        prior_strength=predicted.prior_strength,
        evidence_precision=observed.evidence_precision,
        source_reliability_score=predicted.source_reliability,
        effective_gain=effective,
        gain_bounds=(min_gain, max_gain),
        suppressed=suppressed,
        amplified=amplified,
        unchanged=unchanged,
        suppression_reason=suppression_reason,
        amplification_reason=amplification_reason,
        reason_codes=tuple(dict.fromkeys(reasons)),
        residual_uncertainty=tuple(observed.uncertainty_markers),
    )


def _classify_mismatch(
    *,
    desired,
    predicted,
    observed,
    permitted,
    gain,
    collapsed: bool,
    collapse_reasons: tuple[str, ...],
    tick_id: str,
) -> W05MismatchClassificationRecord:
    if collapsed:
        mismatch_class = W05MismatchClass.MALFORMED_SIGNAL_STACK
        direction = W05MismatchDirection.DESIRED_VS_PREDICTED
        candidates = (W05MismatchClass.MALFORMED_SIGNAL_STACK,)
        target = W05InjectionTarget.INTERPRETATION_INTERFACE
        compared_channels = (
            W05SignalChannel.DESIRED,
            W05SignalChannel.PREDICTED,
            W05SignalChannel.OBSERVED,
            W05SignalChannel.PERMITTED,
        )
        reason = tuple(dict.fromkeys(("collapsed_signal_channels", *collapse_reasons)))
    elif permitted.must_block or permitted.must_abstain:
        mismatch_class = W05MismatchClass.DESIRED_VS_PERMITTED
        direction = W05MismatchDirection.DESIRED_VS_PERMITTED
        candidates = (W05MismatchClass.DESIRED_VS_PERMITTED, W05MismatchClass.AUTHORITY_SCOPE)
        target = W05InjectionTarget.POLICY_INTERFACE
        compared_channels = (W05SignalChannel.DESIRED, W05SignalChannel.PERMITTED)
        reason = ("w04_blocked_or_abstain",)
    elif desired.requested_outcome != predicted.expected_goal_satisfaction:
        mismatch_class = W05MismatchClass.DESIRED_VS_PREDICTED
        direction = W05MismatchDirection.DESIRED_VS_PREDICTED
        candidates = (W05MismatchClass.DESIRED_VS_PREDICTED,)
        target = W05InjectionTarget.GOAL_SATISFACTION_MODEL
        compared_channels = (W05SignalChannel.DESIRED, W05SignalChannel.PREDICTED)
        reason = ("desired_predicted_divergence",)
    elif (
        observed.contradiction_markers
        and observed.evidence_precision >= 0.8
        and predicted.expected_observation != observed.observed_outcome
    ):
        mismatch_class = W05MismatchClass.AMBIGUOUS_MULTI_CLASS
        direction = W05MismatchDirection.PRIOR_VS_CURRENT_EVIDENCE
        candidates = (
            W05MismatchClass.WORLD_MODEL,
            W05MismatchClass.AFFORDANCE,
            W05MismatchClass.VALIDITY,
        )
        target = W05InjectionTarget.VALIDITY_MODEL
        compared_channels = (W05SignalChannel.PREDICTED, W05SignalChannel.OBSERVED)
        reason = ("contradictory_evidence_ambiguous",)
    elif predicted.expected_observation != observed.observed_outcome:
        mismatch_class = W05MismatchClass.PREDICTED_VS_OBSERVED
        direction = W05MismatchDirection.PREDICTED_VS_OBSERVED
        candidates = (W05MismatchClass.WORLD_MODEL, W05MismatchClass.AFFORDANCE)
        target = (
            W05InjectionTarget.AFFORDANCE_MODEL
            if predicted.expected_affordance != observed.observed_affordance
            else W05InjectionTarget.WORLD_MODEL_INTERFACE
        )
        compared_channels = (W05SignalChannel.PREDICTED, W05SignalChannel.OBSERVED)
        reason = ("predicted_observed_divergence",)
    elif predicted.expected_validity_window and observed.timestamp_or_sequence > predicted.expected_validity_window[1]:
        mismatch_class = W05MismatchClass.TEMPORAL_SCOPE
        direction = W05MismatchDirection.PRIOR_VS_CURRENT_EVIDENCE
        candidates = (W05MismatchClass.TEMPORAL_SCOPE, W05MismatchClass.VALIDITY)
        target = W05InjectionTarget.VALIDITY_MODEL
        compared_channels = (W05SignalChannel.PREDICTED, W05SignalChannel.OBSERVED)
        reason = ("temporal_scope_mismatch",)
    elif permitted.source_authority and permitted.source_authority != observed.source_authority:
        mismatch_class = W05MismatchClass.AUTHORITY_SCOPE
        direction = W05MismatchDirection.OBSERVED_VS_PERMITTED
        candidates = (W05MismatchClass.AUTHORITY_SCOPE,)
        target = W05InjectionTarget.OWNERSHIP_MODEL
        compared_channels = (W05SignalChannel.OBSERVED, W05SignalChannel.PERMITTED)
        reason = ("observed_permitted_authority_mismatch",)
    elif not observed.provenance:
        mismatch_class = W05MismatchClass.INSUFFICIENT_EVIDENCE
        direction = W05MismatchDirection.PRIOR_VS_CURRENT_EVIDENCE
        candidates = (W05MismatchClass.INSUFFICIENT_EVIDENCE,)
        target = W05InjectionTarget.VALIDITY_MODEL
        compared_channels = (W05SignalChannel.PREDICTED, W05SignalChannel.OBSERVED)
        reason = ("observation_provenance_missing",)
    elif gain.suppressed and observed.contradiction_markers:
        mismatch_class = W05MismatchClass.AMBIGUOUS_MULTI_CLASS
        direction = W05MismatchDirection.PRIOR_VS_CURRENT_EVIDENCE
        candidates = (W05MismatchClass.WORLD_MODEL, W05MismatchClass.AFFORDANCE, W05MismatchClass.VALIDITY)
        target = W05InjectionTarget.VALIDITY_MODEL
        compared_channels = (W05SignalChannel.PREDICTED, W05SignalChannel.OBSERVED)
        reason = ("contradictory_evidence_ambiguous",)
    else:
        mismatch_class = W05MismatchClass.NO_MISMATCH
        direction = W05MismatchDirection.PRIOR_VS_CURRENT_EVIDENCE
        candidates = (W05MismatchClass.NO_MISMATCH,)
        target = W05InjectionTarget.INTERPRETATION_INTERFACE
        compared_channels = (W05SignalChannel.PREDICTED, W05SignalChannel.OBSERVED)
        reason = ("no_mismatch_detected",)

    return W05MismatchClassificationRecord(
        mismatch_id=f"w05:{tick_id}:mismatch:1",
        compared_channels=compared_channels,
        mismatch_class=mismatch_class,
        mismatch_direction=direction,
        severity="high" if mismatch_class in {W05MismatchClass.CONSTITUTIONAL_BOUNDARY, W05MismatchClass.MALFORMED_SIGNAL_STACK} else "medium" if mismatch_class is not W05MismatchClass.NO_MISMATCH else "low",
        confidence=0.8 if mismatch_class is not W05MismatchClass.AMBIGUOUS_MULTI_CLASS else 0.5,
        evidence_refs=tuple(dict.fromkeys((*observed.observation_refs, *observed.contradiction_markers))),
        ambiguity_markers=("ambiguous_classification",) if mismatch_class is W05MismatchClass.AMBIGUOUS_MULTI_CLASS else (),
        competing_class_candidates=candidates,
        target_scope_candidate=target,
        reason_codes=reason,
        execution_prohibited=True,
    )


def _build_guard(*, permitted: W05PermittedSignal, target: W05InjectionTarget, protected_blocked: bool) -> W05ConstitutionalGuardCheck:
    protected_targets = tuple(dict.fromkeys((*permitted.protected_targets, *permitted.prohibited_update_targets)))
    attempted = (target,)
    blocked = (target,) if protected_blocked or target in permitted.prohibited_update_targets else ()
    allowed = () if blocked else (target,)
    escalation_required = bool(blocked or target is W05InjectionTarget.PROTECTED_CONSTITUTIONAL_LAYER)
    return W05ConstitutionalGuardCheck(
        protected_targets=protected_targets,
        attempted_update_targets=attempted,
        blocked_targets=blocked,
        allowed_routing_targets=allowed,
        non_learnable_layer_flags=permitted.non_learnable_layer_flags,
        violation_reason="protected_target_blocked" if blocked else "",
        guard_status="blocked" if blocked else "clear",
        escalation_required=escalation_required,
        reason_codes=("protected_target_blocked",) if blocked else ("guard_clear",),
    )


def _channel_collapse_reasons(*, desired, predicted, observed, permitted) -> tuple[str, ...]:
    reasons: list[str] = []
    ids = (
        str(desired.signal_id),
        str(predicted.signal_id),
        str(observed.signal_id),
        str(permitted.signal_id),
    )
    if len(set(ids)) < 4:
        reasons.append("duplicate_signal_id_across_channels")

    expected_channels = (
        (desired, W05SignalChannel.DESIRED, "desired_channel_marker_mismatch"),
        (predicted, W05SignalChannel.PREDICTED, "predicted_channel_marker_mismatch"),
        (observed, W05SignalChannel.OBSERVED, "observed_channel_marker_mismatch"),
        (permitted, W05SignalChannel.PERMITTED, "permitted_channel_marker_mismatch"),
    )
    for signal, expected, marker in expected_channels:
        if getattr(signal, "channel", expected) is not expected:
            reasons.extend(("channel_marker_mismatch", marker))

    if (
        desired.requested_outcome
        and desired.requested_outcome == observed.observed_outcome
        and desired.provenance == observed.provenance
        and not observed.observation_refs
    ):
        reasons.append("desired_observed_collapse_suspected")

    if predicted.prediction_id == permitted.permitted_signal_id:
        reasons.append("predicted_permitted_collapse_suspected")
    elif predicted.provenance == permitted.provenance and not str(permitted.w04_decision_ref).strip():
        reasons.extend(
            (
                "predicted_permitted_collapse_suspected",
                "missing_w04_permission_boundary",
            )
        )

    if observed.observation_id == permitted.permitted_signal_id:
        reasons.append("observed_permitted_collapse_suspected")
    elif observed.provenance == permitted.provenance and not str(permitted.w04_decision_ref).strip():
        reasons.extend(
            (
                "observed_permitted_collapse_suspected",
                "missing_w04_permission_boundary",
            )
        )

    return tuple(dict.fromkeys(reasons))


def _blocked_by_permitted(*, permitted: W05PermittedSignal) -> bool:
    return bool(
        permitted.must_block
        or permitted.must_abstain
        or permitted.must_revalidate
        or not permitted.may_deploy_candidate
    )


def _must_revalidate(*, permitted: W05PermittedSignal, mismatch, observed, gain) -> bool:
    if permitted.must_revalidate or permitted.may_use_after_revalidation:
        return True
    if mismatch.mismatch_class in {
        W05MismatchClass.AMBIGUOUS_MULTI_CLASS,
        W05MismatchClass.INSUFFICIENT_EVIDENCE,
        W05MismatchClass.AUTHORITY_SCOPE,
        W05MismatchClass.TEMPORAL_SCOPE,
        W05MismatchClass.VALIDITY,
    }:
        return True
    if observed.evidence_precision < 0.3:
        return True
    if gain.suppressed and observed.contradiction_markers:
        return True
    return False


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> W05ResultBundle:
    telemetry = W05Telemetry(
        signal_stack_count=0,
        prediction_use_count=0,
        prior_gain_suppressed_count=0,
        prior_gain_amplified_count=0,
        prior_gain_unchanged_count=0,
        mismatch_count=0,
        ambiguous_mismatch_count=0,
        revalidate_route_count=0,
        escalate_route_count=0,
        abstain_count=1,
        constitutional_guard_count=0,
        protected_target_block_count=0,
        must_not_execute_update_count=0,
        permitted_channel_block_count=0,
        channel_collapse_block_count=0,
        consumer_ready=False,
        no_clean_routing=True,
    )
    gate = W05GateDecision(
        consumer_ready=False,
        no_clean_routing=True,
        must_not_execute_update_count=0,
        revalidate_route_count=0,
        escalate_route_count=0,
        abstain_count=1,
        required_restrictions=restrictions,
        reason_codes=("w05_no_clean_routing",),
        reason=reason,
    )
    return W05ResultBundle(
        bundle_id=bundle_id,
        signal_stacks=(),
        prediction_use_records=(),
        prior_gain_decisions=(),
        mismatch_classifications=(),
        update_routing_packets=(),
        constitutional_guard_checks=(),
        permitted_channel_enforcement_records=(),
        revalidation_or_escalation_requests=(),
        downstream_routing_packets=(),
        telemetry=telemetry,
        gate=gate,
        scope_marker=W05ScopeMarker(
            scope="frontier_hosted_w05_predictive_prior_injection_slice",
            prior_injection_only=True,
            no_w06_revision_claim=True,
            no_planner_claim=True,
            no_action_selector_claim=True,
            no_execution_claim=True,
            reason=reason,
        ),
        no_claim_markers=(
            "w05_not_w06",
            "w05_not_planner",
            "w05_not_action_selector",
            "w05_not_execution_authorizer",
        ),
        reason=reason,
    )
