from __future__ import annotations

from substrate.v01_normative_permission_commitment_licensing import V01LicenseResult
from substrate.v02_communicative_intent_utterance_plan_bridge import (
    V02SegmentRole,
    V02UtterancePlanResult,
)
from substrate.v03_surface_verbalization_causality_constrained_realization.models import (
    V03ConstrainedRealizationResult,
    V03ConstraintSatisfactionReport,
    V03RealizationAlignmentMap,
    V03RealizationFailureState,
    V03RealizationGateDecision,
    V03RealizationInput,
    V03RealizationStatus,
    V03RealizedUtteranceArtifact,
    V03ScopeMarker,
    V03SurfaceSpanAlignment,
    V03Telemetry,
)


def build_v03_surface_verbalization_causality_constrained_realization(
    *,
    tick_id: str,
    tick_index: int,
    v02_result: V02UtterancePlanResult,
    v01_result: V01LicenseResult,
    realization_input: V03RealizationInput | None,
    source_lineage: tuple[str, ...],
    realization_enabled: bool = True,
) -> V03ConstrainedRealizationResult:
    if not realization_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )
    if not isinstance(v02_result, V02UtterancePlanResult):
        raise TypeError("build_v03_surface_verbalization_causality_constrained_realization requires V02UtterancePlanResult")
    if not isinstance(v01_result, V01LicenseResult):
        raise TypeError("build_v03_surface_verbalization_causality_constrained_realization requires V01LicenseResult")

    if v02_result.state.segment_count <= 0:
        return _build_no_basis_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    realization_input = realization_input or V03RealizationInput(input_id=f"{tick_id}:v03:default")
    selected_branch_id = realization_input.selected_branch_id or v02_result.state.primary_branch_id
    all_segments = tuple(v02_result.state.segment_graph)
    branch_segments = _select_branch_segments(
        all_segments=all_segments,
        v02_result=v02_result,
    )
    ordered_segments = _apply_optional_forced_reordering(
        segments=branch_segments,
        force_boundary_after_explanation=realization_input.force_boundary_after_explanation,
    )
    segment_text_map = _build_segment_text_map(
        segments=ordered_segments,
        surface_variant=realization_input.surface_variant,
        tamper_segment_id=realization_input.tamper_qualifier_locality_segment_id,
    )
    if realization_input.force_commitment_phrase and ordered_segments:
        tail_id = ordered_segments[-1].segment_id
        segment_text_map[tail_id] = segment_text_map[tail_id] + " I will guarantee this."
    if (
        realization_input.inject_blocked_expansion_token
        and realization_input.inject_blocked_expansion_token in v02_result.state.blocked_expansion_ids
        and ordered_segments
    ):
        head_id = ordered_segments[0].segment_id
        segment_text_map[head_id] = (
            segment_text_map[head_id]
            + f" leaked_blocked_expansion:{realization_input.inject_blocked_expansion_token}"
        )
    if (
        realization_input.inject_protected_omission_token
        and realization_input.inject_protected_omission_token in v02_result.state.protected_omission_ids
        and ordered_segments
    ):
        head_id = ordered_segments[0].segment_id
        segment_text_map[head_id] = (
            segment_text_map[head_id]
            + f" leaked_protected_omission:{realization_input.inject_protected_omission_token}"
        )

    artifact = _build_artifact(
        tick_id=tick_id,
        segments=ordered_segments,
        segment_text_map=segment_text_map,
        selected_branch_id=selected_branch_id,
        blocked_expansion_ids=v02_result.state.blocked_expansion_ids,
        protected_omission_ids=v02_result.state.protected_omission_ids,
    )
    alignment_map = _build_alignment_map(
        segments=ordered_segments,
        artifact=artifact,
        segment_text_map=segment_text_map,
        ordering_edges=v02_result.state.ordering_edges,
    )
    report = _build_constraint_report(
        v02_result=v02_result,
        v01_result=v01_result,
        artifact=artifact,
        alignment_map=alignment_map,
    )

    hard_constraint_violation = report.hard_constraint_violation_count > 0
    if hard_constraint_violation:
        narrowed_segments = tuple(
            item
            for item in ordered_segments
            if item.segment_role
            in {
                V02SegmentRole.QUALIFICATION,
                V02SegmentRole.BOUNDARY,
                V02SegmentRole.CLARIFICATION_REQUEST,
                V02SegmentRole.REFUSAL,
            }
        )
        if narrowed_segments:
            narrowed_text_map = _build_segment_text_map(
                segments=narrowed_segments,
                surface_variant=realization_input.surface_variant,
                tamper_segment_id=None,
            )
            artifact = _build_artifact(
                tick_id=tick_id,
                segments=narrowed_segments,
                segment_text_map=narrowed_text_map,
                selected_branch_id=selected_branch_id,
                blocked_expansion_ids=v02_result.state.blocked_expansion_ids,
                protected_omission_ids=v02_result.state.protected_omission_ids,
                partial_realization_only=True,
            )
            alignment_map = _build_alignment_map(
                segments=narrowed_segments,
                artifact=artifact,
                segment_text_map=narrowed_text_map,
                ordering_edges=v02_result.state.ordering_edges,
            )
            realization_status = _derive_narrowed_status(narrowed_segments)
            failure_state = V03RealizationFailureState(
                failed=True,
                failure_code="hard_constraint_violation",
                partial_realization_only=True,
                replan_required=True,
                reason="v03 narrowed realization to preserve hard constraints",
            )
        else:
            artifact = V03RealizedUtteranceArtifact(
                realization_id=f"v03-realization:{tick_id}",
                surface_text="I need clarification before I can provide a safe response.",
                segment_order=(),
                realized_segment_ids=(),
                omitted_segment_ids=tuple(item.segment_id for item in ordered_segments),
                source_act_ids=(),
                selected_branch_id=selected_branch_id,
                blocked_expansion_ids=v02_result.state.blocked_expansion_ids,
                protected_omission_ids=v02_result.state.protected_omission_ids,
                partial_realization_only=True,
                provenance="v03.surface_realization.failure_fallback",
            )
            alignment_map = V03RealizationAlignmentMap(
                alignments=(),
                aligned_segment_count=0,
                unaligned_segment_ids=tuple(item.segment_id for item in ordered_segments),
                branch_compliance_pass=False,
                ordering_pass=False,
                qualifier_locality_pass=False,
            )
            realization_status = V03RealizationStatus.REALIZATION_FAILED
            failure_state = V03RealizationFailureState(
                failed=True,
                failure_code="realization_not_constructible_under_hard_constraints",
                partial_realization_only=True,
                replan_required=True,
                reason="v03 could not retain any lawful surface segments without violating hard constraints",
            )
    else:
        realization_status = (
            V03RealizationStatus.CLARIFICATION_ONLY_REALIZATION
            if artifact.realized_segment_ids
            and all(
                item.segment_role in {V02SegmentRole.QUALIFICATION, V02SegmentRole.CLARIFICATION_REQUEST}
                for item in ordered_segments
            )
            else V03RealizationStatus.REALIZED_CONSTRAINED
        )
        failure_state = V03RealizationFailureState(
            failed=False,
            failure_code=None,
            partial_realization_only=False,
            replan_required=False,
            reason="v03 constrained realization satisfied hard plan constraints",
        )

    gate = _build_gate(
        report=report,
        failure_state=failure_state,
        surface_text=artifact.surface_text,
    )
    scope_marker = V03ScopeMarker(
        scope="rt01_hosted_v03_first_slice",
        rt01_hosted_only=True,
        v03_first_slice_only=True,
        v_line_not_map_wide_ready=True,
        p02_not_implemented=True,
        map_wide_realization_enforcement=False,
        reason="first bounded v03 slice; map-wide verbalization enforcement is intentionally open",
    )
    telemetry = V03Telemetry(
        realization_id=artifact.realization_id,
        tick_index=tick_index,
        realization_status=realization_status,
        segment_count=len(artifact.realized_segment_ids),
        aligned_segment_count=alignment_map.aligned_segment_count,
        hard_constraint_violation_count=report.hard_constraint_violation_count,
        qualifier_locality_failures=report.qualifier_locality_failures,
        blocked_expansion_leak_detected=report.blocked_expansion_leak_detected,
        protected_omission_count=len(artifact.protected_omission_ids),
        boundary_before_explanation_required=report.boundary_before_explanation_required,
        boundary_before_explanation_satisfied=report.boundary_before_explanation_satisfied,
        partial_realization_only=failure_state.partial_realization_only,
        replan_required=failure_state.replan_required,
        downstream_consumer_ready=(
            gate.realization_consumer_ready
            and gate.alignment_consumer_ready
            and gate.constraint_report_consumer_ready
        ),
    )
    return V03ConstrainedRealizationResult(
        realization_status=realization_status,
        artifact=artifact,
        alignment_map=alignment_map,
        constraint_report=report,
        failure_state=failure_state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=(
            "v03 built constrained surface realization as causal continuation of v02 plan "
            "with alignment and hard-constraint reports"
        ),
    )


