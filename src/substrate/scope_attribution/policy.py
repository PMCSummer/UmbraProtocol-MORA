from __future__ import annotations

from substrate.scope_attribution.models import (
    ApplicabilityBundle,
    ApplicabilityGateDecision,
    ApplicabilityResult,
    ApplicabilityUsabilityClass,
    SelfApplicabilityStatus,
)


def evaluate_applicability_downstream_gate(
    applicability_result_or_bundle: object,
) -> ApplicabilityGateDecision:
    if isinstance(applicability_result_or_bundle, ApplicabilityResult):
        bundle = applicability_result_or_bundle.bundle
    elif isinstance(applicability_result_or_bundle, ApplicabilityBundle):
        bundle = applicability_result_or_bundle
    else:
        raise TypeError(
            "applicability gate requires typed ApplicabilityResult/ApplicabilityBundle"
        )

    restrictions: list[str] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    if bundle.no_truth_upgrade:
        restrictions.append("no_truth_upgrade")
    if bundle.ambiguity_reasons:
        restrictions.append("mixed_or_unresolved_applicability")

    has_blocked_self = False
    has_unresolved = False
    has_external_only = False
    has_clarification = False
    has_actionable_permission = False
    for record in bundle.records:
        if record.confidence >= 0.2:
            accepted_ids.append(record.attribution_id)
        else:
            rejected_ids.append(record.attribution_id)
        if record.self_applicability_status in {
            SelfApplicabilityStatus.SELF_MENTIONED_BLOCKED,
            SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE,
        }:
            has_blocked_self = True
        if "block_self_state_update" in record.downstream_permissions:
            has_blocked_self = True
        if "recommend_clarification" in record.downstream_permissions:
            has_clarification = True
        if "allow_external_model_update" in record.downstream_permissions and "block_self_state_update" in record.downstream_permissions:
            has_external_only = True
        if (
            "allow_self_appraisal" in record.downstream_permissions
            or "allow_external_model_update" in record.downstream_permissions
        ):
            has_actionable_permission = True
        if record.self_applicability_status is SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE:
            has_unresolved = True

    if has_blocked_self:
        restrictions.append("self_state_update_blocked")
    if has_external_only:
        restrictions.append("external_only_handling")
    if has_clarification:
        restrictions.append("clarification_recommended")
    if has_unresolved:
        restrictions.append("unresolved_applicability")
    if bundle.records:
        restrictions.append("permissions_must_be_read")

    accepted = bool(accepted_ids)
    if not accepted:
        restrictions.append("no_usable_applicability_records")
        reason = "scope attribution produced no applicability records above confidence floor"
        usability_class = ApplicabilityUsabilityClass.BLOCKED
    else:
        reason = "typed applicability output emitted with bounded permissions"
        usability_class = ApplicabilityUsabilityClass.USABLE_BOUNDED

    degraded = (
        bundle.low_coverage_mode
        or has_unresolved
        or bool(bundle.ambiguity_reasons)
    )
    if accepted and not has_actionable_permission:
        degraded = True
        restrictions.append("bounded_context_only_output")
    if degraded:
        restrictions.append("downstream_authority_degraded")
    if degraded and accepted:
        usability_class = ApplicabilityUsabilityClass.DEGRADED_BOUNDED

    return ApplicabilityGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_record_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_record_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_runtime_graph_ref,
    )
