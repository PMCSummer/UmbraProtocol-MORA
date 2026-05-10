from __future__ import annotations

from collections import defaultdict

from substrate.w02_regularity_extraction.models import (
    W02ContradictionKind,
    W02ContradictionLedgerEntry,
    W02DisambiguationSlot,
    W02DowngradeOrRevalidationRecord,
    W02DownstreamRegularityPermissionPacket,
    W02GateDecision,
    W02InputBundle,
    W02InstanceKindRoleDisambiguationRecord,
    W02LineageHypothesis,
    W02LineageHypothesisKind,
    W02LineageHypothesisSet,
    W02ObjectMaturityLevel,
    W02ObjectRegularityRecord,
    W02PresenceMode,
    W02PromotionDecisionRecord,
    W02PromotionStatus,
    W02RegularityCandidateType,
    W02ResultBundle,
    W02ScopeMarker,
    W02Telemetry,
    W02TraceRef,
)


def build_w02_regularity_extraction(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: W02InputBundle | None,
    enforcement_enabled: bool = True,
) -> W02ResultBundle:
    if not enforcement_enabled:
        return _minimal_result(
            bundle_id=f"w02:{tick_id}:bundle:none",
            reason="W02 gate disabled in test fixture",
            restrictions=("w02_disabled", "w02_no_clean_regularity_claim"),
        )

    if not isinstance(input_bundle, W02InputBundle):
        return _minimal_result(
            bundle_id=f"w02:{tick_id}:bundle:none",
            reason=(
                "w02 requires typed w01-shaped admitted traces and does not synthesize regularities "
                "from language/history priors"
            ),
            restrictions=("insufficient_w02_basis", "w02_no_clean_regularity_claim"),
        )

    if not input_bundle.traces:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="w02 received no traces and keeps no-clean-regularity state",
            restrictions=("w02_no_trace", "w02_no_clean_regularity_claim"),
        )

    grouped: dict[tuple[str, W02RegularityCandidateType], list[W02TraceRef]] = defaultdict(list)
    for trace in input_bundle.traces:
        grouped[(trace.entity_id, trace.candidate_type)].append(trace)

    regularity_records: list[W02ObjectRegularityRecord] = []
    disambiguation_records: list[W02InstanceKindRoleDisambiguationRecord] = []
    promotion_decisions: list[W02PromotionDecisionRecord] = []
    contradiction_entries: list[W02ContradictionLedgerEntry] = []
    lineage_sets: list[W02LineageHypothesisSet] = []
    downgrade_records: list[W02DowngradeOrRevalidationRecord] = []
    permissions: list[W02DownstreamRegularityPermissionPacket] = []

    for (entity_id, candidate_type), traces in grouped.items():
        traces_sorted = sorted(traces, key=lambda item: item.sequence_index)
        (
            record,
            disambiguation,
            promotion,
            group_contradictions,
            lineage,
            downgrade,
            permission,
        ) = _evaluate_trace_group(
            tick_id=tick_id,
            tick_index=tick_index,
            entity_id=entity_id,
            candidate_type=candidate_type,
            traces=traces_sorted,
            source_lineage=input_bundle.source_lineage,
        )
        regularity_records.append(record)
        disambiguation_records.append(disambiguation)
        promotion_decisions.append(promotion)
        contradiction_entries.extend(group_contradictions)
        lineage_sets.append(lineage)
        if downgrade is not None:
            downgrade_records.append(downgrade)
        permissions.append(permission)

    promoted_count = sum(
        1 for item in regularity_records if item.promotion_status is W02PromotionStatus.PROMOTED
    )
    blocked_count = sum(
        1
        for item in regularity_records
        if item.promotion_status in {W02PromotionStatus.BLOCKED, W02PromotionStatus.NO_CLEAN_REGULARITY_CLAIM}
    )
    contested_count = sum(
        1 for item in regularity_records if item.promotion_status is W02PromotionStatus.CONTESTED
    )
    downgraded_count = sum(
        1 for item in regularity_records if item.promotion_status is W02PromotionStatus.DOWNGRADED
    )
    lineage_ambiguity_count = sum(
        1
        for item in lineage_sets
        if any(h.unresolved for h in item.hypotheses)
    )
    must_abstain_count = sum(1 for item in permissions if item.must_abstain)
    promoted_records = tuple(
        item for item in regularity_records if item.promotion_status is W02PromotionStatus.PROMOTED
    )
    clean_promoted_records = tuple(
        item
        for item in promoted_records
        if "presence_mode_not_clean_present" not in set(item.uncertainty_markers)
    )
    no_clean_regularities = bool(len(clean_promoted_records) == 0)
    contradiction_count = len(contradiction_entries)

    consumer_ready = bool(
        len(clean_promoted_records) > 0
        and must_abstain_count == 0
        and contradiction_count == 0
    )

    restrictions: list[str] = []
    reason_codes: list[str] = []
    if no_clean_regularities:
        restrictions.append("w02_no_clean_regularity_claim")
        reason_codes.append("no_clean_regularity_claim")
    if contradiction_count > 0:
        restrictions.append("w02_contradiction_review_required")
        reason_codes.append("contradiction_present")
    if must_abstain_count > 0:
        restrictions.append("w02_must_abstain")
        reason_codes.append("must_abstain")
    if not consumer_ready:
        restrictions.append("w02_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    telemetry = W02Telemetry(
        trace_selection_count=len(input_bundle.traces),
        candidate_count=len(grouped),
        promoted_count=promoted_count,
        blocked_count=blocked_count,
        contested_count=contested_count,
        downgraded_count=downgraded_count,
        contradiction_count=contradiction_count,
        lineage_ambiguity_count=lineage_ambiguity_count,
        consumer_ready=consumer_ready,
        no_clean_regularities=no_clean_regularities,
        must_abstain_count=must_abstain_count,
    )

    gate = W02GateDecision(
        consumer_ready=consumer_ready,
        clean_regularity_claim_allowed=False,
        accepted_count=promoted_count,
        blocked_count=blocked_count,
        contested_count=contested_count,
        downgraded_count=downgraded_count,
        contradiction_count=contradiction_count,
        lineage_ambiguity_count=lineage_ambiguity_count,
        must_abstain_count=must_abstain_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="w02 keeps regularity claims staged, contradiction-aware, and uncertainty-preserving",
    )

    return W02ResultBundle(
        bundle_id=input_bundle.bundle_id,
        regularity_records=tuple(regularity_records),
        disambiguation_records=tuple(disambiguation_records),
        promotion_decisions=tuple(promotion_decisions),
        contradiction_ledger=tuple(contradiction_entries),
        lineage_hypotheses=tuple(lineage_sets),
        downgrade_records=tuple(downgrade_records),
        downstream_permission_packets=tuple(permissions),
        telemetry=telemetry,
        scope_marker=W02ScopeMarker(
            scope="frontier_hosted_w02_regularity_extraction_slice",
            staged_regularity_only=True,
            no_mature_object_identity_claim=True,
            no_object_permanence_claim=True,
            no_scene_graph_truth_claim=True,
            no_policy_selection_claim=True,
            reason=(
                "w02 stages repeated lived-trace regularities through maturity gates and never emits mature "
                "object truth or stable identity claims"
            ),
        ),
        gate=gate,
        reason="w02 produced staged regularity records with bounded downstream permissions",
    )


