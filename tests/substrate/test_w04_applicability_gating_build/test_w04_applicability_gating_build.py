from __future__ import annotations

from dataclasses import replace

from substrate.w04_applicability_gating import (
    W04ApplicabilityDecisionStatus,
    W04ConstraintHardness,
    W04ConstraintType,
)
from tests.substrate.w04_applicability_gating_testkit import (
    build_w04_harness,
    clone_input,
    w04_constraint,
    w04_context,
    w04_desired_state,
    w04_input_bundle,
    w04_intake,
    w04_perspective,
    w04_profile,
)


def _base_bundle(case_id: str):
    intake = w04_intake(case_id=case_id)
    desired = w04_desired_state(case_id=case_id)
    ctx = w04_context(case_id=case_id)
    perspective = w04_perspective()
    profile = w04_profile(
        case_id=case_id,
        world_constraints=(
            w04_constraint(
                constraint_id=f"{case_id}:world_hard",
                constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
                hard_or_soft=W04ConstraintHardness.HARD,
                current_status="passed",
            ),
        ),
        epistemic_constraints=(
            w04_constraint(
                constraint_id=f"{case_id}:soft_epistemic",
                constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
                hard_or_soft=W04ConstraintHardness.SOFT,
                current_status="passed",
                forbidden_condition=("soft_conflict",),
            ),
        ),
    )
    return w04_input_bundle(
        case_id=case_id,
        intake_views=(intake,),
        desired_state=desired,
        context=ctx,
        perspective=perspective,
        profile=profile,
    )


def _run(case_id: str, bundle):
    return build_w04_harness(case_id, input_bundle=bundle)


def _first_decision(result):
    return result.applicability_decisions[0]


def _first_packet(result):
    return result.downstream_permission_packets[0]


def test_clean_w03_prior_with_clean_constraints_allows_bounded_deployment() -> None:
    result = _run("clean", _base_bundle("clean"))
    decision = _first_decision(result)
    packet = _first_packet(result)
    assert decision.decision_status is W04ApplicabilityDecisionStatus.ALLOWED
    assert packet.may_deploy_candidate is True
    assert packet.action_authorization_granted is False


def test_w03_must_abstain_blocks_applicability() -> None:
    bundle = _base_bundle("w03-must-abstain")
    intake = replace(bundle.w03_intake_views[0], must_abstain=True)
    result = _run("w03-must-abstain", clone_input(bundle, w03_intake_views=(intake,)))
    decision = _first_decision(result)
    packet = _first_packet(result)
    assert decision.decision_status is W04ApplicabilityDecisionStatus.ABSTAIN
    assert packet.must_abstain is True
    assert packet.may_deploy_candidate is False


def test_w03_must_revalidate_blocks_clean_deployment() -> None:
    bundle = _base_bundle("w03-revalidate")
    intake = replace(bundle.w03_intake_views[0], must_revalidate_before_use=True)
    result = _run("w03-revalidate", clone_input(bundle, w03_intake_views=(intake,)))
    packet = _first_packet(result)
    assert packet.must_revalidate is True
    assert packet.may_deploy_candidate is False


def test_w03_stale_prior_requires_revalidation() -> None:
    bundle = _base_bundle("w03-stale")
    intake = replace(bundle.w03_intake_views[0], stale_or_revalidation_status=("stale",))
    result = _run("w03-stale", clone_input(bundle, w03_intake_views=(intake,)))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED


def test_w03_contested_prior_preserves_contradiction_and_blocks_clean_deploy() -> None:
    bundle = _base_bundle("w03-contested")
    intake = replace(
        bundle.w03_intake_views[0],
        contradiction_status=("c1",),
        must_preserve_contradiction=True,
    )
    result = _run("w03-contested", clone_input(bundle, w03_intake_views=(intake,)))
    packet = _first_packet(result)
    assert packet.may_deploy_candidate is False
    assert packet.must_preserve_hard_constraints is True
    assert packet.may_use_as_hint_only is True


def test_missing_w03_authority_scope_blocks_clean_applicability() -> None:
    bundle = _base_bundle("authority-missing")
    intake = replace(bundle.w03_intake_views[0], authority_scope=())
    result = _run("authority-missing", clone_input(bundle, w03_intake_views=(intake,)))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.BLOCKED


