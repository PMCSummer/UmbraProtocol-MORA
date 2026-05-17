from __future__ import annotations

import json

from substrate.ap01_subject_action_publication.models import (
    ALLOWED_ACTION_KINDS,
    FORBIDDEN_MAGIC_ACTION_KINDS,
    TARGET_REQUIRED_ACTION_KINDS,
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01ActionPublicationDecision,
    AP01ActionPublicationTelemetry,
    AP01CandidateOrigin,
    AP01DecisionStatus,
    AP01ExecutionBoundary,
    AP01ScopeMarker,
    AP01SubjectActionPublicationResult,
    AP01SubjectActionRequestPacket,
    AP01WorldExecutionStatus,
)

_FORBIDDEN_BASIS_TOKENS: tuple[str, ...] = (
    "scenario_id",
    "test_name",
    "expected_outcome",
    "gui_label",
    "harness_truth",
    "eval_only",
    "hidden_truth",
    "success_label",
)

_DEFAULT_CLAIM_BOUNDARY: tuple[str, ...] = (
    "request_is_not_execution",
    "request_is_not_world_change",
    "request_is_not_completion_claim",
    "must_wait_for_effect_feedback",
    "no_hidden_truth_basis",
    "no_eval_only_basis",
    "no_scenario_label_basis",
)


def build_ap01_subject_action_publication(
    *,
    tick_id: str,
    tick_index: int,
    candidate_set: AP01ActionPublicationCandidateSet | None,
    publication_enabled: bool = True,
    allow_test_fixture_candidates: bool = False,
) -> AP01SubjectActionPublicationResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if tick_index <= 0:
        raise ValueError("tick_index must be positive")

    if not publication_enabled:
        return _empty_result(
            candidate_set_id=f"ap01:{tick_id}:candidate_set:none",
            reason="ap01 publication disabled in fixture path",
        )

    if not isinstance(candidate_set, AP01ActionPublicationCandidateSet):
        return _empty_result(
            candidate_set_id=f"ap01:{tick_id}:candidate_set:none",
            reason="ap01 requires typed candidate set and does not infer action requests from implicit hints",
        )

    decisions: list[AP01ActionPublicationDecision] = []
    published: list[AP01SubjectActionRequestPacket] = []

    for candidate in candidate_set.candidates:
        decision = _evaluate_candidate(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            allow_test_fixture_candidates=allow_test_fixture_candidates,
        )
        decisions.append(decision)
        if decision.published_request is not None:
            published.append(decision.published_request)

    telemetry = AP01ActionPublicationTelemetry(
        candidate_count=len(candidate_set.candidates),
        published_request_count=len(published),
        blocked_count=sum(int(d.decision_status is AP01DecisionStatus.BLOCKED) for d in decisions),
        revalidation_required_count=sum(
            int(d.decision_status is AP01DecisionStatus.REVALIDATION_REQUIRED) for d in decisions
        ),
        abstain_count=sum(int(d.decision_status is AP01DecisionStatus.ABSTAIN) for d in decisions),
        malformed_count=sum(int(d.decision_status is AP01DecisionStatus.MALFORMED) for d in decisions),
        unsafe_basis_count=sum(int(d.decision_status is AP01DecisionStatus.UNSAFE_BASIS) for d in decisions),
        execution_boundary_preserved=all(
            req.execution_boundary is AP01ExecutionBoundary.EXTERNAL_WORLD_ONLY for req in published
        ),
        must_wait_for_effect=all(req.must_wait_for_world_effect for req in published),
        no_hidden_truth_used=all(
            req.no_hidden_truth_used for req in published
        )
        and all(c.no_hidden_truth_used for c in candidate_set.candidates),
        no_eval_only_used=all(req.no_eval_only_used for req in published) and all(
            c.no_eval_only_used for c in candidate_set.candidates
        ),
        no_scenario_label_used=all(req.no_scenario_label_used for req in published) and all(
            c.no_scenario_label_used for c in candidate_set.candidates
        ),
    )

    return AP01SubjectActionPublicationResult(
        candidate_set_id=candidate_set.candidate_set_id,
        decisions=tuple(decisions),
        published_requests=tuple(published),
        telemetry=telemetry,
        scope_marker=AP01ScopeMarker(
            scope="frontier_hosted_ap01_subject_action_publication_slice",
            rt01_hosted_only=True,
            publication_not_planner=True,
            publication_not_execution=True,
            no_world_mutation_inside_subject=True,
            no_phase_override_authority=True,
            reason=(
                "ap01 only publishes bounded external action request packets and preserves "
                "permission/evidence/uncertainty boundaries without execution authority"
            ),
        ),
        reason="ap01 evaluated typed action publication candidates and emitted bounded request decisions",
    )