def _build_segment_text_map(
    *,
    segments,
    surface_variant: str,
    tamper_segment_id: str | None,
) -> dict[str, str]:
    text_map: dict[str, str] = {}
    for segment in segments:
        qualifier_ids = segment.mandatory_qualifier_ids
        if tamper_segment_id == segment.segment_id:
            qualifier_ids = ()
        qualifier_payload = (
            f" qualifier_ids:[{','.join(qualifier_ids)}]"
            if qualifier_ids
            else ""
        )
        text = _segment_text(segment.segment_role, segment.source_act_ref, surface_variant)
        text_map[segment.segment_id] = text + qualifier_payload
    return text_map


def _segment_text(role: V02SegmentRole, source_act_ref: str, surface_variant: str) -> str:
    if role is V02SegmentRole.QUALIFICATION:
        return (
            "Qualification: bounded uncertainty is explicit."
            if surface_variant == "default"
            else "Qualifier: uncertainty remains explicit and bounded."
        )
    if role is V02SegmentRole.BOUNDARY:
        return (
            "Boundary: I will keep this response constrained."
            if surface_variant == "default"
            else "Boundary: scope remains constrained before expansion."
        )
    if role is V02SegmentRole.CLARIFICATION_REQUEST:
        return (
            "Clarification needed before full continuation."
            if surface_variant == "default"
            else "Before continuing, I need one clarification."
        )
    if role is V02SegmentRole.REFUSAL:
        return (
            "Refusal: I cannot provide that direct expansion."
            if surface_variant == "default"
            else "I cannot provide that expansion directly."
        )
    if role is V02SegmentRole.WARNING:
        return (
            f"Warning for {source_act_ref}: uncertainty remains."
            if surface_variant == "default"
            else f"Warning ({source_act_ref}): residual uncertainty remains."
        )
    if role is V02SegmentRole.COMMITMENT_LIMITER:
        return (
            "Commitment limiter: commitments remain bounded in scope."
            if surface_variant == "default"
            else "Any commitment stays explicitly bounded."
        )
    if role is V02SegmentRole.NEXT_STEP_HANDOFF:
        return (
            f"Narrowed next step from {source_act_ref} is available."
            if surface_variant == "default"
            else f"A narrowed next step ({source_act_ref}) is available."
        )
    return (
        f"Answer segment from {source_act_ref} with bounded scope."
        if surface_variant == "default"
        else f"Bounded answer segment ({source_act_ref}) with explicit scope limits."
    )


