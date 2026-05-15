from __future__ import annotations

from dataclasses import replace

from substrate.w06_error_driven_revision.models import (
    W06AntiParalysisState,
    W06CausalCorrectionCandidate,
    W06ClaimBlockPacket,
    W06ConfidenceAdjustmentRecord,
    W06ConfidenceDropPolicy,
    W06ConsequenceType,
    W06ErrorType,
    W06DownstreamRevisionPermissionPacket,
    W06GateDecision,
    W06IdentityRevisionRecord,
    W06IdentityRoute,
    W06InputBundle,
    W06MismatchClass,
    W06OperationalConsequenceRecord,
    W06ResidualUncertaintyRecord,
    W06ResultBundle,
    W06RevisionDecision,
    W06RevisionLedgerEntry,
    W06RevisionScope,
    W06RouteStatus,
    W06ScopeMarker,
    W06TelemetryTrace,
    W06ViolatedExpectationSource,
)


def build_w06_error_driven_revision(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: W06InputBundle | None,
    enforcement_enabled: bool = True,
) -> W06ResultBundle:
    if not enforcement_enabled:
        return _minimal_result(
            bundle_id=f"w06:{tick_id}:bundle:none",
            reason="W06 gate disabled in test fixture",
            restriction_codes=("w06_disabled", "w06_no_clean_revision"),
        )
    if not isinstance(input_bundle, W06InputBundle):
        return _minimal_result(
            bundle_id=f"w06:{tick_id}:bundle:none",
            reason="w06 requires typed mismatch intake, lineage and revision context",
            restriction_codes=("insufficient_w06_basis", "w06_no_clean_revision"),
        )

    mismatch = input_bundle.mismatch_intake
    lineage = input_bundle.lineage_view
    context = input_bundle.revision_context
    contradictions = tuple(input_bundle.contradiction_intake)
    if mismatch is None or lineage is None or context is None:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="w06 typed intake is incomplete",
            restriction_codes=("incomplete_w06_intake", "w06_no_clean_revision"),
        )

    protected_target = bool(mismatch.constitutional_guard_flags) or (
        mismatch.target_layer in set(context.protected_targets)
    )
    has_unresolved_contradiction = any(item.unresolved_status for item in contradictions)
    contradiction_high = any(
        item.unresolved_status and _severity_rank(item.severity) >= _severity_rank("high")
        for item in contradictions
    )
    forced_global = _should_force_global_scope(
        mismatch=mismatch,
        context=context,
        has_unresolved_contradiction=has_unresolved_contradiction,
    )

    consequence_type, revision_scope, route_status, reason_codes = _select_consequence(
        mismatch=mismatch,
        protected_target=protected_target,
        has_unresolved_contradiction=has_unresolved_contradiction,
        contradiction_high=contradiction_high,
        forced_global=forced_global,
    )

    anti_paralysis = _build_anti_paralysis_state(
        context=context,
        current_consequence=consequence_type,
        reason_codes=reason_codes,
    )
    if anti_paralysis.chosen_escape_route is not W06ConsequenceType.REVALIDATE:
        consequence_type = anti_paralysis.chosen_escape_route
        if consequence_type is W06ConsequenceType.NARROW_CONTINUATION:
            revision_scope = W06RevisionScope.LOCAL
            route_status = W06RouteStatus.NARROW_CONTINUATION
        elif consequence_type is W06ConsequenceType.ESCALATE_REVIEW:
            revision_scope = W06RevisionScope.AUTHORITY_SCOPE_LEVEL
            route_status = W06RouteStatus.ESCALATED
        elif consequence_type is W06ConsequenceType.QUARANTINE:
            revision_scope = W06RevisionScope.LOCAL
            route_status = W06RouteStatus.QUARANTINED
        reason_codes = tuple(dict.fromkeys((*reason_codes, *anti_paralysis.reason_codes)))

    consequence_type, revision_scope, route_status, reason_codes = _enforce_allowed_revision_scope(
        consequence_type=consequence_type,
        revision_scope=revision_scope,
        route_status=route_status,
        context=context,
        mismatch=mismatch,
        reason_codes=reason_codes,
    )
    if _has_ambiguity(mismatch):
        if route_status is W06RouteStatus.CLEAN_REVISION_ROUTE:
            consequence_type = W06ConsequenceType.RETAIN_UNRESOLVED
            revision_scope = W06RevisionScope.LOCAL
            route_status = W06RouteStatus.CONTESTED_REVISION_ROUTE
        reason_codes = tuple(
            dict.fromkeys(
                (
                    *reason_codes,
                    "ambiguous_mismatch_retained",
                    "competing_revision_candidates_preserved",
                    "no_clean_revision_due_to_ambiguity",
                    "correction_candidate_suspected_only",
                )
            )
        )

    confidence = _build_confidence_adjustment(
        mismatch=mismatch,
        lineage=lineage,
        consequence=consequence_type,
        revision_scope=revision_scope,
    )
    if _has_ambiguity(mismatch) and confidence.new_confidence > 0.45:
        confidence = replace(confidence, new_confidence=0.45)
        reason_codes = tuple(dict.fromkeys((*reason_codes, "confidence_capped_due_to_ambiguity")))
    identity_revision = _build_identity_revision(
        mismatch=mismatch,
        contradictions=contradictions,
    )
    blocked_claim_types = _blocked_claim_types(
        mismatch=mismatch,
        consequence=consequence_type,
        identity=identity_revision,
        unresolved_contradiction=has_unresolved_contradiction,
    )

    prohibited_claims = tuple(
        dict.fromkeys(
            (
                *lineage.prohibited_claims,
                *blocked_claim_types,
                *(
                    ("stable_identity_claim_blocked",)
                    if identity_revision.continuity_claim_blocked
                    else ()
                ),
                "correction_execution_forbidden",
                "global_truth_overclaim_forbidden",
            )
        )
    )
    must_revalidate = consequence_type in {
        W06ConsequenceType.REVALIDATE,
        W06ConsequenceType.RETAIN_UNRESOLVED,
        W06ConsequenceType.NARROW_CONTINUATION,
    } or has_unresolved_contradiction
    must_block_claim = bool(blocked_claim_types)
    must_quarantine = consequence_type is W06ConsequenceType.QUARANTINE
    must_escalate = consequence_type is W06ConsequenceType.ESCALATE_REVIEW
    if _expects_claim_block(
        mismatch=mismatch,
        protected_target=protected_target,
        contradiction_high=contradiction_high,
    ) and not must_block_claim:
        blocked_claim_types = tuple(dict.fromkeys((*blocked_claim_types, "expected_claim_block_missing")))
        must_block_claim = True
        must_revalidate = True
        must_quarantine = True
        consequence_type = W06ConsequenceType.QUARANTINE
        route_status = W06RouteStatus.QUARANTINED
        revision_scope = W06RevisionScope.LOCAL
        reason_codes = tuple(dict.fromkeys((*reason_codes, "expected_claim_block_missing")))

    residue = _build_residual_uncertainty(
        tick_id=tick_id,
        mismatch=mismatch,
        consequence=consequence_type,
        prohibited_claims=prohibited_claims,
    )
    if must_block_claim and (not residue.visibility_to_downstream or not residue.retained_markers):
        must_revalidate = True
        must_quarantine = True
        consequence_type = W06ConsequenceType.QUARANTINE
        route_status = W06RouteStatus.QUARANTINED
        reason_codes = tuple(dict.fromkeys((*reason_codes, "claim_block_requires_residue_markers")))

    consequence = W06OperationalConsequenceRecord(
        consequence_type=consequence_type,
        revision_scope=revision_scope,
        criteria_passed=_criteria_passed(
            mismatch=mismatch,
            context=context,
            forced_global=forced_global,
            protected_target=protected_target,
        ),
        criteria_failed=_criteria_failed(
            mismatch=mismatch,
            context=context,
            forced_global=forced_global,
            protected_target=protected_target,
        ),
        affected_targets=(mismatch.target_layer,),
        allowed_continuation_scope=_allowed_continuation_scope(
            consequence_type=consequence_type,
            revision_scope=revision_scope,
            mismatch=mismatch,
        ),
        prohibited_claims=prohibited_claims,
        required_revalidation=must_revalidate,
        guardrail_flags=tuple(dict.fromkeys((*mismatch.constitutional_guard_flags, "must_not_execute_correction"))),
        reason_codes=reason_codes,
    )

    decision = W06RevisionDecision(
        revision_id=f"w06:{tick_id}:revision:1",
        source_mismatch_id=mismatch.mismatch_id,
        source_contradiction_id=contradictions[0].contradiction_id if contradictions else "",
        consequence_type=consequence_type,
        revision_scope=revision_scope,
        affected_targets=(mismatch.target_layer,),
        severity=mismatch.severity,
        confidence=mismatch.confidence,
        allowed_continuation_scope=consequence.allowed_continuation_scope,
        blocked_claims=blocked_claim_types,
        decision_reason_codes=reason_codes,
        route_status=route_status,
        audit_ref=f"w06:{tick_id}:audit:1",
    )

    confidence_drop_policy = _confidence_policy_for(consequence_type=consequence_type, confidence=confidence)
    downstream_effects: list[str] = ["must_not_execute_correction"]
    if must_block_claim:
        downstream_effects.append("must_block_claim")
    if must_revalidate:
        downstream_effects.append("must_revalidate")
    if must_quarantine:
        downstream_effects.append("must_quarantine")
    if must_escalate:
        downstream_effects.append("must_escalate")

    ledger = W06RevisionLedgerEntry(
        ledger_id=f"w06:{tick_id}:ledger:1",
        error_type=_error_type_for(mismatch=mismatch, contradiction_present=has_unresolved_contradiction),
        violated_expectation_source=_violated_source_for(mismatch=mismatch),
        revision_scope=revision_scope,
        confidence_drop_policy=confidence_drop_policy,
        retained_uncertainty_residue=residue.retained_markers,
        evidence_refs=tuple(dict.fromkeys((*mismatch.evidence_refs, *(lineage.negative_evidence_refs or ())))),
        prior_state_ref=lineage.prior_id or lineage.schema_id or "unknown_prior_state",
        new_state_ref=f"w06:{tick_id}:revision_candidate_state",
        downstream_permission_effects=tuple(dict.fromkeys(downstream_effects)),
        reason_codes=reason_codes,
        created_at_cycle=context.cycle_id,
    )

    claim_block = W06ClaimBlockPacket(
        affected_claim_ids=tuple(dict.fromkeys((lineage.prior_id, lineage.schema_id, mismatch.mismatch_id))),
        blocked_claim_types=blocked_claim_types,
        blocked_reason=_blocked_reason_for(
            consequence=consequence_type,
            unresolved_contradiction=has_unresolved_contradiction,
            protected_target=protected_target,
        ),
        required_revalidation=must_revalidate,
        downgrade_level=confidence.drop_or_hold_reason,
        downstream_must_abstain=must_block_claim or must_quarantine,
        allowed_narrow_claims=consequence.allowed_continuation_scope,
        provenance_preserved=tuple(dict.fromkeys((*lineage.negative_evidence_refs, *mismatch.provenance))),
    )

    correction_candidate = W06CausalCorrectionCandidate(
        candidate_id=f"w06:{tick_id}:correction:1",
        suspected_causal_error=mismatch.mismatch_class.value,
        target_scope=mismatch.target_scope or ("local_scope",),
        required_evidence=tuple(dict.fromkeys((*mismatch.evidence_refs, *lineage.negative_evidence_refs))),
        proposed_update_kind=mismatch.update_candidate_type or "causal_revision_candidate",
        guardrails=tuple(
            dict.fromkeys(
                (
                    "execution_prohibited",
                    "w06_route_only",
                    "respect_w04_w05_boundaries",
                    *mismatch.constitutional_guard_flags,
                )
            )
        ),
        execution_prohibited=True,
        owner_layer="W06",
        future_update_seam_ref="W07_or_later_update_executor",
        confidence=(
            min(
                max(0.0, min(1.0, mismatch.confidence * max(confidence.new_confidence, 0.1))),
                0.35,
            )
            if _has_ambiguity(mismatch)
            else max(0.0, min(1.0, mismatch.confidence * max(confidence.new_confidence, 0.1)))
        ),
        competing_candidates=mismatch.competing_class_candidates,
        residue_ref=residue.residue_id,
    )
    downstream = W06DownstreamRevisionPermissionPacket(
        may_continue_narrowly=consequence_type in {
            W06ConsequenceType.NARROW_CONTINUATION,
            W06ConsequenceType.RETAIN_UNRESOLVED,
            W06ConsequenceType.DOWNGRADE,
            W06ConsequenceType.REVALIDATE,
        },
        may_use_with_residue=consequence_type in {
            W06ConsequenceType.NARROW_CONTINUATION,
            W06ConsequenceType.RETAIN_UNRESOLVED,
            W06ConsequenceType.DOWNGRADE,
            W06ConsequenceType.REVALIDATE,
        },
        must_revalidate=must_revalidate,
        must_block_claim=must_block_claim,
        must_split_identity=identity_revision.identity_route is W06IdentityRoute.SPLIT_IDENTITY,
        must_not_execute_correction=True,
        must_escalate=must_escalate,
        must_quarantine=must_quarantine,
        preserved_uncertainty_markers=residue.retained_markers,
        prohibited_claims=prohibited_claims,
        correction_candidate_refs=(correction_candidate.candidate_id,),
        blocked_claim_packet_refs=((claim_block.blocked_reason and claim_block.blocked_reason) or "none",),
    )

    telemetry = W06TelemetryTrace(
        mismatch_intake_count=1,
        contradiction_intake_count=len(contradictions),
        consequence_matrix_count=1,
        revision_scope_count=1,
        confidence_policy_count=1,
        residue_retention_count=1,
        anti_paralysis_count=1 if anti_paralysis.repeated_revalidation_count >= anti_paralysis.loop_threshold else 0,
        identity_route_count=1 if identity_revision.identity_route is not W06IdentityRoute.NONE else 0,
        correction_candidate_count=1,
        downstream_packet_count=1,
        revalidate_count=1 if must_revalidate else 0,
        downgrade_count=1 if consequence_type is W06ConsequenceType.DOWNGRADE else 0,
        invalidate_count=1 if consequence_type is W06ConsequenceType.INVALIDATE else 0,
        split_identity_count=1 if identity_revision.identity_route is W06IdentityRoute.SPLIT_IDENTITY else 0,
        block_claim_count=1 if must_block_claim else 0,
        quarantine_count=1 if must_quarantine else 0,
        retain_unresolved_count=1 if consequence_type is W06ConsequenceType.RETAIN_UNRESOLVED else 0,
        global_scope_count=1 if revision_scope is W06RevisionScope.GLOBAL else 0,
        local_scope_count=1 if revision_scope in {W06RevisionScope.LOCAL, W06RevisionScope.OBJECT_LEVEL, W06RevisionScope.SCHEMA_LEVEL} else 0,
        confidence_drop_count=1 if confidence.new_confidence < confidence.prior_confidence else 0,
        must_not_execute_correction=True,
        claim_blocked=must_block_claim,
        consumer_ready=not must_block_claim and not must_quarantine,
        no_clean_revision=route_status is not W06RouteStatus.CLEAN_REVISION_ROUTE,
    )

    restrictions = [
        "w06_no_clean_revision" if telemetry.no_clean_revision else "w06_clean_revision_route",
        "w06_must_not_execute_correction_restriction",
    ]
    if must_block_claim:
        restrictions.append("w06_claim_blocked_restriction")
    if must_revalidate:
        restrictions.append("w06_revalidate_required_restriction")
    if residue.visibility_to_downstream:
        restrictions.append("w06_residual_uncertainty_restriction")
    if identity_revision.identity_route is W06IdentityRoute.SPLIT_IDENTITY:
        restrictions.append("w06_identity_split_restriction")
    if anti_paralysis.repeated_revalidation_count >= anti_paralysis.loop_threshold:
        restrictions.append("w06_anti_paralysis_restriction")
    if must_quarantine:
        restrictions.append("w06_quarantine_restriction")
    if must_escalate:
        restrictions.append("w06_escalate_restriction")

    gate = W06GateDecision(
        consumer_ready=telemetry.consumer_ready,
        no_clean_revision=telemetry.no_clean_revision,
        must_not_execute_correction=True,
        must_block_claim=must_block_claim,
        must_revalidate=must_revalidate,
        must_escalate=must_escalate,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys((*reason_codes, *restrictions))),
        reason="w06 emits revision consequences and forbids correction execution",
    )

    return W06ResultBundle(
        bundle_id=input_bundle.bundle_id,
        decision=decision,
        ledger=ledger,
        consequence=consequence,
        confidence_adjustment=confidence,
        residual_uncertainty=residue,
        anti_paralysis_state=anti_paralysis,
        identity_revision=identity_revision,
        claim_block_packet=claim_block,
        correction_candidate=correction_candidate,
        downstream_packet=downstream,
        telemetry=telemetry,
        gate=gate,
        scope_marker=W06ScopeMarker(
            scope="frontier_hosted_w06_error_driven_revision_slice",
            revision_routing_only=True,
            no_update_execution_claim=True,
            no_planner_claim=True,
            no_action_selector_claim=True,
            no_schema_mutation_claim=True,
            reason="w06 routes revision consequences only and forbids correction execution",
        ),
        no_claim_markers=(
            "w06_not_learner",
            "w06_not_planner",
            "w06_not_action_selector",
            "w06_not_update_executor",
            "w06_not_schema_editor",
        ),
        reason="w06 produced consequence routing, uncertainty residue and correction-candidate seam",
    )