def _evaluate_trace_group(
    *,
    tick_id: str,
    tick_index: int,
    entity_id: str,
    candidate_type: W02RegularityCandidateType,
    traces: list[W02TraceRef],
    source_lineage: tuple[str, ...],
) -> tuple[
    W02ObjectRegularityRecord,
    W02InstanceKindRoleDisambiguationRecord,
    W02PromotionDecisionRecord,
    list[W02ContradictionLedgerEntry],
    W02LineageHypothesisSet,
    W02DowngradeOrRevalidationRecord | None,
    W02DownstreamRegularityPermissionPacket,
]:
    evidence_count = len(traces)
    source_authority_set = tuple(
        dict.fromkeys(item.source_authority for item in traces if item.source_authority)
    )
    sequence_min = min(item.sequence_index for item in traces)
    sequence_max = max(item.sequence_index for item in traces)
    temporal_spread = max(0, sequence_max - sequence_min)

    present_like = sum(
        1 for item in traces if item.presence_mode is W02PresenceMode.PRESENT
    )
    partial_or_scaffold = sum(
        1
        for item in traces
        if item.presence_mode in {W02PresenceMode.PARTIAL, W02PresenceMode.SCAFFOLD_ONLY}
    )
    absent_or_negative = sum(
        1
        for item in traces
        if item.presence_mode in {W02PresenceMode.ABSENT, W02PresenceMode.CONTRADICTORY, W02PresenceMode.REVOKED}
    )

    duplicate_or_artifact_only = all(
        item.is_duplicate_packet or item.provider_bias_marker or item.text_artifact_marker
        for item in traces
    )
    non_duplicate_repetition = sum(
        1
        for item in traces
        if not item.is_duplicate_packet and not item.provider_bias_marker and not item.text_artifact_marker
    )

    action_effect_linked = sum(1 for item in traces if item.action_ref and item.effect_ref)

    contradictions: list[W02ContradictionLedgerEntry] = []
    uncertainties: list[str] = []
    failed_criteria: list[str] = []
    passed_criteria: list[str] = []
    reason_codes: list[str] = []

    if any(item.revoked for item in traces):
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.REVOKED_TRACE,
                affected=W02ObjectMaturityLevel.DOWNGRADED,
                severity="high",
                downgrade_action="downgrade_to_trace_token",
                revalidation_requirement="new_non_revoked_authority_trace_required",
            )
        )
        uncertainties.append("revoked_trace")

    has_present = any(item.presence_mode is W02PresenceMode.PRESENT for item in traces)
    has_negative = any(
        item.presence_mode in {W02PresenceMode.ABSENT, W02PresenceMode.CONTRADICTORY, W02PresenceMode.REVOKED}
        for item in traces
    )
    if has_present and has_negative:
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.PRESENCE_MODE_CONFLICT,
                affected=W02ObjectMaturityLevel.CONTESTED,
                severity="high",
                downgrade_action="hold_contested",
                revalidation_requirement="presence_conflict_resolution_required",
            )
        )
        uncertainties.append("presence_mode_conflict")

    if len({item.structural_signature for item in traces if item.structural_signature}) > 1:
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.STRUCTURAL_CONFLICT,
                affected=W02ObjectMaturityLevel.CONTESTED,
                severity="medium",
                downgrade_action="hold_contested",
                revalidation_requirement="structural_signature_disambiguation_required",
            )
        )
        uncertainties.append("structural_conflict")

    if candidate_type is W02RegularityCandidateType.AFFORDANCE and action_effect_linked == 0:
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.AFFORDANCE_CONFLICT,
                affected=W02ObjectMaturityLevel.AFFORDANCE_CANDIDATE,
                severity="medium",
                downgrade_action="block_affordance_candidate",
                revalidation_requirement="action_effect_lineage_required",
            )
        )
        uncertainties.append("affordance_linkage_missing")

    if any(item.source_authority in {"", "unknown_source", "revoked_source"} for item in traces):
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.SOURCE_AUTHORITY_CONFLICT,
                affected=W02ObjectMaturityLevel.BLOCKED,
                severity="high",
                downgrade_action="block_promotion",
                revalidation_requirement="trusted_source_authority_required",
            )
        )
        uncertainties.append("source_authority_conflict")

    marker_tokens = {token for item in traces for token in item.contradiction_markers}
    if "replacement" in marker_tokens:
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.REPLACEMENT_AMBIGUITY,
                affected=W02ObjectMaturityLevel.CONTESTED,
                severity="high",
                downgrade_action="block_same_instance_claim",
                revalidation_requirement="lineage_disambiguation_required",
            )
        )
        uncertainties.append("replacement_ambiguity")
    if "identity_swap" in marker_tokens:
        contradictions.append(
            _contradiction_entry(
                tick_id=tick_id,
                tick_index=tick_index,
                entity_id=entity_id,
                traces=traces,
                conflict_type=W02ContradictionKind.IDENTITY_SWAP,
                affected=W02ObjectMaturityLevel.CONTESTED,
                severity="high",
                downgrade_action="block_same_instance_claim",
                revalidation_requirement="lineage_disambiguation_required",
            )
        )
        uncertainties.append("identity_swap")

    # Gate evaluation for maturity ladder.
    prior_level = W02ObjectMaturityLevel.TRACE_TOKEN
    new_level = W02ObjectMaturityLevel.TRACE_TOKEN
    promotion_status = W02PromotionStatus.HELD

    if evidence_count <= 1:
        failed_criteria.append("min_repetition>=2")
        reason_codes.append("single_trace_only")
    else:
        passed_criteria.append("min_repetition>=2")

    if duplicate_or_artifact_only:
        failed_criteria.append("non_duplicate_lived_recurrence")
        reason_codes.append("duplicate_or_artifact_only")
    else:
        passed_criteria.append("non_duplicate_lived_recurrence")

    if temporal_spread >= 1:
        passed_criteria.append("temporal_spread>=1")
    else:
        failed_criteria.append("temporal_spread>=1")

    if len(source_authority_set) > 0:
        passed_criteria.append("source_authority_present")
    else:
        failed_criteria.append("source_authority_present")

    if contradictions:
        failed_criteria.append("contradiction_free")
    else:
        passed_criteria.append("contradiction_free")

    if not contradictions and evidence_count >= 2 and non_duplicate_repetition >= 2 and temporal_spread >= 1:
        new_level = W02ObjectMaturityLevel.RECURRENT_SCAFFOLD
        promotion_status = W02PromotionStatus.PROMOTED
        reason_codes.append("recurrent_scaffold_promoted")
    else:
        promotion_status = W02PromotionStatus.HELD

    if candidate_type is W02RegularityCandidateType.INSTANCE and promotion_status is W02PromotionStatus.PROMOTED:
        if (
            evidence_count >= 3
            and temporal_spread >= 2
            and len(source_authority_set) >= 2
            and present_like >= 2
            and absent_or_negative == 0
        ):
            new_level = W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE
            reason_codes.append("persistent_instance_candidate_promoted")
            if len({item.structural_signature for item in traces if item.structural_signature}) == 1:
                new_level = W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS
                reason_codes.append("persistent_instance_hypothesis_promoted")
        else:
            failed_criteria.append("persistent_instance_gate")

    if candidate_type is W02RegularityCandidateType.KIND and promotion_status is W02PromotionStatus.PROMOTED:
        new_level = W02ObjectMaturityLevel.KIND_CANDIDATE
        reason_codes.append("kind_candidate_promoted")

    if candidate_type is W02RegularityCandidateType.STRUCTURAL_SIGNATURE and promotion_status is W02PromotionStatus.PROMOTED:
        new_level = W02ObjectMaturityLevel.STRUCTURAL_SIGNATURE_CANDIDATE
        reason_codes.append("structural_signature_candidate_promoted")

    if candidate_type is W02RegularityCandidateType.SCENE_ROLE and promotion_status is W02PromotionStatus.PROMOTED:
        new_level = W02ObjectMaturityLevel.SCENE_ROLE_CANDIDATE
        reason_codes.append("scene_role_candidate_promoted")

    if candidate_type is W02RegularityCandidateType.AFFORDANCE and promotion_status is W02PromotionStatus.PROMOTED:
        if action_effect_linked > 0:
            new_level = W02ObjectMaturityLevel.AFFORDANCE_CANDIDATE
            reason_codes.append("affordance_candidate_promoted")
        else:
            promotion_status = W02PromotionStatus.BLOCKED
            new_level = W02ObjectMaturityLevel.BLOCKED
            failed_criteria.append("action_effect_linkage_required")
            reason_codes.append("affordance_requires_action_effect_linkage")

    if contradictions:
        if any(item.conflict_type is W02ContradictionKind.REVOKED_TRACE for item in contradictions):
            promotion_status = W02PromotionStatus.DOWNGRADED
            new_level = W02ObjectMaturityLevel.DOWNGRADED
            reason_codes.append("downgraded_by_revocation_or_negative_evidence")
        else:
            promotion_status = W02PromotionStatus.CONTESTED
            new_level = W02ObjectMaturityLevel.CONTESTED
            reason_codes.append("contested_by_contradiction")

    if absent_or_negative > 0 and new_level in {
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
    }:
        promotion_status = W02PromotionStatus.DOWNGRADED
        new_level = W02ObjectMaturityLevel.DOWNGRADED
        reason_codes.append("negative_presence_downgrade")
        failed_criteria.append("negative_presence_blocks_persistent_instance")

    if partial_or_scaffold > 0 and new_level in {
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
    }:
        promotion_status = W02PromotionStatus.HELD
        new_level = W02ObjectMaturityLevel.RECURRENT_SCAFFOLD
        reason_codes.append("scaffold_only_caps_maturity")

    if any(
        item.presence_mode
        in {
            W02PresenceMode.ABSENT,
            W02PresenceMode.SCAFFOLD_ONLY,
            W02PresenceMode.PARTIAL,
            W02PresenceMode.CONTESTED,
        }
        for item in traces
    ):
        uncertainties.append("presence_mode_not_clean_present")

    if promotion_status is W02PromotionStatus.HELD and new_level is W02ObjectMaturityLevel.TRACE_TOKEN:
        reason_codes.append("held_at_trace_token")

    if promotion_status in {W02PromotionStatus.BLOCKED, W02PromotionStatus.CONTESTED, W02PromotionStatus.DOWNGRADED}:
        if "must_abstain" not in reason_codes:
            reason_codes.append("must_abstain")

    confidence_band = _confidence_band(traces)
    record = W02ObjectRegularityRecord(
        regularity_id=f"w02:{tick_id}:{tick_index}:{entity_id}:{candidate_type.value}",
        source_trace_refs=tuple(item.trace_id for item in traces),
        maturity_level=new_level,
        candidate_type=candidate_type,
        source_authority_set=source_authority_set,
        temporal_span=(sequence_min, sequence_max),
        evidence_count=evidence_count,
        confidence_band=confidence_band,
        uncertainty_markers=tuple(dict.fromkeys(uncertainties)),
        promotion_status=promotion_status,
        provenance=tuple(dict.fromkeys((*source_lineage, *(p for item in traces for p in item.provenance_ref)))),
    )

    disambiguation = W02InstanceKindRoleDisambiguationRecord(
        instance_id_candidate=W02DisambiguationSlot(
            value=f"instance:{entity_id}" if candidate_type is W02RegularityCandidateType.INSTANCE else None,
            confidence_band=confidence_band,
            contradiction_status="contested" if promotion_status is W02PromotionStatus.CONTESTED else "clean",
            provenance=record.provenance,
        ),
        kind_id_candidate=W02DisambiguationSlot(
            value=next((item.kind_label for item in traces if item.kind_label), None),
            confidence_band=_slot_confidence_from_labels(traces, "kind"),
            contradiction_status="contested" if len({item.kind_label for item in traces if item.kind_label}) > 1 else "clean",
            provenance=record.provenance,
        ),
        role_id_candidate=W02DisambiguationSlot(
            value=next((item.role_label for item in traces if item.role_label), None),
            confidence_band=_slot_confidence_from_labels(traces, "role"),
            contradiction_status="contested" if len({item.role_label for item in traces if item.role_label}) > 1 else "clean",
            provenance=record.provenance,
        ),
        structural_signature_id=W02DisambiguationSlot(
            value=next((item.structural_signature for item in traces if item.structural_signature), None),
            confidence_band=_slot_confidence_from_labels(traces, "structure"),
            contradiction_status="contested" if len({item.structural_signature for item in traces if item.structural_signature}) > 1 else "clean",
            provenance=record.provenance,
        ),
        affordance_pattern_id=W02DisambiguationSlot(
            value=f"affordance:{entity_id}" if candidate_type is W02RegularityCandidateType.AFFORDANCE else None,
            confidence_band="medium" if action_effect_linked > 0 else "low",
            contradiction_status="contested" if action_effect_linked == 0 and candidate_type is W02RegularityCandidateType.AFFORDANCE else "clean",
            provenance=record.provenance,
        ),
    )

    lineage = _lineage_hypotheses(entity_id=entity_id, traces=traces, contradictions=contradictions)

    promotion = W02PromotionDecisionRecord(
        attempted_transition=f"{prior_level.value}->{new_level.value}",
        prior_level=prior_level,
        new_level=new_level,
        gate_results=tuple(dict.fromkeys((*passed_criteria, *failed_criteria))),
        failed_criteria=tuple(dict.fromkeys(failed_criteria)),
        passed_criteria=tuple(dict.fromkeys(passed_criteria)),
        decision_reason_codes=tuple(dict.fromkeys(reason_codes)),
        consumer_visible_claim_boundary=(
            "stable_identity_claim_forbidden_in_w02" if new_level is not W02ObjectMaturityLevel.BLOCKED else "must_abstain"
        ),
    )

    downgrade = None
    if promotion_status in {W02PromotionStatus.DOWNGRADED, W02PromotionStatus.REVALIDATION_REQUIRED}:
        trigger_ref = traces[-1].trace_id
        downgrade = W02DowngradeOrRevalidationRecord(
            trigger_trace_ref=trigger_ref,
            violated_assumption="contradiction_or_revocation_detected",
            downgraded_from=W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
            downgraded_to=new_level,
            blocked_downstream_permissions=(
                "may_use_as_instance_hypothesis",
                "may_claim_stable_identity",
            ),
            required_future_evidence=(
                "non_conflicting_trace",
                "trusted_source_authority",
                "temporal_spread_revalidation",
            ),
        )

    permission = _permission_packet(record=record, contradictions=contradictions, reason_codes=promotion.decision_reason_codes)

    return (
        record,
        disambiguation,
        promotion,
        contradictions,
        lineage,
        downgrade,
        permission,
    )


