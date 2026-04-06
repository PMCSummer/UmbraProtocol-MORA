from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from substrate.affordances.models import AffordanceResult
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.mode_arbitration.models import (
    EndogenousTickKind,
    HoldSwitchDecision,
    InterruptibilityClass,
    ModeArbitrationContext,
    ModeArbitrationLedgerEvent,
    ModeArbitrationLedgerEventKind,
    ModeArbitrationResult,
    ModeArbitrationState,
    ModePriorityScore,
    SubjectMode,
)
from substrate.mode_arbitration.policy import evaluate_mode_arbitration_downstream_gate
from substrate.mode_arbitration.telemetry import (
    build_mode_arbitration_telemetry,
    mode_arbitration_result_snapshot,
)
from substrate.regulation.models import RegulationResult, RegulationState
from substrate.regulatory_preferences.models import (
    PreferenceState,
    PreferenceUpdateResult,
)
from substrate.stream_diversification.models import (
    DiversificationDecisionStatus,
    StreamDiversificationResult,
    StreamDiversificationState,
)
from substrate.stream_kernel.models import (
    CarryoverClass,
    StreamInterruptionStatus,
    StreamKernelResult,
    StreamKernelState,
)
from substrate.tension_scheduler.models import (
    TensionKind,
    TensionLifecycleStatus,
    TensionSchedulerResult,
    TensionSchedulerState,
    TensionSchedulingMode,
)
from substrate.transition import execute_transition
from substrate.viability_control.models import (
    ViabilityControlResult,
    ViabilityControlState,
    ViabilityEscalationStage,
)


