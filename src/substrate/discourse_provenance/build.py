from __future__ import annotations

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.discourse_provenance.models import (
    AssertionMode,
    CommitmentLineageRecord,
    CrossTurnAttachmentState,
    CrossTurnProvenanceLink,
    PerspectiveChainBundle,
    PerspectiveChainRecord,
    PerspectiveChainResult,
    PerspectiveOwnerClass,
    PerspectiveSourceClass,
    PerspectiveWrappedProposition,
)
from substrate.discourse_provenance.policy import evaluate_perspective_chain_downstream_gate
from substrate.discourse_provenance.telemetry import (
    build_perspective_chain_telemetry,
    perspective_chain_result_snapshot,
)
from substrate.scope_attribution.models import (
    ApplicabilityBundle,
    ApplicabilityResult,
    ApplicabilityClass,
    CommitmentLevel,
    SelfApplicabilityStatus,
    SourceScopeClass,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g04.validate_typed_inputs",
    "g04.perspective_chain_build",
    "g04.commitment_owner_derivation",
    "g04.cross_turn_reattachment",
    "g04.perspective_sensitive_modus_attachment",
    "g04.ambiguity_preservation",
    "g04.downstream_gate",
)


def build_discourse_provenance_chain(
    applicability_result_or_bundle: ApplicabilityResult | ApplicabilityBundle,
) -> PerspectiveChainResult:
    applicability_bundle, source_lineage = _extract_applicability_input(applicability_result_or_bundle)
    if not applicability_bundle.records:
        return _abstain_result(
            applicability_bundle=applicability_bundle,
            source_lineage=source_lineage,
            reason="applicability bundle has no records",
        )

    chain_records: list[PerspectiveChainRecord] = []
    commitment_lineages: list[CommitmentLineageRecord] = []
    wrapped: list[PerspectiveWrappedProposition] = []
    cross_turn_links: list[CrossTurnProvenanceLink] = []
    ambiguity_reasons: list[str] = list(applicability_bundle.ambiguity_reasons)
    low_coverage_reasons: list[str] = list(applicability_bundle.low_coverage_reasons)

    previous_anchor: str | None = source_lineage[-1] if source_lineage else None
    for idx, record in enumerate(applicability_bundle.records, start=1):
        assertion_mode, source_class = _derive_assertion_and_source(record)
        perspective_owner, commitment_owner = _derive_owners(assertion_mode, record)
        discourse_level = _derive_discourse_level(assertion_mode, source_lineage)

        if perspective_owner is PerspectiveOwnerClass.MIXED_OWNER:
            ambiguity_reasons.append("mixed_provenance")
        if commitment_owner is PerspectiveOwnerClass.UNRESOLVED_OWNER:
            ambiguity_reasons.append("unresolved_commitment_owner")
        if discourse_level >= 3 and assertion_mode in {
            AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
            AssertionMode.QUOTED_EXTERNAL_CONTENT,
            AssertionMode.ATTRIBUTED_BELIEF,
        }:
            ambiguity_reasons.append("ambiguous_perspective_depth")
        if not applicability_bundle.source_surface_ref:
            ambiguity_reasons.append("discourse_anchor_missing")
        if (
            assertion_mode is AssertionMode.QUOTED_EXTERNAL_CONTENT
            and commitment_owner is not PerspectiveOwnerClass.EXTERNAL_OWNER
        ):
            ambiguity_reasons.append("broken_quote_chain")

        path = _build_provenance_path(
            source_class=source_class,
            assertion_mode=assertion_mode,
            commitment_owner=commitment_owner,
            current_anchor=record.attribution_id,
        )
        stack = _build_perspective_stack(source_class, perspective_owner, commitment_owner)
        constraints = _derive_downstream_constraints(
            assertion_mode=assertion_mode,
            source_class=source_class,
            commitment_owner=commitment_owner,
            perspective_owner=perspective_owner,
            record=record,
            ambiguity_reasons=tuple(ambiguity_reasons),
        )

        chain_id = f"chain-{idx}"
        chain_records.append(
            PerspectiveChainRecord(
                chain_id=chain_id,
                proposition_id=record.proposition_id,
                semantic_unit_id=record.semantic_unit_id,
                discourse_level=discourse_level,
                current_anchor=record.attribution_id,
                provenance_path=path,
                perspective_stack=stack,
                commitment_owner=commitment_owner,
                perspective_owner=perspective_owner,
                assertion_mode=assertion_mode,
                source_class=source_class,
                confidence=_estimate_chain_confidence(record.confidence, discourse_level, ambiguity_reasons),
                provenance="g04 perspective chain from g03 applicability record",
            )
        )
        commitment_lineages.append(
            CommitmentLineageRecord(
                lineage_id=f"lineage-{idx}",
                proposition_id=record.proposition_id,
                commitment_owner=commitment_owner,
                ownership_conflict=commitment_owner in {
                    PerspectiveOwnerClass.MIXED_OWNER,
                    PerspectiveOwnerClass.UNRESOLVED_OWNER,
                },
                lineage_path=path,
                downstream_constraints=constraints,
                confidence=_estimate_lineage_confidence(record.confidence, commitment_owner),
                provenance="g04 commitment lineage from perspective chain",
            )
        )
        wrapped.append(
            PerspectiveWrappedProposition(
                wrapper_id=f"wrap-{idx}",
                proposition_id=record.proposition_id,
                semantic_unit_id=record.semantic_unit_id,
                commitment_owner=commitment_owner,
                perspective_owner=perspective_owner,
                assertion_mode=assertion_mode,
                source_class=source_class,
                discourse_level=discourse_level,
                provenance_path=path,
                perspective_stack=stack,
                downstream_constraints=constraints,
                confidence=_estimate_chain_confidence(record.confidence, discourse_level, ambiguity_reasons),
                provenance="g04 perspective-wrapped proposition",
            )
        )

        attachment_state, repair_reason = _derive_cross_turn_state(
            record=record,
            assertion_mode=assertion_mode,
            ambiguity_reasons=tuple(ambiguity_reasons),
            previous_anchor=previous_anchor,
        )
        cross_turn_links.append(
            CrossTurnProvenanceLink(
                link_id=f"xturn-{idx}",
                chain_id=chain_id,
                previous_anchor=previous_anchor,
                current_anchor=record.attribution_id,
                attachment_state=attachment_state,
                repair_reason=repair_reason,
                confidence=_estimate_link_confidence(record.confidence, attachment_state),
                provenance="g04 cross-turn provenance reattachment assessment",
            )
        )
        previous_anchor = record.attribution_id

    if not chain_records:
        low_coverage_reasons.append("chain_records_missing")
    if not commitment_lineages:
        low_coverage_reasons.append("commitment_lineages_missing")
    if not wrapped:
        low_coverage_reasons.append("wrapped_propositions_missing")
    if not cross_turn_links:
        low_coverage_reasons.append("cross_turn_links_missing")

    if any(link.attachment_state is CrossTurnAttachmentState.REPAIR_PENDING for link in cross_turn_links):
        low_coverage_reasons.append("cross_turn_repair_pending")

    low_coverage_mode = bool(low_coverage_reasons)
    bundle = PerspectiveChainBundle(
        source_applicability_ref=applicability_bundle.source_runtime_graph_ref,
        source_runtime_graph_ref=applicability_bundle.source_runtime_graph_ref,
        source_grounded_ref=applicability_bundle.source_grounded_ref,
        source_dictum_ref=applicability_bundle.source_dictum_ref,
        source_syntax_ref=applicability_bundle.source_syntax_ref,
        source_surface_ref=applicability_bundle.source_surface_ref,
        linked_proposition_ids=applicability_bundle.linked_proposition_ids,
        linked_semantic_unit_ids=applicability_bundle.linked_semantic_unit_ids,
        chain_records=tuple(chain_records),
        commitment_lineages=tuple(commitment_lineages),
        wrapped_propositions=tuple(wrapped),
        cross_turn_links=tuple(cross_turn_links),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=low_coverage_mode,
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        no_truth_upgrade=True,
        reason="g04 compiled bounded discourse provenance and perspective-chain ownership",
    )

    gate = evaluate_perspective_chain_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                applicability_bundle.source_runtime_graph_ref,
                applicability_bundle.source_grounded_ref,
                applicability_bundle.source_dictum_ref,
                applicability_bundle.source_syntax_ref,
                *((applicability_bundle.source_surface_ref,) if applicability_bundle.source_surface_ref else ()),
                *source_lineage,
            )
        )
    )
    telemetry = build_perspective_chain_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="g03 applicability transformed into bounded perspective chain and commitment lineage",
    )
    confidence = _estimate_result_confidence(bundle)
    partial_known = bool(bundle.low_coverage_mode or bundle.ambiguity_reasons)
    partial_known_reason = (
        "; ".join(bundle.ambiguity_reasons)
        if bundle.ambiguity_reasons
        else ("; ".join(bundle.low_coverage_reasons) if bundle.low_coverage_reasons else None)
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else gate.reason
    return PerspectiveChainResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_truth_upgrade=True,
    )


