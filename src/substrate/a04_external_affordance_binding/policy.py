from __future__ import annotations

from substrate.a04_external_affordance_binding.models import (
    A04AdmissionStatus,
    A04BindingLedger,
    A04BindingLedgerEntry,
    A04BindingStatus,
    A04BlockedCandidate,
    A04ContestedCandidate,
    A04DownstreamReadinessStatus,
    A04ExternalAffordanceBinding,
    A04ExternalAffordanceBindingResult,
    A04ExternalAffordanceCandidate,
    A04ExternalAffordanceCandidateSet,
    A04ExternalAffordanceGateDecision,
    A04LegalityStatus,
    A04NormalizationDecision,
    A04ObjectMaturityStatus,
    A04ScopeMarker,
    A04Telemetry,
    A04WorldEntityScaffold,
)


def build_a04_external_affordance_binding(
    *,
    tick_id: str,
    tick_index: int,
    candidate_set: A04ExternalAffordanceCandidateSet | None,
    binding_enabled: bool = True,
) -> A04ExternalAffordanceBindingResult:
    if not binding_enabled:
        return _build_minimal_result(
            candidate_set_id=f"a04:{tick_id}:candidate_set:none",
            reason="A04 gate disabled in test fixture",
            restrictions=("a04_disabled", "a04_no_safe_external_affordance_claim"),
        )
    if not isinstance(candidate_set, A04ExternalAffordanceCandidateSet):
        return _build_minimal_result(
            candidate_set_id=f"a04:{tick_id}:candidate_set:none",
            reason=(
                "a04 requires authority-tagged world scaffold input and does not infer "
                "external affordance bindings from untyped hints"
            ),
            restrictions=("insufficient_a04_basis", "a04_no_safe_external_affordance_claim"),
        )
    if not candidate_set.candidates:
        return _build_minimal_result(
            candidate_set_id=candidate_set.candidate_set_id,
            reason="a04 received empty candidate set and cannot emit admitted external affordance bindings",
            restrictions=("insufficient_a04_basis", "a04_no_safe_external_affordance_claim"),
        )

    scaffold_index = _index_scaffolds(candidate_set.world_scaffolds)
    bindings: list[A04ExternalAffordanceBinding] = []
    blocked_candidates: list[A04BlockedCandidate] = []
    contested_candidates: list[A04ContestedCandidate] = []
    ledger_entries: list[A04BindingLedgerEntry] = []

    authority_missing_count = 0
    object_overclaim_blocked_count = 0
    contradiction_count = 0
    revoked_count = 0

    for candidate in candidate_set.candidates:
        evaluation = _evaluate_candidate(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            scaffold_index=scaffold_index,
        )

        if evaluation["binding"] is not None:
            bindings.append(evaluation["binding"])
        if evaluation["blocked"] is not None:
            blocked_candidates.append(evaluation["blocked"])
        if evaluation["contested"] is not None:
            contested_candidates.append(evaluation["contested"])
        ledger_entries.append(evaluation["ledger"])

        authority_missing_count += int(evaluation["authority_missing"])
        object_overclaim_blocked_count += int(evaluation["object_overclaim_blocked"])
        contradiction_count += int(evaluation["contradiction"])
        revoked_count += int(evaluation["revoked"])

    accepted_count = sum(
        int(item.binding_status in {A04BindingStatus.ADMITTED, A04BindingStatus.PROVISIONAL})
        for item in bindings
    )
    contested_count = len(contested_candidates)
    blocked_count = len(blocked_candidates)

    ledger = A04BindingLedger(
        ledger_id=f"a04:{tick_id}:{tick_index}:ledger",
        entries=tuple(ledger_entries),
        accepted_count=accepted_count,
        contested_count=contested_count,
        blocked_count=blocked_count,
        revoked_count=revoked_count,
        authority_missing_count=authority_missing_count,
        object_overclaim_blocked_count=object_overclaim_blocked_count,
        contradiction_count=contradiction_count,
        reason="a04 ledger preserves authority-scoped admission decisions for external affordance bindings",
    )
    telemetry = A04Telemetry(
        a04_binding_count=accepted_count,
        a04_contested_count=contested_count,
        a04_blocked_count=blocked_count,
        a04_revoked_count=revoked_count,
        a04_authority_missing_count=authority_missing_count,
        a04_object_overclaim_blocked_count=object_overclaim_blocked_count,
        a04_consumer_ready=accepted_count > 0 and authority_missing_count == 0 and contradiction_count == 0,
        a04_staged_scaffold_only=True,
        a04_no_map_wide_claim=True,
    )
    gate = _build_gate(ledger=ledger, telemetry=telemetry)
    return A04ExternalAffordanceBindingResult(
        candidate_set_id=candidate_set.candidate_set_id,
        bindings=tuple(bindings),
        blocked_candidates=tuple(blocked_candidates),
        contested_candidates=tuple(contested_candidates),
        ledger=ledger,
        gate=gate,
        telemetry=telemetry,
        scope_marker=A04ScopeMarker(
            scope="frontier_hosted_a04_external_affordance_binding_slice",
            frontier_only=True,
            narrow_slice_only=True,
            staged_scaffold_only=True,
            entity_binding_not_object_perception=True,
            no_map_wide_claim=True,
            no_execution_claim=True,
            no_policy_selection_claim=True,
            reason=(
                "a04 binds external affordance candidates to authority-tagged world scaffolds "
                "without claiming mature object perception, policy selection, or execution"
            ),
        ),
        reason="a04 produced staged authority-scoped external affordance binding packets",
    )


