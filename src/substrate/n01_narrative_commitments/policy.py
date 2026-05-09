from __future__ import annotations

from substrate.n01_narrative_commitments.models import (
    N01CommitmentDecision,
    N01CommitmentEntry,
    N01CommitmentLedger,
    N01CommitmentScope,
    N01CommitmentStrength,
    N01ConflictStatus,
    N01DownstreamObligationKind,
    N01GateDecision,
    N01GroundingBasisKind,
    N01InputBundle,
    N01NarrativeClaimCandidate,
    N01NarrativeClaimKind,
    N01Result,
    N01RevisionAction,
    N01ScopeMarker,
    N01Telemetry,
)


def build_n01_narrative_commitments(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: N01InputBundle | None,
    commitments_enabled: bool = True,
) -> N01Result:
    if not commitments_enabled:
        return _minimal_result(
            bundle_id=f"n01:{tick_id}:bundle:none",
            reason="N01 gate disabled in test fixture",
            restrictions=("n01_disabled", "n01_no_clean_commitment_claim"),
        )

    if not isinstance(input_bundle, N01InputBundle):
        return _minimal_result(
            bundle_id=f"n01:{tick_id}:bundle:none",
            reason=(
                "n01 requires typed narrative claim candidates and support basis and does not treat raw prompt "
                "history repetition as commitment evidence by itself"
            ),
            restrictions=("insufficient_n01_basis", "n01_no_clean_commitment_claim"),
        )

    if not input_bundle.candidates:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="n01 received no typed narrative claim candidates",
            restrictions=("n01_no_typed_candidate", "n01_no_clean_commitment_claim"),
        )

    entries: list[N01CommitmentEntry] = []
    statement_only: list[N01NarrativeClaimCandidate] = []
    contested: list[N01CommitmentEntry] = []
    revised: list[N01CommitmentEntry] = []
    retired: list[N01CommitmentEntry] = []
    reason_codes: list[str] = []
    strong_count = 0
    provisional_count = 0
    statement_count = 0
    contested_count = 0
    revised_count = 0
    retired_count = 0
    scope_narrowed_count = 0
    ungrounded_capability_count = 0
    no_safe_count = 0

    existing_by_id = {item.commitment_id: item for item in input_bundle.existing_commitments}
    emitted_entries_by_id: dict[str, N01CommitmentEntry] = {}
    for item in input_bundle.existing_commitments:
        emitted_entries_by_id[item.commitment_id] = item

    for idx, candidate in enumerate(input_bundle.candidates):
        entry = _evaluate_candidate(
            tick_id=tick_id,
            tick_index=tick_index,
            index=idx,
            candidate=candidate,
            existing_by_id=existing_by_id,
            emitted_entries_by_id=emitted_entries_by_id,
            source_lineage=input_bundle.source_lineage,
        )
        entries.append(entry)
        emitted_entries_by_id[entry.commitment_id] = entry
        reason_codes.extend(entry.reason_codes)

        if entry.decision is N01CommitmentDecision.STATEMENT_ONLY_RECORD:
            statement_count += 1
            statement_only.append(candidate)
        if entry.decision is N01CommitmentDecision.CONTESTED_COMMITMENT:
            contested_count += 1
            contested.append(entry)
        if entry.decision is N01CommitmentDecision.REVISED_COMMITMENT:
            revised_count += 1
            revised.append(entry)
        if entry.decision is N01CommitmentDecision.RETIRED_COMMITMENT:
            retired_count += 1
            retired.append(entry)
        if entry.decision is N01CommitmentDecision.PROVISIONAL_COMMITMENT:
            provisional_count += 1
        if entry.decision is N01CommitmentDecision.CONFIRMED_COMMITMENT:
            strong_count += 1
        if entry.decision is N01CommitmentDecision.NO_CLEAN_COMMITMENT_CLAIM:
            no_safe_count += 1
        if "scope_narrowed_to_basis" in entry.reason_codes:
            scope_narrowed_count += 1
        if "ungrounded_capability_claim" in entry.reason_codes:
            ungrounded_capability_count += 1

    commitment_count = len(entries)
    consumer_ready = strong_count > 0 and contested_count == 0 and no_safe_count == 0
    telemetry = N01Telemetry(
        candidate_count=len(input_bundle.candidates),
        commitment_count=commitment_count,
        strong_commitment_count=strong_count,
        provisional_commitment_count=provisional_count,
        statement_only_count=statement_count,
        contested_commitment_count=contested_count,
        revised_count=revised_count,
        retired_count=retired_count,
        scope_narrowed_count=scope_narrowed_count,
        ungrounded_capability_claim_count=ungrounded_capability_count,
        consumer_ready=consumer_ready,
    )
    gate = _build_gate(
        telemetry=telemetry,
        entries=tuple(entries),
    )
    accepted_commitments = tuple(
        item
        for item in entries
        if item.decision in {
            N01CommitmentDecision.CONFIRMED_COMMITMENT,
            N01CommitmentDecision.PROVISIONAL_COMMITMENT,
        }
    )
    ledger = N01CommitmentLedger(
        accepted_commitments=accepted_commitments,
        statement_only_candidates=tuple(statement_only),
        contested_commitments=tuple(contested),
        revised_commitments=tuple(revised),
        retired_commitments=tuple(retired),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        no_safe_commit_count=no_safe_count,
        provenance=tuple(dict.fromkeys(input_bundle.source_lineage)),
    )

    return N01Result(
        bundle_id=input_bundle.bundle_id,
        commitment_entries=tuple(entries),
        ledger=ledger,
        telemetry=telemetry,
        gate=gate,
        scope_marker=N01ScopeMarker(
            scope="frontier_hosted_n01_narrative_commitment_registry_slice",
            frontier_only=True,
            narrow_slice_only=True,
            narrative_commitment_registry_only=True,
            no_identity_metaphysics_claim=True,
            no_full_autobiography_claim=True,
            no_memory_lifecycle_claim=True,
            no_policy_selection_claim=True,
            reason=(
                "n01 emits typed narrative commitment records with bounded strength/scope/support/revision "
                "and does not claim full autobiography, memory lifecycle, or policy authority"
            ),
        ),
        reason="n01 produced typed narrative commitment registry result",
    )


