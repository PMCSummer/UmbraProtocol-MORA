from __future__ import annotations

from dataclasses import replace

import substrate.w06_error_driven_revision.policy as w06_policy
from substrate.w06_error_driven_revision import (
    W06ConsequenceType,
    W06IdentityRoute,
    W06MismatchClass,
    W06RevisionScope,
    W06RouteStatus,
)
from tests.substrate.w06_error_driven_revision_testkit import (
    build_w06_harness,
    clone_bundle,
    consequence,
    w06_bundle,
    w06_context,
    w06_contradiction,
    w06_lineage,
    w06_mismatch,
)


def _run(case_id: str, bundle):
    return build_w06_harness(case_id, input_bundle=bundle)


def test_mismatch_class_changes_consequence_route() -> None:
    base = w06_bundle("route-by-class")
    world = _run("route-by-class:world", clone_bundle(base, mismatch_intake=w06_mismatch("route-by-class", mismatch_class=W06MismatchClass.WORLD_MODEL)))
    ownership = _run("route-by-class:ownership", clone_bundle(base, mismatch_intake=w06_mismatch("route-by-class", mismatch_class=W06MismatchClass.OWNERSHIP)))
    assert world.decision.consequence_type != ownership.decision.consequence_type


def test_error_type_changes_route_via_authority_class() -> None:
    base = w06_bundle("authority-route")
    authority = _run(
        "authority-route",
        clone_bundle(base, mismatch_intake=w06_mismatch("authority-route", mismatch_class=W06MismatchClass.AUTHORITY_SCOPE)),
    )
    assert authority.decision.consequence_type is W06ConsequenceType.BLOCK_CLAIM
    assert authority.decision.revision_scope is W06RevisionScope.AUTHORITY_SCOPE_LEVEL


def test_violated_expectation_source_changes_route_for_desired_vs_permitted() -> None:
    base = w06_bundle("desired-permitted")
    result = _run(
        "desired-permitted",
        clone_bundle(base, mismatch_intake=w06_mismatch("desired-permitted", mismatch_class=W06MismatchClass.DESIRED_VS_PERMITTED)),
    )
    assert "permission_or_authority_mismatch" in result.decision.decision_reason_codes


def test_protected_status_changes_route_to_escalate_or_block() -> None:
    base = w06_bundle("protected-route")
    protected = _run(
        "protected-route",
        clone_bundle(
            base,
            mismatch_intake=w06_mismatch("protected-route", mismatch_class=W06MismatchClass.CONSTITUTIONAL_BOUNDARY, severity="high", constitutional_guard_flags=("protected",)),
        ),
    )
    assert protected.decision.consequence_type in {W06ConsequenceType.ESCALATE_REVIEW, W06ConsequenceType.BLOCK_CLAIM}
    assert protected.downstream_packet.must_not_execute_correction is True


def test_every_decision_has_revision_ledger_entry() -> None:
    result = _run("ledger-present", w06_bundle("ledger-present"))
    assert result.ledger.ledger_id
    assert result.ledger.error_type.value


def test_ledger_contains_w06_1_fields() -> None:
    result = _run("ledger-fields", w06_bundle("ledger-fields"))
    assert result.ledger.confidence_drop_policy.value
    assert result.ledger.retained_uncertainty_residue
    assert result.ledger.downstream_permission_effects