def _index_scaffolds(
    scaffolds: tuple[A04WorldEntityScaffold, ...],
) -> dict[str, list[A04WorldEntityScaffold]]:
    index: dict[str, list[A04WorldEntityScaffold]] = {}
    for scaffold in scaffolds:
        if scaffold.entity_ref:
            index.setdefault(scaffold.entity_ref, []).append(scaffold)
    return index


def _evaluate_candidate(
    *,
    tick_id: str,
    tick_index: int,
    candidate: A04ExternalAffordanceCandidate,
    scaffold_index: dict[str, list[A04WorldEntityScaffold]],
) -> dict[str, object]:
    candidate_scaffolds = list(scaffold_index.get(candidate.entity_ref, ()))
    if candidate.object_ref is not None:
        candidate_scaffolds = [
            scaffold
            for scaffold in candidate_scaffolds
            if scaffold.object_ref in {None, candidate.object_ref}
        ]

    if not candidate_scaffolds:
        return _blocked_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.BLOCKED_ABSENT_SCAFFOLD,
            status=A04BindingStatus.BLOCKED,
            reason="no authority-tagged world scaffold found for candidate entity reference",
            contradiction=False,
            authority_missing=False,
            object_overclaim_blocked=False,
            revoked=False,
        )

    if not _has_valid_authority(candidate.source_authority):
        return _blocked_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.BLOCKED_NO_AUTHORITY,
            status=A04BindingStatus.BLOCKED,
            reason="candidate has no valid authority-tagged source and cannot be admitted",
            contradiction=False,
            authority_missing=True,
            object_overclaim_blocked=False,
            revoked=False,
        )

    authority_matched_scaffolds = [
        scaffold
        for scaffold in candidate_scaffolds
        if _has_valid_authority(scaffold.source_authority)
    ]
    if not authority_matched_scaffolds:
        return _blocked_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.BLOCKED_NO_AUTHORITY,
            status=A04BindingStatus.BLOCKED,
            reason="world scaffold exists but has no valid authority path",
            contradiction=False,
            authority_missing=True,
            object_overclaim_blocked=False,
            revoked=False,
        )

    scaffold = authority_matched_scaffolds[0]
    if _has_admission_contradiction(authority_matched_scaffolds):
        return _contested_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.BLOCKED_CONTRADICTORY_WORLD_PACKETS,
            reason="contradictory scaffold packets prevent clean admission decision",
            contradiction_refs=tuple(
                dict.fromkeys(
                    (*candidate.contradiction_refs, *(item.provenance[0] for item in authority_matched_scaffolds if item.provenance))
                )
            ),
            contradiction=True,
        )

    if scaffold.revocation_status or scaffold.admission_status is A04AdmissionStatus.REVOKED:
        return _revoked_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            scaffold=scaffold,
            reason="scaffold admission is revoked and binding is no longer active",
        )

    if candidate.revocation_refs:
        return _revoked_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            scaffold=scaffold,
            reason="candidate has revocation refs and cannot remain admitted",
        )

    supported = set(scaffold.supported_affordance_classes)
    if supported and candidate.affordance_class not in supported:
        return _blocked_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.BLOCKED_UNSUPPORTED_CANDIDATE,
            status=A04BindingStatus.BLOCKED,
            reason="scaffold does not support candidate affordance class",
            contradiction=False,
            authority_missing=False,
            object_overclaim_blocked=False,
            revoked=False,
        )

    if scaffold.admission_status is A04AdmissionStatus.CONTESTED or scaffold.confidence < 0.45:
        return _contested_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.CONTESTED_NOISY_SCAFFOLD,
            reason="scaffold confidence/admission remains contested in staged frontier slice",
            contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
            contradiction=False,
        )
    if scaffold.admission_status is A04AdmissionStatus.UNKNOWN:
        return _contested_decision(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate=candidate,
            decision=A04NormalizationDecision.NO_CLEAN_EXTERNAL_AFFORDANCE_CLAIM,
            reason=(
                "unknown scaffold admission status cannot be promoted to a clean admitted "
                "external-affordance binding in narrow staged slice"
            ),
            contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
            contradiction=False,
        )

    admission_status = (
        A04AdmissionStatus.PROVISIONAL
        if scaffold.admission_status is A04AdmissionStatus.PROVISIONAL
        else A04AdmissionStatus.ADMITTED
    )
    binding_status = (
        A04BindingStatus.PROVISIONAL
        if admission_status is A04AdmissionStatus.PROVISIONAL
        else A04BindingStatus.ADMITTED
    )
    object_ref_present = bool(candidate.object_ref)
    object_maturity_claim_blocked = object_ref_present

    binding = A04ExternalAffordanceBinding(
        binding_id=f"a04:{tick_id}:{tick_index}:binding:{candidate.candidate_id}",
        candidate_id=candidate.candidate_id,
        entity_ref=candidate.entity_ref,
        object_ref=candidate.object_ref,
        affordance_class=candidate.affordance_class,
        binding_status=binding_status,
        admission_status=admission_status,
        source_authority=scaffold.source_authority,
        scaffold_scope=scaffold.scaffold_scope,
        epistemic_basis=tuple(dict.fromkeys((*candidate.epistemic_basis, *candidate.required_world_scaffold_refs))),
        legality_status=_legality_status(candidate.permission_basis),
        temporal_validity=scaffold.temporal_validity,
        confidence=min(candidate.confidence, scaffold.confidence),
        downstream_scope=(
            "admitted_object_scaffold_binding"
            if object_ref_present
            else "admitted_entity_scoped_binding"
        ),
        authority_preserved=True,
        object_maturity_claim_blocked=object_maturity_claim_blocked,
        provenance=tuple(dict.fromkeys((*candidate.provenance, *scaffold.provenance))),
    )
    decision = (
        A04NormalizationDecision.ADMITTED_OBJECT_SCAFFOLD_BINDING
        if object_ref_present
        else A04NormalizationDecision.ADMITTED_ENTITY_SCOPED_BINDING
    )
    return {
        "binding": binding,
        "blocked": None,
        "contested": None,
        "ledger": A04BindingLedgerEntry(
            entry_id=f"a04:{tick_id}:{tick_index}:ledger:{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            decision=decision,
            status=binding_status,
            reason="authority-tagged scaffold admission permits staged external affordance binding",
            contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
            revocation_refs=(),
        ),
        "authority_missing": False,
        "object_overclaim_blocked": object_maturity_claim_blocked,
        "contradiction": False,
        "revoked": False,
    }


