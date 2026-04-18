from __future__ import annotations

from substrate.o04_rupture_hostility_coercion import O04DynamicResult
from substrate.r05_appraisal_sovereign_protective_regulation.models import (
    R05AuthorityLevel,
    R05InhibitedSurface,
    R05ProtectiveDirective,
    R05ProtectiveGateDecision,
    R05ProtectiveMode,
    R05ProtectiveRegulationState,
    R05ProtectiveResult,
    R05ProtectiveTriggerInput,
    R05ScopeMarker,
    R05Telemetry,
)
from substrate.p01_project_formation import P01ProjectFormationResult


def build_r05_appraisal_sovereign_protective_regulation(
    *,
    tick_id: str,
    tick_index: int,
    protective_triggers: tuple[R05ProtectiveTriggerInput, ...],
    o04_result: O04DynamicResult | None,
    p01_result: P01ProjectFormationResult | None,
    source_lineage: tuple[str, ...],
    prior_state: R05ProtectiveRegulationState | None = None,
    regulation_enabled: bool = True,
) -> R05ProtectiveResult:
    if not regulation_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    triggers = tuple(
        item for item in protective_triggers if isinstance(item, R05ProtectiveTriggerInput)
    )
    if not triggers:
        return _build_no_signal_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    trigger_ids = tuple(item.trigger_id for item in triggers)
    tone_only = all(item.tone_only_discomfort for item in triggers)
    base_score = max(_trigger_structural_basis_score(item) for item in triggers)
    avg_load = sum(max(0.0, item.load_pressure_score) for item in triggers) / len(triggers)
    any_release_signal = any(item.release_signal_present for item in triggers)
    any_counterevidence = any(item.counterevidence_present for item in triggers)
    any_project_requested = any(item.project_continuation_requested for item in triggers)
    any_project_active = any(item.p01_project_continuation_active for item in triggers)
    any_permission_hardening = any(item.permission_hardening_available for item in triggers)
    any_escalation_route = any(item.escalation_route_available for item in triggers)
    any_comm_exposed = any(item.communication_surface_exposed for item in triggers)
    any_conflicted_project = any(item.p01_blocked_or_conflicted for item in triggers)

    o04_coercive = bool(
        isinstance(o04_result, O04DynamicResult)
        and len(o04_result.state.coercion_candidates) > 0
    )
    o04_rupture = bool(
        isinstance(o04_result, O04DynamicResult)
        and o04_result.state.rupture_status.value
        in {"rupture_risk_only", "rupture_active_candidate", "deescalated_but_not_closed"}
    )
    o04_legitimacy_gap = bool(
        isinstance(o04_result, O04DynamicResult)
        and o04_result.state.legitimacy_boundary_underconstrained
    )
    o04_directionality_ambiguous = bool(
        isinstance(o04_result, O04DynamicResult)
        and o04_result.telemetry.directionality_kind.value == "directionality_ambiguous"
    )

    p01_handoff_ready = bool(
        isinstance(p01_result, P01ProjectFormationResult)
        and p01_result.gate.project_handoff_consumer_ready
    )
    p01_conflicted = bool(
        isinstance(p01_result, P01ProjectFormationResult)
        and (
            p01_result.state.conflicting_authority
            or p01_result.state.no_safe_project_formation
            or p01_result.state.blocked_pending_grounding
        )
    )

    structural_basis_score = min(
        1.0,
        base_score
        + (0.15 if o04_coercive else 0.0)
        + (0.1 if o04_rupture else 0.0)
        + (0.08 if not o04_directionality_ambiguous and o04_coercive else 0.0)
        + (0.08 if any_project_active and any_project_requested else 0.0)
        + (0.06 if any_conflicted_project or p01_conflicted else 0.0),
    )

    regulation_conflict = bool(
        any_conflicted_project and any_project_requested and any_release_signal
    )
    insufficient_basis = bool(
        structural_basis_score < 0.35
        and not o04_coercive
        and not o04_rupture
        and not any_project_requested
    )

    mode, authority_level = _derive_mode_and_authority(
        structural_basis_score=structural_basis_score,
        avg_load=avg_load,
        tone_only=tone_only,
        insufficient_basis=insufficient_basis,
        regulation_conflict=regulation_conflict,
        release_signal_present=any_release_signal,
        counterevidence_present=any_counterevidence,
        prior_state=prior_state,
        o04_coercive=o04_coercive,
        o04_rupture=o04_rupture,
    )

    inhibited_surfaces = _derive_inhibited_surfaces(
        mode=mode,
        communication_exposed=any_comm_exposed,
        project_requested=any_project_requested,
        permission_hardening_available=any_permission_hardening,
        escalation_route_available=any_escalation_route,
    )
    project_override_active = bool(
        mode is R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE
        and R05InhibitedSurface.PROJECT_CONTINUATION in inhibited_surfaces
        and any_project_active
    )
    release_conditions = _derive_release_conditions(
        mode=mode,
        o04_rupture=o04_rupture,
        o04_coercive=o04_coercive,
        legitimacy_gap=o04_legitimacy_gap,
        p01_handoff_ready=p01_handoff_ready,
    )
    release_satisfied = bool(any_release_signal or any_counterevidence)
    prior_hysteresis = prior_state.hysteresis_hold_ticks if isinstance(prior_state, R05ProtectiveRegulationState) else 0
    hysteresis_hold_ticks = _derive_hysteresis_hold_ticks(
        mode=mode,
        prior_state=prior_state,
        release_satisfied=release_satisfied,
        prior_hysteresis=prior_hysteresis,
    )
    release_pending = bool(
        mode in {R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE, R05ProtectiveMode.RECOVERY_IN_PROGRESS}
        and not release_satisfied
    )
    recovery_recheck_due = bool(
        mode in {
            R05ProtectiveMode.RECOVERY_IN_PROGRESS,
            R05ProtectiveMode.DEGRADED_OPERATION_ONLY,
        }
        and release_pending
    )

    override_scope = _derive_override_scope(
        project_override_active=project_override_active,
        inhibited_surfaces=inhibited_surfaces,
    )
    directive = R05ProtectiveDirective(
        directive_id=f"r05-directive:{tick_id}",
        protective_mode=mode,
        authority_level=authority_level,
        inhibited_surfaces=inhibited_surfaces,
        project_override_active=project_override_active,
        release_pending=release_pending,
        release_conditions=release_conditions,
        recheck_after_ticks=1 if recovery_recheck_due else 0,
        reason="r05 bounded protective directive",
    )

    uncertainty_markers: list[str] = []
    if tone_only:
        uncertainty_markers.append("tone_only_protective_override_forbidden")
    if o04_legitimacy_gap:
        uncertainty_markers.append("o04_legitimacy_underconstrained")
    if o04_directionality_ambiguous and o04_coercive:
        uncertainty_markers.append("o04_directionality_ambiguous")
    if insufficient_basis:
        uncertainty_markers.append("insufficient_basis_for_override")
    if regulation_conflict:
        uncertainty_markers.append("regulation_conflict")
    if release_pending:
        uncertainty_markers.append("release_pending")
    if release_satisfied:
        uncertainty_markers.append("release_signal_or_counterevidence_present")
    if hysteresis_hold_ticks > 0:
        uncertainty_markers.append(f"hysteresis_hold_ticks:{hysteresis_hold_ticks}")

    state = R05ProtectiveRegulationState(
        regulation_id=f"r05-regulation:{tick_id}",
        protective_mode=directive.protective_mode,
        authority_level=directive.authority_level,
        trigger_ids=trigger_ids,
        trigger_count=len(trigger_ids),
        structural_basis_score=structural_basis_score,
        inhibited_surfaces=directive.inhibited_surfaces,
        project_override_active=directive.project_override_active,
        override_scope=override_scope,
        release_pending=directive.release_pending,
        release_conditions=directive.release_conditions,
        release_satisfied=release_satisfied,
        recovery_recheck_due=recovery_recheck_due,
        hysteresis_hold_ticks=hysteresis_hold_ticks,
        regulation_conflict=regulation_conflict,
        insufficient_basis_for_override=insufficient_basis,
        justification_links=tuple(
            dict.fromkeys(
                (
                    f"trigger_count:{len(trigger_ids)}",
                    f"structural_basis_score:{structural_basis_score:.2f}",
                    f"protective_mode:{directive.protective_mode.value}",
                    f"authority_level:{directive.authority_level.value}",
                    f"o04_coercive:{'yes' if o04_coercive else 'no'}",
                    f"o04_rupture:{'yes' if o04_rupture else 'no'}",
                    f"p01_handoff_ready:{'yes' if p01_handoff_ready else 'no'}",
                    *uncertainty_markers,
                )
            )
        ),
        provenance="r05.appraisal_sovereign_protective_regulation.policy",
        source_lineage=source_lineage,
        last_update_provenance="r05.appraisal_sovereign_protective_regulation.policy",
    )
    gate = _build_gate(state=state)
    scope_marker = R05ScopeMarker(
        scope="rt01_hosted_r05_first_slice",
        rt01_hosted_only=True,
        r05_first_slice_only=True,
        a05_not_implemented=True,
        v_line_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="bounded r05 slice; downstream protective/planning lines remain open seams",
    )
    telemetry = R05Telemetry(
        regulation_id=state.regulation_id,
        tick_index=tick_index,
        protective_mode=state.protective_mode,
        authority_level=state.authority_level,
        trigger_count=state.trigger_count,
        inhibited_surface_count=len(state.inhibited_surfaces),
        override_active=state.project_override_active,
        release_pending=state.release_pending,
        regulation_conflict=state.regulation_conflict,
        insufficient_basis_for_override=state.insufficient_basis_for_override,
        downstream_consumer_ready=gate.protective_state_consumer_ready,
        project_override_active=state.project_override_active,
    )
    return R05ProtectiveResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=(
            "r05 transformed typed appraisal/threat/project-load basis into bounded protective regulation "
            "with explicit inhibited surfaces, override scope, and release/hysteresis discipline"
        ),
    )


