from __future__ import annotations

from substrate.n03_autobiographical_relevance.models import (
    N03AutobiographicalRelevanceEntry,
    N03AutobiographicalTraceKind,
    N03CurrentTarget,
    N03GateDecision,
    N03InputBundle,
    N03LedgerEntry,
    N03LimitingReason,
    N03RelevanceKind,
    N03Result,
    N03ScopeMarker,
    N03StructuralDimension,
    N03Telemetry,
    N03TraceCandidate,
    N03TransferDecision,
    N03TransferScope,
)


def build_n03_autobiographical_relevance(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: N03InputBundle | None,
    relevance_enabled: bool = True,
) -> N03Result:
    if not relevance_enabled:
        return _minimal_result(
            bundle_id=f"n03:{tick_id}:bundle:none",
            reason="N03 gate disabled in test fixture",
            restrictions=("n03_disabled", "n03_no_safe_transfer"),
        )
    if not isinstance(input_bundle, N03InputBundle):
        return _minimal_result(
            bundle_id=f"n03:{tick_id}:bundle:none",
            reason="n03 requires typed target and autobiographical trace candidates",
            restrictions=("insufficient_n03_basis", "n03_no_safe_transfer"),
        )
    if not input_bundle.trace_candidates or not input_bundle.current_targets:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="n03 received incomplete typed basis and keeps no-safe-transfer state",
            restrictions=("insufficient_n03_basis", "n03_no_safe_transfer"),
        )

    entries: list[N03AutobiographicalRelevanceEntry] = []
    ledger: list[N03LedgerEntry] = []
    for target in input_bundle.current_targets:
        for trace in input_bundle.trace_candidates:
            entry = _evaluate_trace_target(
                tick_id=tick_id,
                tick_index=tick_index,
                trace=trace,
                target=target,
                source_lineage=input_bundle.source_lineage,
            )
            entries.append(entry)
            ledger.append(
                N03LedgerEntry(
                    ledger_entry_id=f"{entry.relevance_id}:ledger",
                    source_trace_id=entry.source_trace_id,
                    current_target_id=entry.current_target_id,
                    transfer_decision=entry.transfer_decision,
                    reason_codes=tuple(item.value for item in entry.limiting_reasons) or ("none",),
                    supported_dimensions=entry.supported_by_dimensions,
                    limiting_reasons=entry.limiting_reasons,
                    transfer_scope=entry.transfer_scope,
                )
            )

    conflicts = _detect_conflicts(entries)
    if conflicts:
        entries = [_mark_entry_conflicted(item) if item.relevance_id in conflicts else item for item in entries]

    relevant_trace_count = sum(
        1
        for item in entries
        if item.transfer_decision
        in {
            N03TransferDecision.USE_AS_CAUTION,
            N03TransferDecision.USE_AS_SUPPORTING_PATTERN,
            N03TransferDecision.USE_AS_COMMITMENT_ANCHOR,
            N03TransferDecision.USE_AS_REGULATORY_WARNING,
            N03TransferDecision.USE_AS_PLAN_CONSTRAINT,
            N03TransferDecision.USE_AS_RECOVERY_TEMPLATE,
        }
    )
    blocked_transfer_count = sum(
        1
        for item in entries
        if item.transfer_decision
        in {
            N03TransferDecision.DO_NOT_TRANSFER,
            N03TransferDecision.NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER,
            N03TransferDecision.CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE,
        }
    )
    provisional_transfer_count = sum(
        1 for item in entries if item.transfer_decision is N03TransferDecision.PROVISIONAL_TRANSFER_ONLY
    )
    conflict_count = sum(
        1 for item in entries if item.transfer_decision is N03TransferDecision.CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE
    )
    no_safe_transfer_count = sum(
        1 for item in entries if item.transfer_decision is N03TransferDecision.NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER
    )

    transfer_packet_ready = any(
        item.transfer_decision
        in {
            N03TransferDecision.USE_AS_CAUTION,
            N03TransferDecision.USE_AS_SUPPORTING_PATTERN,
            N03TransferDecision.USE_AS_COMMITMENT_ANCHOR,
            N03TransferDecision.USE_AS_REGULATORY_WARNING,
            N03TransferDecision.USE_AS_PLAN_CONSTRAINT,
            N03TransferDecision.USE_AS_RECOVERY_TEMPLATE,
            N03TransferDecision.PROVISIONAL_TRANSFER_ONLY,
        }
        and bool(item.anti_generalization_limits)
        for item in entries
    )
    consistency_ready = conflict_count == 0
    consumer_ready = bool(
        transfer_packet_ready
        and consistency_ready
        and no_safe_transfer_count == 0
    )

    restrictions: list[str] = []
    reason_codes: list[str] = []
    if no_safe_transfer_count > 0:
        restrictions.append("n03_no_safe_transfer")
        reason_codes.append("no_safe_transfer")
    if conflict_count > 0:
        restrictions.append("n03_conflict_review_required")
        reason_codes.append("conflicting_trace_set")
    if blocked_transfer_count > 0 and relevant_trace_count == 0:
        restrictions.append("n03_blocked_transfer_path")
        reason_codes.append("blocked_transfer_path")
    if not consumer_ready:
        restrictions.append("n03_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    telemetry = N03Telemetry(
        trace_candidate_count=len(input_bundle.trace_candidates),
        current_target_count=len(input_bundle.current_targets),
        relevance_entry_count=len(entries),
        relevant_trace_count=relevant_trace_count,
        blocked_transfer_count=blocked_transfer_count,
        conflict_count=conflict_count,
        provisional_transfer_count=provisional_transfer_count,
        no_safe_transfer_count=no_safe_transfer_count,
        consumer_ready=consumer_ready,
    )
    gate = N03GateDecision(
        consumer_ready=consumer_ready,
        transfer_packet_consumer_ready=transfer_packet_ready,
        consistency_consumer_ready=consistency_ready,
        relevant_trace_count=relevant_trace_count,
        blocked_transfer_count=blocked_transfer_count,
        conflict_count=conflict_count,
        provisional_transfer_count=provisional_transfer_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="n03 gate preserves bounded autobiographical transfer discipline",
    )
    return N03Result(
        bundle_id=input_bundle.bundle_id,
        relevance_entries=tuple(entries),
        ledger=tuple(ledger),
        telemetry=telemetry,
        gate=gate,
        scope_marker=N03ScopeMarker(
            scope="frontier_hosted_n03_autobiographical_relevance_slice",
            frontier_only=True,
            narrow_slice_only=True,
            autobiographical_relevance_not_retrieval=True,
            autobiographical_relevance_not_planner=True,
            autobiographical_relevance_not_memory_lifecycle=True,
            autobiographical_relevance_not_identity_generator=True,
            reason=(
                "n03 emits typed autobiographical relevance packets for current demands with bounded transfer limits "
                "and does not implement retrieval, planning, or memory lifecycle execution"
            ),
        ),
        reason="n03 produced typed autobiographical relevance packets",
    )


def _evaluate_trace_target(
    *,
    tick_id: str,
    tick_index: int,
    trace: N03TraceCandidate,
    target: N03CurrentTarget,
    source_lineage: tuple[str, ...],
) -> N03AutobiographicalRelevanceEntry:
    supported: list[N03StructuralDimension] = []
    limiting: list[N03LimitingReason] = []
    limits: list[str] = ["must_preserve_current_demand_scope", "must_not_generalize_single_episode"]

    commitment_match = bool(set(trace.commitment_refs) & set(target.active_commitment_refs))
    capability_match = bool(set(trace.capability_gap_refs) & set(target.active_capability_gap_refs))
    affordance_match = bool(set(trace.affordance_refs) & set(target.active_affordance_refs))
    tool_match = bool(set(trace.internal_tool_refs) & set(target.active_internal_tool_refs))
    self_binding_match = bool(set(trace.self_binding_refs) & set(target.active_self_binding_refs))
    identity_region_match = bool(set(trace.identity_region_refs) & set(target.active_identity_region_refs))
    semantic_overlap = bool(set(trace.semantic_topic_tags) & set(target.semantic_topic_tags))
    temporal_supported = trace.temporal_validity_status in {"valid", "current", "supported"}
    if commitment_match:
        supported.append(N03StructuralDimension.COMMITMENT_MATCH)
    if capability_match:
        supported.append(N03StructuralDimension.CAPABILITY_GAP_MATCH)
    if affordance_match:
        supported.append(N03StructuralDimension.AFFORDANCE_CONTOUR_MATCH)
    if tool_match:
        supported.append(N03StructuralDimension.INTERNAL_TOOL_MATCH)
    if self_binding_match:
        supported.append(N03StructuralDimension.SELF_BINDING_MATCH)
    if trace.attribution_profile == target.attribution_profile:
        supported.append(N03StructuralDimension.ATTRIBUTION_MATCH)
    pattern_signature_match = bool(
        trace.failure_or_recovery_signature
        and (
            target.current_evidence_signature == trace.failure_or_recovery_signature
            or target.current_evidence_signature == f"supports:{trace.failure_or_recovery_signature}"
            or target.current_evidence_signature == f"pattern:{trace.failure_or_recovery_signature}"
        )
    )
    if pattern_signature_match and trace.trace_kind in {
        N03AutobiographicalTraceKind.PRIOR_FAILURE,
        N03AutobiographicalTraceKind.REGULATORY_BREAKDOWN,
    }:
        supported.append(N03StructuralDimension.FAILURE_PATTERN_MATCH)
    if pattern_signature_match and trace.trace_kind in {
        N03AutobiographicalTraceKind.PRIOR_RECOVERY,
        N03AutobiographicalTraceKind.REGULATORY_STABILIZATION,
    }:
        supported.append(N03StructuralDimension.RECOVERY_PATTERN_MATCH)
    if identity_region_match and not {"drift_contested", "drift_fracture"} & set(target.active_drift_markers):
        supported.append(N03StructuralDimension.IDENTITY_DRIFT_COMPATIBLE)
    if temporal_supported:
        supported.append(N03StructuralDimension.TEMPORAL_VALIDITY_SUPPORTED)

    structural_count = len(
        [
            item
            for item in supported
            if item
            in {
                N03StructuralDimension.COMMITMENT_MATCH,
                N03StructuralDimension.CAPABILITY_GAP_MATCH,
                N03StructuralDimension.AFFORDANCE_CONTOUR_MATCH,
                N03StructuralDimension.INTERNAL_TOOL_MATCH,
                N03StructuralDimension.SELF_BINDING_MATCH,
                N03StructuralDimension.FAILURE_PATTERN_MATCH,
                N03StructuralDimension.RECOVERY_PATTERN_MATCH,
            }
        ]
    )

    if trace.trace_kind is N03AutobiographicalTraceKind.GENERIC_MEMORY_ONLY:
        limiting.append(N03LimitingReason.GENERIC_MEMORY_NOT_SELF_LINE)
    if semantic_overlap and structural_count == 0:
        supported.append(N03StructuralDimension.SEMANTIC_SIMILARITY_ONLY)
        limiting.append(N03LimitingReason.SEMANTIC_SIMILARITY_ONLY)
    if trace.recency_hint >= 0.8 and structural_count == 0:
        limiting.append(N03LimitingReason.RECENCY_ONLY)
    if trace.vividness_hint >= 0.8 and structural_count == 0:
        limiting.append(N03LimitingReason.VIVIDNESS_NOT_SUFFICIENT)
    if trace.recurrence_count <= 1 and structural_count > 0:
        limiting.append(N03LimitingReason.SINGLE_EPISODE_OVERGENERALIZATION_RISK)
        limits.append("single_episode_scope_cap")
    if not temporal_supported:
        limiting.append(N03LimitingReason.TRACE_OUTDATED)
        limits.append("outdated_trace_no_direct_transfer")
    if {"drift_contested", "drift_fracture"} & set(target.active_drift_markers):
        limiting.append(N03LimitingReason.IDENTITY_DRIFT_REDUCES_TRANSFER)
        limits.append("identity_drift_requires_provisional_or_blocked_transfer")
    if "capability_changed" in target.active_drift_markers and capability_match:
        limiting.append(N03LimitingReason.CAPABILITY_BOUNDARY_CHANGED)
        limits.append("capability_recheck_required")
    if "affordance_changed" in target.active_drift_markers and affordance_match:
        limiting.append(N03LimitingReason.AFFORDANCE_SPACE_CHANGED)
        limits.append("affordance_recheck_required")
    if "self_binding_shift" in target.active_drift_markers and not self_binding_match:
        limiting.append(N03LimitingReason.SELF_BINDING_MISMATCH)
    if trace.attribution_profile == "mixed":
        limiting.append(N03LimitingReason.ATTRIBUTION_TOO_MIXED)
    if (
        target.current_evidence_signature
        and trace.failure_or_recovery_signature
        and target.current_evidence_signature == f"contradicts:{trace.failure_or_recovery_signature}"
    ):
        limiting.append(N03LimitingReason.CURRENT_EVIDENCE_CONTRADICTS_PAST_TRACE)
        limits.append("current_evidence_override")

    relevance_kind = N03RelevanceKind.NO_AUTOBIOGRAPHICAL_RELEVANCE
    transfer = N03TransferDecision.NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER
    scope = N03TransferScope.BROAD_TRANSFER_BLOCKED
    strength = 0.0

    has_blocking = any(
        item
        in {
            N03LimitingReason.GENERIC_MEMORY_NOT_SELF_LINE,
            N03LimitingReason.SEMANTIC_SIMILARITY_ONLY,
            N03LimitingReason.RECENCY_ONLY,
            N03LimitingReason.CURRENT_EVIDENCE_CONTRADICTS_PAST_TRACE,
            N03LimitingReason.TRACE_OUTDATED,
        }
        for item in limiting
    )
    if has_blocking or structural_count == 0:
        transfer = (
            N03TransferDecision.DO_NOT_TRANSFER
            if limiting
            else N03TransferDecision.NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER
        )
        relevance_kind = N03RelevanceKind.NO_AUTOBIOGRAPHICAL_RELEVANCE
        scope = N03TransferScope.CURRENT_CONTEXT_ONLY
    else:
        if trace.trace_kind in {
            N03AutobiographicalTraceKind.PRIOR_FAILURE,
            N03AutobiographicalTraceKind.REGULATORY_BREAKDOWN,
        }:
            relevance_kind = N03RelevanceKind.REGULATORY_WARNING
            transfer = N03TransferDecision.USE_AS_REGULATORY_WARNING
            scope = N03TransferScope.CURRENT_DEMAND_ONLY
        elif trace.trace_kind in {
            N03AutobiographicalTraceKind.PRIOR_RECOVERY,
            N03AutobiographicalTraceKind.REGULATORY_STABILIZATION,
        }:
            relevance_kind = N03RelevanceKind.RECOVERY_PATTERN_RELEVANCE
            transfer = N03TransferDecision.USE_AS_RECOVERY_TEMPLATE
            scope = N03TransferScope.SAME_RECOVERY_PATTERN_ONLY
        elif commitment_match and target.target_kind is not None:
            relevance_kind = N03RelevanceKind.COMMITMENT_PRESERVING_RELEVANCE
            transfer = N03TransferDecision.USE_AS_COMMITMENT_ANCHOR
            scope = N03TransferScope.SAME_COMMITMENT_REGION_ONLY
        elif capability_match or affordance_match or tool_match:
            relevance_kind = N03RelevanceKind.CAPABILITY_BOUNDARY_RELEVANCE
            transfer = N03TransferDecision.USE_AS_PLAN_CONSTRAINT
            scope = N03TransferScope.SAME_CAPABILITY_BOUNDARY_ONLY
        else:
            relevance_kind = N03RelevanceKind.CAUTIONARY_RELEVANCE
            transfer = N03TransferDecision.USE_AS_CAUTION
            scope = N03TransferScope.CURRENT_CONTEXT_ONLY

        if trace.recurrence_count <= 1 or N03LimitingReason.ATTRIBUTION_TOO_MIXED in limiting:
            transfer = N03TransferDecision.PROVISIONAL_TRANSFER_ONLY
            scope = N03TransferScope.CURRENT_CONTEXT_ONLY
        if N03LimitingReason.IDENTITY_DRIFT_REDUCES_TRANSFER in limiting:
            transfer = N03TransferDecision.PROVISIONAL_TRANSFER_ONLY
            scope = N03TransferScope.CURRENT_CONTEXT_ONLY
        if N03LimitingReason.CAPABILITY_BOUNDARY_CHANGED in limiting or N03LimitingReason.AFFORDANCE_SPACE_CHANGED in limiting:
            transfer = N03TransferDecision.USE_AS_CAUTION
            relevance_kind = N03RelevanceKind.CAUTIONARY_RELEVANCE
            scope = N03TransferScope.CURRENT_DEMAND_ONLY
        strength = min(1.0, 0.2 + 0.12 * structural_count + 0.08 * min(trace.recurrence_count, 4))
        if transfer is N03TransferDecision.PROVISIONAL_TRANSFER_ONLY:
            strength = min(strength, 0.58)

    confidence = max(0.0, min(1.0, (trace.confidence * 0.55) + (target.regulation_or_planning_pressure * 0.35)))
    if N03LimitingReason.TRACE_OUTDATED in limiting:
        confidence = min(confidence, 0.45)
    if N03LimitingReason.CURRENT_EVIDENCE_CONTRADICTS_PAST_TRACE in limiting:
        confidence = min(confidence, 0.3)

    return N03AutobiographicalRelevanceEntry(
        relevance_id=f"n03:{tick_id}:{tick_index}:{target.current_target_id}:{trace.source_trace_id}",
        source_trace_id=trace.source_trace_id,
        current_target_id=target.current_target_id,
        relevance_kind=relevance_kind,
        relevance_strength=round(max(0.0, min(1.0, strength)), 4),
        transfer_decision=transfer,
        transfer_scope=scope,
        supported_by_dimensions=tuple(dict.fromkeys(supported)),
        anti_generalization_limits=tuple(dict.fromkeys(limits)),
        limiting_reasons=tuple(dict.fromkeys(limiting)),
        drift_adjustment=(
            "reduced_by_identity_drift" if N03LimitingReason.IDENTITY_DRIFT_REDUCES_TRANSFER in limiting else "none"
        ),
        confidence=round(confidence, 4),
        provenance=tuple(dict.fromkeys((*source_lineage, *trace.provenance, *target.provenance))),
    )


