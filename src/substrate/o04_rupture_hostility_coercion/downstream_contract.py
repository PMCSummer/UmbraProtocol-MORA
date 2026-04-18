from __future__ import annotations

from dataclasses import dataclass

from substrate.o04_rupture_hostility_coercion.models import (
    O04DynamicResult,
    O04DynamicType,
    O04RuptureStatus,
)


@dataclass(frozen=True, slots=True)
class O04DynamicContractView:
    interaction_model_id: str
    dynamic_type: str
    rupture_status: O04RuptureStatus
    directionality_kind: str
    leverage_surface: str
    legitimacy_hint_status: str
    coercion_candidate_count: int
    hostility_candidate_count: int
    no_safe_dynamic_claim: bool
    dependency_model_underconstrained: bool
    tone_shortcut_forbidden_applied: bool
    dynamic_contract_consumer_ready: bool
    directionality_consumer_ready: bool
    protective_handoff_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_o04_first_slice_only: bool
    scope_r05_not_implemented: bool
    scope_v_line_not_implemented: bool
    scope_p04_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class O04DynamicConsumerView:
    interaction_model_id: str
    coercive_structure_candidate: bool
    rupture_risk_or_active: bool
    ambiguity_preserving_required: bool
    no_strong_dynamic_claim: bool
    dynamic_contract_consumer_ready: bool
    directionality_consumer_ready: bool
    protective_handoff_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_o04_dynamic_contract_view(
    result: O04DynamicResult,
) -> O04DynamicContractView:
    if not isinstance(result, O04DynamicResult):
        raise TypeError("derive_o04_dynamic_contract_view requires O04DynamicResult")
    return O04DynamicContractView(
        interaction_model_id=result.state.interaction_model_id,
        dynamic_type=result.telemetry.dynamic_type.value,
        rupture_status=result.state.rupture_status,
        directionality_kind=result.telemetry.directionality_kind.value,
        leverage_surface=result.telemetry.leverage_surface.value,
        legitimacy_hint_status=result.telemetry.legitimacy_hint_status.value,
        coercion_candidate_count=len(result.state.coercion_candidates),
        hostility_candidate_count=len(result.state.hostility_candidates),
        no_safe_dynamic_claim=result.state.no_safe_dynamic_claim,
        dependency_model_underconstrained=result.state.dependency_model_underconstrained,
        tone_shortcut_forbidden_applied=result.state.tone_shortcut_forbidden_applied,
        dynamic_contract_consumer_ready=result.gate.dynamic_contract_consumer_ready,
        directionality_consumer_ready=result.gate.directionality_consumer_ready,
        protective_handoff_consumer_ready=result.gate.protective_handoff_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_o04_first_slice_only=result.scope_marker.o04_first_slice_only,
        scope_r05_not_implemented=result.scope_marker.r05_not_implemented,
        scope_v_line_not_implemented=result.scope_marker.v_line_not_implemented,
        scope_p04_not_implemented=result.scope_marker.p04_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_o04_dynamic_consumer_view(
    result_or_view: O04DynamicResult | O04DynamicContractView,
) -> O04DynamicConsumerView:
    view = (
        derive_o04_dynamic_contract_view(result_or_view)
        if isinstance(result_or_view, O04DynamicResult)
        else result_or_view
    )
    if not isinstance(view, O04DynamicContractView):
        raise TypeError(
            "derive_o04_dynamic_consumer_view requires O04DynamicResult/O04DynamicContractView"
        )
    coercive_structure_candidate = bool(
        view.coercion_candidate_count > 0
        or view.dynamic_type
        in {
            O04DynamicType.COERCIVE_PRESSURE_CANDIDATE.value,
            O04DynamicType.FORCED_COMPLIANCE_CANDIDATE.value,
        }
    )
    rupture_risk_or_active = view.rupture_status in {
        O04RuptureStatus.RUPTURE_RISK_ONLY,
        O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE,
        O04RuptureStatus.DEESCALATED_BUT_NOT_CLOSED,
    }
    ambiguity_preserving_required = bool(
        "legitimacy_underconstrained" in view.restrictions
        or "directionality_ambiguous" in view.restrictions
        or view.no_safe_dynamic_claim
    )
    no_strong_dynamic_claim = bool(
        view.no_safe_dynamic_claim
        or (
            view.directionality_kind == "directionality_ambiguous"
            and coercive_structure_candidate
        )
    )
    return O04DynamicConsumerView(
        interaction_model_id=view.interaction_model_id,
        coercive_structure_candidate=coercive_structure_candidate,
        rupture_risk_or_active=rupture_risk_or_active,
        ambiguity_preserving_required=ambiguity_preserving_required,
        no_strong_dynamic_claim=no_strong_dynamic_claim,
        dynamic_contract_consumer_ready=view.dynamic_contract_consumer_ready,
        directionality_consumer_ready=view.directionality_consumer_ready,
        protective_handoff_consumer_ready=view.protective_handoff_consumer_ready,
        restrictions=view.restrictions,
        reason="o04 dynamic consumer view",
    )


def require_o04_dynamic_contract_consumer_ready(
    result_or_view: O04DynamicResult | O04DynamicContractView,
) -> O04DynamicConsumerView:
    view = derive_o04_dynamic_consumer_view(result_or_view)
    if not view.dynamic_contract_consumer_ready:
        raise PermissionError(
            "o04 dynamic contract consumer requires bounded structural dynamic basis"
        )
    return view


def require_o04_directionality_consumer_ready(
    result_or_view: O04DynamicResult | O04DynamicContractView,
) -> O04DynamicConsumerView:
    view = derive_o04_dynamic_consumer_view(result_or_view)
    if not view.directionality_consumer_ready:
        raise PermissionError(
            "o04 directionality consumer requires non-ambiguous actor-target structure"
        )
    return view


def require_o04_protective_handoff_consumer_ready(
    result_or_view: O04DynamicResult | O04DynamicContractView,
) -> O04DynamicConsumerView:
    view = derive_o04_dynamic_consumer_view(result_or_view)
    if not view.protective_handoff_consumer_ready:
        raise PermissionError(
            "o04 protective handoff consumer requires bounded coercive/rupture dynamic readiness"
        )
    return view
