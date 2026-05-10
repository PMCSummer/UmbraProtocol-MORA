from __future__ import annotations

from collections import defaultdict

from substrate.w03_schema_consolidation.models import (
    W03ContradictionConsequenceRecord,
    W03ContradictionConsequenceRoute,
    W03DownstreamSchemaPermissionPacket,
    W03EverydayPriorRecord,
    W03GateDecision,
    W03InputBundle,
    W03ResultBundle,
    W03SchemaCandidateRecord,
    W03SchemaChannel,
    W03SchemaChannelState,
    W03SchemaStatus,
    W03SchemaVersionRecord,
    W03SchemaVersionTrigger,
    W03ScopeMarker,
    W03StaleSchemaAssessment,
    W03Telemetry,
)


def build_w03_schema_consolidation(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: W03InputBundle | None,
    enforcement_enabled: bool = True,
) -> W03ResultBundle:
    if not enforcement_enabled:
        return _minimal_result(
            bundle_id=f"w03:{tick_id}:bundle:none",
            reason="W03 gate disabled in test fixture",
            restrictions=("w03_disabled", "w03_no_clean_schema_claim"),
        )

    if not isinstance(input_bundle, W03InputBundle):
        return _minimal_result(
            bundle_id=f"w03:{tick_id}:bundle:none",
            reason=(
                "w03 requires typed w02 regularity artifacts and rejects language/common-sense priors as world support"
            ),
            restrictions=("insufficient_w03_basis", "w03_no_clean_schema_claim"),
        )

    if not input_bundle.w02_regularity_records:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="w03 received no w02 regularities and cannot consolidate schema claims",
            restrictions=("w03_no_w02_support", "w03_no_clean_schema_claim"),
        )

    permission_by_id = {getattr(item, "regularity_id", ""): item for item in input_bundle.w02_permission_packets}
    previous_versions = {sid: version for sid, version in input_bundle.previous_schema_versions}

    schema_candidates: list[W03SchemaCandidateRecord] = []
    priors: list[W03EverydayPriorRecord] = []
    channel_states: list[W03SchemaChannelState] = []
    contradiction_consequences: list[W03ContradictionConsequenceRecord] = []
    version_records: list[W03SchemaVersionRecord] = []
    stale_assessments: list[W03StaleSchemaAssessment] = []
    permission_packets: list[W03DownstreamSchemaPermissionPacket] = []
    split_or_merge_proposals: list[str] = []

    channel_agg: dict[W03SchemaChannel, list[W03SchemaCandidateRecord]] = defaultdict(list)

    for record in input_bundle.w02_regularity_records:
        schema_id = f"w03:{tick_id}:{getattr(record, 'regularity_id', 'unknown')}"
        channel = _channel_from_w02_candidate_type(str(getattr(getattr(record, "candidate_type", None), "value", "unknown")))
        packet = permission_by_id.get(getattr(record, "regularity_id", ""))
        contradictions = tuple(
            item
            for item in input_bundle.w02_contradiction_ledger
            if any(ref in set(getattr(record, "source_trace_refs", ())) for ref in getattr(item, "conflicting_trace_refs", ()))
        )

        uncertainty_markers = tuple(getattr(record, "uncertainty_markers", ()))
        source_authority_scope = tuple(getattr(record, "source_authority_set", ()))
        authority_scope_sufficient = bool(source_authority_scope)
        has_revoked_authority = (not authority_scope_sufficient) or any(
            authority in {"revoked_source", "unknown_source", ""}
            for authority in source_authority_scope
        )
        record_provenance = tuple(getattr(record, "provenance", ()))
        provenance_sufficient = bool(record_provenance)
        context_scope = ("w01_w02_world_loop_context",)
        status = _status_from_w02(
            record=record,
            packet=packet,
            contradictions=contradictions,
            authority_scope_sufficient=authority_scope_sufficient,
            provenance_sufficient=provenance_sufficient,
        )

        negative_refs = tuple(
            dict.fromkeys(
                ref
                for item in contradictions
                for ref in getattr(item, "conflicting_trace_refs", ())
            )
        )

        stale_markers: list[str] = []
        temporal_span = tuple(getattr(record, "temporal_span", (tick_index, tick_index)))
        spread = int(temporal_span[1] - temporal_span[0]) if len(temporal_span) == 2 else 0
        if spread <= 0:
            stale_markers.append("temporal_span_zero")
        if not provenance_sufficient:
            stale_markers.append("support_provenance_missing")
        if has_revoked_authority:
            stale_markers.append("authority_revoked_or_unknown")
        if contradictions:
            stale_markers.append("contradiction_present")

        candidate = W03SchemaCandidateRecord(
            schema_id=schema_id,
            schema_channel=channel,
            support_regularities=(str(getattr(record, "regularity_id", "")),),
            negative_evidence_refs=negative_refs,
            source_authority_scope=source_authority_scope,
            context_scope=context_scope,
            temporal_span=temporal_span if len(temporal_span) == 2 else (tick_index, tick_index),
            applicability_conditions=("bounded_by_w02_permission", "override_by_live_w01_w02"),
            confidence_band=str(getattr(record, "confidence_band", "insufficient_basis")),
            maturity_basis=(str(getattr(getattr(record, "maturity_level", None), "value", "unknown")),),
            unresolved_contradictions=tuple(str(getattr(item, "conflict_id", "")) for item in contradictions),
            stale_markers=tuple(dict.fromkeys(stale_markers)),
            status=status,
            provenance=tuple(dict.fromkeys((*input_bundle.source_lineage, *record_provenance))),
        )
        schema_candidates.append(candidate)
        channel_agg[channel].append(candidate)

        consequence = _build_consequence(schema_id=schema_id, contradictions=contradictions, status=status)
        if consequence is not None:
            contradiction_consequences.append(consequence)
            if consequence.consequence_route is W03ContradictionConsequenceRoute.SPLIT:
                split_or_merge_proposals.append(f"split_required:{schema_id}")

        stale = W03StaleSchemaAssessment(
            schema_id=schema_id,
            last_validated_at=f"tick:{tick_index}",
            stale_risk="high" if stale_markers else "low",
            drift_type="authority_or_context_drift" if stale_markers else "none",
            missing_expected_evidence=("temporal_spread_revalidation",) if spread <= 0 else (),
            authority_revocation_status=has_revoked_authority,
            revalidation_required=bool(stale_markers),
            blocked_until_revalidated=status in {
                W03SchemaStatus.BLOCKED,
                W03SchemaStatus.CONTESTED,
                W03SchemaStatus.QUARANTINED,
                W03SchemaStatus.MUST_REVALIDATE,
            },
        )
        stale_assessments.append(stale)

        prior = _maybe_prior_from_candidate(candidate=candidate)
        if prior is not None:
            priors.append(prior)

        permission_packets.append(
            _permission_packet_for_candidate(
                candidate=candidate,
                prior=prior,
                stale=stale,
            )
        )

        prior_version = previous_versions.get(schema_id, 0)
        trigger = (
            W03SchemaVersionTrigger.CONTRADICTION_DOWNGRADE
            if candidate.status in {W03SchemaStatus.CONTESTED, W03SchemaStatus.DOWNGRADED, W03SchemaStatus.QUARANTINED}
            else W03SchemaVersionTrigger.INITIAL_CONSOLIDATION
        )
        version_records.append(
            W03SchemaVersionRecord(
                schema_id=schema_id,
                prior_version=prior_version,
                new_version=prior_version + 1,
                update_trigger=trigger,
                accepted_evidence_refs=candidate.support_regularities,
                rejected_evidence_refs=candidate.negative_evidence_refs,
                changed_commitments=(candidate.status.value,),
                split_from=tuple(x.replace("split_required:", "") for x in split_or_merge_proposals if x.endswith(schema_id)),
                merged_from=(),
                downgraded_from=("w02_regularities",) if trigger is W03SchemaVersionTrigger.CONTRADICTION_DOWNGRADE else (),
                audit_reason_codes=(candidate.status.value,),
            )
        )

    for channel in W03SchemaChannel:
        items = channel_agg.get(channel, [])
        if not items:
            continue
        contradiction_count = sum(1 for item in items if item.unresolved_contradictions)
        stale_count = sum(1 for item in items if item.stale_markers)
        status = _aggregate_channel_status(items)
        reasons: list[str] = []
        if contradiction_count > 0:
            reasons.append("channel_contradiction")
        if stale_count > 0:
            reasons.append("channel_stale")
        if not reasons:
            reasons.append("channel_clean")
        channel_states.append(
            W03SchemaChannelState(
                schema_channel=channel,
                support_count=len(items),
                contradiction_count=contradiction_count,
                stale_count=stale_count,
                status=status,
                reason_codes=tuple(dict.fromkeys(reasons)),
            )
        )

    operational_default_count = sum(1 for item in priors if item.operational_default_status)
    contested_count = sum(1 for item in schema_candidates if item.status in {W03SchemaStatus.CONTESTED, W03SchemaStatus.QUARANTINED, W03SchemaStatus.SPLIT_REQUIRED})
    stale_count = sum(1 for item in stale_assessments if item.revalidation_required)
    must_revalidate_count = sum(1 for item in permission_packets if item.must_revalidate_before_use)
    must_abstain_count = sum(1 for item in permission_packets if item.must_abstain)
    contradiction_count = len(contradiction_consequences)

    clean_prior_exists = any(
        item.status in {W03SchemaStatus.BOUNDED_PRIOR, W03SchemaStatus.OPERATIONAL_DEFAULT, W03SchemaStatus.NARROW_PRIOR}
        for item in priors
    )
    no_clean_schema = not clean_prior_exists
    consumer_ready = bool(clean_prior_exists and must_abstain_count == 0)

    restrictions: list[str] = []
    reason_codes: list[str] = []
    if no_clean_schema:
        restrictions.append("w03_no_clean_schema_claim")
        reason_codes.append("no_clean_schema")
    if contradiction_count > 0:
        restrictions.append("w03_contradiction_review_required")
        reason_codes.append("contradiction_present")
    if must_revalidate_count > 0:
        restrictions.append("w03_revalidation_required")
        reason_codes.append("must_revalidate")
    if must_abstain_count > 0:
        restrictions.append("w03_must_abstain")
        reason_codes.append("must_abstain")
    if not consumer_ready:
        restrictions.append("w03_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    telemetry = W03Telemetry(
        regularity_intake_count=len(input_bundle.w02_regularity_records),
        schema_candidate_count=len(schema_candidates),
        everyday_prior_count=len(priors),
        operational_default_count=operational_default_count,
        contested_count=contested_count,
        stale_count=stale_count,
        must_revalidate_count=must_revalidate_count,
        must_abstain_count=must_abstain_count,
        contradiction_count=contradiction_count,
        version_update_count=len(version_records),
        consumer_ready=consumer_ready,
        no_clean_schema=no_clean_schema,
    )

    gate = W03GateDecision(
        consumer_ready=consumer_ready,
        no_clean_schema=no_clean_schema,
        must_revalidate_count=must_revalidate_count,
        must_abstain_count=must_abstain_count,
        contradiction_count=contradiction_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="w03 consolidates bounded schema/prior candidates from w02 and preserves contradiction/revalidation discipline",
    )

    return W03ResultBundle(
        bundle_id=input_bundle.bundle_id,
        schema_candidates=tuple(schema_candidates),
        everyday_priors=tuple(priors),
        channel_states=tuple(channel_states),
        contradiction_consequences=tuple(contradiction_consequences),
        version_records=tuple(version_records),
        stale_assessments=tuple(stale_assessments),
        split_or_merge_proposals=tuple(dict.fromkeys(split_or_merge_proposals)),
        downstream_permission_packets=tuple(permission_packets),
        telemetry=telemetry,
        gate=gate,
        scope_marker=W03ScopeMarker(
            scope="frontier_hosted_w03_schema_consolidation_slice",
            schema_consolidation_only=True,
            no_mature_world_truth_claim=True,
            no_common_sense_engine_claim=True,
            no_planner_claim=True,
            no_memory_lifecycle_claim=True,
            reason=(
                "w03 consolidates bounded schema/prior candidates with support/authority/context constraints and "
                "never emits mature world truth"
            ),
        ),
        no_claim_markers=(
            "no_mature_world_truth_claim",
            "no_common_sense_engine_claim",
            "no_planner_claim",
            "no_memory_lifecycle_claim",
        ),
        reason="w03 produced bounded schema consolidation and everyday prior packets",
    )