def _select_branch_segments(
    *,
    all_segments,
    v02_result: V02UtterancePlanResult,
):
    has_mutual_exclusion = any(
        edge.relation == "mutually_exclusive" for edge in v02_result.state.ordering_edges
    )
    if not has_mutual_exclusion:
        return tuple(all_segments)
    if v02_result.state.refusal_dominant:
        return tuple(
            item
            for item in all_segments
            if item.segment_role not in {V02SegmentRole.ANSWER, V02SegmentRole.WARNING}
        )
    return tuple(item for item in all_segments if item.segment_role is not V02SegmentRole.REFUSAL)


def _apply_optional_forced_reordering(*, segments, force_boundary_after_explanation: bool):
    if not force_boundary_after_explanation:
        return tuple(segments)
    boundary = [item for item in segments if item.segment_role is V02SegmentRole.BOUNDARY]
    non_boundary = [item for item in segments if item.segment_role is not V02SegmentRole.BOUNDARY]
    return tuple((*non_boundary, *boundary))


def _build_artifact(
    *,
    tick_id: str,
    segments,
    segment_text_map: dict[str, str],
    selected_branch_id: str,
    blocked_expansion_ids: tuple[str, ...],
    protected_omission_ids: tuple[str, ...],
    partial_realization_only: bool = False,
) -> V03RealizedUtteranceArtifact:
    realized_segment_ids = tuple(item.segment_id for item in segments)
    surface_text = " ".join(segment_text_map[item.segment_id] for item in segments)
    return V03RealizedUtteranceArtifact(
        realization_id=f"v03-realization:{tick_id}",
        surface_text=surface_text,
        segment_order=realized_segment_ids,
        realized_segment_ids=realized_segment_ids,
        omitted_segment_ids=(),
        source_act_ids=tuple(dict.fromkeys(item.source_act_ref for item in segments)),
        selected_branch_id=selected_branch_id,
        blocked_expansion_ids=blocked_expansion_ids,
        protected_omission_ids=protected_omission_ids,
        partial_realization_only=partial_realization_only,
        provenance="v03.surface_realization.policy",
    )