def _evaluate_candidate(
    *,
    tick_id: str,
    tick_index: int,
    candidate: AP01ActionPublicationCandidate,
    allow_test_fixture_candidates: bool,
) -> AP01ActionPublicationDecision:
    decision_id = f"ap01:{tick_id}:{tick_index}:decision:{candidate.candidate_id}"

    unsafe_reasons = _unsafe_basis_reasons(candidate, allow_test_fixture_candidates)
    if unsafe_reasons:
        return AP01ActionPublicationDecision(
            decision_id=decision_id,
            candidate_id=candidate.candidate_id,
            decision_status=AP01DecisionStatus.UNSAFE_BASIS,
            reason_codes=tuple(unsafe_reasons),
            blocked_reason="unsafe_candidate_basis",
            missing_requirements=(),
            preserved_residue_refs=tuple(dict.fromkeys((*candidate.residue_refs, *candidate.blocked_claim_refs))),
            downstream_permission_delta=("must_not_publish", "requires_basis_reconstruction"),
            published_request=None,
        )

    malformed_reasons = _malformed_reasons(candidate)
    if malformed_reasons:
        return AP01ActionPublicationDecision(
            decision_id=decision_id,
            candidate_id=candidate.candidate_id,
            decision_status=AP01DecisionStatus.MALFORMED,
            reason_codes=tuple(malformed_reasons),
            blocked_reason="malformed_candidate",
            missing_requirements=(),
            preserved_residue_refs=tuple(dict.fromkeys((*candidate.residue_refs, *candidate.blocked_claim_refs))),
            downstream_permission_delta=("must_not_publish", "requires_schema_correction"),
            published_request=None,
        )

    missing_requirements = _missing_requirements(candidate)
    if missing_requirements:
        return AP01ActionPublicationDecision(
            decision_id=decision_id,
            candidate_id=candidate.candidate_id,
            decision_status=AP01DecisionStatus.BLOCKED,
            reason_codes=("missing_publication_requirements",),
            blocked_reason="required_fields_missing",
            missing_requirements=tuple(missing_requirements),
            preserved_residue_refs=tuple(dict.fromkeys((*candidate.residue_refs, *candidate.blocked_claim_refs))),
            downstream_permission_delta=("must_not_publish", "requires_permission_and_evidence"),
            published_request=None,
        )

    if candidate.blocked_claim_refs:
        return AP01ActionPublicationDecision(
            decision_id=decision_id,
            candidate_id=candidate.candidate_id,
            decision_status=AP01DecisionStatus.BLOCKED,
            reason_codes=("blocked_claim_refs_present",),
            blocked_reason="blocked_claims_present",
            missing_requirements=(),
            preserved_residue_refs=tuple(dict.fromkeys((*candidate.residue_refs, *candidate.blocked_claim_refs))),
            downstream_permission_delta=("must_not_publish", "must_preserve_blocked_claim_refs"),
            published_request=None,
        )

    if candidate.revalidation_refs or candidate.residue_refs:
        return AP01ActionPublicationDecision(
            decision_id=decision_id,
            candidate_id=candidate.candidate_id,
            decision_status=AP01DecisionStatus.REVALIDATION_REQUIRED,
            reason_codes=("w06_revalidation_or_residue_present",),
            blocked_reason="revalidation_required_before_publication",
            missing_requirements=(),
            preserved_residue_refs=tuple(dict.fromkeys((*candidate.residue_refs, *candidate.revalidation_refs))),
            downstream_permission_delta=("hold_request", "must_revalidate"),
            published_request=None,
        )

    if _is_basis_only_without_permission(candidate):
        return AP01ActionPublicationDecision(
            decision_id=decision_id,
            candidate_id=candidate.candidate_id,
            decision_status=AP01DecisionStatus.BLOCKED,
            reason_codes=("basis_without_permission_boundary",),
            blocked_reason="insufficient_permission_or_evidence_basis",
            missing_requirements=(),
            preserved_residue_refs=(),
            downstream_permission_delta=("must_not_publish", "must_not_infer_action_from_desired_or_predicted"),
            published_request=None,
        )

    request = AP01SubjectActionRequestPacket(
        request_id=f"ap01:{tick_id}:{tick_index}:request:{candidate.candidate_id}",
        source_candidate_id=candidate.candidate_id,
        action_kind=candidate.action_kind,
        target_ref=candidate.target_ref,
        args=dict(candidate.args),
        intended_effect=candidate.intended_effect,
        source_tick_ref=candidate.source_tick_ref,
        source_phase_refs=candidate.source_phase_refs,
        affordance_binding_refs=candidate.affordance_binding_refs,
        permission_refs=candidate.permission_refs,
        evidence_refs=candidate.evidence_refs,
        episode_refs=candidate.episode_refs,
        execution_boundary=AP01ExecutionBoundary.EXTERNAL_WORLD_ONLY,
        executed_by_subject=False,
        world_execution_status=AP01WorldExecutionStatus.NOT_EXECUTED_BY_SUBJECT,
        must_wait_for_world_effect=True,
        effect_feedback_required=True,
        no_hidden_truth_used=True,
        no_eval_only_used=True,
        no_scenario_label_used=True,
        publication_confidence=_confidence_from_candidate(candidate),
        uncertainty_markers=tuple(dict.fromkeys((*candidate.revalidation_refs, *candidate.residue_refs))),
        claim_boundary=_DEFAULT_CLAIM_BOUNDARY,
    )
    return AP01ActionPublicationDecision(
        decision_id=decision_id,
        candidate_id=candidate.candidate_id,
        decision_status=AP01DecisionStatus.PUBLISHED,
        reason_codes=("published_bounded_external_request",),
        blocked_reason=None,
        missing_requirements=(),
        preserved_residue_refs=(),
        downstream_permission_delta=(
            "may_submit_to_world_bridge",
            "must_not_execute_inside_subject",
            "must_wait_for_effect_feedback",
        ),
        published_request=request,
    )


