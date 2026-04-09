from __future__ import annotations

from dataclasses import dataclass

from substrate.n_minimal.models import NMinimalResult


@dataclass(frozen=True, slots=True)
class NMinimalContractView:
    narrative_commitment_id: str
    commitment_status: str
    commitment_scope: str
    narrative_basis_present: bool
    self_basis_present: bool
    world_basis_present: bool
    memory_basis_present: bool
    capability_basis_present: bool
    ambiguity_residue: bool
    contradiction_risk: str
    confidence: float
    degraded: bool
    underconstrained: bool
    safe_narrative_commitment_allowed: bool
    bounded_commitment_allowed: bool
    no_safe_narrative_claim: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    n01_admission_ready: bool
    n01_blockers: tuple[str, ...]
    n01_implemented: bool
    n02_implemented: bool
    n03_implemented: bool
    n04_implemented: bool
    scope: str
    scope_rt01_contour_only: bool
    scope_n_minimal_only: bool
    scope_readiness_gate_only: bool
    scope_n01_implemented: bool
    scope_n02_implemented: bool
    scope_n03_implemented: bool
    scope_n04_implemented: bool
    scope_full_narrative_line_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    requires_restrictions_read: bool
    reason: str


def derive_n_minimal_contract_view(result: NMinimalResult) -> NMinimalContractView:
    if not isinstance(result, NMinimalResult):
        raise TypeError("derive_n_minimal_contract_view requires NMinimalResult")
    return NMinimalContractView(
        narrative_commitment_id=result.state.narrative_commitment_id,
        commitment_status=result.state.commitment_status.value,
        commitment_scope=result.state.commitment_scope,
        narrative_basis_present=result.state.narrative_basis_present,
        self_basis_present=result.state.self_basis_present,
        world_basis_present=result.state.world_basis_present,
        memory_basis_present=result.state.memory_basis_present,
        capability_basis_present=result.state.capability_basis_present,
        ambiguity_residue=result.state.ambiguity_residue,
        contradiction_risk=result.state.contradiction_risk.value,
        confidence=result.state.confidence,
        degraded=result.state.degraded,
        underconstrained=result.state.underconstrained,
        safe_narrative_commitment_allowed=result.gate.safe_narrative_commitment_allowed,
        bounded_commitment_allowed=result.gate.bounded_commitment_allowed,
        no_safe_narrative_claim=result.gate.no_safe_narrative_claim,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        n01_admission_ready=result.admission.admission_ready_for_n01,
        n01_blockers=result.admission.blockers,
        n01_implemented=result.admission.n01_implemented,
        n02_implemented=result.admission.n02_implemented,
        n03_implemented=result.admission.n03_implemented,
        n04_implemented=result.admission.n04_implemented,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_n_minimal_only=result.scope_marker.n_minimal_only,
        scope_readiness_gate_only=result.scope_marker.readiness_gate_only,
        scope_n01_implemented=result.scope_marker.n01_implemented,
        scope_n02_implemented=result.scope_marker.n02_implemented,
        scope_n03_implemented=result.scope_marker.n03_implemented,
        scope_n04_implemented=result.scope_marker.n04_implemented,
        scope_full_narrative_line_implemented=result.scope_marker.full_narrative_line_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        requires_restrictions_read=True,
        reason=result.gate.reason,
    )


def require_bounded_n_minimal_scope(
    contract: NMinimalResult | NMinimalContractView,
) -> NMinimalContractView:
    view = (
        derive_n_minimal_contract_view(contract)
        if isinstance(contract, NMinimalResult)
        else contract
    )
    if not isinstance(view, NMinimalContractView):
        raise TypeError(
            "require_bounded_n_minimal_scope requires NMinimalResult/NMinimalContractView"
        )
    if (
        view.scope != "rt01_contour_only"
        or not view.scope_rt01_contour_only
        or not view.scope_n_minimal_only
        or not view.scope_readiness_gate_only
        or view.scope_n01_implemented
        or view.scope_n02_implemented
        or view.scope_n03_implemented
        or view.scope_n04_implemented
        or view.scope_full_narrative_line_implemented
        or view.scope_repo_wide_adoption
    ):
        raise PermissionError(
            "n-minimal contract scope markers do not satisfy bounded rt01 contour-only non-claim discipline"
        )
    return view


def require_strong_narrative_commitment_for_consumer(
    contract: NMinimalResult | NMinimalContractView,
) -> NMinimalContractView:
    view = require_bounded_n_minimal_scope(contract)
    if not view.safe_narrative_commitment_allowed or view.no_safe_narrative_claim:
        raise PermissionError(
            "strong narrative commitment requires safe bounded n-minimal basis and no-safe fallback must remain closed"
        )
    return view
