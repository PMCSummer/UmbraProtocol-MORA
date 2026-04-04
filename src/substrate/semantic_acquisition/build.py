from __future__ import annotations

from dataclasses import replace

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.discourse_provenance.models import (
    AssertionMode,
    CrossTurnAttachmentState,
    PerspectiveChainBundle,
    PerspectiveChainResult,
    PerspectiveOwnerClass,
)
from substrate.semantic_acquisition.models import (
    AcquisitionClusterLink,
    AcquisitionStatus,
    RevisionCondition,
    RevisionConditionKind,
    SemanticAcquisitionBundle,
    SemanticAcquisitionResult,
    StabilityClass,
    SupportConflictProfile,
    ProvisionalAcquisitionRecord,
)
from substrate.semantic_acquisition.policy import evaluate_semantic_acquisition_downstream_gate
from substrate.semantic_acquisition.telemetry import (
    build_semantic_acquisition_telemetry,
    semantic_acquisition_result_snapshot,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g05.validate_typed_inputs",
    "g05.provisional_acquisition_build",
    "g05.support_conflict_profiling",
    "g05.cluster_linkage_and_competition",
    "g05.revision_hook_derivation",
    "g05.downstream_gate",
)


def build_semantic_acquisition(
    perspective_chain_result_or_bundle: PerspectiveChainResult | PerspectiveChainBundle,
) -> SemanticAcquisitionResult:
    perspective_bundle, source_lineage = _extract_perspective_input(perspective_chain_result_or_bundle)
    if not perspective_bundle.wrapped_propositions:
        return _abstain_result(
            perspective_bundle=perspective_bundle,
            source_lineage=source_lineage,
            reason="perspective chain has no wrapped propositions",
        )

    ambiguity_reasons: list[str] = list(perspective_bundle.ambiguity_reasons)
    low_coverage_reasons: list[str] = list(perspective_bundle.low_coverage_reasons)

    links_by_chain = {link.chain_id: link for link in perspective_bundle.cross_turn_links}
    chain_by_prop = {record.proposition_id: record for record in perspective_bundle.chain_records}

    records: list[ProvisionalAcquisitionRecord] = []
    cluster_members: dict[str, list[str]] = {}
    cluster_owner_modes: dict[str, set[tuple[str, str]]] = {}
    cluster_index = 0
    acquisition_index = 0

    for wrapped in perspective_bundle.wrapped_propositions:
        acquisition_index += 1
        chain = chain_by_prop.get(wrapped.proposition_id)
        chain_id = chain.chain_id if chain else None
        link = links_by_chain.get(chain_id) if chain_id else None

        support_reasons, conflict_reasons, unresolved_slots = _derive_support_conflict(
            wrapped=wrapped,
            link=link,
            bundle_ambiguity=tuple(ambiguity_reasons),
        )
        support_score = float(len(support_reasons))
        conflict_score = float(len(conflict_reasons))

        status, stability, blocked_reason = _derive_status(
            support_score=support_score,
            conflict_score=conflict_score,
            wrapped=wrapped,
            unresolved_slots=unresolved_slots,
        )
        revision_conditions = _derive_revision_conditions(
            wrapped=wrapped,
            link=link,
            unresolved_slots=unresolved_slots,
            support_score=support_score,
            conflict_reasons=conflict_reasons,
        )
        downstream_permissions = _derive_downstream_permissions(status, revision_conditions)

        cluster_key = _cluster_basis(wrapped.semantic_unit_id, wrapped.proposition_id)
        if cluster_key not in cluster_members:
            cluster_index += 1
            cluster_members[cluster_key] = []
        cluster_id = f"cluster-{cluster_index}"
        acquisition_id = f"acq-{acquisition_index}"
        cluster_members[cluster_key].append(acquisition_id)
        cluster_owner_modes.setdefault(cluster_key, set()).add(
            (wrapped.commitment_owner.value, wrapped.assertion_mode.value)
        )

        profile = SupportConflictProfile(
            support_score=round(support_score, 4),
            conflict_score=round(conflict_score, 4),
            support_reasons=tuple(dict.fromkeys(support_reasons)),
            conflict_reasons=tuple(dict.fromkeys(conflict_reasons)),
            unresolved_slots=tuple(dict.fromkeys(unresolved_slots)),
        )
        record = ProvisionalAcquisitionRecord(
            acquisition_id=acquisition_id,
            proposition_id=wrapped.proposition_id,
            semantic_unit_id=wrapped.semantic_unit_id,
            acquisition_status=status,
            stability_class=stability,
            support_conflict_profile=profile,
            revision_conditions=tuple(revision_conditions),
            downstream_permissions=downstream_permissions,
            cluster_id=cluster_id,
            compatible_acquisition_ids=(),
            competing_acquisition_ids=(),
            blocked_reason=blocked_reason,
        context_anchor=wrapped.wrapper_id,
        confidence=_estimate_record_confidence(wrapped.confidence, support_score, conflict_score, status),
            provenance="g05 provisional acquisition from g04 perspective-wrapped proposition",
        )
        records.append(record)

    records = _apply_cluster_competition(records, cluster_members, cluster_owner_modes)
    cluster_links = _build_cluster_links(records, cluster_members)

    if not records:
        low_coverage_reasons.append("acquisition_records_missing")
    if not cluster_links:
        low_coverage_reasons.append("cluster_links_missing")

    if any(record.acquisition_status is AcquisitionStatus.COMPETING_PROVISIONAL for record in records):
        ambiguity_reasons.append("competing_meanings_preserved")
    if any(record.acquisition_status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION for record in records):
        ambiguity_reasons.append("blocked_pending_clarification")

    low_coverage_mode = bool(low_coverage_reasons)
    bundle = SemanticAcquisitionBundle(
        source_perspective_chain_ref=perspective_bundle.source_applicability_ref,
        source_applicability_ref=perspective_bundle.source_applicability_ref,
        source_runtime_graph_ref=perspective_bundle.source_runtime_graph_ref,
        source_grounded_ref=perspective_bundle.source_grounded_ref,
        source_dictum_ref=perspective_bundle.source_dictum_ref,
        source_syntax_ref=perspective_bundle.source_syntax_ref,
        source_surface_ref=perspective_bundle.source_surface_ref,
        linked_proposition_ids=perspective_bundle.linked_proposition_ids,
        linked_semantic_unit_ids=perspective_bundle.linked_semantic_unit_ids,
        acquisition_records=tuple(records),
        cluster_links=tuple(cluster_links),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=low_coverage_mode,
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        no_final_semantic_closure=True,
        reason="g05 compiled provisional semantic acquisition with support/conflict and reopen hooks",
    )
    gate = evaluate_semantic_acquisition_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                perspective_bundle.source_applicability_ref,
                perspective_bundle.source_runtime_graph_ref,
                perspective_bundle.source_grounded_ref,
                perspective_bundle.source_dictum_ref,
                perspective_bundle.source_syntax_ref,
                *((perspective_bundle.source_surface_ref,) if perspective_bundle.source_surface_ref else ()),
                *source_lineage,
            )
        )
    )
    telemetry = build_semantic_acquisition_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="g04 perspective chain stabilized into bounded provisional acquisition state",
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
    return SemanticAcquisitionResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_final_semantic_closure=True,
    )


