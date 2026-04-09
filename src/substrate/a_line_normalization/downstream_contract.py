from __future__ import annotations

from dataclasses import dataclass

from substrate.a_line_normalization.models import ALineNormalizationResult


@dataclass(frozen=True, slots=True)
class ALineNormalizationContractView:
    capability_id: str
    affordance_id: str
    capability_class: str
    capability_status: str
    availability_basis_present: bool
    world_dependency_present: bool
    self_dependency_present: bool
    controllability_dependency_present: bool
    legitimacy_dependency_present: bool
    confidence: float
    degraded: bool
    underconstrained: bool
    available_capability_claim_allowed: bool
    world_conditioned_capability_claim_allowed: bool
    self_conditioned_capability_claim_allowed: bool
    policy_conditioned_capability_present: bool
    underconstrained_capability: bool
    no_safe_capability_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    a04_admission_ready: bool
    a04_blockers: tuple[str, ...]
    a04_structurally_present_but_not_ready: bool
    a04_capability_basis_missing: bool
    a04_world_dependency_unmet: bool
    a04_self_dependency_unmet: bool
    a04_policy_legitimacy_unmet: bool
    a04_underconstrained_capability_surface: bool
    a04_external_means_not_justified: bool
    a04_implemented: bool
    a05_touched: bool
    scope: str
    scope_rt01_contour_only: bool
    scope_a_line_normalization_only: bool
    scope_readiness_gate_only: bool
    scope_a04_implemented: bool
    scope_a05_touched: bool
    scope_full_agency_stack_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    requires_restrictions_read: bool
    reason: str


def derive_a_line_normalization_contract_view(
    result: ALineNormalizationResult,
) -> ALineNormalizationContractView:
    if not isinstance(result, ALineNormalizationResult):
        raise TypeError(
            "derive_a_line_normalization_contract_view requires ALineNormalizationResult"
        )
    return ALineNormalizationContractView(
        capability_id=result.state.capability_id,
        affordance_id=result.state.affordance_id,
        capability_class=result.state.capability_class.value,
        capability_status=result.state.capability_status.value,
        availability_basis_present=result.state.availability_basis_present,
        world_dependency_present=result.state.world_dependency_present,
        self_dependency_present=result.state.self_dependency_present,
        controllability_dependency_present=result.state.controllability_dependency_present,
        legitimacy_dependency_present=result.state.legitimacy_dependency_present,
        confidence=result.state.confidence,
        degraded=result.state.degraded,
        underconstrained=result.state.underconstrained,
        available_capability_claim_allowed=result.gate.available_capability_claim_allowed,
        world_conditioned_capability_claim_allowed=(
            result.gate.world_conditioned_capability_claim_allowed
        ),
        self_conditioned_capability_claim_allowed=(
            result.gate.self_conditioned_capability_claim_allowed
        ),
        policy_conditioned_capability_present=result.gate.policy_conditioned_capability_present,
        underconstrained_capability=result.gate.underconstrained_capability,
        no_safe_capability_claim=result.gate.no_safe_capability_claim,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        a04_admission_ready=result.a04_readiness.admission_ready_for_a04,
        a04_blockers=result.a04_readiness.blockers,
        a04_structurally_present_but_not_ready=(
            result.a04_readiness.structurally_present_but_not_ready
        ),
        a04_capability_basis_missing=result.a04_readiness.capability_basis_missing,
        a04_world_dependency_unmet=result.a04_readiness.world_dependency_unmet,
        a04_self_dependency_unmet=result.a04_readiness.self_dependency_unmet,
        a04_policy_legitimacy_unmet=result.a04_readiness.policy_legitimacy_unmet,
        a04_underconstrained_capability_surface=(
            result.a04_readiness.underconstrained_capability_surface
        ),
        a04_external_means_not_justified=(
            result.a04_readiness.external_means_not_justified
        ),
        a04_implemented=result.a04_readiness.a04_implemented,
        a05_touched=result.a04_readiness.a05_touched,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_a_line_normalization_only=result.scope_marker.a_line_normalization_only,
        scope_readiness_gate_only=result.scope_marker.readiness_gate_only,
        scope_a04_implemented=result.scope_marker.a04_implemented,
        scope_a05_touched=result.scope_marker.a05_touched,
        scope_full_agency_stack_implemented=result.scope_marker.full_agency_stack_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        requires_restrictions_read=True,
        reason=result.gate.reason,
    )
