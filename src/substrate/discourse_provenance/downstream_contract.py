from __future__ import annotations

from dataclasses import dataclass

from substrate.discourse_provenance.models import (
    PerspectiveChainBundle,
    PerspectiveChainResult,
    ProvenanceUsabilityClass,
)
from substrate.discourse_provenance.policy import evaluate_perspective_chain_downstream_gate


@dataclass(frozen=True, slots=True)
class PerspectiveChainContractView:
    closure_requires_chain_consistency_check: bool
    response_should_not_echo_as_direct_user_belief: bool
    clarification_recommended_on_owner_ambiguity: bool
    narrative_binding_blocked_without_commitment_owner: bool
    response_should_not_flatten_owner: bool
    cross_turn_repair_pending: bool
    owner_flattening_risk_detected: bool
    usability_class: ProvenanceUsabilityClass
    restrictions: tuple[str, ...]
    requires_chain_read: bool
    requires_usability_read: bool
    strong_owner_commitment_permitted: bool
    accepted_chain_not_owner_truth: bool
    reason: str


def derive_perspective_chain_contract_view(
    perspective_chain_result_or_bundle: PerspectiveChainResult | PerspectiveChainBundle,
) -> PerspectiveChainContractView:
    if isinstance(perspective_chain_result_or_bundle, PerspectiveChainResult):
        bundle = perspective_chain_result_or_bundle.bundle
    elif isinstance(perspective_chain_result_or_bundle, PerspectiveChainBundle):
        bundle = perspective_chain_result_or_bundle
    else:
        raise TypeError(
            "derive_perspective_chain_contract_view requires PerspectiveChainResult/PerspectiveChainBundle"
        )

    gate = evaluate_perspective_chain_downstream_gate(bundle)
    all_constraints = [
        constraint
        for wrapped in bundle.wrapped_propositions
        for constraint in wrapped.downstream_constraints
    ]
    closure_requires_chain_consistency_check = (
        "closure_requires_chain_consistency_check" in all_constraints
        or "chain_consistency_required" in gate.restrictions
    )
    response_should_not_echo_as_direct_user_belief = (
        "response_should_not_echo_as_direct_user_belief" in all_constraints
    )
    clarification_recommended_on_owner_ambiguity = (
        "clarification_recommended_on_owner_ambiguity" in all_constraints
        or "owner_ambiguity_present" in gate.restrictions
    )
    narrative_binding_blocked_without_commitment_owner = (
        "narrative_binding_blocked_without_commitment_owner" in all_constraints
    )
    response_should_not_flatten_owner = (
        "response_should_not_flatten_owner" in all_constraints
        or "response_should_not_flatten_owner" in gate.restrictions
    )
    cross_turn_repair_pending = "cross_turn_repair_pending" in gate.restrictions
    owner_flattening_risk_detected = bool(
        response_should_not_flatten_owner
        or "broken_provenance_chain" in gate.restrictions
        or "owner_ambiguity_present" in gate.restrictions
    )
    return PerspectiveChainContractView(
        closure_requires_chain_consistency_check=closure_requires_chain_consistency_check,
        response_should_not_echo_as_direct_user_belief=response_should_not_echo_as_direct_user_belief,
        clarification_recommended_on_owner_ambiguity=clarification_recommended_on_owner_ambiguity,
        narrative_binding_blocked_without_commitment_owner=narrative_binding_blocked_without_commitment_owner,
        response_should_not_flatten_owner=response_should_not_flatten_owner,
        cross_turn_repair_pending=cross_turn_repair_pending,
        owner_flattening_risk_detected=owner_flattening_risk_detected,
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_chain_read="perspective_chain_must_be_read" in gate.restrictions,
        requires_usability_read="usability_must_be_read" in gate.restrictions,
        strong_owner_commitment_permitted=False,
        accepted_chain_not_owner_truth="accepted_chain_not_owner_truth" in gate.restrictions,
        reason="g04 contract view provides provenance-chain-sensitive downstream constraints",
    )