def _evaluate_candidate(
    *,
    tick_id: str,
    tick_index: int,
    index: int,
    candidate: N01NarrativeClaimCandidate,
    existing_by_id: dict[str, N01CommitmentEntry],
    emitted_entries_by_id: dict[str, N01CommitmentEntry],
    source_lineage: tuple[str, ...],
) -> N01CommitmentEntry:
    reason_codes: list[str] = []
    basis = set(candidate.grounding_basis)
    has_invalidated = N01GroundingBasisKind.INVALIDATED_BASIS in basis
    has_insufficient = N01GroundingBasisKind.INSUFFICIENT_BASIS in basis
    has_mixed = N01GroundingBasisKind.MIXED_OR_CONTESTED_BASIS in basis or candidate.mixed_cause_marker
    temporal_stale = candidate.temporal_validity_status in {"stale", "expired", "invalid", "contested"}
    has_continuity = (
        N01GroundingBasisKind.CONTINUITY_SUPPORT in basis
        or candidate.continuity_support
    )
    capability_support = (
        candidate.capability_support
        or candidate.affordance_support
        or candidate.internal_tool_support
        or N01GroundingBasisKind.CAPABILITY_AFFORDANCE_SUPPORT in basis
        or N01GroundingBasisKind.INTERNAL_TOOL_SUPPORT in basis
    )
    limitation_support = (
        candidate.limitation_support
        or candidate.gap_support
        or N01GroundingBasisKind.CAPABILITY_GAP_SUPPORT in basis
    )
    referenced_commitments = tuple(
        item
        for ref in candidate.existing_commitment_refs
        for item in ((emitted_entries_by_id.get(ref) or existing_by_id.get(ref)),)
        if item is not None
    )
    has_revision_support = bool(
        referenced_commitments
        and has_invalidated
        and any(
            value in basis
            for value in (
                N01GroundingBasisKind.INTERNAL_STATE_SUMMARY,
                N01GroundingBasisKind.TEMPORAL_VALIDITY_SUPPORT,
                N01GroundingBasisKind.SELF_ATTRIBUTION_SUPPORT,
                N01GroundingBasisKind.CAPABILITY_AFFORDANCE_SUPPORT,
                N01GroundingBasisKind.CAPABILITY_GAP_SUPPORT,
                N01GroundingBasisKind.INTERNAL_TOOL_SUPPORT,
                N01GroundingBasisKind.ACTIVE_MODE_SUPPORT,
                N01GroundingBasisKind.CONTINUITY_SUPPORT,
            )
        )
    )
    prior_decision = referenced_commitments[0].decision if referenced_commitments else None
    prior_validation_status = (
        referenced_commitments[0].validation_status if referenced_commitments else None
    )
    revision_reason: str | None = None

    scope, scope_changed = _bounded_scope(candidate.requested_scope, has_continuity=has_continuity)
    if scope_changed:
        reason_codes.append("scope_narrowed_to_basis")
        revision_action = N01RevisionAction.NARROW_SCOPE
    else:
        revision_action = N01RevisionAction.NO_REVISION_NEEDED

    conflict_status = _detect_conflict(candidate, existing_by_id=existing_by_id, emitted_by_id=emitted_entries_by_id)
    decision = N01CommitmentDecision.STATEMENT_ONLY_RECORD
    strength = N01CommitmentStrength.NONE
    validation_status = "statement_only"
    obligations: tuple[N01DownstreamObligationKind, ...] = (
        N01DownstreamObligationKind.NO_DOWNSTREAM_OBLIGATION,
    )

    if has_invalidated and candidate.existing_commitment_refs:
        if has_revision_support:
            decision = N01CommitmentDecision.REVISED_COMMITMENT
            strength = N01CommitmentStrength.PROVISIONAL
            revision_action = N01RevisionAction.REPLACE_WITH_EXPLICIT_REVISION
            validation_status = "revised_after_invalidated_basis"
            obligations = (
                N01DownstreamObligationKind.MUST_NOT_CLAIM_BEYOND_SCOPE,
                N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE,
                N01DownstreamObligationKind.MAY_BE_REVISED_ONLY_UNDER_CONDITION,
            )
            revision_reason = "explicit_revision_after_invalidated_basis"
            reason_codes.extend(
                (
                    "basis_invalidated",
                    "explicit_revision_applied",
                    "prior_status_replaced",
                )
            )
            if prior_decision is not None:
                reason_codes.append(f"prior_decision:{prior_decision.value}")
            if prior_validation_status:
                reason_codes.append(f"prior_validation_status:{prior_validation_status}")
        else:
            decision = N01CommitmentDecision.RETIRED_COMMITMENT
            strength = N01CommitmentStrength.NONE
            revision_action = N01RevisionAction.RETRACT
            validation_status = "retired_due_to_invalidated_basis"
            obligations = (
                N01DownstreamObligationKind.MUST_SURFACE_CONTRADICTION,
                N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE,
            )
            revision_reason = "invalidated_basis_without_replacement_support"
            reason_codes.append("basis_invalidated")
    elif conflict_status is not N01ConflictStatus.NO_CONFLICT:
        decision = N01CommitmentDecision.CONTESTED_COMMITMENT
        strength = N01CommitmentStrength.CONTESTED
        revision_action = N01RevisionAction.MARK_CONTESTED
        validation_status = "contested"
        obligations = (
            N01DownstreamObligationKind.MUST_SURFACE_CONTRADICTION,
            N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE,
        )
        reason_codes.append("conflict_detected")
        if candidate.conflict_marker and not candidate.existing_commitment_refs:
            reason_codes.append("unreferenced_conflict_marker")
    elif candidate.claim_kind is N01NarrativeClaimKind.CAPABILITY_CLAIM and not capability_support:
        decision = N01CommitmentDecision.STATEMENT_ONLY_RECORD
        strength = N01CommitmentStrength.NONE
        validation_status = "ungrounded_capability_claim"
        reason_codes.append("ungrounded_capability_claim")
    elif candidate.claim_kind is N01NarrativeClaimKind.LIMITATION_CLAIM and not limitation_support:
        decision = N01CommitmentDecision.STATEMENT_ONLY_RECORD
        strength = N01CommitmentStrength.NONE
        validation_status = "ungrounded_limitation_claim"
        reason_codes.append("ungrounded_limitation_claim")
    elif has_insufficient:
        decision = N01CommitmentDecision.NO_CLEAN_COMMITMENT_CLAIM
        strength = N01CommitmentStrength.NONE
        validation_status = "insufficient_basis"
        obligations = (
            N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE,
        )
        reason_codes.append("insufficient_basis")
    elif has_mixed or temporal_stale or candidate.self_side_confidence < 0.55:
        decision = N01CommitmentDecision.PROVISIONAL_COMMITMENT
        strength = N01CommitmentStrength.PROVISIONAL
        validation_status = "provisional"
        revision_action = N01RevisionAction.REQUIRE_REVALIDATION_BEFORE_REUSE
        obligations = (
            N01DownstreamObligationKind.MUST_NOT_CLAIM_BEYOND_SCOPE,
            N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE,
            N01DownstreamObligationKind.MAY_BE_REVISED_ONLY_UNDER_CONDITION,
        )
        if has_mixed:
            reason_codes.append("mixed_support_basis")
        if temporal_stale:
            reason_codes.append("stale_temporal_basis")
        if candidate.self_side_confidence < 0.55:
            reason_codes.append("low_self_side_confidence")
    else:
        decision = N01CommitmentDecision.CONFIRMED_COMMITMENT
        strength = N01CommitmentStrength.STRONG
        validation_status = "confirmed"
        obligations = (
            N01DownstreamObligationKind.MUST_REMAIN_CONSISTENT_IN_SELF_REPORT,
            N01DownstreamObligationKind.MUST_NOT_CLAIM_BEYOND_SCOPE,
            N01DownstreamObligationKind.MUST_CONSTRAIN_FUTURE_EXPLANATION,
        )
        if candidate.claim_kind in {
            N01NarrativeClaimKind.VALUE_LIKE_STANCE,
            N01NarrativeClaimKind.RELATION_CLAIM,
        }:
            decision = N01CommitmentDecision.PROVISIONAL_COMMITMENT
            strength = N01CommitmentStrength.PROVISIONAL
            validation_status = "provisional_relation_or_value_scope"
            obligations = (
                N01DownstreamObligationKind.MUST_NOT_CLAIM_BEYOND_SCOPE,
                N01DownstreamObligationKind.MUST_TRIGGER_RECHECK_BEFORE_REUSE,
            )
            reason_codes.append("relation_or_value_claim_capped")
        if candidate.claim_kind is N01NarrativeClaimKind.STATE_DESCRIPTION and not has_continuity:
            strength = N01CommitmentStrength.MODERATE
            reason_codes.append("bounded_state_commitment")
        if candidate.claim_kind is N01NarrativeClaimKind.INTENTION_CLAIM and not (
            candidate.active_mode_support or N01GroundingBasisKind.ACTIVE_MODE_SUPPORT in basis
        ):
            decision = N01CommitmentDecision.PROVISIONAL_COMMITMENT
            strength = N01CommitmentStrength.PROVISIONAL
            validation_status = "provisional_intention_support"
            reason_codes.append("intention_support_incomplete")

    if not reason_codes:
        reason_codes.append(decision.value)

    confidence = _derive_confidence(
        decision=decision,
        self_side_confidence=candidate.self_side_confidence,
        temporal_stale=temporal_stale,
        has_mixed=has_mixed,
    )

    return N01CommitmentEntry(
        commitment_id=f"n01:{tick_id}:{tick_index}:commitment:{candidate.candidate_id}:{index}",
        source_candidate_id=candidate.candidate_id,
        claim_kind=candidate.claim_kind,
        semantic_content=candidate.claim_text_or_semantic_form,
        strength=strength,
        scope=scope,
        grounding_basis=candidate.grounding_basis,
        temporal_horizon=scope.value,
        addressee_or_audience_scope=candidate.addressee_or_audience_scope,
        referenced_commitment_refs=candidate.existing_commitment_refs,
        revision_conditions=("support_basis_change", "scope_change", "conflict_detected"),
        invalidation_triggers=("invalidated_basis", "explicit_retraction", "scope_violation"),
        conflict_status=conflict_status,
        conflict_priority=2 if conflict_status is not N01ConflictStatus.NO_CONFLICT else 0,
        downstream_obligations=obligations,
        validation_status=validation_status,
        confidence=confidence,
        decision=decision,
        revision_action=revision_action,
        prior_decision=prior_decision,
        prior_validation_status=prior_validation_status,
        revision_reason=revision_reason,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        provenance=tuple(dict.fromkeys((*source_lineage, *candidate.provenance, candidate.candidate_id))),
    )