def semantic_acquisition_result_to_payload(result: SemanticAcquisitionResult) -> dict[str, object]:
    return semantic_acquisition_result_snapshot(result)


def persist_semantic_acquisition_result_via_f01(
    *,
    result: SemanticAcquisitionResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g05-semantic-acquisition-provisional-stabilization",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"semantic-acquisition-step-{transition_id}",
            "semantic_acquisition_snapshot": semantic_acquisition_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_perspective_input(
    perspective_chain_result_or_bundle: PerspectiveChainResult | PerspectiveChainBundle,
) -> tuple[PerspectiveChainBundle, tuple[str, ...]]:
    if isinstance(perspective_chain_result_or_bundle, PerspectiveChainResult):
        return perspective_chain_result_or_bundle.bundle, perspective_chain_result_or_bundle.telemetry.source_lineage
    if isinstance(perspective_chain_result_or_bundle, PerspectiveChainBundle):
        return perspective_chain_result_or_bundle, ()
    raise TypeError("build_semantic_acquisition requires PerspectiveChainResult or PerspectiveChainBundle")


def _derive_support_conflict(*, wrapped, link, bundle_ambiguity: tuple[str, ...]) -> tuple[list[str], list[str], list[str]]:
    support: list[str] = []
    conflict: list[str] = []
    unresolved: list[str] = []

    support.append("chain_object_present")
    if wrapped.provenance_path:
        support.append("provenance_path_present")

    if wrapped.assertion_mode is AssertionMode.DIRECT_CURRENT_COMMITMENT:
        support.append("direct_current_commitment_support")
    if wrapped.source_class.value == "current_utterer":
        support.append("current_utterer_source_support")
    if wrapped.source_class.value == "unknown":
        conflict.append("source_scope_unknown")
        unresolved.append("source_scope")
    if wrapped.commitment_owner is PerspectiveOwnerClass.CURRENT_UTTERER:
        support.append("current_owner_support")

    if link is not None:
        if link.attachment_state in {CrossTurnAttachmentState.STABLE, CrossTurnAttachmentState.REATTACHED}:
            support.append("cross_turn_continuity_support")
        if link.attachment_state is CrossTurnAttachmentState.REPAIR_PENDING:
            conflict.append("cross_turn_repair_pending")
            unresolved.append("cross_turn_repair")
        if link.attachment_state is CrossTurnAttachmentState.UNKNOWN:
            conflict.append("cross_turn_unknown")
            unresolved.append("cross_turn_unknown")
        if link.repair_reason:
            conflict.append("cross_turn_repair_signal")

    if wrapped.assertion_mode in {
        AssertionMode.HYPOTHETICAL_BRANCH,
        AssertionMode.QUESTION_FRAME,
        AssertionMode.DENIAL_FRAME,
        AssertionMode.MIXED,
        AssertionMode.UNRESOLVED,
    }:
        conflict.append(f"assertion_mode:{wrapped.assertion_mode.value}")
    if wrapped.commitment_owner in {PerspectiveOwnerClass.MIXED_OWNER, PerspectiveOwnerClass.UNRESOLVED_OWNER}:
        conflict.append("commitment_owner_ambiguous")
        unresolved.append("commitment_owner")
    if wrapped.perspective_owner in {PerspectiveOwnerClass.MIXED_OWNER, PerspectiveOwnerClass.UNRESOLVED_OWNER}:
        unresolved.append("perspective_owner")

    if "clarification_recommended_on_owner_ambiguity" in wrapped.downstream_constraints:
        conflict.append("clarification_required")
    if "narrative_binding_blocked_without_commitment_owner" in wrapped.downstream_constraints:
        conflict.append("binding_blocked")
    if "response_should_not_flatten_owner" in wrapped.downstream_constraints:
        if (
            wrapped.assertion_mode is AssertionMode.DIRECT_CURRENT_COMMITMENT
            and wrapped.source_class.value == "current_utterer"
        ):
            unresolved.append("owner_flattening_risk")
        else:
            conflict.append("owner_flattening_risk")

    if any(
        reason in bundle_ambiguity
        for reason in (
            "mixed_provenance",
            "broken_quote_chain",
            "unresolved_commitment_owner",
        )
    ):
        unresolved.append("bundle_ambiguity_from_g04")
    if "cross_turn_repair_pending" in bundle_ambiguity:
        conflict.append("bundle_cross_turn_repair_pending")
    if "discourse_anchor_missing" in bundle_ambiguity:
        unresolved.append("temporal_anchor")
    if "ambiguous_perspective_depth" in bundle_ambiguity:
        unresolved.append("perspective_depth")

    return support, conflict, unresolved


def _derive_status(
    *,
    support_score: float,
    conflict_score: float,
    wrapped,
    unresolved_slots: list[str],
) -> tuple[AcquisitionStatus, StabilityClass, str | None]:
    has_owner_complication = wrapped.commitment_owner in {
        PerspectiveOwnerClass.MIXED_OWNER,
        PerspectiveOwnerClass.UNRESOLVED_OWNER,
    }

    if conflict_score >= 5 and support_score <= 1:
        return (
            AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
            StabilityClass.BLOCKED,
            "conflict pressure dominates support; clarification required",
        )
    if has_owner_complication and conflict_score >= 3:
        return (
            AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
            StabilityClass.BLOCKED,
            "owner ambiguity blocks provisional stabilization",
        )
    if support_score >= 4 and conflict_score == 0:
        return AcquisitionStatus.STABLE_PROVISIONAL, StabilityClass.STABLE, None
    if support_score >= 1 and conflict_score <= 2:
        return AcquisitionStatus.WEAK_PROVISIONAL, StabilityClass.WEAK, None
    if support_score == 0 and conflict_score <= 1:
        return AcquisitionStatus.CONTEXT_ONLY, StabilityClass.CONTEXT_ONLY, "context-only semantics with weak support"
    if support_score == 0 and conflict_score >= 4:
        return AcquisitionStatus.DISCARDED_AS_INCOHERENT, StabilityClass.INCOHERENT, "incoherent profile under unresolved pressure"

    blocking_unresolved = {"commitment_owner", "cross_turn_repair", "source_scope", "temporal_anchor"}
    if any(slot in blocking_unresolved for slot in unresolved_slots):
        return (
            AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
            StabilityClass.BLOCKED,
            "unresolved slots prevent bounded stabilization",
        )
    return AcquisitionStatus.WEAK_PROVISIONAL, StabilityClass.WEAK, None


def _derive_revision_conditions(
    *,
    wrapped,
    link,
    unresolved_slots: list[str],
    support_score: float,
    conflict_reasons: list[str],
) -> list[RevisionCondition]:
    conditions: list[RevisionCondition] = []
    index = 0

    def _add(kind: RevisionConditionKind, reason: str, confidence: float) -> None:
        nonlocal index
        index += 1
        conditions.append(
            RevisionCondition(
                condition_id=f"rev-{index}",
                condition_kind=kind,
                trigger_reason=reason,
                confidence=max(0.08, min(0.9, round(confidence, 4))),
                provenance="g05 revision condition derived from support/conflict profile",
            )
        )

    if link and link.attachment_state is CrossTurnAttachmentState.REPAIR_PENDING:
        _add(RevisionConditionKind.REOPEN_ON_CORRECTION, "cross-turn repair pending", 0.6)
        _add(RevisionConditionKind.REOPEN_ON_QUOTE_REPAIR, "quote/report repair required", 0.58)
    if wrapped.assertion_mode in {
        AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
        AssertionMode.QUOTED_EXTERNAL_CONTENT,
        AssertionMode.ATTRIBUTED_BELIEF,
        AssertionMode.REMEMBERED_CONTENT,
    }:
        _add(RevisionConditionKind.REOPEN_ON_QUOTE_REPAIR, "reported/quoted perspective remains reopenable", 0.55)
    if wrapped.assertion_mode is AssertionMode.DENIAL_FRAME:
        _add(RevisionConditionKind.REOPEN_ON_CORRECTION, "denial frame is correction-sensitive", 0.57)
    if "commitment_owner" in unresolved_slots or "perspective_owner" in unresolved_slots:
        _add(RevisionConditionKind.REOPEN_ON_TARGET_REBINDING, "owner/target rebinding unresolved", 0.56)
    if wrapped.assertion_mode in {AssertionMode.HYPOTHETICAL_BRANCH, AssertionMode.QUESTION_FRAME}:
        _add(RevisionConditionKind.REOPEN_ON_TEMPORAL_DISAMBIGUATION, "temporal/modal branch remains unresolved", 0.54)
    if "clarification_required" in conflict_reasons:
        _add(RevisionConditionKind.REOPEN_ON_CLARIFICATION_ANSWER, "clarification answer required", 0.62)
    if support_score <= 1:
        _add(RevisionConditionKind.REOPEN_ON_STRONGER_BINDING_EVIDENCE, "support basis weak and reopenable", 0.52)
    return conditions


def _derive_downstream_permissions(
    status: AcquisitionStatus,
    revision_conditions: list[RevisionCondition],
) -> tuple[str, ...]:
    permissions: list[str] = ["no_final_semantic_closure"]
    if revision_conditions:
        permissions.append("revision_hooks_must_be_read")

    if status is AcquisitionStatus.STABLE_PROVISIONAL:
        permissions.append("allow_provisional_semantic_uptake")
    elif status is AcquisitionStatus.WEAK_PROVISIONAL:
        permissions.extend(
            [
                "allow_provisional_semantic_uptake",
                "memory_uptake_blocked",
            ]
        )
    elif status is AcquisitionStatus.COMPETING_PROVISIONAL:
        permissions.extend(
            [
                "competing_meanings_preserved",
                "memory_uptake_blocked",
                "closure_blocked_pending_clarification",
            ]
        )
    elif status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION:
        permissions.extend(
            [
                "closure_blocked_pending_clarification",
                "memory_uptake_blocked",
            ]
        )
    elif status is AcquisitionStatus.CONTEXT_ONLY:
        permissions.extend(
            [
                "context_only_output",
                "memory_uptake_blocked",
            ]
        )
    else:
        permissions.extend(
            [
                "discarded_as_incoherent",
                "memory_uptake_blocked",
                "closure_blocked_pending_clarification",
            ]
        )
    return tuple(dict.fromkeys(permissions))


def _apply_cluster_competition(
    records: list[ProvisionalAcquisitionRecord],
    cluster_members: dict[str, list[str]],
    cluster_owner_modes: dict[str, set[tuple[str, str]]],
) -> list[ProvisionalAcquisitionRecord]:
    by_id = {record.acquisition_id: record for record in records}
    updated: dict[str, ProvisionalAcquisitionRecord] = dict(by_id)

    for cluster_key, member_ids in cluster_members.items():
        owner_modes = cluster_owner_modes.get(cluster_key, set())
        incompatible = len(owner_modes) > 1 and len(member_ids) > 1
        for member_id in member_ids:
            record = updated[member_id]
            compatible_ids = tuple(mid for mid in member_ids if mid != member_id and not incompatible)
            competing_ids = tuple(mid for mid in member_ids if mid != member_id and incompatible)
            if incompatible and record.acquisition_status in {
                AcquisitionStatus.STABLE_PROVISIONAL,
                AcquisitionStatus.WEAK_PROVISIONAL,
                AcquisitionStatus.CONTEXT_ONLY,
            }:
                record = replace(
                    record,
                    acquisition_status=AcquisitionStatus.COMPETING_PROVISIONAL,
                    stability_class=StabilityClass.COMPETING,
                    blocked_reason="cluster owner/assertion incompatibility preserved as competition",
                    downstream_permissions=_derive_downstream_permissions(
                        AcquisitionStatus.COMPETING_PROVISIONAL,
                        list(record.revision_conditions),
                    ),
                )
            updated[member_id] = replace(
                record,
                compatible_acquisition_ids=compatible_ids,
                competing_acquisition_ids=competing_ids,
            )
    return [updated[record.acquisition_id] for record in records]


def _build_cluster_links(
    records: list[ProvisionalAcquisitionRecord],
    cluster_members: dict[str, list[str]],
) -> list[AcquisitionClusterLink]:
    links: list[AcquisitionClusterLink] = []
    cluster_id_map: dict[str, str] = {}
    for record in records:
        cluster_id_map.setdefault(record.cluster_id, record.cluster_id)
    for idx, (_, members) in enumerate(cluster_members.items(), start=1):
        member_set = tuple(members)
        competing: set[str] = set()
        compatible: set[str] = set()
        for record in records:
            if record.acquisition_id in member_set:
                competing.update(record.competing_acquisition_ids)
                compatible.update(record.compatible_acquisition_ids)
        links.append(
            AcquisitionClusterLink(
                cluster_id=f"cluster-{idx}",
                member_acquisition_ids=member_set,
                compatible_member_ids=tuple(sorted(compatible)),
                competing_member_ids=tuple(sorted(competing)),
                confidence=max(0.1, min(0.9, round(0.68 - (0.06 * len(competing)), 4))),
                provenance="g05 cluster linkage from provisional acquisition compatibility/competition",
            )
        )
    return links


def _estimate_record_confidence(
    base: float,
    support_score: float,
    conflict_score: float,
    status: AcquisitionStatus,
) -> float:
    value = base + (support_score * 0.04) - (conflict_score * 0.05)
    floor = 0.08 if status is AcquisitionStatus.DISCARDED_AS_INCOHERENT else 0.22
    return max(floor, min(0.9, round(value, 4)))


def _cluster_basis(semantic_unit_id: str | None, proposition_id: str) -> str:
    if semantic_unit_id:
        return f"unit:{semantic_unit_id}"
    return f"prop:{proposition_id}"


def _estimate_result_confidence(bundle: SemanticAcquisitionBundle) -> float:
    base = 0.7
    base -= min(0.3, len(bundle.ambiguity_reasons) * 0.03)
    if bundle.low_coverage_mode:
        base -= min(0.28, len(bundle.low_coverage_reasons) * 0.05)
    if not bundle.acquisition_records:
        base -= 0.25
    return max(0.08, min(0.9, round(base, 4)))


def _abstain_result(
    *,
    perspective_bundle: PerspectiveChainBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> SemanticAcquisitionResult:
    bundle = SemanticAcquisitionBundle(
        source_perspective_chain_ref=perspective_bundle.source_applicability_ref,
        source_applicability_ref=perspective_bundle.source_applicability_ref,
        source_runtime_graph_ref=perspective_bundle.source_runtime_graph_ref,
        source_grounded_ref=perspective_bundle.source_grounded_ref,
        source_dictum_ref=perspective_bundle.source_dictum_ref,
        source_syntax_ref=perspective_bundle.source_syntax_ref,
        source_surface_ref=perspective_bundle.source_surface_ref,
        linked_proposition_ids=perspective_bundle.linked_proposition_ids,
        linked_semantic_unit_ids=perspective_bundle.linked_semantic_unit_ids,
        acquisition_records=(),
        cluster_links=(),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=("abstain",),
        no_final_semantic_closure=True,
        reason="g05 abstained due to insufficient g04 perspective basis",
    )
    gate = evaluate_semantic_acquisition_downstream_gate(bundle)
    telemetry = build_semantic_acquisition_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient g04 perspective chain -> g05 abstain",
    )
    return SemanticAcquisitionResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_semantic_closure=True,
    )