def test_ledger_downstream_effects_non_empty_when_block_or_revalidate() -> None:
    result = _run(
        "ledger-effects",
        clone_bundle(
            w06_bundle("ledger-effects"),
            mismatch_intake=w06_mismatch("ledger-effects", mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
        ),
    )
    assert result.ledger.downstream_permission_effects


def test_contradiction_cannot_be_telemetry_only() -> None:
    result = _run(
        "contradiction-operational",
        clone_bundle(
            w06_bundle("contradiction-operational"),
            contradiction_intake=(w06_contradiction("contradiction-operational", severity="high", unresolved_status=True),),
        ),
    )
    assert result.gate.must_block_claim or result.gate.must_revalidate


def test_contradiction_changes_claim_block_packet() -> None:
    base = w06_bundle("contradiction-claim")
    with_contradiction = _run("contradiction-claim:with", base)
    without_contradiction = _run("contradiction-claim:without", clone_bundle(base, contradiction_intake=()))
    assert with_contradiction.claim_block_packet.blocked_claim_types != without_contradiction.claim_block_packet.blocked_claim_types


def test_local_mismatch_does_not_globally_invalidate() -> None:
    result = _run(
        "local-no-global",
        clone_bundle(
            w06_bundle("local-no-global"),
            mismatch_intake=w06_mismatch("local-no-global", mismatch_class=W06MismatchClass.AFFORDANCE, target_scope=("local_scope",), severity="medium"),
        ),
    )
    assert result.decision.revision_scope is not W06RevisionScope.GLOBAL


def test_global_invalidation_requires_explicit_criteria() -> None:
    global_allowed_scopes = (*w06_context("global-criteria").allowed_revision_scopes, W06RevisionScope.GLOBAL)
    bundle = w06_bundle(
        "global-criteria",
        mismatch_intake=w06_mismatch(
            "global-criteria",
            mismatch_class=W06MismatchClass.WORLD_MODEL,
            severity="critical",
            confidence=0.95,
            evidence_refs=("e1", "e2", "e3"),
            target_scope=("global_scope",),
            competing_class_candidates=(),
            ambiguity_markers=(),
        ),
        revision_context=w06_context(
            "global-criteria",
            global_revision_allowed=True,
            allowed_revision_scopes=global_allowed_scopes,
        ),
        contradiction_intake=(),
    )
    result = _run("global-criteria", bundle)
    assert result.decision.revision_scope is W06RevisionScope.GLOBAL
    assert result.decision.consequence_type is W06ConsequenceType.INVALIDATE
    assert "global_invalidation_criteria_met" in result.decision.decision_reason_codes


def test_global_route_refused_without_criteria() -> None:
    bundle = w06_bundle(
        "global-refused",
        mismatch_intake=w06_mismatch(
            "global-refused",
            mismatch_class=W06MismatchClass.WORLD_MODEL,
            severity="medium",
            confidence=0.6,
            evidence_refs=("e1",),
            target_scope=("global_scope",),
        ),
        revision_context=w06_context("global-refused", global_revision_allowed=True),
        contradiction_intake=(),
    )
    result = _run("global-refused", bundle)
    assert result.decision.revision_scope is not W06RevisionScope.GLOBAL
    assert "global_criteria_not_met_or_not_allowed" in result.consequence.criteria_failed


def test_scope_whitelist_blocks_disallowed_global_revision_scope() -> None:
    allowed = tuple(scope for scope in w06_context("scope-whitelist").allowed_revision_scopes if scope is not W06RevisionScope.GLOBAL)
    bundle = w06_bundle(
        "scope-whitelist",
        mismatch_intake=w06_mismatch(
            "scope-whitelist",
            mismatch_class=W06MismatchClass.WORLD_MODEL,
            severity="critical",
            confidence=0.95,
            evidence_refs=("e1", "e2", "e3"),
            target_scope=("global_scope",),
        ),
        contradiction_intake=(),
        revision_context=w06_context(
            "scope-whitelist",
            global_revision_allowed=True,
            allowed_revision_scopes=allowed,
        ),
    )
    result = _run("scope-whitelist", bundle)
    assert result.decision.revision_scope is not W06RevisionScope.GLOBAL
    assert "selected_scope_outside_allowed_revision_scopes" in result.decision.decision_reason_codes
    assert "narrowed_revision_scope_to_allowed_boundary" in result.decision.decision_reason_codes


def test_repeated_revalidation_without_progress_triggers_anti_paralysis() -> None:
    bundle = w06_bundle(
        "anti-paralysis",
        mismatch_intake=w06_mismatch("anti-paralysis", mismatch_class=W06MismatchClass.VALIDITY),
        contradiction_intake=(),
        revision_context=w06_context("anti-paralysis", repeated_revalidation_count=5, progress_detected=False, loop_threshold=3),
    )
    result = _run("anti-paralysis", bundle)
    assert result.anti_paralysis_state.chosen_escape_route in {
        W06ConsequenceType.NARROW_CONTINUATION,
        W06ConsequenceType.ESCALATE_REVIEW,
        W06ConsequenceType.QUARANTINE,
    }


def test_revalidation_with_progress_keeps_revalidation_and_records_reason() -> None:
    bundle = w06_bundle(
        "anti-progress",
        mismatch_intake=w06_mismatch("anti-progress", mismatch_class=W06MismatchClass.VALIDITY),
        contradiction_intake=(),
        revision_context=w06_context("anti-progress", repeated_revalidation_count=5, progress_detected=True, loop_threshold=3),
    )
    result = _run("anti-progress", bundle)
    assert "revalidation_progress_detected" in result.anti_paralysis_state.reason_codes


def test_anti_paralysis_does_not_erase_residue() -> None:
    bundle = w06_bundle(
        "anti-residue",
        mismatch_intake=w06_mismatch("anti-residue", mismatch_class=W06MismatchClass.VALIDITY),
        contradiction_intake=(),
        revision_context=w06_context("anti-residue", repeated_revalidation_count=5, progress_detected=False, loop_threshold=3),
    )
    result = _run("anti-residue", bundle)
    assert result.residual_uncertainty.retained_markers


def test_unresolved_non_critical_residue_permits_narrow_continuation() -> None:
    result = _run(
        "narrow-cont",
        clone_bundle(
            w06_bundle("narrow-cont"),
            mismatch_intake=w06_mismatch("narrow-cont", mismatch_class=W06MismatchClass.INSUFFICIENT_EVIDENCE, evidence_precision=0.2),
            contradiction_intake=(),
        ),
    )
    assert result.downstream_packet.may_continue_narrowly is True
    assert result.downstream_packet.may_use_with_residue is True


def test_critical_residue_blocks_or_escalates() -> None:
    result = _run(
        "critical-residue",
        clone_bundle(
            w06_bundle("critical-residue"),
            mismatch_intake=w06_mismatch(
                "critical-residue",
                mismatch_class=W06MismatchClass.CONSTITUTIONAL_BOUNDARY,
                severity="high",
                constitutional_guard_flags=("protected",),
            ),
        ),
    )
    assert result.downstream_packet.must_escalate or result.downstream_packet.must_block_claim


def test_prohibited_claims_preserved_downstream() -> None:
    result = _run("prohibited-preserved", w06_bundle("prohibited-preserved"))
    assert "no_universal_world_truth" in result.downstream_packet.prohibited_claims


def test_duplicate_identity_conflict_routes_to_identity_candidate() -> None:
    result = _run(
        "duplicate-identity",
        clone_bundle(
            w06_bundle("duplicate-identity"),
            contradiction_intake=(w06_contradiction("duplicate-identity", conflict_type="duplicate_identity_conflict"),),
        ),
    )
    assert result.identity_revision.identity_route in {
        W06IdentityRoute.DUPLICATE_CANDIDATE,
        W06IdentityRoute.SPLIT_IDENTITY,
    }


def test_replacement_identity_conflict_routes_to_replacement_candidate() -> None:
    result = _run(
        "replacement-identity",
        clone_bundle(
            w06_bundle("replacement-identity"),
            contradiction_intake=(w06_contradiction("replacement-identity", conflict_type="replacement_identity_conflict"),),
        ),
    )
    assert result.identity_revision.identity_route in {
        W06IdentityRoute.REPLACEMENT_CANDIDATE,
        W06IdentityRoute.SPLIT_IDENTITY,
    }


def test_identity_swap_blocks_continuity_claim() -> None:
    result = _run(
        "swap-identity",
        clone_bundle(
            w06_bundle("swap-identity"),
            mismatch_intake=w06_mismatch("swap-identity", mismatch_class=W06MismatchClass.OWNERSHIP),
            contradiction_intake=(w06_contradiction("swap-identity", conflict_type="identity_swap"),),
        ),
    )
    assert result.identity_revision.continuity_claim_blocked is True


def test_unknown_lineage_marker_on_ambiguous() -> None:
    result = _run(
        "unknown-lineage",
        clone_bundle(
            w06_bundle("unknown-lineage"),
            mismatch_intake=w06_mismatch("unknown-lineage", mismatch_class=W06MismatchClass.AMBIGUOUS_MULTI_CLASS),
            contradiction_intake=(),
        ),
    )
    assert result.identity_revision.unknown_lineage_marker is True


def test_ambiguous_mismatch_caps_correction_confidence_and_preserves_competing_candidates() -> None:
    result = _run(
        "ambiguous-confidence",
        clone_bundle(
            w06_bundle("ambiguous-confidence"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch(
                "ambiguous-confidence",
                mismatch_class=W06MismatchClass.AMBIGUOUS_MULTI_CLASS,
                confidence=0.95,
                ambiguity_markers=("ambiguous",),
                competing_class_candidates=("world_model", "affordance", "ownership"),
            ),
        ),
    )
    assert result.correction_candidate.confidence <= 0.35
    assert result.decision.route_status in {
        W06RouteStatus.CONTESTED_REVISION_ROUTE,
        W06RouteStatus.REVALIDATION_REQUIRED,
        W06RouteStatus.ESCALATED,
    }
    assert "confidence_capped_due_to_ambiguity" in result.decision.decision_reason_codes
    assert result.correction_candidate.competing_candidates
    assert result.residual_uncertainty.retained_markers


def test_correction_candidate_execution_prohibited_is_true() -> None:
    result = _run("candidate-prohibited", w06_bundle("candidate-prohibited"))
    assert result.correction_candidate.execution_prohibited is True


def test_correction_candidate_has_future_update_seam_ref() -> None:
    result = _run("candidate-seam", w06_bundle("candidate-seam"))
    assert result.correction_candidate.future_update_seam_ref


def test_downstream_packet_must_not_execute_correction_true() -> None:
    result = _run("downstream-seam", w06_bundle("downstream-seam"))
    assert result.downstream_packet.must_not_execute_correction is True


def test_confidence_high_precision_high_reliability_severe_drops_more() -> None:
    base = w06_bundle("confidence-drop")
    strong = _run(
        "confidence-drop:strong",
        clone_bundle(
            base,
            mismatch_intake=w06_mismatch("confidence-drop", evidence_precision=0.95, source_reliability=0.95, severity="critical"),
        ),
    )
    weak = _run(
        "confidence-drop:weak",
        clone_bundle(
            base,
            mismatch_intake=w06_mismatch("confidence-drop", evidence_precision=0.2, source_reliability=0.2, severity="medium"),
        ),
    )
    assert strong.confidence_adjustment.new_confidence <= weak.confidence_adjustment.new_confidence


def test_low_precision_weak_source_avoids_overreaction() -> None:
    result = _run(
        "confidence-overreaction",
        clone_bundle(
            w06_bundle("confidence-overreaction"),
            mismatch_intake=w06_mismatch("confidence-overreaction", evidence_precision=0.1, source_reliability=0.1, severity="high"),
        ),
    )
    assert result.confidence_adjustment.new_confidence >= 0.1


def test_confidence_not_globally_collapsed_for_local_mismatch() -> None:
    result = _run(
        "confidence-local",
        clone_bundle(
            w06_bundle("confidence-local"),
            mismatch_intake=w06_mismatch("confidence-local", mismatch_class=W06MismatchClass.AFFORDANCE),
        ),
    )
    assert result.confidence_adjustment.global_collapse_prevented is True


def test_maturity_sensitivity_affects_record() -> None:
    result = _run(
        "maturity-sensitivity",
        clone_bundle(w06_bundle("maturity-sensitivity"), lineage_view=w06_lineage("maturity-sensitivity", maturity_level="high_maturity")),
    )
    assert result.confidence_adjustment.maturity_sensitivity == "high_maturity"


def test_downgrade_route_retains_residue() -> None:
    result = _run(
        "downgrade-residue",
        clone_bundle(
            w06_bundle("downgrade-residue"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("downgrade-residue", mismatch_class=W06MismatchClass.WORLD_MODEL, evidence_precision=0.9, source_reliability=0.9),
        ),
    )
    assert result.decision.consequence_type is W06ConsequenceType.DOWNGRADE
    assert result.residual_uncertainty.retained_markers


def test_revalidate_route_retains_residue() -> None:
    result = _run(
        "revalidate-residue",
        clone_bundle(
            w06_bundle("revalidate-residue"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("revalidate-residue", mismatch_class=W06MismatchClass.VALIDITY),
        ),
    )
    assert result.decision.consequence_type is W06ConsequenceType.REVALIDATE
    assert result.residual_uncertainty.visibility_to_downstream is True


def test_residue_has_relevance_bound_and_trigger() -> None:
    result = _run("residue-shape", w06_bundle("residue-shape"))
    assert result.residual_uncertainty.relevance_bound
    assert result.residual_uncertainty.future_trigger_conditions


def test_blocked_claim_refused_by_downstream_mock() -> None:
    result = _run(
        "downstream-refuse",
        clone_bundle(
            w06_bundle("downstream-refuse"),
            mismatch_intake=w06_mismatch("downstream-refuse", mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
        ),
    )
    can_claim = result.downstream_packet.may_continue_narrowly and not result.downstream_packet.must_block_claim
    assert can_claim is False


def test_blocked_reason_is_preserved() -> None:
    result = _run("blocked-reason", w06_bundle("blocked-reason"))
    assert result.claim_block_packet.blocked_reason


def test_allowed_narrow_claims_remain_available_when_safe() -> None:
    result = _run(
        "narrow-claims",
        clone_bundle(
            w06_bundle("narrow-claims"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("narrow-claims", mismatch_class=W06MismatchClass.INSUFFICIENT_EVIDENCE),
        ),
    )
    assert isinstance(result.claim_block_packet.allowed_narrow_claims, tuple)


def test_action_effect_error_not_world_model_by_default() -> None:
    result = _run(
        "action-effect-scope",
        clone_bundle(
            w06_bundle("action-effect-scope"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("action-effect-scope", mismatch_class=W06MismatchClass.ACTION_EFFECT),
        ),
    )
    assert result.decision.revision_scope is W06RevisionScope.ACTION_EFFECT_LEVEL


def test_ownership_error_not_goal_satisfaction_by_default() -> None:
    result = _run(
        "ownership-scope",
        clone_bundle(
            w06_bundle("ownership-scope"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("ownership-scope", mismatch_class=W06MismatchClass.OWNERSHIP),
        ),
    )
    assert result.decision.revision_scope is W06RevisionScope.OWNERSHIP_LEVEL


def test_validity_error_not_affordance_by_default() -> None:
    result = _run(
        "validity-scope",
        clone_bundle(
            w06_bundle("validity-scope"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("validity-scope", mismatch_class=W06MismatchClass.VALIDITY),
        ),
    )
    assert result.decision.revision_scope is W06RevisionScope.VALIDITY_LEVEL


def test_authority_error_blocks_or_revalidates_authority_scope() -> None:
    result = _run(
        "authority-scope",
        clone_bundle(
            w06_bundle("authority-scope"),
            mismatch_intake=w06_mismatch("authority-scope", mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
        ),
    )
    assert result.decision.revision_scope is W06RevisionScope.AUTHORITY_SCOPE_LEVEL
    assert result.gate.must_block_claim or result.gate.must_revalidate


def test_protected_target_escalates_or_blocks() -> None:
    result = _run(
        "protected-target",
        clone_bundle(
            w06_bundle("protected-target"),
            mismatch_intake=w06_mismatch(
                "protected-target",
                mismatch_class=W06MismatchClass.CONSTITUTIONAL_BOUNDARY,
                constitutional_guard_flags=("protected",),
            ),
        ),
    )
    assert result.gate.must_escalate or result.gate.must_block_claim


def test_guardrail_flags_preserved() -> None:
    result = _run("guardrail-preserved", w06_bundle("guardrail-preserved"))
    assert "must_not_execute_correction" in result.consequence.guardrail_flags


def test_no_correction_execution_route() -> None:
    result = _run("no-exec-route", w06_bundle("no-exec-route"))
    assert result.correction_candidate.execution_prohibited is True
    assert result.downstream_packet.must_not_execute_correction is True


def test_ablation_disabling_residue_retention_changes_downstream_route() -> None:
    original = w06_policy._build_residual_uncertainty

    def _no_residue(*, tick_id, mismatch, consequence, prohibited_claims):
        residue = original(
            tick_id=tick_id,
            mismatch=mismatch,
            consequence=consequence,
            prohibited_claims=prohibited_claims,
        )
        return replace(residue, retained_markers=(), visibility_to_downstream=False)

    w06_policy._build_residual_uncertainty = _no_residue
    try:
        result = _run(
            "ablation-residue",
            clone_bundle(
                w06_bundle("ablation-residue"),
                mismatch_intake=w06_mismatch("ablation-residue", mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
            ),
        )
    finally:
        w06_policy._build_residual_uncertainty = original

    assert result.downstream_packet.must_block_claim is True
    assert result.downstream_packet.must_quarantine is True
    assert "claim_block_requires_residue_markers" in result.decision.decision_reason_codes
    assert result.downstream_packet.must_not_execute_correction is True


def test_ablation_disabling_anti_paralysis_changes_route_under_loop() -> None:
    baseline = _run(
        "ablation-anti",
        clone_bundle(
            w06_bundle("ablation-anti"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("ablation-anti", mismatch_class=W06MismatchClass.VALIDITY),
            revision_context=w06_context("ablation-anti", repeated_revalidation_count=6, progress_detected=False),
        ),
    )
    original = w06_policy._build_anti_paralysis_state

    def _no_escape(*, context, current_consequence, reason_codes):
        return replace(
            original(
                context=context,
                current_consequence=current_consequence,
                reason_codes=reason_codes,
            ),
            chosen_escape_route=W06ConsequenceType.REVALIDATE,
            reason_codes=tuple(dict.fromkeys((*reason_codes, "anti_paralysis_disabled_for_test"))),
        )

    w06_policy._build_anti_paralysis_state = _no_escape
    try:
        ablated = _run(
            "ablation-anti-disabled",
            clone_bundle(
                w06_bundle("ablation-anti-disabled"),
                contradiction_intake=(),
                mismatch_intake=w06_mismatch("ablation-anti-disabled", mismatch_class=W06MismatchClass.VALIDITY),
                revision_context=w06_context("ablation-anti-disabled", repeated_revalidation_count=6, progress_detected=False),
            ),
        )
    finally:
        w06_policy._build_anti_paralysis_state = original

    assert baseline.anti_paralysis_state.chosen_escape_route is not W06ConsequenceType.REVALIDATE
    assert ablated.anti_paralysis_state.chosen_escape_route is W06ConsequenceType.REVALIDATE
    assert baseline.decision.consequence_type != ablated.decision.consequence_type


def test_ablation_disabling_identity_routing_would_fail_identity_conflict_scenario() -> None:
    result = _run(
        "ablation-identity",
        clone_bundle(
            w06_bundle("ablation-identity"),
            contradiction_intake=(w06_contradiction("ablation-identity", conflict_type="duplicate_identity_conflict"),),
        ),
    )
    assert result.identity_revision.identity_route is not W06IdentityRoute.NONE


def test_ablation_disabling_execution_seam_would_fail() -> None:
    result = _run("ablation-exec-seam", w06_bundle("ablation-exec-seam"))
    assert result.gate.must_not_execute_correction is True
    assert result.downstream_packet.must_not_execute_correction is True


def test_blocked_claim_and_residue_are_both_required_for_blocked_claim_consumer_obedience() -> None:
    baseline = _run(
        "blocked-with-residue",
        clone_bundle(
            w06_bundle("blocked-with-residue"),
            mismatch_intake=w06_mismatch("blocked-with-residue", mismatch_class=W06MismatchClass.AUTHORITY_SCOPE),
        ),
    )
    assert baseline.downstream_packet.must_block_claim is True
    assert baseline.downstream_packet.preserved_uncertainty_markers
    assert baseline.downstream_packet.may_continue_narrowly is False

    original_residue = w06_policy._build_residual_uncertainty
    original_blocked = w06_policy._blocked_claim_types

    def _no_residue(*, tick_id, mismatch, consequence, prohibited_claims):
        residue = original_residue(
            tick_id=tick_id,
            mismatch=mismatch,
            consequence=consequence,
            prohibited_claims=prohibited_claims,
        )
        return replace(residue, retained_markers=(), visibility_to_downstream=False)

    def _no_blocked_claims(*, mismatch, consequence, identity, unresolved_contradiction):
        return ()

    w06_policy._build_residual_uncertainty = _no_residue
    w06_policy._blocked_claim_types = _no_blocked_claims
    try:
        ablated = _run(
            "blocked-without-obedience-signals",
            clone_bundle(
                w06_bundle("blocked-without-obedience-signals"),
                mismatch_intake=w06_mismatch(
                    "blocked-without-obedience-signals",
                    mismatch_class=W06MismatchClass.AUTHORITY_SCOPE,
                ),
            ),
        )
    finally:
        w06_policy._build_residual_uncertainty = original_residue
        w06_policy._blocked_claim_types = original_blocked

    assert ablated.downstream_packet.must_block_claim is True
    assert ablated.downstream_packet.must_quarantine is True
    assert "expected_claim_block_missing" in ablated.decision.decision_reason_codes
    assert "claim_block_requires_residue_markers" in ablated.decision.decision_reason_codes
    assert ablated.downstream_packet.must_not_execute_correction is True


def test_telemetry_reconstructs_revision_path() -> None:
    result = _run("telemetry", w06_bundle("telemetry"))
    assert result.telemetry.mismatch_intake_count == 1
    assert result.telemetry.consequence_matrix_count == 1
    assert result.telemetry.downstream_packet_count == 1


def test_clean_revision_route_status_is_typed() -> None:
    result = _run(
        "route-status",
        clone_bundle(
            w06_bundle("route-status"),
            contradiction_intake=(),
            mismatch_intake=w06_mismatch("route-status", mismatch_class=W06MismatchClass.NO_MISMATCH, evidence_precision=0.9),
        ),
    )
    assert result.decision.route_status in {
        W06RouteStatus.CLEAN_REVISION_ROUTE,
        W06RouteStatus.NARROW_CONTINUATION,
    }