ATTEMPTED_MODE_ARBITRATION_PATHS: tuple[str, ...] = (
    "mode_arbitration.validate_typed_inputs",
    "mode_arbitration.collect_internal_basis",
    "mode_arbitration.endogenous_tick_contract",
    "mode_arbitration.multi_factor_priority",
    "mode_arbitration.hold_vs_switch_governance",
    "mode_arbitration.dwell_budget_recheck",
    "mode_arbitration.safe_idle_fallback",
    "mode_arbitration.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class _ArbitrationFactors:
    strong_survival_pressure: bool
    has_revisit_pressure: bool
    has_recovery_pressure: bool
    has_diversification_pressure: bool
    has_pending_output: bool
    has_unresolved_continuity: bool
    internal_basis: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _TickContract:
    tick_kind: EndogenousTickKind
    endogenous_tick_allowed: bool


def build_mode_arbitration(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
    tension_scheduler_state_or_result: TensionSchedulerState | TensionSchedulerResult,
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
    regulation_state_or_result: RegulationState | RegulationResult,
    affordance_result: AffordanceResult,
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
    context: ModeArbitrationContext | None = None,
) -> ModeArbitrationResult:
    context = context or ModeArbitrationContext()
    if not isinstance(context, ModeArbitrationContext):
        raise TypeError("context must be ModeArbitrationContext")
    if context.step_delta < 1:
        raise ValueError("context.step_delta must be >= 1")
    if not isinstance(affordance_result, AffordanceResult):
        raise TypeError("build_mode_arbitration requires typed AffordanceResult")

    stream_state = _extract_stream_input(stream_state_or_result)
    scheduler_state = _extract_scheduler_input(tension_scheduler_state_or_result)
    diversification_state = _extract_diversification_input(diversification_state_or_result)
    _, regulation_ref = _extract_regulation_input(regulation_state_or_result)
    _, preference_ref = _extract_preference_input(preference_state_or_result)
    viability_state, viability_ref = _extract_viability_input(viability_state_or_result)

    prior = context.prior_mode_arbitration_state
    if prior is not None and not isinstance(prior, ModeArbitrationState):
        raise TypeError(
            "context.prior_mode_arbitration_state must be ModeArbitrationState"
        )

    factors = _collect_arbitration_factors(
        stream_state=stream_state,
        scheduler_state=scheduler_state,
        diversification_state=diversification_state,
        viability_state=viability_state,
    )
    tick_contract = _derive_tick_contract(
        factors=factors,
        context=context,
    )

    priority_vector = _build_mode_priority_vector(
        stream_state=stream_state,
        scheduler_state=scheduler_state,
        diversification_state=diversification_state,
        factors=factors,
        tick_contract=tick_contract,
        context=context,
        prior=prior,
    )
    enabled_candidates = tuple(item for item in priority_vector if item.enabled)
    enabled_candidates_sorted = tuple(
        sorted(enabled_candidates, key=lambda item: item.score, reverse=True)
    )
    candidate_modes = tuple(item.mode for item in enabled_candidates_sorted)

    (
        active_mode,
        hold_or_switch_decision,
        handoff_reason,
        forced_rearbitration,
        dwell_budget_remaining,
    ) = _select_mode_with_governance(
        factors=factors,
        tick_contract=tick_contract,
        context=context,
        prior=prior,
        enabled_candidates=enabled_candidates_sorted,
    )
    confidence = _estimate_arbitration_confidence(
        active_mode=active_mode,
        enabled_candidates=enabled_candidates_sorted,
        hold_or_switch_decision=hold_or_switch_decision,
        factors=factors,
    )
    interruptibility = _derive_interruptibility(
        active_mode=active_mode,
        hold_or_switch_decision=hold_or_switch_decision,
        strong_survival_pressure=factors.strong_survival_pressure,
    )

    state = ModeArbitrationState(
        arbitration_id=f"mode-arbitration-{stream_state.stream_id}",
        tick_id=f"c04-tick-{stream_state.stream_id}-{stream_state.sequence_index}",
        stream_id=stream_state.stream_id,
        source_stream_sequence_index=stream_state.sequence_index,
        active_mode=active_mode,
        candidate_modes=candidate_modes,
        arbitration_basis=factors.internal_basis,
        mode_priority_vector=priority_vector,
        hold_or_switch_decision=hold_or_switch_decision,
        interruptibility=interruptibility,
        dwell_budget_remaining=dwell_budget_remaining,
        forced_rearbitration=forced_rearbitration,
        endogenous_tick_kind=tick_contract.tick_kind,
        endogenous_tick_allowed=tick_contract.endogenous_tick_allowed,
        external_turn_present=context.external_turn_present,
        handoff_reason=handoff_reason,
        arbitration_confidence=confidence,
        source_c01_state_ref=f"{stream_state.stream_id}@{stream_state.sequence_index}",
        source_c02_state_ref=(
            f"{scheduler_state.scheduler_id}@{scheduler_state.source_stream_sequence_index}"
        ),
        source_c03_state_ref=(
            f"{diversification_state.diversification_id}@{diversification_state.source_stream_sequence_index}"
        ),
        source_regulation_ref=regulation_ref,
        source_affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
        source_preference_ref=preference_ref,
        source_viability_ref=viability_ref,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *context.source_lineage,
                    *stream_state.source_lineage,
                    *scheduler_state.source_lineage,
                    *diversification_state.source_lineage,
                )
            )
        ),
        last_update_provenance="c04.mode_arbitration_from_c01_c02_c03_r04",
    )
    gate = evaluate_mode_arbitration_downstream_gate(state)
    ledger_events = _build_ledger_events(
        state=state,
        factors=factors,
    )
    telemetry = build_mode_arbitration_telemetry(
        state=state,
        ledger_events=ledger_events,
        attempted_paths=ATTEMPTED_MODE_ARBITRATION_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "typed c01/c02/c03/r04 pressures with bounded dwell/interruptibility governance for endogenous mode arbitration"
        ),
    )
    abstain = bool(
        hold_or_switch_decision
        in {
            HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
            HoldSwitchDecision.ARBITRATION_CONFLICT,
            HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
        }
        and confidence < 0.55
    )
    abstain_reason = (
        "insufficient_internal_basis"
        if hold_or_switch_decision == HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS
        else (
            "arbitration_conflict"
            if hold_or_switch_decision == HoldSwitchDecision.ARBITRATION_CONFLICT
            else "no_clear_mode_winner"
        )
        if abstain
        else None
    )
    return ModeArbitrationResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_planner_mode_selection_dependency=True,
        no_background_loop_dependency=True,
        no_external_turn_substitution_dependency=True,
    )


def mode_arbitration_result_to_payload(
    result: ModeArbitrationResult,
) -> dict[str, object]:
    return mode_arbitration_result_snapshot(result)