def _select_consequence(
    *,
    mismatch,
    protected_target: bool,
    has_unresolved_contradiction: bool,
    contradiction_high: bool,
    forced_global: bool,
) -> tuple[W06ConsequenceType, W06RevisionScope, W06RouteStatus, tuple[str, ...]]:
    reason_codes: list[str] = []
    mismatch_class = mismatch.mismatch_class
    severity_rank = _severity_rank(mismatch.severity)

    if protected_target or mismatch_class is W06MismatchClass.CONSTITUTIONAL_BOUNDARY:
        reason_codes.append("protected_or_constitutional_boundary")
        consequence = (
            W06ConsequenceType.ESCALATE_REVIEW
            if severity_rank >= _severity_rank("high")
            else W06ConsequenceType.BLOCK_CLAIM
        )
        return (
            consequence,
            W06RevisionScope.AUTHORITY_SCOPE_LEVEL,
            W06RouteStatus.ESCALATED if consequence is W06ConsequenceType.ESCALATE_REVIEW else W06RouteStatus.BLOCKED,
            tuple(reason_codes),
        )

    if has_unresolved_contradiction and contradiction_high:
        reason_codes.append("unresolved_high_contradiction")
        return (
            W06ConsequenceType.BLOCK_CLAIM,
            W06RevisionScope.SCHEMA_LEVEL if mismatch_class in {W06MismatchClass.WORLD_MODEL, W06MismatchClass.PRIOR_VS_CURRENT_EVIDENCE} else W06RevisionScope.LOCAL,
            W06RouteStatus.BLOCKED,
            tuple(reason_codes),
        )

    if mismatch_class in {
        W06MismatchClass.MALFORMED_SIGNAL_STACK,
        W06MismatchClass.DESIRED_VS_PERMITTED,
        W06MismatchClass.OBSERVED_VS_PERMITTED,
        W06MismatchClass.AUTHORITY_SCOPE,
    }:
        reason_codes.append("permission_or_authority_mismatch")
        return (
            W06ConsequenceType.BLOCK_CLAIM,
            W06RevisionScope.AUTHORITY_SCOPE_LEVEL,
            W06RouteStatus.BLOCKED,
            tuple(reason_codes),
        )

    if mismatch_class in {W06MismatchClass.VALIDITY, W06MismatchClass.TEMPORAL_SCOPE}:
        reason_codes.append("validity_temporal_revalidation")
        return (
            W06ConsequenceType.REVALIDATE,
            W06RevisionScope.VALIDITY_LEVEL if mismatch_class is W06MismatchClass.VALIDITY else W06RevisionScope.TEMPORAL_WINDOW_LEVEL,
            W06RouteStatus.REVALIDATION_REQUIRED,
            tuple(reason_codes),
        )

    if mismatch_class in {W06MismatchClass.ACTION_EFFECT, W06MismatchClass.PREDICTED_VS_OBSERVED}:
        reason_codes.append("action_effect_route")
        if mismatch.evidence_precision >= 0.85 and mismatch.source_reliability >= 0.75:
            return (
                W06ConsequenceType.DOWNGRADE,
                W06RevisionScope.ACTION_EFFECT_LEVEL,
                W06RouteStatus.CORRECTION_CANDIDATE_ONLY,
                tuple(reason_codes),
            )
        return (
            W06ConsequenceType.REVALIDATE,
            W06RevisionScope.ACTION_EFFECT_LEVEL,
            W06RouteStatus.REVALIDATION_REQUIRED,
            tuple(reason_codes),
        )

    if mismatch_class in {W06MismatchClass.WORLD_MODEL, W06MismatchClass.PRIOR_VS_CURRENT_EVIDENCE}:
        reason_codes.append("world_model_route")
        if mismatch.evidence_precision <= 0.3 or mismatch.source_reliability <= 0.3:
            return (
                W06ConsequenceType.RETAIN_UNRESOLVED,
                W06RevisionScope.LOCAL,
                W06RouteStatus.CONTESTED_REVISION_ROUTE,
                tuple(reason_codes),
            )
        if forced_global:
            reason_codes.append("global_invalidation_criteria_met")
            return (
                W06ConsequenceType.INVALIDATE,
                W06RevisionScope.GLOBAL,
                W06RouteStatus.CLEAN_REVISION_ROUTE,
                tuple(reason_codes),
            )
        return (
            W06ConsequenceType.DOWNGRADE,
            W06RevisionScope.OBJECT_LEVEL,
            W06RouteStatus.CORRECTION_CANDIDATE_ONLY,
            tuple(reason_codes),
        )

    if mismatch_class is W06MismatchClass.AFFORDANCE:
        reason_codes.append("affordance_route")
        return (
            W06ConsequenceType.REVALIDATE if mismatch.evidence_precision < 0.8 else W06ConsequenceType.DOWNGRADE,
            W06RevisionScope.AFFORDANCE_LEVEL,
            W06RouteStatus.REVALIDATION_REQUIRED
            if mismatch.evidence_precision < 0.8
            else W06RouteStatus.CORRECTION_CANDIDATE_ONLY,
            tuple(reason_codes),
        )

    if mismatch_class is W06MismatchClass.OWNERSHIP:
        reason_codes.append("ownership_identity_route")
        return (
            W06ConsequenceType.SPLIT_IDENTITY,
            W06RevisionScope.OWNERSHIP_LEVEL,
            W06RouteStatus.CONTESTED_REVISION_ROUTE,
            tuple(reason_codes),
        )

    if mismatch_class is W06MismatchClass.GOAL_SATISFACTION:
        reason_codes.append("goal_satisfaction_review")
        return (
            W06ConsequenceType.REVALIDATE,
            W06RevisionScope.GOAL_SATISFACTION_LEVEL,
            W06RouteStatus.REVALIDATION_REQUIRED,
            tuple(reason_codes),
        )

    if mismatch_class is W06MismatchClass.AMBIGUOUS_MULTI_CLASS:
        reason_codes.append("ambiguous_multi_class")
        return (
            W06ConsequenceType.RETAIN_UNRESOLVED,
            W06RevisionScope.LOCAL,
            W06RouteStatus.CONTESTED_REVISION_ROUTE,
            tuple(reason_codes),
        )

    if mismatch_class is W06MismatchClass.INSUFFICIENT_EVIDENCE:
        reason_codes.append("insufficient_evidence")
        return (
            W06ConsequenceType.REVALIDATE,
            W06RevisionScope.LOCAL,
            W06RouteStatus.REVALIDATION_REQUIRED,
            tuple(reason_codes),
        )

    reason_codes.append("no_mismatch_narrow_continuation")
    return (
        W06ConsequenceType.NARROW_CONTINUATION,
        W06RevisionScope.LOCAL,
        W06RouteStatus.CLEAN_REVISION_ROUTE,
        tuple(reason_codes),
    )


