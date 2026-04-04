from __future__ import annotations

from dataclasses import dataclass

from substrate.scope_attribution.models import (
    ApplicabilityBundle,
    ApplicabilityResult,
    ApplicabilityUsabilityClass,
)
from substrate.scope_attribution.policy import evaluate_applicability_downstream_gate


@dataclass(frozen=True, slots=True)
class ApplicabilityContractView:
    self_update_allowed: bool
    self_update_blocked: bool
    external_only_routing: bool
    clarification_recommended: bool
    narrative_deferred: bool
    mixed_or_unresolved_present: bool
    context_only_mode: bool
    degraded_handling_required: bool
    usability_class: ApplicabilityUsabilityClass
    restrictions: tuple[str, ...]
    requires_permission_read: bool
    requires_restriction_read: bool
    strong_self_state_commitment_permitted: bool
    reason: str


def derive_applicability_contract_view(
    applicability_result_or_bundle: ApplicabilityResult | ApplicabilityBundle,
) -> ApplicabilityContractView:
    if isinstance(applicability_result_or_bundle, ApplicabilityResult):
        bundle = applicability_result_or_bundle.bundle
    elif isinstance(applicability_result_or_bundle, ApplicabilityBundle):
        bundle = applicability_result_or_bundle
    else:
        raise TypeError(
            "derive_applicability_contract_view requires ApplicabilityResult/ApplicabilityBundle"
        )

    gate = evaluate_applicability_downstream_gate(bundle)
    all_permissions = [permission for record in bundle.records for permission in record.downstream_permissions]
    self_update_allowed = "allow_self_appraisal" in all_permissions
    self_update_blocked = "block_self_state_update" in all_permissions
    external_only_routing = "allow_external_model_update" in all_permissions and not self_update_allowed
    clarification_recommended = "recommend_clarification" in all_permissions
    narrative_deferred = "defer_narrative_binding" in all_permissions
    mixed_or_unresolved_present = bool(
        "mixed_or_unresolved_applicability" in gate.restrictions
        or "unresolved_applicability" in gate.restrictions
    )
    context_only_mode = "bounded_context_only_output" in gate.restrictions
    degraded_handling_required = gate.usability_class is not ApplicabilityUsabilityClass.USABLE_BOUNDED
    return ApplicabilityContractView(
        self_update_allowed=self_update_allowed,
        self_update_blocked=self_update_blocked,
        external_only_routing=external_only_routing,
        clarification_recommended=clarification_recommended,
        narrative_deferred=narrative_deferred,
        mixed_or_unresolved_present=mixed_or_unresolved_present,
        context_only_mode=context_only_mode,
        degraded_handling_required=degraded_handling_required,
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_permission_read="permissions_must_be_read" in gate.restrictions,
        requires_restriction_read=True,
        strong_self_state_commitment_permitted=False,
        reason="g03 contract view provides permission-sensitive bounded routing surface",
    )