def _channel_from_w02_candidate_type(candidate_type_value: str) -> W03SchemaChannel:
    mapping = {
        "instance": W03SchemaChannel.INSTANCE_PRIOR,
        "kind": W03SchemaChannel.KIND_PRIOR,
        "scene_role": W03SchemaChannel.SCENE_ROLE_PRIOR,
        "structural_signature": W03SchemaChannel.STRUCTURAL_SIGNATURE_PRIOR,
        "affordance": W03SchemaChannel.AFFORDANCE_PRIOR,
    }
    return mapping.get(candidate_type_value, W03SchemaChannel.MULTI_CHANNEL_CONTESTED)


def _status_from_w02(
    *,
    record: object,
    packet: object | None,
    contradictions: tuple[object, ...],
    authority_scope_sufficient: bool,
    provenance_sufficient: bool,
) -> W03SchemaStatus:
    promotion = str(getattr(getattr(record, "promotion_status", None), "value", ""))
    maturity = str(getattr(getattr(record, "maturity_level", None), "value", ""))
    uncertainties = set(getattr(record, "uncertainty_markers", ()))

    if packet is None:
        return W03SchemaStatus.BLOCKED

    must_abstain = bool(getattr(packet, "must_abstain", False))
    may_instance = bool(getattr(packet, "may_use_as_instance_hypothesis", False))
    may_hint = bool(
        getattr(packet, "may_use_as_kind_hint", False)
        or getattr(packet, "may_use_as_affordance_hint", False)
        or getattr(packet, "may_use_as_scene_role_hint", False)
        or getattr(packet, "may_use_as_scaffold", False)
    )

    if must_abstain:
        return W03SchemaStatus.QUARANTINED if contradictions else W03SchemaStatus.BLOCKED

    if not authority_scope_sufficient:
        return W03SchemaStatus.MUST_REVALIDATE

    if not provenance_sufficient:
        return W03SchemaStatus.DEFERRED

    if contradictions:
        return W03SchemaStatus.CONTESTED

    if "presence_mode_not_clean_present" in uncertainties or "source_authority_conflict" in uncertainties:
        return W03SchemaStatus.DEFERRED

    if promotion != "promoted":
        return W03SchemaStatus.DEFERRED

    if maturity in {"persistent_instance_hypothesis", "persistent_instance_candidate"} and may_instance:
        return W03SchemaStatus.BOUNDED_PRIOR

    if may_hint:
        return W03SchemaStatus.NARROW_PRIOR

    return W03SchemaStatus.SCHEMA_CANDIDATE


