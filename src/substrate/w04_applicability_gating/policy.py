from __future__ import annotations

from substrate.w04_applicability_gating.models import (
    W04ActiveApplicabilityContext,
    W04ApplicabilityDecision,
    W04ApplicabilityDecisionStatus,
    W04BlockedApplicabilityRecord,
    W04Constraint,
    W04ConstraintEvaluationRecord,
    W04ConstraintEvaluationStatus,
    W04ConstraintHardness,
    W04ConstraintProfile,
    W04ConstraintType,
    W04DesiredStateRequest,
    W04DownstreamApplicabilityPermissionPacket,
    W04GateDecision,
    W04InputBundle,
    W04IntersectionAssessment,
    W04PerspectiveFrame,
    W04PerspectiveSafetyRecord,
    W04RelaxationLedgerEntry,
    W04ResultBundle,
    W04RevalidationRequest,
    W04ScopeMarker,
    W04Telemetry,
    W04W03IntakeView,
)


def build_w04_applicability_gating(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: W04InputBundle | None,
    enforcement_enabled: bool = True,
) -> W04ResultBundle:
    if not enforcement_enabled:
        return _minimal_result(
            bundle_id=f"w04:{tick_id}:bundle:none",
            reason="W04 gate disabled in test fixture",
            restrictions=("w04_disabled", "w04_no_clean_applicability"),
        )

    if not isinstance(input_bundle, W04InputBundle):
        return _minimal_result(
            bundle_id=f"w04:{tick_id}:bundle:none",
            reason="w04 requires typed w03 intake views plus desired-state/context/perspective/constraints",
            restrictions=("insufficient_w04_basis", "w04_no_clean_applicability"),
        )

    if not input_bundle.w03_intake_views:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="w04 received no w03 intake views and cannot emit clean applicability",
            restrictions=("w04_no_w03_support", "w04_no_clean_applicability"),
        )

    desired = input_bundle.desired_state_request
    context = input_bundle.active_context
    frame = input_bundle.perspective_frame
    profile = input_bundle.constraint_profile

    if desired is None or context is None or frame is None or profile is None:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="w04 missing desired-state/context/perspective/constraint profile and cannot emit clean applicability",
            restrictions=("w04_missing_required_inputs", "w04_no_clean_applicability"),
        )

    decisions: list[W04ApplicabilityDecision] = []
    assessments: list[W04IntersectionAssessment] = []
    eval_records_all: list[W04ConstraintEvaluationRecord] = []
    perspective_records: list[W04PerspectiveSafetyRecord] = []
    relaxations_all: list[W04RelaxationLedgerEntry] = []
    revalidation_requests: list[W04RevalidationRequest] = []
    blocked_records: list[W04BlockedApplicabilityRecord] = []
    packets: list[W04DownstreamApplicabilityPermissionPacket] = []

    for index, intake in enumerate(input_bundle.w03_intake_views, start=1):
        decision_id = f"w04:{tick_id}:{index}"
        eval_records, hard_failures, soft_conflicts, unknown_hard = _evaluate_constraints(
            constraints=_flatten_constraints(profile),
            desired=desired,
            context=context,
            frame=frame,
            intake=intake,
        )
        eval_records_all.extend(eval_records)

        perspective_blocked = _is_perspective_blocked(frame=frame, desired=desired, intake=intake)
        authority_blocked = _is_authority_blocked(desired=desired, intake=intake)
        temporal_blocked = _is_temporal_blocked(desired=desired, context=context, intake=intake)
        desired_malformed_reasons = _desired_state_malformed_reasons(desired)

        perspective_record = W04PerspectiveSafetyRecord(
            actor_scope=frame.actor_scope,
            observer_scope=frame.observer_scope,
            subject_scope=frame.subject_scope,
            source_perspective=frame.source_perspective,
            requested_perspective=frame.requested_perspective,
            allowed_perspective_transfer=frame.allowed_perspective_transfer,
            blocked_transfer=perspective_blocked,
            authority_boundary=frame.authority_boundary,
            leakage_risk=frame.leakage_risk,
            reason_codes=("perspective_checked", "blocked" if perspective_blocked else "allowed"),
        )
        perspective_records.append(perspective_record)

        status, blocked_reason = _derive_decision_status(
            intake=intake,
            desired=desired,
            hard_failures=hard_failures,
            soft_conflicts=soft_conflicts,
            unknown_hard=unknown_hard,
            perspective_blocked=perspective_blocked,
            authority_blocked=authority_blocked,
            temporal_blocked=temporal_blocked,
            desired_malformed_reasons=desired_malformed_reasons,
        )

        relaxation_entries: tuple[W04RelaxationLedgerEntry, ...] = ()
        if status in {
            W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION,
            W04ApplicabilityDecisionStatus.RELAXABLE,
        }:
            relaxation_entries = _build_relaxation_ledger(
                tick_id=tick_id,
                decision_id=decision_id,
                desired=desired,
                soft_conflicts=soft_conflicts,
                hard_failures=hard_failures,
            )
            relaxations_all.extend(relaxation_entries)

        must_revalidate = status in {
            W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED,
            W04ApplicabilityDecisionStatus.HINT_ONLY,
        }
        if must_revalidate:
            revalidation_requests.append(
                W04RevalidationRequest(
                    request_id=f"revalidate:{decision_id}",
                    target_schema_or_prior=intake.prior_id or intake.schema_id,
                    reason=blocked_reason or "w04_revalidation_required",
                    missing_evidence=("fresh_context",) if temporal_blocked else (),
                    stale_field="stale_or_revalidation_status",
                    contradiction_ref=";".join(intake.contradiction_status),
                    required_upstream_layer="W03",
                    deadline_or_priority=desired.priority,
                    blocked_until_revalidated=True,
                )
            )

        assessment = W04IntersectionAssessment(
            assessment_id=f"assessment:{decision_id}",
            evaluated_constraint_ids=tuple(item.constraint_id for item in eval_records),
            hard_constraint_results=tuple(
                item.enforcement_action
                for item in eval_records
                if item.hard_or_soft
                in {W04ConstraintHardness.HARD, W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED}
            ),
            soft_constraint_results=tuple(
                item.enforcement_action
                for item in eval_records
                if item.hard_or_soft is W04ConstraintHardness.SOFT
            ),
            empty_intersection_status="empty_hard" if hard_failures or unknown_hard else "non_empty",
            feasible_region=("bounded_context",)
            if status
            in {
                W04ApplicabilityDecisionStatus.ALLOWED,
                W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION,
                W04ApplicabilityDecisionStatus.NARROWED,
            }
            else (),
            infeasible_region=tuple(dict.fromkeys((*hard_failures, *unknown_hard))),
            unknown_region=unknown_hard,
            narrowed_applicability_conditions=("bounded_by_w03_scope",)
            if status in {W04ApplicabilityDecisionStatus.NARROWED, W04ApplicabilityDecisionStatus.HINT_ONLY}
            else (),
            hard_failure_ids=hard_failures,
            soft_conflict_ids=soft_conflicts,
            unknown_hard_ids=unknown_hard,
            reason_codes=_reason_codes_from_status(status=status, blocked_reason=blocked_reason),
        )
        assessments.append(assessment)

        packet = _build_packet(
            decision_id=decision_id,
            intake=intake,
            status=status,
            blocked_reason=blocked_reason,
            hard_failures=hard_failures,
            unknown_hard=unknown_hard,
            perspective_blocked=perspective_blocked,
            authority_blocked=authority_blocked,
            temporal_blocked=temporal_blocked,
            relaxation_entries=relaxation_entries,
            desired=desired,
        )
        packets.append(packet)

        if status in {
            W04ApplicabilityDecisionStatus.BLOCKED,
            W04ApplicabilityDecisionStatus.ABSTAIN,
            W04ApplicabilityDecisionStatus.MALFORMED_REQUEST,
            W04ApplicabilityDecisionStatus.NO_CLEAN_APPLICABILITY,
        }:
            blocked_records.append(
                W04BlockedApplicabilityRecord(
                    blocked_reason=blocked_reason or status.value,
                    violated_hard_constraints=hard_failures,
                    malformed_desired_state_markers=tuple(
                        dict.fromkeys((*desired.malformed_markers, *desired_malformed_reasons))
                    ),
                    authority_scope_violation=authority_blocked,
                    temporal_violation=temporal_blocked,
                    perspective_violation=perspective_blocked,
                    unknown_hard_feasibility=bool(unknown_hard),
                    downstream_abstain_requirement=packet.must_abstain,
                    reason_codes=packet.decision_reason_codes,
                )
            )

        decisions.append(
            W04ApplicabilityDecision(
                decision_id=decision_id,
                candidate_id=intake.candidate_id,
                schema_id=intake.schema_id,
                prior_id=intake.prior_id,
                desired_state_id=desired.desired_state_id,
                decision_status=status,
                allowed_scope=("bounded_context",) if packet.may_deploy_candidate else (),
                blocked_scope=("full_scope",) if packet.must_block else (),
                narrowed_scope=("hint_only_scope",)
                if status
                in {W04ApplicabilityDecisionStatus.NARROWED, W04ApplicabilityDecisionStatus.HINT_ONLY}
                else (),
                decision_reason_codes=packet.decision_reason_codes,
                blocked_reason=packet.blocked_reason,
                confidence_band="high" if packet.may_deploy_candidate else "low",
                audit_ref=f"{tick_id}:{intake.schema_id}:{desired.desired_state_id}",
                intersection_assessment=assessment,
                constraint_evaluations=tuple(eval_records),
                perspective_safety=perspective_record,
                relaxation_ledger=relaxation_entries,
                revalidation_requests=tuple(
                    req
                    for req in revalidation_requests
                    if req.target_schema_or_prior in {intake.prior_id, intake.schema_id}
                ),
                downstream_permission_packet=packet,
                no_claim_markers=(
                    "w04_not_planner",
                    "w04_not_action_selector",
                    "w04_not_world_model",
                    "w04_not_w05_or_w06",
                ),
            )
        )

    telemetry = _build_telemetry(
        desired=desired,
        intakes=input_bundle.w03_intake_views,
        decisions=tuple(decisions),
        packets=tuple(packets),
        eval_records=tuple(eval_records_all),
        blocked_records=tuple(blocked_records),
    )

    restrictions: list[str] = []
    if telemetry.no_clean_applicability:
        restrictions.append("w04_no_clean_applicability")
    if telemetry.hard_constraint_failure_count > 0:
        restrictions.append("w04_hard_constraint_failure")
    if telemetry.unknown_hard_count > 0:
        restrictions.append("w04_unknown_hard_feasibility")
    if telemetry.revalidate_required_count > 0:
        restrictions.append("w04_revalidation_required")
    if telemetry.abstain_count > 0:
        restrictions.append("w04_must_abstain")
    if telemetry.malformed_desired_state_count > 0:
        restrictions.append("w04_malformed_desired_state")
    if telemetry.perspective_block_count > 0:
        restrictions.append("w04_perspective_scope_violation")
    if telemetry.authority_block_count > 0:
        restrictions.append("w04_authority_scope_violation")
    if telemetry.stale_block_count > 0:
        restrictions.append("w04_stale_or_temporal_block")
    if telemetry.relaxation_count > 0:
        restrictions.append("w04_relaxation_route")

    gate = W04GateDecision(
        consumer_ready=telemetry.consumer_ready,
        no_clean_applicability=telemetry.no_clean_applicability,
        blocked_count=telemetry.blocked_count,
        revalidate_required_count=telemetry.revalidate_required_count,
        abstain_count=telemetry.abstain_count,
        hard_constraint_failure_count=telemetry.hard_constraint_failure_count,
        unknown_hard_count=telemetry.unknown_hard_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(restrictions or ["w04_allowed"])),
        reason="w04 computes bounded applicability gating without planner/action authorization",
    )

    return W04ResultBundle(
        bundle_id=input_bundle.bundle_id,
        applicability_decisions=tuple(decisions),
        intersection_assessments=tuple(assessments),
        constraint_evaluations=tuple(eval_records_all),
        perspective_safety_records=tuple(perspective_records),
        relaxation_ledger_entries=tuple(relaxations_all),
        revalidation_requests=tuple(revalidation_requests),
        blocked_records=tuple(blocked_records),
        downstream_permission_packets=tuple(packets),
        telemetry=telemetry,
        gate=gate,
        scope_marker=W04ScopeMarker(
            scope="frontier_hosted_w04_applicability_gating_slice",
            applicability_gating_only=True,
            no_planner_claim=True,
            no_action_selector_claim=True,
            no_world_model_expansion_claim=True,
            no_w05_or_w06_claim=True,
            reason="w04 gates applicability only and does not authorize actions or modify upstream schema content",
        ),
        no_claim_markers=(
            "w04_not_planner",
            "w04_not_action_selector",
            "w04_not_world_model",
            "w04_not_w05_or_w06",
        ),
        reason="w04 produced applicability gating decisions with perspective-safe constraint intersection",
    )