def _build_alignment_map(
    *,
    segments,
    artifact: V03RealizedUtteranceArtifact,
    segment_text_map: dict[str, str],
    ordering_edges,
) -> V03RealizationAlignmentMap:
    positions = {segment_id: idx for idx, segment_id in enumerate(artifact.segment_order)}
    ordering_pass_map: dict[str, bool] = {
        segment.segment_id: True for segment in segments
    }
    branch_compliance_pass = True
    for edge in ordering_edges:
        source = edge.from_segment_id
        target = edge.to_segment_id
        if source not in positions or target not in positions:
            continue
        if edge.relation in {"must_precede", "prerequisite"} and positions[source] >= positions[target]:
            ordering_pass_map[source] = False
            ordering_pass_map[target] = False
        if edge.relation == "mutually_exclusive":
            branch_compliance_pass = False
            ordering_pass_map[source] = False
            ordering_pass_map[target] = False

    alignments: list[V03SurfaceSpanAlignment] = []
    cursor = 0
    for segment in segments:
        text = segment_text_map[segment.segment_id]
        start = cursor
        end = start + len(text)
        cursor = end + 1
        qualifier_locality_pass = _segment_qualifier_locality_pass(
            mandatory_qualifier_ids=segment.mandatory_qualifier_ids,
            realized_text=text,
        )
        alignments.append(
            V03SurfaceSpanAlignment(
                segment_id=segment.segment_id,
                start_index=start,
                end_index=end,
                realized_text=text,
                source_act_ref=segment.source_act_ref,
                realized=True,
                qualifier_locality_pass=qualifier_locality_pass,
                ordering_pass=ordering_pass_map.get(segment.segment_id, True),
            )
        )
    return V03RealizationAlignmentMap(
        alignments=tuple(alignments),
        aligned_segment_count=len(alignments),
        unaligned_segment_ids=(),
        branch_compliance_pass=branch_compliance_pass,
        ordering_pass=all(item.ordering_pass for item in alignments),
        qualifier_locality_pass=all(item.qualifier_locality_pass for item in alignments),
    )