def _permission_packet(
    *,
    record: W02ObjectRegularityRecord,
    contradictions: list[W02ContradictionLedgerEntry],
    reason_codes: tuple[str, ...],
) -> W02DownstreamRegularityPermissionPacket:
    maturity = record.maturity_level
    candidate = record.candidate_type
    has_conflict = bool(contradictions)
    must_abstain = bool(
        has_conflict
        or record.promotion_status in {
            W02PromotionStatus.BLOCKED,
            W02PromotionStatus.CONTESTED,
            W02PromotionStatus.DOWNGRADED,
            W02PromotionStatus.NO_CLEAN_REGULARITY_CLAIM,
        }
    )
    may_use_as_scaffold = maturity in {
        W02ObjectMaturityLevel.RECURRENT_SCAFFOLD,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
        W02ObjectMaturityLevel.KIND_CANDIDATE,
        W02ObjectMaturityLevel.STRUCTURAL_SIGNATURE_CANDIDATE,
        W02ObjectMaturityLevel.AFFORDANCE_CANDIDATE,
        W02ObjectMaturityLevel.SCENE_ROLE_CANDIDATE,
    } and not must_abstain
    may_use_as_instance_hypothesis = maturity in {
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_CANDIDATE,
        W02ObjectMaturityLevel.PERSISTENT_INSTANCE_HYPOTHESIS,
    } and not must_abstain
    may_use_as_kind_hint = candidate is W02RegularityCandidateType.KIND and not must_abstain
    may_use_as_affordance_hint = candidate is W02RegularityCandidateType.AFFORDANCE and not must_abstain
    may_use_as_scene_role_hint = candidate is W02RegularityCandidateType.SCENE_ROLE and not must_abstain

    reasons = list(reason_codes)
    if must_abstain:
        reasons.append("must_abstain")
    if has_conflict:
        reasons.append("conflict_review_required")
    reasons.append("stable_identity_claim_forbidden")

    return W02DownstreamRegularityPermissionPacket(
        regularity_id=record.regularity_id,
        may_use_as_scaffold=may_use_as_scaffold,
        may_use_as_instance_hypothesis=may_use_as_instance_hypothesis,
        may_use_as_kind_hint=may_use_as_kind_hint,
        may_use_as_affordance_hint=may_use_as_affordance_hint,
        may_use_as_scene_role_hint=may_use_as_scene_role_hint,
        may_claim_stable_identity=False,
        must_preserve_uncertainty=must_abstain or bool(record.uncertainty_markers),
        must_abstain=must_abstain,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def _lineage_hypotheses(
    *,
    entity_id: str,
    traces: list[W02TraceRef],
    contradictions: list[W02ContradictionLedgerEntry],
) -> W02LineageHypothesisSet:
    markers = {marker for item in traces for marker in item.contradiction_markers}
    hypotheses: list[W02LineageHypothesis] = []

    if any(item.revoked for item in traces):
        hypotheses.append(
            W02LineageHypothesis(
                lineage_kind=W02LineageHypothesisKind.REVOKED_LINEAGE,
                evidence_refs=tuple(item.trace_id for item in traces if item.revoked),
                unresolved=True,
            )
        )

    if "replacement" in markers:
        hypotheses.append(
            W02LineageHypothesis(
                lineage_kind=W02LineageHypothesisKind.REPLACEMENT,
                evidence_refs=tuple(item.trace_id for item in traces),
                unresolved=True,
            )
        )

    if any(item.is_duplicate_packet for item in traces) or "duplicate" in markers:
        hypotheses.append(
            W02LineageHypothesis(
                lineage_kind=W02LineageHypothesisKind.DUPLICATE_INSTANCE,
                evidence_refs=tuple(item.trace_id for item in traces if item.is_duplicate_packet) or tuple(item.trace_id for item in traces),
                unresolved=True,
            )
        )

    if "identity_swap" in markers:
        hypotheses.append(
            W02LineageHypothesis(
                lineage_kind=W02LineageHypothesisKind.SPLIT_IDENTITY,
                evidence_refs=tuple(item.trace_id for item in traces),
                unresolved=True,
            )
        )

    if not hypotheses and not contradictions and len(traces) >= 2:
        hypotheses.append(
            W02LineageHypothesis(
                lineage_kind=W02LineageHypothesisKind.SAME_INSTANCE,
                evidence_refs=tuple(item.trace_id for item in traces),
                unresolved=False,
            )
        )

    if not hypotheses:
        hypotheses.append(
            W02LineageHypothesis(
                lineage_kind=W02LineageHypothesisKind.UNKNOWN_LINEAGE,
                evidence_refs=tuple(item.trace_id for item in traces),
                unresolved=True,
            )
        )

    return W02LineageHypothesisSet(entity_id=entity_id, hypotheses=tuple(hypotheses))


def _contradiction_entry(
    *,
    tick_id: str,
    tick_index: int,
    entity_id: str,
    traces: list[W02TraceRef],
    conflict_type: W02ContradictionKind,
    affected: W02ObjectMaturityLevel,
    severity: str,
    downgrade_action: str,
    revalidation_requirement: str,
) -> W02ContradictionLedgerEntry:
    return W02ContradictionLedgerEntry(
        conflict_id=f"w02:{tick_id}:{tick_index}:conflict:{entity_id}:{conflict_type.value}",
        conflicting_trace_refs=tuple(item.trace_id for item in traces),
        conflict_type=conflict_type,
        affected_maturity_level=affected,
        severity=severity,
        unresolved_status=True,
        downgrade_action=downgrade_action,
        revalidation_requirement=revalidation_requirement,
    )


def _slot_confidence_from_labels(traces: list[W02TraceRef], label_kind: str) -> str:
    if label_kind == "kind":
        labels = {item.kind_label for item in traces if item.kind_label}
    elif label_kind == "role":
        labels = {item.role_label for item in traces if item.role_label}
    else:
        labels = {item.structural_signature for item in traces if item.structural_signature}

    if not labels:
        return "insufficient_basis"
    if len(labels) == 1:
        return "medium"
    return "low"


def _confidence_band(traces: list[W02TraceRef]) -> str:
    bands = [str(item.confidence_band or "").lower() for item in traces]
    if not bands:
        return "insufficient_basis"
    if any(item in {"insufficient_basis", "low"} for item in bands):
        return "low"
    if any(item == "medium" for item in bands):
        return "medium"
    return "high"


def _minimal_result(
    *,
    bundle_id: str,
    reason: str,
    restrictions: tuple[str, ...],
) -> W02ResultBundle:
    telemetry = W02Telemetry(
        trace_selection_count=0,
        candidate_count=0,
        promoted_count=0,
        blocked_count=0,
        contested_count=0,
        downgraded_count=0,
        contradiction_count=0,
        lineage_ambiguity_count=0,
        consumer_ready=False,
        no_clean_regularities=True,
        must_abstain_count=0,
    )
    gate = W02GateDecision(
        consumer_ready=False,
        clean_regularity_claim_allowed=False,
        accepted_count=0,
        blocked_count=0,
        contested_count=0,
        downgraded_count=0,
        contradiction_count=0,
        lineage_ambiguity_count=0,
        must_abstain_count=0,
        required_restrictions=restrictions,
        reason_codes=("no_clean_regularity_claim",),
        reason=reason,
    )
    return W02ResultBundle(
        bundle_id=bundle_id,
        regularity_records=(),
        disambiguation_records=(),
        promotion_decisions=(),
        contradiction_ledger=(),
        lineage_hypotheses=(),
        downgrade_records=(),
        downstream_permission_packets=(),
        telemetry=telemetry,
        scope_marker=W02ScopeMarker(
            scope="frontier_hosted_w02_regularity_extraction_slice",
            staged_regularity_only=True,
            no_mature_object_identity_claim=True,
            no_object_permanence_claim=True,
            no_scene_graph_truth_claim=True,
            no_policy_selection_claim=True,
            reason=reason,
        ),
        gate=gate,
        reason=reason,
    )