def _should_force_global_scope(
    *,
    mismatch,
    context,
    has_unresolved_contradiction: bool,
) -> bool:
    if not context.global_revision_allowed:
        return False
    criteria = [
        _severity_rank(mismatch.severity) >= _severity_rank("high"),
        mismatch.confidence >= 0.85,
        len(tuple(dict.fromkeys(mismatch.evidence_refs))) >= 2,
        mismatch.target_scope and any("global" in item for item in mismatch.target_scope),
        has_unresolved_contradiction,
    ]
    return sum(1 for flag in criteria if flag) >= 4


def _enforce_allowed_revision_scope(
    *,
    consequence_type: W06ConsequenceType,
    revision_scope: W06RevisionScope,
    route_status: W06RouteStatus,
    context,
    mismatch,
    reason_codes: tuple[str, ...],
) -> tuple[W06ConsequenceType, W06RevisionScope, W06RouteStatus, tuple[str, ...]]:
    allowed = tuple(context.allowed_revision_scopes)
    if not allowed or revision_scope in allowed:
        return consequence_type, revision_scope, route_status, reason_codes
    narrowed_scope = (
        W06RevisionScope.LOCAL
        if W06RevisionScope.LOCAL in allowed
        else allowed[0]
    )
    reasons = [
        *reason_codes,
        "revision_scope_not_allowed",
        "selected_scope_outside_allowed_revision_scopes",
    ]
    if revision_scope is W06RevisionScope.GLOBAL:
        reasons.append("global_revision_scope_requires_explicit_criteria")
        reasons.append("global_revision_scope_blocked_without_criteria")
    reasons.append("narrowed_revision_scope_to_allowed_boundary")
    if consequence_type in {
        W06ConsequenceType.BLOCK_CLAIM,
        W06ConsequenceType.ESCALATE_REVIEW,
        W06ConsequenceType.QUARANTINE,
    }:
        return consequence_type, narrowed_scope, W06RouteStatus.BLOCKED, tuple(dict.fromkeys(reasons))
    return (
        W06ConsequenceType.REVALIDATE,
        narrowed_scope,
        W06RouteStatus.REVALIDATION_REQUIRED,
        tuple(dict.fromkeys(reasons)),
    )


