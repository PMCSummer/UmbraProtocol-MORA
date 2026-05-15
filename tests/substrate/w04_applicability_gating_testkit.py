from __future__ import annotations

from dataclasses import replace

from substrate.w04_applicability_gating import (
    W04ActiveApplicabilityContext,
    W04Constraint,
    W04ConstraintHardness,
    W04ConstraintProfile,
    W04ConstraintType,
    W04DesiredStateRequest,
    W04InputBundle,
    W04PerspectiveFrame,
    W04ResultBundle,
    W04W03IntakeView,
    build_w04_applicability_gating,
)


def w04_constraint(
    *,
    constraint_id: str,
    constraint_type: W04ConstraintType,
    hard_or_soft: W04ConstraintHardness,
    current_status: str = "passed",
    source_authority: str = "trusted_authority",
    required_condition: tuple[str, ...] = (),
    forbidden_condition: tuple[str, ...] = (),
) -> W04Constraint:
    return W04Constraint(
        constraint_id=constraint_id,
        constraint_type=constraint_type,
        hard_or_soft=hard_or_soft,
        source_authority=source_authority,
        target_scope=("bounded_context",),
        required_condition=required_condition,
        forbidden_condition=forbidden_condition,
        current_status=current_status,
        enforcement_route="default_route",
        provenance=("tests.w04", constraint_id),
    )


def w04_intake(
    *,
    case_id: str,
    prior_id: str = "prior:1",
    schema_id: str = "schema:1",
    candidate_id: str = "candidate:1",
    authority_scope: tuple[str, ...] = ("trusted_authority",),
    context_scope: tuple[str, ...] = ("self",),
    stale_or_revalidation_status: tuple[str, ...] = (),
    contradiction_status: tuple[str, ...] = (),
    may_use_as_bounded_prior: bool = True,
    may_use_as_schema_hint: bool = True,
    may_use_as_operational_default: bool = False,
    must_revalidate_before_use: bool = False,
    must_preserve_contradiction: bool = False,
    must_abstain: bool = False,
) -> W04W03IntakeView:
    return W04W03IntakeView(
        prior_id=f"{case_id}:{prior_id}",
        schema_id=f"{case_id}:{schema_id}",
        candidate_id=f"{case_id}:{candidate_id}",
        permission_packet_ref=f"{case_id}:packet:1",
        support_refs=(f"{case_id}:support:1",),
        authority_scope=authority_scope,
        context_scope=context_scope,
        applicability_conditions=("bounded_by_w03_scope",),
        stale_or_revalidation_status=stale_or_revalidation_status,
        contradiction_status=contradiction_status,
        prohibited_claims=("world_truth_claim",),
        allowed_use_cases=("bounded_use",),
        blocked_use_cases=("global_use",),
        override_conditions=("live_w01_w02_override",),
        may_use_as_bounded_prior=may_use_as_bounded_prior,
        may_use_as_schema_hint=may_use_as_schema_hint,
        may_use_as_operational_default=may_use_as_operational_default,
        must_revalidate_before_use=must_revalidate_before_use,
        must_preserve_contradiction=must_preserve_contradiction,
        must_abstain=must_abstain,
    )


def w04_desired_state(
    *,
    case_id: str,
    requested_outcome: str = "bounded_deployment",
    actor_id: str = "actor_a",
    target_subject: str = "subject_a",
    perspective_id: str = "self",
    intended_use: str = "bounded_applicability",
    priority: str = "normal",
    temporal_window: tuple[int, int] | None = (1, 10),
    acceptable_relaxation_dimensions: tuple[str, ...] = ("soft_conflict",),
    non_negotiable_constraints: tuple[str, ...] = ("hard_non_negotiable",),
    source_authority: str = "trusted_authority",
    malformed_markers: tuple[str, ...] = (),
    embedded_forbidden_conclusions: tuple[str, ...] = (),
) -> W04DesiredStateRequest:
    return W04DesiredStateRequest(
        desired_state_id=f"{case_id}:desired",
        requested_outcome=requested_outcome,
        actor_id=actor_id,
        target_subject=target_subject,
        perspective_id=perspective_id,
        intended_use=intended_use,
        priority=priority,
        temporal_window=temporal_window,
        acceptable_relaxation_dimensions=acceptable_relaxation_dimensions,
        non_negotiable_constraints=non_negotiable_constraints,
        source_authority=source_authority,
        provenance=("tests.w04", case_id),
        malformed_markers=malformed_markers,
        embedded_forbidden_conclusions=embedded_forbidden_conclusions,
        requested_schema_or_prior_refs=(f"{case_id}:schema:1",),
    )


def w04_context(
    *,
    case_id: str,
    current_time_or_sequence: int = 1,
    unavailable_or_unknown_markers: tuple[str, ...] = (),
    stale_context_markers: tuple[str, ...] = (),
    active_actor_id: str = "actor_a",
    active_perspective_id: str = "self",
) -> W04ActiveApplicabilityContext:
    return W04ActiveApplicabilityContext(
        context_id=f"{case_id}:context",
        cycle_id=f"cycle:{case_id}",
        stream_id="rt01",
        current_time_or_sequence=current_time_or_sequence,
        world_context_refs=("world:1",),
        regularity_refs=(f"{case_id}:regularity:1",),
        schema_refs=(f"{case_id}:schema:1",),
        contradiction_refs=(),
        stale_context_markers=stale_context_markers,
        unavailable_or_unknown_markers=unavailable_or_unknown_markers,
        active_actor_id=active_actor_id,
        active_perspective_id=active_perspective_id,
        source_context_scope=("bounded_context",),
    )


def w04_perspective(
    *,
    requested_perspective: str = "self",
    source_perspective: str = "self",
    allowed_perspective_transfer: tuple[str, ...] = ("self->self",),
    blocked_perspective_transfer: tuple[str, ...] = (),
) -> W04PerspectiveFrame:
    return W04PerspectiveFrame(
        actor_scope="actor_a",
        observer_scope="observer_a",
        subject_scope="subject_a",
        source_perspective=source_perspective,
        requested_perspective=requested_perspective,
        allowed_perspective_transfer=allowed_perspective_transfer,
        blocked_perspective_transfer=blocked_perspective_transfer,
        self_other_boundary="preserved",
        authority_boundary="preserved",
        leakage_risk="low",
    )


def w04_profile(
    *,
    case_id: str,
    world_constraints: tuple[W04Constraint, ...] = (),
    legality_constraints: tuple[W04Constraint, ...] = (),
    epistemic_constraints: tuple[W04Constraint, ...] = (),
    temporal_constraints: tuple[W04Constraint, ...] = (),
    perspective_constraints: tuple[W04Constraint, ...] = (),
    authority_constraints: tuple[W04Constraint, ...] = (),
    safety_constraints: tuple[W04Constraint, ...] = (),
    downstream_contract_constraints: tuple[W04Constraint, ...] = (),
    malformed_markers: tuple[str, ...] = (),
) -> W04ConstraintProfile:
    hard_count = sum(
        1
        for item in (
            *world_constraints,
            *legality_constraints,
            *epistemic_constraints,
            *temporal_constraints,
            *perspective_constraints,
            *authority_constraints,
            *safety_constraints,
            *downstream_contract_constraints,
        )
        if item.hard_or_soft in {W04ConstraintHardness.HARD, W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED}
    )
    soft_count = sum(
        1
        for item in (
            *world_constraints,
            *legality_constraints,
            *epistemic_constraints,
            *temporal_constraints,
            *perspective_constraints,
            *authority_constraints,
            *safety_constraints,
            *downstream_contract_constraints,
        )
        if item.hard_or_soft is W04ConstraintHardness.SOFT
    )
    unknown_hard_count = sum(
        1
        for item in (
            *world_constraints,
            *legality_constraints,
            *epistemic_constraints,
            *temporal_constraints,
            *perspective_constraints,
            *authority_constraints,
            *safety_constraints,
            *downstream_contract_constraints,
        )
        if item.hard_or_soft is W04ConstraintHardness.UNKNOWN_HARD_UNTIL_VERIFIED
    )
    return W04ConstraintProfile(
        profile_id=f"{case_id}:profile",
        world_constraints=world_constraints,
        legality_constraints=legality_constraints,
        epistemic_constraints=epistemic_constraints,
        temporal_constraints=temporal_constraints,
        perspective_constraints=perspective_constraints,
        authority_constraints=authority_constraints,
        safety_constraints=safety_constraints,
        downstream_contract_constraints=downstream_contract_constraints,
        profile_source_authority="trusted_authority",
        hard_constraint_count=hard_count,
        soft_constraint_count=soft_count,
        unknown_hard_count=unknown_hard_count,
        malformed_markers=malformed_markers,
    )


def w04_input_bundle(
    *,
    case_id: str,
    intake_views: tuple[W04W03IntakeView, ...],
    desired_state: W04DesiredStateRequest,
    context: W04ActiveApplicabilityContext,
    perspective: W04PerspectiveFrame,
    profile: W04ConstraintProfile,
    source_lineage: tuple[str, ...] = (),
) -> W04InputBundle:
    return W04InputBundle(
        bundle_id=f"{case_id}:bundle",
        source_lineage=source_lineage or ("tests.w04", case_id),
        w03_intake_views=intake_views,
        desired_state_request=desired_state,
        active_context=context,
        perspective_frame=perspective,
        constraint_profile=profile,
        reason=case_id,
    )


def build_w04_harness(case_id: str, *, input_bundle: W04InputBundle | None, enforcement_enabled: bool = True) -> W04ResultBundle:
    return build_w04_applicability_gating(
        tick_id=f"tests.w04:{case_id}",
        tick_index=1,
        input_bundle=input_bundle,
        enforcement_enabled=enforcement_enabled,
    )


def w04_input_from_w03_result(*, case_id: str, w03_result) -> W04InputBundle:
    intake_views: list[W04W03IntakeView] = []
    candidates = tuple(getattr(w03_result, "schema_candidates", ()))
    packets = tuple(getattr(w03_result, "downstream_permission_packets", ()))
    priors = tuple(getattr(w03_result, "everyday_priors", ()))

    for candidate, packet in zip(candidates, packets, strict=False):
        prior = next((item for item in priors if item.schema_id == candidate.schema_id), None)
        intake_views.append(
            w04_intake(
                case_id=case_id,
                prior_id=getattr(prior, "prior_id", f"prior:{candidate.schema_id}"),
                schema_id=candidate.schema_id,
                candidate_id=candidate.schema_id,
                authority_scope=tuple(getattr(candidate, "source_authority_scope", ())),
                context_scope=tuple(getattr(candidate, "context_scope", ())),
                stale_or_revalidation_status=tuple(getattr(candidate, "stale_markers", ())),
                contradiction_status=tuple(getattr(candidate, "unresolved_contradictions", ())),
                may_use_as_bounded_prior=bool(getattr(packet, "may_use_as_bounded_prior", False)),
                may_use_as_schema_hint=bool(getattr(packet, "may_use_as_schema_hint", False)),
                may_use_as_operational_default=bool(getattr(packet, "may_use_as_operational_default", False)),
                must_revalidate_before_use=bool(getattr(packet, "must_revalidate_before_use", False)),
                must_preserve_contradiction=bool(getattr(packet, "must_preserve_contradiction", False)),
                must_abstain=bool(getattr(packet, "must_abstain", False)),
            )
        )

    desired = w04_desired_state(case_id=case_id)
    ctx = w04_context(case_id=case_id)
    perspective = w04_perspective()
    profile = w04_profile(
        case_id=case_id,
        world_constraints=(
            w04_constraint(
                constraint_id=f"{case_id}:world-hard",
                constraint_type=W04ConstraintType.WORLD_CONSTRAINT,
                hard_or_soft=W04ConstraintHardness.HARD,
                current_status="passed",
            ),
        ),
        epistemic_constraints=(
            w04_constraint(
                constraint_id=f"{case_id}:epistemic-soft",
                constraint_type=W04ConstraintType.EPISTEMIC_CONSTRAINT,
                hard_or_soft=W04ConstraintHardness.SOFT,
                current_status="passed",
                forbidden_condition=("soft_conflict",),
            ),
        ),
    )
    return w04_input_bundle(
        case_id=case_id,
        intake_views=tuple(intake_views),
        desired_state=desired,
        context=ctx,
        perspective=perspective,
        profile=profile,
    )


def clone_input(base: W04InputBundle, **changes) -> W04InputBundle:
    return replace(base, **changes)
