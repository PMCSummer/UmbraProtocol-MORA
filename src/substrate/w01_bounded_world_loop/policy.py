from __future__ import annotations

from collections import defaultdict

from substrate.w01_bounded_world_loop.models import (
    W01CausalLinkStatus,
    W01ContradictionLedgerEntry,
    W01DownstreamPermissionPacket,
    W01EntityCentricWorldScaffoldToken,
    W01GateDecision,
    W01ObservationActionEffectLinkage,
    W01PacketIntegrityStatus,
    W01PresenceMode,
    W01Result,
    W01ScaffoldTokenKind,
    W01ScopeMarker,
    W01SourceAuthority,
    W01Telemetry,
    W01WorldAdmissionState,
    W01WorldLoopAdmissionRecord,
    W01WorldPacket,
    W01WorldPacketSet,
)


def build_w01_bounded_world_loop(
    *,
    tick_id: str,
    tick_index: int,
    packet_set: W01WorldPacketSet | None,
    enforcement_enabled: bool = True,
) -> W01Result:
    if not enforcement_enabled:
        return _minimal_result(
            packet_set_id=f"w01:{tick_id}:packet_set:none",
            reason="W01 gate disabled in test fixture",
            restrictions=("w01_disabled", "w01_no_clean_world_claim"),
        )

    if not isinstance(packet_set, W01WorldPacketSet):
        return _minimal_result(
            packet_set_id=f"w01:{tick_id}:packet_set:none",
            reason=(
                "w01 requires typed world packets and does not synthesize scaffold admission "
                "from text/history hints"
            ),
            restrictions=("insufficient_w01_basis", "w01_no_clean_world_claim"),
        )

    if not packet_set.packets:
        return _minimal_result(
            packet_set_id=packet_set.packet_set_id,
            reason="w01 received no world packets and preserves explicit absence/no-clean world claim",
            restrictions=("w01_no_world_packet", "w01_no_clean_world_claim"),
            absent_count=1,
        )

    admissions: list[W01WorldLoopAdmissionRecord] = []
    tokens: list[W01EntityCentricWorldScaffoldToken] = []
    permissions: list[W01DownstreamPermissionPacket] = []
    contradictions: list[W01ContradictionLedgerEntry] = []

    authority_missing_count = 0
    non_mature_object_claim_count = 0

    grouped_by_entity: dict[str, list[W01WorldPacket]] = defaultdict(list)
    for packet in packet_set.packets:
        grouped_by_entity[packet.entity_ref].append(packet)

    contradictory_packet_refs: set[str] = set()
    for entity_ref, packets in grouped_by_entity.items():
        modes = {packet.presence_mode for packet in packets}
        has_present_like = bool(
            modes.intersection({W01PresenceMode.PRESENT, W01PresenceMode.PARTIAL, W01PresenceMode.DEGRADED})
        )
        has_absent_like = bool(
            modes.intersection({W01PresenceMode.ABSENT, W01PresenceMode.REVOKED_OR_INVALID})
        )
        if (has_present_like and has_absent_like) or any(packet.contradiction_markers for packet in packets):
            refs = tuple(packet.packet_id for packet in packets)
            contradictory_packet_refs.update(refs)
            contradictions.append(
                W01ContradictionLedgerEntry(
                    conflict_id=f"w01:{tick_id}:{tick_index}:conflict:{entity_ref}",
                    conflicting_packet_refs=refs,
                    conflict_type="presence_mode_conflict",
                    unresolved_status=True,
                    authority_comparison="conflicting_world_packets",
                    revocation_status="mixed_or_unresolved",
                    required_downstream_behavior=(
                        "must_preserve_uncertainty",
                        "must_not_promote_clean_world_claim",
                    ),
                    provenance_ref=tuple(packet.provenance_ref[0] for packet in packets if packet.provenance_ref),
                )
            )

    for packet in packet_set.packets:
        decision_state, reason_codes, uncertainty = _decide_admission(packet, contradictory_packet_refs)
        confidence_band = _confidence_band(packet.confidence)
        admissions.append(
            W01WorldLoopAdmissionRecord(
                admission_id=f"w01:{tick_id}:{tick_index}:admission:{packet.packet_id}",
                packet_ref=packet.packet_id,
                cycle_id=f"{tick_id}:{tick_index}",
                entity_id=packet.entity_ref,
                source_authority=packet.source_authority,
                presence_mode_normalized=packet.presence_mode,
                admission_state=decision_state,
                decision_reason_codes=reason_codes,
                confidence_band=confidence_band,
                uncertainty_markers=uncertainty,
                provenance_ref=packet.provenance_ref,
            )
        )

        if "missing_source_authority" in reason_codes:
            authority_missing_count += 1
        if packet.object_label or packet.object_stream_id:
            non_mature_object_claim_count += 1

        tokens.extend(_build_tokens(tick_id=tick_id, tick_index=tick_index, packet=packet, decision_state=decision_state))
        permissions.append(
            _build_permission(
                admission_ref=f"w01:{tick_id}:{tick_index}:admission:{packet.packet_id}",
                decision_state=decision_state,
                reason_codes=reason_codes,
            )
        )

    linkages = _build_linkages(tick_id=tick_id, tick_index=tick_index, packets=packet_set.packets)

    admitted_count = sum(int(item.admission_state is W01WorldAdmissionState.ADMITTED) for item in admissions)
    admitted_with_uncertainty_count = sum(
        int(item.admission_state is W01WorldAdmissionState.ADMITTED_WITH_UNCERTAINTY) for item in admissions
    )
    scaffold_only_count = sum(int(item.admission_state is W01WorldAdmissionState.SCAFFOLD_ONLY) for item in admissions)
    absent_count = sum(int(item.admission_state is W01WorldAdmissionState.ABSENT) for item in admissions)
    contested_count = sum(int(item.admission_state is W01WorldAdmissionState.CONTESTED) for item in admissions)
    rejected_count = sum(int(item.admission_state in {W01WorldAdmissionState.REJECTED, W01WorldAdmissionState.NO_CLEAN_WORLD_CLAIM}) for item in admissions)
    revoked_count = sum(int(item.admission_state is W01WorldAdmissionState.REVOKED) for item in admissions)
    linked_effect_count = sum(int(item.causal_link_status is W01CausalLinkStatus.LINKED_PROVISIONAL) for item in linkages)
    no_link_count = sum(int(item.causal_link_status is not W01CausalLinkStatus.LINKED_PROVISIONAL) for item in linkages)

    telemetry = W01Telemetry(
        packet_count=len(packet_set.packets),
        admitted_count=admitted_count,
        admitted_with_uncertainty_count=admitted_with_uncertainty_count,
        scaffold_only_count=scaffold_only_count,
        absent_count=absent_count,
        contested_count=contested_count,
        rejected_count=rejected_count,
        revoked_count=revoked_count,
        contradiction_count=len(contradictions),
        linked_effect_count=linked_effect_count,
        no_link_count=no_link_count,
        source_authority_missing_count=authority_missing_count,
        non_mature_object_claim_count=non_mature_object_claim_count,
        consumer_ready_count=sum(int((not p.must_abstain) and p.may_use_as_world_scaffold) for p in permissions),
    )
    gate = _build_gate(telemetry=telemetry)

    return W01Result(
        packet_set_id=packet_set.packet_set_id,
        packet_refs=tuple(packet.packet_id for packet in packet_set.packets),
        admission_records=tuple(admissions),
        scaffold_tokens=tuple(tokens),
        action_effect_linkages=tuple(linkages),
        contradiction_ledger=tuple(contradictions),
        downstream_permissions=tuple(permissions),
        telemetry=telemetry,
        scope_marker=W01ScopeMarker(
            scope="frontier_hosted_w01_bounded_world_scaffold_slice",
            staged_world_scaffold_only=True,
            no_mature_object_claim=True,
            no_object_permanence_claim=True,
            no_scene_graph_maturity_claim=True,
            no_policy_selection_claim=True,
            no_world_truth_claim=True,
            reason=(
                "w01 admits authority-scoped world packets as staged scaffold evidence and "
                "does not claim mature object/world truth in this narrow frontier slice"
            ),
        ),
        gate=gate,
        reason="w01 produced bounded world-loop admission records and downstream permission packets",
    )