def _build_gate(
    *,
    state: R05ProtectiveRegulationState,
) -> R05ProtectiveGateDecision:
    protective_state_ready = bool(
        state.trigger_count > 0
        and state.protective_mode
        not in {
            R05ProtectiveMode.INSUFFICIENT_BASIS_FOR_OVERRIDE,
            R05ProtectiveMode.REGULATION_CONFLICT,
        }
    )
    surface_inhibition_ready = bool(len(state.inhibited_surfaces) > 0)
    release_contract_ready = bool(
        state.release_conditions
        and state.protective_mode
        in {
            R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE,
            R05ProtectiveMode.RECOVERY_IN_PROGRESS,
            R05ProtectiveMode.DEGRADED_OPERATION_ONLY,
            R05ProtectiveMode.RELEASE_TO_NORMAL_OPERATION,
        }
    )
    restrictions: list[str] = []
    if state.insufficient_basis_for_override:
        restrictions.append("insufficient_basis_for_override")
    if state.regulation_conflict:
        restrictions.append("regulation_conflict")
    if state.project_override_active:
        restrictions.append("project_override_active")
    if state.release_pending:
        restrictions.append("release_pending")
    if state.recovery_recheck_due:
        restrictions.append("recovery_recheck_due")
    if len(state.inhibited_surfaces) == 0:
        restrictions.append("no_surface_inhibition")
    return R05ProtectiveGateDecision(
        protective_state_consumer_ready=protective_state_ready,
        surface_inhibition_consumer_ready=surface_inhibition_ready,
        release_contract_consumer_ready=release_contract_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="r05 gate exposes protective-state, surface-inhibition and release-contract readiness",
    )