def _build_constraint_report(
    *,
    v02_result: V02UtterancePlanResult,
    v01_result: V01LicenseResult,
    artifact: V03RealizedUtteranceArtifact,
    alignment_map: V03RealizationAlignmentMap,
) -> V03ConstraintSatisfactionReport:
    violation_codes: list[str] = []
    satisfied_codes: list[str] = []
    positions = {segment_id: idx for idx, segment_id in enumerate(artifact.segment_order)}

    ordering_pass = True
    branch_compliance_pass = True
    for edge in v02_result.state.ordering_edges:
        source = edge.from_segment_id
        target = edge.to_segment_id
        if source not in positions or target not in positions:
            continue
        if edge.relation in {"must_precede", "prerequisite"} and positions[source] >= positions[target]:
            ordering_pass = False
            violation_codes.append(f"ordering_violation:{edge.reason_code}")
        if edge.relation == "mutually_exclusive":
            branch_compliance_pass = False
            violation_codes.append(f"branch_violation:{edge.reason_code}")
    if ordering_pass:
        satisfied_codes.append("ordering_pass")
    if branch_compliance_pass:
        satisfied_codes.append("branch_compliance_pass")

    boundary_required = v02_result.state.protective_boundary_first
    boundary_edges = tuple(
        edge
        for edge in v02_result.state.ordering_edges
        if edge.reason_code == "protective_boundary_first"
    )
    if boundary_edges:
        boundary_satisfied = True
        for edge in boundary_edges:
            source = edge.from_segment_id
            target = edge.to_segment_id
            if source not in positions or target not in positions:
                continue
            if positions[source] >= positions[target]:
                boundary_satisfied = False
                break
    else:
        boundary_satisfied = _boundary_before_explanation_satisfied(artifact, positions)
    if boundary_required and not boundary_satisfied:
        violation_codes.append("boundary_before_explanation_violation")
    elif boundary_required:
        satisfied_codes.append("boundary_before_explanation_satisfied")

    clarification_required = v02_result.state.clarification_first_required
    clarification_satisfied = _clarification_before_assertion_satisfied(artifact, positions)
    if clarification_required and not clarification_satisfied:
        violation_codes.append("clarification_before_assertion_violation")
    elif clarification_required:
        satisfied_codes.append("clarification_before_assertion_satisfied")

    qualifier_locality_failures = sum(
        1 for item in alignment_map.alignments if not item.qualifier_locality_pass
    )
    if qualifier_locality_failures > 0:
        violation_codes.append("qualifier_locality_violation")
    else:
        satisfied_codes.append("qualifier_locality_pass")

    blocked_expansion_leak_detected = any(
        item in artifact.surface_text for item in artifact.blocked_expansion_ids
    )
    if blocked_expansion_leak_detected:
        violation_codes.append("blocked_expansion_leak_detected")
    else:
        satisfied_codes.append("blocked_expansion_absent")

    protected_omission_violation_detected = any(
        item in artifact.surface_text for item in artifact.protected_omission_ids
    )
    if protected_omission_violation_detected:
        violation_codes.append("protected_omission_violation_detected")
    else:
        satisfied_codes.append("protected_omission_respected")

    implicit_commitment_leak_detected = bool(
        v01_result.state.promise_like_act_denied
        and (
            "I will " in artifact.surface_text
            or " guarantee" in artifact.surface_text
            or "guarantee " in artifact.surface_text
        )
    )
    if implicit_commitment_leak_detected:
        violation_codes.append("implicit_commitment_leak_detected")
    else:
        satisfied_codes.append("implicit_commitment_not_detected")

    hard_constraint_violation_count = len(tuple(dict.fromkeys(violation_codes)))
    return V03ConstraintSatisfactionReport(
        hard_constraint_violation_count=hard_constraint_violation_count,
        qualifier_locality_failures=qualifier_locality_failures,
        blocked_expansion_leak_detected=blocked_expansion_leak_detected,
        protected_omission_violation_detected=protected_omission_violation_detected,
        boundary_before_explanation_required=boundary_required,
        boundary_before_explanation_satisfied=boundary_satisfied,
        clarification_before_assertion_required=clarification_required,
        clarification_before_assertion_satisfied=clarification_satisfied,
        branch_compliance_pass=branch_compliance_pass,
        ordering_pass=ordering_pass,
        implicit_commitment_leak_detected=implicit_commitment_leak_detected,
        violation_codes=tuple(dict.fromkeys(violation_codes)),
        satisfied_codes=tuple(dict.fromkeys(satisfied_codes)),
    )