def _decide_admission(
    packet: W01WorldPacket,
    contradictory_packet_refs: set[str],
) -> tuple[W01WorldAdmissionState, tuple[str, ...], tuple[str, ...]]:
    reasons: list[str] = []
    uncertainty: list[str] = []

    if packet.packet_id in contradictory_packet_refs:
        reasons.append("contradictory_world_packets")
        uncertainty.append("contradictory")
        return W01WorldAdmissionState.CONTESTED, tuple(reasons), tuple(uncertainty)

    if packet.source_authority in {W01SourceAuthority.UNKNOWN_SOURCE, W01SourceAuthority.REVOKED_SOURCE}:
        reasons.append("missing_source_authority")
        uncertainty.append("authority_missing")
        return W01WorldAdmissionState.REJECTED, tuple(reasons), tuple(uncertainty)

    if packet.integrity_status is W01PacketIntegrityStatus.MISSING_AUTHORITY:
        reasons.append("missing_source_authority")
        uncertainty.append("integrity_missing_authority")
        return W01WorldAdmissionState.REJECTED, tuple(reasons), tuple(uncertainty)

    if packet.integrity_status is W01PacketIntegrityStatus.MALFORMED:
        reasons.append("malformed_packet")
        uncertainty.append("malformed")
        return W01WorldAdmissionState.REJECTED, tuple(reasons), tuple(uncertainty)

    if packet.integrity_status is W01PacketIntegrityStatus.REVOKED or packet.revoked_ref:
        reasons.append("revoked_packet")
        uncertainty.append("revoked")
        return W01WorldAdmissionState.REVOKED, tuple(reasons), tuple(uncertainty)

    if packet.source_authority is W01SourceAuthority.LANGUAGE_CONTEXT:
        reasons.append("language_context_not_world_admission")
        uncertainty.append("no_clean_world_claim")
        return W01WorldAdmissionState.NO_CLEAN_WORLD_CLAIM, tuple(reasons), tuple(uncertainty)

    if packet.presence_mode is W01PresenceMode.UNKNOWN:
        reasons.append("unknown_presence_mode")
        uncertainty.append("unknown_presence")
        return W01WorldAdmissionState.CONTESTED, tuple(reasons), tuple(uncertainty)

    if packet.presence_mode is W01PresenceMode.ABSENT:
        reasons.append("explicit_absence")
        uncertainty.append("absence_marker")
        return W01WorldAdmissionState.ABSENT, tuple(reasons), tuple(uncertainty)

    if packet.presence_mode in {W01PresenceMode.SCAFFOLD_ONLY, W01PresenceMode.PARTIAL, W01PresenceMode.DEGRADED}:
        reasons.append("staged_scaffold_or_partial")
        uncertainty.append("scaffold_only")
        return W01WorldAdmissionState.SCAFFOLD_ONLY, tuple(reasons), tuple(uncertainty)

    if packet.presence_mode is W01PresenceMode.CONTRADICTORY:
        reasons.append("explicit_contradictory_mode")
        uncertainty.append("contradictory")
        return W01WorldAdmissionState.CONTESTED, tuple(reasons), tuple(uncertainty)

    if packet.presence_mode is W01PresenceMode.REVOKED_OR_INVALID:
        reasons.append("presence_revoked_or_invalid")
        uncertainty.append("revoked_or_invalid")
        return W01WorldAdmissionState.REVOKED, tuple(reasons), tuple(uncertainty)

    object_authority_decision = _evaluate_object_authority_tags(packet)
    if object_authority_decision is not None:
        decision_state, object_reasons, object_uncertainty = object_authority_decision
        reasons.extend(object_reasons)
        uncertainty.extend(object_uncertainty)
        return decision_state, tuple(reasons), tuple(uncertainty)

    if packet.integrity_status is W01PacketIntegrityStatus.DEGRADED:
        reasons.append("integrity_degraded")
        uncertainty.append("degraded_integrity")
        if packet.object_label or packet.object_stream_id:
            reasons.append("object_scaffold_authority_tagged")
            uncertainty.append("non_mature_object_claim")
        return W01WorldAdmissionState.ADMITTED_WITH_UNCERTAINTY, tuple(reasons), tuple(uncertainty)

    reasons.append("trusted_packet_admitted_as_scaffold")
    if packet.object_label or packet.object_stream_id:
        reasons.append("object_scaffold_authority_tagged")
        uncertainty.append("non_mature_object_claim")
    return W01WorldAdmissionState.ADMITTED, tuple(reasons), tuple(uncertainty)