def _build_consequence(
    *,
    schema_id: str,
    contradictions: tuple[object, ...],
    status: W03SchemaStatus,
) -> W03ContradictionConsequenceRecord | None:
    if not contradictions:
        return None

    route = W03ContradictionConsequenceRoute.BLOCK_DOWNSTREAM_USE
    action = "block_clean_schema_use"
    if any(str(getattr(getattr(item, "conflict_type", None), "value", "")) == "replacement_ambiguity" for item in contradictions):
        route = W03ContradictionConsequenceRoute.SPLIT
        action = "split_lineage_required"
    elif status is W03SchemaStatus.CONTESTED:
        route = W03ContradictionConsequenceRoute.RETAIN_AS_NARROW_CONTESTED_PRIOR
        action = "retain_contested_narrow_prior"

    first = contradictions[0]
    return W03ContradictionConsequenceRecord(
        conflict_id=str(getattr(first, "conflict_id", f"{schema_id}:conflict")),
        consequence_route=route,
        affected_schema_ids=(schema_id,),
        action_taken=action,
        downstream_permission_change=("must_abstain", "must_preserve_contradiction"),
        unresolved_status=True,
        future_revalidation_requirement="w02_contradiction_resolution_required",
    )


def _maybe_prior_from_candidate(*, candidate: W03SchemaCandidateRecord) -> W03EverydayPriorRecord | None:
    if candidate.status in {
        W03SchemaStatus.BLOCKED,
        W03SchemaStatus.CONTESTED,
        W03SchemaStatus.QUARANTINED,
        W03SchemaStatus.SPLIT_REQUIRED,
        W03SchemaStatus.NO_CLEAN_SCHEMA_CLAIM,
    }:
        return None

    operational = candidate.status is W03SchemaStatus.BOUNDED_PRIOR and not candidate.stale_markers
    prior_status = W03SchemaStatus.OPERATIONAL_DEFAULT if operational else candidate.status
    return W03EverydayPriorRecord(
        prior_id=f"prior:{candidate.schema_id}",
        schema_id=candidate.schema_id,
        prior_statement=f"bounded_{candidate.schema_channel.value}",
        operational_default_status=operational,
        allowed_use_cases=("bounded_context_use",),
        blocked_use_cases=("global_truth_claim", "planner_override_without_live_evidence"),
        override_conditions=("live_w01_w02_evidence_overrides_w03_prior",),
        revalidation_conditions=("stale_or_contradiction_requires_revalidation",),
        prohibited_claims=(
            "stable_object_identity_truth",
            "universal_common_sense_rule",
            "ontology_commitment",
        ),
        claim_boundary="bounded_prior_only",
        status=prior_status,
        provenance=candidate.provenance,
    )