def test_w03_prohibited_claims_are_preserved_in_w04_downstream_packet() -> None:
    bundle = _base_bundle("w03-prohibited-propagation")
    intake = replace(
        bundle.w03_intake_views[0],
        prohibited_claims=(
            "no_universal_world_truth",
            "no_stable_object_identity",
            "no_action_authorization",
            "no_broad_context_transfer",
        ),
    )
    result = _run(
        "w03-prohibited-propagation",
        clone_input(bundle, w03_intake_views=(intake,)),
    )
    decision = _first_decision(result)
    packet = _first_packet(result)
    assert decision.decision_status is W04ApplicabilityDecisionStatus.ALLOWED
    assert "no_universal_world_truth" in packet.prohibited_uses
    assert "no_stable_object_identity" in packet.prohibited_uses
    assert "no_action_authorization" in packet.prohibited_uses
    assert "no_broad_context_transfer" in packet.prohibited_uses
    assert "action_authorization_from_w04" in packet.prohibited_uses
    assert "preserve_upstream_prohibited_claims" in packet.required_preserved_markers
    assert packet.action_authorization_granted is False


def test_missing_desired_state_target_is_malformed_and_abstains() -> None:
    bundle = _base_bundle("desired-missing-target")
    desired = replace(bundle.desired_state_request, target_subject="")
    result = _run("desired-missing-target", clone_input(bundle, desired_state_request=desired))
    packet = _first_packet(result)
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.MALFORMED_REQUEST
    assert packet.must_block is True


def test_missing_desired_state_provenance_or_authority_blocks_clean_deploy() -> None:
    bundle = _base_bundle("desired-missing-source")
    missing_source = replace(bundle.desired_state_request, source_authority="")
    missing_provenance = replace(bundle.desired_state_request, provenance=())

    source_result = _run(
        "desired-missing-source",
        clone_input(bundle, desired_state_request=missing_source),
    )
    provenance_result = _run(
        "desired-missing-provenance",
        clone_input(bundle, desired_state_request=missing_provenance),
    )
    for result in (source_result, provenance_result):
        decision = _first_decision(result)
        packet = _first_packet(result)
        assert decision.decision_status is W04ApplicabilityDecisionStatus.MALFORMED_REQUEST
        assert packet.may_deploy_candidate is False
        assert packet.action_authorization_granted is False
        assert packet.must_block is True
        assert any(
            code in packet.decision_reason_codes
            for code in ("missing_desired_state_source_authority", "missing_desired_state_provenance")
        )


def test_self_contradictory_desired_state_is_rejected() -> None:
    bundle = _base_bundle("desired-self-contradict")
    desired = replace(bundle.desired_state_request, malformed_markers=("self_contradictory",))
    result = _run("desired-self-contradict", clone_input(bundle, desired_state_request=desired))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.MALFORMED_REQUEST


def test_desired_state_embedded_forbidden_conclusion_is_blocked() -> None:
    bundle = _base_bundle("desired-forbidden")
    desired = replace(bundle.desired_state_request, embedded_forbidden_conclusions=("authorize_action",))
    result = _run("desired-forbidden", clone_input(bundle, desired_state_request=desired))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.MALFORMED_REQUEST


def test_desired_state_priority_does_not_override_hard_constraint() -> None:
    bundle = _base_bundle("priority-hard")
    failed_hard = w04_constraint(
        constraint_id="priority-hard:world_hard",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.HARD,
        current_status="failed",
    )
    profile = w04_profile(case_id="priority-hard", world_constraints=(failed_hard,))
    desired = replace(bundle.desired_state_request, priority="urgent")
    result = _run("priority-hard", clone_input(bundle, desired_state_request=desired, constraint_profile=profile))
    assert _first_packet(result).may_deploy_candidate is False


def test_hard_world_constraint_failure_blocks_deploy() -> None:
    bundle = _base_bundle("hard-world-fail")
    failed_hard = w04_constraint(
        constraint_id="hard-world-fail:hard",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.HARD,
        current_status="failed",
    )
    profile = w04_profile(case_id="hard-world-fail", world_constraints=(failed_hard,))
    result = _run("hard-world-fail", clone_input(bundle, constraint_profile=profile))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.BLOCKED