def _bounded_scope(
    requested_scope: N01CommitmentScope,
    *,
    has_continuity: bool,
) -> tuple[N01CommitmentScope, bool]:
    if requested_scope is N01CommitmentScope.GLOBAL_FORBIDDEN_UNLESS_EXPLICITLY_GROUNDED:
        return (
            N01CommitmentScope.LONG_HORIZON if has_continuity else N01CommitmentScope.DIALOGUE_LOCAL,
            True,
        )
    if requested_scope is N01CommitmentScope.LONG_HORIZON and not has_continuity:
        return N01CommitmentScope.SHORT_HORIZON, True
    return requested_scope, False


def _detect_conflict(
    candidate: N01NarrativeClaimCandidate,
    *,
    existing_by_id: dict[str, N01CommitmentEntry],
    emitted_by_id: dict[str, N01CommitmentEntry],
) -> N01ConflictStatus:
    refs = tuple(dict.fromkeys((*candidate.existing_commitment_refs,)))
    if not refs and candidate.conflict_marker:
        return N01ConflictStatus.UNRESOLVED_NARRATIVE_TENSION
    if not refs:
        return N01ConflictStatus.NO_CONFLICT
    normalized_candidate = _normalize(candidate.claim_text_or_semantic_form)
    for ref in refs:
        existing = emitted_by_id.get(ref) or existing_by_id.get(ref)
        if existing is None:
            continue
        normalized_existing = _normalize(existing.semantic_content)
        if normalized_existing == normalized_candidate:
            continue
        if existing.strength in {N01CommitmentStrength.STRONG, N01CommitmentStrength.MODERATE}:
            return N01ConflictStatus.CONTRADICTS_EXISTING_STRONG
        if existing.strength in {N01CommitmentStrength.PROVISIONAL, N01CommitmentStrength.WEAK}:
            return N01ConflictStatus.CONTRADICTS_EXISTING_PROVISIONAL
        return N01ConflictStatus.UNRESOLVED_NARRATIVE_TENSION
    return N01ConflictStatus.NO_CONFLICT


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _derive_confidence(
    *,
    decision: N01CommitmentDecision,
    self_side_confidence: float,
    temporal_stale: bool,
    has_mixed: bool,
) -> float:
    base = max(0.0, min(1.0, self_side_confidence))
    if temporal_stale:
        base *= 0.65
    if has_mixed:
        base *= 0.75
    if decision in {
        N01CommitmentDecision.STATEMENT_ONLY_RECORD,
        N01CommitmentDecision.NO_CLEAN_COMMITMENT_CLAIM,
    }:
        base *= 0.6
    if decision in {
        N01CommitmentDecision.CONTESTED_COMMITMENT,
        N01CommitmentDecision.RETIRED_COMMITMENT,
    }:
        base *= 0.55
    return round(max(0.0, min(1.0, base)), 4)