def _unsafe_basis_reasons(
    candidate: AP01ActionPublicationCandidate,
    allow_test_fixture_candidates: bool,
) -> list[str]:
    reasons: list[str] = []
    if candidate.candidate_origin is AP01CandidateOrigin.UNSAFE_EXTERNAL_OR_HARNESS_CANDIDATE:
        reasons.append("unsafe_origin_external_or_harness")
    if candidate.candidate_origin is AP01CandidateOrigin.TEST_FIXTURE_CANDIDATE and not allow_test_fixture_candidates:
        reasons.append("test_fixture_origin_not_allowed")
    if not candidate.no_hidden_truth_used:
        reasons.append("hidden_truth_basis_forbidden")
    if not candidate.no_eval_only_used:
        reasons.append("eval_only_basis_forbidden")
    if not candidate.no_scenario_label_used:
        reasons.append("scenario_label_basis_forbidden")
    lowered_markers = tuple(item.lower() for item in candidate.forbidden_basis_markers)
    for token in _FORBIDDEN_BASIS_TOKENS:
        if any(token in marker for marker in lowered_markers):
            reasons.append(f"forbidden_basis_marker:{token}")
    return reasons


def _malformed_reasons(candidate: AP01ActionPublicationCandidate) -> list[str]:
    reasons: list[str] = []
    if candidate.action_kind == "emit_world_action":
        reasons.append("generic_world_adapter_stub_action_forbidden")
    if candidate.target_ref == "external_stub_target":
        reasons.append("generic_stub_target_forbidden")
    if candidate.action_kind not in ALLOWED_ACTION_KINDS:
        reasons.append("unknown_action_kind")
    if candidate.action_kind in FORBIDDEN_MAGIC_ACTION_KINDS:
        reasons.append("forbidden_magic_action_kind")
    if candidate.action_kind in TARGET_REQUIRED_ACTION_KINDS and not candidate.target_ref:
        reasons.append("missing_target_for_targeted_action")
    if not candidate.intended_effect:
        reasons.append("missing_intended_effect")
    try:
        json.dumps(candidate.args, sort_keys=True)
    except TypeError:
        reasons.append("non_serializable_args")
    return reasons