def _detect_conflicts(entries: list[N03AutobiographicalRelevanceEntry]) -> set[str]:
    by_target: dict[str, list[N03AutobiographicalRelevanceEntry]] = {}
    for item in entries:
        by_target.setdefault(item.current_target_id, []).append(item)
    conflicted: set[str] = set()
    incompatible_pairs: tuple[frozenset[N03TransferDecision], ...] = (
        frozenset(
            {
                N03TransferDecision.USE_AS_PLAN_CONSTRAINT,
                N03TransferDecision.USE_AS_COMMITMENT_ANCHOR,
            }
        ),
    )
    for items in by_target.values():
        decisions = {item.transfer_decision for item in items}
        has_warning = any(
            item.transfer_decision in {N03TransferDecision.USE_AS_REGULATORY_WARNING, N03TransferDecision.USE_AS_CAUTION}
            for item in items
        )
        has_recovery = any(item.transfer_decision is N03TransferDecision.USE_AS_RECOVERY_TEMPLATE for item in items)
        has_incompatible_pair = any(pair.issubset(decisions) for pair in incompatible_pairs)
        if (has_warning and has_recovery) or has_incompatible_pair:
            conflicted.update(item.relevance_id for item in items)
    return conflicted


def _mark_entry_conflicted(entry: N03AutobiographicalRelevanceEntry) -> N03AutobiographicalRelevanceEntry:
    return N03AutobiographicalRelevanceEntry(
        relevance_id=entry.relevance_id,
        source_trace_id=entry.source_trace_id,
        current_target_id=entry.current_target_id,
        relevance_kind=entry.relevance_kind,
        relevance_strength=min(entry.relevance_strength, 0.45),
        transfer_decision=N03TransferDecision.CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE,
        transfer_scope=N03TransferScope.CURRENT_DEMAND_ONLY,
        supported_by_dimensions=entry.supported_by_dimensions,
        anti_generalization_limits=tuple(dict.fromkeys((*entry.anti_generalization_limits, "conflict_review_required"))),
        limiting_reasons=tuple(dict.fromkeys((*entry.limiting_reasons, N03LimitingReason.CONFLICTING_TRACE_SET))),
        drift_adjustment=entry.drift_adjustment,
        confidence=min(entry.confidence, 0.5),
        provenance=entry.provenance,
    )


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> N03Result:
    telemetry = N03Telemetry(
        trace_candidate_count=0,
        current_target_count=0,
        relevance_entry_count=0,
        relevant_trace_count=0,
        blocked_transfer_count=0,
        conflict_count=0,
        provisional_transfer_count=0,
        no_safe_transfer_count=1,
        consumer_ready=False,
    )
    gate = N03GateDecision(
        consumer_ready=False,
        transfer_packet_consumer_ready=False,
        consistency_consumer_ready=False,
        relevant_trace_count=0,
        blocked_transfer_count=0,
        conflict_count=0,
        provisional_transfer_count=0,
        required_restrictions=restrictions,
        reason_codes=("no_safe_autobiographical_transfer",),
        reason=reason,
    )
    return N03Result(
        bundle_id=bundle_id,
        relevance_entries=(),
        ledger=(),
        telemetry=telemetry,
        gate=gate,
        scope_marker=N03ScopeMarker(
            scope="frontier_hosted_n03_autobiographical_relevance_slice",
            frontier_only=True,
            narrow_slice_only=True,
            autobiographical_relevance_not_retrieval=True,
            autobiographical_relevance_not_planner=True,
            autobiographical_relevance_not_memory_lifecycle=True,
            autobiographical_relevance_not_identity_generator=True,
            reason=reason,
        ),
        reason=reason,
    )
