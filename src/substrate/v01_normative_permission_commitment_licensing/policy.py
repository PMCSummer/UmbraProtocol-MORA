from __future__ import annotations

from substrate.r05_appraisal_sovereign_protective_regulation import R05ProtectiveResult
from substrate.v01_normative_permission_commitment_licensing.models import (
    V01ActType,
    V01CommitmentDelta,
    V01CommitmentDeltaKind,
    V01CommunicativeActCandidate,
    V01CommunicativeLicenseState,
    V01DeniedActEntry,
    V01LicenseGateDecision,
    V01LicenseResult,
    V01LicensedActEntry,
    V01ScopeMarker,
    V01Telemetry,
)


def build_v01_normative_permission_commitment_licensing(
    *,
    tick_id: str,
    tick_index: int,
    act_candidates: tuple[V01CommunicativeActCandidate, ...],
    r05_result: R05ProtectiveResult | None,
    source_lineage: tuple[str, ...],
    prior_state: V01CommunicativeLicenseState | None = None,
    licensing_enabled: bool = True,
) -> V01LicenseResult:
    if not licensing_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    candidates = tuple(
        item for item in act_candidates if isinstance(item, V01CommunicativeActCandidate)
    )
    if not candidates:
        return _build_no_candidate_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    protective_mode = (
        r05_result.state.protective_mode.value
        if isinstance(r05_result, R05ProtectiveResult)
        else "vigilance_without_override"
    )
    protective_surface_pressure = bool(
        isinstance(r05_result, R05ProtectiveResult)
        and any(
            surface.value in {"interaction_intensity", "project_continuation"}
            for surface in r05_result.state.inhibited_surfaces
        )
    )
    protective_defer_required = bool(
        isinstance(r05_result, R05ProtectiveResult)
        and not r05_result.state.insufficient_basis_for_override
        and protective_mode
        in {"active_protective_mode", "degraded_operation_only", "recovery_in_progress"}
        and (
            r05_result.state.project_override_active
            or r05_result.state.release_pending
            or r05_result.state.hysteresis_hold_ticks > 0
            or protective_surface_pressure
        )
    )

    licensed: list[V01LicensedActEntry] = []
    denied: list[V01DeniedActEntry] = []
    commitment_deltas: list[V01CommitmentDelta] = []
    mandatory_qualifiers: list[str] = []
    assertion_licensed = False
    assertion_allowed_commitment_denied = False
    clarification_before_commitment = False
    cannot_license_advice = False

    for candidate in candidates:
        evidence = _clamp(0.0, 1.0, candidate.evidence_strength)
        helpfulness_pressure = _clamp(0.0, 1.0, candidate.helpfulness_pressure)

        if candidate.act_type is V01ActType.ASSERTION:
            if candidate.authority_basis_present and evidence >= 0.9:
                qualifiers = ()
                if candidate.explicit_uncertainty_present is False and evidence < 0.96:
                    qualifiers = ("preserve_explicit_uncertainty",)
                licensed.append(
                    V01LicensedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        conditional_license=bool(qualifiers),
                        mandatory_qualifiers=qualifiers,
                        reason_codes=("assertion_basis_sufficient",),
                    )
                )
                mandatory_qualifiers.extend(qualifiers)
                assertion_licensed = True
            elif candidate.authority_basis_present and evidence >= 0.45:
                qualifiers = ("qualified_assertion_required", "preserve_explicit_uncertainty")
                licensed.append(
                    V01LicensedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        conditional_license=True,
                        mandatory_qualifiers=qualifiers,
                        reason_codes=("qualification_required",),
                    )
                )
                mandatory_qualifiers.extend(qualifiers)
                assertion_licensed = True
            else:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason="assertion requires grounded evidence basis",
                        blocking_reason_code="insufficient_assertion_basis",
                        alternative_narrowed_act_type=V01ActType.QUESTION,
                    )
                )

        elif candidate.act_type is V01ActType.ADVICE:
            if helpfulness_pressure >= 0.8 and not candidate.authority_basis_present:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason="helpfulness pressure does not provide advice authority basis",
                        blocking_reason_code="helpfulness_not_authority_basis",
                        alternative_narrowed_act_type=V01ActType.QUESTION,
                    )
                )
                cannot_license_advice = True
            elif protective_defer_required and candidate.protective_sensitivity:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason="protective defer active for advice-like act under current protective state",
                        blocking_reason_code="protective_defer_required",
                        alternative_narrowed_act_type=V01ActType.BOUNDARY_STATEMENT,
                    )
                )
                cannot_license_advice = True
            elif candidate.authority_basis_present and evidence >= 0.66:
                qualifiers = ()
                if evidence < 0.82:
                    qualifiers = ("advice_basis_disclosure_required",)
                licensed.append(
                    V01LicensedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        conditional_license=bool(qualifiers),
                        mandatory_qualifiers=qualifiers,
                        reason_codes=("advice_basis_sufficient",),
                    )
                )
                mandatory_qualifiers.extend(qualifiers)
            elif candidate.authority_basis_present and evidence >= 0.4:
                qualifiers = ("advice_basis_disclosure_required", "preserve_explicit_uncertainty")
                licensed.append(
                    V01LicensedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        conditional_license=True,
                        mandatory_qualifiers=qualifiers,
                        reason_codes=("cannot_license_advice_without_qualification",),
                    )
                )
                mandatory_qualifiers.extend(qualifiers)
                cannot_license_advice = True
            else:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason="advice denied due to insufficient normative basis",
                        blocking_reason_code="cannot_license_advice",
                        alternative_narrowed_act_type=V01ActType.QUESTION,
                    )
                )
                cannot_license_advice = True

        elif candidate.act_type is V01ActType.PROMISE:
            if candidate.authority_basis_present and evidence >= 0.9 and not protective_defer_required:
                qualifiers = ()
                if candidate.explicit_uncertainty_present is False and evidence < 0.96:
                    qualifiers = ("bounded_commitment_scope",)
                licensed.append(
                    V01LicensedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        conditional_license=bool(qualifiers),
                        mandatory_qualifiers=qualifiers,
                        reason_codes=("promise_commitment_lawfully_licensed",),
                    )
                )
                mandatory_qualifiers.extend(qualifiers)
                commitment_deltas.append(
                    V01CommitmentDelta(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        delta_kind=V01CommitmentDeltaKind.CREATE_COMMITMENT,
                        commitment_target_ref=candidate.commitment_target_ref,
                        allowed=True,
                        reason="promise licensed with explicit bounded commitment delta",
                    )
                )
            elif candidate.authority_basis_present and evidence >= 0.54 and assertion_licensed:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason="promise denied; assertion may proceed under weaker license",
                        blocking_reason_code="assertion_allowed_commitment_denied",
                        alternative_narrowed_act_type=V01ActType.ASSERTION,
                    )
                )
                commitment_deltas.append(
                    V01CommitmentDelta(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        delta_kind=V01CommitmentDeltaKind.COMMITMENT_DENIED,
                        commitment_target_ref=candidate.commitment_target_ref,
                        allowed=False,
                        reason="commitment denied pending stronger commitment basis",
                    )
                )
                assertion_allowed_commitment_denied = True
                clarification_before_commitment = True
            else:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason=(
                            "promise denied under protective defer"
                            if protective_defer_required
                            else "promise denied due to insufficient commitment basis"
                        ),
                        blocking_reason_code=(
                            "protective_defer_required"
                            if protective_defer_required
                            else "clarification_before_commitment"
                        ),
                        alternative_narrowed_act_type=V01ActType.ASSERTION
                        if assertion_licensed
                        else V01ActType.QUESTION,
                    )
                )
                commitment_deltas.append(
                    V01CommitmentDelta(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        delta_kind=V01CommitmentDeltaKind.COMMITMENT_DENIED,
                        commitment_target_ref=candidate.commitment_target_ref,
                        allowed=False,
                        reason="promise-like commitment denied by licensing gate",
                    )
                )
                clarification_before_commitment = True

        elif candidate.act_type is V01ActType.WARNING:
            if evidence >= 0.5:
                qualifiers = ("preserve_explicit_uncertainty",) if evidence < 0.72 else ()
                licensed.append(
                    V01LicensedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        conditional_license=bool(qualifiers),
                        mandatory_qualifiers=qualifiers,
                        reason_codes=("warning_license",),
                    )
                )
                mandatory_qualifiers.extend(qualifiers)
            else:
                denied.append(
                    V01DeniedActEntry(
                        act_id=candidate.act_id,
                        act_type=candidate.act_type,
                        deny_reason="warning denied due to insufficient warning basis",
                        blocking_reason_code="insufficient_warning_basis",
                        alternative_narrowed_act_type=V01ActType.QUESTION,
                    )
                )

        elif candidate.act_type is V01ActType.REQUEST:
            qualifiers = ("request_scope_clarification_required",) if evidence < 0.5 else ()
            licensed.append(
                V01LicensedActEntry(
                    act_id=candidate.act_id,
                    act_type=candidate.act_type,
                    conditional_license=bool(qualifiers),
                    mandatory_qualifiers=qualifiers,
                    reason_codes=("request_license",),
                )
            )
            mandatory_qualifiers.extend(qualifiers)

        elif candidate.act_type in {
            V01ActType.QUESTION,
            V01ActType.REFUSAL,
            V01ActType.ACKNOWLEDGEMENT,
            V01ActType.BOUNDARY_STATEMENT,
            V01ActType.EXPLANATION,
        }:
            licensed.append(
                V01LicensedActEntry(
                    act_id=candidate.act_id,
                    act_type=candidate.act_type,
                    conditional_license=False,
                    mandatory_qualifiers=(),
                    reason_codes=("baseline_license",),
                )
            )
        else:
            denied.append(
                V01DeniedActEntry(
                    act_id=candidate.act_id,
                    act_type=candidate.act_type,
                    deny_reason="act type not licensable under current frontier slice",
                    blocking_reason_code="unsupported_act_type",
                    alternative_narrowed_act_type=V01ActType.QUESTION,
                )
            )

    licensed_act_count = len(licensed)
    denied_act_count = len(denied)
    conditional_act_count = sum(1 for item in licensed if item.conditional_license)
    mandatory_qualifiers_unique = tuple(dict.fromkeys(mandatory_qualifiers))
    commitment_delta_count = len(commitment_deltas)
    promise_like_act_denied = any(item.act_type is V01ActType.PROMISE for item in denied)
    alternative_narrowed_act_available = any(
        item.alternative_narrowed_act_type is not None for item in denied
    )
    insufficient_license_basis = bool(
        licensed_act_count == 0 and denied_act_count > 0 and not alternative_narrowed_act_available
    )

    state = V01CommunicativeLicenseState(
        license_id=f"v01-license:{tick_id}",
        candidate_act_count=len(candidates),
        licensed_acts=tuple(licensed),
        denied_acts=tuple(denied),
        commitment_deltas=tuple(commitment_deltas),
        mandatory_qualifiers=mandatory_qualifiers_unique,
        licensed_act_count=licensed_act_count,
        denied_act_count=denied_act_count,
        conditional_act_count=conditional_act_count,
        commitment_delta_count=commitment_delta_count,
        mandatory_qualifier_count=len(mandatory_qualifiers_unique),
        protective_defer_required=protective_defer_required,
        insufficient_license_basis=insufficient_license_basis,
        qualification_required=conditional_act_count > 0,
        assertion_allowed_commitment_denied=assertion_allowed_commitment_denied,
        clarification_before_commitment=clarification_before_commitment,
        cannot_license_advice=cannot_license_advice,
        promise_like_act_denied=promise_like_act_denied,
        alternative_narrowed_act_available=alternative_narrowed_act_available,
        justification_links=tuple(
            dict.fromkeys(
                (
                    f"candidate_act_count:{len(candidates)}",
                    f"licensed_act_count:{licensed_act_count}",
                    f"denied_act_count:{denied_act_count}",
                    f"protective_mode:{protective_mode}",
                    "qualification_required" if conditional_act_count > 0 else "qualification_not_required",
                    (
                        "assertion_allowed_commitment_denied"
                        if assertion_allowed_commitment_denied
                        else "no_assertion_commitment_split"
                    ),
                )
            )
        ),
        provenance="v01.normative_permission_commitment_licensing.policy",
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *(
                        r05_result.state.source_lineage
                        if isinstance(r05_result, R05ProtectiveResult)
                        else ()
                    ),
                )
            )
        ),
        last_update_provenance="v01.normative_permission_commitment_licensing.policy",
    )
    gate = _build_gate(state)
    scope_marker = V01ScopeMarker(
        scope="rt01_hosted_v01_first_slice",
        rt01_hosted_only=True,
        v01_first_slice_only=True,
        v02_not_implemented=True,
        v03_not_implemented=True,
        p02_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="first bounded v01 slice; v02/v03 and episode-policy layers remain open seams",
    )
    telemetry = V01Telemetry(
        license_id=state.license_id,
        tick_index=tick_index,
        candidate_act_count=state.candidate_act_count,
        licensed_act_count=state.licensed_act_count,
        denied_act_count=state.denied_act_count,
        conditional_act_count=state.conditional_act_count,
        commitment_delta_count=state.commitment_delta_count,
        mandatory_qualifier_count=state.mandatory_qualifier_count,
        protective_defer_required=state.protective_defer_required,
        insufficient_license_basis=state.insufficient_license_basis,
        downstream_consumer_ready=gate.license_consumer_ready,
        promise_like_act_denied=state.promise_like_act_denied,
        alternative_narrowed_act_available=state.alternative_narrowed_act_available,
    )
    return V01LicenseResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=(
            "v01 produced act-level normative license/deny/conditional outcomes with explicit commitment deltas "
            "and mandatory qualifier binding requirements"
        ),
    )