def _build_no_signal_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> R05ProtectiveResult:
    state = R05ProtectiveRegulationState(
        regulation_id=f"r05-regulation:{tick_id}",
        protective_mode=R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE,
        authority_level=R05AuthorityLevel.NONE,
        trigger_ids=(),
        trigger_count=0,
        structural_basis_score=0.0,
        inhibited_surfaces=(),
        project_override_active=False,
        override_scope="none",
        release_pending=False,
        release_conditions=(),
        release_satisfied=False,
        recovery_recheck_due=False,
        hysteresis_hold_ticks=0,
        regulation_conflict=False,
        insufficient_basis_for_override=True,
        justification_links=("trigger_count:0", "no_real_protective_basis"),
        provenance="r05.appraisal_sovereign_protective_regulation.no_signal",
        source_lineage=source_lineage,
        last_update_provenance="r05.appraisal_sovereign_protective_regulation.no_signal",
    )
    gate = R05ProtectiveGateDecision(
        protective_state_consumer_ready=False,
        surface_inhibition_consumer_ready=False,
        release_contract_consumer_ready=False,
        restrictions=("insufficient_basis_for_override", "no_surface_inhibition"),
        reason="r05 requires typed protective trigger basis; no default friction without signals",
    )
    scope_marker = R05ScopeMarker(
        scope="rt01_hosted_r05_first_slice",
        rt01_hosted_only=True,
        r05_first_slice_only=True,
        a05_not_implemented=True,
        v_line_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="r05 no-signal fallback",
    )
    telemetry = R05Telemetry(
        regulation_id=state.regulation_id,
        tick_index=tick_index,
        protective_mode=state.protective_mode,
        authority_level=state.authority_level,
        trigger_count=0,
        inhibited_surface_count=0,
        override_active=False,
        release_pending=False,
        regulation_conflict=False,
        insufficient_basis_for_override=True,
        downstream_consumer_ready=False,
        project_override_active=False,
    )
    return R05ProtectiveResult(
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
) -> R05ProtectiveResult:
    state = R05ProtectiveRegulationState(
        regulation_id=f"r05-regulation:{tick_id}",
        protective_mode=R05ProtectiveMode.INSUFFICIENT_BASIS_FOR_OVERRIDE,
        authority_level=R05AuthorityLevel.NONE,
        trigger_ids=(),
        trigger_count=0,
        structural_basis_score=0.0,
        inhibited_surfaces=(),
        project_override_active=False,
        override_scope="none",
        release_pending=False,
        release_conditions=(),
        release_satisfied=False,
        recovery_recheck_due=False,
        hysteresis_hold_ticks=0,
        regulation_conflict=False,
        insufficient_basis_for_override=True,
        justification_links=("r05_disabled",),
        provenance="r05.appraisal_sovereign_protective_regulation.disabled",
        source_lineage=source_lineage,
        last_update_provenance="r05.appraisal_sovereign_protective_regulation.disabled",
    )
    gate = R05ProtectiveGateDecision(
        protective_state_consumer_ready=False,
        surface_inhibition_consumer_ready=False,
        release_contract_consumer_ready=False,
        restrictions=("r05_disabled", "insufficient_basis_for_override"),
        reason="r05 protective regulation disabled in ablation context",
    )
    scope_marker = R05ScopeMarker(
        scope="rt01_hosted_r05_first_slice",
        rt01_hosted_only=True,
        r05_first_slice_only=True,
        a05_not_implemented=True,
        v_line_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="r05 disabled path",
    )
    telemetry = R05Telemetry(
        regulation_id=state.regulation_id,
        tick_index=tick_index,
        protective_mode=state.protective_mode,
        authority_level=state.authority_level,
        trigger_count=0,
        inhibited_surface_count=0,
        override_active=False,
        release_pending=False,
        regulation_conflict=False,
        insufficient_basis_for_override=True,
        downstream_consumer_ready=False,
        project_override_active=False,
    )
    return R05ProtectiveResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _trigger_structural_basis_score(trigger: R05ProtectiveTriggerInput) -> float:
    score = max(0.0, min(1.0, trigger.threat_structure_score))
    if trigger.o04_coercive_structure_present:
        score += 0.2
    if trigger.o04_rupture_risk_present:
        score += 0.12
    if trigger.p01_project_continuation_active and trigger.project_continuation_requested:
        score += 0.08
    if trigger.g08_appraisal_significance_hint is not None:
        score += max(0.0, min(1.0, trigger.g08_appraisal_significance_hint)) * 0.1
    if trigger.tone_only_discomfort:
        score -= 0.18
    return max(0.0, min(1.0, score))