def _has_ambiguity(mismatch) -> bool:
    return bool(
        mismatch.mismatch_class is W06MismatchClass.AMBIGUOUS_MULTI_CLASS
        or mismatch.ambiguity_markers
        or mismatch.competing_class_candidates
    )


def _expects_claim_block(
    *,
    mismatch,
    protected_target: bool,
    contradiction_high: bool,
) -> bool:
    if protected_target or contradiction_high:
        return True
    return mismatch.mismatch_class in {
        W06MismatchClass.AUTHORITY_SCOPE,
        W06MismatchClass.DESIRED_VS_PERMITTED,
        W06MismatchClass.OBSERVED_VS_PERMITTED,
        W06MismatchClass.MALFORMED_SIGNAL_STACK,
    }


def _severity_rank(label: str) -> int:
    table = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return table.get(str(label).lower().strip(), 2)


def _build_confidence_adjustment(
    *,
    mismatch,
    lineage,
    consequence: W06ConsequenceType,
    revision_scope: W06RevisionScope,
) -> W06ConfidenceAdjustmentRecord:
    prior = _band_to_confidence(lineage.confidence_band)
    severity_weight = _severity_rank(mismatch.severity) / 4.0
    precision_weight = max(0.0, min(1.0, mismatch.evidence_precision))
    reliability_weight = max(0.0, min(1.0, mismatch.source_reliability))
    base_drop = 0.05 + 0.35 * severity_weight * precision_weight * max(reliability_weight, 0.2)
    if consequence in {W06ConsequenceType.INVALIDATE, W06ConsequenceType.BLOCK_CLAIM, W06ConsequenceType.QUARANTINE}:
        base_drop += 0.2
    if revision_scope is W06RevisionScope.GLOBAL:
        base_drop += 0.1
    if mismatch.mismatch_class in {W06MismatchClass.INSUFFICIENT_EVIDENCE, W06MismatchClass.AMBIGUOUS_MULTI_CLASS}:
        base_drop *= 0.5
    if mismatch.evidence_precision <= 0.25:
        base_drop *= 0.4
    floor = 0.1
    ceiling = 0.99
    new = max(floor, min(ceiling, prior - base_drop))
    reason = (
        "confidence_hold_pending_revalidation"
        if consequence in {W06ConsequenceType.REVALIDATE, W06ConsequenceType.RETAIN_UNRESOLVED}
        else "confidence_drop_applied"
    )
    return W06ConfidenceAdjustmentRecord(
        target_id=lineage.prior_id or lineage.schema_id or "unknown_target",
        prior_confidence=prior,
        new_confidence=new,
        drop_or_hold_reason=reason,
        evidence_precision=mismatch.evidence_precision,
        source_reliability=mismatch.source_reliability,
        mismatch_severity=mismatch.severity,
        maturity_sensitivity=lineage.maturity_level or "unknown",
        floor_bound=floor,
        ceiling_bound=ceiling,
        global_collapse_prevented=revision_scope is not W06RevisionScope.GLOBAL,
    )