def _evaluate_object_authority_tags(
    packet: W01WorldPacket,
) -> tuple[W01WorldAdmissionState, tuple[str, ...], tuple[str, ...]] | None:
    object_metadata_present = bool(packet.object_label or packet.object_stream_id)
    if not object_metadata_present:
        return None

    normalized_tags = tuple(
        tag.strip().lower()
        for tag in packet.object_authority_tags
        if isinstance(tag, str) and tag.strip()
    )
    if not normalized_tags:
        return (
            W01WorldAdmissionState.SCAFFOLD_ONLY,
            ("object_authority_tags_missing", "object_scaffold_authority_not_admitted"),
            ("object_scaffold_authority_unverified", "non_mature_object_claim"),
        )

    if any("revoked" in tag for tag in normalized_tags):
        return (
            W01WorldAdmissionState.REVOKED,
            ("object_authority_tags_revoked", "object_scaffold_authority_not_admitted"),
            ("object_scaffold_authority_revoked", "non_mature_object_claim"),
        )

    invalid_markers = {"invalid", "unknown", "missing", "none", "not_authoritative", "untrusted"}
    if any(tag in invalid_markers for tag in normalized_tags):
        return (
            W01WorldAdmissionState.REJECTED,
            ("object_authority_tags_invalid", "object_scaffold_authority_not_admitted"),
            ("object_scaffold_authority_invalid", "non_mature_object_claim"),
        )

    incompatible_markers = {"incompatible", "wrong_authority", "not_admitted"}
    if any(tag in incompatible_markers for tag in normalized_tags):
        return (
            W01WorldAdmissionState.CONTESTED,
            ("object_authority_tags_incompatible", "object_scaffold_authority_not_admitted"),
            ("object_scaffold_authority_uncertain", "non_mature_object_claim"),
        )

    return None


