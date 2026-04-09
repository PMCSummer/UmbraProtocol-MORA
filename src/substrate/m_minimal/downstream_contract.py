from __future__ import annotations

from dataclasses import dataclass

from substrate.m_minimal.models import MMinimalResult


@dataclass(frozen=True, slots=True)
class MMinimalContractView:
    memory_item_id: str
    memory_packet_id: str
    lifecycle_status: str
    retention_class: str
    bounded_persistence_allowed: bool
    temporary_carry_allowed: bool
    review_required: bool
    reactivation_eligible: bool
    decay_eligible: bool
    pruning_eligible: bool
    stale_risk: str
    conflict_risk: str
    confidence: float
    reliability: str
    degraded: bool
    underconstrained: bool
    safe_memory_claim_allowed: bool
    bounded_retained_claim_allowed: bool
    no_safe_memory_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    m01_admission_ready: bool
    m01_blockers: tuple[str, ...]
    m01_structurally_present_but_not_ready: bool
    m01_stale_risk_unacceptable: bool
    m01_conflict_risk_unacceptable: bool
    m01_reactivation_requires_review: bool
    m01_temporary_carry_not_stable_enough: bool
    m01_no_safe_memory_basis: bool
    m01_provenance_insufficient: bool
    m01_lifecycle_underconstrained: bool
    m01_implemented: bool
    m02_implemented: bool
    m03_implemented: bool
    scope: str
    scope_rt01_contour_only: bool
    scope_m_minimal_only: bool
    scope_readiness_gate_only: bool
    scope_m01_implemented: bool
    scope_m02_implemented: bool
    scope_m03_implemented: bool
    scope_full_memory_stack_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    requires_restrictions_read: bool
    reason: str


def derive_m_minimal_contract_view(result: MMinimalResult) -> MMinimalContractView:
    if not isinstance(result, MMinimalResult):
        raise TypeError("derive_m_minimal_contract_view requires MMinimalResult")
    return MMinimalContractView(
        memory_item_id=result.state.memory_item_id,
        memory_packet_id=result.state.memory_packet_id,
        lifecycle_status=result.state.lifecycle_status.value,
        retention_class=result.state.retention_class.value,
        bounded_persistence_allowed=result.state.bounded_persistence_allowed,
        temporary_carry_allowed=result.state.temporary_carry_allowed,
        review_required=result.state.review_required,
        reactivation_eligible=result.state.reactivation_eligible,
        decay_eligible=result.state.decay_eligible,
        pruning_eligible=result.state.pruning_eligible,
        stale_risk=result.state.stale_risk.value,
        conflict_risk=result.state.conflict_risk.value,
        confidence=result.state.confidence,
        reliability=result.state.reliability,
        degraded=result.state.degraded,
        underconstrained=result.state.underconstrained,
        safe_memory_claim_allowed=result.gate.safe_memory_claim_allowed,
        bounded_retained_claim_allowed=result.gate.bounded_retained_claim_allowed,
        no_safe_memory_claim=result.gate.no_safe_memory_claim,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        m01_admission_ready=result.admission.admission_ready_for_m01,
        m01_blockers=result.admission.blockers,
        m01_structurally_present_but_not_ready=result.admission.structurally_present_but_not_ready,
        m01_stale_risk_unacceptable=result.admission.stale_risk_unacceptable,
        m01_conflict_risk_unacceptable=result.admission.conflict_risk_unacceptable,
        m01_reactivation_requires_review=result.admission.reactivation_requires_review,
        m01_temporary_carry_not_stable_enough=result.admission.temporary_carry_not_stable_enough,
        m01_no_safe_memory_basis=result.admission.no_safe_memory_basis,
        m01_provenance_insufficient=result.admission.provenance_insufficient,
        m01_lifecycle_underconstrained=result.admission.lifecycle_underconstrained,
        m01_implemented=result.admission.m01_implemented,
        m02_implemented=result.admission.m02_implemented,
        m03_implemented=result.admission.m03_implemented,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_m_minimal_only=result.scope_marker.m_minimal_only,
        scope_readiness_gate_only=result.scope_marker.readiness_gate_only,
        scope_m01_implemented=result.scope_marker.m01_implemented,
        scope_m02_implemented=result.scope_marker.m02_implemented,
        scope_m03_implemented=result.scope_marker.m03_implemented,
        scope_full_memory_stack_implemented=result.scope_marker.full_memory_stack_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        requires_restrictions_read=True,
        reason=result.gate.reason,
    )