def _blocked_decision(
    *,
    tick_id: str,
    tick_index: int,
    candidate: A04ExternalAffordanceCandidate,
    decision: A04NormalizationDecision,
    status: A04BindingStatus,
    reason: str,
    contradiction: bool,
    authority_missing: bool,
    object_overclaim_blocked: bool,
    revoked: bool,
) -> dict[str, object]:
    blocked = A04BlockedCandidate(
        candidate_id=candidate.candidate_id,
        decision=decision,
        reason=reason,
        contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
    )
    return {
        "binding": None,
        "blocked": blocked,
        "contested": None,
        "ledger": A04BindingLedgerEntry(
            entry_id=f"a04:{tick_id}:{tick_index}:ledger:{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            decision=decision,
            status=status,
            reason=reason,
            contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
            revocation_refs=tuple(dict.fromkeys(candidate.revocation_refs)),
        ),
        "authority_missing": authority_missing,
        "object_overclaim_blocked": object_overclaim_blocked,
        "contradiction": contradiction,
        "revoked": revoked,
    }


def _contested_decision(
    *,
    tick_id: str,
    tick_index: int,
    candidate: A04ExternalAffordanceCandidate,
    decision: A04NormalizationDecision,
    reason: str,
    contradiction_refs: tuple[str, ...],
    contradiction: bool,
) -> dict[str, object]:
    contested = A04ContestedCandidate(
        candidate_id=candidate.candidate_id,
        decision=decision,
        reason=reason,
        contradiction_refs=contradiction_refs,
    )
    return {
        "binding": None,
        "blocked": None,
        "contested": contested,
        "ledger": A04BindingLedgerEntry(
            entry_id=f"a04:{tick_id}:{tick_index}:ledger:{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            decision=decision,
            status=A04BindingStatus.CONTESTED,
            reason=reason,
            contradiction_refs=contradiction_refs,
            revocation_refs=tuple(dict.fromkeys(candidate.revocation_refs)),
        ),
        "authority_missing": False,
        "object_overclaim_blocked": False,
        "contradiction": contradiction,
        "revoked": False,
    }