def test_soft_world_constraint_conflict_can_relax_only_with_ledger() -> None:
    bundle = _base_bundle("soft-relax")
    soft = w04_constraint(
        constraint_id="soft_conflict",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
        forbidden_condition=("soft_conflict",),
    )
    profile = w04_profile(
        case_id="soft-relax",
        world_constraints=(bundle.constraint_profile.world_constraints[0],),
        epistemic_constraints=(soft,),
    )
    desired = replace(bundle.desired_state_request, acceptable_relaxation_dimensions=("soft_conflict",))
    result = _run("soft-relax", clone_input(bundle, desired_state_request=desired, constraint_profile=profile))
    packet = _first_packet(result)
    assert packet.may_use_with_relaxation is True
    assert result.relaxation_ledger_entries


def test_same_constraint_soft_vs_hard_changes_decision() -> None:
    base = _base_bundle("soft-vs-hard")
    soft = w04_constraint(
        constraint_id="same",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
    )
    hard = w04_constraint(
        constraint_id="same",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.HARD,
        current_status="failed",
    )
    soft_profile = w04_profile(case_id="soft-vs-hard:soft", world_constraints=(soft,))
    hard_profile = w04_profile(case_id="soft-vs-hard:hard", world_constraints=(hard,))
    soft_result = _run("soft-vs-hard:soft", clone_input(base, constraint_profile=soft_profile))
    hard_result = _run("soft-vs-hard:hard", clone_input(base, constraint_profile=hard_profile))
    assert _first_decision(soft_result).decision_status in {
        W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION,
        W04ApplicabilityDecisionStatus.NARROWED,
        W04ApplicabilityDecisionStatus.RELAXABLE,
    }
    assert _first_decision(hard_result).decision_status is W04ApplicabilityDecisionStatus.BLOCKED


def test_unknown_hard_feasibility_routes_to_revalidation_or_abstain() -> None:
    base = _base_bundle("unknown-hard")
    unknown = w04_constraint(
        constraint_id="unknown-hard:hard",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED,
        current_status="unknown",
    )
    profile = w04_profile(case_id="unknown-hard", world_constraints=(unknown,))
    result = _run("unknown-hard", clone_input(base, constraint_profile=profile))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED


def test_empty_intersection_blocks_without_silent_force_fit() -> None:
    base = _base_bundle("empty-hard")
    hard_fail = w04_constraint(
        constraint_id="empty-hard:hard",
        constraint_type=W04ConstraintType.SAFETY_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.HARD,
        current_status="failed",
    )
    profile = w04_profile(case_id="empty-hard", safety_constraints=(hard_fail,))
    result = _run("empty-hard", clone_input(base, constraint_profile=profile))
    assert _first_packet(result).must_block is True


def test_empty_soft_intersection_can_narrow_or_relax_with_ledger() -> None:
    base = _base_bundle("empty-soft")
    soft_fail = w04_constraint(
        constraint_id="soft_conflict",
        constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
    )
    profile = w04_profile(
        case_id="empty-soft",
        world_constraints=base.constraint_profile.world_constraints,
        epistemic_constraints=(soft_fail,),
    )
    desired = replace(base.desired_state_request, acceptable_relaxation_dimensions=("soft_conflict",))
    result = _run("empty-soft", clone_input(base, desired_state_request=desired, constraint_profile=profile))
    assert _first_decision(result).decision_status in {
        W04ApplicabilityDecisionStatus.ALLOWED_WITH_RELAXATION,
        W04ApplicabilityDecisionStatus.RELAXABLE,
        W04ApplicabilityDecisionStatus.NARROWED,
    }


def test_relaxation_ledger_records_original_bound_authority_and_residual_risk() -> None:
    base = _base_bundle("relax-ledger")
    soft_fail = w04_constraint(
        constraint_id="soft_conflict",
        constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
    )
    profile = w04_profile(case_id="relax-ledger", world_constraints=base.constraint_profile.world_constraints, epistemic_constraints=(soft_fail,))
    desired = replace(base.desired_state_request, acceptable_relaxation_dimensions=("soft_conflict",))
    result = _run("relax-ledger", clone_input(base, desired_state_request=desired, constraint_profile=profile))
    assert result.relaxation_ledger_entries
    entry = result.relaxation_ledger_entries[0]
    assert entry.original_constraint
    assert entry.relaxation_bound
    assert entry.relaxation_authority
    assert entry.residual_risk


