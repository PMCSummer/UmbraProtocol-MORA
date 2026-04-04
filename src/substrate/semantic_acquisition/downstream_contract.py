from __future__ import annotations

from dataclasses import dataclass

from substrate.semantic_acquisition.models import (
    AcquisitionStatus,
    AcquisitionUsabilityClass,
    SemanticAcquisitionBundle,
    SemanticAcquisitionResult,
)
from substrate.semantic_acquisition.policy import evaluate_semantic_acquisition_downstream_gate


@dataclass(frozen=True, slots=True)
class SemanticAcquisitionContractView:
    stable_provisional_present: bool
    weak_provisional_present: bool
    competing_provisional_present: bool
    blocked_pending_clarification_present: bool
    context_only_present: bool
    provisional_uptake_allowed: bool
    memory_uptake_allowed: bool
    closure_blocked_pending_clarification: bool
    competing_meanings_preserved: bool
    revision_hooks_required: bool
    context_only_output: bool
    usability_class: AcquisitionUsabilityClass
    restrictions: tuple[str, ...]
    requires_status_read: bool
    requires_restrictions_read: bool
    degraded_authority_present: bool
    accepted_degraded_requires_restrictions_read: bool
    accepted_provisional_not_commitment: bool
    strong_closure_permitted: bool
    reason: str


def derive_semantic_acquisition_contract_view(
    semantic_acquisition_result_or_bundle: SemanticAcquisitionResult | SemanticAcquisitionBundle,
) -> SemanticAcquisitionContractView:
    if isinstance(semantic_acquisition_result_or_bundle, SemanticAcquisitionResult):
        bundle = semantic_acquisition_result_or_bundle.bundle
    elif isinstance(semantic_acquisition_result_or_bundle, SemanticAcquisitionBundle):
        bundle = semantic_acquisition_result_or_bundle
    else:
        raise TypeError(
            "derive_semantic_acquisition_contract_view requires SemanticAcquisitionResult/SemanticAcquisitionBundle"
        )

    gate = evaluate_semantic_acquisition_downstream_gate(bundle)
    statuses = [record.acquisition_status for record in bundle.acquisition_records]
    all_permissions = [
        permission
        for record in bundle.acquisition_records
        for permission in record.downstream_permissions
    ]

    stable = AcquisitionStatus.STABLE_PROVISIONAL in statuses
    weak = AcquisitionStatus.WEAK_PROVISIONAL in statuses
    competing = AcquisitionStatus.COMPETING_PROVISIONAL in statuses
    blocked = AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION in statuses
    context_only = AcquisitionStatus.CONTEXT_ONLY in statuses

    provisional_uptake_allowed = "allow_provisional_semantic_uptake" in all_permissions
    memory_uptake_allowed = provisional_uptake_allowed and "memory_uptake_blocked" not in gate.restrictions
    closure_blocked = "closure_blocked_pending_clarification" in gate.restrictions
    competing_preserved = "competing_meanings_preserved" in gate.restrictions
    revision_hooks_required = "revision_hooks_must_be_read" in gate.restrictions
    context_output = "context_only_output" in gate.restrictions

    return SemanticAcquisitionContractView(
        stable_provisional_present=stable,
        weak_provisional_present=weak,
        competing_provisional_present=competing,
        blocked_pending_clarification_present=blocked,
        context_only_present=context_only,
        provisional_uptake_allowed=provisional_uptake_allowed,
        memory_uptake_allowed=memory_uptake_allowed,
        closure_blocked_pending_clarification=closure_blocked,
        competing_meanings_preserved=competing_preserved,
        revision_hooks_required=revision_hooks_required,
        context_only_output=context_output,
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_status_read=(
            "acquisition_status_must_be_read" in gate.restrictions
            and "restrictions_must_be_read" in gate.restrictions
        ),
        requires_restrictions_read=("restrictions_must_be_read" in gate.restrictions),
        degraded_authority_present=("downstream_authority_degraded" in gate.restrictions),
        accepted_degraded_requires_restrictions_read=(
            "accepted_degraded_requires_restrictions_read" in gate.restrictions
        ),
        accepted_provisional_not_commitment=("accepted_provisional_not_commitment" in gate.restrictions),
        strong_closure_permitted=False,
        reason="g05 contract view provides status-sensitive provisional acquisition constraints",
    )