def _permission_packet_for_candidate(
    *,
    candidate: W03SchemaCandidateRecord,
    prior: W03EverydayPriorRecord | None,
    stale: W03StaleSchemaAssessment,
) -> W03DownstreamSchemaPermissionPacket:
    hard_blocked = candidate.status in {
        W03SchemaStatus.CONTESTED,
        W03SchemaStatus.QUARANTINED,
        W03SchemaStatus.BLOCKED,
        W03SchemaStatus.SPLIT_REQUIRED,
        W03SchemaStatus.NO_CLEAN_SCHEMA_CLAIM,
    }
    clean_bounded_statuses = {
        W03SchemaStatus.BOUNDED_PRIOR,
        W03SchemaStatus.OPERATIONAL_DEFAULT,
    }
    must_revalidate = stale.revalidation_required or candidate.status in {
        W03SchemaStatus.DEFERRED,
        W03SchemaStatus.MUST_REVALIDATE,
        W03SchemaStatus.STALE,
        W03SchemaStatus.DOWNGRADED,
    }
    must_abstain = hard_blocked
    may_bounded = bool(
        prior is not None
        and prior.status in clean_bounded_statuses
        and candidate.status in clean_bounded_statuses
        and not candidate.unresolved_contradictions
        and not candidate.stale_markers
        and not must_revalidate
        and not must_abstain
    )
    may_default = bool(
        prior is not None
        and prior.operational_default_status
        and prior.status is W03SchemaStatus.OPERATIONAL_DEFAULT
        and may_bounded
    )

    reason_codes: list[str] = [candidate.status.value]
    if must_revalidate:
        reason_codes.append("must_revalidate")
    if must_abstain:
        reason_codes.append("must_abstain")
    if not may_bounded:
        reason_codes.append("bounded_prior_not_permitted")
    if candidate.unresolved_contradictions:
        reason_codes.append("must_preserve_contradiction")

    prohibited_claims = [
        "mature_world_truth",
        "stable_object_identity_beyond_w02",
        "universal_common_sense_rule",
    ]
    if not may_bounded:
        prohibited_claims.extend(
            [
                "clean_everyday_prior_without_clean_w02_support",
                "broad_context_transfer_without_authority_scope_gate",
                "operational_default_without_clean_schema_status",
            ]
        )
    if must_revalidate:
        prohibited_claims.append("operational_default_before_revalidation")
    if must_abstain:
        prohibited_claims.append("bounded_prior_use_while_blocked_or_contested")

    return W03DownstreamSchemaPermissionPacket(
        schema_id=candidate.schema_id,
        channel=candidate.schema_channel,
        may_use_as_bounded_prior=may_bounded,
        may_use_as_schema_hint=bool(candidate.status in {W03SchemaStatus.SCHEMA_CANDIDATE, W03SchemaStatus.NARROW_PRIOR, W03SchemaStatus.BOUNDED_PRIOR} and not must_abstain),
        may_use_as_operational_default=may_default,
        must_revalidate_before_use=must_revalidate,
        must_preserve_contradiction=bool(candidate.unresolved_contradictions),
        must_abstain=must_abstain,
        prohibited_claims=tuple(dict.fromkeys(prohibited_claims)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def _aggregate_channel_status(items: list[W03SchemaCandidateRecord]) -> W03SchemaStatus:
    if any(item.status in {W03SchemaStatus.CONTESTED, W03SchemaStatus.QUARANTINED, W03SchemaStatus.SPLIT_REQUIRED} for item in items):
        return W03SchemaStatus.CONTESTED
    if any(item.status is W03SchemaStatus.MUST_REVALIDATE for item in items):
        return W03SchemaStatus.MUST_REVALIDATE
    if any(item.status is W03SchemaStatus.BOUNDED_PRIOR for item in items):
        return W03SchemaStatus.BOUNDED_PRIOR
    if any(item.status is W03SchemaStatus.NARROW_PRIOR for item in items):
        return W03SchemaStatus.NARROW_PRIOR
    if any(item.status is W03SchemaStatus.SCHEMA_CANDIDATE for item in items):
        return W03SchemaStatus.SCHEMA_CANDIDATE
    return W03SchemaStatus.DEFERRED


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> W03ResultBundle:
    telemetry = W03Telemetry(
        regularity_intake_count=0,
        schema_candidate_count=0,
        everyday_prior_count=0,
        operational_default_count=0,
        contested_count=0,
        stale_count=0,
        must_revalidate_count=0,
        must_abstain_count=0,
        contradiction_count=0,
        version_update_count=0,
        consumer_ready=False,
        no_clean_schema=True,
    )
    gate = W03GateDecision(
        consumer_ready=False,
        no_clean_schema=True,
        must_revalidate_count=0,
        must_abstain_count=0,
        contradiction_count=0,
        required_restrictions=restrictions,
        reason_codes=("no_clean_schema",),
        reason=reason,
    )
    return W03ResultBundle(
        bundle_id=bundle_id,
        schema_candidates=(),
        everyday_priors=(),
        channel_states=(),
        contradiction_consequences=(),
        version_records=(),
        stale_assessments=(),
        split_or_merge_proposals=(),
        downstream_permission_packets=(),
        telemetry=telemetry,
        gate=gate,
        scope_marker=W03ScopeMarker(
            scope="frontier_hosted_w03_schema_consolidation_slice",
            schema_consolidation_only=True,
            no_mature_world_truth_claim=True,
            no_common_sense_engine_claim=True,
            no_planner_claim=True,
            no_memory_lifecycle_claim=True,
            reason=reason,
        ),
        no_claim_markers=(
            "no_mature_world_truth_claim",
            "no_common_sense_engine_claim",
            "no_planner_claim",
            "no_memory_lifecycle_claim",
        ),
        reason=reason,
    )