def _band_to_confidence(label: str) -> float:
    mapping = {
        "high": 0.85,
        "medium": 0.65,
        "low": 0.45,
        "uncertain": 0.35,
        "revoked": 0.2,
    }
    return mapping.get(str(label).lower().strip(), 0.4)


def _confidence_policy_for(
    *,
    consequence_type: W06ConsequenceType,
    confidence: W06ConfidenceAdjustmentRecord,
) -> W06ConfidenceDropPolicy:
    if consequence_type in {W06ConsequenceType.BLOCK_CLAIM, W06ConsequenceType.QUARANTINE}:
        return W06ConfidenceDropPolicy.BLOCK_CONFIDENCE_CLAIM
    if consequence_type is W06ConsequenceType.INVALIDATE:
        return W06ConfidenceDropPolicy.SEVERE_DROP
    if confidence.new_confidence >= confidence.prior_confidence:
        return W06ConfidenceDropPolicy.NO_DROP
    if consequence_type in {W06ConsequenceType.REVALIDATE, W06ConsequenceType.RETAIN_UNRESOLVED}:
        return W06ConfidenceDropPolicy.HOLD_PENDING_REVALIDATION
    delta = confidence.prior_confidence - confidence.new_confidence
    if delta >= 0.35:
        return W06ConfidenceDropPolicy.SEVERE_DROP
    if delta >= 0.2:
        return W06ConfidenceDropPolicy.MODERATE_DROP
    if delta >= 0.08:
        return W06ConfidenceDropPolicy.SMALL_DROP
    return W06ConfidenceDropPolicy.FLOOR_AT_UNCERTAIN