def persist_mode_arbitration_result_via_f01(
    *,
    result: ModeArbitrationResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("c04-mode-arbitration-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": (
                f"mode-arbitration-step-{result.state.source_stream_sequence_index}"
            ),
            "mode_arbitration_snapshot": mode_arbitration_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _collect_arbitration_factors(
    *,
    stream_state: StreamKernelState,
    scheduler_state: TensionSchedulerState,
    diversification_state: StreamDiversificationState,
    viability_state: ViabilityControlState,
) -> _ArbitrationFactors:
    strong_survival_pressure = bool(
        viability_state.escalation_stage
        in {ViabilityEscalationStage.THREAT, ViabilityEscalationStage.CRITICAL}
        or viability_state.pressure_level >= 0.72
    )
    revisit_entries = [
        entry
        for entry in scheduler_state.tensions
        if entry.scheduling_mode
        in {
            TensionSchedulingMode.REVISIT_NOW,
            TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
        }
        and entry.current_status
        in {TensionLifecycleStatus.ACTIVE, TensionLifecycleStatus.REACTIVATED}
    ]
    recovery_entries = [
        entry
        for entry in scheduler_state.tensions
        if entry.tension_kind in {TensionKind.PENDING_RECOVERY, TensionKind.INTERRUPTION_CONTINUITY}
        and entry.current_status
        in {
            TensionLifecycleStatus.ACTIVE,
            TensionLifecycleStatus.REACTIVATED,
            TensionLifecycleStatus.DEFERRED,
        }
    ]
    has_revisit_pressure = bool(revisit_entries)
    has_recovery_pressure = bool(
        recovery_entries
        or stream_state.interruption_status != StreamInterruptionStatus.NONE
    )
    has_diversification_pressure = bool(
        diversification_state.decision_status
        == DiversificationDecisionStatus.ALTERNATIVE_PATH_OPENING
        and diversification_state.diversification_pressure >= 0.55
        and diversification_state.actionable_alternative_classes
        and not diversification_state.no_safe_diversification
        and not diversification_state.diversification_conflict_with_survival
    )
    has_pending_output = bool("pending_output_or_recovery" in stream_state.pending_operations)
    has_load_bearing_carryover = any(
        item.carryover_class != CarryoverClass.HELD_FOCUS_ANCHOR
        for item in stream_state.carryover_items
    )
    has_unresolved_continuity = bool(
        has_load_bearing_carryover
        or stream_state.unresolved_anchors
        or stream_state.pending_operations
    )

    basis: list[str] = []
    if strong_survival_pressure:
        basis.append("strong_survival_pressure")
    if has_revisit_pressure:
        basis.append("active_revisit_pressure")
    if has_recovery_pressure:
        basis.append("recovery_pressure")
    if has_diversification_pressure:
        basis.append("diversification_pressure")
    if has_pending_output:
        basis.append("pending_output_work")
    if has_unresolved_continuity:
        basis.append("continuity_carryover_present")
    if not basis:
        basis.append("no_internal_pressure_basis")

    return _ArbitrationFactors(
        strong_survival_pressure=strong_survival_pressure,
        has_revisit_pressure=has_revisit_pressure,
        has_recovery_pressure=has_recovery_pressure,
        has_diversification_pressure=has_diversification_pressure,
        has_pending_output=has_pending_output,
        has_unresolved_continuity=has_unresolved_continuity,
        internal_basis=tuple(dict.fromkeys(basis)),
    )


def _derive_tick_contract(
    *,
    factors: _ArbitrationFactors,
    context: ModeArbitrationContext,
) -> _TickContract:
    has_internal_basis = factors.internal_basis != ("no_internal_pressure_basis",)
    if context.allow_endogenous_tick:
        if has_internal_basis and not context.cooldown_active and context.resource_budget >= 0.25:
            return _TickContract(
                tick_kind=EndogenousTickKind.ENDOGENOUS,
                endogenous_tick_allowed=True,
            )
        if has_internal_basis:
            return _TickContract(
                tick_kind=EndogenousTickKind.DEGRADED_ENDOGENOUS,
                endogenous_tick_allowed=True,
            )
    if context.external_turn_present:
        return _TickContract(
            tick_kind=EndogenousTickKind.EXTERNAL_REACTIVE,
            endogenous_tick_allowed=False,
        )
    return _TickContract(
        tick_kind=EndogenousTickKind.QUIESCENT,
        endogenous_tick_allowed=False,
    )


def _build_mode_priority_vector(
    *,
    stream_state: StreamKernelState,
    scheduler_state: TensionSchedulerState,
    diversification_state: StreamDiversificationState,
    factors: _ArbitrationFactors,
    tick_contract: _TickContract,
    context: ModeArbitrationContext,
    prior: ModeArbitrationState | None,
) -> tuple[ModePriorityScore, ...]:
    revisit_priority = max(
        (
            entry.revisit_priority
            for entry in scheduler_state.tensions
            if entry.scheduling_mode
            in {
                TensionSchedulingMode.REVISIT_NOW,
                TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
            }
        ),
        default=0.0,
    )
    dormant_or_stale = any(
        entry.current_status in {TensionLifecycleStatus.DORMANT, TensionLifecycleStatus.STALE}
        for entry in scheduler_state.tensions
    )
    scores: dict[SubjectMode, float] = {
        SubjectMode.HOLD_CURRENT_STREAM: (
            0.22
            + (0.2 if factors.has_unresolved_continuity else 0.0)
            + (0.14 if stream_state.continuity_confidence >= 0.6 else 0.0)
        ),
        SubjectMode.REVISIT_UNRESOLVED_TENSION: 0.25 + (0.55 * revisit_priority),
        SubjectMode.RECOVERY_MODE: (
            0.2
            + (0.5 if factors.strong_survival_pressure else 0.0)
            + (0.24 if factors.has_recovery_pressure else 0.0)
        ),
        SubjectMode.DIVERSIFICATION_PROBE: (
            0.15
            + (
                0.5 * diversification_state.diversification_pressure
                if factors.has_diversification_pressure
                else 0.0
            )
        ),
        SubjectMode.PASSIVE_MONITORING: 0.22 + (0.15 if dormant_or_stale else 0.0),
        SubjectMode.OUTPUT_PREPARATION: 0.18 + (0.35 if factors.has_pending_output else 0.0),
        SubjectMode.SAFE_IDLE: 0.1
        + (0.25 if factors.internal_basis == ("no_internal_pressure_basis",) else 0.0),
    }

    if context.resource_budget < 0.4:
        scores[SubjectMode.DIVERSIFICATION_PROBE] -= 0.2
        scores[SubjectMode.OUTPUT_PREPARATION] -= 0.24
    if context.cooldown_active:
        scores[SubjectMode.DIVERSIFICATION_PROBE] -= 0.15
        scores[SubjectMode.REVISIT_UNRESOLVED_TENSION] -= 0.12
        scores[SubjectMode.OUTPUT_PREPARATION] -= 0.12
    if prior is not None:
        scores[prior.active_mode] = scores.get(prior.active_mode, 0.0) + 0.08
        if prior.dwell_budget_remaining <= 0 and not factors.strong_survival_pressure:
            scores[prior.active_mode] -= 0.14
    for mode in context.recent_failed_modes:
        scores[mode] = scores.get(mode, 0.0) - 0.18
    for mode in context.recent_completed_modes:
        if mode != SubjectMode.SAFE_IDLE:
            scores[mode] = scores.get(mode, 0.0) - 0.06

    vector: list[ModePriorityScore] = []
    for mode in SubjectMode:
        enabled = True
        reasons: list[str] = []
        if mode == SubjectMode.REVISIT_UNRESOLVED_TENSION and not factors.has_revisit_pressure:
            enabled = False
            reasons.append("no_revisit_pressure")
        if mode == SubjectMode.RECOVERY_MODE and not (
            factors.has_recovery_pressure or factors.strong_survival_pressure
        ):
            enabled = False
            reasons.append("no_recovery_or_survival_basis")
        if mode == SubjectMode.DIVERSIFICATION_PROBE:
            if not factors.has_diversification_pressure:
                enabled = False
                reasons.append("no_diversification_pressure")
            if diversification_state.no_safe_diversification:
                enabled = False
                reasons.append("no_safe_diversification")
            if diversification_state.diversification_conflict_with_survival:
                enabled = False
                reasons.append("diversification_conflict_with_survival")
        if mode == SubjectMode.OUTPUT_PREPARATION and (
            not factors.has_pending_output or context.resource_budget < 0.25
        ):
            enabled = False
            reasons.append("no_pending_output_or_resource_too_low")
        if mode == SubjectMode.HOLD_CURRENT_STREAM and not factors.has_unresolved_continuity:
            enabled = False
            reasons.append("no_continuity_carryover")
        if mode == SubjectMode.PASSIVE_MONITORING and not (
            dormant_or_stale or factors.has_unresolved_continuity
        ):
            enabled = False
            reasons.append("no_monitoring_basis")
        if (
            factors.strong_survival_pressure
            and mode in {SubjectMode.DIVERSIFICATION_PROBE, SubjectMode.OUTPUT_PREPARATION}
        ):
            enabled = False
            reasons.append("survival_dominance")
        if (
            not tick_contract.endogenous_tick_allowed
            and mode
            in {
                SubjectMode.REVISIT_UNRESOLVED_TENSION,
                SubjectMode.RECOVERY_MODE,
                SubjectMode.DIVERSIFICATION_PROBE,
                SubjectMode.OUTPUT_PREPARATION,
            }
        ):
            enabled = False
            reasons.append("no_endogenous_tick_authority")

        reason = ";".join(reasons) if reasons else "mode_enabled"
        vector.append(
            ModePriorityScore(
                mode=mode,
                score=round(max(0.0, min(1.0, scores[mode])), 4),
                enabled=enabled,
                reason=reason,
            )
        )
    return tuple(sorted(vector, key=lambda item: item.score, reverse=True))


def _select_mode_with_governance(
    *,
    factors: _ArbitrationFactors,
    tick_contract: _TickContract,
    context: ModeArbitrationContext,
    prior: ModeArbitrationState | None,
    enabled_candidates: tuple[ModePriorityScore, ...],
) -> tuple[SubjectMode, HoldSwitchDecision, str, bool, int]:
    has_internal_basis = factors.internal_basis != ("no_internal_pressure_basis",)
    if factors.internal_basis == ("no_internal_pressure_basis",) and not context.external_turn_present:
        return (
            SubjectMode.SAFE_IDLE,
            HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
            "no_internal_basis_for_endogenous_mode_selection",
            False,
            max(0, context.default_dwell_budget),
        )
    if not enabled_candidates:
        return (
            SubjectMode.SAFE_IDLE,
            HoldSwitchDecision.SAFE_IDLE_ONLY,
            "no_enabled_mode_candidates",
            False,
            max(0, context.default_dwell_budget),
        )

    top = enabled_candidates[0]
    second = enabled_candidates[1] if len(enabled_candidates) > 1 else None
    selected = top.mode
    decision = (
        HoldSwitchDecision.CONTINUE_CURRENT_MODE
        if prior is not None and prior.active_mode == selected
        else HoldSwitchDecision.SWITCH_TO_MODE
    )
    reason = "top_priority_mode_selected"

    if (
        second is not None
        and abs(top.score - second.score) <= context.conflict_margin
        and top.mode != SubjectMode.SAFE_IDLE
    ):
        if prior is not None and any(item.mode == prior.active_mode for item in enabled_candidates):
            selected = prior.active_mode
            decision = HoldSwitchDecision.ARBITRATION_CONFLICT
            reason = "near_equal_candidates_hold_prior_mode"
        else:
            selected = (
                SubjectMode.PASSIVE_MONITORING
                if any(item.mode == SubjectMode.PASSIVE_MONITORING for item in enabled_candidates)
                else SubjectMode.SAFE_IDLE
            )
            decision = HoldSwitchDecision.ARBITRATION_CONFLICT
            reason = "near_equal_candidates_no_clear_winner"
    elif (
        top.score < context.min_confidence_for_switch
        and not factors.strong_survival_pressure
        and top.mode != SubjectMode.SAFE_IDLE
    ):
        if prior is not None and any(item.mode == prior.active_mode for item in enabled_candidates):
            selected = prior.active_mode
            decision = HoldSwitchDecision.NO_CLEAR_MODE_WINNER
            reason = "switch_below_confidence_threshold_hold_prior"
        else:
            weak_basis_fallback = next(
                (
                    item.mode
                    for item in enabled_candidates
                    if item.mode in {SubjectMode.PASSIVE_MONITORING, SubjectMode.HOLD_CURRENT_STREAM}
                ),
                None,
            )
            if has_internal_basis and tick_contract.endogenous_tick_allowed and weak_basis_fallback is not None:
                selected = weak_basis_fallback
                reason = "switch_below_confidence_threshold_weak_basis_fallback"
            else:
                selected = SubjectMode.SAFE_IDLE
                reason = "switch_below_confidence_threshold_no_prior"
            decision = HoldSwitchDecision.NO_CLEAR_MODE_WINNER

    if (
        context.weak_external_event
        and not context.closure_progress_event
        and not factors.strong_survival_pressure
        and prior is not None
        and selected != prior.active_mode
        and prior.dwell_budget_remaining > 0
    ):
        selected = prior.active_mode
        decision = HoldSwitchDecision.CONTINUE_CURRENT_MODE
        reason = "weak_external_event_has_no_interrupt_right"

    if (
        prior is not None
        and prior.hold_or_switch_decision == HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL
        and not factors.strong_survival_pressure
        and selected == prior.active_mode
    ):
        alternatives = tuple(
            item for item in enabled_candidates if item.mode != prior.active_mode
        )
        if alternatives and alternatives[0].score >= context.min_confidence_for_switch - 0.08:
            selected = alternatives[0].mode
            decision = HoldSwitchDecision.SWITCH_TO_MODE
            reason = "survival_deescalated_release_monopoly_to_viable_alternative"
        else:
            decision = HoldSwitchDecision.NO_CLEAR_MODE_WINNER
            reason = "survival_deescalated_requires_recheck_before_persistent_hold"

    if (
        factors.strong_survival_pressure
        and prior is not None
        and prior.active_mode
        in {
            SubjectMode.RECOVERY_MODE,
            SubjectMode.REVISIT_UNRESOLVED_TENSION,
            SubjectMode.HOLD_CURRENT_STREAM,
        }
        and selected in {SubjectMode.DIVERSIFICATION_PROBE, SubjectMode.OUTPUT_PREPARATION}
    ):
        selected = prior.active_mode
        decision = HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL
        reason = "survival_protected_mode_dominates_unsafe_switch"

    if factors.strong_survival_pressure and selected == SubjectMode.SAFE_IDLE:
        recovery_enabled = any(
            item.mode == SubjectMode.RECOVERY_MODE for item in enabled_candidates
        )
        if recovery_enabled:
            selected = SubjectMode.RECOVERY_MODE
            decision = HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL
            reason = "survival_pressure_forces_non_idle_recovery_mode"

    if prior is None:
        dwell = max(0, context.default_dwell_budget)
        return selected, decision, reason, False, dwell

    if selected == prior.active_mode:
        dwell = max(0, prior.dwell_budget_remaining - context.step_delta)
        if (
            prior.hold_or_switch_decision == HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL
            and not factors.strong_survival_pressure
        ):
            dwell = max(0, dwell - 1)
    else:
        dwell = max(0, context.default_dwell_budget)
    forced_rearb = False
    if selected == prior.active_mode and dwell == 0 and not factors.strong_survival_pressure:
        forced_rearb = True
        alternatives = tuple(
            item for item in enabled_candidates if item.mode != prior.active_mode
        )
        if alternatives and alternatives[0].score >= context.min_confidence_for_switch - 0.08:
            selected = alternatives[0].mode
            decision = HoldSwitchDecision.FORCED_REARBITRATION
            reason = "dwell_budget_exhausted_switch_to_next_viable_mode"
            dwell = max(0, context.default_dwell_budget)
        else:
            preferred_stable_mode = (
                prior.active_mode
                if any(item.mode == prior.active_mode for item in enabled_candidates)
                else (
                    SubjectMode.PASSIVE_MONITORING
                    if any(item.mode == SubjectMode.PASSIVE_MONITORING for item in enabled_candidates)
                    else SubjectMode.SAFE_IDLE
                )
            )
            selected = preferred_stable_mode
            decision = HoldSwitchDecision.NO_CLEAR_MODE_WINNER
            reason = "dwell_budget_exhausted_stabilized_hold_without_strong_alternative"
            dwell = max(1, context.default_dwell_budget)
            forced_rearb = False

    if (
        tick_contract.endogenous_tick_allowed is False
        and tick_contract.tick_kind == EndogenousTickKind.EXTERNAL_REACTIVE
        and selected not in {SubjectMode.PASSIVE_MONITORING, SubjectMode.SAFE_IDLE}
    ):
        can_keep_bounded_hold = bool(
            prior.active_mode == SubjectMode.HOLD_CURRENT_STREAM
            and factors.has_unresolved_continuity
            and (factors.has_pending_output or factors.has_revisit_pressure)
            and context.closure_progress_event
            and context.resource_budget >= 0.45
        )
        selected = (
            SubjectMode.HOLD_CURRENT_STREAM
            if can_keep_bounded_hold
            else SubjectMode.PASSIVE_MONITORING
        )
        decision = (
            HoldSwitchDecision.CONTINUE_CURRENT_MODE
            if can_keep_bounded_hold
            else HoldSwitchDecision.NO_CLEAR_MODE_WINNER
        )
        reason = (
            "external_turn_with_progress_allows_bounded_stream_hold"
            if can_keep_bounded_hold
            else "external_turn_only_cannot_substitute_internal_tick"
        )
        dwell = max(0, context.default_dwell_budget - 1)

    if tick_contract.tick_kind == EndogenousTickKind.QUIESCENT and selected != SubjectMode.SAFE_IDLE:
        selected = SubjectMode.SAFE_IDLE
        decision = HoldSwitchDecision.SAFE_IDLE_ONLY
        reason = "quiescent_tick_requires_safe_idle"
        dwell = max(0, context.default_dwell_budget)

    return selected, decision, reason, forced_rearb, dwell


def _estimate_arbitration_confidence(
    *,
    active_mode: SubjectMode,
    enabled_candidates: tuple[ModePriorityScore, ...],
    hold_or_switch_decision: HoldSwitchDecision,
    factors: _ArbitrationFactors,
) -> float:
    if not enabled_candidates:
        return 0.2
    top = enabled_candidates[0]
    second = enabled_candidates[1] if len(enabled_candidates) > 1 else None
    margin = max(0.0, top.score - (second.score if second is not None else 0.0))
    confidence = 0.22 + (0.58 * top.score) + (0.2 * min(0.25, margin))
    if hold_or_switch_decision in {
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
        HoldSwitchDecision.ARBITRATION_CONFLICT,
        HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
        HoldSwitchDecision.FORCED_REARBITRATION,
    }:
        confidence -= 0.14
    if active_mode == SubjectMode.SAFE_IDLE and factors.internal_basis == ("no_internal_pressure_basis",):
        confidence = max(confidence, 0.82)
    if factors.strong_survival_pressure and active_mode == SubjectMode.RECOVERY_MODE:
        confidence += 0.08
    return round(max(0.0, min(1.0, confidence)), 4)


def _derive_interruptibility(
    *,
    active_mode: SubjectMode,
    hold_or_switch_decision: HoldSwitchDecision,
    strong_survival_pressure: bool,
) -> InterruptibilityClass:
    if strong_survival_pressure or active_mode == SubjectMode.RECOVERY_MODE:
        return InterruptibilityClass.LOW
    if hold_or_switch_decision == HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL:
        return InterruptibilityClass.BLOCKED
    if active_mode in {SubjectMode.SAFE_IDLE, SubjectMode.PASSIVE_MONITORING}:
        return InterruptibilityClass.HIGH
    return InterruptibilityClass.MEDIUM


def _build_ledger_events(
    *,
    state: ModeArbitrationState,
    factors: _ArbitrationFactors,
) -> tuple[ModeArbitrationLedgerEvent, ...]:
    events: list[ModeArbitrationLedgerEvent] = [
        _ledger_event(
            event_kind=ModeArbitrationLedgerEventKind.ASSESSED,
            state=state,
            mode=state.active_mode,
            reason="mode arbitration assessed typed upstream pressures",
            reason_code="mode_assessed",
        )
    ]
    if state.active_mode == SubjectMode.SAFE_IDLE:
        events.append(
            _ledger_event(
                event_kind=ModeArbitrationLedgerEventKind.SAFE_IDLE,
                state=state,
                mode=state.active_mode,
                reason=state.handoff_reason,
                reason_code="safe_idle",
            )
        )
    elif state.hold_or_switch_decision in {
        HoldSwitchDecision.CONTINUE_CURRENT_MODE,
        HoldSwitchDecision.NO_CLEAR_MODE_WINNER,
        HoldSwitchDecision.INSUFFICIENT_INTERNAL_BASIS,
    }:
        events.append(
            _ledger_event(
                event_kind=ModeArbitrationLedgerEventKind.HOLD,
                state=state,
                mode=state.active_mode,
                reason=state.handoff_reason,
                reason_code="hold_mode",
            )
        )
    elif state.hold_or_switch_decision == HoldSwitchDecision.FORCED_HOLD_DUE_TO_SURVIVAL:
        events.append(
            _ledger_event(
                event_kind=ModeArbitrationLedgerEventKind.FORCED_HOLD,
                state=state,
                mode=state.active_mode,
                reason=state.handoff_reason,
                reason_code="forced_hold_survival",
            )
        )
    elif state.hold_or_switch_decision == HoldSwitchDecision.FORCED_REARBITRATION:
        events.append(
            _ledger_event(
                event_kind=ModeArbitrationLedgerEventKind.REARBITRATION,
                state=state,
                mode=state.active_mode,
                reason=state.handoff_reason,
                reason_code="forced_rearbitration",
            )
        )
    else:
        events.append(
            _ledger_event(
                event_kind=ModeArbitrationLedgerEventKind.SWITCH,
                state=state,
                mode=state.active_mode,
                reason=state.handoff_reason,
                reason_code="switch_mode",
            )
        )
    if factors.strong_survival_pressure and state.active_mode == SubjectMode.RECOVERY_MODE:
        events.append(
            _ledger_event(
                event_kind=ModeArbitrationLedgerEventKind.FORCED_HOLD,
                state=state,
                mode=state.active_mode,
                reason="survival pressure dominates arbitration outcome",
                reason_code="survival_dominance",
            )
        )
    return tuple(events)


def _ledger_event(
    *,
    event_kind: ModeArbitrationLedgerEventKind,
    state: ModeArbitrationState,
    mode: SubjectMode | None,
    reason: str,
    reason_code: str,
) -> ModeArbitrationLedgerEvent:
    return ModeArbitrationLedgerEvent(
        event_id=f"c04-ledger-{uuid4().hex[:10]}",
        event_kind=event_kind,
        tick_id=state.tick_id,
        stream_id=state.stream_id,
        mode=mode,
        reason=reason,
        reason_code=reason_code,
        provenance="c04.mode_arbitration_ledger",
    )


def _extract_stream_input(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
) -> StreamKernelState:
    if isinstance(stream_state_or_result, StreamKernelResult):
        return stream_state_or_result.state
    if isinstance(stream_state_or_result, StreamKernelState):
        return stream_state_or_result
    raise TypeError(
        "build_mode_arbitration requires StreamKernelState or StreamKernelResult"
    )


def _extract_scheduler_input(
    tension_scheduler_state_or_result: TensionSchedulerState | TensionSchedulerResult,
) -> TensionSchedulerState:
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerResult):
        return tension_scheduler_state_or_result.state
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerState):
        return tension_scheduler_state_or_result
    raise TypeError(
        "build_mode_arbitration requires TensionSchedulerState or TensionSchedulerResult"
    )