def _derive_mode_and_authority(
    *,
    structural_basis_score: float,
    avg_load: float,
    tone_only: bool,
    insufficient_basis: bool,
    regulation_conflict: bool,
    release_signal_present: bool,
    counterevidence_present: bool,
    prior_state: R05ProtectiveRegulationState | None,
    o04_coercive: bool,
    o04_rupture: bool,
) -> tuple[R05ProtectiveMode, R05AuthorityLevel]:
    if regulation_conflict:
        return R05ProtectiveMode.REGULATION_CONFLICT, R05AuthorityLevel.BOUNDED_MONITORING
    if insufficient_basis:
        if tone_only:
            return R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE, R05AuthorityLevel.NONE
        return R05ProtectiveMode.INSUFFICIENT_BASIS_FOR_OVERRIDE, R05AuthorityLevel.NONE

    prior_mode = prior_state.protective_mode if isinstance(prior_state, R05ProtectiveRegulationState) else None
    prior_active = prior_mode in {
        R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE,
        R05ProtectiveMode.DEGRADED_OPERATION_ONLY,
        R05ProtectiveMode.RECOVERY_IN_PROGRESS,
    }
    release_evidence = bool(release_signal_present or counterevidence_present)

    if prior_active and release_evidence and structural_basis_score < 0.6:
        if structural_basis_score < 0.4:
            return R05ProtectiveMode.RELEASE_TO_NORMAL_OPERATION, R05AuthorityLevel.BOUNDED_MONITORING
        return R05ProtectiveMode.RECOVERY_IN_PROGRESS, R05AuthorityLevel.BOUNDED_MONITORING

    if structural_basis_score >= 0.72 and (o04_coercive or o04_rupture):
        return R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE, R05AuthorityLevel.BOUNDED_OVERRIDE
    if structural_basis_score >= 0.52 or avg_load >= 0.65:
        if prior_active and not release_evidence:
            return R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE, R05AuthorityLevel.BOUNDED_OVERRIDE
        return R05ProtectiveMode.DEGRADED_OPERATION_ONLY, R05AuthorityLevel.BOUNDED_MONITORING
    if structural_basis_score >= 0.35:
        return R05ProtectiveMode.PROTECTIVE_CANDIDATE_ONLY, R05AuthorityLevel.BOUNDED_MONITORING
    return R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE, R05AuthorityLevel.NONE