def _build_residual_uncertainty(
    *,
    tick_id: str,
    mismatch,
    consequence: W06ConsequenceType,
    prohibited_claims: tuple[str, ...],
) -> W06ResidualUncertaintyRecord:
    retained = [f"mismatch:{mismatch.mismatch_class.value}"]
    retained.extend(mismatch.ambiguity_markers)
    if mismatch.required_revalidation:
        retained.append("required_revalidation")
    if consequence in {
        W06ConsequenceType.REVALIDATE,
        W06ConsequenceType.RETAIN_UNRESOLVED,
        W06ConsequenceType.DOWNGRADE,
        W06ConsequenceType.CREATE_CAUSAL_CORRECTION_CANDIDATE,
        W06ConsequenceType.NARROW_CONTINUATION,
    }:
        retained.append("residual_uncertainty_visible")
    return W06ResidualUncertaintyRecord(
        residue_id=f"w06:{tick_id}:residue:1",
        residue_type="revision_residue",
        affected_scope=mismatch.target_scope or ("local_scope",),
        retained_markers=tuple(dict.fromkeys(retained)),
        future_trigger_conditions=("new_high_precision_evidence", "authority_revalidation", "temporal_refresh"),
        prohibited_claims=prohibited_claims,
        visibility_to_downstream=True,
        relevance_bound="bounded_scope",
        decay_or_release_condition="release_after_revalidation_and_consistent_evidence",
    )


