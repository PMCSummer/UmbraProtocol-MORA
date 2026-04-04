from __future__ import annotations

from substrate.discourse_provenance.models import (
    CrossTurnAttachmentState,
    PerspectiveChainBundle,
    PerspectiveChainGateDecision,
    PerspectiveChainResult,
    PerspectiveOwnerClass,
    ProvenanceUsabilityClass,
)


def evaluate_perspective_chain_downstream_gate(
    perspective_chain_result_or_bundle: object,
) -> PerspectiveChainGateDecision:
    if isinstance(perspective_chain_result_or_bundle, PerspectiveChainResult):
        bundle = perspective_chain_result_or_bundle.bundle
    elif isinstance(perspective_chain_result_or_bundle, PerspectiveChainBundle):
        bundle = perspective_chain_result_or_bundle
    else:
        raise TypeError(
            "perspective chain gate requires typed PerspectiveChainResult/PerspectiveChainBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_truth_upgrade:
        restrictions.append("no_truth_upgrade")

    has_owner_ambiguity = False
    has_broken_chain = False
    has_response_nonflattening = False
    has_chain_consistency_requirement = False
    has_cross_turn_repair_pending = False
    has_shallow_owner_risk = False

    for record in bundle.chain_records:
        if record.confidence >= 0.2:
            accepted_ids.append(record.chain_id)
        else:
            rejected_ids.append(record.chain_id)

        if record.commitment_owner in {
            PerspectiveOwnerClass.MIXED_OWNER,
            PerspectiveOwnerClass.UNRESOLVED_OWNER,
        }:
            has_owner_ambiguity = True
        if record.discourse_level > 1:
            has_chain_consistency_requirement = True
        if record.discourse_level <= 1 and record.assertion_mode.value in {
            "mixed",
            "unresolved",
            "hypothetical_branch",
            "question_frame",
            "denial_frame",
        }:
            has_shallow_owner_risk = True

    for wrapped in bundle.wrapped_propositions:
        if "response_should_not_flatten_owner" in wrapped.downstream_constraints:
            has_response_nonflattening = True
        if "closure_requires_chain_consistency_check" in wrapped.downstream_constraints:
            has_chain_consistency_requirement = True
        if (
            "clarification_recommended_on_owner_ambiguity" in wrapped.downstream_constraints
            or "narrative_binding_blocked_without_commitment_owner" in wrapped.downstream_constraints
        ):
            has_owner_ambiguity = True

    for link in bundle.cross_turn_links:
        if link.attachment_state is CrossTurnAttachmentState.REPAIR_PENDING:
            has_cross_turn_repair_pending = True

    if bundle.ambiguity_reasons:
        has_broken_chain = any(
            reason in bundle.ambiguity_reasons
            for reason in (
                "mixed_provenance",
                "broken_quote_chain",
                "unresolved_commitment_owner",
                "ambiguous_perspective_depth",
                "discourse_anchor_missing",
            )
        )

    if has_chain_consistency_requirement:
        restrictions.append("chain_consistency_required")
    if has_owner_ambiguity:
        restrictions.append("owner_ambiguity_present")
    if has_broken_chain:
        restrictions.append("broken_provenance_chain")
    if has_cross_turn_repair_pending:
        restrictions.append("cross_turn_repair_pending")
    if has_response_nonflattening:
        restrictions.append("response_should_not_flatten_owner")
    if has_shallow_owner_risk:
        restrictions.append("shallow_owner_chain_risk")
    if bundle.chain_records:
        restrictions.append("perspective_chain_must_be_read")
        restrictions.append("usability_must_be_read")

    accepted = bool(accepted_ids)
    if not accepted:
        restrictions.append("no_usable_perspective_chain_records")
        usability_class = ProvenanceUsabilityClass.BLOCKED
        reason = "discourse provenance produced no chain records above confidence floor"
    else:
        usability_class = ProvenanceUsabilityClass.USABLE_BOUNDED
        reason = "typed discourse provenance chain emitted with bounded ownership constraints"
        restrictions.append("accepted_chain_not_owner_truth")

    degraded = (
        bundle.low_coverage_mode
        or has_owner_ambiguity
        or has_broken_chain
        or has_cross_turn_repair_pending
        or has_shallow_owner_risk
    )
    if degraded:
        restrictions.append("downstream_authority_degraded")
    if degraded and accepted:
        usability_class = ProvenanceUsabilityClass.DEGRADED_BOUNDED

    return PerspectiveChainGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_chain_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_chain_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_applicability_ref,
    )
