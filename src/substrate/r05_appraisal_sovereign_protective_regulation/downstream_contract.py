from __future__ import annotations

from dataclasses import dataclass

from substrate.r05_appraisal_sovereign_protective_regulation.models import (
    R05ProtectiveMode,
    R05ProtectiveResult,
)


@dataclass(frozen=True, slots=True)
class R05ProtectiveContractView:
    regulation_id: str
    protective_mode: str
    authority_level: str
    trigger_count: int
    structural_basis_score: float
    inhibited_surfaces: tuple[str, ...]
    project_override_active: bool
    override_scope: str
    release_pending: bool
    release_conditions: tuple[str, ...]
    release_satisfied: bool
    recovery_recheck_due: bool
    hysteresis_hold_ticks: int
    regulation_conflict: bool
    insufficient_basis_for_override: bool
    protective_state_consumer_ready: bool
    surface_inhibition_consumer_ready: bool
    release_contract_consumer_ready: bool
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_hosted_only: bool
    scope_r05_first_slice_only: bool
    scope_a05_not_implemented: bool
    scope_v_line_not_implemented: bool
    scope_p04_not_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class R05ProtectiveConsumerView:
    regulation_id: str
    protective_override_required: bool
    surface_throttle_required: bool
    release_recheck_required: bool
    project_continuation_allowed: bool
    communication_exposure_throttled: bool
    protective_state_consumer_ready: bool
    surface_inhibition_consumer_ready: bool
    release_contract_consumer_ready: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_r05_protective_contract_view(
    result: R05ProtectiveResult,
) -> R05ProtectiveContractView:
    if not isinstance(result, R05ProtectiveResult):
        raise TypeError("derive_r05_protective_contract_view requires R05ProtectiveResult")
    return R05ProtectiveContractView(
        regulation_id=result.state.regulation_id,
        protective_mode=result.state.protective_mode.value,
        authority_level=result.state.authority_level.value,
        trigger_count=result.state.trigger_count,
        structural_basis_score=result.state.structural_basis_score,
        inhibited_surfaces=tuple(item.value for item in result.state.inhibited_surfaces),
        project_override_active=result.state.project_override_active,
        override_scope=result.state.override_scope,
        release_pending=result.state.release_pending,
        release_conditions=result.state.release_conditions,
        release_satisfied=result.state.release_satisfied,
        recovery_recheck_due=result.state.recovery_recheck_due,
        hysteresis_hold_ticks=result.state.hysteresis_hold_ticks,
        regulation_conflict=result.state.regulation_conflict,
        insufficient_basis_for_override=result.state.insufficient_basis_for_override,
        protective_state_consumer_ready=result.gate.protective_state_consumer_ready,
        surface_inhibition_consumer_ready=result.gate.surface_inhibition_consumer_ready,
        release_contract_consumer_ready=result.gate.release_contract_consumer_ready,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_hosted_only=result.scope_marker.rt01_hosted_only,
        scope_r05_first_slice_only=result.scope_marker.r05_first_slice_only,
        scope_a05_not_implemented=result.scope_marker.a05_not_implemented,
        scope_v_line_not_implemented=result.scope_marker.v_line_not_implemented,
        scope_p04_not_implemented=result.scope_marker.p04_not_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_r05_protective_consumer_view(
    result_or_view: R05ProtectiveResult | R05ProtectiveContractView,
) -> R05ProtectiveConsumerView:
    view = (
        derive_r05_protective_contract_view(result_or_view)
        if isinstance(result_or_view, R05ProtectiveResult)
        else result_or_view
    )
    if not isinstance(view, R05ProtectiveContractView):
        raise TypeError(
            "derive_r05_protective_consumer_view requires R05ProtectiveResult/R05ProtectiveContractView"
        )
    inhibited = set(view.inhibited_surfaces)
    protective_override_required = bool(
        view.project_override_active
        or view.protective_mode
        in {
            R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE.value,
            R05ProtectiveMode.DEGRADED_OPERATION_ONLY.value,
        }
    )
    surface_throttle_required = bool(
        "interaction_intensity" in inhibited
        or "communication_exposure" in inhibited
    )
    release_recheck_required = bool(
        view.release_pending
        or view.recovery_recheck_due
        or view.protective_mode == R05ProtectiveMode.RECOVERY_IN_PROGRESS.value
    )
    project_continuation_allowed = "project_continuation" not in inhibited
    communication_exposure_throttled = "communication_exposure" in inhibited
    return R05ProtectiveConsumerView(
        regulation_id=view.regulation_id,
        protective_override_required=protective_override_required,
        surface_throttle_required=surface_throttle_required,
        release_recheck_required=release_recheck_required,
        project_continuation_allowed=project_continuation_allowed,
        communication_exposure_throttled=communication_exposure_throttled,
        protective_state_consumer_ready=view.protective_state_consumer_ready,
        surface_inhibition_consumer_ready=view.surface_inhibition_consumer_ready,
        release_contract_consumer_ready=view.release_contract_consumer_ready,
        restrictions=view.restrictions,
        reason="r05 protective consumer view",
    )


def require_r05_protective_state_consumer_ready(
    result_or_view: R05ProtectiveResult | R05ProtectiveContractView,
) -> R05ProtectiveConsumerView:
    view = derive_r05_protective_consumer_view(result_or_view)
    if not view.protective_state_consumer_ready:
        raise PermissionError(
            "r05 protective state consumer requires bounded protective state readiness"
        )
    return view


def require_r05_surface_inhibition_consumer_ready(
    result_or_view: R05ProtectiveResult | R05ProtectiveContractView,
) -> R05ProtectiveConsumerView:
    view = derive_r05_protective_consumer_view(result_or_view)
    if not view.surface_inhibition_consumer_ready:
        raise PermissionError(
            "r05 surface inhibition consumer requires typed inhibited-surface profile"
        )
    return view


def require_r05_release_contract_consumer_ready(
    result_or_view: R05ProtectiveResult | R05ProtectiveContractView,
) -> R05ProtectiveConsumerView:
    view = derive_r05_protective_consumer_view(result_or_view)
    if not view.release_contract_consumer_ready:
        raise PermissionError(
            "r05 release consumer requires explicit release/hysteresis contract"
        )
    return view