def _build_gate(state: V01CommunicativeLicenseState) -> V01LicenseGateDecision:
    license_ready = bool(state.candidate_act_count > 0 and (state.licensed_act_count + state.denied_act_count) > 0)
    commitment_ready = bool(state.commitment_delta_count > 0)
    qualifier_ready = bool(state.qualification_required and state.mandatory_qualifier_count > 0)
    restrictions: list[str] = []
    if state.denied_act_count > 0:
        restrictions.append("unlicensed_act_present")
    if state.qualification_required:
        restrictions.append("qualification_required")
    if state.promise_like_act_denied:
        restrictions.append("commitment_denied")
    if state.protective_defer_required:
        restrictions.append("protective_defer_required")
    if state.insufficient_license_basis:
        restrictions.append("insufficient_license_basis")
    if state.commitment_delta_count == 0:
        restrictions.append("no_commitment_delta")
    if state.mandatory_qualifier_count == 0:
        restrictions.append("no_mandatory_qualifier_binding")
    return V01LicenseGateDecision(
        license_consumer_ready=license_ready,
        commitment_delta_consumer_ready=commitment_ready,
        qualifier_binding_consumer_ready=qualifier_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="v01 gate exposes license, commitment-delta and qualifier-binding readiness",
    )


def _build_no_candidate_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> V01LicenseResult:
    state = V01CommunicativeLicenseState(
        license_id=f"v01-license:{tick_id}",
        candidate_act_count=0,
        licensed_acts=(),
        denied_acts=(),
        commitment_deltas=(),
        mandatory_qualifiers=(),
        licensed_act_count=0,
        denied_act_count=0,
        conditional_act_count=0,
        commitment_delta_count=0,
        mandatory_qualifier_count=0,
        protective_defer_required=False,
        insufficient_license_basis=True,
        qualification_required=False,
        assertion_allowed_commitment_denied=False,
        clarification_before_commitment=False,
        cannot_license_advice=False,
        promise_like_act_denied=False,
        alternative_narrowed_act_available=False,
        justification_links=("candidate_act_count:0", "no_v01_candidate_basis"),
        provenance="v01.normative_permission_commitment_licensing.no_candidate",
        source_lineage=source_lineage,
        last_update_provenance="v01.normative_permission_commitment_licensing.no_candidate",
    )
    gate = V01LicenseGateDecision(
        license_consumer_ready=False,
        commitment_delta_consumer_ready=False,
        qualifier_binding_consumer_ready=False,
        restrictions=("insufficient_license_basis", "no_candidate_acts"),
        reason="v01 no-candidate fallback keeps licensing gate non-activating",
    )
    scope_marker = V01ScopeMarker(
        scope="rt01_hosted_v01_first_slice",
        rt01_hosted_only=True,
        v01_first_slice_only=True,
        v02_not_implemented=True,
        v03_not_implemented=True,
        p02_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="v01 no-candidate fallback",
    )
    telemetry = V01Telemetry(
        license_id=state.license_id,
        tick_index=tick_index,
        candidate_act_count=0,
        licensed_act_count=0,
        denied_act_count=0,
        conditional_act_count=0,
        commitment_delta_count=0,
        mandatory_qualifier_count=0,
        protective_defer_required=False,
        insufficient_license_basis=True,
        downstream_consumer_ready=False,
        promise_like_act_denied=False,
        alternative_narrowed_act_available=False,
    )
    return V01LicenseResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> V01LicenseResult:
    state = V01CommunicativeLicenseState(
        license_id=f"v01-license:{tick_id}",
        candidate_act_count=0,
        licensed_acts=(),
        denied_acts=(),
        commitment_deltas=(),
        mandatory_qualifiers=(),
        licensed_act_count=0,
        denied_act_count=0,
        conditional_act_count=0,
        commitment_delta_count=0,
        mandatory_qualifier_count=0,
        protective_defer_required=False,
        insufficient_license_basis=True,
        qualification_required=False,
        assertion_allowed_commitment_denied=False,
        clarification_before_commitment=False,
        cannot_license_advice=False,
        promise_like_act_denied=False,
        alternative_narrowed_act_available=False,
        justification_links=("v01_disabled",),
        provenance="v01.normative_permission_commitment_licensing.disabled",
        source_lineage=source_lineage,
        last_update_provenance="v01.normative_permission_commitment_licensing.disabled",
    )
    gate = V01LicenseGateDecision(
        license_consumer_ready=False,
        commitment_delta_consumer_ready=False,
        qualifier_binding_consumer_ready=False,
        restrictions=("v01_disabled", "insufficient_license_basis"),
        reason="v01 licensing disabled in ablation context",
    )
    scope_marker = V01ScopeMarker(
        scope="rt01_hosted_v01_first_slice",
        rt01_hosted_only=True,
        v01_first_slice_only=True,
        v02_not_implemented=True,
        v03_not_implemented=True,
        p02_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="v01 disabled path",
    )
    telemetry = V01Telemetry(
        license_id=state.license_id,
        tick_index=tick_index,
        candidate_act_count=0,
        licensed_act_count=0,
        denied_act_count=0,
        conditional_act_count=0,
        commitment_delta_count=0,
        mandatory_qualifier_count=0,
        protective_defer_required=False,
        insufficient_license_basis=True,
        downstream_consumer_ready=False,
        promise_like_act_denied=False,
        alternative_narrowed_act_available=False,
    )
    return V01LicenseResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _clamp(min_value: float, max_value: float, value: float) -> float:
    return max(min_value, min(max_value, float(value)))
