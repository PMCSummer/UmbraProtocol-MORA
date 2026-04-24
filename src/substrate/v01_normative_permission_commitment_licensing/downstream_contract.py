from __future__ import annotations

from dataclasses import dataclass

from substrate.v01_normative_permission_commitment_licensing.models import (
    V01CommitmentDeltaKind,
    V01LicenseResult,
)


@dataclass(frozen=True, slots=True)
class V01LicenseContractView:
    license_id: str
    candidate_act_count: int
    licensed_act_count: int
    denied_act_count: int
    conditional_act_count: int
    commitment_delta_count: int
    mandatory_qualifier_count: int
    protective_defer_required: bool
    insufficient_license_basis: bool
    qualification_required: bool
    assertion_allowed_commitment_denied: bool
    clarification_before_commitment: bool
    cannot_license_advice: bool
    promise_like_act_denied: bool
    alternative_narrowed_act_available: bool
    license_consumer_ready: bool
    commitment_delta_consumer_ready: bool
    qualifier_binding_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_v01_first_slice_only: bool
    scope_v02_not_implemented: bool
    scope_v03_not_implemented: bool
    scope_p02_not_implemented: bool
    scope_p04_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class V01LicenseConsumerView:
    license_id: str
    unlicensed_act_present: bool
    qualification_required: bool
    commitment_denied: bool
    protective_defer_required: bool
    alternative_narrowed_act_available: bool
    license_consumer_ready: bool
    commitment_delta_consumer_ready: bool
    qualifier_binding_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_v01_license_contract_view(result: V01LicenseResult) -> V01LicenseContractView:
    if not isinstance(result, V01LicenseResult):
        raise TypeError("derive_v01_license_contract_view requires V01LicenseResult")
    return V01LicenseContractView(
        license_id=result.state.license_id,
        candidate_act_count=result.state.candidate_act_count,
        licensed_act_count=result.state.licensed_act_count,
        denied_act_count=result.state.denied_act_count,
        conditional_act_count=result.state.conditional_act_count,
        commitment_delta_count=result.state.commitment_delta_count,
        mandatory_qualifier_count=result.state.mandatory_qualifier_count,
        protective_defer_required=result.state.protective_defer_required,
        insufficient_license_basis=result.state.insufficient_license_basis,
        qualification_required=result.state.qualification_required,
        assertion_allowed_commitment_denied=result.state.assertion_allowed_commitment_denied,
        clarification_before_commitment=result.state.clarification_before_commitment,
        cannot_license_advice=result.state.cannot_license_advice,
        promise_like_act_denied=result.state.promise_like_act_denied,
        alternative_narrowed_act_available=result.state.alternative_narrowed_act_available,
        license_consumer_ready=result.gate.license_consumer_ready,
        commitment_delta_consumer_ready=result.gate.commitment_delta_consumer_ready,
        qualifier_binding_consumer_ready=result.gate.qualifier_binding_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_v01_first_slice_only=result.scope_marker.v01_first_slice_only,
        scope_v02_not_implemented=result.scope_marker.v02_not_implemented,
        scope_v03_not_implemented=result.scope_marker.v03_not_implemented,
        scope_p02_not_implemented=result.scope_marker.p02_not_implemented,
        scope_p04_not_implemented=result.scope_marker.p04_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_v01_license_consumer_view(
    result_or_view: V01LicenseResult | V01LicenseContractView,
) -> V01LicenseConsumerView:
    view = (
        derive_v01_license_contract_view(result_or_view)
        if isinstance(result_or_view, V01LicenseResult)
        else result_or_view
    )
    if not isinstance(view, V01LicenseContractView):
        raise TypeError(
            "derive_v01_license_consumer_view requires V01LicenseResult/V01LicenseContractView"
        )
    unlicensed_act_present = bool(view.denied_act_count > 0)
    commitment_denied = bool(
        view.promise_like_act_denied
        or "commitment_denied" in view.restrictions
        or "clarification_before_commitment" in view.restrictions
    )
    return V01LicenseConsumerView(
        license_id=view.license_id,
        unlicensed_act_present=unlicensed_act_present,
        qualification_required=bool(
            view.qualification_required and view.mandatory_qualifier_count > 0
        ),
        commitment_denied=commitment_denied,
        protective_defer_required=view.protective_defer_required,
        alternative_narrowed_act_available=view.alternative_narrowed_act_available,
        license_consumer_ready=view.license_consumer_ready,
        commitment_delta_consumer_ready=bool(
            view.commitment_delta_consumer_ready
            and (
                view.commitment_delta_count > 0
                or view.assertion_allowed_commitment_denied
                or view.promise_like_act_denied
            )
        ),
        qualifier_binding_consumer_ready=view.qualifier_binding_consumer_ready,
        restrictions=view.restrictions,
        reason="v01 license consumer view",
    )


def require_v01_license_consumer_ready(
    result_or_view: V01LicenseResult | V01LicenseContractView,
) -> V01LicenseConsumerView:
    view = derive_v01_license_consumer_view(result_or_view)
    if not view.license_consumer_ready:
        raise PermissionError("v01 license consumer requires act-level license state readiness")
    return view


def require_v01_commitment_delta_consumer_ready(
    result_or_view: V01LicenseResult | V01LicenseContractView,
) -> V01LicenseConsumerView:
    view = derive_v01_license_consumer_view(result_or_view)
    if not view.commitment_delta_consumer_ready:
        raise PermissionError("v01 commitment consumer requires explicit commitment delta surface")
    return view


def require_v01_qualifier_binding_consumer_ready(
    result_or_view: V01LicenseResult | V01LicenseContractView,
) -> V01LicenseConsumerView:
    view = derive_v01_license_consumer_view(result_or_view)
    if not view.qualifier_binding_consumer_ready:
        raise PermissionError("v01 qualifier consumer requires mandatory qualifier-binding surface")
    return view