def _build_gate(
    *,
    telemetry: N01Telemetry,
    entries: tuple[N01CommitmentEntry, ...],
) -> N01GateDecision:
    restrictions: list[str] = []
    reason_codes: list[str] = []

    if telemetry.commitment_count == 0:
        restrictions.append("n01_no_commitment_entries")
        reason_codes.append("no_commitment_entries")
    if telemetry.ungrounded_capability_claim_count > 0:
        restrictions.append("n01_ungrounded_capability_claim")
        reason_codes.append("ungrounded_capability_claim")
    if telemetry.contested_commitment_count > 0:
        restrictions.append("n01_contested_commitment_present")
        reason_codes.append("contested_commitment_present")
    if telemetry.scope_narrowed_count > 0:
        restrictions.append("n01_scope_narrowed_to_basis")
        reason_codes.append("scope_narrowed_to_basis")

    consistency_ready = all(
        N01DownstreamObligationKind.MUST_NOT_CLAIM_BEYOND_SCOPE in item.downstream_obligations
        or item.decision in {
            N01CommitmentDecision.STATEMENT_ONLY_RECORD,
            N01CommitmentDecision.NO_CLEAN_COMMITMENT_CLAIM,
        }
        for item in entries
    ) if entries else False
    consumer_ready = bool(
        telemetry.strong_commitment_count > 0
        and telemetry.contested_commitment_count == 0
        and telemetry.ungrounded_capability_claim_count == 0
    )
    if not consumer_ready:
        restrictions.append("n01_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    return N01GateDecision(
        consumer_ready=consumer_ready,
        consistency_consumer_ready=consistency_ready,
        strong_commitment_count=telemetry.strong_commitment_count,
        provisional_commitment_count=telemetry.provisional_commitment_count,
        statement_only_count=telemetry.statement_only_count,
        contested_commitment_count=telemetry.contested_commitment_count,
        revised_or_retired_count=telemetry.revised_count + telemetry.retired_count,
        scope_narrowed_count=telemetry.scope_narrowed_count,
        ungrounded_capability_claim_count=telemetry.ungrounded_capability_claim_count,
        required_restrictions=tuple(dict.fromkeys(restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="n01 gate preserves commitment-scope and support-basis discipline",
    )


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> N01Result:
    telemetry = N01Telemetry(
        candidate_count=0,
        commitment_count=0,
        strong_commitment_count=0,
        provisional_commitment_count=0,
        statement_only_count=0,
        contested_commitment_count=0,
        revised_count=0,
        retired_count=0,
        scope_narrowed_count=0,
        ungrounded_capability_claim_count=0,
        consumer_ready=False,
    )
    gate = N01GateDecision(
        consumer_ready=False,
        consistency_consumer_ready=False,
        strong_commitment_count=0,
        provisional_commitment_count=0,
        statement_only_count=0,
        contested_commitment_count=0,
        revised_or_retired_count=0,
        scope_narrowed_count=0,
        ungrounded_capability_claim_count=0,
        required_restrictions=restrictions,
        reason_codes=("no_clean_commitment_claim",),
        reason=reason,
    )
    ledger = N01CommitmentLedger(
        accepted_commitments=(),
        statement_only_candidates=(),
        contested_commitments=(),
        revised_commitments=(),
        retired_commitments=(),
        reason_codes=("no_clean_commitment_claim",),
        no_safe_commit_count=1,
        provenance=(),
    )
    return N01Result(
        bundle_id=bundle_id,
        commitment_entries=(),
        ledger=ledger,
        telemetry=telemetry,
        gate=gate,
        scope_marker=N01ScopeMarker(
            scope="frontier_hosted_n01_narrative_commitment_registry_slice",
            frontier_only=True,
            narrow_slice_only=True,
            narrative_commitment_registry_only=True,
            no_identity_metaphysics_claim=True,
            no_full_autobiography_claim=True,
            no_memory_lifecycle_claim=True,
            no_policy_selection_claim=True,
            reason=reason,
        ),
        reason=reason,
    )