def test_hard_constraint_cannot_be_relaxed() -> None:
    base = _base_bundle("hard-cannot-relax")
    hard_fail = w04_constraint(
        constraint_id="hard-cannot-relax:hard",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.HARD,
        current_status="failed",
    )
    profile = w04_profile(case_id="hard-cannot-relax", world_constraints=(hard_fail,))
    desired = replace(base.desired_state_request, acceptable_relaxation_dimensions=("hard-cannot-relax:hard",))
    result = _run("hard-cannot-relax", clone_input(base, desired_state_request=desired, constraint_profile=profile))
    assert not result.relaxation_ledger_entries
    assert _first_packet(result).may_use_with_relaxation is False


def test_overbroad_desired_state_relaxation_request_is_rejected_or_narrowed() -> None:
    base = _base_bundle("overbroad-relaxation")
    soft_fail = w04_constraint(
        constraint_id="soft_conflict",
        constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
    )
    profile = w04_profile(
        case_id="overbroad-relaxation",
        world_constraints=base.constraint_profile.world_constraints,
        epistemic_constraints=(soft_fail,),
    )
    desired = replace(
        base.desired_state_request,
        acceptable_relaxation_dimensions=("hard_constraints", "all", "authority_scope", "perspective_scope"),
    )
    result = _run(
        "overbroad-relaxation",
        clone_input(base, desired_state_request=desired, constraint_profile=profile),
    )
    decision = _first_decision(result)
    packet = _first_packet(result)
    assert decision.decision_status is W04ApplicabilityDecisionStatus.MALFORMED_REQUEST
    assert packet.may_deploy_candidate is False
    assert packet.may_use_with_relaxation is False
    assert not result.relaxation_ledger_entries
    assert "overbroad_relaxation_request" in packet.decision_reason_codes
    assert packet.action_authorization_granted is False


def test_authority_scope_mismatch_blocks_or_revalidates() -> None:
    base = _base_bundle("authority-mismatch")
    desired = replace(base.desired_state_request, source_authority="other_authority")
    result = _run("authority-mismatch", clone_input(base, desired_state_request=desired))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.BLOCKED


def test_narrow_authority_scope_does_not_become_global_applicability() -> None:
    base = _base_bundle("authority-narrow")
    intake = replace(base.w03_intake_views[0], authority_scope=("trusted_authority",))
    result = _run("authority-narrow", clone_input(base, w03_intake_views=(intake,)))
    packet = _first_packet(result)
    assert "authority_scope_broadening_from_w04" in packet.prohibited_uses


def test_perspective_transfer_requires_explicit_permission() -> None:
    base = _base_bundle("perspective-transfer")
    frame = w04_perspective(
        requested_perspective="other",
        source_perspective="self",
        allowed_perspective_transfer=(),
        blocked_perspective_transfer=("self->other",),
    )
    desired = replace(base.desired_state_request, perspective_id="other")
    result = _run("perspective-transfer", clone_input(base, perspective_frame=frame, desired_state_request=desired))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.BLOCKED


def test_actor_observer_subject_boundaries_do_not_collapse() -> None:
    base = _base_bundle("boundary-no-collapse")
    frame = replace(base.perspective_frame, requested_perspective="other", source_perspective="self", blocked_perspective_transfer=("self->other",))
    desired = replace(base.desired_state_request, perspective_id="other")
    result = _run("boundary-no-collapse", clone_input(base, perspective_frame=frame, desired_state_request=desired))
    assert _first_packet(result).must_preserve_perspective_scope is True


def test_prior_valid_for_actor_a_not_clean_for_actor_b_without_transfer() -> None:
    base = _base_bundle("actor-a-vs-b")
    ctx = replace(base.active_context, active_actor_id="actor_b")
    desired = replace(base.desired_state_request, actor_id="actor_b", perspective_id="other")
    frame = replace(base.perspective_frame, requested_perspective="other", blocked_perspective_transfer=("self->other",))
    result = _run("actor-a-vs-b", clone_input(base, active_context=ctx, desired_state_request=desired, perspective_frame=frame))
    assert _first_packet(result).may_deploy_candidate is False