def perspective_chain_result_to_payload(result: PerspectiveChainResult) -> dict[str, object]:
    return perspective_chain_result_snapshot(result)


def persist_perspective_chain_result_via_f01(
    *,
    result: PerspectiveChainResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g04-discourse-provenance-perspective-chaining",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"discourse-provenance-step-{transition_id}",
            "discourse_provenance_snapshot": perspective_chain_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_applicability_input(
    applicability_result_or_bundle: ApplicabilityResult | ApplicabilityBundle,
) -> tuple[ApplicabilityBundle, tuple[str, ...]]:
    if isinstance(applicability_result_or_bundle, ApplicabilityResult):
        return applicability_result_or_bundle.bundle, applicability_result_or_bundle.telemetry.source_lineage
    if isinstance(applicability_result_or_bundle, ApplicabilityBundle):
        return applicability_result_or_bundle, ()
    raise TypeError("build_discourse_provenance_chain requires ApplicabilityResult or ApplicabilityBundle")


def _derive_assertion_and_source(record):
    if record.source_scope_class is SourceScopeClass.QUOTED:
        return AssertionMode.QUOTED_EXTERNAL_CONTENT, PerspectiveSourceClass.QUOTED_SPEAKER
    if record.source_scope_class is SourceScopeClass.REPORTED:
        if record.commitment_level is CommitmentLevel.EXTERNAL_REPORTED:
            return AssertionMode.REPORTED_EXTERNAL_COMMITMENT, PerspectiveSourceClass.REPORTED_SOURCE
        return AssertionMode.ATTRIBUTED_BELIEF, PerspectiveSourceClass.BELIEVER
    if record.source_scope_class is SourceScopeClass.HYPOTHETICAL:
        return AssertionMode.HYPOTHETICAL_BRANCH, PerspectiveSourceClass.IMAGINER
    if record.source_scope_class is SourceScopeClass.QUESTIONED:
        return AssertionMode.QUESTION_FRAME, PerspectiveSourceClass.QUESTIONER
    if record.source_scope_class is SourceScopeClass.MIXED:
        return AssertionMode.MIXED, PerspectiveSourceClass.MIXED
    if record.source_scope_class is SourceScopeClass.UNRESOLVED:
        return AssertionMode.UNRESOLVED, PerspectiveSourceClass.UNKNOWN
    if record.commitment_level is CommitmentLevel.DENIED:
        return AssertionMode.DENIAL_FRAME, PerspectiveSourceClass.DENIER
    return AssertionMode.DIRECT_CURRENT_COMMITMENT, PerspectiveSourceClass.CURRENT_UTTERER


def _derive_owners(assertion_mode: AssertionMode, record) -> tuple[PerspectiveOwnerClass, PerspectiveOwnerClass]:
    if assertion_mode in {
        AssertionMode.QUOTED_EXTERNAL_CONTENT,
        AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
        AssertionMode.ATTRIBUTED_BELIEF,
        AssertionMode.REMEMBERED_CONTENT,
    }:
        return PerspectiveOwnerClass.EXTERNAL_OWNER, PerspectiveOwnerClass.EXTERNAL_OWNER
    if assertion_mode in {AssertionMode.MIXED, AssertionMode.IRONIC_META_PERSPECTIVE_CANDIDATE}:
        return PerspectiveOwnerClass.MIXED_OWNER, PerspectiveOwnerClass.MIXED_OWNER
    if assertion_mode in {AssertionMode.UNRESOLVED, AssertionMode.HYPOTHETICAL_BRANCH, AssertionMode.QUESTION_FRAME}:
        return PerspectiveOwnerClass.UNRESOLVED_OWNER, PerspectiveOwnerClass.UNRESOLVED_OWNER
    if (
        record.self_applicability_status is SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE
        or record.applicability_class is ApplicabilityClass.MIXED_APPLICABILITY
    ):
        return PerspectiveOwnerClass.MIXED_OWNER, PerspectiveOwnerClass.UNRESOLVED_OWNER
    return PerspectiveOwnerClass.CURRENT_UTTERER, PerspectiveOwnerClass.CURRENT_UTTERER


def _derive_discourse_level(assertion_mode: AssertionMode, source_lineage: tuple[str, ...]) -> int:
    level = 1
    if assertion_mode in {
        AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
        AssertionMode.QUOTED_EXTERNAL_CONTENT,
        AssertionMode.ATTRIBUTED_BELIEF,
        AssertionMode.HYPOTHETICAL_BRANCH,
        AssertionMode.QUESTION_FRAME,
    }:
        level = 2
    lineage_depth_hint = min(2, max(0, len(source_lineage) - 3))
    return min(3, level + lineage_depth_hint)


def _build_provenance_path(
    *,
    source_class: PerspectiveSourceClass,
    assertion_mode: AssertionMode,
    commitment_owner: PerspectiveOwnerClass,
    current_anchor: str,
) -> tuple[str, ...]:
    path = ["anchor:current_utterer"]
    if source_class is PerspectiveSourceClass.REPORTED_SOURCE:
        path.append("transition:report")
    elif source_class is PerspectiveSourceClass.QUOTED_SPEAKER:
        path.append("transition:quote")
    elif source_class is PerspectiveSourceClass.BELIEVER:
        path.append("transition:belief_attribution")
    elif source_class is PerspectiveSourceClass.IMAGINER:
        path.append("transition:hypothetical_branch")
    elif source_class is PerspectiveSourceClass.QUESTIONER:
        path.append("transition:question_frame")
    elif source_class is PerspectiveSourceClass.DENIER:
        path.append("transition:denial_frame")
    elif source_class is PerspectiveSourceClass.MIXED:
        path.append("transition:mixed_source")
    elif source_class is PerspectiveSourceClass.UNKNOWN:
        path.append("transition:unknown_source")

    path.append(f"assertion_mode:{assertion_mode.value}")
    path.append(f"commitment_owner:{commitment_owner.value}")
    path.append(f"anchor:{current_anchor}")
    return tuple(path)


def _build_perspective_stack(
    source_class: PerspectiveSourceClass,
    perspective_owner: PerspectiveOwnerClass,
    commitment_owner: PerspectiveOwnerClass,
) -> tuple[str, ...]:
    return (
        "frame:current_utterer",
        f"source:{source_class.value}",
        f"perspective_owner:{perspective_owner.value}",
        f"commitment_owner:{commitment_owner.value}",
    )


def _derive_downstream_constraints(
    *,
    assertion_mode: AssertionMode,
    source_class: PerspectiveSourceClass,
    commitment_owner: PerspectiveOwnerClass,
    perspective_owner: PerspectiveOwnerClass,
    record,
    ambiguity_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    constraints: list[str] = ["no_truth_upgrade", "closure_requires_chain_consistency_check"]
    if commitment_owner is not PerspectiveOwnerClass.CURRENT_UTTERER:
        constraints.append("response_should_not_echo_as_direct_user_belief")
    if commitment_owner in {PerspectiveOwnerClass.UNRESOLVED_OWNER, PerspectiveOwnerClass.MIXED_OWNER}:
        constraints.append("narrative_binding_blocked_without_commitment_owner")
        constraints.append("clarification_recommended_on_owner_ambiguity")
    if source_class in {PerspectiveSourceClass.REPORTED_SOURCE, PerspectiveSourceClass.QUOTED_SPEAKER}:
        constraints.append("response_should_not_flatten_owner")
    if assertion_mode in {AssertionMode.HYPOTHETICAL_BRANCH, AssertionMode.QUESTION_FRAME, AssertionMode.MIXED, AssertionMode.UNRESOLVED}:
        constraints.append("narrative_binding_blocked_without_commitment_owner")
    if "recommend_clarification" in record.downstream_permissions:
        constraints.append("clarification_recommended_on_owner_ambiguity")
    if "discourse_anchor_missing" in ambiguity_reasons or "ambiguous_perspective_depth" in ambiguity_reasons:
        constraints.append("closure_requires_chain_consistency_check")
    return tuple(dict.fromkeys(constraints))


def _derive_cross_turn_state(
    *,
    record,
    assertion_mode: AssertionMode,
    ambiguity_reasons: tuple[str, ...],
    previous_anchor: str | None,
) -> tuple[CrossTurnAttachmentState, str | None]:
    if previous_anchor and assertion_mode is AssertionMode.DENIAL_FRAME:
        return CrossTurnAttachmentState.REPAIR_PENDING, "denial frame indicates prior attribution correction pending"
    if any(
        reason in ambiguity_reasons
        for reason in (
            "broken_quote_chain",
            "mixed_provenance",
            "unresolved_commitment_owner",
        )
    ):
        return CrossTurnAttachmentState.REPAIR_PENDING, "owner/perspective ambiguity requires reattachment"
    if previous_anchor and assertion_mode in {
        AssertionMode.QUOTED_EXTERNAL_CONTENT,
        AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
        AssertionMode.ATTRIBUTED_BELIEF,
    }:
        return CrossTurnAttachmentState.REATTACHED, "external perspective reattached from prior anchor"
    if previous_anchor is None:
        return CrossTurnAttachmentState.UNKNOWN, "no prior discourse anchor"
    return CrossTurnAttachmentState.STABLE, None


def _estimate_chain_confidence(base: float, discourse_level: int, ambiguity_reasons: list[str]) -> float:
    value = base
    value -= max(0, discourse_level - 1) * 0.06
    value -= min(0.25, len(set(ambiguity_reasons)) * 0.015)
    return max(0.08, min(0.9, round(value, 4)))


def _estimate_lineage_confidence(base: float, commitment_owner: PerspectiveOwnerClass) -> float:
    value = base
    if commitment_owner in {PerspectiveOwnerClass.MIXED_OWNER, PerspectiveOwnerClass.UNRESOLVED_OWNER}:
        value -= 0.18
    return max(0.08, min(0.9, round(value, 4)))


def _estimate_link_confidence(base: float, state: CrossTurnAttachmentState) -> float:
    value = base
    if state is CrossTurnAttachmentState.REPAIR_PENDING:
        value -= 0.2
    elif state is CrossTurnAttachmentState.UNKNOWN:
        value -= 0.1
    return max(0.08, min(0.9, round(value, 4)))


def _estimate_result_confidence(bundle: PerspectiveChainBundle) -> float:
    base = 0.72
    base -= min(0.26, len(bundle.ambiguity_reasons) * 0.03)
    if bundle.low_coverage_mode:
        base -= min(0.28, len(bundle.low_coverage_reasons) * 0.05)
    if not bundle.chain_records:
        base -= 0.25
    return max(0.08, min(0.9, round(base, 4)))


def _abstain_result(
    *,
    applicability_bundle: ApplicabilityBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> PerspectiveChainResult:
    bundle = PerspectiveChainBundle(
        source_applicability_ref=applicability_bundle.source_runtime_graph_ref,
        source_runtime_graph_ref=applicability_bundle.source_runtime_graph_ref,
        source_grounded_ref=applicability_bundle.source_grounded_ref,
        source_dictum_ref=applicability_bundle.source_dictum_ref,
        source_syntax_ref=applicability_bundle.source_syntax_ref,
        source_surface_ref=applicability_bundle.source_surface_ref,
        linked_proposition_ids=applicability_bundle.linked_proposition_ids,
        linked_semantic_unit_ids=applicability_bundle.linked_semantic_unit_ids,
        chain_records=(),
        commitment_lineages=(),
        wrapped_propositions=(),
        cross_turn_links=(),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=("abstain",),
        no_truth_upgrade=True,
        reason="g04 abstained due to insufficient g03 applicability basis",
    )
    gate = evaluate_perspective_chain_downstream_gate(bundle)
    telemetry = build_perspective_chain_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient g03 applicability -> g04 abstain",
    )
    return PerspectiveChainResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_truth_upgrade=True,
    )