def _build_gate(
    *,
    report: V03ConstraintSatisfactionReport,
    failure_state: V03RealizationFailureState,
    surface_text: str,
) -> V03RealizationGateDecision:
    realization_consumer_ready = bool(surface_text.strip())
    alignment_consumer_ready = bool(
        report.ordering_pass
        and report.branch_compliance_pass
        and report.qualifier_locality_failures <= 0
        and not report.blocked_expansion_leak_detected
        and not report.protected_omission_violation_detected
    )
    constraint_report_consumer_ready = report.hard_constraint_violation_count <= 0
    restrictions: list[str] = []
    if not realization_consumer_ready:
        restrictions.append("realization_not_ready")
    if not alignment_consumer_ready:
        restrictions.append("alignment_violation")
    if not constraint_report_consumer_ready:
        restrictions.append("hard_constraint_violation")
    if failure_state.replan_required:
        restrictions.append("replan_required")
    if failure_state.partial_realization_only:
        restrictions.append("partial_realization_only")
    return V03RealizationGateDecision(
        realization_consumer_ready=realization_consumer_ready,
        alignment_consumer_ready=alignment_consumer_ready,
        constraint_report_consumer_ready=constraint_report_consumer_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="v03 gate exposes constrained-realization, alignment and hard-constraint readiness",
    )


def _segment_qualifier_locality_pass(
    *,
    mandatory_qualifier_ids: tuple[str, ...],
    realized_text: str,
) -> bool:
    if not mandatory_qualifier_ids:
        return True
    return all(item in realized_text for item in mandatory_qualifier_ids)


def _boundary_before_explanation_satisfied(
    artifact: V03RealizedUtteranceArtifact,
    positions: dict[str, int],
) -> bool:
    boundary_positions = [
        positions[item] for item in artifact.segment_order if item.endswith(":boundary")
    ]
    answer_like_positions = [
        positions[item]
        for item in artifact.segment_order
        if item.endswith(":answer") or item.endswith(":warning")
    ]
    if not boundary_positions or not answer_like_positions:
        return True
    return min(boundary_positions) < min(answer_like_positions)


def _clarification_before_assertion_satisfied(
    artifact: V03RealizedUtteranceArtifact,
    positions: dict[str, int],
) -> bool:
    clarification_positions = [
        positions[item]
        for item in artifact.segment_order
        if item.endswith(":clarification_request")
    ]
    answer_positions = [positions[item] for item in artifact.segment_order if item.endswith(":answer")]
    if not clarification_positions or not answer_positions:
        return True
    return min(clarification_positions) < min(answer_positions)


def _derive_narrowed_status(segments) -> V03RealizationStatus:
    roles = {item.segment_role for item in segments}
    if roles == {V02SegmentRole.BOUNDARY}:
        return V03RealizationStatus.BOUNDARY_ONLY_REALIZATION
    if roles.issubset({V02SegmentRole.QUALIFICATION, V02SegmentRole.CLARIFICATION_REQUEST}):
        return V03RealizationStatus.CLARIFICATION_ONLY_REALIZATION
    return V03RealizationStatus.PARTIAL_REALIZATION_ONLY