def test_temporal_window_expired_blocks_or_revalidates() -> None:
    base = _base_bundle("temporal-expired")
    desired = replace(base.desired_state_request, temporal_window=(1, 1))
    ctx = replace(base.active_context, current_time_or_sequence=10)
    result = _run("temporal-expired", clone_input(base, desired_state_request=desired, active_context=ctx))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED


def test_missing_freshness_basis_prevents_clean_deployment() -> None:
    base = _base_bundle("missing-freshness")
    desired = replace(base.desired_state_request, temporal_window=None)
    ctx = replace(base.active_context, unavailable_or_unknown_markers=("missing_freshness_basis",))
    result = _run("missing-freshness", clone_input(base, desired_state_request=desired, active_context=ctx))
    assert _first_packet(result).may_deploy_candidate is False


def test_legality_unknown_is_not_allowed() -> None:
    base = _base_bundle("legality-unknown")
    legality = w04_constraint(
        constraint_id="legality-unknown:c",
        constraint_type=W04ConstraintType.LEGALITY_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED,
        current_status="unknown",
    )
    profile = w04_profile(case_id="legality-unknown", legality_constraints=(legality,))
    result = _run("legality-unknown", clone_input(base, constraint_profile=profile))
    assert _first_packet(result).may_deploy_candidate is False


def test_safety_unknown_is_not_allowed() -> None:
    base = _base_bundle("safety-unknown")
    safety = w04_constraint(
        constraint_id="safety-unknown:c",
        constraint_type=W04ConstraintType.SAFETY_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED,
        current_status="unknown",
    )
    profile = w04_profile(case_id="safety-unknown", safety_constraints=(safety,))
    result = _run("safety-unknown", clone_input(base, constraint_profile=profile))
    assert _first_decision(result).decision_status is W04ApplicabilityDecisionStatus.REVALIDATE_REQUIRED


def test_downstream_packet_exact_for_allowed_blocked_hint_revalidate_relaxation() -> None:
    allowed = _run("packet-allowed", _base_bundle("packet-allowed"))
    assert _first_packet(allowed).may_deploy_candidate is True

    blocked_bundle = _base_bundle("packet-blocked")
    blocked_profile = w04_profile(
        case_id="packet-blocked",
        world_constraints=(
            w04_constraint(
                constraint_id="packet-blocked:hard",
                constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
                hard_or_soft=W04ConstraintHardness.HARD,
                current_status="failed",
            ),
        ),
    )
    blocked = _run("packet-blocked", clone_input(blocked_bundle, constraint_profile=blocked_profile))
    assert _first_packet(blocked).must_block is True

    hint_bundle = _base_bundle("packet-hint")
    hint_intake = replace(hint_bundle.w03_intake_views[0], may_use_as_bounded_prior=False, may_use_as_schema_hint=True)
    hint = _run("packet-hint", clone_input(hint_bundle, w03_intake_views=(hint_intake,)))
    assert _first_packet(hint).may_use_as_hint_only is True

    revalidate_bundle = _base_bundle("packet-revalidate")
    revalidate_intake = replace(revalidate_bundle.w03_intake_views[0], must_revalidate_before_use=True)
    revalidate = _run("packet-revalidate", clone_input(revalidate_bundle, w03_intake_views=(revalidate_intake,)))
    assert _first_packet(revalidate).must_revalidate is True

    relax_bundle = _base_bundle("packet-relax")
    soft_fail = w04_constraint(
        constraint_id="soft_conflict",
        constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
    )
    relax_profile = w04_profile(case_id="packet-relax", world_constraints=relax_bundle.constraint_profile.world_constraints, epistemic_constraints=(soft_fail,))
    relax_desired = replace(relax_bundle.desired_state_request, acceptable_relaxation_dimensions=("soft_conflict",))
    relax = _run("packet-relax", clone_input(relax_bundle, constraint_profile=relax_profile, desired_state_request=relax_desired))
    assert _first_packet(relax).may_use_with_relaxation is True