def _build_tokens(
    *,
    tick_id: str,
    tick_index: int,
    packet: W01WorldPacket,
    decision_state: W01WorldAdmissionState,
) -> list[W01EntityCentricWorldScaffoldToken]:
    base = {
        "packet_ref": packet.packet_id,
        "entity_ref": packet.entity_ref,
        "relation_to_entity": "packet_bound_entity_reference",
        "unresolved_reference": not bool(packet.entity_ref),
        "contradiction_marker": bool(packet.contradiction_markers),
        "absence_marker": packet.presence_mode is W01PresenceMode.ABSENT,
        "scaffold_only_marker": decision_state in {
            W01WorldAdmissionState.SCAFFOLD_ONLY,
            W01WorldAdmissionState.ADMITTED_WITH_UNCERTAINTY,
        },
        "non_mature_object_claim": bool(packet.object_label or packet.object_stream_id),
        "confidence": packet.confidence,
        "provenance_ref": packet.provenance_ref,
    }
    tokens = [
        W01EntityCentricWorldScaffoldToken(
            token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:obs",
            token_kind=W01ScaffoldTokenKind.OBSERVATION_ANCHOR,
            **base,
        ),
        W01EntityCentricWorldScaffoldToken(
            token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:entity",
            token_kind=W01ScaffoldTokenKind.RELATION_TO_ENTITY,
            **base,
        ),
    ]
    if packet.action_ref:
        tokens.append(
            W01EntityCentricWorldScaffoldToken(
                token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:action",
                token_kind=W01ScaffoldTokenKind.ACTION_SURFACE,
                **base,
            )
        )
    if packet.effect_payload:
        tokens.append(
            W01EntityCentricWorldScaffoldToken(
                token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:effect",
                token_kind=W01ScaffoldTokenKind.EFFECT_TRACE,
                **base,
            )
        )
    if base["absence_marker"]:
        tokens.append(
            W01EntityCentricWorldScaffoldToken(
                token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:absence",
                token_kind=W01ScaffoldTokenKind.ABSENCE_MARKER,
                **base,
            )
        )
    if base["contradiction_marker"]:
        tokens.append(
            W01EntityCentricWorldScaffoldToken(
                token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:contradiction",
                token_kind=W01ScaffoldTokenKind.CONTRADICTION_MARKER,
                **base,
            )
        )
    if base["scaffold_only_marker"]:
        tokens.append(
            W01EntityCentricWorldScaffoldToken(
                token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:scaffold",
                token_kind=W01ScaffoldTokenKind.SCAFFOLD_ONLY_MARKER,
                **base,
            )
        )
    if base["non_mature_object_claim"]:
        tokens.append(
            W01EntityCentricWorldScaffoldToken(
                token_id=f"w01:{tick_id}:{tick_index}:token:{packet.packet_id}:non_mature",
                token_kind=W01ScaffoldTokenKind.NON_MATURE_OBJECT_MARKER,
                **base,
            )
        )
    return tokens