def _revoked_decision(
    *,
    tick_id: str,
    tick_index: int,
    candidate: A04ExternalAffordanceCandidate,
    scaffold: A04WorldEntityScaffold,
    reason: str,
) -> dict[str, object]:
    binding = A04ExternalAffordanceBinding(
        binding_id=f"a04:{tick_id}:{tick_index}:binding:{candidate.candidate_id}",
        candidate_id=candidate.candidate_id,
        entity_ref=candidate.entity_ref,
        object_ref=candidate.object_ref,
        affordance_class=candidate.affordance_class,
        binding_status=A04BindingStatus.REVOKED,
        admission_status=A04AdmissionStatus.REVOKED,
        source_authority=scaffold.source_authority,
        scaffold_scope=scaffold.scaffold_scope,
        epistemic_basis=tuple(dict.fromkeys(candidate.epistemic_basis)),
        legality_status=_legality_status(candidate.permission_basis),
        temporal_validity=scaffold.temporal_validity,
        confidence=min(candidate.confidence, scaffold.confidence),
        downstream_scope="revoked_binding",
        authority_preserved=True,
        object_maturity_claim_blocked=bool(candidate.object_ref),
        provenance=tuple(dict.fromkeys((*candidate.provenance, *scaffold.provenance))),
    )
    return {
        "binding": binding,
        "blocked": A04BlockedCandidate(
            candidate_id=candidate.candidate_id,
            decision=A04NormalizationDecision.REVOKED_BINDING,
            reason=reason,
            contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
        ),
        "contested": None,
        "ledger": A04BindingLedgerEntry(
            entry_id=f"a04:{tick_id}:{tick_index}:ledger:{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            decision=A04NormalizationDecision.REVOKED_BINDING,
            status=A04BindingStatus.REVOKED,
            reason=reason,
            contradiction_refs=tuple(dict.fromkeys(candidate.contradiction_refs)),
            revocation_refs=tuple(dict.fromkeys((*candidate.revocation_refs, *scaffold.revocation_refs))),
        ),
        "authority_missing": False,
        "object_overclaim_blocked": bool(candidate.object_ref),
        "contradiction": False,
        "revoked": True,
    }