def test_applicability_approval_never_grants_action_authorization() -> None:
    result = _run("no-action-auth", _base_bundle("no-action-auth"))
    assert _first_packet(result).action_authorization_granted is False


def test_bypass_raw_w03_prior_without_w04_packet_is_blocked() -> None:
    result = _run("no-input", None)
    assert result.gate.no_clean_applicability is True
    assert result.gate.consumer_ready is False


def test_ablation_removing_hard_soft_separation_changes_outcome() -> None:
    base = _base_bundle("ablation-hard-soft")
    hard = w04_constraint(
        constraint_id="same:c",
        constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.HARD,
        current_status="failed",
    )
    soft = replace(hard, hard_or_soft=W04ConstraintHardness.SOFT)
    hard_profile = w04_profile(case_id="ablation-hard-soft:hard", world_constraints=(hard,))
    soft_profile = w04_profile(case_id="ablation-hard-soft:soft", world_constraints=(soft,))
    hard_result = _run("ablation-hard-soft:hard", clone_input(base, constraint_profile=hard_profile))
    soft_result = _run("ablation-hard-soft:soft", clone_input(base, constraint_profile=soft_profile))
    assert _first_packet(hard_result).may_deploy_candidate is False
    assert _first_decision(soft_result).decision_status is not W04ApplicabilityDecisionStatus.BLOCKED


def test_ablation_removing_perspective_frame_changes_outcome() -> None:
    base = _base_bundle("ablation-perspective")
    blocked_frame = replace(base.perspective_frame, requested_perspective="other", blocked_perspective_transfer=("self->other",))
    desired = replace(base.desired_state_request, perspective_id="other")
    blocked = _run("ablation-perspective:block", clone_input(base, perspective_frame=blocked_frame, desired_state_request=desired))
    allowed_frame = replace(base.perspective_frame, requested_perspective="other", allowed_perspective_transfer=("self->other",), blocked_perspective_transfer=())
    allowed = _run("ablation-perspective:allow", clone_input(base, perspective_frame=allowed_frame, desired_state_request=desired))
    assert _first_packet(blocked).may_deploy_candidate is False
    assert _first_packet(allowed).may_deploy_candidate is True


def test_ablation_removing_authority_scope_changes_outcome() -> None:
    base = _base_bundle("ablation-authority")
    missing = replace(base.w03_intake_views[0], authority_scope=())
    blocked = _run("ablation-authority:block", clone_input(base, w03_intake_views=(missing,)))
    allowed = _run("ablation-authority:allow", base)
    assert _first_packet(blocked).may_deploy_candidate is False
    assert _first_packet(allowed).may_deploy_candidate is True


def test_ablation_removing_relaxation_ledger_changes_outcome() -> None:
    base = _base_bundle("ablation-relax-ledger")
    soft_fail = w04_constraint(
        constraint_id="soft_conflict",
        constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
        hard_or_soft=W04ConstraintHardness.SOFT,
        current_status="failed",
    )
    profile = w04_profile(case_id="ablation-relax-ledger", world_constraints=base.constraint_profile.world_constraints, epistemic_constraints=(soft_fail,))
    with_ledger_desired = replace(base.desired_state_request, acceptable_relaxation_dimensions=("soft_conflict",))
    without_ledger_desired = replace(base.desired_state_request, acceptable_relaxation_dimensions=())
    with_ledger = _run("ablation-relax-ledger:yes", clone_input(base, constraint_profile=profile, desired_state_request=with_ledger_desired))
    without_ledger = _run("ablation-relax-ledger:no", clone_input(base, constraint_profile=profile, desired_state_request=without_ledger_desired))
    assert _first_packet(with_ledger).may_use_with_relaxation is True
    assert _first_packet(without_ledger).may_use_with_relaxation is False


def test_telemetry_reconstructs_applicability_path() -> None:
    result = _run("telemetry", _base_bundle("telemetry"))
    telemetry = result.telemetry
    assert telemetry.desired_state_intake_count == 1
    assert telemetry.w03_candidate_intake_count >= 1
    assert telemetry.applicability_decision_count >= 1
    assert telemetry.consumer_ready in {True, False}