def _build_permission(
    *,
    admission_ref: str,
    decision_state: W01WorldAdmissionState,
    reason_codes: tuple[str, ...],
) -> W01DownstreamPermissionPacket:
    may_use_as_world_scaffold = decision_state in {
        W01WorldAdmissionState.ADMITTED,
        W01WorldAdmissionState.ADMITTED_WITH_UNCERTAINTY,
        W01WorldAdmissionState.SCAFFOLD_ONLY,
    }
    may_use_for_grounded_transition = decision_state in {
        W01WorldAdmissionState.ADMITTED,
        W01WorldAdmissionState.ADMITTED_WITH_UNCERTAINTY,
    }
    must_abstain = decision_state in {
        W01WorldAdmissionState.REJECTED,
        W01WorldAdmissionState.REVOKED,
        W01WorldAdmissionState.NO_CLEAN_WORLD_CLAIM,
    }
    must_preserve_uncertainty = decision_state in {
        W01WorldAdmissionState.CONTESTED,
        W01WorldAdmissionState.ABSENT,
        W01WorldAdmissionState.SCAFFOLD_ONLY,
        W01WorldAdmissionState.ADMITTED_WITH_UNCERTAINTY,
        W01WorldAdmissionState.NO_CLEAN_WORLD_CLAIM,
    }
    must_escalate = must_abstain or decision_state is W01WorldAdmissionState.CONTESTED
    return W01DownstreamPermissionPacket(
        admission_ref=admission_ref,
        may_use_as_world_scaffold=may_use_as_world_scaffold,
        may_use_for_grounded_transition=may_use_for_grounded_transition,
        may_claim_object_presence=False,
        must_abstain=must_abstain,
        must_escalate=must_escalate,
        must_preserve_uncertainty=must_preserve_uncertainty,
        reason_codes=reason_codes,
    )


def _build_linkages(
    *,
    tick_id: str,
    tick_index: int,
    packets: tuple[W01WorldPacket, ...],
) -> list[W01ObservationActionEffectLinkage]:
    linkages: list[W01ObservationActionEffectLinkage] = []
    indexed_by_action: dict[str, list[W01WorldPacket]] = defaultdict(list)
    for packet in packets:
        if packet.action_ref:
            indexed_by_action[packet.action_ref].append(packet)

    for packet in packets:
        if not packet.effect_payload:
            continue

        if not packet.action_ref:
            linkages.append(
                W01ObservationActionEffectLinkage(
                    linkage_id=f"w01:{tick_id}:{tick_index}:link:{packet.packet_id}",
                    observation_packet_ref=packet.packet_id,
                    action_ref=None,
                    effect_packet_ref=packet.packet_id,
                    temporal_window_status="missing_action_ref",
                    authority_compatible=False,
                    causal_link_status=W01CausalLinkStatus.NOT_LINKED_MISSING_ACTION_REF,
                    no_link_reason="effect packet has no action_ref",
                    provenance_ref=packet.provenance_ref,
                )
            )
            continue

        peers = [item for item in indexed_by_action.get(packet.action_ref, ()) if item.packet_id != packet.packet_id]
        if not peers:
            linkages.append(
                W01ObservationActionEffectLinkage(
                    linkage_id=f"w01:{tick_id}:{tick_index}:link:{packet.packet_id}",
                    observation_packet_ref=packet.packet_id,
                    action_ref=packet.action_ref,
                    effect_packet_ref=packet.packet_id,
                    temporal_window_status="missing_observation_peer",
                    authority_compatible=False,
                    causal_link_status=W01CausalLinkStatus.NOT_LINKED_MISSING_ACTION_REF,
                    no_link_reason="no observation packet shares action_ref",
                    provenance_ref=packet.provenance_ref,
                )
            )
            continue

        peer = peers[0]
        temporal_ok = abs(packet.sequence - peer.sequence) <= 1
        authority_compatible = packet.source_authority == peer.source_authority
        integrity_ok = packet.integrity_status in {W01PacketIntegrityStatus.VALID, W01PacketIntegrityStatus.DEGRADED} and peer.integrity_status in {W01PacketIntegrityStatus.VALID, W01PacketIntegrityStatus.DEGRADED}

        if not integrity_ok:
            status = W01CausalLinkStatus.NOT_LINKED_PACKET_INVALID
            reason = "packet integrity not valid enough for linkage"
            temporal_status = "packet_invalid"
        elif not authority_compatible:
            status = W01CausalLinkStatus.NOT_LINKED_AUTHORITY_MISMATCH
            reason = "authority mismatch between observation and effect packet"
            temporal_status = "authority_mismatch"
        elif not temporal_ok:
            status = W01CausalLinkStatus.NOT_LINKED_TEMPORAL_MISMATCH
            reason = "temporal window mismatch between observation/effect packets"
            temporal_status = "temporal_mismatch"
        elif not peer.observation_payload:
            status = W01CausalLinkStatus.NOT_LINKED_EFFECT_UNVERIFIED
            reason = "observation payload missing for shared action_ref"
            temporal_status = "effect_unverified"
        else:
            status = W01CausalLinkStatus.LINKED_PROVISIONAL
            reason = None
            temporal_status = "within_window"

        linkages.append(
            W01ObservationActionEffectLinkage(
                linkage_id=f"w01:{tick_id}:{tick_index}:link:{packet.packet_id}",
                observation_packet_ref=peer.packet_id,
                action_ref=packet.action_ref,
                effect_packet_ref=packet.packet_id,
                temporal_window_status=temporal_status,
                authority_compatible=authority_compatible,
                causal_link_status=status,
                no_link_reason=reason,
                provenance_ref=tuple(dict.fromkeys((*peer.provenance_ref, *packet.provenance_ref))),
            )
        )

    return linkages