def _derive_inhibited_surfaces(
    *,
    mode: R05ProtectiveMode,
    communication_exposed: bool,
    project_requested: bool,
    permission_hardening_available: bool,
    escalation_route_available: bool,
) -> tuple[R05InhibitedSurface, ...]:
    inhibited: list[R05InhibitedSurface] = []
    if mode is R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE:
        if communication_exposed:
            inhibited.append(R05InhibitedSurface.COMMUNICATION_EXPOSURE)
        inhibited.append(R05InhibitedSurface.INTERACTION_INTENSITY)
        if project_requested:
            inhibited.append(R05InhibitedSurface.PROJECT_CONTINUATION)
        if permission_hardening_available:
            inhibited.append(R05InhibitedSurface.PERMISSION_HARDENING)
        if escalation_route_available:
            inhibited.append(R05InhibitedSurface.ESCALATION_ROUTING)
    elif mode is R05ProtectiveMode.DEGRADED_OPERATION_ONLY:
        inhibited.append(R05InhibitedSurface.INTERACTION_INTENSITY)
        if communication_exposed:
            inhibited.append(R05InhibitedSurface.COMMUNICATION_EXPOSURE)
    elif mode is R05ProtectiveMode.RECOVERY_IN_PROGRESS:
        inhibited.append(R05InhibitedSurface.INTERACTION_INTENSITY)
        if project_requested:
            inhibited.append(R05InhibitedSurface.PROJECT_CONTINUATION)
    return tuple(dict.fromkeys(inhibited))


def _derive_release_conditions(
    *,
    mode: R05ProtectiveMode,
    o04_rupture: bool,
    o04_coercive: bool,
    legitimacy_gap: bool,
    p01_handoff_ready: bool,
) -> tuple[str, ...]:
    if mode in {
        R05ProtectiveMode.VIGILANCE_WITHOUT_OVERRIDE,
        R05ProtectiveMode.PROTECTIVE_CANDIDATE_ONLY,
        R05ProtectiveMode.INSUFFICIENT_BASIS_FOR_OVERRIDE,
        R05ProtectiveMode.REGULATION_CONFLICT,
    }:
        return ()
    conditions = ["counterevidence_present", "trigger_downgrade"]
    if o04_rupture:
        conditions.append("o04_rupture_deescalated")
    if o04_coercive:
        conditions.append("o04_coercive_structure_cleared")
    if legitimacy_gap:
        conditions.append("legitimacy_basis_clarified")
    if p01_handoff_ready:
        conditions.append("project_handoff_stable")
    return tuple(dict.fromkeys(conditions))


def _derive_hysteresis_hold_ticks(
    *,
    mode: R05ProtectiveMode,
    prior_state: R05ProtectiveRegulationState | None,
    release_satisfied: bool,
    prior_hysteresis: int,
) -> int:
    if mode is R05ProtectiveMode.ACTIVE_PROTECTIVE_MODE and not release_satisfied:
        return min(3, max(1, prior_hysteresis + 1))
    if mode is R05ProtectiveMode.RECOVERY_IN_PROGRESS and not release_satisfied:
        return min(2, max(1, prior_hysteresis))
    return 0


def _derive_override_scope(
    *,
    project_override_active: bool,
    inhibited_surfaces: tuple[R05InhibitedSurface, ...],
) -> str:
    if project_override_active:
        return "project_continuation_bounded_override"
    if inhibited_surfaces:
        return "surface_throttle_only"
    return "none"