def _flatten_constraints(profile: W04ConstraintProfile) -> tuple[W04Constraint, ...]:
    return tuple(
        item
        for bucket in (
            profile.world_constraints,
            profile.legality_constraints,
            profile.epistemic_constraints,
            profile.temporal_constraints,
            profile.perspective_constraints,
            profile.authority_constraints,
            profile.safety_constraints,
            profile.downstream_contract_constraints,
        )
        for item in bucket
    )


def _evaluate_constraints(
    *,
    constraints: tuple[W04Constraint, ...],
    desired: W04DesiredStateRequest,
    context: W04ActiveApplicabilityContext,
    frame: W04PerspectiveFrame,
    intake: W04W03IntakeView,
) -> tuple[
    list[W04ConstraintEvaluationRecord],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    records: list[W04ConstraintEvaluationRecord] = []
    hard_failures: list[str] = []
    soft_conflicts: list[str] = []
    unknown_hard: list[str] = []

    for constraint in constraints:
        status = _evaluate_constraint_status(
            constraint=constraint,
            desired=desired,
            context=context,
            frame=frame,
            intake=intake,
        )
        passed = status in {
            W04ConstraintEvaluationStatus.PASSED,
            W04ConstraintEvaluationStatus.NOT_APPLICABLE,
        }
        failed = status in {
            W04ConstraintEvaluationStatus.FAILED,
            W04ConstraintEvaluationStatus.MALFORMED,
            W04ConstraintEvaluationStatus.AUTHORITY_MISMATCH,
            W04ConstraintEvaluationStatus.PERSPECTIVE_MISMATCH,
            W04ConstraintEvaluationStatus.TEMPORAL_INVALID,
            W04ConstraintEvaluationStatus.BLOCKED_BY_UPSTREAM_PERMISSION,
            W04ConstraintEvaluationStatus.STALE,
        }
        unknown = status is W04ConstraintEvaluationStatus.UNKNOWN

        if constraint.hard_or_soft in {W04ConstraintHardness.HARD, W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED}:
            if failed:
                hard_failures.append(constraint.constraint_id)
            if unknown or constraint.hard_or_soft is W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED:
                if status is not W04ConstraintEvaluationStatus.PASSED:
                    unknown_hard.append(constraint.constraint_id)
        elif constraint.hard_or_soft is W04ConstraintHardness.SOFT and failed:
            soft_conflicts.append(constraint.constraint_id)

        records.append(
            W04ConstraintEvaluationRecord(
                constraint_id=constraint.constraint_id,
                constraint_type=constraint.constraint_type,
                hard_or_soft=constraint.hard_or_soft,
                source_authority=constraint.source_authority,
                passed=passed,
                failed=failed,
                unknown=unknown,
                violated_by=constraint.forbidden_condition if failed else (),
                enforcement_action=status.value,
                reason_codes=(status.value,),
                provenance=constraint.provenance,
            )
        )

    return (
        records,
        tuple(dict.fromkeys(hard_failures)),
        tuple(dict.fromkeys(soft_conflicts)),
        tuple(dict.fromkeys(unknown_hard)),
    )


def _evaluate_constraint_status(
    *,
    constraint: W04Constraint,
    desired: W04DesiredStateRequest,
    context: W04ActiveApplicabilityContext,
    frame: W04PerspectiveFrame,
    intake: W04W03IntakeView,
) -> W04ConstraintEvaluationStatus:
    token = str(constraint.current_status or "").strip().lower()
    if token in {item.value for item in W04ConstraintEvaluationStatus}:
        return W04ConstraintEvaluationStatus(token)

    if constraint.constraint_type is W04ConstraintType.AUTHORITY_CONSTRAINT:
        if desired.source_authority and desired.source_authority not in intake.authority_scope:
            return W04ConstraintEvaluationStatus.AUTHORITY_MISMATCH
    if constraint.constraint_type is W04ConstraintType.PERSPECTIVE_CONSTRAINT:
        transfer_key = f"{frame.source_perspective}->{frame.requested_perspective}"
        if transfer_key in frame.blocked_perspective_transfer:
            return W04ConstraintEvaluationStatus.PERSPECTIVE_MISMATCH
    if constraint.constraint_type is W04ConstraintType.TEMPORAL_CONSTRAINT:
        if desired.temporal_window is not None and desired.temporal_window[1] < context.current_time_or_sequence:
            return W04ConstraintEvaluationStatus.TEMPORAL_INVALID

    if intake.must_abstain:
        return W04ConstraintEvaluationStatus.BLOCKED_BY_UPSTREAM_PERMISSION

    if "unknown" in constraint.required_condition:
        return W04ConstraintEvaluationStatus.UNKNOWN

    return W04ConstraintEvaluationStatus.PASSED


def _is_perspective_blocked(
    *, frame: W04PerspectiveFrame, desired: W04DesiredStateRequest, intake: W04W03IntakeView
) -> bool:
    transfer_key = f"{frame.source_perspective}->{frame.requested_perspective}"
    if transfer_key in frame.blocked_perspective_transfer:
        return True
    if frame.requested_perspective != desired.perspective_id:
        return True
    if frame.requested_perspective != _context_perspective(intake=intake, desired=desired):
        if transfer_key not in frame.allowed_perspective_transfer:
            return True
    return False


def _context_perspective(*, intake: W04W03IntakeView, desired: W04DesiredStateRequest) -> str:
    if desired.perspective_id in intake.context_scope:
        return desired.perspective_id
    return intake.context_scope[0] if intake.context_scope else desired.perspective_id


def _is_authority_blocked(*, desired: W04DesiredStateRequest, intake: W04W03IntakeView) -> bool:
    if not desired.source_authority:
        return True
    if not intake.authority_scope:
        return True
    return desired.source_authority not in intake.authority_scope


def _is_temporal_blocked(
    *, desired: W04DesiredStateRequest, context: W04ActiveApplicabilityContext, intake: W04W03IntakeView
) -> bool:
    if "stale" in intake.stale_or_revalidation_status:
        return True
    if desired.temporal_window is None:
        return "missing_freshness_basis" in context.unavailable_or_unknown_markers
    return desired.temporal_window[1] < context.current_time_or_sequence


def _is_malformed_desired_state(desired: W04DesiredStateRequest) -> bool:
    return bool(_desired_state_malformed_reasons(desired))


def _has_overbroad_relaxation_request(desired: W04DesiredStateRequest) -> bool:
    if not desired.acceptable_relaxation_dimensions:
        return False
    normalized = {str(item).strip().lower() for item in desired.acceptable_relaxation_dimensions}
    forbidden = {
        "*",
        "all",
        "hard_constraints",
        "authority_scope",
        "perspective_scope",
        "legality_constraint",
        "safety_constraint",
    }
    if normalized.intersection(forbidden):
        return True
    non_negotiable = {str(item).strip().lower() for item in desired.non_negotiable_constraints}
    if normalized.intersection(non_negotiable):
        return True
    return False


def _desired_state_malformed_reasons(desired: W04DesiredStateRequest) -> tuple[str, ...]:
    reasons: list[str] = []
    if not desired.requested_outcome or not desired.target_subject:
        reasons.append("malformed_desired_state")
    if desired.malformed_markers:
        reasons.append("malformed_desired_state_marker_present")
    if desired.embedded_forbidden_conclusions:
        reasons.append("embedded_forbidden_conclusion")
    if not desired.source_authority:
        reasons.append("missing_desired_state_source_authority")
    if not desired.provenance:
        reasons.append("missing_desired_state_provenance")
    if _has_overbroad_relaxation_request(desired):
        reasons.append("overbroad_relaxation_request")
    return tuple(dict.fromkeys(reasons))


def _derive_decision_status(
    *,
    intake: W04W03IntakeView,
    desired: W04DesiredStateRequest,
    hard_failures: tuple[str, ...],
    soft_conflicts: tuple[str, ...],
    unknown_hard: tuple[str, ...],
    perspective_blocked: bool,
    authority_blocked: bool,
    temporal_blocked: bool,
    desired_malformed_reasons: tuple[str, ...],
) -> tuple[W04ApplicabilityDecisionStatus, str]:
    if desired_malformed_reasons:
        return W04ApplicabilityDecisionStatus.MALFORMED_REQUEST, desired_malformed_reasons[0]
    if intake.must_abstain:
        return W04ApplicabilityDecisionStatus.ABSTAIN, "w03_must_abstain"
    if perspective_blocked:
        return W04ApplicabilityDecisionStatus.BLOCKED, "perspective_transfer_blocked"
    if authority_blocked:
        return W04ApplicabilityDecisionStatus.BLOCKED, "authority_scope_mismatch"
    if hard_failures:
        return W04ApplicabilityDecisionStatus.BLOCKED, "hard_constraint_failure"
    if unknown_hard:
        return W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED, "unknown_hard_feasibility"
    if temporal_blocked or intake.must_revalidate_before_use:
        return W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED, "stale_or_temporal_revalidation"
    if intake.must_preserve_contradiction or intake.contradiction_status:
        return W04ApplicabilityDecisionStatus.HINT_ONLY, "contradiction_preserved"
    if not intake.may_use_as_bounded_prior:
        if intake.may_use_as_schema_hint:
            if soft_conflicts:
                if desired.source_authority and desired.source_authority in intake.authority_scope:
                    return W04ApplicabilityDecisionStatus.RELAXABLE, "soft_conflict_relaxable"
            return W04ApplicabilityDecisionStatus.HINT_ONLY, "hint_only_upstream_permission"
        return W04ApplicabilityDecisionStatus.NO_CLEAN_APPLICABILITY, "no_clean_upstream_permission"
    if soft_conflicts:
        if desired.source_authority and desired.source_authority in intake.authority_scope:
            return W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION, "soft_conflict_relaxed"
        return W04ApplicabilityDecisionStatus.NARROWED, "soft_conflict_narrowed"
    if desired.priority == "urgent" and "hard_non_negotiable" in desired.non_negotiable_constraints:
        return W04ApplicabilityDecisionStatus.BLOCKED, "desired_priority_cannot_override_hard"
    return W04ApplicabilityDecisionStatus.ALLOWED, "bounded_allowed"


def _build_relaxation_ledger(
    *,
    tick_id: str,
    decision_id: str,
    desired: W04DesiredStateRequest,
    soft_conflicts: tuple[str, ...],
    hard_failures: tuple[str, ...],
) -> tuple[W04RelaxationLedgerEntry, ...]:
    if not soft_conflicts:
        return ()
    if not desired.acceptable_relaxation_dimensions:
        return ()
    entries: list[W04RelaxationLedgerEntry] = []
    for idx, conflict in enumerate(soft_conflicts, start=1):
        if conflict not in desired.acceptable_relaxation_dimensions and desired.acceptable_relaxation_dimensions:
            continue
        entries.append(
            W04RelaxationLedgerEntry(
                relaxation_id=f"{decision_id}:relax:{idx}",
                relaxed_field=conflict,
                original_constraint=conflict,
                relaxed_constraint=f"bounded:{conflict}",
                relaxation_bound="bounded_local_only",
                relaxation_authority=desired.source_authority,
                residual_risk="medium",
                downstream_effect="may_use_with_relaxation",
                non_relaxable_constraints_preserved=hard_failures,
                reason_codes=("soft_relaxation",),
                audit_ref=f"{tick_id}:{decision_id}:{conflict}",
            )
        )
    return tuple(entries)


def _reason_codes_from_status(
    *, status: W04ApplicabilityDecisionStatus, blocked_reason: str
) -> tuple[str, ...]:
    codes = [status.value]
    if blocked_reason:
        codes.append(blocked_reason)
    return tuple(dict.fromkeys(codes))


def _build_packet(
    *,
    decision_id: str,
    intake: W04W03IntakeView,
    status: W04ApplicabilityDecisionStatus,
    blocked_reason: str,
    hard_failures: tuple[str, ...],
    unknown_hard: tuple[str, ...],
    perspective_blocked: bool,
    authority_blocked: bool,
    temporal_blocked: bool,
    relaxation_entries: tuple[W04RelaxationLedgerEntry, ...],
    desired: W04DesiredStateRequest,
) -> W04DownstreamApplicabilityPermissionPacket:
    may_deploy = status in {
        W04ApplicabilityDecisionStatus.ALLOWED,
        W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION,
        W04ApplicabilityDecisionStatus.NARROWED,
    } and not hard_failures and not unknown_hard
    must_block = status in {
        W04ApplicabilityDecisionStatus.BLOCKED,
        W04ApplicabilityDecisionStatus.MALFORMED_REQUEST,
    }
    must_abstain = status in {
        W04ApplicabilityDecisionStatus.ABSTAIN,
        W04ApplicabilityDecisionStatus.NO_CLEAN_APPLICABILITY,
    }
    must_revalidate = status is W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED

    prohibited = [
        "action_authorization_from_w04",
        "world_truth_claim_from_w04",
        "authority_scope_broadening_from_w04",
        "perspective_scope_leakage_from_w04",
        *tuple(intake.prohibited_claims),
    ]
    if not may_deploy:
        prohibited.extend(
            [
                "clean_deploy_without_intersection",
                "operational_default_without_constraints_passed",
            ]
        )
    if status in {
        W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED,
        W04ApplicabilityDecisionStatus.HINT_ONLY,
        W04ApplicabilityDecisionStatus.ABSTAIN,
        W04ApplicabilityDecisionStatus.BLOCKED,
        W04ApplicabilityDecisionStatus.NO_CLEAN_APPLICABILITY,
        W04ApplicabilityDecisionStatus.MALFORMED_REQUEST,
    }:
        prohibited.append("clean_everyday_prior_deployment")

    markers = [
        "preserve_hard_constraints",
        "preserve_perspective_scope",
        "preserve_authority_scope",
    ]
    if temporal_blocked:
        markers.append("temporal_revalidation")
    if intake.must_preserve_contradiction:
        markers.append("preserve_upstream_contradiction")
    if intake.prohibited_claims:
        markers.append("preserve_upstream_prohibited_claims")

    if desired.intended_use == "action_authorization":
        must_block = True
        may_deploy = False
        blocked_reason = "w04_never_grants_action_authorization"

    return W04DownstreamApplicabilityPermissionPacket(
        decision_id=decision_id,
        candidate_id=intake.candidate_id,
        may_deploy_candidate=may_deploy,
        may_use_as_hint_only=status
        in {W04ApplicabilityDecisionStatus.HINT_ONLY, W04ApplicabilityDecisionStatus.NARROWED},
        may_use_after_revalidation=must_revalidate,
        may_use_with_relaxation=status
        in {
            W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION,
            W04ApplicabilityDecisionStatus.RELAXABLE,
        }
        and bool(relaxation_entries),
        must_abstain=must_abstain,
        must_block=must_block,
        must_revalidate=must_revalidate,
        must_preserve_hard_constraints=True,
        must_preserve_perspective_scope=True,
        must_preserve_authority_scope=True,
        action_authorization_granted=False,
        prohibited_uses=tuple(dict.fromkeys(prohibited)),
        required_preserved_markers=tuple(dict.fromkeys(markers)),
        blocked_reason=blocked_reason,
        decision_reason_codes=_reason_codes_from_status(status=status, blocked_reason=blocked_reason),
        violated_hard_constraints=hard_failures,
        unknown_hard_constraints=unknown_hard,
        perspective_boundary_markers=("perspective_blocked",) if perspective_blocked else (),
        authority_boundary_markers=("authority_blocked",) if authority_blocked else (),
        stale_or_revalidation_markers=("stale_or_temporal",) if temporal_blocked or must_revalidate else (),
        relaxation_ledger_refs=tuple(item.relaxation_id for item in relaxation_entries),
    )


def _build_telemetry(
    *,
    desired: W04DesiredStateRequest,
    intakes: tuple[W04W03IntakeView, ...],
    decisions: tuple[W04ApplicabilityDecision, ...],
    packets: tuple[W04DownstreamApplicabilityPermissionPacket, ...],
    eval_records: tuple[W04ConstraintEvaluationRecord, ...],
    blocked_records: tuple[W04BlockedApplicabilityRecord, ...],
) -> W04Telemetry:
    allowed = sum(1 for item in decisions if item.decision_status is W04ApplicabilityDecisionStatus.ALLOWED)
    blocked = sum(1 for item in decisions if item.decision_status is W04ApplicabilityDecisionStatus.BLOCKED)
    narrowed = sum(1 for item in decisions if item.decision_status is W04ApplicabilityDecisionStatus.NARROWED)
    hint_only = sum(1 for item in decisions if item.decision_status is W04ApplicabilityDecisionStatus.HINT_ONLY)
    revalidate = sum(
        1 for item in decisions if item.decision_status is W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED
    )
    abstain = sum(1 for item in decisions if item.decision_status is W04ApplicabilityDecisionStatus.ABSTAIN)
    relaxation = sum(
        1
        for item in decisions
        if item.decision_status
        in {W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION, W04ApplicabilityDecisionStatus.RELAXABLE}
    )
    hard_fail = sum(
        1
        for item in eval_records
        if item.hard_or_soft in {W04ConstraintHardness.HARD, W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED}
        and item.failed
    )
    unknown_hard = sum(
        1
        for item in eval_records
        if item.hard_or_soft in {W04ConstraintHardness.HARD, W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED}
        and item.unknown
    )
    malformed = 1 if _desired_state_malformed_reasons(desired) else 0
    perspective_block = sum(1 for item in packets if item.perspective_boundary_markers)
    authority_block = sum(1 for item in packets if item.authority_boundary_markers)
    stale_block = sum(1 for item in packets if item.stale_or_revalidation_markers)
    consumer_ready = any(item.may_deploy_candidate for item in packets)
    no_clean = not consumer_ready

    _ = blocked_records
    return W04Telemetry(
        desired_state_intake_count=1,
        w03_candidate_intake_count=len(intakes),
        applicability_decision_count=len(decisions),
        allowed_count=allowed,
        blocked_count=blocked,
        narrowed_count=narrowed,
        hint_only_count=hint_only,
        revalidate_required_count=revalidate,
        abstain_count=abstain,
        relaxation_count=relaxation,
        hard_constraint_failure_count=hard_fail,
        unknown_hard_count=unknown_hard,
        malformed_desired_state_count=malformed,
        perspective_block_count=perspective_block,
        authority_block_count=authority_block,
        stale_block_count=stale_block,
        consumer_ready=consumer_ready,
        no_clean_applicability=no_clean,
    )


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> W04ResultBundle:
    telemetry = W04Telemetry(
        desired_state_intake_count=0,
        w03_candidate_intake_count=0,
        applicability_decision_count=0,
        allowed_count=0,
        blocked_count=0,
        narrowed_count=0,
        hint_only_count=0,
        revalidate_required_count=0,
        abstain_count=0,
        relaxation_count=0,
        hard_constraint_failure_count=0,
        unknown_hard_count=0,
        malformed_desired_state_count=0,
        perspective_block_count=0,
        authority_block_count=0,
        stale_block_count=0,
        consumer_ready=False,
        no_clean_applicability=True,
    )
    gate = W04GateDecision(
        consumer_ready=False,
        no_clean_applicability=True,
        blocked_count=0,
        revalidate_required_count=0,
        abstain_count=0,
        hard_constraint_failure_count=0,
        unknown_hard_count=0,
        required_restrictions=restrictions,
        reason_codes=("w04_no_clean_applicability",),
        reason=reason,
    )
    return W04ResultBundle(
        bundle_id=bundle_id,
        applicability_decisions=(),
        intersection_assessments=(),
        constraint_evaluations=(),
        perspective_safety_records=(),
        relaxation_ledger_entries=(),
        revalidation_requests=(),
        blocked_records=(),
        downstream_permission_packets=(),
        telemetry=telemetry,
        gate=gate,
        scope_marker=W04ScopeMarker(
            scope="frontier_hosted_w04_applicability_gating_slice",
            applicability_gating_only=True,
            no_planner_claim=True,
            no_action_selector_claim=True,
            no_world_model_expansion_claim=True,
            no_w05_or_w06_claim=True,
            reason=reason,
        ),
        no_claim_markers=(
            "w04_not_planner",
            "w04_not_action_selector",
            "w04_not_world_model",
            "w04_not_w05_or_w06",
        ),
        reason=reason,
    )