def _missing_requirements(candidate: AP01ActionPublicationCandidate) -> list[str]:
    missing: list[str] = []
    if not candidate.source_tick_ref:
        missing.append("source_tick_ref")
    if not candidate.source_phase_refs:
        missing.append("source_phase_refs")
    if not candidate.permission_refs:
        missing.append("permission_refs")
    if not candidate.evidence_refs:
        missing.append("evidence_refs")
    if not candidate.permitted_refs:
        missing.append("permitted_refs")
    if not candidate.episode_refs:
        missing.append("episode_refs")
    source_phase_tokens = tuple(ref.upper() for ref in candidate.source_phase_refs)
    if not any("W04" in token for token in source_phase_tokens):
        missing.append("w04_boundary_ref")
    if not any("W05" in token for token in source_phase_tokens):
        missing.append("w05_boundary_ref")
    if not any("W06" in token for token in source_phase_tokens):
        missing.append("w06_boundary_ref")
    if (
        candidate.action_kind in TARGET_REQUIRED_ACTION_KINDS
        and not candidate.affordance_binding_refs
    ):
        missing.append("affordance_binding_refs")
    return missing


def _is_basis_only_without_permission(candidate: AP01ActionPublicationCandidate) -> bool:
    # Desired/predicted/affordance/observed signals can inform candidate quality,
    # but AP01 forbids publication unless explicit permission/permitted/evidence is present.
    desired_or_predicted = bool(candidate.desired_refs or candidate.predicted_refs)
    affordance_only = bool(candidate.affordance_binding_refs) and not (
        candidate.permission_refs and candidate.permitted_refs
    )
    observed_only = bool(candidate.observed_refs) and not (
        candidate.permission_refs and candidate.evidence_refs
    )
    return desired_or_predicted or affordance_only or observed_only


def _confidence_from_candidate(candidate: AP01ActionPublicationCandidate) -> float:
    uncertainty_penalty = 0.05 * len(
        tuple(dict.fromkeys((*candidate.residue_refs, *candidate.revalidation_refs, *candidate.blocked_claim_refs)))
    )
    base = 0.8
    return max(0.1, min(0.95, base - uncertainty_penalty))


def _empty_result(*, candidate_set_id: str, reason: str) -> AP01SubjectActionPublicationResult:
    return AP01SubjectActionPublicationResult(
        candidate_set_id=candidate_set_id,
        decisions=(),
        published_requests=(),
        telemetry=AP01ActionPublicationTelemetry(
            candidate_count=0,
            published_request_count=0,
            blocked_count=0,
            revalidation_required_count=0,
            abstain_count=1,
            malformed_count=0,
            unsafe_basis_count=0,
            execution_boundary_preserved=True,
            must_wait_for_effect=True,
            no_hidden_truth_used=True,
            no_eval_only_used=True,
            no_scenario_label_used=True,
        ),
        scope_marker=AP01ScopeMarker(
            scope="frontier_hosted_ap01_subject_action_publication_slice",
            rt01_hosted_only=True,
            publication_not_planner=True,
            publication_not_execution=True,
            no_world_mutation_inside_subject=True,
            no_phase_override_authority=True,
            reason="ap01 remains a bounded publication seam even when no candidate basis is provided",
        ),
        reason=reason,
    )