def _build_no_basis_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> V03ConstrainedRealizationResult:
    return _build_minimal_result(
        tick_id=tick_id,
        tick_index=tick_index,
        status=V03RealizationStatus.INSUFFICIENT_REALIZATION_BASIS,
        reason="v03 no-basis fallback keeps constrained realization gate non-activating",
        source_lineage=source_lineage,
        restrictions=("insufficient_realization_basis", "no_v03_realization_basis"),
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> V03ConstrainedRealizationResult:
    return _build_minimal_result(
        tick_id=tick_id,
        tick_index=tick_index,
        status=V03RealizationStatus.INSUFFICIENT_REALIZATION_BASIS,
        reason="v03 constrained realization disabled in ablation context",
        source_lineage=source_lineage,
        restrictions=("v03_disabled", "insufficient_realization_basis"),
    )


def _build_minimal_result(
    *,
    tick_id: str,
    tick_index: int,
    status: V03RealizationStatus,
    reason: str,
    source_lineage: tuple[str, ...],
    restrictions: tuple[str, ...],
) -> V03ConstrainedRealizationResult:
    artifact = V03RealizedUtteranceArtifact(
        realization_id=f"v03-realization:{tick_id}",
        surface_text="",
        segment_order=(),
        realized_segment_ids=(),
        omitted_segment_ids=(),
        source_act_ids=(),
        selected_branch_id="branch:none",
        blocked_expansion_ids=(),
        protected_omission_ids=(),
        partial_realization_only=True,
        provenance="v03.surface_realization.minimal",
    )
    alignment_map = V03RealizationAlignmentMap(
        alignments=(),
        aligned_segment_count=0,
        unaligned_segment_ids=(),
        branch_compliance_pass=False,
        ordering_pass=False,
        qualifier_locality_pass=False,
    )
    report = V03ConstraintSatisfactionReport(
        hard_constraint_violation_count=0,
        qualifier_locality_failures=0,
        blocked_expansion_leak_detected=False,
        protected_omission_violation_detected=False,
        boundary_before_explanation_required=False,
        boundary_before_explanation_satisfied=False,
        clarification_before_assertion_required=False,
        clarification_before_assertion_satisfied=False,
        branch_compliance_pass=False,
        ordering_pass=False,
        implicit_commitment_leak_detected=False,
        violation_codes=(),
        satisfied_codes=(),
    )
    failure = V03RealizationFailureState(
        failed=True,
        failure_code="insufficient_realization_basis",
        partial_realization_only=True,
        replan_required=False,
        reason=reason,
    )
    gate = V03RealizationGateDecision(
        realization_consumer_ready=False,
        alignment_consumer_ready=False,
        constraint_report_consumer_ready=False,
        restrictions=restrictions,
        reason=reason,
    )
    scope = V03ScopeMarker(
        scope="rt01_hosted_v03_first_slice",
        rt01_hosted_only=True,
        v03_first_slice_only=True,
        v_line_not_map_wide_ready=True,
        p02_not_implemented=True,
        map_wide_realization_enforcement=False,
        reason="v03 minimal fallback scope",
    )
    telemetry = V03Telemetry(
        realization_id=artifact.realization_id,
        tick_index=tick_index,
        realization_status=status,
        segment_count=0,
        aligned_segment_count=0,
        hard_constraint_violation_count=0,
        qualifier_locality_failures=0,
        blocked_expansion_leak_detected=False,
        protected_omission_count=0,
        boundary_before_explanation_required=False,
        boundary_before_explanation_satisfied=False,
        partial_realization_only=True,
        replan_required=False,
        downstream_consumer_ready=False,
    )
    return V03ConstrainedRealizationResult(
        realization_status=status,
        artifact=artifact,
        alignment_map=alignment_map,
        constraint_report=report,
        failure_state=failure,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )
