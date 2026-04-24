from __future__ import annotations

from substrate.o04_rupture_hostility_coercion import O04DynamicResult
from substrate.p01_project_formation import P01ProjectFormationResult
from substrate.r05_appraisal_sovereign_protective_regulation import (
    R05InhibitedSurface,
    R05ProtectiveResult,
)
from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01LicenseResult,
)
from substrate.v02_communicative_intent_utterance_plan_bridge.models import (
    V02OptionalityStatus,
    V02OrderingEdge,
    V02PlanGateDecision,
    V02PlanSegment,
    V02PlanStatus,
    V02ScopeMarker,
    V02SegmentRole,
    V02Telemetry,
    V02UncertaintyState,
    V02UtterancePlanInput,
    V02UtterancePlanResult,
    V02UtterancePlanState,
)


def build_v02_communicative_intent_utterance_plan_bridge(
    *,
    tick_id: str,
    tick_index: int,
    v01_result: V01LicenseResult,
    r05_result: R05ProtectiveResult | None,
    o04_result: O04DynamicResult | None,
    p01_result: P01ProjectFormationResult | None,
    plan_input: V02UtterancePlanInput | None,
    source_lineage: tuple[str, ...],
    prior_state: V02UtterancePlanState | None = None,
    planning_enabled: bool = True,
) -> V02UtterancePlanResult:
    if not planning_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )
    if not isinstance(v01_result, V01LicenseResult):
        raise TypeError("build_v02_communicative_intent_utterance_plan_bridge requires V01LicenseResult")

    if (
        v01_result.state.candidate_act_count <= 0
        and v01_result.state.licensed_act_count <= 0
        and plan_input is None
    ):
        return _build_no_basis_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    licensed_acts = tuple(v01_result.state.licensed_acts)
    denied_acts = tuple(v01_result.state.denied_acts)
    source_act_ids = tuple(dict.fromkeys(item.act_id for item in (*licensed_acts, *denied_acts)))
    mandatory_qualifiers = tuple(v01_result.state.mandatory_qualifiers)
    mandatory_qualifier_ids = tuple(dict.fromkeys(mandatory_qualifiers))
    blocked_expansion_ids = tuple(dict.fromkeys(f"expand:{item.act_id}" for item in denied_acts))
    protected_omission_ids = tuple(dict.fromkeys(f"omit:{item.act_id}" for item in denied_acts))

    prior_unresolved_question = bool(plan_input and plan_input.prior_unresolved_question)
    prior_refusal_present = bool(plan_input and plan_input.prior_refusal_present)
    prior_commitment_carry_present = bool(plan_input and plan_input.prior_commitment_carry_present)
    prior_repair_required = bool(plan_input and plan_input.prior_repair_required)
    p01_handoff_blocked = bool(
        isinstance(p01_result, P01ProjectFormationResult)
        and (
            p01_result.state.blocked_pending_grounding
            or p01_result.state.candidate_only_without_activation_basis
            or p01_result.state.no_safe_project_formation
            or not p01_result.gate.project_handoff_consumer_ready
        )
    )
    discourse_history_sensitive = bool(
        prior_unresolved_question
        or prior_refusal_present
        or prior_commitment_carry_present
        or prior_repair_required
        or p01_handoff_blocked
    )

    protective_boundary_first = _protective_boundary_first(r05_result, v01_result)
    clarification_first_required = bool(
        prior_unresolved_question
        or v01_result.state.clarification_before_commitment
        or p01_handoff_blocked
        or (
            isinstance(o04_result, O04DynamicResult)
            and o04_result.state.rupture_status.value in {"rupture_risk_only", "deescalated_but_not_closed"}
        )
    )
    refusal_dominant = bool(
        prior_refusal_present
        or (v01_result.state.licensed_act_count <= 0 and v01_result.state.denied_act_count > 0)
        or (
            v01_result.state.protective_defer_required
            and v01_result.state.denied_act_count > 0
            and v01_result.state.licensed_act_count <= 1
        )
    )

    segments: list[V02PlanSegment] = []
    edges: list[V02OrderingEdge] = []
    segment_ids: list[str] = []

    def _add_segment(
        *,
        segment_role: V02SegmentRole,
        source_act_ref: str,
        content_refs: tuple[str, ...],
        target_update: str,
        mandatory_ids: tuple[str, ...] = (),
        blocked_ids: tuple[str, ...] = (),
        protected_ids: tuple[str, ...] = (),
        uncertainty_state: V02UncertaintyState = V02UncertaintyState.BOUNDED,
        optionality_status: V02OptionalityStatus = V02OptionalityStatus.REQUIRED,
    ) -> str:
        segment_id = f"seg:{len(segments) + 1}:{segment_role.value}"
        segment_ids.append(segment_id)
        segments.append(
            V02PlanSegment(
                segment_id=segment_id,
                source_act_ref=source_act_ref,
                segment_role=segment_role,
                content_refs=content_refs,
                target_update=target_update,
                mandatory_qualifier_ids=mandatory_ids,
                blocked_expansion_ids=blocked_ids,
                protected_omission_ids=protected_ids,
                prerequisite_segment_ids=(),
                must_precede_segment_ids=(),
                mutually_exclusive_segment_ids=(),
                uncertainty_state=uncertainty_state,
                optionality_status=optionality_status,
            )
        )
        return segment_id

    qualifier_segment_id: str | None = None
    if mandatory_qualifiers:
        qualifier_segment_id = _add_segment(
            segment_role=V02SegmentRole.QUALIFICATION,
            source_act_ref="v01:mandatory_qualifiers",
            content_refs=mandatory_qualifiers,
            target_update="bind_mandatory_qualifiers",
            mandatory_ids=mandatory_qualifiers,
            uncertainty_state=V02UncertaintyState.QUALIFIED,
        )

    boundary_segment_id: str | None = None
    if protective_boundary_first:
        boundary_segment_id = _add_segment(
            segment_role=V02SegmentRole.BOUNDARY,
            source_act_ref="r05:protective_boundary",
            content_refs=(),
            target_update="set_protective_boundary",
            blocked_ids=blocked_expansion_ids,
            protected_ids=protected_omission_ids,
            uncertainty_state=V02UncertaintyState.QUALIFIED,
        )

    clarification_segment_id: str | None = None
    if clarification_first_required:
        clarification_segment_id = _add_segment(
            segment_role=V02SegmentRole.CLARIFICATION_REQUEST,
            source_act_ref="v01:clarification_gate",
            content_refs=(),
            target_update="request_clarification_before_commitment",
            protected_ids=protected_omission_ids,
            uncertainty_state=V02UncertaintyState.UNRESOLVED,
        )

    answer_segment_ids: list[str] = []
    refusal_segment_ids: list[str] = []
    commitment_limiter_segment_id: str | None = None
    next_step_segment_id: str | None = None

    for item in licensed_acts:
        role = _map_act_role(item.act_type)
        uncertainty = (
            V02UncertaintyState.QUALIFIED
            if item.conditional_license or mandatory_qualifiers
            else V02UncertaintyState.BOUNDED
        )
        optionality = (
            V02OptionalityStatus.CONDITIONAL
            if item.conditional_license
            else V02OptionalityStatus.REQUIRED
        )
        segment_id = _add_segment(
            segment_role=role,
            source_act_ref=item.act_id,
            content_refs=(item.act_id,),
            target_update=f"deliver_{role.value}",
            mandatory_ids=item.mandatory_qualifiers,
            blocked_ids=blocked_expansion_ids,
            protected_ids=protected_omission_ids,
            uncertainty_state=uncertainty,
            optionality_status=optionality,
        )
        if role is V02SegmentRole.ANSWER or role is V02SegmentRole.WARNING:
            answer_segment_ids.append(segment_id)
        if role is V02SegmentRole.REFUSAL:
            refusal_segment_ids.append(segment_id)
        if role is V02SegmentRole.NEXT_STEP_HANDOFF:
            next_step_segment_id = segment_id

    if prior_commitment_carry_present and not commitment_limiter_segment_id:
        commitment_limiter_segment_id = _add_segment(
            segment_role=V02SegmentRole.COMMITMENT_LIMITER,
            source_act_ref="history:prior_commitment_carry",
            content_refs=("carry_commitment_limits",),
            target_update="bound_commitment_carry",
            mandatory_ids=("bounded_commitment_scope",),
            uncertainty_state=V02UncertaintyState.QUALIFIED,
            optionality_status=V02OptionalityStatus.CONDITIONAL,
        )
    elif v01_result.state.commitment_delta_count > 0 and not v01_result.state.promise_like_act_denied:
        commitment_limiter_segment_id = _add_segment(
            segment_role=V02SegmentRole.COMMITMENT_LIMITER,
            source_act_ref="v01:commitment_delta",
            content_refs=("commitment_delta",),
            target_update="bind_commitment_delta",
            mandatory_ids=tuple(
                qualifier for qualifier in mandatory_qualifiers if qualifier == "bounded_commitment_scope"
            ),
            uncertainty_state=V02UncertaintyState.QUALIFIED,
            optionality_status=V02OptionalityStatus.CONDITIONAL,
        )

    if refusal_dominant and not refusal_segment_ids:
        refusal_segment_ids.append(
            _add_segment(
                segment_role=V02SegmentRole.REFUSAL,
                source_act_ref="v01:denied_surface",
                content_refs=tuple(item.act_id for item in denied_acts),
                target_update="deliver_refusal_with_narrowed_alternative",
                blocked_ids=blocked_expansion_ids,
                protected_ids=protected_omission_ids,
                uncertainty_state=V02UncertaintyState.QUALIFIED,
            )
        )

    if v01_result.state.alternative_narrowed_act_available and next_step_segment_id is None:
        next_step_segment_id = _add_segment(
            segment_role=V02SegmentRole.NEXT_STEP_HANDOFF,
            source_act_ref="v01:narrowed_alternative",
            content_refs=tuple(item.act_id for item in denied_acts),
            target_update="handoff_narrowed_alternative",
            blocked_ids=blocked_expansion_ids,
            protected_ids=protected_omission_ids,
            uncertainty_state=V02UncertaintyState.QUALIFIED,
            optionality_status=V02OptionalityStatus.CONDITIONAL,
        )

    if qualifier_segment_id:
        for target in answer_segment_ids:
            edges.append(
                V02OrderingEdge(
                    from_segment_id=qualifier_segment_id,
                    to_segment_id=target,
                    relation="must_precede",
                    reason_code="mandatory_qualifier_binding",
                )
            )
    if clarification_segment_id:
        for target in answer_segment_ids:
            edges.append(
                V02OrderingEdge(
                    from_segment_id=clarification_segment_id,
                    to_segment_id=target,
                    relation="prerequisite",
                    reason_code="clarification_first_required",
                )
            )
    if boundary_segment_id:
        for target in [*answer_segment_ids, *refusal_segment_ids]:
            edges.append(
                V02OrderingEdge(
                    from_segment_id=boundary_segment_id,
                    to_segment_id=target,
                    relation="must_precede",
                    reason_code="protective_boundary_first",
                )
            )
    if commitment_limiter_segment_id and next_step_segment_id:
        edges.append(
            V02OrderingEdge(
                from_segment_id=commitment_limiter_segment_id,
                to_segment_id=next_step_segment_id,
                relation="prerequisite",
                reason_code="commitment_limiter_before_handoff",
            )
        )
    if refusal_segment_ids and answer_segment_ids:
        for refusal_id in refusal_segment_ids:
            for answer_id in answer_segment_ids:
                edges.append(
                    V02OrderingEdge(
                        from_segment_id=refusal_id,
                        to_segment_id=answer_id,
                        relation="mutually_exclusive",
                        reason_code="refusal_vs_answer_branch_split",
                    )
                )

    alternative_branch_ids: list[str] = []
    primary_branch_id = "branch:main"
    unresolved_branching = False
    if clarification_first_required and answer_segment_ids:
        alternative_branch_ids.append("branch:clarification_first")
    if refusal_dominant and answer_segment_ids:
        alternative_branch_ids.append("branch:refusal_dominant")
    if protective_boundary_first and answer_segment_ids:
        alternative_branch_ids.append("branch:protective_boundary_first")
    if len(alternative_branch_ids) > 1:
        unresolved_branching = True
        primary_branch_id = "branch:bounded_primary"

    segment_count = len(segments)
    ordering_edge_count = len(edges)
    branch_count = 1 + len(alternative_branch_ids)
    mandatory_qualifier_attachment_count = sum(
        len(segment.mandatory_qualifier_ids) for segment in segments
    )
    blocked_expansion_count = len(blocked_expansion_ids)
    protected_omission_count = len(protected_omission_ids)

    partial_plan_only = bool(
        unresolved_branching
        or (segment_count > 1 and ordering_edge_count == 0)
        or (prior_repair_required and not clarification_first_required)
    )
    if prior_state is not None and prior_state.partial_plan_only and prior_repair_required:
        partial_plan_only = True

    if discourse_history_sensitive and segment_count > 1 and ordering_edge_count == 0:
        plan_status = V02PlanStatus.CANNOT_ORDER_WITH_CURRENT_HISTORY
    elif unresolved_branching:
        plan_status = V02PlanStatus.MULTIPLE_BRANCHES_UNRESOLVED
    elif refusal_dominant:
        plan_status = V02PlanStatus.REFUSAL_DOMINANT_PLAN
    elif protective_boundary_first:
        plan_status = V02PlanStatus.PROTECTIVE_DEFER_PLAN
    elif clarification_first_required:
        plan_status = V02PlanStatus.CLARIFICATION_FIRST_PLAN
    elif partial_plan_only:
        plan_status = V02PlanStatus.PARTIAL_PLAN_ONLY
    elif segment_count > 0:
        plan_status = V02PlanStatus.FULL_PLAN_READY
    else:
        plan_status = V02PlanStatus.INSUFFICIENT_PLAN_BASIS

    realization_contract_ready = bool(
        segment_count > 0
        and not unresolved_branching
        and (ordering_edge_count > 0 or segment_count <= 1)
        and plan_status
        not in {
            V02PlanStatus.CANNOT_ORDER_WITH_CURRENT_HISTORY,
            V02PlanStatus.INSUFFICIENT_PLAN_BASIS,
        }
    )
    downstream_consumer_ready = bool(segment_count > 0 and (ordering_edge_count > 0 or segment_count <= 1))

    state = V02UtterancePlanState(
        plan_id=f"v02-plan:{tick_id}",
        plan_status=plan_status,
        primary_branch_id=primary_branch_id,
        alternative_branch_ids=tuple(alternative_branch_ids),
        segment_graph=tuple(segments),
        ordering_edges=tuple(edges),
        segment_ids=tuple(segment_ids),
        source_act_ids=source_act_ids,
        mandatory_qualifier_ids=mandatory_qualifier_ids,
        blocked_expansion_ids=blocked_expansion_ids,
        protected_omission_ids=protected_omission_ids,
        unresolved_branching=unresolved_branching,
        clarification_first_required=clarification_first_required,
        refusal_dominant=refusal_dominant,
        protective_boundary_first=protective_boundary_first,
        partial_plan_only=partial_plan_only,
        realization_contract_ready=realization_contract_ready,
        discourse_history_sensitive=discourse_history_sensitive,
        downstream_consumer_ready=downstream_consumer_ready,
        segment_count=segment_count,
        branch_count=branch_count,
        ordering_edge_count=ordering_edge_count,
        mandatory_qualifier_attachment_count=mandatory_qualifier_attachment_count,
        blocked_expansion_count=blocked_expansion_count,
        protected_omission_count=protected_omission_count,
        justification_links=tuple(
            dict.fromkeys(
                (
                    f"plan_status:{plan_status.value}",
                    f"segment_count:{segment_count}",
                    f"ordering_edge_count:{ordering_edge_count}",
                    f"blocked_expansion_count:{blocked_expansion_count}",
                    f"protected_omission_count:{protected_omission_count}",
                    f"protective_boundary_first:{protective_boundary_first}",
                    f"clarification_first_required:{clarification_first_required}",
                    f"refusal_dominant:{refusal_dominant}",
                    f"p01_handoff_blocked:{p01_handoff_blocked}",
                )
            )
        ),
        provenance="v02.communicative_intent_utterance_plan_bridge.policy",
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *v01_result.state.source_lineage,
                    *(r05_result.state.source_lineage if isinstance(r05_result, R05ProtectiveResult) else ()),
                    *(p01_result.state.source_lineage if isinstance(p01_result, P01ProjectFormationResult) else ()),
                )
            )
        ),
        last_update_provenance="v02.communicative_intent_utterance_plan_bridge.policy",
    )
    gate = _build_gate(state)
    scope_marker = V02ScopeMarker(
        scope="rt01_hosted_v02_first_slice",
        rt01_hosted_only=True,
        v02_first_slice_only=True,
        v03_not_implemented=True,
        p02_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="first bounded v02 slice; realization and episode layers remain open seams",
    )
    telemetry = V02Telemetry(
        plan_id=state.plan_id,
        tick_index=tick_index,
        plan_status=state.plan_status,
        segment_count=state.segment_count,
        branch_count=state.branch_count,
        ordering_edge_count=state.ordering_edge_count,
        mandatory_qualifier_attachment_count=state.mandatory_qualifier_attachment_count,
        blocked_expansion_count=state.blocked_expansion_count,
        protected_omission_count=state.protected_omission_count,
        clarification_first_required=state.clarification_first_required,
        refusal_dominant=state.refusal_dominant,
        protective_boundary_first=state.protective_boundary_first,
        partial_plan_only=state.partial_plan_only,
        unresolved_branching=state.unresolved_branching,
        downstream_consumer_ready=state.downstream_consumer_ready,
    )
    return V02UtterancePlanResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=(
            "v02 built typed utterance-plan bridge with segment ordering, qualifier binding, "
            "protected omission and branch-state surfaces"
        ),
    )


def _build_gate(state: V02UtterancePlanState) -> V02PlanGateDecision:
    plan_consumer_ready = bool(state.segment_count > 0)
    ordering_consumer_ready = bool(state.segment_count <= 1 or state.ordering_edge_count > 0)
    realization_contract_consumer_ready = bool(state.realization_contract_ready)
    restrictions: list[str] = []
    if state.partial_plan_only:
        restrictions.append("partial_plan_only")
    if state.clarification_first_required:
        restrictions.append("clarification_first_required")
    if state.protective_boundary_first:
        restrictions.append("protective_boundary_first")
    if state.unresolved_branching:
        restrictions.append("unresolved_branching")
    if state.blocked_expansion_count > 0:
        restrictions.append("blocked_expansion_present")
    if state.protected_omission_count > 0:
        restrictions.append("protected_omission_present")
    if not ordering_consumer_ready:
        restrictions.append("cannot_order_with_current_history")
    if not realization_contract_consumer_ready:
        restrictions.append("realization_contract_not_ready")
    return V02PlanGateDecision(
        plan_consumer_ready=plan_consumer_ready,
        ordering_consumer_ready=ordering_consumer_ready,
        realization_contract_consumer_ready=realization_contract_consumer_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="v02 gate exposes plan, ordering and realization-contract readiness",
    )


def _map_act_role(act_type: V01ActType) -> V02SegmentRole:
    if act_type in {V01ActType.ASSERTION, V01ActType.ADVICE, V01ActType.EXPLANATION}:
        return V02SegmentRole.ANSWER
    if act_type is V01ActType.WARNING:
        return V02SegmentRole.WARNING
    if act_type is V01ActType.QUESTION:
        return V02SegmentRole.CLARIFICATION_REQUEST
    if act_type is V01ActType.REQUEST:
        return V02SegmentRole.NEXT_STEP_HANDOFF
    if act_type is V01ActType.REFUSAL:
        return V02SegmentRole.REFUSAL
    if act_type is V01ActType.BOUNDARY_STATEMENT:
        return V02SegmentRole.BOUNDARY
    if act_type is V01ActType.PROMISE:
        return V02SegmentRole.NEXT_STEP_HANDOFF
    return V02SegmentRole.ANSWER


def _protective_boundary_first(
    r05_result: R05ProtectiveResult | None,
    v01_result: V01LicenseResult,
) -> bool:
    if not isinstance(r05_result, R05ProtectiveResult):
        return bool(v01_result.state.protective_defer_required)
    inhibited = {surface for surface in r05_result.state.inhibited_surfaces}
    return bool(
        v01_result.state.protective_defer_required
        or r05_result.state.project_override_active
        or r05_result.state.protective_mode.value in {"active_protective_mode", "degraded_operation_only"}
        or R05InhibitedSurface.COMMUNICATION_EXPOSURE in inhibited
        or R05InhibitedSurface.INTERACTION_INTENSITY in inhibited
    )


def _build_no_basis_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> V02UtterancePlanResult:
    state = V02UtterancePlanState(
        plan_id=f"v02-plan:{tick_id}",
        plan_status=V02PlanStatus.INSUFFICIENT_PLAN_BASIS,
        primary_branch_id="branch:none",
        alternative_branch_ids=(),
        segment_graph=(),
        ordering_edges=(),
        segment_ids=(),
        source_act_ids=(),
        mandatory_qualifier_ids=(),
        blocked_expansion_ids=(),
        protected_omission_ids=(),
        unresolved_branching=False,
        clarification_first_required=False,
        refusal_dominant=False,
        protective_boundary_first=False,
        partial_plan_only=True,
        realization_contract_ready=False,
        discourse_history_sensitive=False,
        downstream_consumer_ready=False,
        segment_count=0,
        branch_count=0,
        ordering_edge_count=0,
        mandatory_qualifier_attachment_count=0,
        blocked_expansion_count=0,
        protected_omission_count=0,
        justification_links=("insufficient_plan_basis",),
        provenance="v02.communicative_intent_utterance_plan_bridge.no_basis",
        source_lineage=source_lineage,
        last_update_provenance="v02.communicative_intent_utterance_plan_bridge.no_basis",
    )
    gate = V02PlanGateDecision(
        plan_consumer_ready=False,
        ordering_consumer_ready=False,
        realization_contract_consumer_ready=False,
        restrictions=("insufficient_plan_basis", "no_v02_plan_basis"),
        reason="v02 no-basis fallback keeps utterance planning gate non-activating",
    )
    scope_marker = V02ScopeMarker(
        scope="rt01_hosted_v02_first_slice",
        rt01_hosted_only=True,
        v02_first_slice_only=True,
        v03_not_implemented=True,
        p02_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="v02 no-basis fallback",
    )
    telemetry = V02Telemetry(
        plan_id=state.plan_id,
        tick_index=tick_index,
        plan_status=state.plan_status,
        segment_count=0,
        branch_count=0,
        ordering_edge_count=0,
        mandatory_qualifier_attachment_count=0,
        blocked_expansion_count=0,
        protected_omission_count=0,
        clarification_first_required=False,
        refusal_dominant=False,
        protective_boundary_first=False,
        partial_plan_only=True,
        unresolved_branching=False,
        downstream_consumer_ready=False,
    )
    return V02UtterancePlanResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> V02UtterancePlanResult:
    state = V02UtterancePlanState(
        plan_id=f"v02-plan:{tick_id}",
        plan_status=V02PlanStatus.INSUFFICIENT_PLAN_BASIS,
        primary_branch_id="branch:none",
        alternative_branch_ids=(),
        segment_graph=(),
        ordering_edges=(),
        segment_ids=(),
        source_act_ids=(),
        mandatory_qualifier_ids=(),
        blocked_expansion_ids=(),
        protected_omission_ids=(),
        unresolved_branching=False,
        clarification_first_required=False,
        refusal_dominant=False,
        protective_boundary_first=False,
        partial_plan_only=True,
        realization_contract_ready=False,
        discourse_history_sensitive=False,
        downstream_consumer_ready=False,
        segment_count=0,
        branch_count=0,
        ordering_edge_count=0,
        mandatory_qualifier_attachment_count=0,
        blocked_expansion_count=0,
        protected_omission_count=0,
        justification_links=("v02_disabled",),
        provenance="v02.communicative_intent_utterance_plan_bridge.disabled",
        source_lineage=source_lineage,
        last_update_provenance="v02.communicative_intent_utterance_plan_bridge.disabled",
    )
    gate = V02PlanGateDecision(
        plan_consumer_ready=False,
        ordering_consumer_ready=False,
        realization_contract_consumer_ready=False,
        restrictions=("v02_disabled", "insufficient_plan_basis"),
        reason="v02 plan bridge disabled in ablation context",
    )
    scope_marker = V02ScopeMarker(
        scope="rt01_hosted_v02_first_slice",
        rt01_hosted_only=True,
        v02_first_slice_only=True,
        v03_not_implemented=True,
        p02_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="v02 disabled path",
    )
    telemetry = V02Telemetry(
        plan_id=state.plan_id,
        tick_index=tick_index,
        plan_status=state.plan_status,
        segment_count=0,
        branch_count=0,
        ordering_edge_count=0,
        mandatory_qualifier_attachment_count=0,
        blocked_expansion_count=0,
        protected_omission_count=0,
        clarification_first_required=False,
        refusal_dominant=False,
        protective_boundary_first=False,
        partial_plan_only=True,
        unresolved_branching=False,
        downstream_consumer_ready=False,
    )
    return V02UtterancePlanResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )
