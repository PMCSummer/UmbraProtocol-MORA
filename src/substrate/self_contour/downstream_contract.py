from __future__ import annotations

from dataclasses import dataclass

from substrate.self_contour.models import SMinimalContourResult


@dataclass(frozen=True, slots=True)
class SMinimalContourContractView:
    boundary_state_id: str
    attribution_class: str
    source_status: str
    self_attribution_basis_present: bool
    world_attribution_basis_present: bool
    controllability_estimate: float
    ownership_estimate: float
    attribution_confidence: float
    boundary_breach_risk: str
    degraded: bool
    underconstrained: bool
    self_owned_state_claim_allowed: bool
    self_caused_change_claim_allowed: bool
    self_controlled_transition_claim_allowed: bool
    externally_caused_change_claim_allowed: bool
    world_caused_perturbation_claim_allowed: bool
    no_safe_self_claim: bool
    no_safe_world_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    s01_admission_ready: bool
    future_s01_s05_remain_open: bool
    full_self_model_implemented: bool
    scope: str
    scope_minimal_contour_only: bool
    scope_s01_s05_implemented: bool
    scope_full_self_model_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    requires_restrictions_read: bool
    reason: str


def derive_s_minimal_contour_contract_view(
    result: SMinimalContourResult,
) -> SMinimalContourContractView:
    if not isinstance(result, SMinimalContourResult):
        raise TypeError("derive_s_minimal_contour_contract_view requires SMinimalContourResult")
    return SMinimalContourContractView(
        boundary_state_id=result.state.boundary_state_id,
        attribution_class=result.state.attribution_class.value,
        source_status=result.state.internal_vs_external_source_status.value,
        self_attribution_basis_present=result.state.self_attribution_basis_present,
        world_attribution_basis_present=result.state.world_attribution_basis_present,
        controllability_estimate=result.state.controllability_estimate,
        ownership_estimate=result.state.ownership_estimate,
        attribution_confidence=result.state.attribution_confidence,
        boundary_breach_risk=result.state.boundary_breach_risk.value,
        degraded=result.state.degraded,
        underconstrained=result.state.underconstrained,
        self_owned_state_claim_allowed=result.gate.self_owned_state_claim_allowed,
        self_caused_change_claim_allowed=result.gate.self_caused_change_claim_allowed,
        self_controlled_transition_claim_allowed=result.gate.self_controlled_transition_claim_allowed,
        externally_caused_change_claim_allowed=result.gate.externally_caused_change_claim_allowed,
        world_caused_perturbation_claim_allowed=result.gate.world_caused_perturbation_claim_allowed,
        no_safe_self_claim=result.gate.no_safe_self_claim,
        no_safe_world_claim=result.gate.no_safe_world_claim,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        s01_admission_ready=result.admission.admission_ready_for_s01,
        future_s01_s05_remain_open=result.admission.future_s01_s05_remain_open,
        full_self_model_implemented=result.admission.full_self_model_implemented,
        scope=result.scope_marker.scope,
        scope_minimal_contour_only=result.scope_marker.minimal_contour_only,
        scope_s01_s05_implemented=result.scope_marker.s01_s05_implemented,
        scope_full_self_model_implemented=result.scope_marker.full_self_model_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        requires_restrictions_read=True,
        reason=result.gate.reason,
    )