def _build_anti_paralysis_state(*, context, current_consequence: W06ConsequenceType, reason_codes: tuple[str, ...]) -> W06AntiParalysisState:
    chosen = current_consequence
    escalation = False
    reasons = list(reason_codes)
    if (
        context.repeated_revalidation_count >= context.loop_threshold
        and not context.progress_detected
        and current_consequence is W06ConsequenceType.REVALIDATE
    ):
        if context.protected_targets:
            chosen = W06ConsequenceType.ESCALATE_REVIEW
            escalation = True
            reasons.append("anti_paralysis_escalate_review")
        else:
            chosen = W06ConsequenceType.NARROW_CONTINUATION
            reasons.append("anti_paralysis_narrow_continuation")
    elif context.progress_detected and current_consequence is W06ConsequenceType.REVALIDATE:
        reasons.append("revalidation_progress_detected")
    return W06AntiParalysisState(
        revalidation_loop_id=context.revalidation_loop_id,
        repeated_revalidation_count=context.repeated_revalidation_count,
        progress_detected=context.progress_detected,
        loop_threshold=context.loop_threshold,
        chosen_escape_route=chosen,
        bounded_continuation_permissions=("narrow_scope_only", "must_preserve_residue"),
        escalation_status=escalation,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def _build_identity_revision(*, mismatch, contradictions) -> W06IdentityRevisionRecord:
    route = W06IdentityRoute.NONE
    unknown_lineage = False
    continuity_blocked = False
    split = ""
    duplicate = ""
    replacement = ""
    merged = ""
    if mismatch.mismatch_class is W06MismatchClass.OWNERSHIP:
        route = W06IdentityRoute.SPLIT_IDENTITY
        split = f"{mismatch.mismatch_id}:split"
        continuity_blocked = True
    if mismatch.mismatch_class is W06MismatchClass.AMBIGUOUS_MULTI_CLASS:
        route = W06IdentityRoute.UNKNOWN_LINEAGE
        unknown_lineage = True
        continuity_blocked = True
    if any("duplicate" in item.conflict_type for item in contradictions):
        route = W06IdentityRoute.DUPLICATE_CANDIDATE
        duplicate = f"{mismatch.mismatch_id}:duplicate"
        continuity_blocked = True
    if any("replacement" in item.conflict_type for item in contradictions):
        route = W06IdentityRoute.REPLACEMENT_CANDIDATE
        replacement = f"{mismatch.mismatch_id}:replacement"
        continuity_blocked = True
    if any("merge" in item.conflict_type for item in contradictions):
        route = W06IdentityRoute.MERGED_IDENTITY_CANDIDATE
        merged = f"{mismatch.mismatch_id}:merge"
        continuity_blocked = True
    return W06IdentityRevisionRecord(
        affected_identity_candidate=mismatch.target_layer or "unknown_identity",
        same_instance_status="contested" if continuity_blocked else "provisionally_same",
        split_identity_candidate=split,
        duplicate_candidate=duplicate,
        replacement_candidate=replacement,
        merged_identity_candidate=merged,
        unknown_lineage_marker=unknown_lineage,
        required_future_evidence=("identity_disambiguation_evidence",),
        continuity_claim_blocked=continuity_blocked,
        identity_route=route,
    )


def _blocked_claim_types(
    *,
    mismatch,
    consequence: W06ConsequenceType,
    identity: W06IdentityRevisionRecord,
    unresolved_contradiction: bool,
) -> tuple[str, ...]:
    blocked: list[str] = []
    if consequence in {
        W06ConsequenceType.BLOCK_CLAIM,
        W06ConsequenceType.QUARANTINE,
        W06ConsequenceType.INVALIDATE,
    }:
        blocked.append("broad_claim_blocked")
    if mismatch.mismatch_class in {W06MismatchClass.AUTHORITY_SCOPE, W06MismatchClass.DESIRED_VS_PERMITTED, W06MismatchClass.OBSERVED_VS_PERMITTED}:
        blocked.append("authority_scope_claim_blocked")
    if mismatch.mismatch_class in {W06MismatchClass.WORLD_MODEL, W06MismatchClass.PRIOR_VS_CURRENT_EVIDENCE}:
        blocked.append("clean_world_claim_blocked")
    if unresolved_contradiction:
        blocked.append("contradiction_unresolved_claim_blocked")
    if identity.continuity_claim_blocked:
        blocked.append("stable_identity_claim_blocked")
    return tuple(dict.fromkeys(blocked))


def _allowed_continuation_scope(
    *,
    consequence_type: W06ConsequenceType,
    revision_scope: W06RevisionScope,
    mismatch,
) -> tuple[str, ...]:
    if consequence_type in {W06ConsequenceType.BLOCK_CLAIM, W06ConsequenceType.QUARANTINE, W06ConsequenceType.ESCALATE_REVIEW}:
        return ()
    if consequence_type in {W06ConsequenceType.NARROW_CONTINUATION, W06ConsequenceType.RETAIN_UNRESOLVED, W06ConsequenceType.REVALIDATE}:
        return tuple(dict.fromkeys(("scaffold_claim_only", *(mismatch.target_scope or ("local_scope",)))))
    if revision_scope is W06RevisionScope.GLOBAL:
        return ("global_revision_bound",)
    return mismatch.target_scope or ("local_scope",)


def _blocked_reason_for(
    *,
    consequence: W06ConsequenceType,
    unresolved_contradiction: bool,
    protected_target: bool,
) -> str:
    if protected_target:
        return "protected_target_or_constitutional_boundary"
    if consequence is W06ConsequenceType.QUARANTINE:
        return "quarantined_due_to_scope_risk"
    if consequence is W06ConsequenceType.BLOCK_CLAIM:
        return "claim_blocked_by_revision_policy"
    if consequence is W06ConsequenceType.INVALIDATE:
        return "invalidated_due_to_high_confidence_error"
    if unresolved_contradiction:
        return "unresolved_contradiction_requires_block"
    return "bounded_revision_route"


def _criteria_passed(*, mismatch, context, forced_global: bool, protected_target: bool) -> tuple[str, ...]:
    passed = ["typed_mismatch_intake_present", "typed_lineage_present", "typed_revision_context_present"]
    if mismatch.execution_prohibited:
        passed.append("upstream_execution_prohibited_preserved")
    if mismatch.required_revalidation:
        passed.append("upstream_revalidation_marker_present")
    if context.allowed_revision_scopes:
        passed.append("revision_scope_whitelist_present")
    if forced_global:
        passed.append("global_criteria_met")
    if protected_target:
        passed.append("protected_target_detected")
    return tuple(passed)


def _criteria_failed(*, mismatch, context, forced_global: bool, protected_target: bool) -> tuple[str, ...]:
    failed: list[str] = []
    if not mismatch.evidence_refs:
        failed.append("missing_evidence_refs")
    if mismatch.source_reliability <= 0.2:
        failed.append("weak_source_reliability")
    if mismatch.evidence_precision <= 0.2:
        failed.append("low_evidence_precision")
    if not forced_global:
        failed.append("global_criteria_not_met_or_not_allowed")
    if protected_target:
        failed.append("clean_correction_forbidden_for_protected_target")
    if context.global_revision_allowed is False:
        failed.append("global_revision_not_allowed")
    return tuple(dict.fromkeys(failed))


def _error_type_for(*, mismatch, contradiction_present: bool) -> W06ErrorType:
    if mismatch.mismatch_class is W06MismatchClass.CONSTITUTIONAL_BOUNDARY:
        return W06ErrorType.PROTECTED_BOUNDARY
    if mismatch.mismatch_class is W06MismatchClass.AUTHORITY_SCOPE:
        return W06ErrorType.AUTHORITY_CONFLICT
    if mismatch.mismatch_class is W06MismatchClass.TEMPORAL_SCOPE:
        return W06ErrorType.TEMPORAL_DRIFT
    if mismatch.mismatch_class is W06MismatchClass.OWNERSHIP:
        return W06ErrorType.IDENTITY_CONFLICT
    if mismatch.mismatch_class in {W06MismatchClass.INSUFFICIENT_EVIDENCE, W06MismatchClass.MALFORMED_SIGNAL_STACK}:
        return W06ErrorType.INSUFFICIENT_EVIDENCE
    if mismatch.mismatch_class is W06MismatchClass.AMBIGUOUS_MULTI_CLASS:
        return W06ErrorType.AMBIGUOUS_MISMATCH
    if contradiction_present:
        return W06ErrorType.CONTRADICTION
    return W06ErrorType.EXPECTATION_VIOLATION


def _violated_source_for(*, mismatch) -> W06ViolatedExpectationSource:
    mapping = {
        W06MismatchClass.DESIRED_VS_PERMITTED: W06ViolatedExpectationSource.PERMITTED,
        W06MismatchClass.OBSERVED_VS_PERMITTED: W06ViolatedExpectationSource.PERMITTED,
        W06MismatchClass.DESIRED_VS_PREDICTED: W06ViolatedExpectationSource.DESIRED,
        W06MismatchClass.PREDICTED_VS_OBSERVED: W06ViolatedExpectationSource.PREDICTED,
        W06MismatchClass.AUTHORITY_SCOPE: W06ViolatedExpectationSource.AUTHORITY_SCOPE,
        W06MismatchClass.TEMPORAL_SCOPE: W06ViolatedExpectationSource.TEMPORAL_WINDOW,
        W06MismatchClass.CONSTITUTIONAL_BOUNDARY: W06ViolatedExpectationSource.CONSTITUTIONAL_GUARD,
    }
    return mapping.get(mismatch.mismatch_class, W06ViolatedExpectationSource.PRIOR_SCHEMA_LINEAGE)


def _minimal_result(*, bundle_id: str, reason: str, restriction_codes: tuple[str, ...]) -> W06ResultBundle:
    decision = W06RevisionDecision(
        revision_id=f"{bundle_id}:revision:minimal",
        source_mismatch_id="",
        source_contradiction_id="",
        consequence_type=W06ConsequenceType.ABSTAIN,
        revision_scope=W06RevisionScope.LOCAL,
        affected_targets=(),
        severity="low",
        confidence=0.0,
        allowed_continuation_scope=(),
        blocked_claims=("insufficient_w06_basis",),
        decision_reason_codes=restriction_codes,
        route_status=W06RouteStatus.ABSTAIN,
        audit_ref=f"{bundle_id}:audit:minimal",
    )
    ledger = W06RevisionLedgerEntry(
        ledger_id=f"{bundle_id}:ledger:minimal",
        error_type=W06ErrorType.INSUFFICIENT_EVIDENCE,
        violated_expectation_source=W06ViolatedExpectationSource.PRIOR_SCHEMA_LINEAGE,
        revision_scope=W06RevisionScope.LOCAL,
        confidence_drop_policy=W06ConfidenceDropPolicy.HOLD_PENDING_REVALIDATION,
        retained_uncertainty_residue=("insufficient_w06_basis",),
        evidence_refs=(),
        prior_state_ref="unknown",
        new_state_ref="unknown",
        downstream_permission_effects=("must_not_execute_correction",),
        reason_codes=restriction_codes,
        created_at_cycle="",
    )
    consequence = W06OperationalConsequenceRecord(
        consequence_type=W06ConsequenceType.ABSTAIN,
        revision_scope=W06RevisionScope.LOCAL,
        criteria_passed=("none",),
        criteria_failed=("insufficient_basis",),
        affected_targets=(),
        allowed_continuation_scope=(),
        prohibited_claims=("global_truth_overclaim_forbidden",),
        required_revalidation=True,
        guardrail_flags=("must_not_execute_correction",),
        reason_codes=restriction_codes,
    )
    confidence = W06ConfidenceAdjustmentRecord(
        target_id="unknown_target",
        prior_confidence=0.0,
        new_confidence=0.0,
        drop_or_hold_reason="insufficient_basis",
        evidence_precision=0.0,
        source_reliability=0.0,
        mismatch_severity="low",
        maturity_sensitivity="unknown",
        floor_bound=0.0,
        ceiling_bound=1.0,
        global_collapse_prevented=True,
    )
    residue = W06ResidualUncertaintyRecord(
        residue_id=f"{bundle_id}:residue:minimal",
        residue_type="insufficient_basis_residue",
        affected_scope=("unknown",),
        retained_markers=("insufficient_w06_basis",),
        future_trigger_conditions=("typed_w06_input_required",),
        prohibited_claims=("global_truth_overclaim_forbidden",),
        visibility_to_downstream=True,
        relevance_bound="unknown",
        decay_or_release_condition="release_after_typed_basis",
    )
    anti = W06AntiParalysisState(
        revalidation_loop_id="",
        repeated_revalidation_count=0,
        progress_detected=False,
        loop_threshold=3,
        chosen_escape_route=W06ConsequenceType.ABSTAIN,
        bounded_continuation_permissions=(),
        escalation_status=False,
        reason_codes=("insufficient_basis",),
    )
    identity = W06IdentityRevisionRecord(
        affected_identity_candidate="",
        same_instance_status="unknown",
        split_identity_candidate="",
        duplicate_candidate="",
        replacement_candidate="",
        merged_identity_candidate="",
        unknown_lineage_marker=True,
        required_future_evidence=("typed_identity_basis",),
        continuity_claim_blocked=True,
        identity_route=W06IdentityRoute.UNKNOWN_LINEAGE,
    )
    claim_block = W06ClaimBlockPacket(
        affected_claim_ids=(),
        blocked_claim_types=("insufficient_w06_basis",),
        blocked_reason="insufficient_w06_basis",
        required_revalidation=True,
        downgrade_level="unknown",
        downstream_must_abstain=True,
        allowed_narrow_claims=(),
        provenance_preserved=(),
    )
    correction = W06CausalCorrectionCandidate(
        candidate_id=f"{bundle_id}:correction:minimal",
        suspected_causal_error="insufficient_basis",
        target_scope=("unknown",),
        required_evidence=("typed_w06_input",),
        proposed_update_kind="none",
        guardrails=("execution_prohibited",),
        execution_prohibited=True,
        owner_layer="W06",
        future_update_seam_ref="W07_or_later_update_executor",
        confidence=0.0,
        competing_candidates=(),
        residue_ref=residue.residue_id,
    )
    downstream = W06DownstreamRevisionPermissionPacket(
        may_continue_narrowly=False,
        may_use_with_residue=False,
        must_revalidate=True,
        must_block_claim=True,
        must_split_identity=True,
        must_not_execute_correction=True,
        must_escalate=False,
        must_quarantine=False,
        preserved_uncertainty_markers=residue.retained_markers,
        prohibited_claims=("global_truth_overclaim_forbidden",),
        correction_candidate_refs=(correction.candidate_id,),
        blocked_claim_packet_refs=("insufficient_w06_basis",),
    )
    telemetry = W06TelemetryTrace(
        mismatch_intake_count=0,
        contradiction_intake_count=0,
        consequence_matrix_count=0,
        revision_scope_count=0,
        confidence_policy_count=0,
        residue_retention_count=1,
        anti_paralysis_count=0,
        identity_route_count=1,
        correction_candidate_count=1,
        downstream_packet_count=1,
        revalidate_count=1,
        downgrade_count=0,
        invalidate_count=0,
        split_identity_count=1,
        block_claim_count=1,
        quarantine_count=0,
        retain_unresolved_count=0,
        global_scope_count=0,
        local_scope_count=1,
        confidence_drop_count=0,
        must_not_execute_correction=True,
        claim_blocked=True,
        consumer_ready=False,
        no_clean_revision=True,
    )
    gate = W06GateDecision(
        consumer_ready=False,
        no_clean_revision=True,
        must_not_execute_correction=True,
        must_block_claim=True,
        must_revalidate=True,
        must_escalate=False,
        required_restrictions=restriction_codes,
        reason_codes=restriction_codes,
        reason=reason,
    )
    return W06ResultBundle(
        bundle_id=bundle_id,
        decision=decision,
        ledger=ledger,
        consequence=consequence,
        confidence_adjustment=confidence,
        residual_uncertainty=residue,
        anti_paralysis_state=anti,
        identity_revision=identity,
        claim_block_packet=claim_block,
        correction_candidate=correction,
        downstream_packet=downstream,
        telemetry=telemetry,
        gate=gate,
        scope_marker=W06ScopeMarker(
            scope="frontier_hosted_w06_error_driven_revision_slice",
            revision_routing_only=True,
            no_update_execution_claim=True,
            no_planner_claim=True,
            no_action_selector_claim=True,
            no_schema_mutation_claim=True,
            reason=reason,
        ),
        no_claim_markers=(
            "w06_not_learner",
            "w06_not_planner",
            "w06_not_action_selector",
            "w06_not_update_executor",
            "w06_not_schema_editor",
        ),
        reason=reason,
    )