def _extract_diversification_input(
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
) -> StreamDiversificationState:
    if isinstance(diversification_state_or_result, StreamDiversificationResult):
        return diversification_state_or_result.state
    if isinstance(diversification_state_or_result, StreamDiversificationState):
        return diversification_state_or_result
    raise TypeError(
        "build_mode_arbitration requires StreamDiversificationState or StreamDiversificationResult"
    )


def _extract_regulation_input(
    regulation_state_or_result: RegulationState | RegulationResult,
) -> tuple[RegulationState, str]:
    if isinstance(regulation_state_or_result, RegulationResult):
        state = regulation_state_or_result.state
        return state, f"regulation-step-{state.last_updated_step}"
    if isinstance(regulation_state_or_result, RegulationState):
        return (
            regulation_state_or_result,
            f"regulation-step-{regulation_state_or_result.last_updated_step}",
        )
    raise TypeError(
        "build_mode_arbitration requires RegulationState or RegulationResult"
    )


def _extract_preference_input(
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
) -> tuple[PreferenceState, str]:
    if isinstance(preference_state_or_result, PreferenceUpdateResult):
        state = preference_state_or_result.updated_preference_state
        return state, f"preference-step-{state.last_updated_step}:{state.schema_version}"
    if isinstance(preference_state_or_result, PreferenceState):
        return (
            preference_state_or_result,
            f"preference-step-{preference_state_or_result.last_updated_step}:{preference_state_or_result.schema_version}",
        )
    raise TypeError(
        "build_mode_arbitration requires PreferenceState or PreferenceUpdateResult"
    )


def _extract_viability_input(
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
) -> tuple[ViabilityControlState, str]:
    if isinstance(viability_state_or_result, ViabilityControlResult):
        state = viability_state_or_result.state
        return (
            state,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    if isinstance(viability_state_or_result, ViabilityControlState):
        state = viability_state_or_result
        return (
            state,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    raise TypeError(
        "build_mode_arbitration requires ViabilityControlState or ViabilityControlResult"
    )