def _build_gate(
    *,
    ledger: A04BindingLedger,
    telemetry: A04Telemetry,
) -> A04ExternalAffordanceGateDecision:
    restrictions: list[str] = []
    binding_packet_consumer_ready = telemetry.a04_binding_count > 0
    authority_path_consumer_ready = ledger.authority_missing_count == 0
    consumer_ready = bool(
        binding_packet_consumer_ready
        and authority_path_consumer_ready
        and ledger.contradiction_count == 0
        and ledger.revoked_count == 0
    )

    status = A04DownstreamReadinessStatus.READY
    if not binding_packet_consumer_ready:
        restrictions.append("a04_binding_packet_not_ready")
        status = A04DownstreamReadinessStatus.MISSING_BINDING_PACKET_CONSUMER
    if not authority_path_consumer_ready:
        restrictions.append("a04_authority_path_missing")
        if status is A04DownstreamReadinessStatus.READY:
            status = A04DownstreamReadinessStatus.MISSING_AUTHORITY_PATH_CONSUMER
    if ledger.contested_count > 0:
        restrictions.append("a04_contested_scaffold_binding")
    if ledger.blocked_count > 0:
        restrictions.append("a04_blocked_external_affordance_binding")
    if ledger.revoked_count > 0:
        restrictions.append("a04_revoked_binding_present")
    if ledger.contradiction_count > 0:
        restrictions.append("a04_contradictory_scaffold_packets")
    if not consumer_ready:
        restrictions.append("a04_no_safe_external_affordance_claim")
        status = A04DownstreamReadinessStatus.NO_SAFE_DOWNSTREAM_EXTERNAL_AFFORDANCE_CLAIM

    return A04ExternalAffordanceGateDecision(
        accepted_count=ledger.accepted_count,
        contested_count=ledger.contested_count,
        blocked_count=ledger.blocked_count,
        revoked_count=ledger.revoked_count,
        authority_missing_count=ledger.authority_missing_count,
        object_overclaim_blocked_count=ledger.object_overclaim_blocked_count,
        contradiction_count=ledger.contradiction_count,
        binding_packet_consumer_ready=binding_packet_consumer_ready,
        authority_path_consumer_ready=authority_path_consumer_ready,
        consumer_ready=consumer_ready,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        downstream_readiness_status=status,
        no_map_wide_claim=True,
        staged_scaffold_only=True,
        reason="a04 gate exposes authority-scoped staged binding readiness for downstream external-affordance consumers",
    )


def _build_minimal_result(
    *,
    candidate_set_id: str,
    reason: str,
    restrictions: tuple[str, ...],
) -> A04ExternalAffordanceBindingResult:
    ledger = A04BindingLedger(
        ledger_id="a04:minimal:ledger",
        entries=(),
        accepted_count=0,
        contested_count=0,
        blocked_count=0,
        revoked_count=0,
        authority_missing_count=0,
        object_overclaim_blocked_count=0,
        contradiction_count=0,
        reason=reason,
    )
    telemetry = A04Telemetry(
        a04_binding_count=0,
        a04_contested_count=0,
        a04_blocked_count=0,
        a04_revoked_count=0,
        a04_authority_missing_count=0,
        a04_object_overclaim_blocked_count=0,
        a04_consumer_ready=False,
        a04_staged_scaffold_only=True,
        a04_no_map_wide_claim=True,
    )
    gate = A04ExternalAffordanceGateDecision(
        accepted_count=0,
        contested_count=0,
        blocked_count=0,
        revoked_count=0,
        authority_missing_count=0,
        object_overclaim_blocked_count=0,
        contradiction_count=0,
        binding_packet_consumer_ready=False,
        authority_path_consumer_ready=False,
        consumer_ready=False,
        required_restrictions=restrictions,
        downstream_readiness_status=A04DownstreamReadinessStatus.NO_SAFE_DOWNSTREAM_EXTERNAL_AFFORDANCE_CLAIM,
        no_map_wide_claim=True,
        staged_scaffold_only=True,
        reason=reason,
    )
    return A04ExternalAffordanceBindingResult(
        candidate_set_id=candidate_set_id,
        bindings=(),
        blocked_candidates=(),
        contested_candidates=(),
        ledger=ledger,
        gate=gate,
        telemetry=telemetry,
        scope_marker=A04ScopeMarker(
            scope="frontier_hosted_a04_external_affordance_binding_slice",
            frontier_only=True,
            narrow_slice_only=True,
            staged_scaffold_only=True,
            entity_binding_not_object_perception=True,
            no_map_wide_claim=True,
            no_execution_claim=True,
            no_policy_selection_claim=True,
            reason=reason,
        ),
        reason=reason,
    )


def _has_valid_authority(value: str) -> bool:
    return bool(str(value).strip())


def _has_admission_contradiction(scaffolds: list[A04WorldEntityScaffold]) -> bool:
    statuses = {item.admission_status for item in scaffolds}
    return bool(
        A04AdmissionStatus.REVOKED in statuses
        and (A04AdmissionStatus.ADMITTED in statuses or A04AdmissionStatus.PROVISIONAL in statuses)
    )


def _legality_status(permission_basis: tuple[str, ...]) -> A04LegalityStatus:
    lowered = {item.lower() for item in permission_basis}
    if "forbidden" in lowered or "blocked" in lowered:
        return A04LegalityStatus.FORBIDDEN
    if "restricted" in lowered:
        return A04LegalityStatus.RESTRICTED
    if "permitted" in lowered or "allowed" in lowered:
        return A04LegalityStatus.PERMITTED
    return A04LegalityStatus.UNKNOWN