def _build_gate(*, telemetry: W01Telemetry) -> W01GateDecision:
    blocked_count = telemetry.rejected_count + telemetry.absent_count
    restrictions: list[str] = []
    reason_codes: list[str] = []

    if telemetry.packet_count == 0:
        restrictions.append("w01_no_world_packet")
        reason_codes.append("no_world_packet")
    if telemetry.source_authority_missing_count > 0:
        restrictions.append("w01_source_authority_missing")
        reason_codes.append("source_authority_missing")
    if telemetry.contradiction_count > 0:
        restrictions.append("w01_contradictory_packets")
        reason_codes.append("contradictory_packets")
    if telemetry.revoked_count > 0:
        restrictions.append("w01_revoked_packets")
        reason_codes.append("revoked_packets")
    if telemetry.non_mature_object_claim_count > 0:
        restrictions.append("w01_non_mature_object_claim_restriction")
        reason_codes.append("non_mature_object_claim")
    if telemetry.no_link_count > 0:
        restrictions.append("w01_unlinked_effect_trace")
        reason_codes.append("unlinked_effect_trace")

    consumer_ready = bool(
        telemetry.admitted_count > 0
        and telemetry.source_authority_missing_count == 0
        and telemetry.contradiction_count == 0
        and telemetry.revoked_count == 0
    )
    if not consumer_ready:
        restrictions.append("w01_no_clean_world_claim")
        reason_codes.append("no_clean_world_claim")

    return W01GateDecision(
        consumer_ready=consumer_ready,
        admission_required=True,
        clean_world_claim_allowed=False,
        accepted_count=telemetry.admitted_count + telemetry.admitted_with_uncertainty_count,
        contested_count=telemetry.contested_count,
        blocked_count=blocked_count,
        revoked_count=telemetry.revoked_count,
        authority_missing_count=telemetry.source_authority_missing_count,
        object_overclaim_blocked_count=telemetry.non_mature_object_claim_count,
        contradiction_count=telemetry.contradiction_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def _minimal_result(
    *,
    packet_set_id: str,
    reason: str,
    restrictions: tuple[str, ...],
    absent_count: int = 0,
) -> W01Result:
    telemetry = W01Telemetry(
        packet_count=0,
        admitted_count=0,
        admitted_with_uncertainty_count=0,
        scaffold_only_count=0,
        absent_count=absent_count,
        contested_count=0,
        rejected_count=0,
        revoked_count=0,
        contradiction_count=0,
        linked_effect_count=0,
        no_link_count=0,
        source_authority_missing_count=0,
        non_mature_object_claim_count=0,
        consumer_ready_count=0,
    )
    gate = W01GateDecision(
        consumer_ready=False,
        admission_required=True,
        clean_world_claim_allowed=False,
        accepted_count=0,
        contested_count=0,
        blocked_count=absent_count,
        revoked_count=0,
        authority_missing_count=0,
        object_overclaim_blocked_count=0,
        contradiction_count=0,
        required_restrictions=restrictions,
        reason_codes=("no_clean_world_claim",),
    )
    return W01Result(
        packet_set_id=packet_set_id,
        packet_refs=(),
        admission_records=(),
        scaffold_tokens=(),
        action_effect_linkages=(),
        contradiction_ledger=(),
        downstream_permissions=(),
        telemetry=telemetry,
        scope_marker=W01ScopeMarker(
            scope="frontier_hosted_w01_bounded_world_scaffold_slice",
            staged_world_scaffold_only=True,
            no_mature_object_claim=True,
            no_object_permanence_claim=True,
            no_scene_graph_maturity_claim=True,
            no_policy_selection_claim=True,
            no_world_truth_claim=True,
            reason=reason,
        ),
        gate=gate,
        reason=reason,
    )


def _confidence_band(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.55:
        return "medium"
    if confidence >= 0.3:
        return "low"
    return "insufficient_basis"
